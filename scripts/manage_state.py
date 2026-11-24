"""State management for JSA V21 — daily delta tracking + cleanup/dedup.

Tracks job lifecycle across runs: new, active, expired, user actions.
Provides library functions and a thin CLI wrapper with subcommands:
  sync, record-action, cleanup, dedup
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from dataclasses import fields as dataclass_fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

EXPIRY_DAYS = 14
VALID_ACTIONS = {"accepted", "rejected", "brief_requested"}
VALID_CHECKPOINT_PHASES = ["search", "verify", "dedup", "present", "deliver"]

# ---------------------------------------------------------------------------
# Canonical schema -- single source of truth for required fields and defaults
# ---------------------------------------------------------------------------

CANONICAL_FIELDS: dict[str, type | tuple[type, ...]] = {
    "job_id": str,
    "title": str,
    "company": str,
    "job_url": str,
    "role_type": str,
    "score": int,
    "source_channel": str,
    "run_date": str,
    "location": str,
    "status": str,
}
"""Canonical 10-field schema. Keys are required field names, values are expected types.
All consumers (validate-schema, migrate-schema, tests) derive from this constant.
To add an 11th field: add it here — all downstream consumers pick it up automatically.

Optional fields (validated when present, never required — missing = legacy default):
  - hard_gate_pass (bool): False = role's must-have requirements trip a context.md
    ## Hard-Gate Exclusions rule. Missing = legacy pass (True). Consumed by
    filter-presentation to suppress gated jobs from chat (files left in place).
  - hard_gate_reasons (list[str]): rule-id + quoted requirement per tripped rule."""

CANONICAL_FIELD_DEFAULTS: dict[str, Any] = {
    field: 0 if expected_type is int else ""
    for field, expected_type in CANONICAL_FIELDS.items()
}


@dataclass
class JobEntry:
    title: str
    company: str
    score: int
    role_type: str
    source: str
    first_seen: str
    last_seen: str
    active_status: str
    job_url: str
    location: str
    requirements_met: list[str]
    user_action: str | None = None
    expired_date: str | None = None
    applied_date: str | None = None
    reappeared: bool = False


@dataclass
class State:
    last_run_date: str | None = None
    jobs: dict[str, JobEntry] = field(default_factory=dict)
    expired_jobs: dict[str, JobEntry] = field(default_factory=dict)


def load_state(path: Path) -> State:
    """Load state from JSON file. Returns empty State if file doesn't exist."""
    if not path.exists():
        return State()

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    _known = {f.name for f in dataclass_fields(JobEntry)}

    jobs = {}
    for key, entry in data.get("jobs", {}).items():
        # Tolerate unknown fields written by newer/older sessions so a single
        # stray key never crash-wipes applied stamps (V27 regression guard).
        jobs[key] = JobEntry(**{k: v for k, v in entry.items() if k in _known})

    expired_jobs = {}
    for key, entry in data.get("expired_jobs", {}).items():
        expired_jobs[key] = JobEntry(**{k: v for k, v in entry.items() if k in _known})

    return State(
        last_run_date=data.get("last_run_date"),
        jobs=jobs,
        expired_jobs=expired_jobs,
    )


def save_state(state: State, path: Path) -> None:
    """Atomically write state to JSON file."""
    data = {
        "last_run_date": state.last_run_date,
        "jobs": {k: asdict(v) for k, v in state.jobs.items()},
        "expired_jobs": {k: asdict(v) for k, v in state.expired_jobs.items()},
    }

    tmp = tempfile.NamedTemporaryFile(
        dir=path.parent, delete=False, mode="w", suffix=".json", encoding="utf-8"
    )
    try:
        json.dump(data, tmp, indent=2)
        tmp.close()
        os.replace(tmp.name, path)
    except Exception:
        tmp.close()
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise


def _extract_score(verified_json: dict[str, Any]) -> int:
    """Extract score from verified JSON using canonical top-level `score` field only.

    The canonical schema defines `score` as a required int at the top level.
    All fallback paths removed -- migrate-schema normalises legacy files first.

    Raises ValueError if score is missing or not an int/float, signaling that
    migrate-schema has not been run. Callers should run validate-schema as a
    hard prerequisite before dedup to ensure this never fires in production.
    """
    score = verified_json.get("score")
    if isinstance(score, int):
        return score
    if isinstance(score, float):
        return int(score)
    raise ValueError(
        f"Missing or invalid 'score' field (got {score!r}). "
        f"Run migrate-schema before dedup."
    )


def _extract_job_entry(verified_json: dict[str, Any], role_type: str, run_date: str) -> JobEntry:
    """Extract a JobEntry from a verified JSON dict."""
    return JobEntry(
        title=verified_json["title"],
        company=verified_json["company"],
        score=_extract_score(verified_json),
        role_type=role_type,
        source=verified_json.get("source", "unknown"),
        first_seen=run_date,
        last_seen=run_date,
        active_status=verified_json.get("active_status", verified_json.get("status", "verified")),
        job_url=verified_json.get("job_url", ""),
        location=verified_json.get("location", ""),
        requirements_met=verified_json.get("requirements_met", []),
    )


def _scan_verified_dir(verified_dir: Path, searched_role_types: list[str]) -> dict[str, dict[str, Any]]:
    """Scan verified directory for job JSON files. Returns {job_key: parsed_json}."""
    found: dict[str, dict[str, Any]] = {}

    for role_type in searched_role_types:
        role_dir = verified_dir / role_type
        if not role_dir.is_dir():
            continue
        for json_file in role_dir.glob("*.json"):
            if json_file.name.startswith("_"):
                continue
            key = f"{role_type}/{json_file.stem}"
            with open(json_file, encoding="utf-8") as f:
                found[key] = json.load(f)

    return found


def update_state(
    state: State,
    verified_dir: Path,
    run_date: str,
    searched_role_types: list[str],
) -> State:
    """Update state with current verified jobs. Handles new, returning, and expired jobs."""
    state.last_run_date = run_date

    # Scan verified directory for current jobs
    current_jobs = _scan_verified_dir(verified_dir, searched_role_types)

    # Track which keys were seen this scan (for reappeared flag reset)
    seen_keys: set[str] = set()
    # Track which keys were resurrected this run
    resurrected_keys: set[str] = set()

    # Process each found job
    for key, verified_json in current_jobs.items():
        seen_keys.add(key)
        role_type = key.split("/")[0]

        if key in state.expired_jobs:
            # Resurrection: restore from expired
            expired_entry = state.expired_jobs.pop(key)
            expired_entry.last_seen = run_date
            expired_entry.user_action = None
            expired_entry.reappeared = True
            expired_entry.expired_date = None
            # Update score in case it changed
            expired_entry.score = verified_json["score"]
            expired_entry.active_status = verified_json.get("active_status", "verified")
            state.jobs[key] = expired_entry
            resurrected_keys.add(key)
        elif key in state.jobs:
            # Returning job: update last_seen and score
            entry = state.jobs[key]
            entry.last_seen = run_date
            entry.score = verified_json["score"]
            entry.active_status = verified_json.get("active_status", "verified")
        else:
            # New job
            state.jobs[key] = _extract_job_entry(verified_json, role_type, run_date)

    # Expire old jobs (only in searched role types)
    run_dt = datetime.strptime(run_date, "%Y-%m-%d")
    expiry_threshold = run_dt - timedelta(days=EXPIRY_DAYS)

    keys_to_expire = []
    for key, entry in state.jobs.items():
        role_type = key.split("/")[0]
        if role_type not in searched_role_types:
            continue
        if key not in seen_keys:
            last_seen_dt = datetime.strptime(entry.last_seen, "%Y-%m-%d")
            if last_seen_dt <= expiry_threshold:
                keys_to_expire.append(key)

    for key in keys_to_expire:
        entry = state.jobs.pop(key)
        entry.expired_date = run_date
        state.expired_jobs[key] = entry

    # Reset reappeared flag for jobs seen this scan but NOT resurrected this run
    for key in seen_keys:
        if key in state.jobs and key not in resurrected_keys:
            state.jobs[key].reappeared = False

    return state


def compute_delta(state: State, run_date: str) -> dict:
    """Compute delta from state. Returns job key classification lists."""
    new_jobs = []
    still_active = []

    for key, entry in state.jobs.items():
        if entry.first_seen == run_date:
            new_jobs.append(key)
        elif entry.user_action != "rejected":
            still_active.append(key)

    rejected_count = sum(1 for e in state.jobs.values() if e.user_action == "rejected")

    return {
        "run_date": run_date,
        "new_jobs": new_jobs,
        "still_active": still_active,
        "expired_count": len(state.expired_jobs),
        "rejected_count": rejected_count,
    }


PURGE_DAYS = 90


def purge_expired(state: State, run_date: str) -> State:
    """Remove expired jobs older than PURGE_DAYS from state.expired_jobs."""
    run_dt = datetime.strptime(run_date, "%Y-%m-%d")
    purge_threshold = run_dt - timedelta(days=PURGE_DAYS)

    keys_to_purge = []
    for key, entry in state.expired_jobs.items():
        if entry.expired_date:
            try:
                expired_dt = datetime.strptime(entry.expired_date, "%Y-%m-%d")
            except ValueError:
                continue  # Skip entries with malformed dates
            if expired_dt <= purge_threshold:
                keys_to_purge.append(key)

    for key in keys_to_purge:
        del state.expired_jobs[key]

    return state


def record_action(state: State, job_key: str, action: str) -> State:
    """Record a user action on a job."""
    if job_key not in state.jobs:
        raise KeyError(f"Job key not found: {job_key}")
    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid action: {action!r}. Valid: {VALID_ACTIONS}")
    state.jobs[job_key].user_action = action
    return state


# ---------------------------------------------------------------------------
# Cleanup subcommand
# ---------------------------------------------------------------------------

CLEANUP_DIRS = ["raw", "search-results", "unverified"]


def _cli_cleanup(args: argparse.Namespace) -> None:
    """CLI cleanup subcommand: remove temporary output directories."""
    output_dir = Path(args.output_dir)
    dry_run: bool = args.dry_run

    for dirname in CLEANUP_DIRS:
        target = output_dir / dirname
        if target.exists():
            if dry_run:
                print(f"[dry-run] would remove: {target}")
            else:
                shutil.rmtree(target, ignore_errors=True)


# ---------------------------------------------------------------------------
# Dedup subcommand (V21 rewrite)
# ---------------------------------------------------------------------------

SCORE_THRESHOLD = 70


def _load_verified_jobs(
    verified_dir: Path,
    role_types: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Scan output/verified/*/ for all JSON files.

    Args:
        verified_dir: Path to the verified/ directory.
        role_types: When provided, only scan subdirectories whose names appear
            in the list. When ``None``, scan all (backward compatible).

    Returns a list of dicts, each augmented with:
      _filepath: Path to the file on disk
      _role: role directory name
      _filename: the JSON filename
    """
    jobs: list[dict[str, Any]] = []
    if not verified_dir.is_dir():
        return jobs

    for role_dir in sorted(verified_dir.iterdir()):
        if not role_dir.is_dir():
            continue
        role = role_dir.name
        if role_types is not None and role not in role_types:
            continue
        for json_file in sorted(role_dir.glob("*.json")):
            if json_file.name.startswith("_"):
                continue
            data = json.loads(json_file.read_text(encoding="utf-8"))
            data["_filepath"] = json_file
            data["_role"] = role
            data["_filename"] = json_file.name
            jobs.append(data)

    return jobs


def _optional_score(job: dict[str, Any]) -> int | None:
    """Legacy score as int, or None when absent/invalid (never raises, never fabricates)."""
    score = job.get("score")
    if isinstance(score, bool):
        return None
    if isinstance(score, int):
        return score
    if isinstance(score, float) and math.isfinite(score):
        return int(score)
    return None


def _record_recency(job: dict[str, Any]) -> str:
    """Most recent checked_at/date_verified string ('' if neither present)."""
    return max(str(job.get("checked_at") or ""), str(job.get("date_verified") or ""))


def _order_duplicates(group: list[dict[str, Any]]) -> None:
    """Prefer recent records if a group contains new-format or unscored data."""
    group.sort(key=lambda job: str(job["_filepath"]))
    if all(_optional_score(job) is not None for job in group):
        group.sort(key=_optional_score, reverse=True)
    else:
        group.sort(key=_record_recency, reverse=True)


def _find_cross_role_duplicates(
    jobs_by_key: dict[str, list[dict[str, Any]]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Find cross-role duplicates.

    For each (company, title) key that appears in multiple roles, keep the
    winning copy (see _order_duplicates) and return (keep, archive) pairs
    for the rest.
    """
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []

    for _key, group in jobs_by_key.items():
        if len(group) <= 1:
            continue
        _order_duplicates(group)
        keeper = group[0]
        for dup in group[1:]:
            pairs.append((keeper, dup))

    return pairs


def _find_same_url_duplicates(
    jobs_by_url: dict[str, list[dict[str, Any]]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Find within-role same-URL duplicates.

    For each (role, normalized_url) key that has multiple entries, keep the
    winning copy (see _order_duplicates) and return (keep, archive) pairs
    for the rest.
    """
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []

    for _key, group in jobs_by_url.items():
        if len(group) <= 1:
            continue
        _order_duplicates(group)
        keeper = group[0]
        for dup in group[1:]:
            pairs.append((keeper, dup))

    return pairs


def _apply_archive(
    archive_list: list[dict[str, Any]],
    archive_base: Path,
    dry_run: bool,
) -> None:
    """Move files to archive directory. Creates subdirs as needed."""
    for job in archive_list:
        src: Path = job["_filepath"]
        if not src.exists():
            continue  # already archived by a previous pass
        role = job["_role"]
        filename = job["_filename"]
        dest_dir = archive_base / role
        dest = dest_dir / filename
        serial = 1
        while dest.exists():
            dest = dest_dir / f"{src.stem}-{serial}{src.suffix}"
            serial += 1

        if dry_run:
            print(f"[dry-run] would archive: {src} -> {dest}")
        else:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(str(src), str(dest))


def _derive_active_role_types(verified_dir: Path, run_date: str) -> tuple[list[str], list[str]]:
    """Scan verified_dir subdirectories to find active vs stale role types.

    A role type is "active" if it contains at least one .json file whose
    `run_date` field matches the given run_date.
    Returns (active_role_types, stale_role_types).
    """
    active: list[str] = []
    stale: list[str] = []

    if not verified_dir.is_dir():
        return active, stale

    for role_dir in sorted(verified_dir.iterdir()):
        if not role_dir.is_dir():
            continue
        role = role_dir.name
        is_active = False
        for json_file in role_dir.glob("*.json"):
            if json_file.name.startswith("_"):
                continue
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if data.get("run_date") == run_date:
                    is_active = True
                    break
            except (json.JSONDecodeError, OSError):
                continue
        if is_active:
            active.append(role)
        else:
            stale.append(role)

    return active, stale


SAFETY_BOUND_PCT = 50


def _check_safety_bound(
    jobs: list[dict[str, Any]],
    to_archive: dict[Path, dict[str, Any]],
    *,
    last_run_date: str | None = None,
    today: str | None = None,
) -> list[str]:
    """Check the safety bound per role type.

    Gap detection: if last_run_date is provided and gap > 7 days,
    threshold auto-adjusts from 50% to 90%.
    """
    threshold = SAFETY_BOUND_PCT
    if last_run_date and today:
        try:
            last_dt = datetime.strptime(last_run_date, "%Y-%m-%d")
            today_dt = datetime.strptime(today, "%Y-%m-%d")
            gap_days = (today_dt - last_dt).days
            if gap_days > 7:
                threshold = 90
                print(
                    f"WARNING: {gap_days}-day gap since last run - "
                    f"safety bound adjusted from {SAFETY_BOUND_PCT}% to {threshold}%",
                    file=sys.stderr,
                )
        except ValueError:
            pass

    role_total: dict[str, int] = {}
    role_archived: dict[str, int] = {}

    for job in jobs:
        role = job["_role"]
        role_total[role] = role_total.get(role, 0) + 1

    for job in to_archive.values():
        role = job["_role"]
        role_archived[role] = role_archived.get(role, 0) + 1

    errors: list[str] = []
    for role, archived_count in role_archived.items():
        total = role_total.get(role, 0)
        if total == 0:
            continue
        pct = (archived_count / total) * 100
        if pct > threshold:
            errors.append(
                f"Safety bound exceeded for {role!r}: would archive "
                f"{archived_count}/{total} ({pct:.0f}%)"
            )
    return errors


def _cli_dedup(args: argparse.Namespace) -> None:
    """CLI dedup subcommand: cross-role + same-URL dedup.

    The legacy numeric score is diagnostic only: it never archives a record
    by default (matching-policy.md section 8). The old score < 70 archival
    runs only with --legacy-score-archive. Archival moves files to
    output/archive (history preserved).

    Supports three scoping modes:
    1. --auto-scope --run-date DATE: derive active role types from run_date field
    2. --role-types SLUGS: explicit comma-separated list
    3. (no flags): process all directories (backward compat)

    Auto-scope also enforces a per-role-type safety bound (>50% archive -> abort).
    """
    output_dir = Path(args.output_dir)
    verified_dir = output_dir / "verified"
    archive_base = output_dir / "archive"
    dry_run: bool = args.dry_run
    auto_scope: bool = getattr(args, "auto_scope", False)
    run_date: str | None = getattr(args, "run_date", None)

    stale_role_types: list[str] = []

    if auto_scope and run_date:
        active_role_types, stale_role_types = _derive_active_role_types(
            verified_dir, run_date
        )
        role_types: list[str] | None = active_role_types
        print(
            f"Dedup auto-scope: {len(active_role_types)} active role types, "
            f"{len(stale_role_types)} stale (skipped): "
            f"{', '.join(stale_role_types) if stale_role_types else 'none'}",
            file=sys.stderr,
        )
    elif args.role_types is not None:
        if args.role_types == "":
            early_summary: dict[str, int] = {"total_input": 0, "archived": 0, "remaining": 0}
            sys.stdout.write(json.dumps(early_summary, indent=2) + "\n")
            return
        role_types = [rt.strip() for rt in args.role_types.split(",") if rt.strip()]
    else:
        role_types = None

    # --active-only: restrict to role types from context.md ## Target
    if getattr(args, "active_only", False):
        active_slugs = _get_active_role_types(
            getattr(args, "context_path", "context.md")
        )
        if active_slugs:
            if role_types is not None:
                # Intersect with any existing role-type filter
                role_types = [rt for rt in role_types if rt in active_slugs]
            else:
                role_types = sorted(active_slugs)

    jobs = _load_verified_jobs(verified_dir, role_types=role_types)

    to_archive: dict[Path, dict[str, Any]] = {}

    # --- 1. Cross-role dedup by (company, title) ---
    jobs_by_key: dict[str, list[dict[str, Any]]] = {}
    for job in jobs:
        company = job.get("company", "").lower().strip()
        title = job.get("title", "").lower().strip()
        key = f"{company}:{title}"
        jobs_by_key.setdefault(key, []).append(job)

    cross_role_pairs = _find_cross_role_duplicates(jobs_by_key)
    for _keeper, dup in cross_role_pairs:
        to_archive[dup["_filepath"]] = dup

    # --- 2. Within-role same-URL dedup ---
    remaining = [j for j in jobs if j["_filepath"] not in to_archive]
    jobs_by_url: dict[str, list[dict[str, Any]]] = {}
    for job in remaining:
        url = (job.get("job_url") or job.get("url") or "").lower().strip()
        if not url:
            continue
        role = job["_role"]
        url_key = f"{role}:{url}"
        jobs_by_url.setdefault(url_key, []).append(job)

    same_url_pairs = _find_same_url_duplicates(jobs_by_url)
    for _keeper, dup in same_url_pairs:
        to_archive[dup["_filepath"]] = dup

    # --- 3. Score threshold (legacy, opt-in only; score has no archival authority) ---
    if getattr(args, "legacy_score_archive", False):
        remaining = [j for j in jobs if j["_filepath"] not in to_archive]
        for job in remaining:
            score = _optional_score(job)
            if score is not None and score < SCORE_THRESHOLD:
                to_archive[job["_filepath"]] = job

    # --- 4. Safety bound (all modes — use --no-safety-bound to opt out) ---
    no_safety_bound: bool = getattr(args, "no_safety_bound", False)
    if not no_safety_bound:
        state_path = output_dir.parent / "state.json"
        _last_run_date: str | None = None
        if state_path.exists():
            try:
                with open(state_path, encoding="utf-8") as f:
                    state_data = json.load(f)
                _last_run_date = state_data.get("last_run_date")
            except (json.JSONDecodeError, OSError):
                pass
        _today = run_date or datetime.now().strftime("%Y-%m-%d")
        bound_errors = _check_safety_bound(
            jobs, to_archive,
            last_run_date=_last_run_date, today=_today,
        )
        if bound_errors:
            for err in bound_errors:
                print(f"ERROR: {err}", file=sys.stderr)
            print(
                "Aborting dedup -- safety bound exceeded. No files archived. "
                "Use --no-safety-bound to override.",
                file=sys.stderr,
            )
            sys.exit(1)

    # --- Apply ---
    archive_jobs = list(to_archive.values())
    _apply_archive(archive_jobs, archive_base, dry_run)

    summary: dict[str, int | str] = {
        "total_input": len(jobs),
        "archived": len(archive_jobs),
        "remaining": len(jobs) - len(archive_jobs),
        "active_role_types": len(role_types) if role_types is not None else "all",
        "stale_role_types_skipped": len(stale_role_types),
    }
    sys.stdout.write(json.dumps(summary, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Checkpoint subcommands
# ---------------------------------------------------------------------------


def _cli_checkpoint_write(args: argparse.Namespace) -> None:
    """Write a checkpoint file for the given phase."""
    output_dir = Path(args.output_dir)
    checkpoints_dir = output_dir / ".checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "phase": args.phase,
        "count": args.count,
        "committed": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    cp_path = checkpoints_dir / f"{args.phase}.json"
    with open(cp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _cli_checkpoint_validate(args: argparse.Namespace) -> None:
    """Validate that a checkpoint exists and is committed."""
    output_dir = Path(args.output_dir)
    cp_path = output_dir / ".checkpoints" / f"{args.phase}.json"

    if not cp_path.exists():
        print(f"FAIL: no checkpoint for phase '{args.phase}'", file=sys.stderr)
        sys.exit(1)

    with open(cp_path, encoding="utf-8") as f:
        data = json.load(f)

    # Minimal schema validation
    required_keys = {"phase", "count", "timestamp"}
    missing = required_keys - set(data.keys())
    if missing:
        print(f"FAIL: checkpoint '{args.phase}' missing required keys: {missing}", file=sys.stderr)
        sys.exit(1)

    if not data.get("committed", False):
        print(f"FAIL: checkpoint '{args.phase}' exists but not committed", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {args.phase} — count={data.get('count', '?')}")


def _cli_checkpoint_status(args: argparse.Namespace) -> None:
    """Print status table of all checkpoint phases."""
    output_dir = Path(args.output_dir)
    checkpoints_dir = output_dir / ".checkpoints"
    pad = max(len(p) for p in VALID_CHECKPOINT_PHASES) + 2

    for phase in VALID_CHECKPOINT_PHASES:
        cp_path = checkpoints_dir / f"{phase}.json"
        if cp_path.exists():
            with open(cp_path, encoding="utf-8") as f:
                data = json.load(f)
            committed = "yes" if data.get("committed", False) else "no"
            count = data.get("count", "?")
            ts = data.get("timestamp", "?")
            print(f"{phase:<{pad}} COMPLETE  count={count}  committed={committed}  ts={ts}")
        else:
            print(f"{phase:<{pad}} PENDING")


def _cli_checkpoint_clear(args: argparse.Namespace) -> None:
    """Delete all checkpoint JSON files."""
    output_dir = Path(args.output_dir)
    checkpoints_dir = output_dir / ".checkpoints"

    if not checkpoints_dir.exists():
        return

    for json_file in checkpoints_dir.glob("*.json"):
        json_file.unlink()

    print(f"Cleared all checkpoints in {checkpoints_dir}")


# ---------------------------------------------------------------------------
# list-active-role-types subcommand
# ---------------------------------------------------------------------------


def _slugify(name: str) -> str:
    """Convert a role type name to a clean kebab-case slug.

    Rules: lowercase, spaces/underscores -> hyphens, non-[a-z0-9] -> hyphens,
    collapse multiple hyphens, strip leading/trailing hyphens.

    Examples: "AI Engineer Jobs" -> "ai-engineer-jobs", "DevRel & Advocacy" -> "devrel-advocacy"
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    return slug


def _parse_target_section(content: str) -> list[str]:
    """Extract role type names from the ## Target section of context.md.

    Parses bullet-point lines (starting with '- ') within the ## Target
    section and returns them as a list of strings.
    """
    lines = content.splitlines()
    in_target = False
    role_types: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Detect start of ## Target section
        if stripped == "## Target":
            in_target = True
            continue

        # Detect next section header (stop parsing)
        if in_target and stripped.startswith("## "):
            break

        # Extract bullet items within ## Target
        if in_target and stripped.startswith("- "):
            name = stripped[2:].strip()
            if name:
                role_types.append(name)

    return role_types


def _get_active_role_types(context_path: str) -> set[str]:
    """Read active role-type slugs from context.md ## Target section.

    Factored out as internal helper so dedup --active-only can call directly
    without subprocess self-invocation.
    """
    ctx = Path(context_path)
    if not ctx.exists():
        return set()
    content = ctx.read_text(encoding="utf-8")
    role_names = _parse_target_section(content)
    slugs = set()
    for name in role_names:
        slug = _slugify(name)
        if slug:
            slugs.add(slug)
    return slugs


def _cli_list_active_role_types(args: argparse.Namespace) -> None:
    """CLI list-active-role-types subcommand: extract role-type slugs from context.md."""
    context_path = Path(args.context_path)

    if not context_path.exists():
        print(f"Error: context file not found: {context_path}", file=sys.stderr)
        sys.exit(1)

    slugs = _get_active_role_types(args.context_path)
    for slug in sorted(slugs):
        print(slug)


# ---------------------------------------------------------------------------
# verify-clean-working-tree subcommand
# ---------------------------------------------------------------------------


def _cli_verify_batch_committed(args: argparse.Namespace) -> None:
    """Verify that all files under --verified-path are committed in git.

    Exits 0 if the path doesn't exist or all files are committed.
    Exits 1 if there are uncommitted (untracked or modified) files.
    """
    verified_path = Path(args.verified_path).resolve()

    if not verified_path.exists():
        # Nothing to verify — exit cleanly
        return

    # Find the git repo root that contains the verified path
    toplevel_result = subprocess.run(
        ["git", "-C", str(verified_path), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if toplevel_result.returncode != 0:
        # Not inside a git repo — nothing to verify
        return

    repo_root = toplevel_result.stdout.strip()

    result = subprocess.run(
        ["git", "-C", repo_root, "status", "--porcelain", str(verified_path)],
        capture_output=True,
        text=True,
    )

    if result.stdout.strip():
        print(
            f"ERROR: uncommitted files in {verified_path}:\n{result.stdout}",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# verify-channels-dispatched subcommand
# ---------------------------------------------------------------------------

REQUIRED_CHANNELS = [
    "direct-career-pages",
    "industry-job-boards",
    "jobspy-aggregator",
    "niche-newsletters",
    "web-search-discovery",
]


def _cli_verify_channels_dispatched(args: argparse.Namespace) -> None:
    """Verify all 5 search channel .done files exist with today's mtime.

    Exits 0 if all channels have .done files dated to --run-date.
    Exits 1 if any are missing or stale, listing the problems.
    """
    output_dir = Path(args.output_dir)
    run_date = args.run_date
    channels_dir = output_dir / ".channels"

    errors: list[str] = []

    for channel in REQUIRED_CHANNELS:
        done_file = channels_dir / f"{channel}.done"
        if not done_file.exists():
            errors.append(f"missing: {channel}")
            continue

        # Check mtime date matches run_date
        mtime = done_file.stat().st_mtime
        mtime_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        if mtime_date != run_date:
            errors.append(f"stale: {channel} (mtime {mtime_date}, expected {run_date})")

    if errors:
        print(
            "ERROR: channel verification failed:\n" + "\n".join(f"  - {e}" for e in errors),
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# verify-session-state-updated subcommand
# ---------------------------------------------------------------------------


def _cli_verify_session_state_updated(args: argparse.Namespace) -> None:
    """Verify session-state.md exists and was modified on the run date.

    Exits 0 if the file exists and its mtime date matches --run-date.
    Exits 1 if the file is missing or stale.
    """
    session_state_path = Path(args.session_state_path)
    run_date = args.run_date

    if not session_state_path.exists():
        print(
            f"ERROR: session-state.md not found: {session_state_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    mtime = session_state_path.stat().st_mtime
    mtime_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

    if mtime_date != run_date:
        print(
            f"ERROR: session-state.md is stale (mtime {mtime_date}, expected {run_date})",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# check-session-resume subcommand
# ---------------------------------------------------------------------------


def _cli_check_session_resume(args: argparse.Namespace) -> None:
    """Check if a digest was already sent today.

    Exits 1 if _status.json exists and its sent_at date matches today.
    Exits 0 if the file is missing or the date is different.
    """
    status_path = Path(args.status_path)
    run_date = args.run_date

    if not status_path.exists():
        sys.exit(0)

    with open(status_path, encoding="utf-8") as f:
        data = json.load(f)

    sent_at = data.get("sent_at", "")
    # Extract date portion (first 10 chars of ISO datetime or plain date string)
    sent_date = sent_at[:10] if sent_at else ""

    if sent_date == run_date:
        print(f"A digest was already sent today ({run_date})")
        sys.exit(1)

    sys.exit(0)


# ---------------------------------------------------------------------------
# verify-state-clean subcommand
# ---------------------------------------------------------------------------


def _cli_verify_state_clean(args: argparse.Namespace) -> None:
    """Verify state.json is a clean, complete, inspectable state file.

    Exits 0 (clean) when the file is fully-formed OR when it is absent. An
    absent file is treated as clean because load_state() returns an empty
    State() for a missing path -- there is nothing corrupt to inspect.

    Exits 1 with a human-readable diagnostic on stderr (no traceback) when the
    file is corrupt JSON, is not a JSON object, is missing a required top-level
    key (the save_state contract: last_run_date, jobs, expired_jobs), or
    contains an entry that fails to load into JobEntry.
    """
    path = Path(args.state)

    if not path.exists():
        # Absent == empty state, per load_state(). Nothing corrupt to inspect.
        sys.exit(0)

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"state.json is corrupt: {path}: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print(
            f"state.json is not a JSON object (got {type(data).__name__}): {path}",
            file=sys.stderr,
        )
        sys.exit(1)

    required = ("last_run_date", "jobs", "expired_jobs")
    missing = [k for k in required if k not in data]
    if missing:
        print(
            f"state.json is missing required keys {missing}: {path}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Reuse load_state to verify entries deserialize into JobEntry. Any
    # structural load failure is converted into a clean diagnostic rather than
    # escaping as a traceback.
    try:
        load_state(path)
    except Exception as e:
        print(
            f"state.json has an entry that fails to load: {path}: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


# ---------------------------------------------------------------------------
# check-model-settings subcommand
# ---------------------------------------------------------------------------

VALID_AGENT_MODELS = {"haiku", "sonnet"}


def _parse_yaml_frontmatter(content: str) -> dict[str, str]:
    """Parse YAML frontmatter from a markdown file.

    Returns a dict of key-value string pairs from the frontmatter block.
    Returns an empty dict if no frontmatter is found.
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    fields: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            fields[key.strip()] = value.strip()

    return fields


def _cli_check_model_settings(args: argparse.Namespace) -> None:
    """Validate model: field in all agent frontmatter files.

    Valid values: haiku, sonnet.
    Everything else (including inherit, opus, or missing) is a failure.
    Exits 0 if all agents pass, exits 1 on first (or any) failure.
    """
    agents_dir = Path(args.agents_dir)
    exclude_set: set[str] = set()
    if args.exclude:
        exclude_set = {name.strip() for name in args.exclude.split(",") if name.strip()}

    if not agents_dir.exists():
        print(f"Agents directory not found: {agents_dir}", file=sys.stderr)
        sys.exit(1)

    errors: list[str] = []

    for md_file in sorted(agents_dir.glob("*.md")):
        if md_file.name in exclude_set:
            continue

        content = md_file.read_text(encoding="utf-8")
        frontmatter = _parse_yaml_frontmatter(content)
        model_value = frontmatter.get("model", None)

        if model_value is None:
            errors.append(
                f"Agent model misconfigured: {md_file.name} has model: (missing) "
                f"(expected haiku or sonnet)"
            )
        elif model_value not in VALID_AGENT_MODELS:
            errors.append(
                f"Agent model misconfigured: {md_file.name} has model: {model_value} "
                f"(expected haiku or sonnet)"
            )

    if errors:
        for error in errors:
            print(error)
        sys.exit(1)

    print("All agent model settings validated")


# ---------------------------------------------------------------------------
# validate-schema subcommand
# ---------------------------------------------------------------------------

REQUIRED_SCHEMA_FIELDS = list(CANONICAL_FIELDS.keys())


def _handle_validate_schema(args: argparse.Namespace) -> None:
    """Walk output/verified/*/ and validate all JSON files against the canonical schema."""
    output_dir = Path(args.output_dir)
    verified_dir = output_dir / "verified"

    total = 0
    failures: list[str] = []

    if verified_dir.is_dir():
        for role_dir in sorted(verified_dir.iterdir()):
            if not role_dir.is_dir():
                continue
            for json_file in sorted(role_dir.glob("*.json")):
                if json_file.name.startswith("_"):
                    continue
                total += 1
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    failures.append(f"{json_file}: JSON parse error -- {exc}")
                    continue

                file_errors: list[str] = []

                for field in REQUIRED_SCHEMA_FIELDS:
                    if field not in data:
                        file_errors.append(f"missing field '{field}'")

                if "score" in data and not isinstance(data["score"], int):
                    file_errors.append(
                        f"field 'score' must be int, got {type(data['score']).__name__!r} "
                        f"(value: {data['score']!r})"
                    )

                # Optional field: hard_gate_pass. Missing = legacy pass (True),
                # so the ~270 existing files without it are NOT rejected. When
                # present it must be a bool; hard_gate_reasons (if present) a list.
                if "hard_gate_pass" in data and not isinstance(data["hard_gate_pass"], bool):
                    file_errors.append(
                        f"field 'hard_gate_pass' must be bool, "
                        f"got {type(data['hard_gate_pass']).__name__!r} "
                        f"(value: {data['hard_gate_pass']!r})"
                    )
                if "hard_gate_reasons" in data and not isinstance(data["hard_gate_reasons"], list):
                    file_errors.append(
                        f"field 'hard_gate_reasons' must be list, "
                        f"got {type(data['hard_gate_reasons']).__name__!r}"
                    )

                # URL quality check: reject generic career pages
                job_url = data.get("job_url", "")
                if job_url and not _is_specific_job_url(job_url):
                    file_errors.append(
                        f"job_url is a generic career page, not a specific listing - {job_url}"
                    )

                # active_status check: must be non-null after verification
                has_verification = (
                    "verification_date" in data
                    or "verified_at" in data
                    or data.get("active_status") in ("expired", "live")
                )
                if has_verification and data.get("active_status") is None:
                    file_errors.append(
                        "active_status is null after verification"
                    )

                if file_errors:
                    failures.append(
                        f"{json_file}: " + "; ".join(file_errors)
                    )

    passed = total - len(failures)
    print(f"Validated {total} files: {passed} passed, {len(failures)} failed")

    if failures:
        for failure in failures:
            print(f"  FAIL: {failure}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# migrate-schema subcommand
# ---------------------------------------------------------------------------

def _migrate_one_file(path: Path) -> bool:
    """Migrate a single JSON file to the canonical schema.
    Returns True if the file was modified, False if already canonical.
    """
    try:
        original_text = path.read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(original_text)
    except (json.JSONDecodeError, OSError):
        return False

    changed = False

    # 1. Normalise score
    if "score" not in data:
        legacy_score: int | None = None
        if "overall_score" in data:
            try:
                legacy_score = int(data["overall_score"])
            except (TypeError, ValueError):
                pass
        if legacy_score is None:
            sb = data.get("scoring_breakdown")
            if isinstance(sb, dict) and "overall_score" in sb:
                try:
                    legacy_score = int(sb["overall_score"])
                except (TypeError, ValueError):
                    pass
        data["score"] = legacy_score if legacy_score is not None else 0
        changed = True
    elif not isinstance(data["score"], int):
        try:
            data["score"] = int(data["score"])
            changed = True
        except (TypeError, ValueError):
            data["score"] = 0
            changed = True

    # 2. Add missing required fields with defaults
    for fld, default in CANONICAL_FIELD_DEFAULTS.items():
        if fld not in data:
            data[fld] = default
            changed = True

    if not changed:
        return False

    new_text = json.dumps(data, indent=2, ensure_ascii=False)
    path.write_text(new_text, encoding="utf-8")
    return True


def _handle_migrate_schema(args: argparse.Namespace) -> None:
    """Walk output/verified/*/ and output/archive/*/ and migrate all JSON files."""
    output_dir = Path(args.output_dir)
    total = 0
    modified = 0

    scan_dirs = [output_dir / "verified", output_dir / "archive"]

    for scan_root in scan_dirs:
        if not scan_root.is_dir():
            continue
        for role_dir in sorted(scan_root.iterdir()):
            if not role_dir.is_dir():
                continue
            for json_file in sorted(role_dir.glob("*.json")):
                if json_file.name.startswith("_"):
                    continue
                total += 1
                if _migrate_one_file(json_file):
                    modified += 1

    already_canonical = total - modified
    print(f"Migrated {total} files: {modified} modified, {already_canonical} already canonical")


# ---------------------------------------------------------------------------
# check-dashboard-url subcommand
# ---------------------------------------------------------------------------


def _parse_delivery_section(content: str) -> str:
    """Extract Dashboard: value from the ## Delivery section of context.md.

    Returns the URL string, or empty string if not found or empty.
    """
    lines = content.splitlines()
    in_delivery = False

    for line in lines:
        stripped = line.strip()

        if stripped == "## Delivery":
            in_delivery = True
            continue

        if in_delivery and stripped.startswith("## "):
            break

        if in_delivery and stripped.startswith("Dashboard:"):
            _, _, value = stripped.partition(":")
            return value.strip()

    return ""


def _cli_check_dashboard_url(args: argparse.Namespace) -> None:
    """Check that Dashboard: URL is present and non-empty in context.md.

    Exits 0 if found and non-empty (prints the URL).
    Exits 1 if missing or empty.
    """
    context_path = Path(args.context_path)

    if not context_path.exists():
        print("Dashboard URL missing or empty in context.md")
        sys.exit(1)

    content = context_path.read_text(encoding="utf-8")
    url = _parse_delivery_section(content)

    if not url:
        print("Dashboard URL missing or empty in context.md")
        sys.exit(1)

    print(url)


# ---------------------------------------------------------------------------
# Existing CLI subcommands (sync, record-action)
# ---------------------------------------------------------------------------


def _cli_sync(args: argparse.Namespace) -> None:
    """CLI sync subcommand: update state + compute delta in one pass."""
    state_path = Path(args.state)
    verified_dir = Path(args.verified_dir)
    output_path = Path(args.output)

    searched = args.searched_role_types.split(",") if args.searched_role_types else []

    state = load_state(state_path)
    state = update_state(state, verified_dir, args.run_date, searched)
    state = purge_expired(state, args.run_date)
    save_state(state, state_path)

    delta = compute_delta(state, args.run_date)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(delta, f, indent=2)


def _cli_record_action(args: argparse.Namespace) -> None:
    """CLI record-action subcommand: record a user action on a job."""
    state_path = Path(args.state)
    state = load_state(state_path)
    state = record_action(state, args.job_key, args.action)
    save_state(state, state_path)


# ---------------------------------------------------------------------------


def _cli_verify_session_state_written(args: argparse.Namespace) -> None:
    """Verify session-state.md contains an entry for the given run date.

    Two-tier check (simplified per code-simplicity-reviewer):
    1. Check for `## {date}` heading
    2. Fall back to plain string match anywhere in file

    Exits 0 if found, exits 1 if missing or file does not exist.
    """
    session_state_path = Path(args.session_state_path)
    run_date = args.run_date

    if not session_state_path.exists():
        print(
            f"ERROR: session-state.md not found: {session_state_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    content = session_state_path.read_text(encoding="utf-8")

    # Tier 1: heading match
    if f"## {run_date}" in content:
        print(f"OK: session-state.md contains entry for {run_date}")
        return

    # Tier 2: plain string match anywhere
    if run_date in content:
        print(f"OK: session-state.md contains entry for {run_date}")
        return

    print(
        f"ERROR: session-state.md does not contain entry for {run_date}",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# increment-dispatch-counter subcommand
# ---------------------------------------------------------------------------


def _read_dispatch_count(session_state_path: Path) -> int:
    """Read dispatch_count from session-state.md. Returns 0 if not found.

    Uses regex matching consistent with _write_dispatch_count (symmetric approach).
    """
    if not session_state_path.exists():
        return 0
    content = session_state_path.read_text(encoding="utf-8")
    m = re.search(r"dispatch_count:\s*(\d+)", content)
    return int(m.group(1)) if m else 0


def _write_dispatch_count(session_state_path: Path, count: int) -> None:
    """Write dispatch_count into ## Budget section of session-state.md.

    Uses regex-replace approach: if ``dispatch_count: \\d+`` exists, replace in-place.
    If ## Budget section exists but no count line, append. If no section, append both.
    """
    if not session_state_path.exists():
        session_state_path.write_text(
            f"# Session State\n\n## Budget\ndispatch_count: {count}\n",
            encoding="utf-8",
        )
        return

    content = session_state_path.read_text(encoding="utf-8")

    # Try regex replace first
    new_content, n = re.subn(r"dispatch_count: \d+", f"dispatch_count: {count}", content)
    if n > 0:
        session_state_path.write_text(new_content, encoding="utf-8")
        return

    # No existing count line — append to ## Budget section or create it
    if "## Budget" in content:
        new_content = content.replace("## Budget", f"## Budget\ndispatch_count: {count}", 1)
    else:
        new_content = content.rstrip() + f"\n\n## Budget\ndispatch_count: {count}\n"

    session_state_path.write_text(new_content, encoding="utf-8")


def _cli_increment_dispatch_counter(args: argparse.Namespace) -> None:
    """Increment the dispatch counter in session-state.md ## Budget section."""
    session_state_path = Path(args.session_state_path)
    current = _read_dispatch_count(session_state_path)
    new_count = current + 1
    _write_dispatch_count(session_state_path, new_count)
    print(f"Dispatch count: {current} -> {new_count}")


# ---------------------------------------------------------------------------
# check-dispatch-budget subcommand
# ---------------------------------------------------------------------------


def _cli_check_dispatch_budget(args: argparse.Namespace) -> None:
    """Check if dispatch count is under the ceiling.

    Exits 0 if under ceiling (budget available).
    Exits 1 if at or over ceiling (budget exhausted).
    """
    session_state_path = Path(args.session_state_path)
    ceiling = int(args.ceiling)
    current = _read_dispatch_count(session_state_path)

    if current >= ceiling:
        print(f"Budget exhausted: {current}/{ceiling} dispatches")
        sys.exit(1)

    print(f"Budget available: {current}/{ceiling} dispatches")


# ---------------------------------------------------------------------------
# validate-url-type subcommand
# ---------------------------------------------------------------------------

# Patterns that indicate a direct source (company ATS or career page)
_SOURCE_PATTERNS: dict[str, re.Pattern[str]] = {
    "greenhouse": re.compile(r"greenhouse\.io", re.IGNORECASE),
    "ashby": re.compile(r"ashbyhq\.com", re.IGNORECASE),
    "lever": re.compile(r"lever\.co", re.IGNORECASE),
    "workable": re.compile(r"workable\.com", re.IGNORECASE),
    "gem": re.compile(r"jobs\.gem\.com", re.IGNORECASE),
    "rippling": re.compile(r"rippling\.com", re.IGNORECASE),
    "breezy": re.compile(r"breezy\.hr", re.IGNORECASE),
    "jazz": re.compile(r"jazz\.co", re.IGNORECASE),
    "applytojob": re.compile(r"applytojob\.com", re.IGNORECASE),
    "smartrecruiters": re.compile(r"smartrecruiters\.com", re.IGNORECASE),
    "recruitee": re.compile(r"recruitee\.com", re.IGNORECASE),
    "bamboohr": re.compile(r"bamboohr\.com", re.IGNORECASE),
    "personio": re.compile(r"personio\.de|personio\.com", re.IGNORECASE),
    "factorial": re.compile(r"factorialhr\.com", re.IGNORECASE),
    "icims": re.compile(r"icims\.com", re.IGNORECASE),
    "taleo": re.compile(r"taleo\.net", re.IGNORECASE),
    "successfactors": re.compile(r"successfactors\.com|successfactors\.eu", re.IGNORECASE),
    "myworkday": re.compile(r"myworkday\.com|myworkdayjobs\.com|wd\d+\.myworkdaysite\.com", re.IGNORECASE),
}

# Patterns that indicate an aggregator (job board)
_AGGREGATOR_PATTERNS: dict[str, re.Pattern[str]] = {
    "indeed": re.compile(r"indeed\.com", re.IGNORECASE),
    "linkedin": re.compile(r"linkedin\.com", re.IGNORECASE),
    "glassdoor": re.compile(r"glassdoor\.com|glassdoor\.co", re.IGNORECASE),
    "studysmarter": re.compile(r"studysmarter\.co", re.IGNORECASE),
    "ziprecruiter": re.compile(r"ziprecruiter\.com|ziprecruiter\.co\.[a-z]{2}", re.IGNORECASE),
    "monster": re.compile(r"monster\.com", re.IGNORECASE),
    "simplyhired": re.compile(r"simplyhired\.com", re.IGNORECASE),
}


def classify_url(url: str) -> dict[str, str]:
    """Classify a URL as source, aggregator, or unknown.

    Returns a dict with keys: url, type, pattern_matched.
    """
    from run_validation import web_url

    host = urlparse(url).hostname if web_url(url) else ""
    for kind, patterns in (("source", _SOURCE_PATTERNS), ("aggregator", _AGGREGATOR_PATTERNS)):
        for name, pattern in patterns.items():
            for match in pattern.finditer(host):
                if match.end() == len(host) and (match.start() == 0 or host[match.start() - 1] == "."):
                    return {"url": url, "type": kind, "pattern_matched": name}
    return {"url": url, "type": "unknown", "pattern_matched": "unknown"}


def _cli_validate_url_type(args: argparse.Namespace) -> None:
    """CLI validate-url-type subcommand: classify a URL as source/aggregator/unknown."""
    result = classify_url(args.url)
    print(json.dumps(result))


# ---------------------------------------------------------------------------
# verify-before-archive subcommand
# ---------------------------------------------------------------------------


def verify_before_archive(input_path: Path, *, write: bool = False) -> dict[str, str]:
    """Check if a job URL is still live via HTTP HEAD (source-first strategy).

    Returns dict with keys: status, evidence, url.
    Does NOT modify the file unless --write is explicitly passed.

    Source-first strategy (V25 regression fix): classifies the URL first.
    - Source URLs: HTTP HEAD result is definitive.
    - Aggregator URLs: HTTP HEAD is unreliable (aggregators return 200 for
      expired listings). Returns status="unverified" instead of "live".
    - Unknown URLs: HTTP HEAD result is used but marked as "unverified-source".
    """
    if requests is None:
        raise ImportError("requests library required for verify-before-archive")

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    job_url = data.get("job_url", "")
    result: dict[str, str] = {"url": job_url}

    # Classify URL first (source-first strategy)
    url_classification = classify_url(job_url)
    url_type = url_classification["type"]
    result["url_type"] = url_type

    try:
        from urllib.parse import urlparse

        original_domain = urlparse(job_url).netloc
        resp = requests.head(job_url, timeout=10, allow_redirects=True)
        code = resp.status_code
        result["evidence"] = f"HTTP {code}"

        # Redirect detection: if final URL domain changed significantly,
        # the listing may have redirected to a generic "no longer accepting" page
        final_url = resp.url if isinstance(getattr(resp, "url", None), str) else job_url
        final_domain = urlparse(final_url).netloc
        redirected_to_different_domain = (
            original_domain != final_domain
            and not final_domain.endswith(original_domain)
            and not original_domain.endswith(final_domain)
        )

        if 200 <= code <= 399:
            if redirected_to_different_domain:
                result["status"] = "unverified-redirect"
                result["evidence"] = (
                    f"HTTP {code} after redirect to {final_domain} "
                    f"(original: {original_domain}) — possible generic page"
                )
            elif url_type == "source":
                result["status"] = "live"
            elif url_type == "aggregator":
                # Aggregators return 200 for expired listings — NOT definitive
                result["status"] = "unverified"
                result["evidence"] = (
                    f"HTTP {code} (aggregator — not definitive, "
                    f"source-first strategy requires ATS verification)"
                )
            else:
                result["status"] = "unverified-source"
                result["evidence"] = f"HTTP {code} (unknown domain — unverified)"
        elif code in (404, 410):
            result["status"] = "expired"
        else:
            result["status"] = "unreachable"

    except requests.Timeout:
        result["status"] = "unreachable"
        result["evidence"] = "timeout"
    except requests.ConnectionError as exc:
        result["status"] = "unreachable"
        result["evidence"] = f"error: {exc}"
    except requests.RequestException as exc:
        result["status"] = "unreachable"
        result["evidence"] = f"error: {exc}"

    # Only write verdict to file if explicitly requested
    if write:
        data["active_status"] = result["status"]
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return result


def _cli_verify_before_archive(args: argparse.Namespace) -> None:
    """CLI verify-before-archive subcommand."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    result = verify_before_archive(input_path, write=args.write)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")


# ---------------------------------------------------------------------------
# validate-presentation subcommand
# ---------------------------------------------------------------------------

_GENERIC_PAGES = {
    "open-positions", "open-roles", "all-jobs", "all-roles", "join-us", "current-openings",
    "job-openings", "view-all", "see-all", "search-results", "our-team", "life-at", "search",
    "careers", "jobs", "positions", "departments",
}
_ROLE_PREFIXES = {"careers", "jobs", "job", "roles", "role", "positions", "vacancies", "openings", "o"}


def _is_specific_job_url(url: str) -> bool:
    """Check URL shape. The employer or a reviewed source establishes liveness."""
    from run_validation import web_url

    if not web_url(url):
        return False
    parsed = urlparse(url)
    path = [segment for segment in parsed.path.strip("/").lower().split("/") if segment]
    query = parse_qs(parsed.query)
    provider = classify_url(url)["pattern_matched"]
    if any(value.isdigit() for value in query.get("gh_jid", [])):
        return True
    if provider in ("ashby", "lever"):
        return len(path) >= 2 and path[1] not in _GENERIC_PAGES
    if provider == "greenhouse":
        return (len(path) >= 3 and path[1] == "jobs" and path[2].isdigit()) or (
            path == ["embed", "job_app"] and bool(query.get("token"))
        )
    if provider == "linkedin":
        return len(path) == 3 and path[:2] == ["jobs", "view"] and path[2][-1:].isdigit()
    if provider == "indeed":
        return path in (["viewjob"], ["rc", "clk"]) and bool(query.get("jk"))
    if provider == "workable":
        return len(path) >= 3 and path[-2] == "j"

    if not path:
        host = parsed.hostname
        return any(
            host.endswith("." + domain) and "-" in host[: -len(domain) - 1]
            for domain in ("lovable.app", "framer.website", "framer.app", "webflow.io", "carrd.co")
        )
    if path[-1] in _GENERIC_PAGES:
        return False
    if any(re.match(r"^\d{4,}(?:-|$)", segment) or re.fullmatch(
        r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", segment
    ) for segment in path):
        return True
    if len(path) == 2:
        return path[0] in _ROLE_PREFIXES and bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", path[1]))
    return len(path) >= 3


def _cli_validate_run(args: argparse.Namespace) -> None:
    """Validate a completed tier-based run and its exact presentation set."""
    from run_validation import validate_run

    result, _ = validate_run(Path(args.manifest), today=args.today, max_age_days=args.max_age_days)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)


def _cli_validate_presentation(args: argparse.Namespace) -> None:
    """CLI validate-presentation: check verified JSONs are presentation-ready."""
    output_dir = Path(args.output_dir)
    verified_dir = output_dir / "verified"
    role_types = [rt.strip() for rt in args.role_types.split(",") if rt.strip()]

    violations: list[str] = []

    for role_type in role_types:
        role_dir = verified_dir / role_type
        if not role_dir.is_dir():
            continue

        for json_file in sorted(role_dir.glob("*.json")):
            if json_file.name.startswith("_"):
                continue

            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                violations.append(f"{json_file.name}: JSON read error - {exc}")
                continue

            job_url = data.get("job_url", "")
            # Liveness lives in `active_status` (legacy schema) or `status`
            # (current schema). Fall back to `status` only when the
            # `active_status` key is absent; an explicit null means
            # verification left it unresolved and must fail.
            if "active_status" in data:
                active_status = data["active_status"]
            else:
                active_status = data.get("status")

            # Normalize: values that mean "verified live" across both schemas.
            live_values = {
                "active", "verified", "live", "live-uk", "open", "new",
            }
            dead_values = {"expired", "dead", "closed", "inactive", "gone", "404"}
            normalized = active_status.lower() if isinstance(active_status, str) else None

            if not _is_specific_job_url(job_url):
                violations.append(
                    f"{json_file.name}: job_url is a generic career page, "
                    f"not a specific listing - {job_url}"
                )

            if normalized is None:
                violations.append(f"{json_file.name}: active_status/status is null")
            elif normalized in dead_values:
                violations.append(
                    f"{json_file.name}: expired/dead job in active verified list"
                    f" (status={active_status})"
                )
            elif normalized not in live_values:
                violations.append(
                    f"{json_file.name}: liveness unconfirmed (status={active_status})"
                )

    passed = len(violations) == 0
    result = {"passed": passed, "violations": violations}
    sys.stdout.write(json.dumps(result, indent=2) + "\n")

    if not passed:
        sys.exit(1)


# ---------------------------------------------------------------------------
# filter-presentation subcommand (hard-gate enforcement)
# ---------------------------------------------------------------------------


def _hard_gate_passes(data: dict[str, Any]) -> bool:
    """Return True if a verified job passes the hard gate.

    A job passes unless it explicitly carries ``hard_gate_pass == false``.
    A MISSING field is treated as a legacy pass (True) so the ~270 existing
    files written before this field existed are never silently suppressed.
    """
    value = data.get("hard_gate_pass")
    if value is None:
        return True  # legacy / un-evaluated file -> pass
    return bool(value)


def _cli_filter_presentation(args: argparse.Namespace) -> None:
    """Produce the chat-facing set by EXCLUDING hard-gated jobs (flag, not archive).

    Scans output/verified/{role_type}/ for the given role types. Jobs with
    ``hard_gate_pass == false`` are recorded to a suppressed-list file
    (default output/_hard_gated.json) so the board-builder can flag them 🔴
    while the parent omits them from chat. Files are LEFT IN PLACE — nothing
    is moved or deleted.

    Safety bound: if suppressing would empty an entire role type (all jobs in
    that role gated), a WARNING is logged to stderr — never silently empty a
    whole role type without logging.
    """
    output_dir = Path(args.output_dir)
    verified_dir = output_dir / "verified"
    role_types = [rt.strip() for rt in args.role_types.split(",") if rt.strip()]
    out_path = Path(args.out) if getattr(args, "out", None) else output_dir / "_hard_gated.json"

    suppressed: list[dict[str, Any]] = []
    presented_count = 0
    role_total: dict[str, int] = {}
    role_suppressed: dict[str, int] = {}

    for role_type in role_types:
        role_dir = verified_dir / role_type
        if not role_dir.is_dir():
            continue

        for json_file in sorted(role_dir.glob("*.json")):
            if json_file.name.startswith("_"):
                continue
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            role_total[role_type] = role_total.get(role_type, 0) + 1

            if _hard_gate_passes(data):
                presented_count += 1
                continue

            role_suppressed[role_type] = role_suppressed.get(role_type, 0) + 1
            suppressed.append(
                {
                    "job_id": data.get("job_id", json_file.stem),
                    "company": data.get("company", ""),
                    "title": data.get("title", ""),
                    "role_type": role_type,
                    "hard_gate_reasons": data.get("hard_gate_reasons", []),
                }
            )

    # Safety bound: log (do NOT abort) if a whole role type was emptied.
    for role_type, total in role_total.items():
        if total > 0 and role_suppressed.get(role_type, 0) == total:
            print(
                f"WARNING: hard-gate would suppress ALL {total} job(s) in role "
                f"type {role_type!r} from chat presentation (files left in place)",
                file=sys.stderr,
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(suppressed, indent=2) + "\n", encoding="utf-8")

    summary = {
        "total_scanned": presented_count + len(suppressed),
        "presented": presented_count,
        "suppressed": len(suppressed),
        "suppressed_file": str(out_path),
    }
    sys.stdout.write(json.dumps(summary, indent=2) + "\n")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="JSA V21 State Management")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- sync ---
    sync_parser = subparsers.add_parser("sync", help="Update state and compute delta")
    sync_parser.add_argument("--verified-dir", required=True, dest="verified_dir")
    sync_parser.add_argument("--run-date", required=True, dest="run_date")
    sync_parser.add_argument("--searched-role-types", required=True, dest="searched_role_types")
    sync_parser.add_argument("--state", default="state.json")
    sync_parser.add_argument("--output", required=True)
    sync_parser.set_defaults(func=_cli_sync)

    # --- record-action ---
    action_parser = subparsers.add_parser("record-action", help="Record user action on a job")
    action_parser.add_argument("--state", default="state.json")
    action_parser.add_argument("--job-key", required=True, dest="job_key")
    action_parser.add_argument("--action", required=True)
    action_parser.set_defaults(func=_cli_record_action)

    # --- cleanup ---
    cleanup_parser = subparsers.add_parser("cleanup", help="Remove temporary output directories")
    cleanup_parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=str(Path(__file__).resolve().parent.parent / "output"),
        help="Base output directory (default: output/ relative to project root)",
    )
    cleanup_parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Print actions without executing",
    )
    cleanup_parser.set_defaults(func=_cli_cleanup)

    # --- dedup ---
    dedup_parser = subparsers.add_parser(
        "dedup",
        help="Cross-role + URL deduplication (legacy score is diagnostic only; "
        "never archives by default)",
    )
    dedup_parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=str(Path(__file__).resolve().parent.parent / "output"),
        help="Base output directory (default: output/ relative to project root)",
    )
    dedup_parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Report duplicates without moving files",
    )
    dedup_parser.add_argument(
        "--role-types",
        type=str,
        default=None,
        help="Comma-separated role type slugs to process",
    )
    dedup_parser.add_argument(
        "--auto-scope",
        action="store_true",
        dest="auto_scope",
        default=False,
        help="Auto-derive active role types from run_date field in JSON files",
    )
    dedup_parser.add_argument(
        "--run-date",
        dest="run_date",
        default=None,
        help="Run date YYYY-MM-DD used for auto-scoping (required with --auto-scope)",
    )
    dedup_parser.add_argument(
        "--no-safety-bound",
        action="store_true",
        dest="no_safety_bound",
        default=False,
        help="Disable per-role-type safety bound check (use with caution)",
    )
    dedup_parser.add_argument(
        "--active-only",
        action="store_true",
        default=False,
        help="Only dedup role-type directories matching active role types from context.md",
    )
    dedup_parser.add_argument(
        "--context-path",
        dest="context_path",
        default="context.md",
        help="Path to context.md for --active-only filtering (default: context.md)",
    )
    dedup_parser.add_argument(
        "--legacy-score-archive",
        action="store_true",
        dest="legacy_score_archive",
        default=False,
        help="Opt in to legacy archival of records with score < 70 "
        "(score is otherwise diagnostic only)",
    )
    dedup_parser.set_defaults(func=_cli_dedup)

    # --- checkpoint ---
    cp_parser = subparsers.add_parser("checkpoint", help="Checkpoint operations")
    cp_subparsers = cp_parser.add_subparsers(dest="cp_command", required=True)

    # Shared --output-dir parent parser for all checkpoint subcommands
    cp_output_parent = argparse.ArgumentParser(add_help=False)
    cp_output_parent.add_argument(
        "--output-dir",
        dest="output_dir",
        default=str(Path(__file__).resolve().parent.parent / "output"),
        help="Base output directory",
    )

    # checkpoint write
    cp_write = cp_subparsers.add_parser(
        "write", help="Write a phase checkpoint", parents=[cp_output_parent],
    )
    cp_write.add_argument(
        "phase",
        choices=VALID_CHECKPOINT_PHASES,
        help="Pipeline phase name",
    )
    cp_write.add_argument("--count", type=int, required=True, help="Item count")
    cp_write.set_defaults(func=_cli_checkpoint_write)

    # checkpoint validate
    cp_validate = cp_subparsers.add_parser(
        "validate", help="Validate a phase checkpoint", parents=[cp_output_parent],
    )
    cp_validate.add_argument(
        "phase",
        choices=VALID_CHECKPOINT_PHASES,
        help="Pipeline phase name",
    )
    cp_validate.set_defaults(func=_cli_checkpoint_validate)

    # checkpoint status
    cp_status = cp_subparsers.add_parser(
        "status", help="Show status of all phases", parents=[cp_output_parent],
    )
    cp_status.set_defaults(func=_cli_checkpoint_status)

    # checkpoint clear
    cp_clear = cp_subparsers.add_parser(
        "clear", help="Clear all checkpoints", parents=[cp_output_parent],
    )
    cp_clear.set_defaults(func=_cli_checkpoint_clear)

    # --- list-active-role-types ---
    list_rt_parser = subparsers.add_parser(
        "list-active-role-types",
        help="Extract active role-type slugs from context.md ## Target",
    )
    list_rt_parser.add_argument(
        "--context-path",
        dest="context_path",
        default="context.md",
        help="Path to context.md (default: context.md)",
    )
    list_rt_parser.set_defaults(func=_cli_list_active_role_types)

    # --- verify-clean-working-tree ---
    vcwt_parser = subparsers.add_parser(
        "verify-clean-working-tree",
        help="Verify all files under verified path are committed in git",
    )
    vcwt_parser.add_argument(
        "--verified-path",
        dest="verified_path",
        default="output/verified",
        help="Path to verified directory (default: output/verified)",
    )
    vcwt_parser.set_defaults(func=_cli_verify_batch_committed)

    # --- verify-channels-dispatched ---
    vcd_parser = subparsers.add_parser(
        "verify-channels-dispatched",
        help="Verify all 5 search channel .done files exist with today's mtime",
    )
    vcd_parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default="output",
        help="Path to output directory (default: output)",
    )
    vcd_parser.add_argument(
        "--run-date",
        dest="run_date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Expected run date YYYY-MM-DD (default: today)",
    )
    vcd_parser.set_defaults(func=_cli_verify_channels_dispatched)

    # --- verify-session-state-updated ---
    vssu_parser = subparsers.add_parser(
        "verify-session-state-updated",
        help="Verify session-state.md exists and was modified on the run date",
    )
    vssu_parser.add_argument(
        "--session-state-path",
        dest="session_state_path",
        default="session-state.md",
        help="Path to session-state.md (default: session-state.md)",
    )
    vssu_parser.add_argument(
        "--run-date",
        dest="run_date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Expected run date YYYY-MM-DD (default: today)",
    )
    vssu_parser.set_defaults(func=_cli_verify_session_state_updated)

    # --- check-session-resume ---
    csr_parser = subparsers.add_parser(
        "check-session-resume",
        help="Exit 1 if a digest was already sent today, else exit 0",
    )
    csr_parser.add_argument(
        "--status-path",
        dest="status_path",
        default="output/digests/_status.json",
        help="Path to _status.json (default: output/digests/_status.json)",
    )
    csr_parser.add_argument(
        "--run-date",
        dest="run_date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date to check against YYYY-MM-DD (default: today)",
    )
    csr_parser.set_defaults(func=_cli_check_session_resume)

    # --- verify-state-clean ---
    vsc_parser = subparsers.add_parser(
        "verify-state-clean",
        help="Exit 0 if state.json is clean/complete (or absent); exit 1 with a stderr diagnostic if corrupt or partial",
    )
    vsc_parser.add_argument("--state", default="state.json")
    vsc_parser.set_defaults(func=_cli_verify_state_clean)

    # --- check-model-settings ---
    cms_parser = subparsers.add_parser(
        "check-model-settings",
        help="Validate model: field in all .claude/agents/*.md frontmatter",
    )
    cms_parser.add_argument(
        "--agents-dir",
        dest="agents_dir",
        default=".claude/agents",
        help="Path to agents directory (default: .claude/agents)",
    )
    cms_parser.add_argument(
        "--exclude",
        dest="exclude",
        default="",
        help="Comma-separated agent filenames to skip validation",
    )
    cms_parser.set_defaults(func=_cli_check_model_settings)

    # --- validate-schema ---
    vs_parser = subparsers.add_parser(
        "validate-schema",
        help="Validate all verified JSONs against the canonical 10-field schema",
    )
    vs_parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=str(Path(__file__).resolve().parent.parent / "output"),
        help="Base output directory (default: output/ relative to project root)",
    )
    vs_parser.set_defaults(func=_handle_validate_schema)

    # --- migrate-schema ---
    ms_parser = subparsers.add_parser(
        "migrate-schema",
        help="Migrate all verified/archive JSONs to the canonical 10-field schema",
    )
    ms_parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=str(Path(__file__).resolve().parent.parent / "output"),
        help="Base output directory (default: output/ relative to project root)",
    )
    ms_parser.set_defaults(func=_handle_migrate_schema)

    # --- check-dashboard-url ---
    cdu_parser = subparsers.add_parser(
        "check-dashboard-url",
        help="Verify Dashboard: URL is present and non-empty in context.md",
    )
    cdu_parser.add_argument(
        "--context-path",
        dest="context_path",
        default="context.md",
        help="Path to context.md (default: context.md)",
    )
    cdu_parser.set_defaults(func=_cli_check_dashboard_url)

    # --- verify-session-state-written ---
    vssw_parser = subparsers.add_parser(
        "verify-session-state-written",
        help="Verify session-state.md contains an entry for the run date",
    )
    vssw_parser.add_argument(
        "--session-state-path",
        dest="session_state_path",
        default="output/session-state.md",
        help="Path to session-state.md (default: output/session-state.md)",
    )
    vssw_parser.add_argument(
        "--run-date",
        dest="run_date",
        required=True,
        help="Expected run date YYYY-MM-DD",
    )
    vssw_parser.set_defaults(func=_cli_verify_session_state_written)

    # --- increment-dispatch-counter ---
    idc_parser = subparsers.add_parser(
        "increment-dispatch-counter",
        help="Increment the dispatch counter in session-state.md ## Budget section",
    )
    idc_parser.add_argument(
        "--session-state-path",
        dest="session_state_path",
        default="output/session-state.md",
    )
    idc_parser.set_defaults(func=_cli_increment_dispatch_counter)

    # --- check-dispatch-budget ---
    cdb_parser = subparsers.add_parser(
        "check-dispatch-budget",
        help="Check if dispatch count is under the ceiling",
    )
    cdb_parser.add_argument(
        "--session-state-path",
        dest="session_state_path",
        default="output/session-state.md",
    )
    cdb_parser.add_argument(
        "--ceiling",
        type=int,
        default=25,
    )
    cdb_parser.set_defaults(func=_cli_check_dispatch_budget)

    # --- validate-url-type ---
    vut_parser = subparsers.add_parser(
        "validate-url-type",
        help="Classify a URL as source (ATS), aggregator, or unknown",
    )
    vut_parser.add_argument(
        "--url",
        required=True,
        help="The URL to classify",
    )
    vut_parser.set_defaults(func=_cli_validate_url_type)

    # --- verify-before-archive ---
    vba_parser = subparsers.add_parser(
        "verify-before-archive",
        help="Check if a job URL is still live via HTTP HEAD",
    )
    vba_parser.add_argument(
        "--input",
        required=True,
        help="Path to verified JSON file",
    )
    vba_parser.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Write verdict to the JSON file's active_status field (default: read-only check)",
    )
    vba_parser.set_defaults(func=_cli_verify_before_archive)

    # --- validate-presentation ---
    vp_parser = subparsers.add_parser(
        "validate-presentation",
        help="Validate verified JSONs are presentation-ready",
    )
    vp_parser.add_argument(
        "--output-dir", dest="output_dir",
        default=str(Path(__file__).resolve().parent.parent / "output"),
        help="Base output directory",
    )
    vp_parser.add_argument(
        "--role-types", required=True,
        help="Comma-separated role type slugs to validate",
    )
    vp_parser.set_defaults(func=_cli_validate_presentation)

    # --- validate-run ---
    vr_parser = subparsers.add_parser(
        "validate-run",
        help="Validate the exact presentation set of a current run manifest",
    )
    vr_parser.add_argument("--manifest", required=True, help="Path to _run-manifest.json")
    vr_parser.add_argument(
        "--today", default=None, help="Override today's date YYYY-MM-DD (default: system date)"
    )
    vr_parser.add_argument(
        "--max-age-days", dest="max_age_days", type=int, default=2,
        help="Maximum manifest age in days (default: 2)",
    )
    vr_parser.set_defaults(func=_cli_validate_run)

    # --- filter-presentation (hard-gate enforcement) ---
    fp_parser = subparsers.add_parser(
        "filter-presentation",
        help="Suppress hard-gated jobs from the chat-facing set (flag, not archive)",
    )
    fp_parser.add_argument(
        "--output-dir", dest="output_dir",
        default=str(Path(__file__).resolve().parent.parent / "output"),
        help="Base output directory",
    )
    fp_parser.add_argument(
        "--role-types", required=True,
        help="Comma-separated role type slugs to scan",
    )
    fp_parser.add_argument(
        "--out", dest="out", default=None,
        help="Path to write the suppressed-job list (default output/_hard_gated.json)",
    )
    fp_parser.set_defaults(func=_cli_filter_presentation)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

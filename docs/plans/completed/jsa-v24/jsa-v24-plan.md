# Plan: JSA V24 — Schema-First Fix

## Overview

Targeted patch addressing the root cause of chronic schema inconsistency across 8+ JSA versions. Implements a canonical 10-field verified JSON schema with normalize-on-write, promotes search-verify from Haiku to Sonnet tier, adds blocking gate-check semantics between phases, fixes dedup auto-scoping to active role types, and adds a migration script for backward compatibility.

**Approach:** Schema-First Fix (Three-Layer implementation)
- **Layer 1:** Scripts — manage_state.py (validate-schema, dedup fix, slug fix, migration)
- **Layer 2:** Orchestration + Config — search-verify Sonnet, canonical schema contract, blocking gates
- **Layer 3:** Validation + Preflight — preflight schema checks, integration tests

## Context Budget

1. **Parent may only read status files and dispatch subagents.** Parent must NEVER execute `manage_state.py` directly (V18 regression). All script invocations are subagent-delegated.
2. **All `manage_state.py` invocations are subagent-delegated.** Gate-check, migration, and validation commands run inside dispatched subagents, not in the parent context.
3. **Step 27 must dispatch a subagent** to run `migrate-schema` and `validate-schema` against actual V23 data. Parent reads only the subagent's status output.

## Files to Modify

### Layer 1 (Scripts)
- `scripts/manage_state.py` — New subcommands: validate-schema, migrate-schema. Fixes: _extract_score(), dedup auto-scoping + safety bound, _slugify() collapse
- `tests/helpers.py` — New: shared `_make_job(**overrides)` factory for all test files (replaces `_make_valid_job`, `_make_job_with_score_field`, `_make_canonical_job`, `_make_verified_json`)
- `tests/test_manage_state.py` — New: TestValidateSchema (4 tests), TestSlugExtraction (3 tests), TestMigrateSchema (4 tests)
- `tests/test_manage_state_dedup.py` — New: TestDedupScoreField (2 tests), TestDedupAutoScoping (2 tests)

### Layer 2 (Orchestration + Config)
- `.claude/agents/search-verify.md` — model: haiku → model: sonnet
- `references/subagent-search-verify.md` — New: Output Schema Contract section (10-field JSON)
- `references/orchestration.md` — New: Schema Validation Gate, blocking gate semantics upgrade
- `CLAUDE.md` — Agent Model Tiers table: search-verify moved to Sonnet tier
- `tests/test_claude_md.py` — New: test_search_verify_model_is_sonnet
- `tests/test_workflow.py` — New: TestGateBlocking (4 tests)

### Layer 3 (Validation + Preflight)
- `scripts/preflight.sh` — New: schema validation check, search-verify model tier check
- `tests/test_preflight.py` — New: TestPreflightSchemaValidation (3 tests)
- `tests/test_workflow.py` — New: TestSchemaValidationGate (3 tests), TestDedupScoping (2 tests)

## Implementation Steps

---

## Phase 1: Layer 1 — Scripts (manage_state.py)

### Step 0: Create shared test helpers module

**File:** `tests/helpers.py` (new file)
**Action:** Create

```python
"""Shared test helpers for JSA V24 tests.

All test files import from here instead of defining their own factories.
Single source of truth for verified job JSON construction and script invocation.
"""

import json
import subprocess
import sys
from pathlib import Path

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _make_job(**overrides) -> dict:
    """Single factory for verified job JSON. All 10 canonical fields with defaults."""
    defaults = {
        "job_id": "job-001", "title": "Engineer", "company": "Acme",
        "job_url": "https://example.com/job", "role_type": "ai-engineer",
        "score": 85, "source_channel": "direct-career-pages",
        "run_date": "2026-02-25", "location": "Remote", "status": "verified",
    }
    defaults.update(overrides)
    return defaults


def _write_job(dir_path: Path, filename: str, job_dict: dict) -> Path:
    """Write a job dict as JSON to a file in the given directory."""
    dir_path.mkdir(parents=True, exist_ok=True)
    filepath = dir_path / filename
    filepath.write_text(json.dumps(job_dict, indent=2), encoding="utf-8")
    return filepath


def _run_dedup(
    output_dir: str,
    *,
    role_types: str | None = None,
    auto_scope: bool = False,
    run_date: str | None = None,
    dry_run: bool = False,
) -> subprocess.CompletedProcess:
    """Unified dedup helper supporting explicit role-types, auto-scope, and dry-run."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "dedup",
        "--output-dir",
        output_dir,
    ]
    if role_types is not None:
        cmd.extend(["--role-types", role_types])
    if auto_scope:
        cmd.append("--auto-scope")
    if run_date is not None:
        cmd.extend(["--run-date", run_date])
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, capture_output=True, text=True)
```

**Verify:**
- File exists: `ls tests/helpers.py`
- Lint: `ruff check tests/helpers.py`

---

### Step 1: Write failing test for `validate-schema` subcommand

**File:** `tests/test_manage_state.py` (append new class at end of file)
**Action:** Create

```python
# ---- append to: tests/test_manage_state.py ----


# ---------------------------------------------------------------------------
# TestValidateSchema
# ---------------------------------------------------------------------------

# Import CANONICAL_FIELDS from manage_state.py as single source of truth.
# Add scripts/ to sys.path if needed, or use:
#   from manage_state import CANONICAL_FIELDS
# For subprocess-based tests, REQUIRED_FIELDS is derived from the canonical constant:
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from manage_state import CANONICAL_FIELDS  # noqa: E402
REQUIRED_FIELDS = list(CANONICAL_FIELDS.keys())


def _run_validate_schema(output_dir: str) -> subprocess.CompletedProcess:
    """Run validate-schema subcommand against a given output directory."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "validate-schema",
        "--output-dir",
        output_dir,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


from helpers import _make_job, _write_job, _run_dedup  # noqa: E402


class TestValidateSchema:
    """Tests for the validate-schema subcommand of manage_state.py."""

    def test_validate_schema_all_pass(self, tmp_path: Path) -> None:
        """2 valid JSONs with all 10 required fields -> exit 0."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True, exist_ok=True)

        for i in range(2):
            job = _make_job(job_id=f"job-00{i}", title=f"Engineer {i}")
            (role_dir / f"job-{i:03d}.json").write_text(
                json.dumps(job), encoding="utf-8"
            )

        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0, (
            f"expected exit 0 for all-valid JSONs, got {result.returncode}.\n"
            f"stderr: {result.stderr}\nstdout: {result.stdout}"
        )

    def test_validate_schema_missing_field(self, tmp_path: Path) -> None:
        """JSON missing `score` -> exit 1 with error listing missing field."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True, exist_ok=True)

        job = _make_job()
        del job["score"]
        (role_dir / "bad-job.json").write_text(json.dumps(job), encoding="utf-8")

        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1, (
            f"expected exit 1 for missing 'score', got {result.returncode}"
        )
        combined = result.stdout + result.stderr
        assert "score" in combined, (
            f"expected 'score' mentioned in output, got:\n{combined}"
        )

    def test_validate_schema_wrong_type(self, tmp_path: Path) -> None:
        """`score` is string instead of int -> exit 1 with error."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True, exist_ok=True)

        job = _make_job()
        job["score"] = "85"  # string, not int
        (role_dir / "bad-type.json").write_text(json.dumps(job), encoding="utf-8")

        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1, (
            f"expected exit 1 for score with wrong type, got {result.returncode}"
        )
        combined = result.stdout + result.stderr
        assert "score" in combined, (
            f"expected 'score' mentioned in output, got:\n{combined}"
        )

    def test_validate_schema_empty_dir(self, tmp_path: Path) -> None:
        """No JSONs -> exit 0 (vacuously true)."""
        output_dir = tmp_path / "output"
        verified_dir = output_dir / "verified"
        verified_dir.mkdir(parents=True, exist_ok=True)

        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0, (
            f"expected exit 0 for empty verified dir, got {result.returncode}.\n"
            f"stderr: {result.stderr}"
        )
```

**Verify:**
- Test: `pytest tests/test_manage_state.py::TestValidateSchema -v` -> FAIL (subcommand not yet registered)

---

### Step 2: Implement `validate-schema` subcommand in manage_state.py

**File:** `scripts/manage_state.py` (modify)
**Action:** Modify

Insert before the `# check-dashboard-url subcommand` comment block (around line 856):

```python
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
To add an 11th field: add it here — all downstream consumers pick it up automatically."""

CANONICAL_FIELD_DEFAULTS: dict[str, Any] = {
    field: 0 if expected_type is int else ""
    for field, expected_type in CANONICAL_FIELDS.items()
}

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
```

Register in `main()` — insert before the `# --- check-dashboard-url ---` parser block:

```python
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
```

**Verify:**
- Test: `pytest tests/test_manage_state.py::TestValidateSchema -v` -> PASS
- Lint: `ruff check scripts/manage_state.py`

---

### Step 3: Write failing test for dedup `score` field fix

**File:** `tests/test_manage_state_dedup.py` (append at end of file)
**Action:** Create

```python
# ---- append to: tests/test_manage_state_dedup.py ----


# ---------------------------------------------------------------------------
# TestDedupScoreField
# ---------------------------------------------------------------------------


# Use shared helpers from tests/helpers.py (imported at top of file)
from helpers import _make_job, _write_job, _run_dedup  # noqa: E402


class TestDedupScoreField:
    """Tests that dedup sorts/filters by canonical top-level `score` field only."""

    def test_dedup_reads_canonical_score(self, tmp_path: Path) -> None:
        """Job with {"score": 85} (canonical) -> dedup sorts correctly by score."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job_high = _make_job(
            company="SameCo", title="Strategist", score=85,
            job_url="https://example.com/high", role_type="ai-engineer",
        )
        job_low = _make_job(
            company="SameCo", title="Strategist", score=60,
            job_url="https://example.com/low", role_type="ai-engineer",
        )
        _write_job(verified / "ai-engineer", "sameco-high.json", job_high)
        _write_job(verified / "ai-engineer", "sameco-low.json", job_low)

        result = _run_dedup(str(output_dir), role_types="ai-engineer")
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        assert (verified / "ai-engineer" / "sameco-high.json").exists(), (
            "job with canonical score=85 should be kept"
        )
        assert not (verified / "ai-engineer" / "sameco-low.json").exists(), (
            "job with canonical score=60 should be archived as duplicate"
        )

    def test_dedup_ignores_nested_score_variants(self, tmp_path: Path) -> None:
        """Dedup uses top-level score (85), not nested scoring_breakdown.overall_score (90)."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job_a = _make_job(
            company="NestCo", title="Analyst", score=85,
            job_url="https://example.com/a", role_type="ai-engineer",
            scoring_breakdown={"overall_score": 90, "experience": 80},
        )
        job_b = _make_job(
            company="NestCo", title="Analyst", score=90,
            job_url="https://example.com/b", role_type="ai-engineer",
        )
        _write_job(verified / "ai-engineer", "nestco-a.json", job_a)
        _write_job(verified / "ai-engineer", "nestco-b.json", job_b)

        result = _run_dedup(str(output_dir), role_types="ai-engineer")
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        assert (verified / "ai-engineer" / "nestco-b.json").exists(), (
            "job with canonical score=90 should be kept"
        )
        assert not (verified / "ai-engineer" / "nestco-a.json").exists(), (
            "job with canonical score=85 should be archived"
        )
```

**Verify:**
- Test: `pytest tests/test_manage_state_dedup.py::TestDedupScoreField -v` -> FAIL

---

### Step 4: Fix `_extract_score()` to use canonical `score` field only

**File:** `scripts/manage_state.py` (modify)
**Action:** Modify

**Old (lines 100-118):**
```python
def _extract_score(verified_json: dict[str, Any]) -> int:
    """Extract score from verified JSON, handling multiple schema formats."""
    # 1. Try score_breakdown.total (overrides top-level for founders-associate)
    sb = verified_json.get("score_breakdown")
    if isinstance(sb, dict) and "total" in sb:
        return int(sb["total"])
    # 2. Try scoring.total_score (direct-career-pages, web-search-discovery)
    scoring = verified_json.get("scoring")
    if isinstance(scoring, dict) and "total_score" in scoring:
        return int(scoring["total_score"])
    # 3. Try top-level score
    score = verified_json.get("score")
    if isinstance(score, int):
        return score
    if isinstance(score, float):
        return int(score)
    if isinstance(score, dict) and "total" in score:
        return int(score["total"])
    return 0
```

**New:**
```python
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
```

Also fix sorting key lambdas that reference `overall_score`:

**Old (line 363):**
```python
        group.sort(key=lambda j: (-j.get("overall_score", 0), str(j["_filepath"])))
```
**New:**
```python
        group.sort(key=lambda j: (-_extract_score(j), str(j["_filepath"])))
```

**Old (line 384):**
```python
        group.sort(key=lambda j: (-j.get("overall_score", 0), str(j["_filepath"])))
```
**New:**
```python
        group.sort(key=lambda j: (-_extract_score(j), str(j["_filepath"])))
```

**Old (lines 465-469):**
```python
    # --- 3. Score threshold ---
    remaining = [j for j in jobs if j["_filepath"] not in to_archive]
    for job in remaining:
        score = job.get("overall_score", 0)
        if score < SCORE_THRESHOLD:
            to_archive[job["_filepath"]] = job
```
**New:**
```python
    # --- 3. Score threshold ---
    remaining = [j for j in jobs if j["_filepath"] not in to_archive]
    for job in remaining:
        if _extract_score(job) < SCORE_THRESHOLD:
            to_archive[job["_filepath"]] = job
```

**Verify:**
- Test: `pytest tests/test_manage_state_dedup.py::TestDedupScoreField -v` -> PASS

---

### Step 5: Write failing test for dedup role-type auto-scoping

**File:** `tests/test_manage_state_dedup.py` (append)
**Action:** Create

```python
# ---- append to: tests/test_manage_state_dedup.py ----


# ---------------------------------------------------------------------------
# TestDedupAutoScoping
# ---------------------------------------------------------------------------

TODAY = "2026-02-25"
OLD_DATE = "2026-01-01"


# Use shared helpers from tests/helpers.py (already imported above):
# from helpers import _make_job, _write_job, _run_dedup


class TestDedupAutoScoping:
    """Tests for dedup auto-scoping by today's run_date and safety bound."""

    def test_dedup_only_processes_active_role_types(self, tmp_path: Path) -> None:
        """Active role types (run_date==today) processed; stale ones skipped."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        active_job = _make_job(
            company="ActiveCo", title="Agent Engineer", score=55,
            job_url="https://example.com/active", role_type="ai-engineer",
            run_date=TODAY,
        )
        _write_job(verified / "ai-engineer", "activeco-eng.json", active_job)

        stale_job = _make_job(
            company="StaleCo", title="Old Role", score=55,
            job_url="https://example.com/stale", role_type="stale-role",
            run_date=OLD_DATE,
        )
        _write_job(verified / "stale-role", "staleco-old.json", stale_job)

        result = _run_dedup(str(output_dir), auto_scope=True, run_date=TODAY)
        assert result.returncode == 0, (
            f"dedup auto-scope failed: {result.stderr}\nstdout: {result.stdout}"
        )

        # Active role's low-score job should be archived
        assert not (verified / "ai-engineer" / "activeco-eng.json").exists(), (
            "low-score job in active role type should be archived"
        )

        # Stale role's job should be untouched
        assert (verified / "stale-role" / "staleco-old.json").exists(), (
            "job in stale role type must not be processed or archived"
        )

    def test_dedup_safety_bound_aborts(self, tmp_path: Path) -> None:
        """If dedup would archive >50% of jobs in a role type -> abort, archive nothing."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        # 2 jobs total, both below threshold -> 100% archive rate -> abort
        for i in range(2):
            low_job = _make_job(
                company=f"LowCo{i}", title=f"Temp{i}", score=40,
                job_url=f"https://example.com/low{i}", role_type="ai-engineer",
                run_date=TODAY,
            )
            _write_job(verified / "ai-engineer", f"lowco{i}-temp.json", low_job)

        result = _run_dedup(str(output_dir), auto_scope=True, run_date=TODAY)
        assert result.returncode == 1, (
            f"dedup with 100% archive rate should fail safety bound (exit 1), "
            f"got {result.returncode}.\nstdout: {result.stdout}"
        )

        # Files must be untouched when safety bound aborts
        assert (verified / "ai-engineer" / "lowco0-temp.json").exists(), (
            "safety-bound abort must not archive any files"
        )
        assert (verified / "ai-engineer" / "lowco1-temp.json").exists(), (
            "safety-bound abort must not archive any files"
        )

        combined = result.stdout + result.stderr
        assert "safety" in combined.lower() or "bound" in combined.lower(), (
            f"expected safety bound error message, got:\n{combined}"
        )
```

**Verify:**
- Test: `pytest tests/test_manage_state_dedup.py::TestDedupAutoScoping -v` -> FAIL (--auto-scope and --run-date flags not yet in dedup)

---

### Step 6: Implement dedup auto-scoping and safety bound

**File:** `scripts/manage_state.py` (modify)
**Action:** Modify

Add helper functions before `_cli_dedup`:

```python
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
) -> list[str]:
    """Check the safety bound per role type.

    Returns error strings if any role type would have >SAFETY_BOUND_PCT%
    of its jobs archived. Empty list = safe to proceed.
    """
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
        if pct > SAFETY_BOUND_PCT:
            errors.append(
                f"Safety bound exceeded for {role!r}: would archive "
                f"{archived_count}/{total} ({pct:.0f}%)"
            )
    return errors
```

Replace entire `_cli_dedup` function (lines 414-481):

Replace the entire `_cli_dedup` function body (lines 414-481) with:


```python
def _cli_dedup(args: argparse.Namespace) -> None:
    """CLI dedup subcommand: cross-role + same-URL dedup + score threshold.

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
            summary = {"total_input": 0, "archived": 0, "remaining": 0}
            sys.stdout.write(json.dumps(summary, indent=2) + "\n")
            return
        role_types = [rt.strip() for rt in args.role_types.split(",") if rt.strip()]
    else:
        role_types = None

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
        url = job.get("job_url", "").lower().strip()
        if not url:
            continue
        role = job["_role"]
        url_key = f"{role}:{url}"
        jobs_by_url.setdefault(url_key, []).append(job)

    same_url_pairs = _find_same_url_duplicates(jobs_by_url)
    for _keeper, dup in same_url_pairs:
        to_archive[dup["_filepath"]] = dup

    # --- 3. Score threshold ---
    remaining = [j for j in jobs if j["_filepath"] not in to_archive]
    for job in remaining:
        if _extract_score(job) < SCORE_THRESHOLD:
            to_archive[job["_filepath"]] = job

    # --- 4. Safety bound (all modes — use --no-safety-bound to opt out) ---
    no_safety_bound: bool = getattr(args, "no_safety_bound", False)
    if not no_safety_bound:
        bound_errors = _check_safety_bound(jobs, to_archive)
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

    summary = {
        "total_input": len(jobs),
        "archived": len(archive_jobs),
        "remaining": len(jobs) - len(archive_jobs),
        "active_role_types": len(role_types) if role_types is not None else "all",
        "stale_role_types_skipped": len(stale_role_types),
    }
    sys.stdout.write(json.dumps(summary, indent=2) + "\n")
```

Register `--auto-scope` and `--run-date` on dedup parser in `main()`:

**Old dedup parser (lines 983-1002):**
```python
    dedup_parser.add_argument(
        "--role-types",
        type=str,
        default=None,
        help="Comma-separated role type slugs to process",
    )
    dedup_parser.set_defaults(func=_cli_dedup)
```

**New (append after --role-types):**
```python
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
    dedup_parser.set_defaults(func=_cli_dedup)
```

**Verify:**
- Test: `pytest tests/test_manage_state_dedup.py::TestDedupAutoScoping -v` -> PASS

---

### Step 7: Write failing test for `list-active-role-types` slug fix

**File:** `tests/test_manage_state.py` (append)
**Action:** Create

```python
# ---- append to: tests/test_manage_state.py ----


# ---------------------------------------------------------------------------
# TestSlugExtraction
# ---------------------------------------------------------------------------


def _run_list_active_role_types(context_path: str) -> subprocess.CompletedProcess:
    """Run list-active-role-types subcommand."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "list-active-role-types",
        "--context-path",
        context_path,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestSlugExtraction:
    """Tests that list-active-role-types produces clean kebab-case slugs."""

    def test_slug_clean_format(self, tmp_path: Path) -> None:
        """Directory named `ai-engineer` -> output slug is `ai-engineer`."""
        context_md = tmp_path / "context.md"
        context_md.write_text(
            "# Context\n\n## Target\n- ai-engineer\n\n## Industries\n- AI\n",
            encoding="utf-8",
        )
        result = _run_list_active_role_types(str(context_md))
        assert result.returncode == 0, f"failed: {result.stderr}"
        slugs = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        assert slugs == ["ai-engineer"], f"expected ['ai-engineer'], got {slugs}"

    def test_slug_from_messy_directory(self, tmp_path: Path) -> None:
        """'AI Engineer Jobs' -> 'ai-engineer-jobs'."""
        context_md = tmp_path / "context.md"
        context_md.write_text(
            "# Context\n\n## Target\n- AI Engineer Jobs\n\n## Industries\n- AI\n",
            encoding="utf-8",
        )
        result = _run_list_active_role_types(str(context_md))
        assert result.returncode == 0, f"failed: {result.stderr}"
        slugs = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        assert slugs == ["ai-engineer-jobs"], f"expected ['ai-engineer-jobs'], got {slugs!r}"

    def test_slug_dedup_consistent(self, tmp_path: Path) -> None:
        """Same directory always produces same slug across two invocations."""
        context_md = tmp_path / "context.md"
        context_md.write_text(
            "# Context\n\n## Target\n- Community Manager\n- DevRel & Advocacy\n\n## Industries\n- Startups\n",
            encoding="utf-8",
        )

        result1 = _run_list_active_role_types(str(context_md))
        result2 = _run_list_active_role_types(str(context_md))

        assert result1.returncode == 0
        assert result2.returncode == 0

        slugs1 = result1.stdout.strip().splitlines()
        slugs2 = result2.stdout.strip().splitlines()

        assert slugs1 == slugs2, f"not deterministic: {slugs1!r} vs {slugs2!r}"
        assert slugs1 == ["community-manager", "devrel-advocacy"], (
            f"expected ['community-manager', 'devrel-advocacy'], got {slugs1!r}"
        )
```

**Verify:**
- Test: `pytest tests/test_manage_state.py::TestSlugExtraction -v` -> FAIL

---

### Step 8: Fix `_slugify` to collapse multiple hyphens

**File:** `scripts/manage_state.py` (modify)
**Action:** Modify

**Old (lines 571-581):**
```python
def _slugify(name: str) -> str:
    """Convert a role type name to a kebab-case slug.

    Example: "AI Agent Engineer" -> "ai-agent-engineer"
    """
    slug = name.lower().strip()
    # Replace non-alphanumeric characters (except hyphens) with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    return slug
```

**New:**
```python
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
```

**Verify:**
- Test: `pytest tests/test_manage_state.py::TestSlugExtraction -v` -> PASS

---

### Step 9: Write failing test for `migrate-schema` subcommand

**File:** `tests/test_manage_state.py` (append)
**Action:** Create

```python
# ---- append to: tests/test_manage_state.py ----


# ---------------------------------------------------------------------------
# TestMigrateSchema
# ---------------------------------------------------------------------------

# Derive from single source of truth (already imported above)
from manage_state import CANONICAL_FIELD_DEFAULTS as CANONICAL_DEFAULTS  # noqa: E402


def _run_migrate_schema(output_dir: str) -> subprocess.CompletedProcess:
    """Run migrate-schema subcommand."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "migrate-schema",
        "--output-dir",
        output_dir,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestMigrateSchema:
    """Tests for the migrate-schema subcommand."""

    def test_migrate_adds_missing_fields(self, tmp_path: Path) -> None:
        """JSON with only title, company -> after migration has all 10 required fields."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True, exist_ok=True)

        partial_job = {"title": "Engineer", "company": "Acme Corp"}
        job_file = role_dir / "partial.json"
        job_file.write_text(json.dumps(partial_job), encoding="utf-8")

        result = _run_migrate_schema(str(output_dir))
        assert result.returncode == 0, f"migrate-schema failed: {result.stderr}"

        migrated = json.loads(job_file.read_text(encoding="utf-8"))
        for field in CANONICAL_DEFAULTS:
            assert field in migrated, f"field '{field}' should be present after migration"
        assert migrated["title"] == "Engineer"
        assert migrated["company"] == "Acme Corp"
        assert migrated["job_id"] == ""
        assert migrated["score"] == 0
        assert isinstance(migrated["score"], int)

    def test_migrate_normalizes_score(self, tmp_path: Path) -> None:
        """JSON with overall_score: 85 but no score -> after migration score: 85."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True, exist_ok=True)

        legacy_job = {
            "title": "Analyst", "company": "LegacyCo",
            "overall_score": 85, "job_url": "https://example.com",
        }
        job_file = role_dir / "legacy.json"
        job_file.write_text(json.dumps(legacy_job), encoding="utf-8")

        result = _run_migrate_schema(str(output_dir))
        assert result.returncode == 0

        migrated = json.loads(job_file.read_text(encoding="utf-8"))
        assert migrated["score"] == 85
        assert isinstance(migrated["score"], int)
        assert migrated.get("overall_score") == 85  # preserved

    def test_migrate_preserves_optional_fields(self, tmp_path: Path) -> None:
        """JSON with salary, description -> preserved after migration."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True, exist_ok=True)

        job = {"title": "Manager", "company": "OptCo", "score": 75,
               "salary": "$120k", "description": "A great role."}
        job_file = role_dir / "extras.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        result = _run_migrate_schema(str(output_dir))
        assert result.returncode == 0

        migrated = json.loads(job_file.read_text(encoding="utf-8"))
        assert migrated.get("salary") == "$120k"
        assert migrated.get("description") == "A great role."

    def test_migrate_idempotent(self, tmp_path: Path) -> None:
        """Running migrate-schema twice -> no changes second time."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True, exist_ok=True)

        canonical_job = {
            "job_id": "acme-eng-001", "title": "Engineer", "company": "Acme",
            "job_url": "https://example.com/job", "role_type": "ai-engineer",
            "score": 85, "source_channel": "direct-career-pages",
            "run_date": "2026-02-25", "location": "Remote", "status": "verified",
        }
        job_file = role_dir / "canonical.json"
        job_file.write_text(json.dumps(canonical_job, sort_keys=True), encoding="utf-8")

        result1 = _run_migrate_schema(str(output_dir))
        assert result1.returncode == 0
        content_after_first = job_file.read_text(encoding="utf-8")

        result2 = _run_migrate_schema(str(output_dir))
        assert result2.returncode == 0
        content_after_second = job_file.read_text(encoding="utf-8")

        assert content_after_first == content_after_second, (
            "migrate-schema is not idempotent"
        )
        assert "0 modified" in result2.stdout or "already canonical" in result2.stdout
```

**Verify:**
- Test: `pytest tests/test_manage_state.py::TestMigrateSchema -v` -> FAIL

---

### Step 10: Implement `migrate-schema` subcommand

**File:** `scripts/manage_state.py` (modify)
**Action:** Modify

Insert after `_handle_validate_schema` and before `# check-dashboard-url`:

```python
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
    for field, default in CANONICAL_FIELD_DEFAULTS.items():
        if field not in data:
            data[field] = default
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
```

Register in `main()` after `validate-schema`:

```python
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
```

**Verify:**
- Test: `pytest tests/test_manage_state.py::TestMigrateSchema -v` -> PASS

---

### Step 11: Run full Layer 1 test suite

**Verify:**
- Test: `pytest tests/test_manage_state.py tests/test_manage_state_dedup.py -v`
- Lint: `ruff check scripts/manage_state.py`

---

### Step 12: Commit Layer 1

```bash
git add scripts/manage_state.py tests/helpers.py tests/test_manage_state.py tests/test_manage_state_dedup.py
git commit -m "feat(jsa): V24 Layer 1 -- validate-schema, dedup fixes, slug fix, migration"
```

---

## Phase 2: Layer 2 — Orchestration + Configuration

### Step 13: Promote search-verify agent to Sonnet tier

**File:** `.claude/agents/search-verify.md` (modify)
**Action:** Modify

**Old (line 8):**
```
model: haiku
```
**New:**
```
model: sonnet
```

**Note:** `background: true` remains in the search-verify frontmatter. V23 regression (V20-V23, 8-version recurrence) documented background subagent permission failures. Changing `background: true` to `background: false` is deferred to the next version as it affects orchestration dispatch patterns beyond this plan's scope. Acknowledged as known limitation.

**Verify:**
- Test: `grep "model: sonnet" .claude/agents/search-verify.md`

---

### Step 14: Add canonical schema contract to search-verify prompt template

**File:** `references/subagent-search-verify.md` (modify)
**Action:** Modify

Insert new `## Output Schema Contract` section before the existing `## Deduplication` section:

**Old (at the Deduplication section, around line 278):**
```markdown
## Deduplication

**Note:** For deduplication, use the rules in this template, NOT `references/algorithms.md`.

Before writing a verified job file, check existing files in `output/verified/{role_type_slug}/`:
- **Company + Title + Location** must be unique (exact match)
- **Same job from multiple sources:** Keep first found, note additional source
```

**New:**
```markdown
## Output Schema Contract

Every verified JSON written to `output/verified/{role_type_slug}/` MUST contain these 10 fields at the top level. Missing any field is a hard failure -- do not write the file without all 10.

```json
{
  "job_id": "string -- unique identifier (derive as company_slug-title_slug-run_date)",
  "title": "string -- exact job title character-for-character from listing",
  "company": "string -- exact company name as written on their website",
  "job_url": "string -- URL to the job listing (extracted from page, never constructed)",
  "role_type": "string -- role category slug matching the active role type",
  "score": 0,
  "source_channel": "string -- which search channel found this (direct-career-pages | industry-job-boards | jobspy-aggregator | niche-newsletters | web-search-discovery)",
  "run_date": "YYYY-MM-DD",
  "location": "string -- job location as written in the listing",
  "status": "string -- new | updated | unchanged"
}
```

**Score field rule:** `score` MUST be a top-level integer (0-100). No nested score field takes precedence over this value. `scoring_breakdown` may exist for transparency but the top-level `score` is canonical.

**Optional fields:** All other fields in the extended schema are optional. These 10 are mandatory.

---

## Deduplication

**Note:** For deduplication, use the rules in this template, NOT `references/algorithms.md`.

Before writing a verified job file, check existing files in `output/verified/{role_type_slug}/`:
- **Company + Title + Location** must be unique (exact match)
- **Same job from multiple sources:** Keep first found, note additional source
```

**Verify:**
- Test: `grep -c "Output Schema Contract" references/subagent-search-verify.md` -> 1

---

### Step 15: Update orchestration.md with blocking gate-check semantics

**File:** `references/orchestration.md` (modify)
**Action:** Modify

**Change A** — Insert Schema Validation Gate section after the Cross-Role Dedup section (after line ~218). Add:

```markdown
### Schema Validation Gate

After all channels complete and before dedup runs, parent MUST dispatch a gate-check subagent (model: haiku) with mandatory variables (`working_dir`, `output_directory`, `dashboard_url` per HC10) to run schema validation:

```bash
python3 scripts/manage_state.py validate-schema --output-dir output
```

**This gate is BLOCKING.** Parent must check exit code:
- Exit code 0: PASS -- proceed to dedup.
- Exit code non-zero: STOP. Do NOT proceed to dedup. Print: "Schema validation failed -- fix search-verify output before continuing." Re-dispatch gate-check after correction. Do NOT skip.

Gate-check subagent writes result to `.channels/schema-validation.done` with `{"status": "pass"}` or `{"status": "fail", "errors": [...]}`.

**Gate order (post-search, MUST pass before proceeding to dedup):**
1. `verify-channels-dispatched` -- all 5 channels have `.done` files. MUST pass before proceeding. If gate-check fails: re-dispatch gate-check. Do NOT skip.
2. `validate-schema` (Schema Validation Gate above) -- all verified JSONs have 10 required fields. MUST pass before proceeding. If gate-check fails: re-dispatch gate-check. Do NOT skip.
3. `dedup` -- only after both gates above pass.
```

**Change A-2** — Add agent-memory startup note after the Schema Validation Gate section (HC4 regression, 3-version recurrence V14/V17/V19):

```markdown
> **Note:** Startup sequence must include reading agent-memory files (`.claude/regressions/jsa.md`, `.claude/decision-log/jsa-v24.md`) before dispatching any search channels. This is unchanged from V23 orchestration but noted here for regression awareness.
```

**Change B** — Update advisory language in Per-Channel Commit Gate to mandatory (around line 176):

**Old:**
```
Gate fails if `verify-clean-working-tree` reports uncommitted changes. Parent halts until resolved. This enforces incremental commits per-channel (6-version recurrence: V14/V16/V18/V19/V20/V21).
```
**New:**
```
Gate fails if `verify-clean-working-tree` reports uncommitted changes. This gate MUST pass before proceeding to the next channel. If gate-check fails: re-dispatch gate-check. Do NOT skip. This enforces incremental commits per-channel (6-version recurrence: V14/V16/V18/V19/V20/V21).
```

**Change C** — Update Per-Channel Session-State Gate advisory language (around line 196):

**Old:**
```
Gate fails if session-state.md has no entry for this channel. Parent halts until resolved (5-version recurrence: V14/V16/V18/V19/V21).
```
**New:**
```
Gate fails if session-state.md has no entry for this channel. This gate MUST pass before proceeding. If gate-check fails: re-dispatch gate-check. Do NOT skip. (5-version recurrence: V14/V16/V18/V19/V21).
```

**Change D** — Update Channel Verification Gate advisory language (around line 206):

**Old:**
```
This checks that all 5 channels have a `.done` file in `.channels/`. Gate fails if any channel has no `.done` file -- parent re-dispatches that channel (max 1 retry per channel).
```
**New:**
```
This checks that all 5 channels have a `.done` file in `.channels/`. This gate MUST pass before proceeding. If gate-check fails: re-dispatch gate-check. Do NOT skip. Parent re-dispatches any missing channel (max 1 retry per channel).
```

**Verify:**
- Test: `grep -c "Schema Validation Gate" references/orchestration.md` -> 1

---

### Step 16: Update CLAUDE.md Agent Model Tiers table

**File:** `CLAUDE.md` (modify)
**Action:** Modify

**Old (Agent Model Tiers table, around lines 29-35):**
```markdown
| Tier | Model Value | Agents | Rationale |
|------|-------------|--------|-----------|
| Opus | _(parent only)_ | Parent orchestrator | Orchestration decisions, user interaction, context management |
| Sonnet | `sonnet` | brief-generator, digest-email, briefs-html, onboarding | Good writing quality, template-following -- does not need Opus-level reasoning |
| Haiku | `haiku` | search-verify, source-researcher, gate-check | Mechanical work: fetch pages, filter, score against rubric, extract structured data, run verification gates |
```

**New:**
```markdown
| Tier | Model Value | Agents | Rationale |
|------|-------------|--------|-----------|
| Opus | _(parent only)_ | Parent orchestrator | Orchestration decisions, user interaction, context management |
| Sonnet | `sonnet` | brief-generator, digest-email, briefs-html, onboarding, search-verify | Good writing quality and reasoning for verification scoring; template-following |
| Haiku | `haiku` | source-researcher, gate-check | Mechanical work: source discovery, run verification gates, extract structured data |
```

**Verify:**
- Test: `grep "search-verify.*sonnet" CLAUDE.md`

---

### Step 17: Write test for search-verify model tier

**File:** `tests/test_claude_md.py` (append at end of file)
**Action:** Create

**Note:** This pytest-level config grep test intentionally overlaps with Step 21's preflight.sh runtime check. The pytest test catches drift at dev-time (before code is committed); preflight.sh catches it at run-time (before a scheduled run). Both layers are retained as defense-in-depth.

```python
# ---- append to: tests/test_claude_md.py ----


def test_search_verify_model_is_sonnet() -> None:
    """search-verify agent frontmatter must declare model: sonnet (V24 tier promotion)."""
    import re
    agent_path = PROJECT_ROOT / ".claude" / "agents" / "search-verify.md"
    assert agent_path.exists(), f"search-verify.md not found at {agent_path}"
    content = agent_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, "search-verify.md missing YAML frontmatter"
    frontmatter = match.group(1)
    assert re.search(r"^model:\s*sonnet$", frontmatter, re.MULTILINE), (
        "search-verify agent must declare 'model: sonnet' in YAML frontmatter "
        "(V24 tier promotion -- was haiku in V23)"
    )
```

**Verify:**
- Test: `pytest tests/test_claude_md.py::test_search_verify_model_is_sonnet -v` -> PASS (already changed in Step 13)

---

### Step 18: Write test for gate-check blocking semantics

**File:** `tests/test_workflow.py` (append at end of file)
**Action:** Create

```python
# ---- append to: tests/test_workflow.py ----


class TestGateBlocking:
    """Verify orchestration.md uses blocking gate semantics throughout Phase 1."""

    @property
    def _orch(self) -> str:
        orch_path = Path(__file__).resolve().parent.parent / "references" / "orchestration.md"
        return orch_path.read_text(encoding="utf-8")

    def test_orchestration_has_schema_validation_gate(self) -> None:
        """orchestration.md must contain a Schema Validation Gate section."""
        assert "Schema Validation Gate" in self._orch, (
            "orchestration.md missing 'Schema Validation Gate' section"
        )

    def test_must_pass_before_proceeding_appears_for_each_gate(self) -> None:
        """'MUST pass before proceeding' appears at least 3 times."""
        content = self._orch
        count = content.count("MUST pass before proceeding")
        assert count >= 3, (
            f"'MUST pass before proceeding' found {count} times, need >= 3"
        )

    def test_do_not_skip_appears_for_gates(self) -> None:
        """'Do NOT skip' instruction present for gate failures."""
        assert "Do NOT skip" in self._orch, (
            "orchestration.md missing 'Do NOT skip' instruction"
        )

    def test_schema_validation_gate_is_blocking(self) -> None:
        """Schema Validation Gate references validate-schema and uses blocking language."""
        content = self._orch
        gate_start = content.find("Schema Validation Gate")
        assert gate_start != -1
        gate_section = content[gate_start:gate_start + 600]
        assert "validate-schema" in gate_section, (
            "Schema Validation Gate must reference 'validate-schema' command"
        )
        assert "BLOCKING" in gate_section or "MUST pass" in gate_section, (
            "Schema Validation Gate must use BLOCKING or MUST pass language"
        )
```

**Verify:**
- Test: `pytest tests/test_workflow.py::TestGateBlocking -v` -> PASS (already changed in Step 15)

---

### Step 19: Run full Layer 2 verification

**Verify:**
- Test: `pytest tests/test_claude_md.py tests/test_workflow.py -v`
- Lint: `ruff check tests/test_claude_md.py tests/test_workflow.py`

---

### Step 20: Commit Layer 2

```bash
git add .claude/agents/search-verify.md references/subagent-search-verify.md references/orchestration.md CLAUDE.md tests/test_claude_md.py tests/test_workflow.py
git commit -m "feat(jsa): V24 Layer 2 -- search-verify Sonnet, canonical schema contract, blocking gates"
```

---

## Phase 3: Layer 3 — Validation + Preflight

### Step 21: Add schema validation to preflight.sh

**File:** `scripts/preflight.sh` (modify)
**Action:** Modify

Insert new SCHEMA TIER block before the `# Final result` block (around line 305):

```bash
# ===================================================================
# SCHEMA TIER -- verified JSON schema validation checks
# ===================================================================
if [[ "$RUN_ENV" == "true" ]]; then

    # 1. Validate all verified JSONs conform to canonical schema
    if python3 scripts/manage_state.py validate-schema 2>/dev/null; then
        : # schema validation passed
    else
        fail "[PREFLIGHT FAIL] Schema validation failed -- run migrate-schema first"
    fi

    # 2. Verify search-verify agent is on Sonnet tier
    if [[ -f ".claude/agents/search-verify.md" ]]; then
        if ! grep -q "^model: sonnet$" ".claude/agents/search-verify.md"; then
            fail "[PREFLIGHT FAIL] search-verify agent not on Sonnet tier"
        fi
    else
        fail "[PREFLIGHT FAIL] search-verify agent not on Sonnet tier"
    fi

    if [[ "$FAILED" -ne 0 ]]; then
        exit 1
    fi
fi
```

**Verify:**
- Test: Read modified file, confirm checks are present

---

### Step 22: Write test for preflight schema validation check

**File:** `tests/test_preflight.py` (append at end of file)
**Action:** Create

```python
# ---- append to: tests/test_preflight.py ----


class TestPreflightSchemaValidation:
    """Tests for schema validation and model-tier checks added in Step 21."""

    @staticmethod
    def _write_manage_state_stub(scripts_dir: Path, validate_exit: int) -> None:
        import stat as _stat

        manage_state = scripts_dir / "manage_state.py"
        manage_state.write_text(
            textwrap.dedent(f"""\
                #!/usr/bin/env python3
                import sys
                if len(sys.argv) > 1:
                    cmd = sys.argv[1]
                    if cmd == "cleanup":
                        print("cleanup done")
                        sys.exit(0)
                    elif cmd == "dedup":
                        print("dedup done")
                        sys.exit(0)
                    elif cmd == "validate-schema":
                        sys.exit({validate_exit})
                sys.exit(0)
            """),
            encoding="utf-8",
        )
        manage_state.chmod(manage_state.stat().st_mode | _stat.S_IEXEC)

    @staticmethod
    def _write_search_verify_agent(agents_dir: Path, model: str) -> None:
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "search-verify.md").write_text(
            textwrap.dedent(f"""\
                ---
                name: search-verify
                description: Search job sources and verify active listings
                tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
                model: {model}
                background: true
                ---
                You are a search-verify subagent.
            """),
            encoding="utf-8",
        )

    def test_preflight_runs_schema_validation(self, tmp_path: Path) -> None:
        """Mock validate-schema to exit 0 -> preflight passes this check."""
        _setup_passing_tree(tmp_path)
        self._write_manage_state_stub(tmp_path / "scripts", validate_exit=0)
        self._write_search_verify_agent(tmp_path / ".claude" / "agents", "sonnet")
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 0, (
            f"preflight should pass when validate-schema exits 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_preflight_fails_on_invalid_schema(self, tmp_path: Path) -> None:
        """Mock validate-schema to exit 1 -> preflight reports failure."""
        _setup_passing_tree(tmp_path)
        self._write_manage_state_stub(tmp_path / "scripts", validate_exit=1)
        self._write_search_verify_agent(tmp_path / ".claude" / "agents", "sonnet")
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 1, (
            f"preflight should fail when validate-schema exits 1.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "[PREFLIGHT FAIL] Schema validation failed" in combined

    def test_preflight_checks_search_verify_model(self, tmp_path: Path) -> None:
        """Preflight checks for model: sonnet in search-verify agent."""
        _setup_passing_tree(tmp_path)
        self._write_manage_state_stub(tmp_path / "scripts", validate_exit=0)
        self._write_search_verify_agent(tmp_path / ".claude" / "agents", "haiku")
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 1, (
            f"preflight should fail when search-verify is not on Sonnet tier.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "[PREFLIGHT FAIL] search-verify agent not on Sonnet tier" in combined
```

**Verify:**
- Test: `pytest tests/test_preflight.py::TestPreflightSchemaValidation -v` -> PASS

---

### Step 23: Write integration test for schema validation gate

**File:** `tests/test_workflow.py` (append)
**Action:** Create

```python
# ---- append to: tests/test_workflow.py ----


import json
import subprocess


def _run_manage_state(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run manage_state.py with args from cwd."""
    manage_state = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"
    return subprocess.run(
        ["python3", str(manage_state)] + args,
        capture_output=True, text=True, cwd=str(cwd),
    )


# Use shared factory from tests/helpers.py
from helpers import _make_job  # noqa: E402


def _write_verified_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestSchemaValidationGate:
    """Integration test for chained validate-schema -> dedup workflow.

    Note: Unit-level validate-schema tests (missing field, wrong type, empty dir)
    are already covered by TestValidateSchema in test_manage_state.py.
    This class tests only the integration-specific chained workflow.
    """

    def test_dedup_after_validation_uses_canonical_score(self, tmp_path: Path) -> None:
        """Two valid verified JSONs -> dedup sorts by canonical score."""
        verified_dir = tmp_path / "output" / "verified" / "ai-engineer"
        high = _make_job(title="Senior AI Engineer", company="Alpha Corp",
                                   score=85, job_url="https://alpha.com/jobs/senior-ai")
        low = _make_job(title="Junior AI Engineer", company="Beta Corp",
                                  score=60, job_url="https://beta.com/jobs/junior-ai")
        _write_verified_json(verified_dir / "alpha.json", high)
        _write_verified_json(verified_dir / "beta.json", low)

        validate_result = _run_manage_state(
            ["validate-schema", "--output-dir", str(tmp_path / "output")], cwd=tmp_path,
        )
        assert validate_result.returncode == 0

        dedup_result = _run_manage_state(
            ["dedup", "--output-dir", str(tmp_path / "output"), "--role-types", "ai-engineer"],
            cwd=tmp_path,
        )
        assert dedup_result.returncode == 0
```

**Verify:**
- Test: `pytest tests/test_workflow.py::TestSchemaValidationGate -v` -> PASS

---

### Step 24: Write integration test for dedup scoping

**File:** `tests/test_workflow.py` (append)
**Action:** Create

```python
# ---- append to: tests/test_workflow.py ----


class TestDedupScoping:
    """Integration test for dedup --role-types scoping.

    Note: Safety bound abort test is already covered by TestDedupAutoScoping
    in test_manage_state_dedup.py. This class tests only role-type scoping.
    """

    def test_dedup_scopes_to_todays_role_types(self, tmp_path: Path) -> None:
        """Dedup with --role-types=ai-engineer only touches ai-engineer/, not old-role/."""
        ai_dir = tmp_path / "output" / "verified" / "ai-engineer"
        old_dir = tmp_path / "output" / "verified" / "old-role"

        _write_verified_json(ai_dir / "newco.json", _make_job(
            title="AI Engineer", company="NewCo", score=85,
            job_url="https://newco.com/jobs/ai", role_type="ai-engineer",
        ))
        _write_verified_json(old_dir / "oldco.json", _make_job(
            title="Old Role Specialist", company="OldCo", score=85,
            job_url="https://oldco.com/jobs/old", role_type="old-role",
        ))

        result = _run_manage_state(
            ["dedup", "--output-dir", str(tmp_path / "output"), "--role-types", "ai-engineer"],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert (old_dir / "oldco.json").exists(), "old-role job should NOT be touched"
        assert (ai_dir / "newco.json").exists(), "ai-engineer job should remain"
```

**Verify:**
- Test: `pytest tests/test_workflow.py::TestDedupScoping -v` -> PASS

---

### Step 25: Run full test suite

**Verify:**
- Test: `pytest tests/ -v`
- Lint: `ruff check scripts/ tests/`

---

### Step 26: Commit Layer 3

```bash
git add scripts/preflight.sh tests/test_preflight.py tests/test_workflow.py
git commit -m "feat(jsa): V24 Layer 3 -- preflight schema validation, integration tests"
```

---

### Step 27: Run migration on existing verified JSONs (subagent-delegated)

**Action:** Dispatch a subagent (model: haiku) to run migration against actual V23 data. Parent must NOT execute these commands directly (V18 regression — parent must never run manage_state.py).

Subagent runs:
```bash
python scripts/manage_state.py migrate-schema
python scripts/manage_state.py validate-schema
```

Subagent writes result to a status file. Parent reads only the status output.

**Verify:** Subagent reports `validate-schema` exits 0 (all files now canonical)

---

### Step 28: Final full test suite + commit

**Verify:**
- Test: `pytest tests/ -v` -- ALL tests pass
- Lint: `ruff check scripts/ tests/`

```bash
# Code commit (no data directories)
git add scripts/manage_state.py scripts/preflight.sh \
  tests/helpers.py tests/test_manage_state.py tests/test_manage_state_dedup.py \
  tests/test_claude_md.py tests/test_workflow.py tests/test_preflight.py \
  .claude/agents/search-verify.md references/subagent-search-verify.md \
  references/orchestration.md CLAUDE.md
git commit -m "feat(jsa): V24 complete -- schema-first fix with all tests passing"

# Data-only commit (migrated verified/archive JSONs, separate from code)
git add output/verified/ output/archive/
git commit -m "data(jsa): V24 migrate verified+archive JSONs to canonical schema"
```

---

## Deployment Verification

### Pre-Deploy Checks

```bash
# Run from 03_agents/tests/v23/

# 1. Full test suite
pytest tests/ -v

# 2. Lint
ruff check scripts/ tests/

# 3. Validate existing verified JSON against schema
python scripts/manage_state.py validate-schema

# 4. Dry-run migration on a backup
cp -r output/verified/ output/verified_backup/
python scripts/manage_state.py migrate-schema

# 5. Verify preflight checks pass
bash scripts/preflight.sh
```

### Post-Deploy Checks

```bash
# Run from 03_agents/tests/v23/

# 1. Validate all migrated JSON
python scripts/manage_state.py validate-schema

# 2. Verify search-verify agent is on Sonnet tier
grep "model:" .claude/agents/search-verify.md | grep -q "sonnet" && echo "search-verify model is sonnet"

# 3. Smoke test: run dedup with active role types scoping
pytest tests/test_manage_state_dedup.py::TestDedupAutoScoping -v

# 4. Verify gate-check blocking in workflow
pytest tests/test_workflow.py::TestGateBlocking -v

# 5. Full test suite one more time
pytest tests/ -v
```

### Rollback Plan

```bash
# Run from 03_agents/tests/v23/ if post-deploy checks fail

# 1. Revert all code changes
git revert HEAD --no-edit

# 2. Restore verified JSON from backup (only if migration corrupted data)
rm -rf output/verified/
mv output/verified_backup/ output/verified/

# 3. Verify rollback restored previous state
python scripts/manage_state.py validate-schema 2>&1 | head -5
git status
```

---

## Handoff Contract

- **Total steps:** 29
- **Total phases:** 3 (Layer 1: Steps 0-12, Layer 2: Steps 13-20, Layer 3: Steps 21-28)
- **Files created:** `tests/helpers.py` (shared `_make_job()` test factory)
- **Files modified:**
  - `scripts/manage_state.py` — validate-schema, migrate-schema, _extract_score fix, dedup auto-scoping + safety bound, _slugify fix
  - `tests/test_manage_state.py` — TestValidateSchema, TestSlugExtraction, TestMigrateSchema
  - `tests/test_manage_state_dedup.py` — TestDedupScoreField, TestDedupAutoScoping
  - `.claude/agents/search-verify.md` — model: sonnet
  - `references/subagent-search-verify.md` — Output Schema Contract
  - `references/orchestration.md` — Schema Validation Gate, blocking gate semantics
  - `CLAUDE.md` — Agent Model Tiers table
  - `tests/test_claude_md.py` — test_search_verify_model_is_sonnet
  - `tests/test_workflow.py` — TestGateBlocking, TestSchemaValidationGate, TestDedupScoping
  - `scripts/preflight.sh` — schema validation check, model tier check
  - `tests/test_preflight.py` — TestPreflightSchemaValidation
- **Verification sequence:** Layer 1 tests -> Layer 1 lint -> Layer 2 tests -> Layer 2 lint -> Layer 3 tests -> Layer 3 lint -> Full suite -> Migration -> Final validation
- **Deployment verification:** Pre-deploy (lint, tests, validate-schema, migration dry-run, preflight), Post-deploy (validate, smoke tests, full suite), Rollback (git revert + backup restore)
- **New tests added:** 24 tests across 8 test classes
- **Estimated test count after build:** 170+ existing + 20 new = ~190 tests (reduced from 24 after removing duplicate integration tests)
- **Known out-of-scope regressions:**
  - `send_email.py` CLI interface (`--body-file` vs `--html` flag) correctness is NOT addressed by this plan (V21/V23 regression). Remains a known issue for a future version.
  - `background: true` subagent permission failures (V20-V23, 8-version recurrence). Search-verify agent retains `background: true` in frontmatter. Changing to `background: false` affects orchestration dispatch patterns beyond this plan's scope. Deferred to next version.

<!-- STAGE COMPLETE: /plan, 2026-02-25 -->

<\!-- STAGE COMPLETE: /revise after round 1, 2026-02-25 -->

<!-- STAGE COMPLETE: /revise after round 2, 2026-02-25 -->

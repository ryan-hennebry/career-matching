"""Tests for manage_state.py dedup --role-types feature (9 tests).

All tests are expected to FAIL until the --role-types flag is implemented.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_dedup(
    output_dir: str,
    *,
    role_types: str | None = None,
    dry_run: bool = False,
    no_safety_bound: bool = False,
) -> subprocess.CompletedProcess:
    """Run dedup subcommand with optional --role-types flag."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "dedup",
        "--output-dir",
        output_dir,
    ]
    if role_types is not None:
        cmd.extend(["--role-types", role_types])
    if dry_run:
        cmd.append("--dry-run")
    if no_safety_bound:
        cmd.append("--no-safety-bound")
    return subprocess.run(cmd, capture_output=True, text=True)


def _make_job(
    *,
    company: str = "Acme Corp",
    title: str = "Software Engineer",
    score: int = 80,
    url: str = "https://example.com/jobs/1",
    role_type: str = "community-manager",
    location: str = "Remote",
    source: str = "linkedin",
) -> dict[str, Any]:
    """Return a minimal verified job JSON dict with fields needed by dedup."""
    return {
        "company": company,
        "title": title,
        "score": score,
        "url": url,
        "role_type": role_type,
        "location": location,
        "source": source,
    }


def _write_job(dirpath: Path, filename: str, data: dict) -> Path:
    """Write a verified JSON file and return its path."""
    dirpath.mkdir(parents=True, exist_ok=True)
    fpath = dirpath / filename
    fpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return fpath


# ---------------------------------------------------------------------------
# TestDedupRoleTypes — 9 tests for --role-types scoping
# ---------------------------------------------------------------------------


class TestDedupRoleTypes:
    """Tests for the dedup --role-types flag (context-aware scoping)."""

    def test_role_types_filters_to_specified_dirs(self, tmp_path: Path) -> None:
        """Low-score job in included role is archived; excluded role is untouched."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        # Included role: community-manager — low score, should be archived
        included_job = _make_job(
            company="LowCo",
            title="Intern",
            score=55,
            url="https://example.com/low",
            role_type="community-manager",
        )
        _write_job(verified / "community-manager", "lowco-intern.json", included_job)

        # Excluded role: devrel — low score, should NOT be touched
        excluded_job = _make_job(
            company="ExcludedCo",
            title="Associate",
            score=40,
            url="https://example.com/excluded",
            role_type="devrel",
        )
        _write_job(verified / "devrel", "excludedco-assoc.json", excluded_job)

        result = _run_dedup(str(output_dir), role_types="community-manager", no_safety_bound=True)
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Included role: low-score job should be archived
        assert not (verified / "community-manager" / "lowco-intern.json").exists(), (
            "low-score job in included role should be archived"
        )
        archive_path = output_dir / "archive" / "community-manager" / "lowco-intern.json"
        assert archive_path.exists(), (
            "low-score job in included role should appear in archive/"
        )

        # Excluded role: file must be untouched
        assert (verified / "devrel" / "excludedco-assoc.json").exists(), (
            "job in excluded role-type must NOT be processed"
        )

    def test_role_types_multiple_slugs(self, tmp_path: Path) -> None:
        """Comma-separated slugs are all processed."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        # Two roles, each with a low-score job
        job_cm = _make_job(
            company="AlphaCo",
            title="Coordinator",
            score=50,
            url="https://example.com/cm",
            role_type="community-manager",
        )
        job_devrel = _make_job(
            company="BetaCo",
            title="Advocate",
            score=45,
            url="https://example.com/dr",
            role_type="devrel",
        )
        # Third role NOT in the list
        job_growth = _make_job(
            company="GammaCo",
            title="Analyst",
            score=30,
            url="https://example.com/gr",
            role_type="growth",
        )
        _write_job(verified / "community-manager", "alpha-coord.json", job_cm)
        _write_job(verified / "devrel", "beta-adv.json", job_devrel)
        _write_job(verified / "growth", "gamma-analyst.json", job_growth)

        result = _run_dedup(
            str(output_dir), role_types="community-manager,devrel", no_safety_bound=True,
        )
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Both included roles should have low-score jobs archived
        assert not (verified / "community-manager" / "alpha-coord.json").exists(), (
            "low-score job in community-manager should be archived"
        )
        assert not (verified / "devrel" / "beta-adv.json").exists(), (
            "low-score job in devrel should be archived"
        )

        # Excluded role untouched
        assert (verified / "growth" / "gamma-analyst.json").exists(), (
            "growth role not in --role-types; its files must be untouched"
        )

    def test_role_types_omitted_processes_all(self, tmp_path: Path) -> None:
        """When --role-types is omitted, all directories are processed (backward compat)."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        # Two roles, each with a low-score job
        job_cm = _make_job(
            company="OmitCo",
            title="Intern",
            score=55,
            url="https://example.com/cm",
            role_type="community-manager",
        )
        job_devrel = _make_job(
            company="OmitDevCo",
            title="Junior",
            score=50,
            url="https://example.com/dr",
            role_type="devrel",
        )
        _write_job(verified / "community-manager", "omitco-intern.json", job_cm)
        _write_job(verified / "devrel", "omitdevco-jr.json", job_devrel)

        # No --role-types flag
        result = _run_dedup(str(output_dir), no_safety_bound=True)
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Both low-score jobs should be archived (all dirs processed)
        assert not (verified / "community-manager" / "omitco-intern.json").exists(), (
            "without --role-types, all roles should be processed"
        )
        assert not (verified / "devrel" / "omitdevco-jr.json").exists(), (
            "without --role-types, all roles should be processed"
        )

    def test_role_types_cross_role_dedup_scoped(self, tmp_path: Path) -> None:
        """Cross-role dedup is limited to included roles only.

        Two roles have the same (company, title). Only one role is in --role-types.
        The included role's copy should NOT be archived as a cross-role duplicate
        because the excluded role is out of scope.
        """
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        # Same company+title in two roles, both above threshold
        job_cm = _make_job(
            company="DupeCorp",
            title="Strategist",
            score=85,
            url="https://example.com/cm",
            role_type="community-manager",
        )
        job_devrel = _make_job(
            company="DupeCorp",
            title="Strategist",
            score=90,
            url="https://example.com/dr",
            role_type="devrel",
        )
        _write_job(verified / "community-manager", "dupe-strat.json", job_cm)
        _write_job(verified / "devrel", "dupe-strat.json", job_devrel)

        # Only include community-manager; devrel is out of scope
        result = _run_dedup(str(output_dir), role_types="community-manager")
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # community-manager copy should survive (no cross-role dedup against excluded role)
        assert (verified / "community-manager" / "dupe-strat.json").exists(), (
            "included role's copy must not be archived via cross-role dedup "
            "against an excluded role"
        )
        # devrel must be untouched (excluded)
        assert (verified / "devrel" / "dupe-strat.json").exists(), (
            "excluded role must be completely untouched"
        )

    def test_role_types_cross_role_dedup_both_included(self, tmp_path: Path) -> None:
        """When both roles are included, normal cross-role dedup applies."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job_cm = _make_job(
            company="BothCo",
            title="Manager",
            score=72,
            url="https://example.com/cm",
            role_type="community-manager",
        )
        job_devrel = _make_job(
            company="BothCo",
            title="Manager",
            score=88,
            url="https://example.com/dr",
            role_type="devrel",
        )
        _write_job(verified / "community-manager", "bothco-mgr.json", job_cm)
        _write_job(verified / "devrel", "bothco-mgr.json", job_devrel)

        result = _run_dedup(
            str(output_dir), role_types="community-manager,devrel", no_safety_bound=True,
        )
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Higher score (devrel, 88) survives, lower (community-manager, 72) archived
        assert (verified / "devrel" / "bothco-mgr.json").exists(), (
            "higher-scoring copy should survive cross-role dedup"
        )
        assert not (verified / "community-manager" / "bothco-mgr.json").exists(), (
            "lower-scoring copy should be archived via cross-role dedup"
        )
        archive_path = output_dir / "archive" / "community-manager" / "bothco-mgr.json"
        assert archive_path.exists(), (
            "lower-scoring duplicate should be in archive/"
        )

    def test_role_types_empty_string_processes_none(self, tmp_path: Path) -> None:
        """Passing --role-types '' (empty string) means process nothing."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job = _make_job(
            company="EmptyCo",
            title="Tester",
            score=50,
            url="https://example.com/empty",
            role_type="community-manager",
        )
        _write_job(verified / "community-manager", "emptyco-test.json", job)

        result = _run_dedup(str(output_dir), role_types="")
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Nothing should be processed — file stays
        assert (verified / "community-manager" / "emptyco-test.json").exists(), (
            "empty --role-types should process no directories"
        )

        # Summary should show zero input
        summary = json.loads(result.stdout)
        assert summary["total_input"] == 0, (
            "empty --role-types should report total_input=0"
        )

    def test_role_types_summary_reflects_scoped_counts(self, tmp_path: Path) -> None:
        """JSON output total_input counts only jobs in scoped roles."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        # 2 jobs in included role
        for i, score in enumerate([85, 90]):
            job = _make_job(
                company=f"ScopeCo{i}",
                title=f"Engineer{i}",
                score=score,
                url=f"https://example.com/scope{i}",
                role_type="community-manager",
            )
            _write_job(
                verified / "community-manager", f"scopeco{i}-eng.json", job
            )

        # 3 jobs in excluded role
        for i, score in enumerate([75, 80, 71]):
            job = _make_job(
                company=f"ExclCo{i}",
                title=f"Dev{i}",
                score=score,
                url=f"https://example.com/excl{i}",
                role_type="devrel",
            )
            _write_job(verified / "devrel", f"exclco{i}-dev.json", job)

        result = _run_dedup(str(output_dir), role_types="community-manager")
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        summary = json.loads(result.stdout)
        assert summary["total_input"] == 2, (
            f"total_input should be 2 (scoped role only), got {summary['total_input']}"
        )

    def test_pre_search_archival_preserves_state_json_referenced_dirs(
        self, tmp_path: Path
    ) -> None:
        """A directory not in --role-types but referenced by state.json is preserved.

        Verifies the cross-reference path between archival logic and state.json:
        a role-type directory that is NOT in the active search list but IS
        referenced by an active job in state.json must not be archived or
        processed during dedup.
        """
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        # Active role: community-manager (in --role-types)
        active_job = _make_job(
            company="ActiveCo",
            title="Lead",
            score=85,
            url="https://example.com/active",
            role_type="community-manager",
        )
        _write_job(verified / "community-manager", "activeco-lead.json", active_job)

        # Inactive role: devrel (NOT in --role-types, but referenced by state.json)
        stale_job = _make_job(
            company="StaleCo",
            title="Advocate",
            score=40,
            url="https://example.com/stale",
            role_type="devrel",
        )
        _write_job(verified / "devrel", "staleco-adv.json", stale_job)

        # Create state.json that references the devrel job
        state = {
            "last_run_date": "2026-02-24",
            "jobs": {
                "devrel/staleco-adv": {
                    "title": "Advocate",
                    "company": "StaleCo",
                    "score": 40,
                    "role_type": "devrel",
                    "source": "linkedin",
                    "first_seen": "2026-02-20",
                    "last_seen": "2026-02-24",
                    "active_status": "verified",
                    "job_url": "https://example.com/stale",
                    "location": "Remote",
                    "requirements_met": [],
                    "user_action": "brief_requested",
                    "expired_date": None,
                    "reappeared": False,
                },
            },
            "expired_jobs": {},
        }
        state_path = output_dir / "state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

        result = _run_dedup(str(output_dir), role_types="community-manager")
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # The devrel directory and its files must be completely untouched
        assert (verified / "devrel" / "staleco-adv.json").exists(), (
            "directory referenced by state.json must be preserved even when "
            "not in --role-types"
        )
        # No archive for devrel
        assert not (output_dir / "archive" / "devrel").exists(), (
            "excluded role with state.json reference must not have any archived files"
        )

    def test_within_role_url_dedup(self, tmp_path: Path) -> None:
        """Two jobs with identical URLs but different scores in the same role directory.

        Only the higher-scored entry should be retained. Validates V20
        within-role URL-based dedup survives the V22 copy.
        """
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        shared_url = "https://example.com/jobs/same-posting"
        job_high = _make_job(
            company="UrlDupeCo",
            title="Senior Engineer",
            score=92,
            url=shared_url,
            role_type="community-manager",
        )
        job_low = _make_job(
            company="UrlDupeRepost",
            title="Engineer",
            score=68,
            url=shared_url,
            role_type="community-manager",
        )
        _write_job(verified / "community-manager", "urldupe-senior.json", job_high)
        _write_job(verified / "community-manager", "urldupe-eng.json", job_low)

        result = _run_dedup(str(output_dir), role_types="community-manager")
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Higher-scoring copy preserved
        assert (verified / "community-manager" / "urldupe-senior.json").exists(), (
            "higher-scored same-URL job should be preserved"
        )
        # Lower-scoring same-URL copy archived
        assert not (verified / "community-manager" / "urldupe-eng.json").exists(), (
            "lower-scored same-URL job should be archived"
        )
        archive_path = (
            output_dir / "archive" / "community-manager" / "urldupe-eng.json"
        )
        assert archive_path.exists(), (
            "within-role same-URL duplicate should be in archive/"
        )


# ---------------------------------------------------------------------------
# TestDedupScoreField
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import _make_job as _make_canonical_job, _write_job as _write_canonical_job, _run_dedup as _run_canonical_dedup  # noqa: E402


class TestDedupScoreField:
    """Tests that dedup sorts/filters by canonical top-level `score` field only."""

    def test_dedup_reads_canonical_score(self, tmp_path: Path) -> None:
        """Job with {"score": 85} (canonical) -> dedup sorts correctly by score."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job_high = _make_canonical_job(
            company="SameCo", title="Strategist", score=85,
            job_url="https://example.com/high", role_type="ai-engineer",
        )
        job_low = _make_canonical_job(
            company="SameCo", title="Strategist", score=60,
            job_url="https://example.com/low", role_type="ai-engineer",
        )
        _write_canonical_job(verified / "ai-engineer", "sameco-high.json", job_high)
        _write_canonical_job(verified / "ai-engineer", "sameco-low.json", job_low)

        result = _run_canonical_dedup(str(output_dir), role_types="ai-engineer")
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

        job_a = _make_canonical_job(
            company="NestCo", title="Analyst", score=85,
            job_url="https://example.com/a", role_type="ai-engineer",
            scoring_breakdown={"overall_score": 90, "experience": 80},
        )
        job_b = _make_canonical_job(
            company="NestCo", title="Analyst", score=90,
            job_url="https://example.com/b", role_type="ai-engineer",
        )
        _write_canonical_job(verified / "ai-engineer", "nestco-a.json", job_a)
        _write_canonical_job(verified / "ai-engineer", "nestco-b.json", job_b)

        result = _run_canonical_dedup(str(output_dir), role_types="ai-engineer")
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        assert (verified / "ai-engineer" / "nestco-b.json").exists(), (
            "job with canonical score=90 should be kept"
        )
        assert not (verified / "ai-engineer" / "nestco-a.json").exists(), (
            "job with canonical score=85 should be archived"
        )


# ---------------------------------------------------------------------------
# TestDedupAutoScoping
# ---------------------------------------------------------------------------

TODAY = "2026-02-25"
OLD_DATE = "2026-01-01"


class TestDedupAutoScoping:
    """Tests for dedup auto-scoping by today's run_date and safety bound."""

    def test_dedup_only_processes_active_role_types(self, tmp_path: Path) -> None:
        """Active role types (run_date==today) processed; stale ones skipped."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        active_low = _make_canonical_job(
            company="ActiveCo", title="Agent Engineer", score=55,
            job_url="https://example.com/active", role_type="ai-engineer",
            run_date=TODAY,
        )
        _write_canonical_job(verified / "ai-engineer", "activeco-eng.json", active_low)

        # Two high-score jobs to keep the safety bound below 50% (1/3 = 33%)
        active_high1 = _make_canonical_job(
            company="KeepCo1", title="Senior Engineer", score=85,
            job_url="https://example.com/keep1", role_type="ai-engineer",
            run_date=TODAY,
        )
        _write_canonical_job(verified / "ai-engineer", "keepco1-sr.json", active_high1)

        active_high2 = _make_canonical_job(
            company="KeepCo2", title="Staff Engineer", score=90,
            job_url="https://example.com/keep2", role_type="ai-engineer",
            run_date=TODAY,
        )
        _write_canonical_job(verified / "ai-engineer", "keepco2-staff.json", active_high2)

        stale_job = _make_canonical_job(
            company="StaleCo", title="Old Role", score=55,
            job_url="https://example.com/stale", role_type="stale-role",
            run_date=OLD_DATE,
        )
        _write_canonical_job(verified / "stale-role", "staleco-old.json", stale_job)

        result = _run_canonical_dedup(str(output_dir), auto_scope=True, run_date=TODAY)
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
            low_job = _make_canonical_job(
                company=f"LowCo{i}", title=f"Temp{i}", score=40,
                job_url=f"https://example.com/low{i}", role_type="ai-engineer",
                run_date=TODAY,
            )
            _write_canonical_job(verified / "ai-engineer", f"lowco{i}-temp.json", low_job)

        result = _run_canonical_dedup(str(output_dir), auto_scope=True, run_date=TODAY)
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

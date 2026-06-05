"""Tests for manage_state.py cleanup subcommand (8 tests).

All tests are expected to FAIL until the cleanup subcommand is implemented.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run_cleanup(output_dir: str, *, dry_run: bool = False) -> subprocess.CompletedProcess:
    """Run cleanup subcommand against a given output directory."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "cleanup",
        "--output-dir",
        output_dir,
    ]
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, capture_output=True, text=True)


def _populate_dir(base: Path, subdir: str, filenames: list[str]) -> Path:
    """Create a subdirectory with dummy files and return its path."""
    d = base / subdir
    d.mkdir(parents=True, exist_ok=True)
    for name in filenames:
        (d / name).write_text(json.dumps({"placeholder": True}), encoding="utf-8")
    return d


class TestCleanup:
    """Tests for the cleanup subcommand of manage_state.py."""

    def test_cleanup_removes_raw_directory(self, tmp_path: Path) -> None:
        """Creates temp files in output/raw/, runs cleanup, asserts directory removed."""
        output_dir = tmp_path / "output"
        _populate_dir(output_dir, "raw", ["a.json", "b.json"])
        # Ensure verified/ and jobs/ exist so cleanup has a valid output structure
        _populate_dir(output_dir, "verified/community-manager", ["keeper.json"])
        _populate_dir(output_dir, "jobs", ["job1.json"])

        result = _run_cleanup(str(output_dir))
        assert result.returncode == 0, f"cleanup failed: {result.stderr}"
        assert not (output_dir / "raw").exists(), "raw/ directory should be removed after cleanup"

    def test_cleanup_removes_search_results(self, tmp_path: Path) -> None:
        """Creates temp files in output/search-results/, runs cleanup, asserts removed."""
        output_dir = tmp_path / "output"
        _populate_dir(output_dir, "search-results", ["results-2026-02-19.json"])
        _populate_dir(output_dir, "verified/community-manager", ["keeper.json"])

        result = _run_cleanup(str(output_dir))
        assert result.returncode == 0, f"cleanup failed: {result.stderr}"
        assert not (output_dir / "search-results").exists(), (
            "search-results/ directory should be removed after cleanup"
        )

    def test_cleanup_removes_unverified(self, tmp_path: Path) -> None:
        """Creates temp files in output/unverified/, runs cleanup, asserts removed."""
        output_dir = tmp_path / "output"
        _populate_dir(output_dir, "unverified", ["candidate-a.json", "candidate-b.json"])
        _populate_dir(output_dir, "verified/devrel", ["keeper.json"])

        result = _run_cleanup(str(output_dir))
        assert result.returncode == 0, f"cleanup failed: {result.stderr}"
        assert not (output_dir / "unverified").exists(), (
            "unverified/ directory should be removed after cleanup"
        )

    def test_cleanup_preserves_verified(self, tmp_path: Path) -> None:
        """Creates files in output/verified/, runs cleanup, asserts ALL files remain."""
        output_dir = tmp_path / "output"
        verified_files = ["acme-engineer.json", "beta-analyst.json"]
        _populate_dir(output_dir, "verified/community-manager", verified_files)
        # Also create a temp dir to give cleanup something to remove
        _populate_dir(output_dir, "raw", ["throwaway.json"])

        result = _run_cleanup(str(output_dir))
        assert result.returncode == 0, f"cleanup failed: {result.stderr}"

        verified_cm = output_dir / "verified" / "community-manager"
        assert verified_cm.exists(), "verified/community-manager/ must survive cleanup"
        for fname in verified_files:
            assert (verified_cm / fname).exists(), f"verified file {fname} must survive cleanup"

    def test_cleanup_preserves_jobs(self, tmp_path: Path) -> None:
        """Creates files in output/jobs/, runs cleanup, asserts ALL files remain."""
        output_dir = tmp_path / "output"
        job_files = ["brief-acme.html", "brief-beta.html"]
        _populate_dir(output_dir, "jobs", job_files)
        _populate_dir(output_dir, "raw", ["throwaway.json"])

        result = _run_cleanup(str(output_dir))
        assert result.returncode == 0, f"cleanup failed: {result.stderr}"

        jobs_dir = output_dir / "jobs"
        assert jobs_dir.exists(), "jobs/ directory must survive cleanup"
        for fname in job_files:
            assert (jobs_dir / fname).exists(), f"jobs file {fname} must survive cleanup"

    def test_cleanup_handles_missing_directories(self, tmp_path: Path) -> None:
        """Runs cleanup when temp dirs don't exist, asserts no error."""
        output_dir = tmp_path / "output"
        # Create only verified/ — raw/, search-results/, unverified/ do not exist
        _populate_dir(output_dir, "verified/community-manager", ["keeper.json"])

        result = _run_cleanup(str(output_dir))
        assert result.returncode == 0, (
            f"cleanup should succeed even when temp dirs are missing: {result.stderr}"
        )

    def test_cleanup_dry_run(self, tmp_path: Path) -> None:
        """Runs cleanup with --dry-run, asserts temp dirs still exist."""
        output_dir = tmp_path / "output"
        _populate_dir(output_dir, "raw", ["a.json"])
        _populate_dir(output_dir, "search-results", ["b.json"])
        _populate_dir(output_dir, "unverified", ["c.json"])
        _populate_dir(output_dir, "verified/devrel", ["keeper.json"])

        result = _run_cleanup(str(output_dir), dry_run=True)
        assert result.returncode == 0, f"cleanup --dry-run failed: {result.stderr}"

        assert (output_dir / "raw").exists(), "raw/ must still exist after --dry-run"
        assert (output_dir / "search-results").exists(), (
            "search-results/ must still exist after --dry-run"
        )
        assert (output_dir / "unverified").exists(), (
            "unverified/ must still exist after --dry-run"
        )

    def test_cleanup_never_touches_verified_with_active_jobs(self, tmp_path: Path) -> None:
        """Verified files with active jobs in state.json remain untouched after cleanup."""
        output_dir = tmp_path / "output"

        # Create verified job files
        verified_files = ["acme-growth-lead.json", "beta-analyst.json"]
        _populate_dir(output_dir, "verified/community-manager", verified_files)
        _populate_dir(output_dir, "raw", ["throwaway.json"])

        # Create a state.json with active jobs referencing these verified files
        state = {
            "last_run_date": "2026-02-19",
            "jobs": {
                "community-manager/acme-growth-lead": {
                    "title": "Growth Lead",
                    "company": "Acme Corp",
                    "score": 85,
                    "role_type": "community-manager",
                    "source": "linkedin",
                    "first_seen": "2026-02-10",
                    "last_seen": "2026-02-19",
                    "active_status": "verified",
                    "job_url": "https://linkedin.com/jobs/view/123",
                    "location": "London, UK",
                    "requirements_met": ["python", "growth"],
                    "user_action": None,
                    "expired_date": None,
                    "reappeared": False,
                },
                "community-manager/beta-analyst": {
                    "title": "Analyst",
                    "company": "Beta Corp",
                    "score": 78,
                    "role_type": "community-manager",
                    "source": "indeed",
                    "first_seen": "2026-02-12",
                    "last_seen": "2026-02-19",
                    "active_status": "verified",
                    "job_url": "https://indeed.com/jobs/view/456",
                    "location": "Remote",
                    "requirements_met": ["data-analysis"],
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

        result = _run_cleanup(str(output_dir))
        assert result.returncode == 0, f"cleanup failed: {result.stderr}"

        # Verified files referenced by active jobs must remain
        verified_cm = output_dir / "verified" / "community-manager"
        assert verified_cm.exists(), "verified/ directory must survive cleanup"
        for fname in verified_files:
            assert (verified_cm / fname).exists(), (
                f"verified file {fname} with active job must survive cleanup"
            )


# ---------------------------------------------------------------------------
# Helpers for dedup tests
# ---------------------------------------------------------------------------


def _run_dedup(
    output_dir: str,
    *,
    dry_run: bool = False,
    no_safety_bound: bool = False,
) -> subprocess.CompletedProcess:
    """Run dedup subcommand against a given output directory."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "dedup",
        "--output-dir",
        output_dir,
    ]
    if dry_run:
        cmd.append("--dry-run")
    if no_safety_bound:
        cmd.append("--no-safety-bound")
    return subprocess.run(cmd, capture_output=True, text=True)


def _make_verified_json(
    *,
    company: str = "Acme Corp",
    title: str = "Software Engineer",
    score: int = 80,
    url: str = "https://example.com/jobs/1",
    role_type: str = "community-manager",
    location: str = "Remote",
    source: str = "linkedin",
) -> dict:
    """Return a valid verified job JSON dict with all required fields."""
    return {
        "company": company,
        "title": title,
        "score": score,
        "url": url,
        "role_type": role_type,
        "location": location,
        "source": source,
    }


def _write_verified_json(dirpath: Path, filename: str, data: dict) -> Path:
    """Write a verified JSON file and return its path."""
    dirpath.mkdir(parents=True, exist_ok=True)
    fpath = dirpath / filename
    fpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return fpath


class TestDedup:
    """Tests for the dedup subcommand of manage_state.py."""

    def test_dedup_detects_cross_role_duplicates(self, tmp_path: Path) -> None:
        """Two verified JSONs in different role dirs with same (company, title).

        Asserts lower-scoring copy moved to output/archive/.
        """
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job_a = _make_verified_json(
            company="Acme Corp", title="Growth Lead", score=85,
            url="https://example.com/a", role_type="community-manager",
        )
        job_b = _make_verified_json(
            company="Acme Corp", title="Growth Lead", score=72,
            url="https://example.com/b", role_type="devrel",
        )
        _write_verified_json(verified / "community-manager", "acme-growth.json", job_a)
        _write_verified_json(verified / "devrel", "acme-growth.json", job_b)

        result = _run_dedup(str(output_dir), no_safety_bound=True)
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Higher-scoring copy stays in verified/
        assert (verified / "community-manager" / "acme-growth.json").exists()
        # Lower-scoring copy moved to archive/
        assert not (verified / "devrel" / "acme-growth.json").exists()
        archive_path = output_dir / "archive" / "devrel" / "acme-growth.json"
        assert archive_path.exists(), "lower-scoring duplicate should be archived"

    def test_dedup_normalization_case_insensitive(self, tmp_path: Path) -> None:
        """'Acme Corp' vs 'acme corp' detected as same company."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job_a = _make_verified_json(
            company="Acme Corp", title="Engineer", score=90,
            url="https://example.com/a", role_type="community-manager",
        )
        job_b = _make_verified_json(
            company="acme corp", title="engineer", score=70,
            url="https://example.com/b", role_type="devrel",
        )
        _write_verified_json(verified / "community-manager", "acme-eng.json", job_a)
        _write_verified_json(verified / "devrel", "acme-eng.json", job_b)

        result = _run_dedup(str(output_dir), no_safety_bound=True)
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Only the higher-scoring copy remains in verified/
        assert (verified / "community-manager" / "acme-eng.json").exists()
        assert not (verified / "devrel" / "acme-eng.json").exists()

    def test_dedup_normalization_strips_whitespace(self, tmp_path: Path) -> None:
        """' Acme Corp ' vs 'Acme Corp' detected as same company."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job_a = _make_verified_json(
            company=" Acme Corp ", title=" Engineer ", score=88,
            url="https://example.com/a", role_type="community-manager",
        )
        job_b = _make_verified_json(
            company="Acme Corp", title="Engineer", score=75,
            url="https://example.com/b", role_type="devrel",
        )
        _write_verified_json(verified / "community-manager", "acme-eng.json", job_a)
        _write_verified_json(verified / "devrel", "acme-eng.json", job_b)

        result = _run_dedup(str(output_dir), no_safety_bound=True)
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        assert (verified / "community-manager" / "acme-eng.json").exists()
        assert not (verified / "devrel" / "acme-eng.json").exists()

    def test_dedup_archives_below_threshold(self, tmp_path: Path) -> None:
        """Job with score < 70 moved to output/archive/."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job = _make_verified_json(
            company="LowScore Inc", title="Intern", score=55,
            url="https://example.com/low", role_type="community-manager",
        )
        _write_verified_json(verified / "community-manager", "lowscore.json", job)

        result = _run_dedup(str(output_dir), no_safety_bound=True)
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        assert not (verified / "community-manager" / "lowscore.json").exists(), (
            "job with score < 70 should be moved out of verified/"
        )
        archive_path = output_dir / "archive" / "community-manager" / "lowscore.json"
        assert archive_path.exists(), "job with score < 70 should be in archive/"

    def test_dedup_preserves_above_threshold(self, tmp_path: Path) -> None:
        """Job with score >= 70 preserved in verified/."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job = _make_verified_json(
            company="HighScore Inc", title="Lead", score=70,
            url="https://example.com/high", role_type="community-manager",
        )
        _write_verified_json(verified / "community-manager", "highscore.json", job)

        result = _run_dedup(str(output_dir))
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        assert (verified / "community-manager" / "highscore.json").exists(), (
            "job with score >= 70 should remain in verified/"
        )

    def test_dedup_keeps_highest_score(self, tmp_path: Path) -> None:
        """Of two duplicates (scores 85 and 72), keeps 85 in verified/, archives 72."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job_high = _make_verified_json(
            company="DupeCo", title="Manager", score=85,
            url="https://example.com/a", role_type="community-manager",
        )
        job_low = _make_verified_json(
            company="DupeCo", title="Manager", score=72,
            url="https://example.com/b", role_type="devrel",
        )
        _write_verified_json(verified / "community-manager", "dupeco-mgr.json", job_high)
        _write_verified_json(verified / "devrel", "dupeco-mgr.json", job_low)

        result = _run_dedup(str(output_dir), no_safety_bound=True)
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Score 85 preserved
        assert (verified / "community-manager" / "dupeco-mgr.json").exists()
        # Score 72 archived
        assert not (verified / "devrel" / "dupeco-mgr.json").exists()
        archive_path = output_dir / "archive" / "devrel" / "dupeco-mgr.json"
        assert archive_path.exists()

    def test_dedup_handles_unicode_company_names(self, tmp_path: Path) -> None:
        """'Zürich AG' and 'zürich ag' detected as same company."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job_a = _make_verified_json(
            company="Zürich AG", title="Analyst", score=82,
            url="https://example.com/a", role_type="community-manager",
        )
        job_b = _make_verified_json(
            company="zürich ag", title="analyst", score=71,
            url="https://example.com/b", role_type="devrel",
        )
        _write_verified_json(verified / "community-manager", "zurich.json", job_a)
        _write_verified_json(verified / "devrel", "zurich.json", job_b)

        result = _run_dedup(str(output_dir), no_safety_bound=True)
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        assert (verified / "community-manager" / "zurich.json").exists()
        assert not (verified / "devrel" / "zurich.json").exists()

    def test_dedup_handles_empty_directories(self, tmp_path: Path) -> None:
        """Runs dedup when verified/ has no subdirs, no error."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"
        verified.mkdir(parents=True)

        result = _run_dedup(str(output_dir))
        assert result.returncode == 0, (
            f"dedup should succeed on empty verified/: {result.stderr}"
        )

    def test_dedup_dry_run_preserves_all(self, tmp_path: Path) -> None:
        """Runs with --dry-run, asserts no files moved."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        job_a = _make_verified_json(
            company="DryCo", title="Dev", score=90,
            url="https://example.com/a", role_type="community-manager",
        )
        job_b = _make_verified_json(
            company="DryCo", title="Dev", score=60,
            url="https://example.com/b", role_type="devrel",
        )
        _write_verified_json(verified / "community-manager", "dryco.json", job_a)
        _write_verified_json(verified / "devrel", "dryco.json", job_b)

        result = _run_dedup(str(output_dir), dry_run=True, no_safety_bound=True)
        assert result.returncode == 0, f"dedup --dry-run failed: {result.stderr}"

        # Both files should still exist after dry run
        assert (verified / "community-manager" / "dryco.json").exists(), (
            "dry-run must not move files"
        )
        assert (verified / "devrel" / "dryco.json").exists(), (
            "dry-run must not move files"
        )
        # Archive should NOT exist
        assert not (output_dir / "archive").exists(), (
            "dry-run must not create archive/"
        )

    def test_dedup_scans_filesystem_for_roles(self, tmp_path: Path) -> None:
        """Roles are derived from output/verified/*/ directory names, not hardcoded."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        # Create a non-standard role directory name
        job = _make_verified_json(
            company="CustomRole Inc", title="Specialist", score=80,
            url="https://example.com/custom", role_type="custom-role-xyz",
        )
        _write_verified_json(verified / "custom-role-xyz", "custom.json", job)

        result = _run_dedup(str(output_dir))
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # File should be preserved (unique, above threshold)
        assert (verified / "custom-role-xyz" / "custom.json").exists(), (
            "dedup must scan filesystem role dirs, not rely on hardcoded list"
        )

    def test_dedup_same_url_within_role(self, tmp_path: Path) -> None:
        """Two verified JSONs in the same role dir with the same URL but different
        (company, title). Asserts lower-scoring copy archived.

        V20 regression: within-role same-URL dedup.
        """
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        shared_url = "https://example.com/jobs/42"
        job_a = _make_verified_json(
            company="AlphaCo", title="Engineer", score=88,
            url=shared_url, role_type="community-manager",
        )
        job_b = _make_verified_json(
            company="BetaCo", title="Developer", score=65,
            url=shared_url, role_type="community-manager",
        )
        _write_verified_json(
            verified / "community-manager", "alpha-eng.json", job_a,
        )
        _write_verified_json(
            verified / "community-manager", "beta-dev.json", job_b,
        )

        result = _run_dedup(str(output_dir))
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Higher-scoring copy preserved
        assert (verified / "community-manager" / "alpha-eng.json").exists()
        # Lower-scoring same-URL copy archived
        assert not (verified / "community-manager" / "beta-dev.json").exists()
        archive_path = (
            output_dir / "archive" / "community-manager" / "beta-dev.json"
        )
        assert archive_path.exists(), (
            "within-role same-URL duplicate should be archived"
        )

    def test_dedup_preserves_at_least_one_copy(self, tmp_path: Path) -> None:
        """Cross-role dedup of N duplicates always preserves exactly one copy.

        V20 dashboard API dependency.
        """
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        roles = ["community-manager", "devrel", "growth", "marketing"]
        scores = [75, 90, 82, 71]

        for role, score in zip(roles, scores):
            job = _make_verified_json(
                company="MultiCo", title="Strategist", score=score,
                url=f"https://example.com/{role}", role_type=role,
            )
            _write_verified_json(verified / role, "multico-strat.json", job)

        result = _run_dedup(str(output_dir), no_safety_bound=True)
        assert result.returncode == 0, f"dedup failed: {result.stderr}"

        # Exactly one copy should remain in verified/
        surviving = []
        for role in roles:
            fpath = verified / role / "multico-strat.json"
            if fpath.exists():
                surviving.append(role)

        assert len(surviving) == 1, (
            f"expected exactly 1 surviving copy, found {len(surviving)}: {surviving}"
        )
        # The surviving copy should be the highest score (90 in devrel)
        assert surviving[0] == "devrel", (
            f"expected devrel (score 90) to survive, got {surviving[0]}"
        )

        # The other 3 should be in archive/
        archived_count = 0
        for role in roles:
            if role == "devrel":
                continue
            archive_path = output_dir / "archive" / role / "multico-strat.json"
            if archive_path.exists():
                archived_count += 1
        assert archived_count == 3, (
            f"expected 3 archived copies, found {archived_count}"
        )


# ---------------------------------------------------------------------------
# Helpers for checkpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def cp_output_dir(tmp_path: Path) -> Path:
    """Create and return a tmp_path/output/.checkpoints structure for checkpoint tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    (output_dir / ".checkpoints").mkdir()
    return output_dir


def _run_checkpoint(
    args: list[str], output_dir: str
) -> subprocess.CompletedProcess:
    """Run checkpoint subcommand against a given output directory."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "checkpoint",
    ] + args + [
        "--output-dir",
        output_dir,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestCheckpointWrite:
    """Tests for the checkpoint write subcommand."""

    def test_checkpoint_write_creates_file(self, cp_output_dir: Path) -> None:
        """Run checkpoint write search --count 5, verify file exists."""
        result = _run_checkpoint(
            ["write", "search", "--count", "5"],
            str(cp_output_dir),
        )
        assert result.returncode == 0, f"checkpoint write failed: {result.stderr}"

        cp_file = cp_output_dir / ".checkpoints" / "search.json"
        assert cp_file.exists(), "checkpoint file search.json should exist after write"

    def test_checkpoint_write_content(self, cp_output_dir: Path) -> None:
        """Verify JSON keys: phase, count, committed, timestamp."""
        result = _run_checkpoint(
            ["write", "search", "--count", "5"],
            str(cp_output_dir),
        )
        assert result.returncode == 0, f"checkpoint write failed: {result.stderr}"

        cp_file = cp_output_dir / ".checkpoints" / "search.json"
        data = json.loads(cp_file.read_text(encoding="utf-8"))

        assert data["phase"] == "search"
        assert data["count"] == 5
        assert data["committed"] is True
        assert "timestamp" in data

    def test_checkpoint_write_unknown_phase_fails(self, cp_output_dir: Path) -> None:
        """Exit code != 0 for invalid phase name."""
        result = _run_checkpoint(
            ["write", "bogus-phase", "--count", "1"],
            str(cp_output_dir),
        )
        assert result.returncode != 0, "unknown phase should fail"

    def test_checkpoint_write_requires_count(self, cp_output_dir: Path) -> None:
        """Missing --count flag causes failure."""
        result = _run_checkpoint(
            ["write", "search"],
            str(cp_output_dir),
        )
        assert result.returncode != 0, "missing --count should fail"


class TestCheckpointValidate:
    """Tests for the checkpoint validate subcommand."""

    def test_validate_existing_checkpoint_passes(self, cp_output_dir: Path) -> None:
        """Write then validate — exit 0."""
        write_result = _run_checkpoint(
            ["write", "search", "--count", "5"],
            str(cp_output_dir),
        )
        assert write_result.returncode == 0, f"write failed: {write_result.stderr}"

        val_result = _run_checkpoint(
            ["validate", "search"],
            str(cp_output_dir),
        )
        assert val_result.returncode == 0, f"validate should pass: {val_result.stderr}"

    def test_validate_missing_checkpoint_fails(self, cp_output_dir: Path) -> None:
        """Validate without write — exit 1."""
        val_result = _run_checkpoint(
            ["validate", "verify"],
            str(cp_output_dir),
        )
        assert val_result.returncode == 1, "validate on missing checkpoint should exit 1"


class TestCheckpointStatus:
    """Tests for the checkpoint status subcommand."""

    def test_status_shows_all_phases(self, cp_output_dir: Path) -> None:
        """Write 2 checkpoints, output lists all 5 phases with complete/pending."""
        _run_checkpoint(["write", "search", "--count", "5"], str(cp_output_dir))
        _run_checkpoint(["write", "verify", "--count", "3"], str(cp_output_dir))

        result = _run_checkpoint(["status"], str(cp_output_dir))
        assert result.returncode == 0, f"status failed: {result.stderr}"

        out = result.stdout
        assert "search" in out
        assert "verify" in out
        assert "dedup" in out
        assert "present" in out
        assert "deliver" in out

        lines = out.strip().splitlines()
        phase_lines = {line.split()[0]: line for line in lines if any(p in line for p in ["search", "verify", "dedup", "present", "deliver"])}
        assert "complete" in phase_lines.get("search", "").lower() or "5" in phase_lines.get("search", "")
        assert "pending" in phase_lines.get("dedup", "").lower()

    def test_status_empty(self, cp_output_dir: Path) -> None:
        """All phases show pending when no checkpoints written."""
        result = _run_checkpoint(["status"], str(cp_output_dir))
        assert result.returncode == 0, f"status failed: {result.stderr}"

        out = result.stdout.lower()
        assert out.count("pending") == 5, f"expected 5 pending phases, got: {result.stdout}"


class TestCheckpointClear:
    """Tests for the checkpoint clear subcommand."""

    def test_clear_removes_all(self, cp_output_dir: Path) -> None:
        """Write checkpoints, clear, verify removed."""
        cp_dir = cp_output_dir / ".checkpoints"

        _run_checkpoint(["write", "search", "--count", "5"], str(cp_output_dir))
        _run_checkpoint(["write", "verify", "--count", "3"], str(cp_output_dir))

        assert (cp_dir / "search.json").exists()
        assert (cp_dir / "verify.json").exists()

        result = _run_checkpoint(["clear"], str(cp_output_dir))
        assert result.returncode == 0, f"clear failed: {result.stderr}"

        assert not (cp_dir / "search.json").exists(), "search.json should be removed after clear"
        assert not (cp_dir / "verify.json").exists(), "verify.json should be removed after clear"

    def test_clear_idempotent(self, cp_output_dir: Path) -> None:
        """Clear when empty produces no error."""
        result = _run_checkpoint(["clear"], str(cp_output_dir))
        assert result.returncode == 0, f"clear on empty should succeed: {result.stderr}"


class TestCheckpointPerformance:
    """Performance benchmarks for checkpoint operations."""

    def test_direct_call_under_500ms(self, cp_output_dir: Path) -> None:
        """100 direct-call write+validate cycles complete in under 500ms.

        Tests checkpoint logic directly via Python function import,
        bypassing subprocess overhead."""
        import time
        import argparse as _argparse

        # Import checkpoint functions directly
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        import manage_state

        start = time.monotonic()

        for i in range(100):
            # Direct write
            write_args = _argparse.Namespace(
                phase="search",
                count=i,
                output_dir=str(cp_output_dir),
            )
            manage_state._cli_checkpoint_write(write_args)

            # Direct validate
            validate_args = _argparse.Namespace(
                phase="search",
                output_dir=str(cp_output_dir),
            )
            manage_state._cli_checkpoint_validate(validate_args)

        elapsed = time.monotonic() - start
        assert elapsed < 0.5, (
            f"100 direct write+validate cycles took {elapsed:.2f}s, expected < 0.5s"
        )

    @pytest.mark.slow
    def test_subprocess_under_2_seconds(self, cp_output_dir: Path) -> None:
        """10 subprocess write+validate cycles complete in under 2 seconds.

        Tests CLI integration (subprocess overhead) with reduced cycle count."""
        import time

        start = time.monotonic()

        for i in range(10):
            w = _run_checkpoint(
                ["write", "search", "--count", str(i)],
                str(cp_output_dir),
            )
            assert w.returncode == 0, f"write cycle {i} failed: {w.stderr}"

            v = _run_checkpoint(
                ["validate", "search"],
                str(cp_output_dir),
            )
            assert v.returncode == 0, f"validate cycle {i} failed: {v.stderr}"

        elapsed = time.monotonic() - start
        assert elapsed < 2.0, (
            f"10 subprocess write+validate cycles took {elapsed:.2f}s, expected < 2.0s"
        )


# ---------------------------------------------------------------------------
# Tests for list-active-role-types subcommand
# ---------------------------------------------------------------------------


def _run_list_active_role_types(
    context_path: str,
) -> subprocess.CompletedProcess:
    """Run list-active-role-types subcommand with a given context path."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "list-active-role-types",
        "--context-path",
        context_path,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def _write_context_md(tmp_path: Path, content: str) -> Path:
    """Write a mock context.md file and return its path."""
    context_file = tmp_path / "context.md"
    context_file.write_text(content, encoding="utf-8")
    return context_file


class TestListActiveRoleTypes:
    """Tests for the list-active-role-types subcommand of manage_state.py."""

    def test_extracts_role_types_from_target_section(self, tmp_path: Path) -> None:
        """context.md with ## Target containing role types returns newline-separated slugs, exit 0."""
        context = _write_context_md(tmp_path, (
            "# Context\n\n"
            "## Profile\n\n"
            "Some profile info.\n\n"
            "## Target\n\n"
            "- Community Manager\n"
            "- Marketing Manager\n\n"
            "## Industries\n\n"
            "- AI Startups\n"
        ))

        result = _run_list_active_role_types(str(context))
        assert result.returncode == 0, f"list-active-role-types failed: {result.stderr}"

        slugs = result.stdout.strip().splitlines()
        assert "community-manager" in slugs
        assert "marketing-manager" in slugs

    def test_returns_empty_when_no_target_section(self, tmp_path: Path) -> None:
        """context.md without ## Target section returns empty output, exit 0."""
        context = _write_context_md(tmp_path, (
            "# Context\n\n"
            "## Profile\n\n"
            "Some profile info.\n\n"
            "## Industries\n\n"
            "- AI Startups\n"
        ))

        result = _run_list_active_role_types(str(context))
        assert result.returncode == 0, f"list-active-role-types failed: {result.stderr}"

        output = result.stdout.strip()
        assert output == "", f"expected empty output, got: {output!r}"

    def test_handles_multiple_role_types(self, tmp_path: Path) -> None:
        """context.md with multiple role types listed returns all of them."""
        context = _write_context_md(tmp_path, (
            "# Context\n\n"
            "## Target\n\n"
            "- AI Agent Engineer\n"
            "- Community Manager\n"
            "- Developer Relations\n"
            "- Growth Marketing Lead\n\n"
            "## Industries\n\n"
            "- AI\n"
        ))

        result = _run_list_active_role_types(str(context))
        assert result.returncode == 0, f"list-active-role-types failed: {result.stderr}"

        slugs = result.stdout.strip().splitlines()
        assert len(slugs) == 4, f"expected 4 slugs, got {len(slugs)}: {slugs}"
        assert "ai-agent-engineer" in slugs
        assert "community-manager" in slugs
        assert "developer-relations" in slugs
        assert "growth-marketing-lead" in slugs

    def test_exits_one_when_context_file_missing(self, tmp_path: Path) -> None:
        """Nonexistent context path exits 1 with error message."""
        nonexistent = str(tmp_path / "nonexistent" / "context.md")

        result = _run_list_active_role_types(nonexistent)
        assert result.returncode == 1, (
            f"expected exit code 1 for missing file, got {result.returncode}"
        )
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower(), (
            f"expected error message about missing file, got: {result.stderr!r}"
        )


# ---------------------------------------------------------------------------
# Tests for verify-clean-working-tree subcommand
# ---------------------------------------------------------------------------


def _run_verify_clean_working_tree(
    verified_path: str,
) -> subprocess.CompletedProcess:
    """Run verify-clean-working-tree subcommand with a given verified path."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "verify-clean-working-tree",
        "--verified-path",
        verified_path,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Run a git command in the given repo directory."""
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
        text=True,
    )


def _init_git_repo(repo: Path) -> None:
    """Initialize a git repo with user config at the given path."""
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@test.com")
    _git(repo, "config", "user.name", "Test")


class TestVerifyCleanWorkingTree:
    """Tests for the verify-clean-working-tree subcommand of manage_state.py."""

    def test_clean_repo_exits_zero(self, tmp_path: Path) -> None:
        """All files committed in a git repo, exit 0."""
        repo = tmp_path / "repo"
        _init_git_repo(repo)

        # Create verified directory with a file, commit everything
        verified = repo / "output" / "verified"
        verified.mkdir(parents=True)
        (verified / "test-role" / "job.json").parent.mkdir(parents=True)
        (verified / "test-role" / "job.json").write_text('{"title": "test"}')
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "initial")

        result = _run_verify_clean_working_tree(str(verified))
        assert result.returncode == 0, (
            f"clean repo should exit 0: {result.stderr}"
        )

    def test_uncommitted_files_exit_one(self, tmp_path: Path) -> None:
        """Untracked files in output/verified/, exit 1."""
        repo = tmp_path / "repo"
        _init_git_repo(repo)

        # Create and commit initial file
        verified = repo / "output" / "verified"
        verified.mkdir(parents=True)
        (verified / "test-role").mkdir(parents=True)
        (verified / "test-role" / "job1.json").write_text('{"title": "test1"}')
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "initial")

        # Add an untracked file (not committed)
        (verified / "test-role" / "job2.json").write_text('{"title": "test2"}')

        result = _run_verify_clean_working_tree(str(verified))
        assert result.returncode == 1, (
            f"untracked files should cause exit 1: stdout={result.stdout}"
        )

    def test_modified_file_exit_one(self, tmp_path: Path) -> None:
        """Modified committed file, exit 1."""
        repo = tmp_path / "repo"
        _init_git_repo(repo)

        # Create and commit a file
        verified = repo / "output" / "verified"
        verified.mkdir(parents=True)
        (verified / "test-role").mkdir(parents=True)
        job_file = verified / "test-role" / "job.json"
        job_file.write_text('{"title": "original"}')
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "initial")

        # Modify the committed file without staging/committing
        job_file.write_text('{"title": "modified"}')

        result = _run_verify_clean_working_tree(str(verified))
        assert result.returncode == 1, (
            f"modified file should cause exit 1: stdout={result.stdout}"
        )

    def test_empty_verified_dir_exits_zero(self, tmp_path: Path) -> None:
        """No verified dir, exit 0."""
        repo = tmp_path / "repo"
        _init_git_repo(repo)

        # Create a dummy file so we can make an initial commit
        (repo / "README.md").write_text("placeholder")
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "initial")

        # Point to a non-existent verified path
        nonexistent_verified = repo / "output" / "verified"

        result = _run_verify_clean_working_tree(str(nonexistent_verified))
        assert result.returncode == 0, (
            f"non-existent verified dir should exit 0: {result.stderr}"
        )


# ---------------------------------------------------------------------------
# Tests for verify-channels-dispatched subcommand
# ---------------------------------------------------------------------------

EXPECTED_CHANNELS = [
    "direct-career-pages",
    "industry-job-boards",
    "jobspy-aggregator",
    "niche-newsletters",
    "web-search-discovery",
]


def _run_verify_channels_dispatched(
    output_dir: str, *, run_date: str | None = None,
) -> subprocess.CompletedProcess:
    """Run verify-channels-dispatched subcommand with a given output dir."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "verify-channels-dispatched",
        "--output-dir",
        output_dir,
    ]
    if run_date is not None:
        cmd.extend(["--run-date", run_date])
    return subprocess.run(cmd, capture_output=True, text=True)


class TestVerifyChannelsDispatched:
    """Tests for the verify-channels-dispatched subcommand of manage_state.py."""

    def test_all_channels_present_exits_zero(self, tmp_path: Path) -> None:
        """All 5 .done files with today's mtime, exit 0."""
        output_dir = tmp_path / "output"
        channels_dir = output_dir / ".channels"
        channels_dir.mkdir(parents=True)

        today = datetime.now().strftime("%Y-%m-%d")
        for channel in EXPECTED_CHANNELS:
            (channels_dir / f"{channel}.done").write_text("ok")

        result = _run_verify_channels_dispatched(str(output_dir), run_date=today)
        assert result.returncode == 0, (
            f"all channels present should exit 0: {result.stderr}"
        )

    def test_missing_channel_exits_one(self, tmp_path: Path) -> None:
        """4 of 5 .done files present, exit 1 naming missing channel."""
        output_dir = tmp_path / "output"
        channels_dir = output_dir / ".channels"
        channels_dir.mkdir(parents=True)

        today = datetime.now().strftime("%Y-%m-%d")
        # Create only 4 of 5 channels (skip niche-newsletters)
        for channel in EXPECTED_CHANNELS:
            if channel != "niche-newsletters":
                (channels_dir / f"{channel}.done").write_text("ok")

        result = _run_verify_channels_dispatched(str(output_dir), run_date=today)
        assert result.returncode == 1, (
            f"missing channel should exit 1: stdout={result.stdout}"
        )
        assert "niche-newsletters" in result.stderr, (
            f"should name missing channel: {result.stderr!r}"
        )

    def test_stale_mtime_exits_one(self, tmp_path: Path) -> None:
        """One .done file with yesterday's mtime, exit 1."""
        import time

        output_dir = tmp_path / "output"
        channels_dir = output_dir / ".channels"
        channels_dir.mkdir(parents=True)

        today = datetime.now().strftime("%Y-%m-%d")
        for channel in EXPECTED_CHANNELS:
            (channels_dir / f"{channel}.done").write_text("ok")

        # Set one channel's mtime to yesterday
        stale_file = channels_dir / "jobspy-aggregator.done"
        yesterday_ts = time.time() - 86400
        os.utime(stale_file, (yesterday_ts, yesterday_ts))

        result = _run_verify_channels_dispatched(str(output_dir), run_date=today)
        assert result.returncode == 1, (
            f"stale mtime should exit 1: stdout={result.stdout}"
        )
        assert "jobspy-aggregator" in result.stderr, (
            f"should name stale channel: {result.stderr!r}"
        )

    def test_no_channels_dir_exits_one(self, tmp_path: Path) -> None:
        """No .channels/ directory, exit 1 with all 5 named."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)
        # Do NOT create .channels/ directory

        today = datetime.now().strftime("%Y-%m-%d")
        result = _run_verify_channels_dispatched(str(output_dir), run_date=today)
        assert result.returncode == 1, (
            f"no channels dir should exit 1: stdout={result.stdout}"
        )
        # All 5 channels should be named as missing
        for channel in EXPECTED_CHANNELS:
            assert channel in result.stderr, (
                f"should name {channel} as missing: {result.stderr!r}"
            )


# ---------------------------------------------------------------------------
# Tests for verify-session-state-updated subcommand
# ---------------------------------------------------------------------------


def _run_verify_session_state_updated(
    session_state_path: str,
    *,
    run_date: str | None = None,
) -> subprocess.CompletedProcess:
    """Run verify-session-state-updated subcommand with a given path."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "verify-session-state-updated",
        "--session-state-path",
        session_state_path,
    ]
    if run_date is not None:
        cmd.extend(["--run-date", run_date])
    return subprocess.run(cmd, capture_output=True, text=True)


class TestVerifySessionStateUpdated:
    """Tests for the verify-session-state-updated subcommand of manage_state.py."""

    def test_session_state_modified_today_exits_zero(self, tmp_path: Path) -> None:
        """session-state.md mtime is today, exit 0."""
        session_state = tmp_path / "session-state.md"
        session_state.write_text("# Session State\n\nSome content.\n")

        today = datetime.now().strftime("%Y-%m-%d")
        result = _run_verify_session_state_updated(
            str(session_state), run_date=today,
        )
        assert result.returncode == 0, (
            f"session-state.md modified today should exit 0: {result.stderr}"
        )

    def test_session_state_stale_exits_one(self, tmp_path: Path) -> None:
        """session-state.md mtime is yesterday, exit 1."""
        session_state = tmp_path / "session-state.md"
        session_state.write_text("# Session State\n\nStale content.\n")

        # Set mtime to yesterday
        yesterday_ts = datetime.now().timestamp() - 86400
        os.utime(session_state, (yesterday_ts, yesterday_ts))

        today = datetime.now().strftime("%Y-%m-%d")
        result = _run_verify_session_state_updated(
            str(session_state), run_date=today,
        )
        assert result.returncode == 1, (
            f"stale session-state.md should exit 1: stdout={result.stdout}"
        )

    def test_session_state_missing_exits_one(self, tmp_path: Path) -> None:
        """No session-state.md file, exit 1."""
        nonexistent = str(tmp_path / "nonexistent" / "session-state.md")

        today = datetime.now().strftime("%Y-%m-%d")
        result = _run_verify_session_state_updated(nonexistent, run_date=today)
        assert result.returncode == 1, (
            f"missing session-state.md should exit 1: stdout={result.stdout}"
        )


# ---------------------------------------------------------------------------
# TestValidateSchema
# ---------------------------------------------------------------------------

# Import CANONICAL_FIELDS from manage_state.py as single source of truth.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
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


from helpers import _make_job, _write_job, _run_dedup  # noqa: E402, F401


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


# ---------------------------------------------------------------------------
# TestSlugExtraction
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Tests for verify-and-commit subcommand
# ---------------------------------------------------------------------------


class TestVerifyAndCommit:
    """Tests for the verify-and-commit subcommand of manage_state.py."""

    def test_dirty_output_stages_commits_exits_zero(self, tmp_path: Path) -> None:
        """Dirty output/ directory: stages, commits, exits 0."""
        repo = tmp_path / "repo"
        _init_git_repo(repo)

        # Create initial commit
        (repo / "README.md").write_text("placeholder")
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "initial")

        # Create dirty output directory with a new file
        output_dir = repo / "output"
        verified_dir = output_dir / "verified" / "ai-engineer"
        verified_dir.mkdir(parents=True)
        (verified_dir / "job.json").write_text('{"title": "test"}')

        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-and-commit",
                "--output-dir",
                str(output_dir),
                "--phase-label",
                "search",
                "--no-push",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo),
        )
        assert result.returncode == 0, (
            f"dirty output should stage+commit and exit 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        # Verify the file is now committed
        status = _git(repo, "status", "--porcelain", str(output_dir))
        assert status.stdout.strip() == "", (
            f"output should be clean after commit: {status.stdout}"
        )

    def test_clean_output_exits_zero(self, tmp_path: Path) -> None:
        """Clean output/ directory (nothing to commit): exits 0."""
        repo = tmp_path / "repo"
        _init_git_repo(repo)

        # Create initial commit with output dir
        output_dir = repo / "output"
        verified_dir = output_dir / "verified" / "ai-engineer"
        verified_dir.mkdir(parents=True)
        (verified_dir / "job.json").write_text('{"title": "test"}')
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "initial")

        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-and-commit",
                "--output-dir",
                str(output_dir),
                "--phase-label",
                "search",
                "--no-push",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo),
        )
        assert result.returncode == 0, (
            f"clean output should exit 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_commit_message_contains_phase_label(self, tmp_path: Path) -> None:
        """Commit message includes the phase label."""
        repo = tmp_path / "repo"
        _init_git_repo(repo)

        (repo / "README.md").write_text("placeholder")
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "initial")

        output_dir = repo / "output"
        verified_dir = output_dir / "verified" / "ai-engineer"
        verified_dir.mkdir(parents=True)
        (verified_dir / "job.json").write_text('{"title": "test"}')

        subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-and-commit",
                "--output-dir",
                str(output_dir),
                "--phase-label",
                "search",
                "--no-push",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo),
        )
        log = _git(repo, "log", "--oneline", "-1")
        assert "search" in log.stdout.lower(), (
            f"commit message should contain phase label 'search': {log.stdout}"
        )


# ---------------------------------------------------------------------------
# Tests for verify-session-state-written subcommand
# ---------------------------------------------------------------------------


class TestVerifySessionStateWritten:
    """Tests for the verify-session-state-written subcommand."""

    def test_has_today_date_exits_zero(self, tmp_path: Path) -> None:
        """session-state.md contains today's date entry, exits 0."""
        session_state = tmp_path / "session-state.md"
        session_state.write_text(
            "# Session State\n\n## 2026-02-27\n\nSearch batch 1 complete.\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-session-state-written",
                "--session-state-path",
                str(session_state),
                "--run-date",
                "2026-02-27",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            f"session-state.md with today's date should exit 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_missing_today_date_exits_one(self, tmp_path: Path) -> None:
        """session-state.md without today's date entry, exits 1."""
        session_state = tmp_path / "session-state.md"
        session_state.write_text(
            "# Session State\n\n## 2026-02-25\n\nOld batch data.\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-session-state-written",
                "--session-state-path",
                str(session_state),
                "--run-date",
                "2026-02-27",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 1, (
            f"session-state.md without today's date should exit 1.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_missing_file_exits_one(self, tmp_path: Path) -> None:
        """Missing session-state.md file, exits 1."""
        nonexistent = str(tmp_path / "nonexistent" / "session-state.md")
        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-session-state-written",
                "--session-state-path",
                nonexistent,
                "--run-date",
                "2026-02-27",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 1, (
            f"missing session-state.md should exit 1.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_date_in_content_not_heading_exits_zero(self, tmp_path: Path) -> None:
        """Date appears in body text (not just heading), exits 0."""
        session_state = tmp_path / "session-state.md"
        session_state.write_text(
            "# Session State\n\nRun date: 2026-02-27. Batch complete.\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-session-state-written",
                "--session-state-path",
                str(session_state),
                "--run-date",
                "2026-02-27",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            f"date in body text should still count.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


class TestDedupSafety:
    """Tests for --active-only, --dry-run, and safety bound on dedup subcommand."""

    def test_active_only_flag_accepted(self, tmp_path: Path) -> None:
        """dedup subcommand must accept --active-only flag."""
        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "dedup", "--help"],
            capture_output=True, text=True,
        )
        assert "--active-only" in result.stdout, (
            "dedup subcommand must accept --active-only flag"
        )

    def test_dry_run_flag_accepted(self, tmp_path: Path) -> None:
        """dedup subcommand must accept --dry-run flag."""
        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "dedup", "--help"],
            capture_output=True, text=True,
        )
        assert "--dry-run" in result.stdout, (
            "dedup subcommand must accept --dry-run flag"
        )


class TestSlugFormat:
    """Test that list-active-role-types produces valid slug format."""

    def test_slug_format_regex(self, tmp_path: Path) -> None:
        """Each slug line from list-active-role-types must match ^[a-z0-9-]+$."""
        import re
        context = tmp_path / "context.md"
        context.write_text(
            "# Context\n\n## Target\n- AI Engineer\n- Product Manager\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "list-active-role-types",
             "--context-path", str(context)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        slug_pattern = re.compile(r"^[a-z0-9-]+$")
        for line in result.stdout.strip().splitlines():
            assert slug_pattern.match(line.strip()), (
                f"Slug '{line.strip()}' does not match ^[a-z0-9-]+$ format"
            )

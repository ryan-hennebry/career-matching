"""Tests for _check_safety_bound gap-aware threshold adjustment.

When gap between last_run_date and today exceeds 7 days, threshold
auto-adjusts from 50% to 90%.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import manage_state

from conftest import make_valid_job


def _make_jobs_and_archive(total: int, archived: int, role: str = "ai-engineer"):
    jobs = []
    to_archive = {}
    for i in range(total):
        job = make_valid_job(
            job_id=f"job-{i}", company=f"Co{i}", title=f"Title{i}",
            score=80, role_type=role,
        )
        job["_filepath"] = Path(f"/tmp/fake/{role}/job-{i}.json")
        job["_role"] = role
        job["_filename"] = f"job-{i}.json"
        jobs.append(job)
    for i in range(archived):
        to_archive[jobs[i]["_filepath"]] = jobs[i]
    return jobs, to_archive


class TestSafetyBoundGap:

    def test_1_day_gap_uses_default(self) -> None:
        """1-day gap: 30% archival passes with 50% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 3)
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=yesterday, today=today)
        assert errors == []

    def test_7_day_gap_uses_default(self) -> None:
        """7-day gap: 60% archival fails with 50% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 6)
        today = datetime.now().strftime("%Y-%m-%d")
        seven_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=seven_ago, today=today)
        assert len(errors) > 0

    def test_8_day_gap_adjusts_to_90(self) -> None:
        """8-day gap: 60% archival passes with 90% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 6)
        today = datetime.now().strftime("%Y-%m-%d")
        eight_ago = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=eight_ago, today=today)
        assert errors == []

    def test_30_day_gap_adjusts_to_90(self) -> None:
        """30-day gap: 60% archival passes with 90% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 6)
        today = datetime.now().strftime("%Y-%m-%d")
        thirty_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=thirty_ago, today=today)
        assert errors == []

    def test_8_day_gap_still_rejects_above_90(self) -> None:
        """8-day gap: 95% archival still fails."""
        jobs, to_archive = _make_jobs_and_archive(20, 19)
        today = datetime.now().strftime("%Y-%m-%d")
        eight_ago = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=eight_ago, today=today)
        assert len(errors) > 0

    def test_no_last_run_date_uses_default(self) -> None:
        """None last_run_date: 60% fails with 50% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 6)
        today = datetime.now().strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=None, today=today)
        assert len(errors) > 0

    def test_default_args_both_none_uses_default(self) -> None:
        """Both last_run_date and today as None: falls back to 50% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 6)
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=None, today=None)
        assert len(errors) > 0

    def test_default_args_30pct_passes(self) -> None:
        """Both args None, 30% archival: passes with default 50% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 3)
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=None, today=None)
        assert errors == []

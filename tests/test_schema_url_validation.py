"""Tests for enhanced validate-schema URL and active_status checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conftest import make_valid_job, write_job

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run_validate_schema(output_dir: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MANAGE_STATE), "validate-schema", "--output-dir", output_dir],
        capture_output=True, text=True,
    )


class TestSchemaURLValidation:

    def test_valid_ats_url_passes(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "ai-engineer", "valid.json", make_valid_job())
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0

    def test_generic_careers_page_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(job_url="https://example.com/careers")
        write_job(output_dir / "verified" / "ai-engineer", "bad.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1

    def test_generic_jobs_without_id_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(job_url="https://example.com/jobs")
        write_job(output_dir / "verified" / "ai-engineer", "bad.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1

    def test_url_with_job_id_segment_passes(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(job_url="https://careers.example.com/positions/87654")
        write_job(output_dir / "verified" / "ai-engineer", "good.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0

    def test_url_with_uuid_passes(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(
            job_url="https://jobs.lever.co/acme/a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        write_job(output_dir / "verified" / "ai-engineer", "uuid.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0

    def test_null_active_status_after_verification_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(active_status=None, verification_date="2026-03-20")
        write_job(output_dir / "verified" / "ai-engineer", "null.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1

    def test_linkedin_url_passes(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(job_url="https://www.linkedin.com/jobs/view/4344764433")
        write_job(output_dir / "verified" / "ai-engineer", "li.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0

    def test_pre_existing_valid_job_still_passes(self, tmp_path: Path) -> None:
        """Regression: a known-good fixture that passed before enhancements must still pass."""
        output_dir = tmp_path / "output"
        known_good = make_valid_job(
            job_url="https://boards.greenhouse.io/acme/jobs/12345",
            score=85, status="verified",
        )
        write_job(output_dir / "verified" / "ai-engineer", "known-good.json", known_good)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0, f"Known-good fixture broke: {result.stderr}"

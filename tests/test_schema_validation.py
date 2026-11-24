"""Regression tests for legacy verified-job schema validation."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _make_valid_job(**overrides) -> dict:
    """Create a valid 10-field job entry."""
    defaults = {
        "job_id": "test-001", "title": "Engineer", "company": "TestCo",
        "job_url": "https://example.com/jobs/123456", "role_type": "ai-engineer",
        "score": 85, "source_channel": "direct-career-pages",
        "run_date": "2026-02-27", "location": "Remote", "status": "verified",
    }
    defaults.update(overrides)
    return defaults


def _run_validate_schema(output_dir: str) -> subprocess.CompletedProcess:
    """Run validate-schema subcommand."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "validate-schema",
        "--output-dir",
        output_dir,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestSchemaValidation:
    """Tests for schema validation of verified job JSONs."""

    def test_valid_10_field_job_passes(self, tmp_path: Path) -> None:
        """Valid job with all 10 canonical fields passes validation."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True)
        (role_dir / "valid-job.json").write_text(
            json.dumps(_make_valid_job()), encoding="utf-8",
        )
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0, (
            f"valid 10-field job should pass.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_missing_fields_fails(self, tmp_path: Path) -> None:
        """Job missing required fields fails validation."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True)
        incomplete_job = {"title": "Engineer", "company": "TestCo"}
        (role_dir / "bad-job.json").write_text(
            json.dumps(incomplete_job), encoding="utf-8",
        )
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1, (
            f"job missing fields should fail.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_extra_fields_tolerated(self, tmp_path: Path) -> None:
        """Job with extra fields beyond the 10 canonical still passes."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True)
        job = _make_valid_job(salary="$120k", description="Great role")
        (role_dir / "extra-fields.json").write_text(
            json.dumps(job), encoding="utf-8",
        )
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0, (
            f"extra fields should be tolerated.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

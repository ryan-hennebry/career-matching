"""Tests for validate-presentation subcommand.

Validates verified JSON files are presentation-ready: ATS URLs, non-null
active_status, no expired entries in active list.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conftest import make_valid_job, write_job

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run_validate_presentation(output_dir: str, role_types: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MANAGE_STATE), "validate-presentation",
         "--output-dir", output_dir, "--role-types", role_types],
        capture_output=True, text=True,
    )


class TestValidatePresentation:

    def test_all_valid_passes(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "ai-engineer", "valid.json", make_valid_job())
        result = _run_validate_presentation(str(output_dir), "ai-engineer")
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["passed"] is True
        assert output["violations"] == []

    def test_generic_careers_url_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(job_url="https://example.com/careers")
        write_job(output_dir / "verified" / "ai-engineer", "bad.json", job)
        result = _run_validate_presentation(str(output_dir), "ai-engineer")
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert output["passed"] is False
        assert len(output["violations"]) >= 1

    def test_null_active_status_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(active_status=None)
        write_job(output_dir / "verified" / "ai-engineer", "null.json", job)
        result = _run_validate_presentation(str(output_dir), "ai-engineer")
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert any("active_status" in v for v in output["violations"])

    def test_expired_in_active_list_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(active_status="expired")
        write_job(output_dir / "verified" / "ai-engineer", "expired.json", job)
        result = _run_validate_presentation(str(output_dir), "ai-engineer")
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert any("expired" in v.lower() for v in output["violations"])

    def test_mixed_valid_and_invalid(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "ai-engineer", "good.json", make_valid_job())
        write_job(output_dir / "verified" / "ai-engineer", "bad-url.json",
                   make_valid_job(job_url="https://example.com/jobs"))
        write_job(output_dir / "verified" / "ai-engineer", "null-status.json",
                   make_valid_job(active_status=None))
        result = _run_validate_presentation(str(output_dir), "ai-engineer")
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert len(output["violations"]) >= 2

    def test_multiple_role_types(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "ai-engineer", "good.json", make_valid_job())
        write_job(output_dir / "verified" / "founder-s-associate", "bad.json",
                   make_valid_job(active_status="expired"))
        result = _run_validate_presentation(str(output_dir), "ai-engineer,founder-s-associate")
        assert result.returncode == 1

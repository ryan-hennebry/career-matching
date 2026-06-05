"""Tests for dedup --role-types slug format requirement.

Confirms --role-types must use directory slug format (kebab-case).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conftest import write_job

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run_dedup(output_dir: str, *, role_types: str | None = None,
               no_safety_bound: bool = False) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(MANAGE_STATE), "dedup", "--output-dir", output_dir]
    if role_types is not None:
        cmd.extend(["--role-types", role_types])
    if no_safety_bound:
        cmd.append("--no-safety-bound")
    return subprocess.run(cmd, capture_output=True, text=True)


def _make_low_score_job(role: str) -> dict:
    return {"company": "TestCo", "title": "Junior Role", "score": 40,
            "job_url": f"https://example.com/jobs/{role}/123",
            "role_type": role, "location": "Remote", "source": "linkedin"}


class TestDedupRoleTypesSlugs:

    def test_slug_format_finds_files(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "founder-s-associate",
                   "testco-junior.json", _make_low_score_job("founder-s-associate"))
        result = _run_dedup(str(output_dir), role_types="founder-s-associate",
                           no_safety_bound=True)
        assert result.returncode == 0
        summary = json.loads(result.stdout)
        assert summary["total_input"] > 0

    def test_display_name_format_finds_zero_files(self, tmp_path: Path) -> None:
        """Display name format does NOT match directory slugs."""
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "founder-s-associate",
                   "testco-junior.json", _make_low_score_job("founder-s-associate"))
        result = _run_dedup(str(output_dir), role_types="Founder's Associate",
                           no_safety_bound=True)
        assert result.returncode == 0
        summary = json.loads(result.stdout)
        assert summary["total_input"] == 0

    def test_empty_role_types_returns_zero(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "ai-engineer",
                   "job.json", _make_low_score_job("ai-engineer"))
        result = _run_dedup(str(output_dir), role_types="")
        assert result.returncode == 0
        summary = json.loads(result.stdout)
        assert summary["total_input"] == 0

"""Tests for verify-and-commit --check-only flag."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


class TestVerifyAndCommitCheckOnly:

    def test_check_only_clean_exits_zero(self, tmp_path: Path) -> None:
        """Clean git repo with no uncommitted output files exits 0."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"],
                       cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"],
                       cwd=str(tmp_path), capture_output=True)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / ".gitkeep").write_text("")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"],
                       cwd=str(tmp_path), capture_output=True)

        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "verify-and-commit",
             "--output-dir", str(output_dir), "--phase-label", "search",
             "--check-only"],
            capture_output=True, text=True, cwd=str(tmp_path))
        assert result.returncode == 0

    def test_check_only_dirty_exits_nonzero(self, tmp_path: Path) -> None:
        """Git repo with uncommitted output files exits non-zero."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"],
                       cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"],
                       cwd=str(tmp_path), capture_output=True)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / ".gitkeep").write_text("")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"],
                       cwd=str(tmp_path), capture_output=True)
        # Create uncommitted file
        (output_dir / "new-job.json").write_text('{"test": true}')

        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "verify-and-commit",
             "--output-dir", str(output_dir), "--phase-label", "search",
             "--check-only"],
            capture_output=True, text=True, cwd=str(tmp_path))
        assert result.returncode != 0

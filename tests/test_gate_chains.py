"""Regression tests for gate chaining.

Tests that verify-and-commit, validate-presentation, and verify-before-archive
enforce their preconditions correctly.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from conftest import make_valid_job

import manage_state

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


class TestVerifyAndCommitGate:

    def test_clean_git_repo_exits_zero(self, tmp_path: Path) -> None:
        """Clean git repo with nothing to commit exits 0."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"],
                       cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"],
                       cwd=str(tmp_path), capture_output=True)
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / ".gitkeep").write_text("")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"],
                       cwd=str(tmp_path), capture_output=True)

        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "verify-and-commit",
             "--output-dir", str(tmp_path / "output"), "--phase-label", "search",
             "--no-push"],
            capture_output=True, text=True, cwd=str(tmp_path))
        assert result.returncode == 0


class TestVerifyBeforeArchiveGate:
    """Tests unique to the verify-and-commit -> verify-before-archive gate chain.

    Note: validate-presentation pass/fail tests are already covered in
    test_validate_presentation.py — not duplicated here.
    """

    def test_aggregator_url_returns_unverified(self, tmp_path: Path) -> None:
        """Aggregator URL through gate chain returns unverified, not live."""
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(make_valid_job(
            job_url="https://www.indeed.com/viewjob?jk=abc123")), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://www.indeed.com/viewjob?jk=abc123"
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "unverified"

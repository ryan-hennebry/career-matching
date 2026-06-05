"""Tests for verify-before-archive subcommand.

Mocks HTTP HEAD requests to validate URL liveness classification.
Uses source-first strategy: aggregator URLs return 'unverified' instead of
'live' on HTTP 200, since aggregators return 200 for expired listings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from conftest import make_valid_job


class TestVerifyBeforeArchiveUnit:
    """Unit tests using direct import and mocking requests.head."""

    def test_live_url_200(self, tmp_path: Path) -> None:
        """HTTP 200 -> status=live."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test-job.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "live"
        assert result["evidence"] == "HTTP 200"

    def test_live_url_301(self, tmp_path: Path) -> None:
        """HTTP 301 redirect -> status=live."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 301
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "live"

    def test_expired_url_404(self, tmp_path: Path) -> None:
        """HTTP 404 -> status=expired."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "expired"
        assert result["evidence"] == "HTTP 404"

    def test_expired_url_410(self, tmp_path: Path) -> None:
        """HTTP 410 Gone -> status=expired."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 410
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "expired"

    def test_timeout_unreachable(self, tmp_path: Path) -> None:
        """Timeout -> status=unreachable."""
        import manage_state
        import requests as req_lib

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        with patch("manage_state.requests.head", side_effect=req_lib.Timeout("timed out")):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "unreachable"
        assert result["evidence"] == "timeout"

    def test_connection_error_unreachable(self, tmp_path: Path) -> None:
        """Connection error -> status=unreachable."""
        import manage_state
        import requests as req_lib

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        with patch("manage_state.requests.head", side_effect=req_lib.ConnectionError("refused")):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "unreachable"
        assert result["evidence"] == "error: refused"

    def test_aggregator_url_200_returns_unverified(self, tmp_path: Path) -> None:
        """Aggregator URL with HTTP 200 -> status=unverified (source-first strategy)."""
        import manage_state

        job = make_valid_job(
            job_url="https://www.indeed.com/viewjob?jk=abc123",
            active_status="verified",
        )
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "unverified"
        assert result["url_type"] == "aggregator"

    def test_read_only_by_default(self, tmp_path: Path) -> None:
        """Default mode does NOT write to the JSON file."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("manage_state.requests.head", return_value=mock_response):
            manage_state.verify_before_archive(job_file)

        updated = json.loads(job_file.read_text(encoding="utf-8"))
        assert updated["active_status"] == "verified"  # unchanged

    def test_write_flag_updates_file(self, tmp_path: Path) -> None:
        """With write=True, verdict IS written to the JSON file."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("manage_state.requests.head", return_value=mock_response):
            manage_state.verify_before_archive(job_file, write=True)

        updated = json.loads(job_file.read_text(encoding="utf-8"))
        assert updated["active_status"] == "expired"

"""Tests for manage_state.py validate-url-type subcommand (9 tests).

Verifies URL classification: known ATS patterns -> source,
aggregator patterns -> aggregator, unknown -> unknown.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run_validate_url_type(url: str) -> dict:
    """Run validate-url-type subcommand and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, str(MANAGE_STATE), "validate-url-type", "--url", url],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


class TestValidateUrlType:
    """Tests for the validate-url-type subcommand of manage_state.py."""

    def test_greenhouse_url_is_source(self) -> None:
        output = _run_validate_url_type("https://boards.greenhouse.io/acme/jobs/1234567")
        assert output["type"] == "source"
        assert output["pattern_matched"] == "greenhouse"
        assert output["url"] == "https://boards.greenhouse.io/acme/jobs/1234567"

    def test_ashby_url_is_source(self) -> None:
        output = _run_validate_url_type("https://jobs.ashbyhq.com/acme/abc-123")
        assert output["type"] == "source"
        assert output["pattern_matched"] == "ashby"

    def test_lever_url_is_source(self) -> None:
        output = _run_validate_url_type("https://jobs.lever.co/acme/some-position-id")
        assert output["type"] == "source"
        assert output["pattern_matched"] == "lever"

    def test_workable_url_is_source(self) -> None:
        output = _run_validate_url_type("https://apply.workable.com/acme-corp/j/ABC123/")
        assert output["type"] == "source"
        assert output["pattern_matched"] == "workable"

    def test_rippling_url_is_source(self) -> None:
        output = _run_validate_url_type("https://ats.rippling.com/acme/jobs/abc-def-123")
        assert output["type"] == "source"
        assert output["pattern_matched"] == "rippling"

    def test_indeed_url_is_aggregator(self) -> None:
        output = _run_validate_url_type("https://www.indeed.com/viewjob?jk=abc123def456")
        assert output["type"] == "aggregator"
        assert output["pattern_matched"] == "indeed"

    def test_linkedin_url_is_aggregator(self) -> None:
        output = _run_validate_url_type("https://www.linkedin.com/jobs/view/4344764433")
        assert output["type"] == "aggregator"
        assert output["pattern_matched"] == "linkedin"

    def test_glassdoor_url_is_aggregator(self) -> None:
        output = _run_validate_url_type("https://www.glassdoor.com/job-listing/engineer-acme-JV_IC12345.htm")
        assert output["type"] == "aggregator"
        assert output["pattern_matched"] == "glassdoor"

    def test_unknown_domain_returns_unknown(self) -> None:
        output = _run_validate_url_type("https://www.randomstartup.com/careers/engineer")
        assert output["type"] == "unknown"
        assert output["pattern_matched"] == "unknown"
        assert output["url"] == "https://www.randomstartup.com/careers/engineer"

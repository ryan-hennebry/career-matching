"""Tests for filter_jobs.py - universal title filtering."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def run_filter(input_jobs: list[dict[str, Any]], exclude_titles: list[str]) -> list[dict[str, Any]]:
    """Helper to run filter_jobs.py and return filtered jobs."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump({"jobs": input_jobs}, f)
        input_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        output_path = f.name

    script_path = Path(__file__).parent.parent / "scripts" / "filter_jobs.py"

    cmd = ["python3", str(script_path), input_path, "--output", output_path]
    if exclude_titles:
        cmd.extend(["--exclude-titles"] + exclude_titles)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {result.stderr}")

    with open(output_path, encoding='utf-8') as f:
        return json.load(f)["jobs"]


class TestFilterJobs:
    """Test suite for filter_jobs.py."""

    def test_excludes_matching_titles_case_insensitive(self) -> None:
        """Jobs with excluded title keywords are removed (case-insensitive)."""
        jobs = [
            {"id": "1", "title": "Marketing Manager"},
            {"id": "2", "title": "SENIOR Marketing Manager"},
            {"id": "3", "title": "Lead Marketing Manager"},
        ]

        result = run_filter(jobs, ["senior", "lead"])

        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_preserves_all_fields(self) -> None:
        """Filtered jobs retain all original fields."""
        jobs = [
            {
                "id": "1",
                "title": "Marketing Manager",
                "company": "Acme Inc",
                "location": "London",
                "salary_min": 40000,
                "salary_max": 50000,
                "url": "https://example.com/job/1",
            }
        ]

        result = run_filter(jobs, ["senior"])

        assert result[0] == jobs[0]

    def test_no_exclusions_returns_all(self) -> None:
        """Without exclusions, all jobs pass through."""
        jobs = [
            {"id": "1", "title": "Senior Manager"},
            {"id": "2", "title": "Junior Associate"},
        ]

        result = run_filter(jobs, [])

        assert len(result) == 2

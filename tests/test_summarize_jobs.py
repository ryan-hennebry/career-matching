"""Tests for summarize_jobs.py - context-efficient job summaries."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def run_summarize(jobs: list[dict[str, Any]], max_jobs: int = 20) -> str:
    """Helper to run summarize_jobs.py and return output."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump({"jobs": jobs}, f)
        input_path = f.name

    script_path = Path(__file__).parent.parent / "scripts" / "summarize_jobs.py"
    cmd = ["python3", str(script_path), input_path, "--max", str(max_jobs)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {result.stderr}")

    return result.stdout


class TestSummarizeJobs:
    """Test suite for summarize_jobs.py."""

    def test_output_format(self) -> None:
        """Output contains title, company, location, salary."""
        jobs = [
            {
                "title": "Marketing Manager",
                "company": "Acme Inc",
                "location": "London",
                "min_amount": 40000,
                "max_amount": 50000,
            }
        ]

        output = run_summarize(jobs)

        assert "Marketing Manager" in output
        assert "Acme Inc" in output
        assert "London" in output

    def test_max_jobs_limit(self) -> None:
        """Output limited to max_jobs."""
        jobs = [{"title": f"Job {i}", "company": f"Co {i}"} for i in range(30)]

        output = run_summarize(jobs, max_jobs=20)
        lines = [l for l in output.strip().split('\n') if l and not l.startswith('#') and not l.startswith('...')]

        assert len(lines) <= 20

    def test_handles_nan_values(self) -> None:
        """NaN salary values handled gracefully."""
        jobs = [
            {
                "title": "Marketing Manager",
                "company": "Acme",
                "min_amount": float('nan'),
                "max_amount": float('nan'),
            }
        ]

        output = run_summarize(jobs)

        assert "Marketing Manager" in output
        assert "nan" not in output.lower()

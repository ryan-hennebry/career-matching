#!/usr/bin/env python3
"""Context-efficient job summaries.

Produces one-line summaries to prevent context burn from reading raw JSON.

Usage:
    python3 summarize_jobs.py jobs.json --max 20
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any


def format_salary(min_amt: float | int | None, max_amt: float | int | None) -> str:
    """Format salary range, handling missing/NaN values."""
    def clean(val: float | int | None) -> int | None:
        if val is None:
            return None
        if isinstance(val, float) and math.isnan(val):
            return None
        return int(val)

    min_clean = clean(min_amt)
    max_clean = clean(max_amt)

    if min_clean is None and max_clean is None:
        return "Not listed"
    elif min_clean is not None and max_clean is not None:
        return f"£{min_clean:,}-{max_clean:,}"
    elif min_clean is not None:
        return f"£{min_clean:,}+"
    else:
        return f"Up to £{max_clean:,}"


def summarize_job(job: dict[str, Any]) -> str:
    """Create one-line summary of a job."""
    title = job.get("title", "Unknown Title")
    company = job.get("company", "Unknown Company")
    location = job.get("location", "Unknown Location")
    salary = format_salary(
        job.get("min_amount") or job.get("salary_min"),
        job.get("max_amount") or job.get("salary_max")
    )
    return f"{title} | {company} | {location} | {salary}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create context-efficient job summaries")
    parser.add_argument("input", help="Input JSON file with jobs array")
    parser.add_argument("--max", type=int, default=20, help="Maximum jobs to show")

    args = parser.parse_args()

    try:
        with open(args.input, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    jobs = data.get("jobs", [])

    if not jobs:
        print("No jobs found.")
        return

    for job in jobs[:args.max]:
        print(summarize_job(job))

    if len(jobs) > args.max:
        print(f"\n... and {len(jobs) - args.max} more jobs")


if __name__ == "__main__":
    main()

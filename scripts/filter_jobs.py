#!/usr/bin/env python3
"""Universal job title filter.

Filters jobs from any source based on title exclusions.
The agent derives exclusion terms from onboarding conversation.

Usage:
    python3 filter_jobs.py input.json --output filtered.json --exclude-titles senior lead
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def load_jobs(input_path: str) -> dict[str, Any]:
    """Load jobs from JSON file."""
    with open(input_path, encoding='utf-8') as f:
        return json.load(f)


def filter_jobs(jobs: list[dict[str, Any]], exclude_titles: list[str]) -> list[dict[str, Any]]:
    """Filter jobs by excluding those with specified title keywords.

    Args:
        jobs: List of job dictionaries with 'title' field
        exclude_titles: Keywords to exclude (case-insensitive, partial match)

    Returns:
        Filtered list of jobs
    """
    if not exclude_titles:
        return jobs

    exclude_lower = [term.lower() for term in exclude_titles]

    return [
        job for job in jobs
        if not any(term in job.get("title", "").lower() for term in exclude_lower)
    ]


def save_jobs(output_path: str, data: dict[str, Any]) -> None:
    """Save jobs to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter jobs by title exclusions")
    parser.add_argument("input", help="Input JSON file with jobs array")
    parser.add_argument("--output", "-o", required=True, help="Output JSON file")
    parser.add_argument("--exclude-titles", nargs="*", default=[], help="Title keywords to exclude")

    args = parser.parse_args()

    try:
        data = load_jobs(args.input)
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    original_count = len(data.get("jobs", []))
    data["jobs"] = filter_jobs(data.get("jobs", []), args.exclude_titles)
    filtered_count = len(data["jobs"])

    save_jobs(args.output, data)
    print(f"Filtered {original_count} → {filtered_count} (excluded {original_count - filtered_count})")


if __name__ == "__main__":
    main()

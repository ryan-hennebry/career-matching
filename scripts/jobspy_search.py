#!/usr/bin/env python3
"""
JobSpy search wrapper for the job search agent.
Usage: python3 jobspy_search.py "software engineer" --location "London" --country UK
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any

try:
    from jobspy import scrape_jobs
except ImportError:
    print("Error: python-jobspy not installed. Run: pip install python-jobspy", file=sys.stderr)
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Search job boards using JobSpy")
    parser.add_argument("query", help="Job search query")
    parser.add_argument("--location", default="", help="Location filter")
    parser.add_argument("--remote", action="store_true", help="Remote jobs only")
    parser.add_argument("--results", type=int, default=25, help="Max results per site")
    parser.add_argument("--output", help="Output JSON file (default: stdout)")
    parser.add_argument("--country", default="UK", help="Country for Indeed (default: UK)")
    return parser.parse_args()


def build_output(
    query: str,
    location: str,
    remote: bool,
    jobs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the output dictionary with metadata."""
    return {
        "query": query,
        "location": location,
        "remote": remote,
        "searched_at": datetime.now().isoformat(),
        "count": len(jobs),
        "jobs": jobs,
    }


def main() -> None:
    """Main entry point."""
    args = parse_args()

    try:
        jobs_df = scrape_jobs(
            site_name=["indeed", "linkedin", "glassdoor"],
            search_term=args.query,
            location=args.location,
            results_wanted=args.results,
            is_remote=args.remote,
            country_indeed=args.country,
        )

        # Convert to list of dicts
        results: list[dict[str, Any]] = jobs_df.to_dict(orient="records") if not jobs_df.empty else []

        # Build output
        output = build_output(
            query=args.query,
            location=args.location,
            remote=args.remote,
            jobs=results,
        )

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output, f, indent=2, default=str)
            msg = f"Wrote {len(results)} jobs to {args.output}"
            print(msg)
        else:
            print(json.dumps(output, indent=2, default=str))

    except Exception as e:
        print(f"Error searching jobs: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Plan: JSA V9 Implementation (All Review Changes)

## Overview

Create V9 test environment with all 6 failure fixes from V8, incorporating both **required** and **recommended** changes from Round 1 review.

## Review Changes Summary

### Required (5)
1. Fix WebSearch → WebFetch in Source Discovery section
2. Update settings.local.json: `python scripts/` → `python3 scripts/`
3. Add type hints to all functions in jobspy_search.py
4. Extract `filter_jobs_by_title()` function for testability
5. Fix empty string edge case in title exclusion parsing

### Recommended (5)
1. Collapse Tasks 1-3 into single setup task (simplification)
2. Reduce context.md to bare skeleton (remove comments)
3. Add schema example to Sources section
4. Reduce to 1-2 commits instead of 6
5. Add source accessibility check to Source Discovery workflow

## Files to Create

| File | Description |
|------|-------------|
| `03_agents/tests/v9/CLAUDE.md` | Agent instructions with fixes (~55 lines) |
| `03_agents/tests/v9/context.md` | Bare skeleton template (~15 lines) |
| `03_agents/tests/v9/scripts/jobspy_search.py` | Refactored with types + flags (~90 lines) |
| `03_agents/tests/v9/.claude/settings.local.json` | Updated permissions |
| `03_agents/tests/v9/output/jobs/.gitkeep` | Empty |
| `03_agents/tests/v9/output/briefs/.gitkeep` | Empty |
| `03_agents/tests/v9/output/digests/.gitkeep` | Empty |

---

## Implementation Steps

### Step 1: Create V9 Directory Structure

**Action:** Create all directories and .gitkeep files

```bash
mkdir -p 03_agents/tests/v9/{scripts,.claude,output/{jobs,briefs,digests}}
touch 03_agents/tests/v9/output/{jobs,briefs,digests}/.gitkeep
```

---

### Step 2: Create CLAUDE.md with All Fixes

**File:** `03_agents/tests/v9/CLAUDE.md`

Key changes from V8:
- Add **Principles** section (4 lines)
- Add **Source Discovery** section with WebFetch (not WebSearch) + accessibility check
- Add **Context Management** section (4 lines)
- Fix Capabilities line: `python3 scripts/jobspy_search.py`
- Add Sources schema example

```markdown
# Job Search Agent

You find relevant opportunities and prepare application briefs so the user focuses on interviews and decisions, not discovery and prep.

## Principles

1. **Verify fit before presenting** - Check seniority/requirements match before showing results
2. **Source breadth and variety** - Use niche boards, newsletters, and aggregators — not just major sites
3. **Conserve context** - Filter server-side, store in files, read summaries first
4. **Recommend, don't list** - Suggest single highest-leverage next action

## On Startup

1. Read context.md for profile and constraints
2. Scan output/jobs/ for current state
3. If no profile → ask for CV, extract skills/experience, confirm constraints
4. Otherwise → show status, suggest next action

## Source Discovery

During onboarding, after learning target industries:
1. Research best job sources for each industry (WebFetch)
2. **Verify each source is accessible** before adding to context.md
3. Include variety: niche job boards, newsletters, aggregators
4. Curate 5-10 high-quality sources per industry
5. Store in context.md ## Sources using format: `- [Name](url) - description`

## Context Management

1. Store raw search results in output/jobs/*.json, not in context
2. Read one-line summaries (title/company/location) first
3. Only fetch full descriptions for confirmed-interest jobs
4. Use Task tool for brief generation if context is tight

## Capabilities

- Job search: `python3 scripts/jobspy_search.py` for major boards, WebFetch for specialty sources (per context.md)
- Web research: WebFetch for company context, hiring manager lookup
- File operations: JSON to output/jobs/, Markdown to output/briefs/ and output/digests/

## Outputs

- Jobs: `output/jobs/{company}-{title-slug}.json`
- Briefs: `output/briefs/{company}-{title-slug}-brief.md`
- Digests: `output/digests/{date}.md`

## Job Schema

Minimum fields: id, title, company, url, location, remote, salary_min, salary_max, discovered_at, source, status (new|reviewed|passed|applied), pass_reason (if passed)

Deduplicate by: company + title + location

## Briefs

Include: role summary with match rationale, company context, CV tailoring points, cover letter points, outreach draft (if HM found), application checklist. User writes final copy.

## Dream Companies

Jobs at dream companies (listed in context.md) always surface regardless of other factors.

## Scheduled Runs

When invoked headless:
1. Search sources (continue on errors, note failures in digest)
2. Filter by constraints
3. Generate briefs for up to 10 best matches
4. Write digest
5. Exit
```

---

### Step 3: Create Bare Skeleton context.md

**File:** `03_agents/tests/v9/context.md`

Simplified per review (no comment instructions, just headers):

```markdown
# Job Search Agent - Context

## Profile

## Skills

## Experience

## Target

## Constraints

## Industries

## Sources

## Dream Companies

## Delivery
```

---

### Step 4: Create Refactored jobspy_search.py

**File:** `03_agents/tests/v9/scripts/jobspy_search.py`

Changes:
- Add type hints to all functions
- Extract `parse_args()` function
- Extract `filter_jobs_by_title()` function
- Extract `build_output()` function
- Add `--exclude-titles` and `--country` flags
- Fix empty string edge case with `if x.strip()` filter
- Log filtered count in output

```python
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
    parser.add_argument("--exclude-titles", help="Comma-separated title keywords to exclude")
    parser.add_argument("--country", default="UK", help="Country for Indeed (default: UK)")
    return parser.parse_args()


def filter_jobs_by_title(jobs: list[dict[str, Any]], exclude_titles: str) -> tuple[list[dict[str, Any]], int]:
    """
    Filter jobs by excluding titles containing specified keywords.
    Returns (filtered_jobs, excluded_count).
    """
    # Parse exclusions, filtering out empty strings
    exclusions = [x.strip().lower() for x in exclude_titles.split(",") if x.strip()]

    if not exclusions:
        return jobs, 0

    filtered = []
    excluded_count = 0

    for job in jobs:
        title = job.get("title", "").lower()
        if any(ex in title for ex in exclusions):
            excluded_count += 1
        else:
            filtered.append(job)

    return filtered, excluded_count


def build_output(
    query: str,
    location: str,
    remote: bool,
    jobs: list[dict[str, Any]],
    excluded_count: int = 0,
) -> dict[str, Any]:
    """Build the output dictionary with metadata."""
    output: dict[str, Any] = {
        "query": query,
        "location": location,
        "remote": remote,
        "searched_at": datetime.now().isoformat(),
        "count": len(jobs),
        "jobs": jobs,
    }

    if excluded_count > 0:
        output["excluded_by_title"] = excluded_count

    return output


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

        # Apply title exclusion filter
        excluded_count = 0
        if args.exclude_titles:
            results, excluded_count = filter_jobs_by_title(results, args.exclude_titles)

        # Build output
        output = build_output(
            query=args.query,
            location=args.location,
            remote=args.remote,
            jobs=results,
            excluded_count=excluded_count,
        )

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output, f, indent=2, default=str)
            msg = f"Wrote {len(results)} jobs to {args.output}"
            if excluded_count:
                msg += f" (excluded {excluded_count} by title)"
            print(msg)
        else:
            print(json.dumps(output, indent=2, default=str))

    except Exception as e:
        print(f"Error searching jobs: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

### Step 5: Create Updated settings.local.json

**File:** `03_agents/tests/v9/.claude/settings.local.json`

Change: `python scripts/` → `python3 scripts/`

```json
{
  "permissions": {
    "allow": [
      "Bash(pandoc:*)",
      "Bash(python3 scripts/jobspy_search.py:*)",
      "Bash(python3:*)",
      "WebFetch(domain:cryptocurrencyjobs.co)",
      "WebFetch(domain:web3.career)",
      "WebFetch(domain:earlyandexec.substack.com)",
      "WebFetch(domain:www.workatastartup.com)",
      "WebFetch(domain:boards.greenhouse.io)",
      "WebFetch(domain:jobs.ashbyhq.com)",
      "WebFetch(domain:www.ycombinator.com)",
      "WebFetch(domain:www.joinef.com)",
      "WebFetch(domain:workinstartups.com)",
      "WebFetch(domain:careers.joinef.com)",
      "WebFetch(domain:wellfound.com)",
      "WebFetch(domain:remotecryptowork.com)",
      "WebFetch(domain:cryptojobslist.com)",
      "WebFetch(domain:startup.jobs)",
      "WebFetch(domain:www.glassdoor.com)"
    ]
  }
}
```

---

## Verification

After creating all files:

1. **Check file count:**
   ```bash
   find 03_agents/tests/v9 -type f | wc -l
   # Expected: 7
   ```

2. **Verify Python syntax:**
   ```bash
   python3 -m py_compile 03_agents/tests/v9/scripts/jobspy_search.py
   ```

3. **Verify JSON syntax:**
   ```bash
   python3 -c "import json; json.load(open('03_agents/tests/v9/.claude/settings.local.json'))"
   ```

4. **Check CLAUDE.md line count:**
   ```bash
   wc -l 03_agents/tests/v9/CLAUDE.md
   # Target: ~55 lines
   ```

5. **Verify type hints present:**
   ```bash
   grep -c "def.*->.*:" 03_agents/tests/v9/scripts/jobspy_search.py
   # Expected: 4 (parse_args, filter_jobs_by_title, build_output, main)
   ```

---

## Commit Strategy

Per review recommendation: **2 commits** instead of 6

1. **Commit 1:** Create V9 structure and files
   ```
   feat(career-matching): add V9 test environment with failure fixes
   ```

2. **Commit 2:** Update docs/plans/README.md with V9 entry
   ```
   docs(career-matching): add V9 to active workflows
   ```

---

## Success Criteria

- [ ] All 7 files created
- [ ] CLAUDE.md has Principles, Source Discovery (with WebFetch), Context Management sections
- [ ] Source Discovery includes accessibility check step
- [ ] Sources section has schema example format
- [ ] context.md is bare skeleton (~15 lines, no comments)
- [ ] jobspy_search.py has type hints on all 4 functions
- [ ] Empty string edge case fixed in filter
- [ ] settings.local.json uses `python3 scripts/`
- [ ] Python and JSON syntax valid

# Job Search Agent V10 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 7 failure modes from V9 by adding universal filtering, context-efficient summaries, and dynamic constraint derivation.

**Architecture:** Copy V9 to V10, add two new scripts (filter_jobs.py, summarize_jobs.py), update CLAUDE.md with new sections, replace context.md with blank template.

**Tech Stack:** Python 3, pytest, JSON, Markdown

---

## Pre-Implementation Security Actions (MANUAL)

Before starting implementation, complete these manual actions:

1. **Rotate Resend API key** — The key `re_R3WmeoGJ_...` is in git history. Go to Resend dashboard → regenerate key → revoke old key.

2. **Verify root .gitignore updated** — Confirm these patterns are in root `.gitignore`:
   ```
   **/.claude/settings.local.json
   **/.env
   ```

---

## Files Overview

| Action | Path |
|--------|------|
| Copy | `03_agents/tests/v9/` → `03_agents/tests/v10/` |
| Replace | `03_agents/tests/v10/context.md` (blank template) |
| Modify | `03_agents/tests/v10/CLAUDE.md` (add sections) |
| Modify | `03_agents/tests/v10/.claude/settings.local.json` (remove hardcoded key) |
| Create | `03_agents/tests/v10/scripts/filter_jobs.py` |
| Create | `03_agents/tests/v10/scripts/summarize_jobs.py` |
| Create | `03_agents/tests/v10/tests/test_filter_jobs.py` |
| Create | `03_agents/tests/v10/tests/test_summarize_jobs.py` |

---

## Task 1: Environment Setup

Copy V9 to V10, replace context.md, fix settings.local.json, create .env pattern.

### Step 1.1: Copy V9 to V10

```bash
cp -r 03_agents/tests/v9 03_agents/tests/v10
mkdir -p 03_agents/tests/v10/tests
touch 03_agents/tests/v10/tests/__init__.py
```

### Step 1.2: Replace context.md with blank template

**File:** `03_agents/tests/v10/context.md`

```markdown
# Job Search Agent - Context

## Profile

## Skills

## Experience

## Target

## Constraints

## Industries

## Sources

## Scoring Rubric

## Dream Companies

## Delivery
```

### Step 1.3: Fix settings.local.json

**File:** `03_agents/tests/v10/.claude/settings.local.json`

Remove the hardcoded API key. Change permissions to:

```json
{
  "permissions": {
    "allow": [
      "Bash(source .env && python3 scripts/send_email.py *)",
      "Bash(python3 scripts/filter_jobs.py *)",
      "Bash(python3 scripts/summarize_jobs.py *)",
      "Bash(python3 scripts/jobspy_search.py *)",
      "Bash(pytest tests/ *)"
    ]
  }
}
```

### Step 1.4: Create .env.example and .gitignore

**File:** `03_agents/tests/v10/.env.example`

```
RESEND_API_KEY=your_api_key_here
```

**File:** `03_agents/tests/v10/.gitignore`

```
.env
output/jobs/*.json
```

### Step 1.5: Commit

```bash
git add 03_agents/tests/v10
git commit -m "chore(career-matching): copy V9 to V10 with security fixes and blank context"
```

---

## Task 2: filter_jobs.py (TDD)

### Step 2.1: Write 3 core tests

**File:** `03_agents/tests/v10/tests/test_filter_jobs.py`

```python
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
```

### Step 2.2: Run tests (expect FAIL)

```bash
cd 03_agents/tests/v10 && pytest tests/test_filter_jobs.py -v
```

### Step 2.3: Implement filter_jobs.py

**File:** `03_agents/tests/v10/scripts/filter_jobs.py`

```python
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
```

### Step 2.4: Run tests (expect PASS)

```bash
cd 03_agents/tests/v10 && pytest tests/test_filter_jobs.py -v
```

### Step 2.5: Commit

```bash
git add 03_agents/tests/v10/scripts/filter_jobs.py 03_agents/tests/v10/tests/test_filter_jobs.py
git commit -m "feat(career-matching): add filter_jobs.py with TDD tests"
```

---

## Task 3: summarize_jobs.py (TDD)

### Step 3.1: Write 3 core tests

**File:** `03_agents/tests/v10/tests/test_summarize_jobs.py`

```python
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
```

### Step 3.2: Run tests (expect FAIL)

```bash
cd 03_agents/tests/v10 && pytest tests/test_summarize_jobs.py -v
```

### Step 3.3: Implement summarize_jobs.py

**File:** `03_agents/tests/v10/scripts/summarize_jobs.py`

```python
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
```

### Step 3.4: Run tests (expect PASS)

```bash
cd 03_agents/tests/v10 && pytest tests/test_summarize_jobs.py -v
```

### Step 3.5: Commit

```bash
git add 03_agents/tests/v10/scripts/summarize_jobs.py 03_agents/tests/v10/tests/test_summarize_jobs.py
git commit -m "feat(career-matching): add summarize_jobs.py with TDD tests"
```

---

## Task 4: CLAUDE.md Updates

Add all new sections in a single edit.

### Step 4.1: Add Constraint Derivation section

Insert after "On Startup" section:

```markdown
## Constraint Derivation

During onboarding, derive all constraints from user conversation:

1. **Title exclusions** — Based on seniority preference, determine exclusion keywords. Example: "junior/mid level" → exclude: senior, lead, head, director, vp, principal, chief, staff, manager

2. **Scoring weights** — Default: 5 criteria at 20% each (salary, location, company, role fit, growth). Adjust based on what user emphasizes in conversation.

3. **Store immediately** — Write all derived constraints to context.md right after derivation.

4. **Validate with user** — Before first search, confirm: "Here's what I understood: [constraints]. Does this look right?"
```

### Step 4.2: Update Context Management section

Add this line:

```markdown
- Never read raw JSON files into context — use `python3 scripts/summarize_jobs.py <file>` instead
```

### Step 4.3: Update Source Discovery section

Change step 2 to:

```markdown
2. **Verify source fit** — Check that source content matches user constraints (e.g., if user wants junior roles, verify source doesn't focus on executive positions)
```

### Step 4.4: Update Scheduled Runs section

Add step 6:

```markdown
6. **Verify sync** — Confirm digest top-5 job titles match the 5 brief filenames before sending
```

### Step 4.5: Add Security section at end

```markdown
## Security

- API keys must be stored in `.env` file, never inline in commands
- Run email script with: `source .env && python3 scripts/send_email.py`
- Never commit `.env` files (already in .gitignore)
- Reference: `cp .env.example .env` then edit
```

### Step 4.6: Commit

```bash
git add 03_agents/tests/v10/CLAUDE.md
git commit -m "docs(career-matching): add V10 sections - constraint derivation, security, sync verification"
```

---

## Task 5: Verification

### Step 5.1: Run all tests

```bash
cd 03_agents/tests/v10 && pytest tests/ -v
```

Expected: All 6 tests PASS (3 filter + 3 summarize)

### Step 5.2: Verify file structure

```bash
tree 03_agents/tests/v10/
```

Expected:
```
03_agents/tests/v10/
├── CLAUDE.md
├── context.md
├── .claude/settings.local.json
├── .env.example
├── .gitignore
├── scripts/
│   ├── jobspy_search.py
│   ├── send_email.py
│   ├── filter_jobs.py
│   └── summarize_jobs.py
├── tests/
│   ├── __init__.py
│   ├── test_filter_jobs.py
│   └── test_summarize_jobs.py
└── output/
```

### Step 5.3: Final commit (if needed)

```bash
git status
# If clean: done
# If changes: git add -A && git commit -m "chore(career-matching): V10 implementation complete"
```

---

## Post-Implementation Security Items (Separate PR)

These require follow-up work in a separate PR:

1. **Add path validation to send_email.py** — Restrict --file parameter to project directory only
2. **Add recipient validation to send_email.py** — Validate email addresses against allowlist
3. **Remove overly permissive `python3:*` permission** — Ensure settings.local.json only allows specific scripts

---

## Summary

| Phase | Tasks | Tests | Commits |
|-------|-------|-------|---------|
| 1. Environment | 1 | 0 | 1 |
| 2. filter_jobs.py | 1 | 3 | 1 |
| 3. summarize_jobs.py | 1 | 3 | 1 |
| 4. CLAUDE.md | 1 | 0 | 1 |
| 5. Verification | 1 | 0 | 0-1 |
| **Total** | **5** | **6** | **4-5** |

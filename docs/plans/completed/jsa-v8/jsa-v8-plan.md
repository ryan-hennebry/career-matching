# Job Search Agent V8 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Simplify the job search agent from 247 lines to ~35 lines by deleting defensive guardrails and trusting the agent's judgment, while preserving essential context for agent operation.

**Review Status:** V8 Review 7 approved. Added send_digest.py to deletions (digest format mismatch).

**Architecture:** Delete scoring rubrics, learning systems, and complex templates. Keep only hard constraints (salary, location, industries) in context.md. Reduce output directories from 7 to 3. Delete the references/ folder entirely.

**Tech Stack:** Markdown files only (CLAUDE.md, context.md)

---

## Overview

V7 review feedback: "moved complexity rather than removing it." This plan executes a radical simplification:

| Current | Target |
|---------|--------|
| CLAUDE.md: 247 lines | ~43 lines |
| context.md: 163 lines | ~24 lines (profile + constraints + email) |
| output/: 7 directories | 3 directories |
| references/: 3 files | Deleted |
| run.sh: 82 lines | Deleted |
| status.sh: 81 lines | Deleted |
| scripts/: 2 email scripts | 1 script (jobspy_search.py only) |

## Files to Modify

- `03_agents/career-matching/scripts/jobspy_search.py` - Create (new file)
- `03_agents/career-matching/CLAUDE.md` - Replace with ~43-line version
- `03_agents/career-matching/context.md` - Replace with minimal profile structure
- Delete: `03_agents/career-matching/references/` (entire directory)
- Delete: `03_agents/career-matching/output/applications/`
- Delete: `03_agents/career-matching/output/cv_variants/`
- Delete: `03_agents/career-matching/output/reports/`
- Delete: `03_agents/career-matching/output/archive/`
- Delete: `03_agents/career-matching/run.sh`
- Delete: `03_agents/career-matching/status.sh`
- Delete: `03_agents/career-matching/scripts/send_alert.py`
- Delete: `03_agents/career-matching/scripts/send_digest.py`

---

## Implementation Steps

### Task 0: Create JobSpy search script

**Files:**
- Create: `03_agents/career-matching/scripts/jobspy_search.py`

**Rationale:** CLAUDE.md references `scripts/jobspy_search.py` but it doesn't exist. This wrapper makes JobSpy invocable via Bash.

**Step 1: Create jobspy_search.py**

```python
#!/usr/bin/env python3
"""
JobSpy search wrapper for the job search agent.
Usage: python jobspy_search.py "software engineer" --location "San Francisco" --remote
"""

import argparse
import json
import sys
from datetime import datetime

try:
    from jobspy import scrape_jobs
except ImportError:
    print("Error: python-jobspy not installed. Run: pip install python-jobspy", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Search job boards using JobSpy")
    parser.add_argument("query", help="Job search query")
    parser.add_argument("--location", default="", help="Location filter")
    parser.add_argument("--remote", action="store_true", help="Remote jobs only")
    parser.add_argument("--results", type=int, default=25, help="Max results per site")
    parser.add_argument("--output", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    try:
        jobs = scrape_jobs(
            site_name=["indeed", "linkedin", "glassdoor"],
            search_term=args.query,
            location=args.location,
            results_wanted=args.results,
            is_remote=args.remote,
            country_indeed="USA",
        )

        # Convert to list of dicts
        results = jobs.to_dict(orient="records") if not jobs.empty else []

        # Add metadata
        output = {
            "query": args.query,
            "location": args.location,
            "remote": args.remote,
            "searched_at": datetime.now().isoformat(),
            "count": len(results),
            "jobs": results,
        }

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output, f, indent=2, default=str)
            print(f"Wrote {len(results)} jobs to {args.output}")
        else:
            print(json.dumps(output, indent=2, default=str))

    except Exception as e:
        print(f"Error searching jobs: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: Make executable**

```bash
chmod +x 03_agents/career-matching/scripts/jobspy_search.py
```

**Verify:**
```bash
python 03_agents/career-matching/scripts/jobspy_search.py --help
# Expected: Usage information
```

**Step 3: Commit**

```bash
git add 03_agents/career-matching/scripts/jobspy_search.py
git commit -m "feat(career-matching): add JobSpy search wrapper script

Creates scripts/jobspy_search.py as a thin wrapper around python-jobspy
library. Accepts query, location, and remote flags. Outputs JSON to
stdout or file. Required by CLAUDE.md Capabilities section."
```

---

### Task 1: Replace CLAUDE.md with simplified version

**Files:**
- Modify: `03_agents/career-matching/CLAUDE.md`

**Step 1: Replace CLAUDE.md entirely**

```markdown
# Job Search Agent

You find relevant opportunities and prepare application briefs so the user focuses on interviews and decisions, not discovery and prep.

## On Startup

1. Read context.md for profile and constraints
2. Scan output/jobs/ for current state
3. If no profile → ask for CV, extract skills/experience, confirm constraints
4. Otherwise → show status, suggest next action

## Capabilities

- Job search: `scripts/jobspy_search.py` for major boards (invoke via Bash), WebFetch for company career pages
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

**Verify:**
```bash
wc -l 03_agents/career-matching/CLAUDE.md
# Expected: ~43 lines (under 50)
```

**Step 2: Commit**

```bash
git add 03_agents/career-matching/CLAUDE.md
git commit -m "refactor(career-matching): simplify CLAUDE.md to ~43 lines

Remove scoring rubrics, source tiers, decision boundaries, templates,
learning system, employed mode, LinkedIn audit, interview briefs.
Add: capabilities, job schema, dedup rule, headless criteria, dream companies.
Trust agent judgment while preserving essential operational context."
```

---

### Task 2: Replace context.md with minimal structure

**Files:**
- Modify: `03_agents/career-matching/context.md`

**Step 1: Replace context.md entirely**

```markdown
# Job Search Agent - Context

## Profile
name:
email:
linkedin_url:

## Skills
# populated from CV during onboarding

## Experience
# populated from CV during onboarding

## Target
roles:

## Constraints
salary_minimum:
remote_preference:
industries:

## Dream Companies

## Delivery
email:
```

**Verify:**
```bash
wc -l 03_agents/career-matching/context.md
# Expected: ~24 lines
```

**Step 2: Commit**

```bash
git add 03_agents/career-matching/context.md
git commit -m "refactor(career-matching): simplify context.md to profile + constraints + email

Remove: Learnings section, Source Effectiveness, Interview Outcomes,
Preference Evolution, Pending Suggestions, Auto-Adjustments, Skill Mappings,
Session History, Last Run, Preferences (stretch_tolerance, research_depth).
Keep: Delivery email field for script compatibility."
```

---

### Task 3: Delete references/ directory

**Files:**
- Delete: `03_agents/career-matching/references/algorithms.md`
- Delete: `03_agents/career-matching/references/sources.md`
- Delete: `03_agents/career-matching/references/templates.md`
- Delete: `03_agents/career-matching/references/` (directory)

**Step 1: Remove references directory**

```bash
rm -rf 03_agents/career-matching/references/
```

**Verify:**
```bash
ls 03_agents/career-matching/references/ 2>&1
# Expected: "No such file or directory"
```

**Step 2: Commit**

```bash
git add -A 03_agents/career-matching/references/
git commit -m "refactor(career-matching): delete references/ directory

Remove algorithms.md, sources.md, templates.md. Agent uses judgment
instead of explicit scoring rules and template structures."
```

---

### Task 4: Delete unused output directories

**Files:**
- Delete: `03_agents/career-matching/output/applications/`
- Delete: `03_agents/career-matching/output/cv_variants/`
- Delete: `03_agents/career-matching/output/reports/`
- Delete: `03_agents/career-matching/output/archive/`

**Step 1: Remove unused directories**

```bash
rm -rf 03_agents/career-matching/output/applications/
rm -rf 03_agents/career-matching/output/cv_variants/
rm -rf 03_agents/career-matching/output/reports/
rm -rf 03_agents/career-matching/output/archive/
```

**Verify:**
```bash
ls 03_agents/career-matching/output/
# Expected: jobs/ briefs/ digests/ (3 directories only)
```

**Step 2: Commit**

```bash
git add -A 03_agents/career-matching/output/
git commit -m "refactor(career-matching): reduce output directories to 3

Keep: jobs/, briefs/, digests/
Delete: applications/, cv_variants/, reports/, archive/"
```

---

### Task 5: Delete orchestration scripts and email scripts

**Files:**
- Delete: `03_agents/career-matching/run.sh`
- Delete: `03_agents/career-matching/status.sh`
- Delete: `03_agents/career-matching/scripts/send_alert.py`
- Delete: `03_agents/career-matching/scripts/send_digest.py`

**Rationale:**
- Shell scripts encode prescriptive behavior (8-step instructions, employed mode, 90%+ thresholds) that conflicts with agent-judgment philosophy.
- `send_alert.py` depends on `match_score` and scoring fields that no longer exist after removing the scoring rubrics.
- `send_digest.py` expects PDF files at `{date}-digest.pdf` but V8 uses Markdown digests. Also has hardcoded placeholder stats and references deleted directories (`output/applications/`).
- Agent can send emails directly via Resend API if needed.

**Step 1: Delete scripts**

```bash
rm 03_agents/career-matching/run.sh
rm 03_agents/career-matching/status.sh
rm 03_agents/career-matching/scripts/send_alert.py
rm 03_agents/career-matching/scripts/send_digest.py
```

**Verify:**
```bash
ls 03_agents/career-matching/*.sh 2>&1
# Expected: "No such file or directory"

ls 03_agents/career-matching/scripts/
# Expected: jobspy_search.py only
```

**Step 2: Commit**

```bash
git add -A 03_agents/career-matching/
git commit -m "refactor(career-matching): delete run.sh, status.sh, and email scripts

Shell scripts encoded prescriptive behavior (8-step instructions, employed mode,
90%+ thresholds) that conflicted with agent-judgment philosophy.

send_alert.py depended on match_score field which no longer exists.
send_digest.py expected PDF files but V8 uses Markdown, and had hardcoded
placeholder stats referencing deleted directories.

Agent can send emails directly via Resend API when configured.
Scheduled runs now use: claude -p 'Run your scheduled job search.'"
```

**Note on scheduled runs:**
```bash
# In crontab (if needed)
claude --dangerously-skip-permissions -p "Run your scheduled job search."
```

---

### Task 6: Verify final state

**Step 1: Verify CLAUDE.md line count**

```bash
wc -l 03_agents/career-matching/CLAUDE.md
# Expected: under 50 lines (~43)
```

**Step 2: Verify context.md line count**

```bash
wc -l 03_agents/career-matching/context.md
# Expected: under 30 lines (~24)
```

**Step 3: Verify output directories**

```bash
ls 03_agents/career-matching/output/
# Expected: jobs/ briefs/ digests/ (exactly 3)
```

**Step 4: Verify references deleted**

```bash
ls 03_agents/career-matching/references/ 2>&1 | grep -c "No such file"
# Expected: 1
```

**Step 5: Verify overall structure**

```bash
ls -la 03_agents/career-matching/
# Expected: CLAUDE.md, context.md, output/, scripts/
# NOT expected: references/, run.sh, status.sh
```

---

## Success Criteria

From the design document + review feedback:

1. ✅ CLAUDE.md is under 50 lines (~43 target)
2. ✅ context.md contains profile, constraints, and email (~24 lines)
3. ✅ Three output directories only (jobs/, briefs/, digests/)
4. ✅ No references/ folder
5. ✅ No orchestration scripts (run.sh, status.sh deleted)
5a. ✅ All email scripts deleted (send_alert.py, send_digest.py) - both had incompatibilities
6. ✅ Agent can still discover jobs, create briefs, generate digests (functionality preserved through judgment)
7. ✅ Agent knows available capabilities (JobSpy, WebFetch, file ops)
8. ✅ Job JSON schema is defined with deduplication rule
9. ✅ Headless mode has explicit exit criteria (10 briefs, error handling)
10. ✅ Pass tracking via job JSON (pass_reason field)
11. ✅ scripts/ contains only jobspy_search.py

---

## Verification

After implementation, test the agent manually:

1. Open a new session in `03_agents/career-matching/`
2. The agent should read context.md and show status
3. Verify it can suggest job discovery without referencing deleted files
4. Verify briefs can be created without template references

---

## Handoff

Plan updated with Review 7 feedback:
- Added Task 0: Create `scripts/jobspy_search.py` (was missing)
- Task 5: Deletes both email scripts (`send_alert.py` and `send_digest.py`)
  - send_alert.py depended on removed scoring fields
  - send_digest.py expected PDF format but V8 uses Markdown, and had hardcoded placeholder stats
- Kept 43-line CLAUDE.md (ship, learn, simplify in V9 if needed)
- scripts/ will contain only jobspy_search.py after implementation

Ready for `/build` to implement.

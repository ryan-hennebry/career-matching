# Session Analysis: Job Search Agent V9

## Summary

**Session Duration:** ~15 minutes active work
**Context Usage:** Exceeded 40% (user flagged at mid-session)
**Wins:** 6 | **Failures:** 7 | **Edge Cases:** 2

V9 successfully completed the core workflow (onboarding → search → digest → briefs → email) but exposed several new failure modes around scoring consistency, seniority filtering, and digest/brief synchronization.

---

## What Went Well

### 1. Clean Onboarding Flow
Agent asked one question at a time after user feedback (line 79-114), resulting in complete profile population.

### 2. Source Discovery Worked
Agent researched and curated 14 sources across 3 industries + 6 newsletters after user prompted for newsletter sources (lines 460-546).

### 3. Multi-Source Search Executed
JobSpy (175 jobs) + Web3.Career + CryptocurrencyJobs + AIJobs + Early & Exec all searched successfully.

### 4. Title Exclusion Filtering Applied
`--exclude-titles "senior,head,director,vp,principal,lead"` filtered 50 senior roles at script level (lines 356-380).

### 5. Brief Quality High
5 briefs generated with complete structure: role summary, match rationale, CV tailoring points, cover letter points, application checklist.

### 6. Email Delivery Implemented
Resend integration created and working — digest sent successfully (line 1018-1019).

---

## What Failed

### Failure 1: "Lead" Title Not Excluded
- **What happened:** "Growth & Community Lead @ Neya" ranked #1 despite "lead" being in the exclude list (lines 699-700, user flagged at 801-802)
- **Root cause:** Title exclusion only applied at JobSpy level, not to jobs from WebFetch sources (Early & Exec)
- **Principle violated:** "Verify fit before presenting" — seniority check was incomplete
- **Fix type:** Implementation

### Failure 2: Scoring System Not Persisted
- **What happened:** User asked "how can we know that if I run the agent again in the future it would give me the same rankings?" (line 803)
- **Root cause:** Scoring rubric exists only in agent reasoning, not stored in context.md
- **Principle violated:** Agent-native architecture — agent actions should be reproducible
- **Fix type:** Architectural

### Failure 3: Digest and Briefs Out of Sync
- **What happened:** Digest sent with Neya #1, but briefs excluded Neya (lines 1031-1035)
- **Root cause:** Agent created briefs from corrected list but forgot to update digest file before sending
- **Principle violated:** Single source of truth — digest and briefs generated from different data states
- **Fix type:** Implementation

### Failure 4: Context Burn from Raw JSON Reads
- **What happened:** Context exceeded 40% (user flagged at line 549)
- **Root cause:** Agent read full JobSpy JSON files (~60 jobs × 500-1000 words each) into context
- **Principle violated:** "Conserve context" — violated despite explicit instruction in CLAUDE.md
- **Fix type:** Implementation

### Failure 5: WebFetch Sources Not Filtered
- **What happened:** Jobs from Early & Exec newsletter weren't passed through seniority filter
- **Root cause:** No post-processing filter for WebFetch results — only JobSpy has `--exclude-titles`
- **Principle violated:** Consistent filtering across all sources
- **Fix type:** Implementation

### Failure 6: Newsletter Source Added Without Validation
- **What happened:** Agent added "Early & Exec" as a source, but it's exec-focused (lines 611-612)
- **Root cause:** Agent didn't verify newsletter content matches user's seniority constraints before adding
- **Principle violated:** "Verify each source is accessible" (in CLAUDE.md) — but no instruction to verify content relevance
- **Fix type:** Architectural

### Failure 7: API Key Exposed in Transcript
- **What happened:** Resend API key visible in session output (line 989)
- **Root cause:** User provided key directly, agent used it inline
- **Principle violated:** Security — keys should be stored in .env, not context
- **Fix type:** Implementation

---

## Edge Cases Discovered

### Edge Case 1: Newsletters Have Dual Content
Early & Exec publishes both "Early" (junior/mid) and "Exec" (senior) editions. Agent initially added the newsletter without understanding this distinction.

**Handling:** Agent should check newsletter structure during source discovery and note which editions are relevant.

### Edge Case 2: Dynamic Sites Can't Be Scraped
Remote3 uses JavaScript loading — WebFetch returned no useful data (line 631).

**Handling:** Already noted in CLAUDE.md ("Not searchable via WebFetch") but should be flagged during source discovery, not after failed attempt.

---

## Specific Fixes

### CLAUDE.md Changes

```diff
## Constraints
+ - Exclude titles containing: senior, head, director, vp, principal, lead, chief, staff

## Scoring Rubric
+
+ | Criteria | Weight | Benchmark |
+ |----------|--------|-----------|
+ | Industry (AI/Crypto/Startup) | 25 | Must match 1+ |
+ | Role type match | 25 | Community, Marketing, FA, Growth |
+ | Seniority fit | 20 | Junior/Mid only |
+ | Location fit | 15 | London, Cambridge, Remote UK |
+ | Salary fit | 15 | £35K+ minimum |
+
+ Bonus: +5 for first-hire/early-stage, +5 for events focus
+ Store rubric in context.md during onboarding. Apply consistently to all sources.

## Source Discovery
  During onboarding, after learning target industries:
  1. Research best job sources for each industry (WebFetch)
- 2. **Verify each source is accessible** before adding to context.md
+ 2. **Verify each source is accessible AND content matches constraints** (seniority, industries)
  3. Include variety: niche job boards, newsletters, aggregators
+ 4. For newsletters: note which editions are relevant (e.g., "Early & Exec - Early roles only")
- 4. Curate 5-10 high-quality sources per industry
+ 5. Curate 5-10 high-quality sources per industry
- 5. Store in context.md ## Sources using format: `- [Name](url) - description`
+ 6. Store in context.md ## Sources using format: `- [Name](url) - description`

## Context Management
+ 0. **Never read raw JSON files into context** — use scripts/summarize_jobs.py for summaries
  1. Store raw search results in output/jobs/*.json, not in context
  2. Read one-line summaries (title/company/location) first
  3. Only fetch full descriptions for confirmed-interest jobs
  4. Use Task tool for brief generation if context is tight

## Digest Workflow
+
+ Single-pass generation to prevent sync issues:
+ 1. Collect all jobs from all sources into single list
+ 2. Apply seniority filter to ALL jobs (not just JobSpy)
+ 3. Score and rank using persisted rubric
+ 4. Generate digest from ranked list
+ 5. Generate briefs for top N from same list
+ 6. Send digest
+ Never maintain digest and briefs separately — they must use the same filtered/ranked data.
```

### New Script: scripts/filter_jobs.py

```python
#!/usr/bin/env python3
"""
Filter jobs from any source by title keywords.
Usage: python3 filter_jobs.py input.json --exclude-titles "senior,lead,head"
"""
import argparse
import json
import sys

def filter_by_title(jobs: list[dict], exclude: list[str]) -> tuple[list[dict], int]:
    filtered = []
    excluded = 0
    for job in jobs:
        title = job.get("title", "").lower()
        if any(ex in title for ex in exclude):
            excluded += 1
        else:
            filtered.append(job)
    return filtered, excluded

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("--exclude-titles", required=True, help="Comma-separated exclusions")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    exclude = [x.strip().lower() for x in args.exclude_titles.split(",") if x.strip()]

    with open(args.input) as f:
        data = json.load(f)

    jobs = data.get("jobs", data) if isinstance(data, dict) else data
    filtered, excluded = filter_by_title(jobs, exclude)

    print(f"Filtered: kept {len(filtered)}, excluded {excluded}", file=sys.stderr)

    output = json.dumps(filtered, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)

if __name__ == "__main__":
    main()
```

### New Script: scripts/summarize_jobs.py

```python
#!/usr/bin/env python3
"""
Output one-line summaries from job JSON files.
Usage: python3 summarize_jobs.py output/jobs/*.json
"""
import json
import sys

def summarize(job: dict) -> str:
    title = job.get("title", "Unknown")[:40]
    company = job.get("company", "Unknown")[:25]
    location = job.get("location", "")[:20]
    salary = job.get("salary_min", "")
    return f"{title} | {company} | {location} | {salary}"

def main():
    for path in sys.argv[1:]:
        try:
            with open(path) as f:
                data = json.load(f)
            jobs = data.get("jobs", []) if isinstance(data, dict) else data
            print(f"\n=== {path} ({len(jobs)} jobs) ===")
            for job in jobs[:20]:  # Limit to prevent context burn
                print(summarize(job))
        except Exception as e:
            print(f"Error reading {path}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
```

### context.md Template Addition

```diff
## Constraints

- Location: Remote (UK), Cambridge, London
- Work type: Remote, Hybrid, On-site
- Salary: £35,000+ minimum
- Seniority: Junior/Mid-level (no senior roles)
+ - Exclude titles: senior, head, director, vp, principal, lead, chief, staff

+ ## Scoring Rubric
+
+ | Criteria | Weight | Benchmark |
+ |----------|--------|-----------|
+ | Industry match | 25 | AI, Crypto, Tech Startups |
+ | Role type match | 25 | Community, Marketing, FA, Growth |
+ | Seniority fit | 20 | Junior/Mid only |
+ | Location fit | 15 | London, Cambridge, Remote UK |
+ | Salary fit | 15 | £35K+ minimum |
+
+ Bonus: +5 first-hire/early-stage, +5 events focus
```

---

## Architecture Changes

### 1. Scoring Must Be Deterministic

**Problem:** Scoring exists only in agent reasoning — not reproducible.

**Solution:**
- Add `## Scoring Rubric` section to context.md template
- Agent populates during onboarding based on user profile
- All scoring uses stored rubric, not ad-hoc judgment

### 2. Single Source of Truth for Job List

**Problem:** Digest generated from one list, briefs from another (after manual correction).

**Solution:**
- All filtering happens once, at collection time
- Ranked list written to `output/jobs/ranked-{date}.json`
- Digest and briefs both read from this single file

### 3. Source Validation Must Include Content Check

**Problem:** Agent added exec-focused newsletter for junior/mid user.

**Solution:**
- During source discovery, agent must verify content matches constraints
- For newsletters, identify which editions are relevant
- Note any limitations in context.md Sources section

---

## Recommended Next Step

**Implementation issues dominate.** Run `/plan` to update implementation steps with:

1. Add `scripts/filter_jobs.py` for universal title filtering
2. Add `scripts/summarize_jobs.py` to prevent context burn
3. Add `## Scoring Rubric` template to context.md
4. Add `## Digest Workflow` section to CLAUDE.md
5. Update Source Discovery to include content validation
6. Add excluded titles to context.md Constraints section

V10 should be a **refinement release** focused on:
- Deterministic scoring
- Universal filtering (not just JobSpy)
- Single-pass digest/brief generation
- Context-efficient job summaries

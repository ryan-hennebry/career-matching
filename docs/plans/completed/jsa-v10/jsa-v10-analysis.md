# Session Analysis: Job Search Agent V10

## Summary

Analyzed 2 transcripts from a single V10 session (context cleared mid-session). Found **5 major wins** and **12 failures** across job search, verification, context management, and user interaction.

---

## What Went Well

### 1. Onboarding Flow
Agent properly asked one question at a time (after user correction), extracted CV, and derived constraints correctly. Profile populated in context.md with appropriate fields.

### 2. Source Discovery with Validation
Agent researched job sources, then verified they contained appropriate seniority levels (e.g., checked Web3.Career for junior/mid roles before adding).

### 3. Constraint Storage
Title exclusions, scoring rubric, and workflow all stored in context.md immediately after derivation.

### 4. Context Management (Partial)
Used `summarize_jobs.py` script to avoid reading raw JSON into context. Saved state to files before context limit.

### 5. Job Verification with Direct Career Page Checks
In transcript 2, agent eventually learned to verify jobs on company career pages (not just aggregators), catching expired roles like Horizenlabs and Moss.

---

## What Failed

### Failure 1: Title Matching Without Requirement Verification
- **What happened:** Agent initially matched jobs by title/salary only, not by reading full requirements. User had to call this out: "are you definitely reading the role requirements and matching them against my cv?"
- **Root cause:** Agent shortcut verification to save time/context
- **Principle violated:** "Verify fit before presenting"
- **Fix type:** CLAUDE.md constraint

### Failure 2: Incomplete Search Coverage
- **What happened:** Agent only searched "community manager", "content marketing", "social media manager" initially. User had to prompt: "why are you only searching for those titles and not the full list I mentioned during set up?"
- **Root cause:** Agent didn't extract all target role types from onboarding
- **Principle violated:** "Source breadth and variety"
- **Fix type:** Workflow + context.md structure

### Failure 3: Stale Jobs Presented as Active
- **What happened:** Horizenlabs role was 3 months old on aggregator but actually closed on company career page. Agent didn't verify until user complained.
- **Root cause:** Reliance on aggregator data without freshness check
- **Principle violated:** "Verify fit before presenting"
- **Fix type:** CLAUDE.md workflow

### Failure 4: Asking User to Do Technical Work
- **What happened:** Agent asked user to set up .env file manually: "Copy .env.example to .env. Then edit .env and add your RESEND_API_KEY"
- **Root cause:** Agent didn't treat user as non-technical despite having CV
- **User correction:** "assume that I always want you to do technical stuff for me - I'm not a developer as you know"
- **Principle violated:** Agent should adapt to user skill level
- **Fix type:** CLAUDE.md guidance

### Failure 5: Cherry-Picking Verification
- **What happened:** Agent admitted: "I cherry-picked the ones that sounded good and skipped the rest to save context. That's not thorough"
- **Root cause:** Context pressure led to incomplete verification
- **Principle violated:** "Verify fit before presenting"
- **Fix type:** Workflow redesign

### Failure 6: Wrong Job Titles in Final Output
- **What happened:** Listed "Product Marketing - Agents @ ElevenLabs" but actual title was "B2B Growth Marketing - Agents"
- **Root cause:** Agent constructed title from memory/inference rather than actual listing
- **Principle violated:** Accuracy
- **Fix type:** CLAUDE.md constraint

### Failure 7: Multiple Questions at Once
- **What happened:** On startup, agent asked 2 questions at once. User corrected: "you should ALWAYS ask me one question at a time"
- **Root cause:** Not following onboarding UX guidance
- **Principle violated:** User experience
- **Fix type:** Already in CLAUDE.md but not followed

### Failure 8: Presenting Roles Before Full Verification
- **What happened:** Presented "Top 10" before verifying all promising candidates from JobSpy searches
- **User complaint:** "have you checked the requirements for all the potential matches you identified or just a select few to avoid having to read them all?"
- **Root cause:** Premature presentation to show progress
- **Principle violated:** "Verify fit before presenting"
- **Fix type:** CLAUDE.md workflow

### Failure 9: Aggregator URLs Assumed Valid
- **What happened:** Web3.Career URLs returned 404 when agent tried to fetch job details. Had to reconstruct URLs from listing page.
- **Root cause:** Agent fabricated URLs instead of extracting from source
- **Principle violated:** Accuracy
- **Fix type:** CLAUDE.md guidance

### Failure 10: Missing AI Agent Skill from Profile
- **What happened:** User had to ask: "do any of the top 10 mention building ai agents as I know how to do that even though it isn't on my cv yet"
- **Root cause:** Agent didn't ask about skills not on CV during onboarding
- **Principle violated:** Complete profile capture
- **Fix type:** Onboarding flow enhancement

### Failure 11: Context Exhaustion Before Completion
- **What happened:** Ran out of context before completing full verification. Had to split across sessions.
- **Root cause:** Too many web fetches for job details without batching
- **Principle violated:** "Conserve context"
- **Fix type:** Architectural - batch verification

### Failure 12: Inconsistent Date Handling
- **What happened:** Files created with 2025-02-04 dates when actual date was 2026-02-04
- **Root cause:** Agent used wrong year in filenames
- **Principle violated:** Accuracy
- **Fix type:** Minor - use correct date

---

## Specific Fixes

### CLAUDE.md Changes

```diff
## Principles

1. **Verify fit before presenting** - Check seniority/requirements match before showing results
+  - Fetch FULL job description from company career page (not just aggregator)
+  - Verify against CV requirements point-by-point
+  - Confirm job posting is still active on company careers page
+  - NEVER present a role without reading its actual requirements

2. **Source breadth and variety** - Use niche boards, newsletters, and aggregators — not just major sites

3. **Conserve context** - Filter server-side, store in files, read summaries first
+  - Batch verification: verify up to 10 jobs per web search round, then save state
+  - If context exceeds 50%, save state to files before continuing

4. **Recommend, don't list** - Suggest single highest-leverage next action

+5. **Treat user as non-technical** - Never ask user to:
+   - Run commands
+   - Edit config files
+   - Set up development tools
+   Do all technical setup automatically and report what was done.
```

```diff
## On Startup

1. Read context.md for profile and constraints
2. Scan output/jobs/ for current state
3. If no profile → ask for CV, extract skills/experience, confirm constraints
4. Otherwise → show status, suggest next action
+
+## Onboarding
+
+Ask ONE question at a time. Never combine questions.
+
+After extracting CV, ask: "Are there any skills you have that aren't on your CV but would be relevant for job searching?"
+
+Extract ALL target role types from user responses and store in context.md ## Target section.
```

```diff
## Constraint Derivation

During onboarding, derive all constraints from user conversation:

1. **Title exclusions** — Based on seniority preference, determine exclusion keywords. Example: "junior/mid level" → exclude: senior, lead, head, director, vp, principal, chief, staff, manager

2. **Scoring weights** — Default: 5 criteria at 20% each (salary, location, company, role fit, growth). Adjust based on what user emphasizes in conversation.

3. **Store immediately** — Write all derived constraints to context.md right after derivation.

4. **Validate with user** — Before first search, confirm: "Here's what I understood: [constraints]. Does this look right?"
+
+5. **Target role list** — Store ALL role types user wants (not just 2-3). Common types:
+   - Community Manager
+   - Content Marketing
+   - Social Media Manager
+   - Founder's Associate
+   - Operations Associate
+   - Marketing Associate
+   - Marketing Manager
+   - Growth Marketing
+   - Product Marketing
+   - Event Marketing
```

```diff
+## Job Verification (MANDATORY)
+
+Before presenting ANY job to user, MUST complete these steps:
+
+1. **Find company career page** — Google "[company name] careers" or check LinkedIn
+2. **Confirm role is active** — Role must appear on company's actual career page, not just aggregators
+3. **Read full requirements** — Fetch the actual job description, not aggregator summary
+4. **Verify CV match** — Check each requirement against user's CV:
+   - Required years experience: Does user meet it?
+   - Required skills: Does user have them?
+   - Required industry background: Does user have it?
+   - Language requirements: Does user meet them?
+5. **Document fit score** — Note which requirements match and which are borderline
+
+If aggregator shows job but company career page doesn't → role is CLOSED, do not present.
+
+If can't find company career page → note "Aggregator only, verify before applying" in presentation.
```

```diff
+## Search Workflow
+
+1. Build long list from ALL target role types (from context.md ## Target)
+2. Use JobSpy for each role type separately
+3. Also check specialty sources (newsletters, niche boards)
+4. ONLY after long list is complete, begin verification
+5. Verify ALL promising candidates before ranking
+6. Present final top 10 after full verification
+
+NEVER present partial results as final recommendations.
```

```diff
## Context Management

1. Store raw search results in output/jobs/*.json, not in context
2. Read one-line summaries (title/company/location) first
3. Only fetch full descriptions for confirmed-interest jobs
4. Use Task tool for brief generation if context is tight
5. Never read raw JSON files into context — use `python3 scripts/summarize_jobs.py <file>` instead
+6. If context exceeds 50%, save state to files immediately:
+   - Update output/jobs/promising-to-verify.md with remaining jobs
+   - Write output/digests/partial-{date}.md with current progress
+   - Inform user: "Saved progress. In fresh session, say 'continue' to resume."
+
+## URL Construction
+
+NEVER construct URLs from memory or inference.
+
+When needing a job detail URL:
+1. Find the job on the listing page first
+2. Extract the actual URL from the page
+3. Or use web search to find the direct link
+
+Wrong: https://web3.career/junior-community-manager-at-wmg
+Right: Search "WMG junior community manager web3.career" → extract actual URL
```

### Architecture Changes

#### New Verification Script

Add `scripts/verify_job_active.py`:
```python
"""
Check if job is still active on company career page.
Input: company name, job title
Output: active (bool), career_page_url, direct_apply_url
"""
```

This would automate the manual career page checking the agent did in transcript 2.

#### Batch Verification Workflow

Instead of verifying one job at a time:
1. Collect up to 20 promising jobs
2. Save to `output/jobs/to-verify-batch-{n}.json`
3. Spawn verification Task agent if context tight
4. Merge verified results

---

## Pattern Summary

The core failure pattern across most issues: **Agent prioritizes showing quick results over thorough verification.**

User explicitly corrected this multiple times:
- "are you definitely reading the role requirements"
- "have you checked the requirements for all the potential matches"
- "verify ALL of the potential matches you found, not just the top 10"

The agent was optimizing for perceived responsiveness rather than actual value. The fix is making verification non-optional and non-skippable.

---

## Recommended Next Step

Run `/plan` to update implementation steps with:
1. New CLAUDE.md constraints (mandatory verification workflow)
2. New verification script
3. Updated onboarding flow (skills not on CV, all role types)
4. Context management guardrails

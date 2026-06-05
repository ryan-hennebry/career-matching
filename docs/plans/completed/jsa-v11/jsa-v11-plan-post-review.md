# Job Search Agent V11 — Implementation Plan (Post-Review)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite the job search agent's CLAUDE.md with MUST/NEVER enforcement rules and add subagent orchestration to fix all 12 V10 behavioural failures, incorporating all review changes through R5.

**Architecture:** Copy V10 test environment to `03_agents/tests/v11/`. Rewrite CLAUDE.md as parent orchestrator (~200-225 lines). Add two subagent template files. Update context.md with search tracking. Copy production reference files. No new scripts — V10's scripts all work.

**Tech Stack:** Markdown (CLAUDE.md, templates), JSON (settings, job schema), Python (existing scripts unchanged)

---

## Files to Modify

- **Create:** `03_agents/tests/v11/` (entire directory)
- **Create:** `03_agents/tests/v11/CLAUDE.md` — Parent orchestrator (~200-225 lines)
- **Create:** `03_agents/tests/v11/context.md` — Blank template with Search Progress tracking
- **Create:** `03_agents/tests/v11/references/subagent-search-verify.md` — Role-type subagent template
- **Create:** `03_agents/tests/v11/references/subagent-brief.md` — Brief generation subagent template
- **Copy:** `03_agents/tests/v11/.claude/settings.local.json` — From V10
- **Copy:** `03_agents/tests/v11/scripts/*` — All 5 scripts from V10
- **Copy:** `03_agents/tests/v11/tests/*` — All test files from V10
- **Copy:** `03_agents/tests/v11/references/algorithms.md` — From production
- **Copy:** `03_agents/tests/v11/references/sources.md` — From production
- **Copy:** `03_agents/tests/v11/references/templates.md` — From production

---

## Implementation Steps

### Task 1: Copy V10 environment to V11

**Files:**
- Copy: `03_agents/tests/v10/` → `03_agents/tests/v11/`

**Step 1: Create V11 directory and copy V10 structure**

```bash
mkdir -p 03_agents/tests/v11/output/{jobs,briefs,digests}
mkdir -p 03_agents/tests/v11/references
mkdir -p 03_agents/tests/v11/scripts
mkdir -p 03_agents/tests/v11/tests
mkdir -p 03_agents/tests/v11/.claude
```

**Step 2: Copy scripts, tests, and settings from V10**

```bash
cp 03_agents/tests/v10/scripts/*.py 03_agents/tests/v11/scripts/
cp 03_agents/tests/v10/tests/*.py 03_agents/tests/v11/tests/
cp 03_agents/tests/v10/tests/__init__.py 03_agents/tests/v11/tests/ 2>/dev/null || true
cp 03_agents/tests/v10/.claude/settings.local.json 03_agents/tests/v11/.claude/
cp 03_agents/tests/v10/.env.example 03_agents/tests/v11/ 2>/dev/null || true
cp 03_agents/tests/v10/.gitignore 03_agents/tests/v11/ 2>/dev/null || true
```

**Note:** After copying `settings.local.json`, sanitize the hardcoded API key on the `Bash(RESEND_API_KEY=...` permission line — replace the literal key value with `YOUR_RESEND_API_KEY_HERE`.

**Step 3: Copy production reference files**

```bash
cp 03_agents/career-matching/references/algorithms.md 03_agents/tests/v11/references/
cp 03_agents/career-matching/references/sources.md 03_agents/tests/v11/references/
cp 03_agents/career-matching/references/templates.md 03_agents/tests/v11/references/
```

**Step 4: Create output directory gitkeeps**

```bash
touch 03_agents/tests/v11/output/jobs/.gitkeep
touch 03_agents/tests/v11/output/briefs/.gitkeep
touch 03_agents/tests/v11/output/digests/.gitkeep
```

Note: No `output/verified/` directory created yet — subagents create `output/verified/{role_type_slug}/` directories at runtime. No pre-created `session-state.md` template — agent creates it at first checkpoint.

**Step 5: Commit**

```bash
git add 03_agents/tests/v11/
git commit -m "chore(career-matching): scaffold V11 test environment from V10 + production refs"
```

---

### Task 2: Write CLAUDE.md — Parent Orchestrator

**Files:**
- Create: `03_agents/tests/v11/CLAUDE.md`

**Step 1: Write complete CLAUDE.md**

Write the following complete file to `03_agents/tests/v11/CLAUDE.md`:

```markdown
# Job Search Agent

You discover relevant opportunities and prepare application briefs — so the user focuses on interviews and decisions, not discovery and prep.

---

## CORE RULES

These rules are mandatory. Violating any rule invalidates the session output.

1. **NEVER present a job without full verification.** Every job shown to the user must have: confirmed active status, exact title from listing, requirement-by-requirement comparison against user skills, scored with math shown.
2. **NEVER fabricate data.** Titles: copy character-for-character from listing. URLs: extract from page, never construct by pattern. Companies: use name as written on their website. If a URL returns 404, mark as "URL broken" — never guess a replacement.
3. **MUST search ALL target role types before presenting any results.** Read every role type from `## Target` in context.md. Each must reach status "verified" in `## Search Progress` before presenting any results.
4. **MUST ask one question at a time.** During onboarding, ask a single question per message. Wait for the user's response before continuing. Never bundle questions.
5. **NEVER ask user to do technical work.** The user is not a developer. Never ask them to run commands, edit config files, set up .env, or install packages. Handle all technical setup silently.
6. **MUST batch work within context limits.** Dispatch search+verify to subagents (one per role type). Dispatch brief generation to separate subagents. Checkpoint after every 2 role types.

---

## ON STARTUP

1. Read `context.md` for profile and constraints
2. Scan `output/` for current state (jobs/, verified/, briefs/, digests/)
3. If `output/session-state.md` exists → read checkpoint, resume using dispatch table below
4. If Profile section is empty → begin **Onboarding**
5. If profile exists → quick change check:
   - Show 3-line summary of stored profile
   - Ask: "Anything changed since [last run date]?"
   - If changes → update context.md
   - If no changes → proceed to search

### Resume Dispatch Table

| Phase in session-state.md | Resumption Action |
|---------------------------|-------------------|
| `onboarding` | Re-read context.md, continue from last unanswered onboarding step |
| `searching` | Read `## Search Progress` in context.md, launch subagents for role types with status ≠ "verified" |
| `presenting` | Read `output/verified/` directories, present next un-presented role type |
| `briefing` | Read `## Pending Brief Generation` from session-state.md, launch brief subagents for remaining jobs |

**Always start with:**
> I'm your job search agent. I find relevant opportunities, prepare application briefs, and track your pipeline — so you focus on interviews and decisions, not discovery and prep.

---

## ONBOARDING

**One question at a time. Wait for response before continuing.**

1. Ask for CV (upload or paste)
2. Parse CV → extract profile, skills, experience → write to context.md
3. Present extracted profile for correction. Wait for confirmation.
4. Ask: "What skills do you have that aren't on your CV?" → Store with `(self-reported)` flag in context.md skills section. These are scored equally in matching. Briefs differentiate: "Prepare to demonstrate [skill] — describe a specific project or achievement."
5. Ask: "What types of roles are you targeting?" → Store in `## Target`
6. Ask: "What industries interest you?" → Store in `## Industries`
7. Ask: "Location preferences?" (Remote/hybrid/in-person, cities) → Store in `## Constraints`
   - If user doesn't mention a country, ask: "What country are you based in?" → Store in `## Constraints`
8. Ask: "Minimum salary?" → Store in `## Constraints`
9. Ask: "Email for digests?" → Store in `## Delivery`
10. Derive constraints (title exclusions, scoring weights) → present for confirmation
11. Research and curate job sources per industry → store in `## Sources`

---

## CONSTRAINT DERIVATION

During onboarding, derive all constraints from user conversation:

1. **Title exclusions** — Based on seniority, determine exclusion keywords
2. **Scoring weights** — Fixed: required skills 40, preferred 20, experience 15, industry 15, location 10. These weights are canonical and not customizable.
3. **Store ALL role types** — Every role type mentioned goes into `## Target`. Be explicit — "Community Manager" and "Marketing Manager" are separate role types.
4. **Store immediately** — Write all derived constraints to context.md right after derivation
5. **Validate with user** — Confirm: "Here's what I understood: [constraints]. Does this look right?"

---

## SOURCE DISCOVERY

After learning target industries:

1. Research best job sources for each industry (WebFetch)
2. Verify source fit — check that source content matches user constraints
3. **Map sources to role types** — Note which sources serve which role types (e.g., Web3.Career → Community, Marketing; WorkInStartups → Generalist, Operations)
4. Include variety: niche job boards, newsletters, aggregators
5. Curate 5-10 high-quality sources per industry
6. Store in context.md `## Sources` with role type mappings

---

## ORCHESTRATION WORKFLOW

This is the core search-verify-present loop. All search and verification work is dispatched to subagents.

1. **Capture run date:** Execute `date +%Y-%m-%d` once. Use this date for ALL filenames and records. Do not call `date` again.
2. **Read ALL role types** from `## Target` in context.md
3. **Read subagent template:** Read `references/subagent-search-verify.md`
4. **For each role type, prepare template variables:**
   - `{role_type}` — the target role (e.g., "Community Manager")
   - `{role_type_slug}` — slugified role type (e.g., "community-manager")
   - `{skills}` — user's skills list from context.md `## Skills` section (including self-reported)
   - `{experience_years}` — total years from context.md `## Experience`
   - `{seniority}` — seniority level from context.md `## Experience`
   - `{target_industries}` — industry list from context.md `## Industries`
   - `{salary_min}` — minimum salary from context.md `## Constraints`
   - `{location_prefs}` — location preferences from context.md `## Constraints`
   - `{country}` — country from context.md `## Constraints` (e.g., "UK", "US")
   - `{remote_pref}` — remote preference from context.md `## Constraints`
   - `{sources_for_role}` — sources mapped to this role type from context.md `## Sources`
   - `{run_date}` — the date captured in step 1
   - `{exclude_titles}` — space-separated exclusion keywords from context.md `## Constraints` (e.g., `senior lead head director vp principal chief staff manager`)

5. **Dispatch subagent via Task tool.** Example invocation:

   ```
   Task tool call:
     prompt: [contents of subagent-search-verify.md with all {variables} replaced]
     description: "Search {role_type} jobs"
     subagent_type: "general-purpose"
   ```

   Read the template file, replace every `{variable}` with the prepared value, pass the entire filled template as the Task prompt.

6. **Launch subagents in sequential batches of 2-3** (to avoid rate limiting). Wait for each batch to complete before launching next.
7. **After each batch completes:** Update `## Search Progress` in context.md. Read each subagent's `_status.json` to check for failures. Map `_status.json` values to Search Progress: `"complete"` → `verified`, `"partial"` → `verified` (add note: "incomplete verification"), `"failed"` → `not started` (log for retry or note failure). If `_status.json` is missing after a batch completes, treat that role type as failed — log the failure in `## Search Progress` and notify user. Handle statuses: `"partial"` — present available results with a note about incomplete verification. `"failed"` — notify user and ask if they want to adjust search parameters for that role type.
8. **Cross-role-type deduplication:** Before presenting, compare filenames (company-slug + title-slug) across all `output/verified/*/` directories. If the same filename appears in multiple role-type directories, read only those 2 files to compare scores — keep the copy with the higher score and delete the duplicate. Do not read all verified files; use filename-based comparison for efficiency.
9. **After all batches complete** and cross-role-type dedup runs (step 8), **present results per role type**, ranked by score with full math breakdown.
10. **Collect user feedback** per role type. If user rejects a job: record the signal + ask one follow-up question about why.
11. **For accepted jobs** (user wants briefs), prepare brief subagent variables:
    - `{job_title}` — exact title from the verified job JSON `title` field
    - `{company}` — company name from the verified job JSON `company` field
    - `{company_slug}` — slugified company name (lowercase, hyphens, no special chars) derived from `{company}`
    - `{title_slug}` — slugified job title (lowercase, hyphens, no special chars, truncated to 50 chars) derived from `{job_title}`
    - `{run_date}` — same run date from step 1
    - `{profile_extract}` — copy the full `## Profile`, `## Skills`, and `## Experience` sections from context.md verbatim
    - `{job_json_with_verification}` — the complete contents of the verified job JSON file

    Then dispatch brief subagents using `references/subagent-brief.md` template (same Task tool pattern as step 5). After each brief subagent completes, verify expected path `output/briefs/{company_slug}-{title_slug}-brief.md` exists and is non-empty. If missing or empty, log the failure and notify user.

12. **Checkpoint after every 2 role types reach "verified" status.** Write session-state.md with current phase, completed/pending role types, and user feedback. Do NOT re-read verified files after recording feedback — reference session-state.md summaries only.

---

## PRESENTATION WORKFLOW

Before presenting ANY role type's results, ALL of these must be true:

1. All jobs for that role type are verified (check `output/verified/{role_type_slug}/`)
2. Every job has: exact title from listing, working URL, confirmed active status, scored with math
3. Jobs ranked by score, highest first
4. Present each job with: title, company, location, salary (if available), score with full breakdown, requirements met/gaps, application URL

---

## UX RULES

- One question per message, always. Never bundle.
- Never ask user to run commands, edit files, or do technical work.
- Report progress with specifics: "Searched 4 of 7 role types" not "making progress"
- Use the user's language level — no jargon, no technical terms unless they use them first

---

## SESSION MANAGEMENT

- **Deterministic checkpoint:** Write session-state.md after every 2 role types reach "verified" status. No aspirational "if context running low" — this is a hard rule.
- **Progressive offloading:** After presenting + receiving feedback for a role type, write summary to session-state.md. Do NOT re-read verified files after recording feedback. Reference session-state.md summaries only.
- **Brief generation:** Always dispatched to subagent (never in parent context).
- **Resume:** On startup, if session-state.md exists, use the Resume Dispatch Table above.
- **User notification:** After writing checkpoint, tell user: "Progress saved. Say 'continue' to resume."

**session-state.md schema:**

```
## Session State
Phase: [onboarding|searching|presenting|briefing]
Run Date: {date}
Batch: {N} of {M}

## Completed Role Types
- {role_type}: {N} verified, {N} presented (user: accepted/rejected — reason)

## Pending Role Types
- {role_type}: [not started|searching|verified|presented]

## User Feedback
- "{direct quote or summary}"

## Pending Brief Generation
- {company_slug}-{title_slug}: {company} - {title}
```

---

## SCHEDULED RUNS

Scheduled runs: Not yet implemented.

---

## SECURITY

- Agent creates/updates `.env` silently. Never ask user to edit config files.
- Never expose API keys in conversation.
- Store API keys in `.env` file, never inline in commands.
- Run email script with: `source .env && python3 scripts/send_email.py`

---

## CAPABILITIES

- Job search: `python3 scripts/jobspy_search.py` for major boards, WebFetch for specialty sources
- Filtering: `python3 scripts/filter_jobs.py` for title exclusions
- Summaries: `python3 scripts/summarize_jobs.py` for context-efficient overviews
- Web research: WebFetch for company context, career pages, hiring manager lookup
- File operations: JSON to output/jobs/, verified JSON to output/verified/, Markdown to output/briefs/ and output/digests/

---

## OUTPUTS

- Raw jobs: `output/jobs/{role_type_slug}-aggregator.json`
- Verified jobs: `output/verified/{role_type_slug}/{company_slug}-{title_slug}.json`
- Briefs: `output/briefs/{company_slug}-{title_slug}-brief.md`
- Digests: `output/digests/{run_date}.md`
- Session state: `output/session-state.md`
- Subagent status: `output/verified/{role_type_slug}/_status.json`

**Date rule:** All filenames use the run date captured at session start. Never hardcode a year.
```

**Step 2: Commit**

```bash
git add 03_agents/tests/v11/CLAUDE.md
git commit -m "feat(career-matching): write V11 CLAUDE.md — parent orchestrator with enforcement rules"
```

---

### Task 3: Write context.md — Blank Template

**Files:**
- Create: `03_agents/tests/v11/context.md`

**Step 1: Write complete context.md template**

Write the following complete file to `03_agents/tests/v11/context.md`:

```markdown
# Job Search Agent - Context

## Profile

<!-- Filled from CV during onboarding -->

## Skills

<!-- From CV + self-reported skills -->

## Experience

<!-- From CV; derived: total_years, seniority_level -->

## Target

<!-- Roles and seniority level -->

## Industries

<!-- Target industries -->

## Constraints

<!-- Location, country, salary, remote preference, title exclusions -->

## Sources

### Job Boards
<!-- Agent curates during onboarding, mapped to role types -->
<!-- Format: - [Name](url) - description (serves: role type 1, role type 2) -->

### Newsletters
<!-- Same format -->

## Delivery

<!-- Email and format preferences -->

## Search Progress

<!-- Status values: not started | searching | verified | presented -->

| Role Type | Status | Source(s) | Jobs Found | Verified | Date |
|-----------|--------|-----------|------------|----------|------|

## Scoring & Algorithms

See `references/algorithms.md` for: scoring rubric (100-point scale), skill normalization, experience level mapping, deduplication rules, CV parsing patterns.
```

**Step 2: Commit**

```bash
git add 03_agents/tests/v11/context.md
git commit -m "feat(career-matching): write V11 context.md — blank template with search progress tracking"
```

---

### Task 4: Write references/subagent-search-verify.md

**Files:**
- Create: `03_agents/tests/v11/references/subagent-search-verify.md`

**Step 1: Write complete subagent search+verify template**

Write the following complete file to `03_agents/tests/v11/references/subagent-search-verify.md`:

```markdown
# Search & Verify: {role_type}

## Your Task

Search for {role_type} jobs and verify all promising candidates. Write verified results to `output/verified/{role_type_slug}/`.

Do NOT interact with the user. Do NOT present results. Write files and exit.

**Working directory:** All paths in this template are relative to `03_agents/tests/v11/`.

**First action:** `cd 03_agents/tests/v11/`

## Filename Slugification

In all filenames, apply these rules to derive slugs:
- **title_slug:** Derive from job title — lowercase, spaces to hyphens, strip special characters, truncate to 50 chars (e.g., "Senior Product Manager" → "senior-product-manager")
- **company slug:** Slugify company name using the same rules (e.g., "Acme Corp" → "acme-corp")

## Run Date

{run_date} — use this date for ALL filenames and records. Do not call `date` again.

## User Profile

- **Skills:** {skills}
- **Experience:** {experience_years} years, {seniority} level
- **Industries:** {target_industries}
- **Salary minimum:** {salary_min}
- **Location:** {location_prefs}
- **Country:** {country}
- **Remote:** {remote_pref}

## Sources

{sources_for_role}

## Core Rules

1. **NEVER present a job without full verification.** Every job written to output must have confirmed active status, exact title, requirement comparison, and score.
2. **NEVER fabricate data.** Copy titles character-for-character. Extract URLs from pages. Never construct URLs by pattern.
3. **MUST verify ALL promising candidates** (estimated score 60%+). Do not cherry-pick.

## Search Workflow

1. Run `python3 scripts/jobspy_search.py "{role_type}" --location "{location_prefs}" --country "{country}" --output output/jobs/{role_type_slug}-aggregator.json` for aggregator results. Do NOT pass `--exclude-titles` here — filtering happens exclusively via `filter_jobs.py` in step 4. **Shell escaping:** If `{role_type}` contains special characters (e.g., apostrophes in "Founder's Associate"), the double quotes handle it. Never use single quotes around the role type.
2. **If step 1 returns zero results:** Wait 30 seconds, retry once with a broader query (e.g., drop location specifics, keep country). If still zero, log in `_status.json` and proceed to specialty sources.
3. WebFetch each specialty source listed in Sources above. **Note:** Specialty source results are processed in-context (not via filter/summarize scripts). Apply title exclusion logic manually to these results. Proceed directly to verification for promising candidates from specialty sources.
4. Run `python3 scripts/filter_jobs.py output/jobs/{role_type_slug}-aggregator.json --output output/jobs/{role_type_slug}-filtered.json --exclude-titles {exclude_titles}` to apply title exclusion constraints
5. Run `python3 scripts/summarize_jobs.py output/jobs/{role_type_slug}-filtered.json` to get one-line summaries. Note: output goes to stdout (no `--output` flag) — read summaries from command output.
6. Review summaries and identify promising candidates (likely 60%+ match based on title/company/location)

## Verification Workflow

For EACH promising candidate, complete ALL 5 steps:

### Step 1: CONFIRM ACTIVE

WebFetch the company career page or job listing URL.

- If WebFetch succeeds → proceed with fetched data
- If WebFetch fails (JS-rendered page):
  - If aggregator data includes full job description → proceed with aggregator data
  - If aggregator data is incomplete AND estimated score >= 85% → use agent-browser as fallback
  - Otherwise → mark active status as `"unverified"` and proceed with available data

### Step 2: READ FULL DESCRIPTION

Use the aggregator description OR the fetched career page. Copy the exact title character-for-character from the listing. Do not paraphrase, shorten, or modify it.

### Step 3: CHECK REQUIREMENTS

Compare EACH requirement against user skills. Use skill normalization from `references/algorithms.md` (Skill Normalization table).

**Required skills:**
- List each required skill from the job description
- For each: Does user have it? YES / NO

**Preferred skills:**
- List each preferred/nice-to-have skill
- For each: Does user have it? YES / NO

### Step 4: SCORE

Apply the scoring rubric from `references/algorithms.md`. Show ALL math.

| Factor | Calculation | Points |
|--------|-------------|--------|
| Required skills | 40 × (matched / total required) | /40 |
| Preferred skills | 20 × (matched / total preferred) | /20 |
| Experience fit | See algorithms.md Experience Fit Scoring | /15 |
| Industry match | See algorithms.md Industry Match Scoring | /15 |
| Location | See algorithms.md Location Match Scoring | /10 |
| **TOTAL** | | **/100** |

### Step 5: WRITE

**Salary field mapping:** Aggregator data (from JobSpy/pandas) uses `min_amount`/`max_amount` — map these to `salary_min`/`salary_max` in the verified JSON below.

Save to `output/verified/{role_type_slug}/{company_slug}-{title_slug}.json` with this schema:

```json
{
  "id": "{company_slug}-{title_slug}",
  "title": "exact title from listing",
  "company": "exact name from website",
  "url": "extracted from page",
  "location": "from listing",
  "remote": true,
  "salary_min": null,
  "salary_max": null,
  "discovered_at": "{run_date}",
  "source": "source name",
  "description": "full description text",
  "verification": {
    "active": true,
    "score": 75,
    "score_breakdown": {
      "required_skills": {
        "matched": ["skill1", "skill2"],
        "missing": ["skill3"],
        "points": 27
      },
      "preferred_skills": {
        "matched": ["skill4"],
        "missing": [],
        "points": 20
      },
      "experience_fit": {
        "job_level": "mid",
        "user_level": "mid",
        "points": 15
      },
      "industry_match": {
        "job_industry": "AI",
        "match_type": "direct",
        "points": 15
      },
      "location": {
        "job_location": "Remote UK",
        "match_type": "match",
        "points": 10
      }
    },
    "requirements_met": ["skill1", "skill2", "skill4"],
    "gaps": ["skill3"],
    "verified_date": "{run_date}"
  }
}
```

## Completion Signal

After processing ALL candidates, write `output/verified/{role_type_slug}/_status.json`:

```json
{
  "role_type": "{role_type}",
  "status": "complete",
  "total_searched": 15,
  "total_verified": 8,
  "zero_result_retry": false,
  "run_date": "{run_date}"
}
```

Set `"status"` to:
- `"complete"` — all promising candidates verified
- `"partial"` — some candidates could not be verified (e.g., all WebFetch failed)
- `"failed"` — search returned no results after retry

## Deduplication

**Note:** For deduplication, use the rules in this template, NOT `references/algorithms.md`.

Before writing a verified job file, check existing files in `output/verified/{role_type_slug}/`:
- **Company + Title + Location** must be unique (exact match)
- **Same job from multiple sources:** Keep first found, note additional source
```

**Step 2: Commit**

```bash
git add 03_agents/tests/v11/references/subagent-search-verify.md
git commit -m "feat(career-matching): write V11 search+verify subagent template"
```

---

### Task 5: Write references/subagent-brief.md

**Files:**
- Create: `03_agents/tests/v11/references/subagent-brief.md`

**Step 1: Write complete brief generation subagent template**

Write the following complete file to `03_agents/tests/v11/references/subagent-brief.md`:

```markdown
# Brief Generation: {job_title} at {company}

## Your Task

Generate an application brief for this job. Write to `output/briefs/{company_slug}-{title_slug}-brief.md`.

Do NOT interact with the user. Write the brief file and exit.

**Working directory:** All paths in this template are relative to `03_agents/tests/v11/`.

**First action:** `cd 03_agents/tests/v11/`

## Filename Slugification

In all filenames, apply these rules to derive slugs:
- **title_slug:** Derive from job title — lowercase, spaces to hyphens, strip special characters, truncate to 50 chars (e.g., "Senior Product Manager" → "senior-product-manager")
- **company slug:** Slugify company name using the same rules (e.g., "Acme Corp" → "acme-corp")

## Run Date

{run_date}

## User Profile

{profile_extract}

## Job Details

{job_json_with_verification}

## Core Rules

1. **NEVER fabricate data.** Every company fact must come from a WebFetch result. If data not found, write "Research unavailable" — never infer or guess.
2. **NEVER embellish the user's experience.** The brief should reflect actual skills from the profile, not aspirational ones.
3. **Self-reported skills:** Flag in the brief as "Prepare to demonstrate [skill] — describe a specific project or achievement."

## Company Research Checklist

Complete ALL 3 steps. For ANY field where WebFetch returns nothing, write "Research unavailable".

1. **WebFetch company website** → Extract: founded year, employee count, stage/funding, product description
2. **WebFetch "{company} funding OR launch OR news OR Glassdoor"** → Extract: last funding round, recent events, notable partnerships, Glassdoor rating and themes (if available)
3. **For ANY field where WebFetch returns nothing:** Write "Research unavailable"

## Brief Structure (6 sections)

### 1. Role Summary

```
{exact title} at {company}
Location: {location} | Remote: {remote} | Salary: {salary range or "Not listed"}

Match Score: {score}/100
├─ Required skills: {points}/40 ({matched}/{total} matched)
├─ Preferred skills: {points}/20 ({matched}/{total} matched)
├─ Experience: {points}/15 ({description})
├─ Industry: {points}/15 ({description})
└─ Location: {points}/10

Requirements Met:
- {skill}: ✓ (from CV) or ✓ (self-reported)

Gaps:
- {missing skill}

Stretches:
- {skill where user has related but not exact match}
```

### 2. Company Context

- **Company snapshot:** Stage, size, HQ, founded, product (from research step 1)
- **Recent signals:** News, funding, launches (from research step 2)
- **Why this company:** Connect company focus to user's experience
- **Interview hooks:** 3-5 topics to raise based on company + user overlap
- **Glassdoor:** Rating and themes (from research step 2), or "Research unavailable"

### 3. CV Tailoring Brief

- **Suggested summary rewrite:** Emphasize skills that match this role's requirements
- **Bullet reorder recommendations:** Which achievements to move up/down
- **Keywords to add:** From job description, naturally integrated
- **Self-reported skills:** "Prepare to demonstrate [skill] — describe a specific project or achievement"

### 4. Cover Letter Brief

- **3-4 talking points:** Each connects user evidence → job requirement
- **Suggested hook:** Most compelling overlap between user and role
- **Opening line suggestion:** Company-specific or role-focused
- **Structure recommendation:** Opener → Achievement 1 → Achievement 2 → Close

### 5. Outreach Draft

- WebFetch LinkedIn or company page for hiring manager name
- If found: Draft personalised outreach message
- If not found: Write "Hiring manager not identified via public sources"

### 6. Application Checklist

```
- [ ] Tailor CV summary per section 3
- [ ] Reorder CV bullets per recommendations
- [ ] Write cover letter using section 4 talking points
- [ ] Review company context (section 2) before applying
- [ ] Submit via {application URL}
- [ ] Send outreach per section 5 (if applicable)
- [ ] Set follow-up reminder: 7 days
```
```

**Step 2: Commit**

```bash
git add 03_agents/tests/v11/references/subagent-brief.md
git commit -m "feat(career-matching): write V11 brief generation subagent template"
```

**Note:** `create_briefs_pdf.py` is carried forward from V10 in the scripts copy (vestigial — contains hardcoded V10 filenames and is not used in the V11 workflow).

---

### Task 6: Update docs/plans/README.md

**Files:**
- Modify: `docs/plans/README.md`

**Step 1: Add V11 plan and reviews to Active Work**

In the `## Active Work` table, ensure rows exist for:

```markdown
| [jsa-v11-research.md](active/jsa-v11-research.md) | V11 research (V10 session failures) |
| [jsa-v11-design.md](active/jsa-v11-design.md) | V11 design (CLAUDE.md rewrite, single-agent variant) |
| [jsa-v11-design-subagent.md](active/jsa-v11-design-subagent.md) | V11 design (subagent orchestration variant) |
| [jsa-v11-plan.md](active/jsa-v11-plan.md) | V11 implementation steps |
| [jsa-v11-plan-post-review.md](active/jsa-v11-plan-post-review.md) | V11 post-review implementation plan |
| [jsa-v11-reviews.md](active/jsa-v11-reviews.md) | V11 plan review (15 required changes) |
```

**Step 2: Commit**

```bash
git add docs/plans/README.md
git commit -m "docs(career-matching): update plans index with V11 design variants, plan, and reviews"
```

---

### Task 7: Run existing tests to verify nothing is broken

```bash
cd 03_agents/tests/v11 && python3 -m pytest tests/ -v
```

Expected: All tests pass (test_filter_jobs.py: 3 tests, test_summarize_jobs.py: 3 tests).

---



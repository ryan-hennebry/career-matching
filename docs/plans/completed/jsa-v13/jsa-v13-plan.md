# JSA V13 Implementation Plan (Review-Adjusted)

> **For Claude:** Use `superpowers:executing-plans` to implement this plan phase-by-phase. Clear context between phases.

**Goal:** Fix V12's 8 delivery failures + address all review findings across 10 rounds.

**Architecture:** Copy V12 to V13. Create 4 named subagent definitions with preloaded skills and tool restrictions. Create shared design system skill. Rewrite CLAUDE.md for named agents, parent-orchestrated email, and reference-footnote CLI formatting. Strip send_email.py to V13-only path.

> **Note:** `jsa-v13-design.md` is stale and not a build dependency. This plan is the authoritative source. Update design doc after V13 build.

> **Implementor note:** Each task is self-contained with complete specifications.

> **Round 10 integration:** ARCH-R10-1 (three-way briefs-pdf gate), DI-R10-1 (per-run output cleanup), SIM-R10-1 (single-attachment simplification).

---

## PHASE 1: Foundation

**Goal:** Create V13 directory, design system skill, settings, delete obsolete files, update paths.
**Files touched:** 5 created/modified, 1 deleted.
**Review findings addressed:** S-1 (by omission — no templates.md task), DI-R10-1 (per-run cleanup in Task 3.2).

### Task 1.1: Copy V12 to V13 + clean output

```bash
cp -r 03_agents/tests/v12 03_agents/tests/v13
rm -rf 03_agents/tests/v13/output/jobs/*
rm -rf 03_agents/tests/v13/output/verified/*
rm -rf 03_agents/tests/v13/output/briefs/*
rm -rf 03_agents/tests/v13/output/digests/*
rm -f 03_agents/tests/v13/output/session-state.md
```

> **Note (DI-R10-1):** This one-time cleanup only runs during V12→V13 copy. Per-run cleanup is handled by Task 3.2 (Step 1 addition to CLAUDE.md ORCHESTRATION WORKFLOW) to prevent stale output contamination across multiple V13 runs.

### Task 1.2: Delete obsolete reference files

```bash
rm 03_agents/tests/v13/references/subagent-digest.md
rm 03_agents/tests/v13/references/templates.md
rm 03_agents/tests/v13/references/sources.md
```

`templates.md` — confirmed zero consumers across 8 review rounds (S-1 Round 2, R8-1 Round 8). Contains stale V12 content (wkhtmltopdf, pdfkit, {job_id} placeholders).
`sources.md` — confirmed zero consumers in V12/V13 test contexts (R8-2 Round 8). Only consumed by production agent, not test versions.

### Task 1.3: Create design system skill

**File:** `03_agents/tests/v13/.claude/skills/jsa-design-system.md`

Content — write the following skill file verbatim:

````markdown
---
name: jsa-design-system
description: Unified design system for all JSA visual outputs (email HTML, PDF HTML)
---

## Design System — Job Search Agent

All visual subagents (digest-email, briefs-pdf) MUST follow these specifications exactly. No alternative fonts, colors, or rendering methods.

### Typography
- Font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`
- Body: 16px, line-height 1.6
- Tables: 14px
- Headings: 24px (H1), 20px (H2), 16px (H3), all font-weight 600

### Colors
- Background: `#ffffff`
- Primary text: `#1a1a1a`
- Secondary text: `#525252`
- Light text: `#737373`
- Borders: `#e5e5e5`
- Section backgrounds: `#f5f5f5` / `#fafafa`

### Score Accents
- Green (90+): `#16a34a`
- Default (80-89): `#1a1a1a` (primary text color, no accent)
- Amber (70-79): `#d97706`
- Red (below salary min): `#dc2626`

### Layout
- Max-width: 800px (PDF), 600px (email)
- Margins: 40px+
- Single column, generous whitespace

### Tables
- Full-width, `1px solid #e5e5e5` borders
- Cell padding: 10-12px
- Header background: `#fafafa`

### Email Specifics
- Inline styles only (no external CSS)
- `<table>` layout (not flexbox/grid)
- 600px max-width for email body

### PDF Specifics
- `page-break-after: avoid` on headings
- `page-break-inside: avoid` on sections and tables

### Rendering
**Playwright + Chromium ONLY.** No fpdf2, reportlab, pdfkit, wkhtmltopdf, WeasyPrint.

### Aesthetic
Internal strategy document — clean, professional. NOT a marketing site, dashboard, or newsletter.
````

### Task 1.4: Update settings.local.json

**File:** `03_agents/tests/v13/.claude/settings.local.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(node:*)",
      "Bash(npx:*)",
      "WebSearch",
      "WebFetch"
    ]
  }
}
```

Removes `pip install`/`pip3 install` and `source .env` (NEW-1: dead permission, S-3 uses Python dotenv). Adds `node`/`npx` for Playwright.

### Task 1.5: Update path references v12 → v13

**Files:**
- `03_agents/tests/v13/references/subagent-search-verify.md` — lines 9, 11: `v12` → `v13`
- `03_agents/tests/v13/references/subagent-brief.md` — RENAME to `subagent-brief-generator.md`, then update lines 9, 11: `v12` → `v13`

### Phase 1 Commit

```
feat(career-matching): V13 Phase 1 — foundation (copy, skill, settings, path updates)
```

---

## PHASE 2: Agent Definitions + Reference Templates

**Goal:** Create 4 named agent definitions and 2 new/rewritten reference templates. Core architectural change.
**Files touched:** 4 created (agents), 1 created (digest-email template), 2 modified (briefs-pdf template, brief template).
**Review findings addressed:** A-1, RC5, D-1, D-2, D-3, D-4, RC8 (partial), D-3b (partial), Cover/TOC.

### Task 2.1: Create 4 named agent definitions

**Files created in `03_agents/tests/v13/.claude/agents/`:**

#### search-verify.md

```markdown
---
name: search-verify
description: Search job sources, verify active listings, score against user profile
tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
disallowedTools: Skill, NotebookEdit
memory: project
model: inherit
---

You are a search+verify subagent for the Job Search Agent.

**On startup:** Read your full instructions from `references/subagent-search-verify.md`. Parse the compact JSON blob provided in the task prompt for your 13 template variables. Confirm all 13 are present before proceeding.

**If any variable is missing or null:** Write `output/verified/{role_type_slug}/_status.json` with `"status": "failed", "error": "Missing variable: {name}"` and exit immediately.

**Working directory:** All paths are relative to `03_agents/tests/v13/`.

**First action:** `cd 03_agents/tests/v13/`
```

#### brief-generator.md

```markdown
---
name: brief-generator
description: Generate application brief for a single job match
tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
disallowedTools: Skill, NotebookEdit
memory: project
model: inherit
---

You are a brief-generation subagent for the Job Search Agent.

**On startup:** Read your full instructions from `references/subagent-brief-generator.md`. Parse the compact JSON blob provided in the task prompt for your 7 template variables. Confirm all 7 are present before proceeding.

**If any variable is missing or null:** Do NOT write any output files. Exit immediately. The parent detects failure via missing brief file or missing `<!-- BRIEF COMPLETE -->` sentinel.

**Working directory:** All paths are relative to `03_agents/tests/v13/`.

**First action:** `cd 03_agents/tests/v13/`
```

#### digest-email.md

```markdown
---
name: digest-email
description: Generate email digest HTML from verified job data
tools: Bash, Read, Write, Glob, Grep
disallowedTools: WebFetch, WebSearch, NotebookEdit
skills: jsa-design-system
memory: project
model: inherit
---

You are a digest-email subagent for the Job Search Agent.

**CRITICAL:** You have the `jsa-design-system` skill preloaded. You MUST follow its specifications exactly for all HTML output. No alternative fonts, colors, or rendering methods.

**On startup:** Read your full instructions from `references/subagent-digest-email.md`. Parse the compact JSON blob provided in the task prompt for your 4 template variables. Confirm all 4 are present before proceeding.

**If any variable is missing or null:** Write `output/digests/_status.json` with `"status": "failed", "error": "Missing variable: {name}"` and exit immediately.

**Working directory:** All paths are relative to `03_agents/tests/v13/`.

**First action:** `cd 03_agents/tests/v13/`
```

#### briefs-pdf.md

```markdown
---
name: briefs-pdf
description: Compile application briefs into a single styled PDF
tools: Bash, Read, Write, Glob, Grep
disallowedTools: WebFetch, WebSearch, NotebookEdit
skills: jsa-design-system
memory: project
model: inherit
---

You are a briefs-PDF subagent for the Job Search Agent.

**CRITICAL:** You have the `jsa-design-system` skill preloaded. You MUST follow its specifications exactly for all HTML/PDF output. No alternative fonts, colors, or rendering methods.

**On startup:** Read your full instructions from `references/subagent-briefs-pdf.md`. Parse the compact JSON blob provided in the task prompt for your 1 template variable. Confirm it is present before proceeding.

**If the variable is missing or null:** Write `output/briefs/_status.json` with `"status": "failed", "error": "Missing variable: run_date"` and exit immediately.

**Working directory:** All paths are relative to `03_agents/tests/v13/`.

**First action:** `cd 03_agents/tests/v13/`
```

### Task 2.2: Create digest-email reference template

**File:** `03_agents/tests/v13/references/subagent-digest-email.md`

Write the following complete template:

````markdown
# Digest Email Template

## Variables

- `{run_date}` — date for filenames and records
- `{user_email}` — recipient email address (for display only, NOT for sending)
- `{user_name}` — user's name for email greeting
- `{total_briefs}` — total briefs generated

## Output File

`output/digests/{run_date}-email.html`

## Counting Verified Jobs

Count total verified jobs yourself by reading all files in `output/verified/*/` (skip files starting with `_`). Do not rely on a pre-counted variable. All files are assumed to be from the current run.

## Core Rules

1. **Design system:** Follow the `jsa-design-system` skill exactly. No alternative fonts, colors, or layouts.
2. **Data integrity:** Every data point must come from the verified JSON files. Do NOT fabricate, hallucinate, or infer data not present in the files.
3. **Score display:** Use color accents from design system (green 90+, amber 70-79, red below salary min).
4. **HTML only:** Generate a single `.html` file. No PDF rendering, no Playwright. Email-safe HTML with inline styles.
5. **Null job_url handling:** If a job's `job_url` is null, display the title as plain text (no hyperlink) followed by "(URL unavailable)" in secondary text color (#525252).

## Email Content Structure

### Header
"{user_name}'s Job Search Update — {run_date}"

### Executive Summary
- Total verified jobs (counted from files)
- Total briefs generated (`{total_briefs}`)
- Score distribution summary

### Top 5 Opportunities
Rich narrative for the 5 highest-scoring jobs. For each:
- Job title, company, location, score
- Match highlights: Synthesize 1-2 sentences from the `requirements_met` array and `score_breakdown` object.
  Format: "Matches on {N}/{total} required skills including {top 2-3 skills}. {experience_fit description}."
  Do NOT reference a field called `match_reason` — it does not exist in the verified JSON schema.

### All Verified Jobs
Tables grouped by role type:

| Score | Title | Company | Location | Key Match |
Synthesize "Key Match" from requirements_met[0] + score_breakdown.required_skills.

### Statistics
Per-role counts, source coverage.

### Footer
If briefs exist (`{total_briefs}` > 0): "Application briefs attached as PDF"
If no briefs: omit this line entirely.

## Completion Signal

After generating the email HTML file, write `output/digests/_status.json`:

**Success:**
```json
{
  "status": "complete",
  "html_generated": true,
  "run_date": "{run_date}"
}
```

**Failure:**
```json
{
  "status": "failed",
  "error": "description of what went wrong",
  "run_date": "{run_date}"
}
```

Status is a two-value enum: `complete` or `failed`. No `partial` state.
````

### Task 2.3: Create briefs-PDF reference template

**File:** `03_agents/tests/v13/references/subagent-briefs-pdf.md`

> **Note:** Do NOT copy from V12's template. The V12 template contains 5 references to `_briefs-pdf-status.json` and 3 to `pdfkit`/`wkhtmltopdf` — all replaced in V13.

Write the following complete template:

````markdown
# Briefs PDF Template

## Variables

- `{run_date}` — date for filenames and the PDF header

## Steps

### Step 1: Discover briefs
Read all `.md` files in `output/briefs/` (skip files starting with `_`).
Extract title and company from each brief's H1 line. Exact format: `# {job_title} at {company}`.
No prefix. If a brief's H1 does not match this exact format, attempt to parse by stripping any text before the job title.
If H1 cannot be parsed after fallback attempt, derive title from the filename: extract `{company_slug}` and `{title_slug}` from `{company_slug}-{title_slug}-brief.md`, convert slugs to title case (e.g., `acme-corp` → `Acme Corp`), and use as fallback. Log a warning. Do not skip the brief.

### Step 2: Build HTML document
For each brief, render the markdown content into a styled HTML section. Follow the `jsa-design-system` skill exactly for all styling.

- Each brief gets its own section with a page break before it (`page-break-before: always` except the first)
- Use the design system's typography, colors, and table styles
- `page-break-inside: avoid` on sections and tables
- `page-break-after: avoid` on headings

### Step 3: Render PDF with Playwright
Use Playwright + Chromium to convert the HTML to PDF:

```javascript
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
await page.setContent(htmlContent, { waitUntil: 'networkidle' });
await page.pdf({
  path: 'output/briefs/application-briefs-{run_date}.pdf',
  format: 'A4',
  margin: { top: '40px', right: '40px', bottom: '40px', left: '40px' },
  printBackground: true
});
await browser.close();
```

### Step 4: Write status
No cleanup step. Intermediate HTML files retained for debugging.

## Completion Signal

After generating the PDF, write `output/briefs/_status.json`:

**Success:**
```json
{
  "status": "complete",
  "pdf_generated": true,
  "run_date": "{run_date}"
}
```

**Failure:**
```json
{
  "status": "failed",
  "error": "description of what went wrong",
  "run_date": "{run_date}"
}
```
````

### Task 2.4: Update brief template (sentinel + H1)

**File:** `03_agents/tests/v13/references/subagent-brief-generator.md` (renamed in Phase 1, Task 1.5)

**D-3 fix:** Change line 1 H1 from:
```
# Brief Generation: {job_title} at {company}
```
To:
```
# {job_title} at {company}
```

**D-1 fix:** Add new section at end of file:
```markdown
## Completion Signal

After writing the complete brief file, append this exact line at the very end:

<!-- BRIEF COMPLETE -->

This sentinel is required. The parent orchestrator verifies brief integrity by checking for this line. If it is missing, the brief is treated as corrupt/truncated.
```

### Phase 2 Commit

```
feat(career-matching): V13 Phase 2 — named agent defs + reference templates
```

---

## PHASE 3: CLAUDE.md Rewrites

**Goal:** Rewrite presentation format, delivery workflow, OUTPUTS, CAPABILITIES, SECURITY.
**File:** `03_agents/tests/v13/CLAUDE.md` (single file, multiple sections).
**Review findings addressed:** RC1, D-1 (parent side), E-1, E-2, E-3, RC8 (CLAUDE.md side), D-3b (CLAUDE.md side), S-3, DI-9, DI-13, F-1, SIM-R9-3, ARCH-R10-1, DI-R10-1.

### Task 3.1: Rewrite presentation format (Steps 9-10)

**Location:** Lines 210-231 (PRESENTATION WORKFLOW section)

Replace hyperlink table format with reference footnote pattern. Content from original plan lines 913-936 — unchanged by review.

**Find (lines 221-231):** The standard table format and rules starting with `**Standard table format (ALL role types):**`

**Replace with:**
```
**Standard table format (ALL role types) — reference footnote pattern:**

**Results: {Role Type}** ({N} verified, {M} above threshold)

| Score | Title                      | Company       | Location         |
|-------|----------------------------|---------------|------------------|
| 92    | Founder Associate [1]      | Duku AI       | London (Remote)  |
| 87    | Growth Lead [2]            | MAGIC AI      | London           |
| 95    | Associate PMM * [3]        | Triptease     | London (Hybrid)  |

[1] https://linkedin.com/jobs/view/4344764433
[2] https://web3.career/jobs/magic-ai-growth-lead
[3] https://linkedin.com/jobs/view/4355891722

* Triptease salary £25-35K, below your £40K minimum

**Formatting rules:**
- **URLs as reference footnotes:** Each title gets `[N]` suffix. Full clickable URLs listed below table. Never inline URLs in table cells.
- **Salary/concern notes:** Mark with `*` after title. Footnote explanation below URL list. Table rows stay uniform width.
- **Score breakdown — briefs only.** Full 5-factor breakdown shown ONLY for jobs getting briefs (90+). All others show score in table.
- **Job freshness.** If `date_posted` is available and >30 days ago, present last with a note: "Posted >30 days ago — may still be active." Do not skip entirely.
- **No hyperlinks in table.** URLs are reference footnotes below, not markdown links.
```

### Task 3.2: Rewrite delivery workflow (Steps 3, 5, 11, 13-16)

**Multiple locations in CLAUDE.md:**

#### Step 1 (~line 68): Add per-run output cleanup (DI-R10-1)

**Find:** The existing Step 1 line (e.g., `1. **Read CLAUDE.md...`):

**Add BEFORE Step 1** (becomes new first instruction in the ORCHESTRATION WORKFLOW):

```
**Pre-run cleanup (new runs only):** Before starting Step 1, check if `output/session-state.md` exists and read its `run_date`. If the file does not exist OR its `run_date` differs from today's date, this is a new run — clean stale output:

    rm -f output/jobs/*
    rm -f output/verified/*/*
    rm -f output/briefs/*
    rm -f output/digests/*

Do NOT clean if `session-state.md` exists with today's `run_date` — that means this is a resume of the current run. Cleaning would destroy in-progress results.
```

**DI-R10-1 fix:** Without this, stale output files from prior runs persist. The briefs-pdf agent discovers ALL `.md` files in `output/briefs/`, so Tuesday's PDF would include Monday's briefs. The cleanup is conditioned on `session-state.md` to distinguish new runs from crash-recovery resumes.

#### Step 3 (~line 87): Remove parent template-reading instruction

**Find:** The entire Step 3 line:
```
3. **Read subagent template (HARD RULE):** Read `references/subagent-search-verify.md` in full BEFORE dispatching any subagents. Confirm you understand the workflow: jobspy first, then specialty sources, then filter, then summarize, then verify.
```

**Replace with:**
```
3. **Named agents read their own templates on startup.** Parent only needs to read `references/context.md` for user profile data. Do NOT read subagent template files — they are loaded automatically by each named agent's startup instructions.
```

**DI-13 fix:** Named agents read their own templates via the "On startup: Read references/subagent-{name}.md" instruction in each agent definition. The parent reading the template wastes context window and contradicts the named-agent architecture.

#### Step 5 (~line 103-114): Remove cd instruction, use named agent

**Find:** The entire prompt block for step 5 (lines 103-114)

**Replace with:**
```
5. **Dispatch subagent via Task tool (NAMED AGENT PATTERN).** Do NOT inline the full template. Instead:

   Task tool call:
     prompt: "{compact JSON blob}"
     description: "Search {role_type} jobs"
     subagent_type: "search-verify"

   The compact JSON blob contains ALL 13 template variables:
   {"role_type": "...", "role_type_slug": "...", "skills": "...", "experience_years": "...",
    "seniority": "...", "target_industries": "...", "salary_min": "...", "location_prefs": "...",
    "country": "...", "remote_pref": "...", "sources_for_role": "...", "run_date": "...",
    "exclude_titles": "..."}

   Named agent reads its own template on startup — keeps parent context small.
```

#### Step 11 (~lines 133-148): Remove cd instruction, use named agent

**Find:** The entire prompt block for step 11

**Replace with:**
```
11. **Dispatch brief subagents (NAMED AGENT PATTERN).** For each accepted job:

    Task tool call:
      prompt: "{compact JSON blob}"
      description: "Generate brief for {job_title} at {company}"
      subagent_type: "brief-generator"

    The compact JSON blob contains ALL 7 template variables:
    {"job_title": "...", "company": "...", "company_slug": "...", "title_slug": "...",
     "run_date": "...", "profile_extract": "...", "job_json_with_verification": "..."}

    After each brief subagent completes, verify `output/briefs/{company_slug}-{title_slug}-brief.md`:
    - File must exist
    - File's last non-whitespace line must be exactly `<!-- BRIEF COMPLETE -->`
    - If sentinel is missing, treat as corrupt/truncated. Log failure, notify user.
    - **Hang detection:** If Task tool returns but brief file does not exist, treat that specific brief as failed and continue with remaining briefs. Do not abort the entire run.
```

#### Steps 13-16 (~lines 161-206): Full rewrite for named agents + email safety

**Find:** Everything from step 13 through the "Note: Steps 13 and 14" line

**Replace with:**
```
13. **Dispatch digest-email agent (NAMED AGENT PATTERN).** After briefs generated and feedback collected.

    Task tool call:
      prompt: "{compact JSON blob}"
      description: "Generate digest email HTML"
      subagent_type: "digest-email"

    The compact JSON blob contains ALL 4 template variables:
    {"run_date": "...", "user_email": "...", "user_name": "...", "total_briefs": N}

    Variable sources: `run_date` from session, `user_email` from context.md `## Delivery`, `user_name` from context.md `## Profile`, `total_briefs` counted from output/briefs.

    Agent generates:
    - `output/digests/{run_date}-email.html` (full digest as email body)
    - `output/digests/_status.json`

    Note: If user rejected ALL jobs (zero briefs), the digest "Top Opportunities" section is omitted.

    Verify completion: Read `output/digests/_status.json`.
    - If status file exists but cannot be parsed as valid JSON, treat as failed (corrupted write).
    - If `"failed"` → notify user with the `error` message.
    - If `"complete"` → verify `html_generated` is true.
    - **Hang detection:** If Task tool returns but no status file exists, treat as failed. Log: "Agent returned without writing status file."

14. **Dispatch briefs-pdf agent (NAMED AGENT PATTERN).** If any briefs generated:

    Task tool call:
      prompt: "{compact JSON blob}"
      description: "Compile briefs into PDF"
      subagent_type: "briefs-pdf"

    The compact JSON blob contains the template variable:
    {"run_date": "..."}

    Agent generates:
    - `output/briefs/application-briefs-{run_date}.pdf`
    - `output/briefs/_status.json`

    Verify completion: Read `output/briefs/_status.json`.
    - If status file exists but cannot be parsed as valid JSON, treat as failed (corrupted write).
    - If `"failed"` → notify user with the `error` message.
    - If `"complete"` → verify `pdf_generated` is true.
    - **Hang detection:** If Task tool returns but no status file exists, treat as failed.

**Note:** Steps 13 and 14 have no mutual dependency and CAN run in parallel.

15. **Send email (PARENT-ORCHESTRATED).** Gate on Steps 13 and 14 having passed, then send.

    Pre-send gate:
    a. Check idempotency: Read `output/digests/_status.json`. If `sent_at` field exists AND `run_date` matches the current session's `run_date`, SKIP — email was already sent for this run. Tell user: "Email already sent for this run ({run_date})." If `run_date` differs (previous run's status), proceed normally — this is a new run.
    b. Three-way briefs-pdf status check:
       - **Step 14 succeeded** (`output/briefs/_status.json` exists with `"status": "complete"`): include attachment.
       - **Step 14 failed** (`output/briefs/_status.json` exists with `"status": "failed"`): notify user and ask how to proceed.
       - **Step 14 was never dispatched** (zero briefs generated, `output/briefs/_status.json` does not exist): proceed directly to email send without attachment. Do NOT treat missing status file as a failure — Step 14 is conditional on briefs existing.
    c. If digest failed → do NOT send.

    If gate passes (or user chose to send without attachment):

    ```bash
    python3 scripts/send_email.py \
      --to "{user_email}" \
      --subject "Job Search Update — {run_date}" \
      --body-file output/digests/{run_date}-email.html \
      --attachment output/briefs/application-briefs-{run_date}.pdf
    ```

    If no briefs PDF (user rejected all jobs or chose to proceed without): omit `--attachment` flag.
    If RESEND_API_KEY not set: ask user for key, write to .env.

    **AFTER successful send:** Read existing `output/digests/_status.json`, add `sent_at` and `to` fields to the existing object, write back. Preserve all existing fields written by the digest-email subagent (`status`, `html_generated`, `run_date`).
    ```json
    {
      "status": "complete",
      "html_generated": true,
      "run_date": "{run_date}",
      "sent_at": "{ISO timestamp}",
      "to": "{user_email}"
    }
    ```

    If send fails: no `sent_at` field is written. On resume, idempotency check sees no `sent_at` → retries send. Safe: if the email actually sent but the write failed, user gets a duplicate (observable, preferable to silent blocking).

    **CRITICAL:** The parent orchestrator sends email, NOT a subagent. This avoids Bash permission issues in subagents.
```

### Task 3.3: Update OUTPUTS, CAPABILITIES, SECURITY sections

#### OUTPUTS section (~lines 278-291)

**Replace with:**
```
## OUTPUTS

- Raw jobs: `output/jobs/{role_type_slug}-aggregator.json`
- Verified jobs: `output/verified/{role_type_slug}/{company_slug}-{title_slug}.json`
- Briefs: `output/briefs/{company_slug}-{title_slug}-brief.md`
- Briefs PDF: `output/briefs/application-briefs-{run_date}.pdf`
- Email HTML: `output/digests/{run_date}-email.html`
- Digest status: `output/digests/_status.json` (subagent writes `status`/`html_generated`/`run_date`; parent appends `sent_at`/`to` after successful email send)
- Briefs-PDF status: `output/briefs/_status.json`
- Session state: `output/session-state.md`
- Subagent status: `output/verified/{role_type_slug}/_status.json`

**Date rule:** All filenames use the run date captured at session start. Never hardcode a year.
```

#### CAPABILITIES section (~lines 266-275)

**Replace with:**
```
## CAPABILITIES

- Job search: `python3 scripts/jobspy_search.py` for major boards, WebFetch for specialty sources
- Filtering: `python3 scripts/filter_jobs.py` for title exclusions
- Summaries: `python3 scripts/summarize_jobs.py` for context-efficient overviews
- Web research: WebFetch for company context, career pages, hiring manager lookup
- Digest generation: named `digest-email` agent (design system enforced)
- Briefs compilation: named `briefs-pdf` agent (design system enforced)
- Email delivery: parent-orchestrated via `scripts/send_email.py`
- File operations: JSON to output/jobs/, verified JSON to output/verified/, Markdown to output/briefs/, HTML to output/digests/
```

#### SECURITY section (~lines 257-263)

**S-3 fix:** Change line 262 from:
```
- Run email script with: `source .env && python3 scripts/send_email.py`
```
To:
```
- Run email script with: `python3 scripts/send_email.py` (script auto-loads .env via Python dotenv)
```

### Phase 3 Commit

```
feat(career-matching): V13 Phase 3 — CLAUDE.md rewrites (named agents, email safety, footnotes)
```

---

## PHASE 4: send_email.py Rewrite

**Goal:** Strip send_email.py to V13-only code path (~75 lines).
**File:** `03_agents/tests/v13/scripts/send_email.py`
**Review findings addressed:** S-2, SIM-R10-1.

### Task 4.1: Rewrite send_email.py

**File:** `03_agents/tests/v13/scripts/send_email.py`

Complete rewrite. `--body-file` is now **required** (not optional).

```python
#!/usr/bin/env python3
"""Send email via Resend API with HTML body from file and optional PDF attachments."""

import argparse
import base64
import os
import sys
from pathlib import Path


def load_dotenv():
    """Load .env from parent directory if it exists.

    Note: Uses setdefault — existing shell env vars take precedence over .env values.
    """
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    value = value.strip().strip('"').strip("'")
                    os.environ.setdefault(key.strip(), value)


def main():
    load_dotenv()

    try:
        import resend
    except ImportError:
        print("Error: resend not installed. Run: pip install resend", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Send email via Resend API")
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body-file", required=True, help="Path to HTML file for email body")
    parser.add_argument("--attachment", default=None, help="Path to PDF attachment")
    args = parser.parse_args()

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("Error: RESEND_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    resend.api_key = api_key

    with open(args.body_file, encoding="utf-8") as f:
        html_body = f.read()

    params = {
        # TODO: Replace with verified custom domain for production use
        "from": "Job Search Agent <onboarding@resend.dev>",
        "to": [args.to],
        "subject": args.subject,
        "html": html_body,
    }

    if args.attachment:
        if not os.path.exists(args.attachment):
            print(f"Error: Attachment not found: {args.attachment}", file=sys.stderr)
            sys.exit(1)
        with open(args.attachment, "rb") as f:
            raw = f.read()
        content = base64.b64encode(raw).decode("utf-8")
        params["attachments"] = [{"filename": os.path.basename(args.attachment), "content": content}]

    try:
        result = resend.Emails.send(params)
        print(f"Email sent. ID: {result['id']}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

Removed vs V12: `--body`, `--file`, `--html`, `--test`, `markdown_to_html()`, HTML auto-detection, multi-attachment list machinery (SIM-R10-1: simplified to single optional string).

### Phase 4 Commit

```
feat(career-matching): V13 Phase 4 — stripped send_email.py to V13-only path
```

---

## PHASE 5: Final Verification

**Goal:** Cross-file consistency checks. Fix any issues found.
**Review findings addressed:** A-2 (Playwright check), DI-16 (_briefs-pdf-status grep), ARCH-R10-1 (verify three-way gate logic), DI-R10-1 (verify cleanup step).

> **Note (SIM-1):** Phase 5 is the sole verification phase. Per-phase verification blocks were removed — they duplicated these cross-file checks without adding value.

### Task 5.1: Full verification suite

```bash
# === 8 HIGH-VALUE CROSS-FILE CHECKS ===

# 1. No v12 path remnants (RC1)
grep -r "v12" 03_agents/tests/v13/ --include="*.md" --include="*.py" --include="*.json" | grep -v ".git"  # expect: no output

# 2. No match_reason references (D-2)
grep -r "match_reason" 03_agents/tests/v13/references/ --include="*.md"  # expect: no output

# 3. BRIEF COMPLETE sentinel in both files (D-1)
grep "BRIEF COMPLETE" 03_agents/tests/v13/references/subagent-brief-generator.md  # expect: match
grep "BRIEF COMPLETE" 03_agents/tests/v13/CLAUDE.md  # expect: match

# 4. Playwright available (A-2)
npx playwright --version  # expect: version string

# 5. No stale _briefs-pdf-status.json references (DI-16)
grep -r "_briefs-pdf-status" 03_agents/tests/v13/ --include="*.md" --include="*.json"  # expect: no output

# 6. Three-way briefs-pdf gate in CLAUDE.md (ARCH-R10-1)
grep "was never dispatched" 03_agents/tests/v13/CLAUDE.md  # expect: match (zero-briefs path)

# 7. Per-run cleanup step in CLAUDE.md (DI-R10-1)
grep "Pre-run cleanup" 03_agents/tests/v13/CLAUDE.md  # expect: match (cleanup instruction)

# 8. No action="append" in send_email.py (SIM-R10-1)
grep "action=\"append\"" 03_agents/tests/v13/scripts/send_email.py  # expect: no output
```

### Task 5.2: Fix any issues found

If any check fails, fix and re-verify.

### Phase 5 Commit (only if fixes needed)

```
fix(career-matching): V13 Phase 5 — final verification fixes
```


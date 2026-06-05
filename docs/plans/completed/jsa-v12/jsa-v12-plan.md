# JSA V12 Implementation Plan (Post-Review)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create V12 of the career-matching with 13 incremental improvements over V11.

**Architecture:** Copy V11 to `03_agents/tests/v12/`, apply 10 CLAUDE.md changes, 1 search-template update, 2 new subagent templates. All prompt/template engineering — no new Python code.

**Tech Stack:** Markdown templates, JSON schemas, Python scripts (copied unchanged), pdfkit for PDF generation.

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `03_agents/tests/v12/` | Create dirs | Full directory tree |
| `03_agents/tests/v12/CLAUDE.md` | Create (from V11 + 10 changes) | Parent orchestrator |
| `03_agents/tests/v12/references/subagent-search-verify.md` | Create (from V11 + schema alignment) | Search template |
| `03_agents/tests/v12/references/subagent-brief.md` | Create (copy V11, update paths) | Brief template |
| `03_agents/tests/v12/references/subagent-digest.md` | Create (new) | Digest + PDF + email |
| `03_agents/tests/v12/references/subagent-briefs-pdf.md` | Create (new) | Briefs compilation PDF |
| `03_agents/tests/v12/context.md` | Create (from V11, reset progress) | User profile |
| `03_agents/tests/v12/references/algorithms.md` | Copy unchanged | Scoring rules |
| `03_agents/tests/v12/references/templates.md` | Copy unchanged | Output format specs |
| `03_agents/tests/v12/references/sources.md` | Copy unchanged | Job source configs |
| `03_agents/tests/v12/scripts/*.py` | Copy 4 of 5 (NOT create_briefs_pdf.py) | Python utilities |
| `03_agents/tests/v12/tests/*` | Copy unchanged | Unit tests |
| `03_agents/tests/v12/.gitignore` | Create (from V11 + PDF exclusions) | Git ignore |
| `03_agents/tests/v12/.env.example` | Copy unchanged | Env template |
| `03_agents/tests/v12/.claude/settings.local.json` | Create (clean) | Minimal permissions |

---

## Implementation Steps

### Task 1: Create V12 Directory Structure

**Step 1.1: Create directories**
```bash
mkdir -p 03_agents/tests/v12/{references,scripts,tests,output/{jobs,verified,briefs,digests},.claude}
```

**Step 1.2: Create .gitkeep files**

Create empty `.gitkeep` files in:
- `03_agents/tests/v12/output/jobs/.gitkeep`
- `03_agents/tests/v12/output/verified/.gitkeep`
- `03_agents/tests/v12/output/briefs/.gitkeep`
- `03_agents/tests/v12/output/digests/.gitkeep`

**Verify:** `find 03_agents/tests/v12/ -type d | sort` shows complete tree.

---

### Task 2: Copy Unchanged Files from V11

**Step 2.1: Copy reference docs (3 files)**
```bash
cp 03_agents/tests/v11/references/algorithms.md 03_agents/tests/v12/references/
cp 03_agents/tests/v11/references/templates.md 03_agents/tests/v12/references/
cp 03_agents/tests/v11/references/sources.md 03_agents/tests/v12/references/
```

**Step 2.2: Copy Python scripts (4 of 5 — NOT create_briefs_pdf.py)**
```bash
cp 03_agents/tests/v11/scripts/jobspy_search.py 03_agents/tests/v12/scripts/
cp 03_agents/tests/v11/scripts/filter_jobs.py 03_agents/tests/v12/scripts/
cp 03_agents/tests/v11/scripts/summarize_jobs.py 03_agents/tests/v12/scripts/
cp 03_agents/tests/v11/scripts/send_email.py 03_agents/tests/v12/scripts/
```
Do NOT copy `create_briefs_pdf.py` — it is replaced by `subagent-briefs-pdf.md` and contains hardcoded V11 values.

**Step 2.3: Copy test files**
```bash
cp 03_agents/tests/v11/tests/__init__.py 03_agents/tests/v12/tests/
cp 03_agents/tests/v11/tests/test_*.py 03_agents/tests/v12/tests/
```

**Step 2.4: Copy .env.example**
```bash
cp 03_agents/tests/v11/.env.example 03_agents/tests/v12/
```

**Step 2.5: Create .gitignore with PDF exclusions**

Write `03_agents/tests/v12/.gitignore`:
```
.env
output/jobs/*.json
__pycache__/
output/briefs/*.pdf
output/digests/*.pdf
```

**Verify:** `ls 03_agents/tests/v12/scripts/` shows 4 files (no create_briefs_pdf.py). `cat 03_agents/tests/v12/.gitignore` shows 5 lines including PDF exclusions.

---

### Task 3: Create V12 CLAUDE.md (10 Changes)

**Source:** `03_agents/tests/v11/CLAUDE.md` (194 lines)
**Target:** `03_agents/tests/v12/CLAUDE.md`

Write the complete V12 CLAUDE.md applying all changes below. Write as one complete file.

**Change 1 — Core Rule 6:** Replace:
```
6. **MUST batch work within context limits.** Dispatch search+verify to subagents (one per role type). Dispatch brief generation to separate subagents. Checkpoint after every 2 role types.
```
With:
```
6. **MUST batch work within context limits.** Dispatch search+verify to subagents (one per role type). Dispatch brief generation, digest, and briefs-PDF to separate subagents. Checkpoint after every 3 role types.
```

**Change 2 — Orchestration step 3 (template read HARD RULE):** Replace:
```
3. **Read subagent template:** Read `references/subagent-search-verify.md`
```
With:
```
3. **Read subagent template (HARD RULE):** Read `references/subagent-search-verify.md` in full BEFORE dispatching any subagents. Confirm you understand the workflow: jobspy first, then specialty sources, then filter, then summarize, then verify.
```

**Change 3 — Orchestration step 5 (compact dispatch):** Replace lines 103-112 (the inline dispatch) with:
```
5. **Dispatch subagent via Task tool (COMPACT PATTERN).** Do NOT inline the full template. Instead:

   Task tool call:
     prompt: "You are a search+verify subagent. Read your full instructions from
              `references/subagent-search-verify.md`. Your variables: {compact JSON blob}.
              cd to `03_agents/tests/v12/`, read the template, fill in variables, execute.
              Before executing, confirm 13 variables parsed from the JSON blob.
              If any variable is missing or null, write `_status.json` with
              `\"status\": \"failed\", \"error\": \"Missing variable: {name}\"` and exit.
              Do NOT proceed with partial variables."
     description: "Search {role_type} jobs"
     subagent_type: "general-purpose"

   The compact JSON blob contains ALL 13 template variables:
   {"role_type": "...", "role_type_slug": "...", "skills": "...", "experience_years": "...",
    "seniority": "...", "target_industries": "...", "salary_min": "...", "location_prefs": "...",
    "country": "...", "remote_pref": "...", "sources_for_role": "...", "run_date": "...",
    "exclude_titles": "..."}

   Saves ~60% parent context per dispatch vs inlining the full template.
```

**Change 4 — New step 8 (cross-role dedup):** Insert between batch completion and presentation:
```
8. **Cross-role-type deduplication (MANDATORY before presentation).**
   - Scan all `output/verified/*/` directories (skip files starting with `_`)
   - If same company+title filename exists in multiple role types, read ONLY those duplicate files to compare scores
   - Keep highest-scoring copy, delete duplicates
   - Log dedup actions in session-state.md
```
Renumber old steps 8→9, 9→10, 10→11, 11→12.

**Change 5 — Replace PRESENTATION WORKFLOW:** Replace the entire PRESENTATION WORKFLOW section with:
```
## PRESENTATION WORKFLOW

Before presenting ANY role type's results:
1. All jobs for that role type are verified
2. Cross-role-type deduplication completed
3. Jobs ranked by score, highest first

**Minimum score threshold: 70.** Only present jobs scoring 70+. Below 70 = not shown, logged in session-state.md.

**Empty results fallback:** If a role type has zero jobs above 70, present top 3 regardless of score with a note: "No strong matches found. Here are the closest."

**Standard table format (ALL role types):**
| Score | Title | Company | Location |
|-------|-------|---------|----------|
| 85 | [Title](job_url) | Company | London (Remote) |

**Score breakdown — briefs only.** Full 5-factor breakdown shown ONLY for jobs getting briefs (90+). All others show score in table.

**Job freshness.** If `date_posted` is available and >30 days ago, present last with a note: "Posted >30 days ago — may still be active." Do not skip entirely.

**All titles hyperlinked.** Every job title MUST be `[Title](job_url)` using the actual `job_url` from verified JSON.
```

**Change 6 — Update checkpoint step (renumbered to 12):**
```
12. **Checkpoint after every 3 role types (HARD RULE).** After batch 1 completes, IMMEDIATELY write session-state.md before launching batch 2. Not a suggestion — a hard rule.
```

**Change 7 — SESSION MANAGEMENT update (NOT a new section):** Replace the SESSION MANAGEMENT section with:
```
## SESSION MANAGEMENT

Write progress to session-state.md after completing each role type. On startup, if session-state.md exists, read it and resume where you left off. Tell user: "Progress saved. Say 'continue' to resume."

After presenting results, do NOT re-read verified files. Reference only session-state.md.
```
Do NOT create a separate CONTEXT CONSERVATION section.

**Status file handling:** Subagent `_status.json` files are overwritten on each run. No explicit cleanup of stale status files is needed on startup.

**Change 8 — Update SECURITY section:** Replace first bullet with:
```
- **API key onboarding:** On first run, .env will NOT contain RESEND_API_KEY. When email is needed, check if set. If not, ask user: "I need a Resend API key to send your digest. Get one at resend.com/api-keys. What's your key?" Write to .env silently.
```

**Change 9 — Rewrite step 10 + add steps 13-14:**

Rewrite step 11 (brief dispatch, renumbered from V11 step 10) to use compact pattern:

    **Brief variable preparation (retain from V11 step 10):**
    Before dispatching each brief subagent, prepare the 7 variables:
    - `{job_title}` = title from verified JSON
    - `{company}` = company from verified JSON
    - `{company_slug}` = slugified company name (lowercase, hyphens)
    - `{title_slug}` = slugified title (lowercase, hyphens)
    - `{run_date}` = current run date
    - `{profile_extract}` = copy from context.md sections: `## Profile`, `## Skills`, `## Experience`
    - `{job_json_with_verification}` = complete contents of the verified JSON file

```
11. **Dispatch brief subagents (COMPACT PATTERN).** For each accepted job:

    Task tool call:
      prompt: "You are a brief-generation subagent. Read your full instructions from
               `references/subagent-brief.md`. Your variables: {compact JSON blob}.
               cd to `03_agents/tests/v12/`, read the template, fill in variables, execute.
               Before executing, confirm 7 variables parsed from the JSON blob.
               If any variable is missing, exit without writing any output files."
      description: "Generate brief for {job_title} at {company}"
      subagent_type: "general-purpose"

    The compact JSON blob contains ALL template variables:
    {"job_title": "...", "company": "...", "company_slug": "...", "title_slug": "...",
     "run_date": "...", "profile_extract": "...", "job_json_with_verification": "..."}

    After each brief subagent completes, verify `output/briefs/{company_slug}-{title_slug}-brief.md` exists and is non-empty.
```

Add steps 13-14:
```
13. **Dispatch digest subagent (COMPACT PATTERN).** After briefs generated and feedback collected. Note: if user rejected ALL jobs (zero briefs), the digest "Top Opportunities" section will be empty — template handles this gracefully by omitting that section when `{total_briefs}` is 0.

    Task tool call:
      prompt: "You are a digest-generation subagent. Read your full instructions from
               `references/subagent-digest.md`. Your variables: {compact JSON blob}.
               cd to `03_agents/tests/v12/`, read the template, fill in variables, execute.
               Before executing, confirm 5 variables parsed from the JSON blob.
               If any variable is missing or null, write `output/digests/_status.json` with
               `\"status\": \"failed\", \"error\": \"Missing variable: {name}\"` and exit.
               Do NOT proceed with partial variables."
      description: "Generate digest and send email"
      subagent_type: "general-purpose"

    The compact JSON blob contains ALL 5 template variables:
    {"run_date": "...", "user_email": "...", "user_name": "...",
     "total_verified": N, "total_briefs": N}

    Variable sources: `run_date` from session, `user_email` from context.md `## Delivery`, `user_name` from context.md `## Profile`, `total_verified` counted from output/verified, `total_briefs` counted from output/briefs.

    Verify completion: Read `output/digests/_status.json`.
    Read `status` field first:
    - If `"failed"` → notify user with the `error` message. Do NOT proceed as if successful.
    - If `"partial"` → PDF generated but email failed. Notify user: "Digest PDF saved to output/digests/{run_date}.pdf but email send failed. Check .env for RESEND_API_KEY." Offer to retry email only.
    - If `"complete"` → verify specific fields (`pdf_generated`, `email_sent`, etc.).

14. **Dispatch briefs-PDF subagent (COMPACT PATTERN).** If any briefs generated:

    Task tool call:
      prompt: "You are a briefs-PDF subagent. Read your full instructions from
               `references/subagent-briefs-pdf.md`. Your variables: {compact JSON blob}.
               cd to `03_agents/tests/v12/`, read the template, fill in variables, execute.
               Before executing, confirm 1 variable parsed from the JSON blob.
               If the variable is missing or null, write `output/briefs/_briefs-pdf-status.json` with
               `\"status\": \"failed\", \"error\": \"Missing variable: run_date\"` and exit."
      description: "Compile briefs into PDF"
      subagent_type: "general-purpose"

    The compact JSON blob contains the template variable:
    {"run_date": "..."}

    Verify completion: Read `output/briefs/_briefs-pdf-status.json`.
    Read `status` field first:
    - If `"failed"` → notify user with the `error` message. Do NOT proceed as if successful.
    - If `"complete"` → verify specific fields (`pdf_generated`, etc.).

**Note:** Steps 13 and 14 have no mutual dependency and CAN run in parallel.
```

**Change 10 — Update OUTPUTS section:** Add:
```
- Briefs PDF: `output/briefs/application-briefs-{run_date}.pdf`
- Digest PDF: `output/digests/{run_date}.pdf`
- Digest status: `output/digests/_status.json`
- Briefs-PDF status: `output/briefs/_briefs-pdf-status.json`
```
Update CAPABILITIES to mention "Digest generation: subagent with frontend-design skill" and "Briefs compilation: subagent with frontend-design skill".

**Verify:** Deferred to Task 10 (single verification pass for all files).

---

### Task 4: Create Modified subagent-search-verify.md

**Source:** `03_agents/tests/v11/references/subagent-search-verify.md` (178 lines)
**Target:** `03_agents/tests/v12/references/subagent-search-verify.md`

**Step 4.1: Copy and update all path references**
- Line 9: `03_agents/tests/v11/` → `03_agents/tests/v12/`
- Line 11: `03_agents/tests/v11/` → `03_agents/tests/v12/`

**Step 4.2: Add freshness recording to Step 1 (CONFIRM ACTIVE)**

After the existing WebFetch/fallback logic (lines 58-64), insert:
```
**Job freshness (during verification):**
- Record `date_posted` from listing or aggregator data if available
- If `date_posted` is unavailable, leave field as null — do not fabricate
- Freshness does NOT affect verification — verify all promising candidates regardless of age
- Parent orchestrator handles deprioritization at presentation time
```

**Step 4.3: Align verified JSON schema to match actual output**

Replace the entire JSON schema in Step 5: WRITE with the actual schema that V11 subagents produce:
```json
{
  "title": "exact title from listing",
  "company": "exact name from website",
  "location": "from listing",
  "job_type": "Full-time",
  "work_arrangement": "Remote / Hybrid / In-person",
  "salary_min": null,
  "salary_max": null,
  "currency": null,
  "job_url": "extracted from page",
  "source": "source name",
  "date_posted": "2026-01-20 or null if unavailable",
  "active_status": "confirmed / unverified",
  "industry": "job industry",
  "requirements_met": ["requirement: evidence from user profile"],
  "gaps": ["gap description"],
  "preferred_met": ["preferred skill or qualification met"],
  "score": 85,  // MUST be a top-level integer. Never a nested object like {"total": 85, ...}
  "score_breakdown": {
    "required_skills": {
      "matched": 4,
      "total": 5,
      "points": 32,
      "calculation": "40 * (4/5) = 32"
    },
    "preferred_skills": {
      "matched": 2,
      "total": 3,
      "points": 13,
      "calculation": "20 * (2/3) = 13.3"
    },
    "experience_fit": {
      "points": 15,
      "calculation": "description of fit"
    },
    "industry_match": {
      "points": 15,
      "calculation": "description of match"
    },
    "location_match": {
      "points": 10,
      "calculation": "description of match"
    },
    "total": 85
  },
  "benefits": [],
  "notes": "optional — additional context about this job, omit if none",
  "run_date": "{run_date}",
  "verified_at": "{run_date}"
}
```

This replaces the old schema that used `url` (now `job_url`), `remote: true` (now `work_arrangement`), `discovered_at` (now `date_posted`), and the nested `verification` wrapper (now flat top-level fields).

**Verify:** `grep "v11"` returns 0. `grep "job_url"` returns hits. `grep "date_posted"` returns hits. `grep "freshness_flag"` returns 0. `grep "posted_date"` returns 0 (uses `date_posted`). `grep "\"url\":"` returns 0 (now `job_url`). `grep "discovered_at"` returns 0.

---

### Task 5: Create subagent-brief.md (path update + field rename)

**Source:** `03_agents/tests/v11/references/subagent-brief.md` (109 lines)
**Target:** `03_agents/tests/v12/references/subagent-brief.md`

Copy and apply three changes:
- Line 9: `03_agents/tests/v11/` → `03_agents/tests/v12/`
- Line 11: `03_agents/tests/v11/` → `03_agents/tests/v12/`
- Line 51: `Location: {location} | Remote: {remote}` → `Location: {location} | Arrangement: {work_arrangement}`

**Note:** V12 schema changed from nested (`verification.score`) to flat top-level fields (`score`, `score_breakdown`, etc.). The brief subagent receives full JSON via `{job_json_with_verification}`. Extract `score` from the top-level `score` field (integer). Extract breakdown from `score_breakdown` (top-level object). Do NOT look inside a `verification` wrapper.

**Verify:** `grep "v11"` returns 0. `grep "work_arrangement"` returns 1+ hit. `grep "Remote: {remote}"` returns 0.

---

### Task 6: Create NEW subagent-digest.md

**Target:** `03_agents/tests/v12/references/subagent-digest.md`

Create entirely new file following the standard template structure (matching subagent-search-verify.md and subagent-brief.md patterns):

```markdown
# Digest Generation: {run_date}

## Your Task

Generate a professional PDF digest of all verified jobs, then email it to the user. Write digest to `output/digests/{run_date}.pdf` and send via email.

Do NOT interact with the user. Generate files, send email, and exit.

**Working directory:** All paths in this template are relative to `03_agents/tests/v12/`.

**First action:** `cd 03_agents/tests/v12/`

## Variables

- `{run_date}` — date for filenames and records
- `{user_email}` — recipient email address
- `{user_name}` — user's name for email greeting
- `{total_verified}` — total verified jobs across all role types
- `{total_briefs}` — total briefs generated

## Core Rules

1. **ALL job titles MUST be hyperlinked** to their application URLs using `job_url` from verified JSON. Not just brief jobs — ALL titles.
2. **NEVER fabricate data.** Use only data from verified JSON files.
3. **Clean up intermediates.** Delete .md and .html files after PDF generation. Keep only .pdf.

## Pre-checks (BEFORE any work)

1. Run `which wkhtmltopdf` — must find the binary. If not found, write `output/digests/_status.json` with `"error": "wkhtmltopdf not installed"` and exit.
2. Run `pip3 install pdfkit` — ensure pdfkit is available.
3. Run `pip3 install markdown` — required by `send_email.py` for HTML conversion. Without it, email falls back to `<pre>` wrapping (poorly formatted).
4. If any check fails, write `output/digests/_status.json` with error details and exit.

## Workflow

### Step 1: Read all verified JSON

- Read all files in `output/verified/*/` (skip files starting with `_`)
- Group jobs by role type (directory name)
- Extract: title, company, location, work_arrangement, score, job_url, date_posted

### Step 2: Read brief filenames

- Read `output/briefs/` to identify which jobs have briefs
- Match by company-title slug pattern

### Step 3: Generate markdown digest

Write to `output/digests/{run_date}.md`:

- **Summary section:** {user_name}'s Job Search Update — {run_date}. {total_verified} verified jobs, {total_briefs} application briefs.
- **Top Opportunities section:** Briefs-ready jobs (score 90+) with full details. Each title hyperlinked.
- **All Verified Jobs section:** Tables per role type, ALL titles hyperlinked as `[Title](job_url)`:

| Score | Title | Company | Location |
|-------|-------|---------|----------|
| 85 | [Title](job_url) | Company | London (Remote) |

- **Statistics section:** Jobs per role type, score distribution, sources used.

### Step 4: Convert to PDF

Use frontend-design skill to create HTML, then convert to PDF via pdfkit.

**Design constraints:**
- Typography: sans-serif, 16px body, 14px tables
- Colors: #ffffff background, #1a1a1a text, max-width 800px
- Score colors: 90+ green (#16a34a), 80-89 default, 70-79 amber (#d97706)
- Print-optimized: proper margins (40px+), no dark themes, no decorative elements

Save to `output/digests/{run_date}.pdf`.

> **Note:** The PDF (Step 4) and email body (Step 5) are separate outputs. The email body is markdown, NOT the HTML from Step 4. `send_email.py` handles markdown→HTML conversion.

### Step 5: Compose and send email

Write markdown summary to temp file, then send via `send_email.py` (which converts markdown to HTML):

1. Write concise markdown summary to `output/digests/_email-body.md`:
   - Greeting with {user_name}
   - Top 3-5 matches with scores and hyperlinked titles (markdown links)
   - Brief stats (total verified, total briefs)
   - "Full digest attached as PDF"
2. Send email:
   ```bash
   source .env && python3 scripts/send_email.py --to "{user_email}" --subject "Job Search Update — {run_date}" --html --file output/digests/_email-body.md --attachment output/digests/{run_date}.pdf
   ```

### Completion Signal

After Step 5, write `output/digests/_status.json`:

```json
{
  "status": "complete",
  "pdf_generated": true,
  "email_sent": true,
  "total_jobs_in_digest": 48,
  "run_date": "{run_date}"
}
```

Set `"status"` to:
- `"complete"` — PDF generated and email sent
- `"partial"` — PDF generated but email failed
- `"failed"` — PDF generation failed

### Step 6: Clean up (conditional)

- Read `output/digests/_status.json`
- ONLY IF `status` is `"complete"`: delete intermediate files (`output/digests/{run_date}.md`, `output/digests/_email-body.md`)
- If status is `"partial"` or `"failed"`, keep ALL intermediates for debugging
- Always keep: `output/digests/{run_date}.pdf` and `output/digests/_status.json`

**Verify:** File has "Your Task", "Working directory", "First action", "Core Rules", "Completion Signal" sections. Has `_status.json` output. Has pdfkit/wkhtmltopdf pre-check. Uses `--file` for email body. Mentions `send_email.py`. Mentions `frontend-design`. Hyperlink rule explicit.

---

### Task 7: Create NEW subagent-briefs-pdf.md

**Target:** `03_agents/tests/v12/references/subagent-briefs-pdf.md`

Create entirely new file following the standard template structure:

```markdown
# Briefs PDF Compilation: {run_date}

## Your Task

Compile all application briefs into a single professional PDF with cover page and table of contents. Write to `output/briefs/application-briefs-{run_date}.pdf`.

Do NOT interact with the user. Generate the PDF and exit.

**Working directory:** All paths in this template are relative to `03_agents/tests/v12/`.

**First action:** `cd 03_agents/tests/v12/`

## Variables

- `{run_date}` — date for filenames

## Core Rules

1. **NEVER fabricate data.** Use only data from brief .md files.
2. **Each brief gets its own page** — use `page-break-before: always` CSS.
3. **Clean up intermediates.** Delete .html files. Keep .md sources and .pdf output.

## Pre-checks (BEFORE any work)

1. Run `which wkhtmltopdf` — must find the binary. If not found, write `output/briefs/_briefs-pdf-status.json` with `"error": "wkhtmltopdf not installed"` and exit.
2. Run `pip3 install pdfkit` — ensure pdfkit is available.
3. If either check fails, write `output/briefs/_briefs-pdf-status.json` with error details and exit.

## Workflow

### Step 1: Read all brief files

- Read all `.md` files in `output/briefs/` (skip `.pdf` files and files starting with `_`)
- Extract title and company from each brief for table of contents
- Sort alphabetically by company name

### Step 2: Generate combined HTML

- **Cover page:** "Application Briefs — {run_date}", total briefs count
- **Table of contents:** Each brief listed with company and title
- **Brief pages:** Each brief as its own page with `page-break-before: always`

**Design constraints (same as digest):**
- Typography: sans-serif, 16px body, 14px tables
- Colors: #ffffff background, #1a1a1a text, max-width 800px
- Score colors: match green (#16a34a), gap red (#dc2626), stretch amber (#d97706)
- Print-optimized: proper margins (40px+), no dark themes

### Step 3: Convert to PDF

Convert HTML to PDF via pdfkit. Save to `output/briefs/application-briefs-{run_date}.pdf`.

## Completion Signal

After Step 3, write `output/briefs/_briefs-pdf-status.json`:

```json
{
  "status": "complete",
  "pdf_generated": true,
  "briefs_compiled": 5,
  "run_date": "{run_date}"
}
```

Set `"status"` to:
- `"complete"` — PDF generated successfully
- `"failed"` — PDF generation failed

### Step 4: Clean up (conditional)

- Read `output/briefs/_briefs-pdf-status.json`
- ONLY IF `pdf_generated: true`: delete intermediate `.html` files
- If PDF generation failed, keep `.html` source for debugging
- Always keep: `.md` sources, `.pdf` output, and `_briefs-pdf-status.json`
```

**Verify:** File has "Your Task", "Working directory", "First action", "Core Rules", "Completion Signal" sections. Has `_briefs-pdf-status.json` output. Has pdfkit/wkhtmltopdf pre-check. Outputs to `application-briefs-{run_date}.pdf`. Has page-break CSS. Step 4 cleanup is conditional on PDF success.

---

### Task 8: Create context.md (reset progress)

**Source:** `03_agents/tests/v11/context.md` (100 lines)
**Target:** `03_agents/tests/v12/context.md`

Copy from V11. Reset the `## Search Progress` table — all 7 role types set to "not started" with empty Source/Jobs Found/Verified/Date columns:

```markdown
| Role Type | Status | Source(s) | Jobs Found | Verified | Date |
|-----------|--------|-----------|------------|----------|------|
| Marketing Manager | not started | | | | |
| Marketing Associate | not started | | | | |
| Community Manager | not started | | | | |
| Community Associate | not started | | | | |
| Founder's Associate | not started | | | | |
| Product Marketing Associate | not started | | | | |
| Growth Marketing Associate | not started | | | | |
```

**Verify:** All 7 role types show "not started". `grep "v11"` returns 0.

---

### Task 9: Create .claude/settings.local.json (clean)

**Target:** `03_agents/tests/v12/.claude/settings.local.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(pip install:*)",
      "Bash(pip3 install:*)",
      "Bash(source .env)",
      "WebSearch",
      "WebFetch"
    ]
  }
}
```

Start clean (V11 had 79 accumulated permissions). Let permissions grow during test run.

---

### Task 10: Final Verification

**Step 10.1: Verify file tree**
```bash
find 03_agents/tests/v12/ -type f | sort
```
Expected: 22 files (1 fewer than original plan — no create_briefs_pdf.py).

**Step 10.2: Verify no V11 path references**
```bash
grep -r "v11" 03_agents/tests/v12/
```
Expected: 0 matches.

**Step 10.3: Verify all changes present**

**Positive checks (must find):**

| # | What | File | Command | Expected |
|---|------|------|---------|----------|
| 1 | No v11 references | all | `grep -r "v11" 03_agents/tests/v12/` | 0 hits |
| 2 | COMPACT PATTERN | CLAUDE.md | `grep "COMPACT PATTERN"` | 4 hits |
| 3 | HARD RULE | CLAUDE.md | `grep "HARD RULE"` | 2 hits |
| 4 | Schema fields | subagent-search-verify.md | `grep "job_url"` | 1+ hits |
| 5 | New templates exist | references/ | `ls subagent-digest.md subagent-briefs-pdf.md` | both found |
| 6 | No create_briefs_pdf.py | scripts/ | `ls scripts/create_briefs_pdf.py` | not found |

**Step 10.4: Commit**
```bash
git add 03_agents/tests/v12/
git commit -m "feat(career-matching): V12 implementation — 13 improvements, 15 review refinements"
```

---


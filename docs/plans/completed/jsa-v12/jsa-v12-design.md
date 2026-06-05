# Design: JSA V12 — Incremental Improvements

## Context

V11 works remarkably well — 48 verified jobs, 5 briefs, digest emailed, all 7 role types completed in one session. V12 is incremental: fix 8 known issues, add PDF digest, improve context efficiency. No architectural changes.

**Key user priorities:**
- Keep it simple (V11's simplicity is a strength)
- Professional PDF output for digest and briefs (frontend-design skill)
- Better context management (target <40% at batch 2)
- Higher quality filtering (freshness, score threshold)

---

## Chosen Approach

Keep the subagent-via-Task-tool template architecture. Optimize dispatch pattern (compact JSON + self-reading templates). Add two new subagent templates: digest generation and briefs PDF compilation. Use frontend-design skill for all PDF output (matching competitor-intel pattern).

---

## Changes (13 total)

### CLAUDE.md Parent Orchestrator (10 changes)

**1. Read template before dispatching (fixes analysis #1, #6)**
Strengthen orchestration step 3: agent MUST read the full subagent-search-verify.md template and confirm it understands the workflow (jobspy_search.py first, then specialty sources, then filter, then summarize) before dispatching ANY subagents.

**2. Compact dispatch pattern (fixes analysis #8 — context)**
Instead of inlining the full 178-line template into the Task prompt, dispatch with:
- Instruction: "Read your instructions from `references/subagent-search-verify.md`"
- Variables: compact JSON blob with all 12 template variables
- Subagent reads its own template file, fills variables, executes

Saves ~60% parent context per subagent dispatch.

**3. Cross-role-type deduplication (fixes analysis #3)**
Add mandatory step between "all batches complete" and "present results": scan all `output/verified/*/` directories, if same company+title filename exists in multiple role types, keep highest-scoring copy, delete duplicates.

**4. Standard presentation format (fixes analysis #4)**
All role types presented as markdown tables: Score | Title | Company | Location. Consistent across every role type, no more mixing flat lists and tables.

**5. Score breakdown — briefs only (fixes analysis #2, per user comment)**
Full 5-factor score breakdown shown ONLY for jobs that will get briefs. All other jobs show average score in the table. This reduces presentation noise.

**6. Minimum score threshold: 70 (fixes analysis #5)**
Only present jobs scoring 70 or above. Below 70 = not shown. This matches ~30% callback rate threshold — realistic chance of getting the role.

**7. Job freshness filter (new, per user comment on stale jobs)**
- Skip jobs posted >30 days ago (don't present or verify)
- Flag jobs 14-30 days old: "Apply soon — posted X days ago"
- Add `posted_date` field to verified JSON schema

**8. Checkpoint every 3 role types (fixes analysis #7, per user comment)**
Matches batch size. After batch 1 completes (3 role types), immediately write session-state.md before launching batch 2. Hard rule.

**9. Context conservation rules (fixes analysis #8)**
- After presenting a role type's results, do NOT re-read verified files
- Reference only session-state.md summaries for completed role types
- Dispatch digest and briefs-PDF as subagents (see below)

**10. All digest titles hyperlinked (per user comment)**
ALL job titles in the digest MUST be hyperlinked to their application URLs — not just the ones with briefs.

### New Subagent Templates (2 new files)

**11. `references/subagent-digest.md` — Digest generation + delivery**

This subagent:
1. Reads all verified JSON from `output/verified/*/`
2. Reads brief filenames from `output/briefs/` (to identify which jobs have briefs)
3. Generates markdown digest with ALL job titles hyperlinked
4. Uses frontend-design skill to convert markdown → professional HTML
5. Converts HTML → PDF
6. Composes a clean HTML summary email (separate from digest)
7. Sends email via `send_email.py` with HTML summary body + PDF attachment
8. Deletes intermediate .md and .html files, keeps only .pdf

Design constraints (matching competitor-intel):
- Clean sans-serif typography, 16px body, 14px tables
- Light background (#ffffff), high contrast text (#1a1a1a)
- Single column, max-width 800px, generous whitespace
- Full-width tables with clear borders
- Print-optimized (no dark backgrounds)
- "Looks like a clean internal strategy doc, not a dashboard"

Variables from parent: `{run_date}`, `{user_email}`, `{user_name}`, `{total_verified}`, `{total_briefs}`

**12. `references/subagent-briefs-pdf.md` — Briefs compilation to PDF**

This subagent:
1. Reads all brief .md files from `output/briefs/`
2. Combines into a single document with cover page and table of contents
3. Uses frontend-design skill → HTML → PDF
4. Saves to `output/briefs/application-briefs-{run_date}.pdf`
5. Deletes intermediate files

Same design constraints as digest. Replaces the hardcoded `create_briefs_pdf.py` script.

### Template Update (1 change)

**13. `references/subagent-search-verify.md` — Job freshness check**

Add to verification Step 1 (CONFIRM ACTIVE):
- Extract posted date from listing if available
- If >30 days old → skip (don't verify, mark as "too old")
- If 14-30 days old → verify but add `freshness_flag: "apply_soon"` to JSON
- If <14 days or unknown → verify normally

Add `posted_date` and `freshness_flag` fields to verified JSON schema.

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `03_agents/tests/v12/CLAUDE.md` | Create (copy v11, apply 10 changes) | Parent orchestrator with all fixes |
| `03_agents/tests/v12/references/subagent-search-verify.md` | Create (copy v11, add freshness) | Search template with posted_date |
| `03_agents/tests/v12/references/subagent-brief.md` | Create (copy v11 unchanged) | Brief template (no changes needed) |
| `03_agents/tests/v12/references/subagent-digest.md` | Create (new) | Digest generation + PDF + email |
| `03_agents/tests/v12/references/subagent-briefs-pdf.md` | Create (new) | Briefs compilation to PDF |
| `03_agents/tests/v12/context.md` | Create (copy v11) | User profile template |
| `03_agents/tests/v12/scripts/*` | Create (copy v11 scripts) | Python utilities (unchanged) |
| `03_agents/tests/v12/output/` | Create (empty dirs) | Output directory structure |

---

## What Does NOT Change

- Subagent architecture (Task tool + templates)
- `subagent-brief.md` template (works perfectly)
- Python scripts (jobspy_search.py, filter_jobs.py, summarize_jobs.py, send_email.py)
- Onboarding flow
- Scoring rubric (40/20/15/15/10 weights)
- Source discovery approach
- File naming conventions

---

## API Key Handling (per user comment)

For V12 test runs: do NOT pre-save RESEND_API_KEY in .env. Let the agent experience the onboarding flow where it asks the user for the key. Add a note in CLAUDE.md Security section.

---

## Success Criteria

1. All 8 V11 analysis issues resolved (no regressions)
2. Context usage <40% at batch 2 dispatch (compact dispatch + progressive offloading)
3. Professional PDF digest emailed with all titles hyperlinked
4. Professional PDF briefs compilation generated
5. No jobs >30 days old presented
6. No jobs scoring <70 presented
7. Consistent table format across all role types
8. Session completes with room for follow-up questions

## Verification Plan

1. Run V12 with all 7 role types from V11 profile
2. Check context usage at batch 2 dispatch (target <40%)
3. Verify cross-role dedup ran (no duplicate jobs across role types)
4. Verify presentation format is consistent tables
5. Verify no jobs <70 score shown
6. Verify no jobs >30 days old shown
7. Check digest PDF: all titles hyperlinked, clean design
8. Check briefs PDF: all briefs compiled, clean design
9. Check email: HTML summary + PDF attachment received
10. Verify session completes without context exhaustion

---

## Risks

| Risk | Mitigation |
|------|------------|
| frontend-design skill may not produce perfect PDF on first try | Validation loop in subagent: check PDF, fix HTML, regenerate |
| Compact dispatch may confuse subagent (reading own template) | Template is self-contained with clear variable markers |
| pdfkit/wkhtmltopdf may not be installed | Add installation check at start of digest subagent |
| 70 threshold may filter too aggressively for niche roles | User can adjust after first run; threshold is in CLAUDE.md |

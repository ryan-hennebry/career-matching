# Design: Job Search Agent V11

## Context

V10 fixed V9's structural issues (universal filtering, scoring storage, context burn, source validation). The V10 session exposed **12 new behavioural failures** — the agent has correct principles but lacks enforcement mechanisms. The root cause: "Agent optimises for perceived responsiveness over actual value."

V11 is a **CLAUDE.md rewrite + context.md template change**. No new scripts. The fix is entirely in the instruction and accountability layer.

## Options Considered

### Option 1: CLAUDE.md Only
Rewrite CLAUDE.md with mandatory workflows. Keep context.md as-is.
- Pros: Minimal changes, focused
- Cons: No accountability tracking — agent can still skip verification invisibly

### Option 2: CLAUDE.md + New Scripts
Add `verify_job_active.py` for automated career page checking.
- Pros: Belt-and-suspenders
- Cons: Scripts can be skipped too. Problem is discipline, not capability.

### Option 3: CLAUDE.md + context.md Template Changes
Rewrite CLAUDE.md with MUST/NEVER rules. Add `## Search Progress` and `## Verification Log` to context.md as accountability tracking.
- Pros: Two enforcement layers (rules + visible tracking). Cherry-picking becomes detectable.
- Cons: Slightly more complex template

## Chosen Approach

**Option 3: CLAUDE.md + context.md template changes.**

The scripts work. The agent already has the tools to verify jobs (WebFetch). The problem is discipline, not capability. Adding tracking sections makes skipping visible — if `## Search Progress` shows 3 of 7 role types searched, the gap is obvious.

## Architecture

### Target: `03_agents/tests/v11/`

Copy V10 environment. Rewrite CLAUDE.md (~135 lines). Replace context.md with blank template + 2 new sections. Keep all scripts unchanged.

### Core Rules (replace V10's 4 aspirational principles)

| Rule | Statement | Failures Fixed |
|------|-----------|----------------|
| 1 | NEVER present a job without full verification | 1, 3, 5, 8 |
| 2 | NEVER fabricate data — copy exactly from source | 6, 9, 12 |
| 3 | MUST search ALL target role types before ranking | 2 |
| 4 | MUST ask one question at a time | 7 |
| 5 | NEVER ask user to do technical work | 4 |
| 6 | MUST batch work within context limits | 5, 11 |

### V11 CLAUDE.md Section Structure (~135 lines)

| Section | Lines | Status | Purpose |
|---------|-------|--------|---------|
| Header | ~3 | Same as V10 | Agent identity |
| **Core Rules** | ~24 | **NEW** | 6 MUST/NEVER rules replacing 4 principles |
| **Onboarding** | ~18 | **NEW** | 8-step flow, includes "skills beyond CV" |
| Constraint Derivation | ~12 | Modified | + store ALL role types explicitly |
| Source Discovery | ~8 | Modified | + map sources to role types |
| **Search Workflow** | ~10 | **NEW** | Mandatory search ALL role types, track progress |
| **Verification Workflow** | ~14 | **NEW** | 5-step gate per job, batches of 5 |
| **Accuracy Rules** | ~6 | **NEW** | Exact titles, extracted URLs, system dates |
| **Presentation Rules** | ~8 | **NEW** | 4 preconditions before showing results |
| **UX Rules** | ~6 | **NEW** | One question, no tech work, progress reporting |
| Capabilities | ~3 | Same | Reference |
| Outputs | ~4 | Modified | + date rule |
| Job Schema | ~3 | Same | Reference |
| Briefs | ~3 | Modified | + match breakdown requirement |
| Dream Companies | ~2 | Same | Reference |
| Scheduled Runs | ~7 | Same | Reference |
| Security | ~4 | **Rewritten** | Agent handles .env silently |

### New Sections Detail

**Onboarding (8 steps):**
1. Read context.md + scan output/
2. If profile exists → show status, suggest next action
3. Ask for CV
4. Parse CV → write to context.md
5. Present extracted profile for correction
6. Ask: "Skills you have that aren't on your CV?" ← fixes Failure 10
7. Target questions (one per message): roles, industries, location, salary, dream companies, email
8. Derive constraints → confirm with user

**Search Workflow:**
1. Read ALL role types from `## Target`
2. For each: run jobspy_search.py + check specialty sources
3. Update `## Search Progress` after each role type
4. After ALL searched: filter → summarize → identify promising candidates
5. Only then proceed to Verification Workflow

**Verification Workflow (per job, batches of 5):**
1. CONFIRM ACTIVE — Check company career page
2. READ FULL DESCRIPTION — Fetch actual posting, copy exact title
3. CHECK REQUIREMENTS — Compare each requirement against CV/skills
4. SCORE — Apply rubric, show math
5. LOG — Record in `## Verification Log`

**Accuracy Rules:**
- Titles: copy character-for-character from listing
- URLs: extract from page, never construct by pattern
- Dates: use `date +%Y-%m-%d`, never hardcode year
- Companies: use name as written on their website

**Presentation Rules (4 preconditions):**
1. All role types searched (check `## Search Progress`)
2. All promising candidates verified (check `## Verification Log`)
3. Every job has: exact title, working URL, active status, scored
4. Jobs ranked by score, highest first

**UX Rules:**
- One question per message, always
- Never ask user to run commands or edit configs
- Report progress with specifics ("Searched 4 of 7 role types")
- If context running low, save state and instruct "say continue"

### context.md Template (V11)

Blank headers (same as V10 design intent) plus two new tracking sections:

```
## Search Progress

| Role Type | Status | Source(s) | Jobs Found | Date |
|-----------|--------|-----------|------------|------|

## Verification Log

| Title (exact) | Company | Active? | Score | Result | Reason | Date |
|----------------|---------|---------|-------|--------|--------|------|
```

The column "Title (exact)" is itself an instruction — reminds the agent to copy precisely every time it fills in the table.

### Modified Existing Sections

- **Constraint Derivation:** Add instruction to store ALL mentioned role types in `## Target`
- **Source Discovery:** Add instruction to map each source to the role types it serves
- **Outputs:** Add date rule: "All filenames use `date +%Y-%m-%d`. Never hardcode a year."
- **Briefs:** Add: "Include match breakdown — requirements met, stretches, and gaps"
- **Security:** Rewrite to: "Agent creates/updates .env silently. Never ask user to edit config files."

## Failure-to-Fix Mapping

| # | Failure | Fixed By |
|---|---------|----------|
| 1 | Title matching without requirements | Rule 1 + Verification Workflow step 3 |
| 2 | Incomplete search coverage | Rule 3 + Search Workflow + Search Progress |
| 3 | Stale jobs presented as active | Rule 1 + Verification Workflow step 1 |
| 4 | Asked user to do technical work | Rule 5 + Security rewrite |
| 5 | Cherry-picking verification | Rule 1 + Rule 6 + Verification Log |
| 6 | Wrong job titles | Rule 2 + Accuracy Rules |
| 7 | Multiple questions at once | Rule 4 + UX Rules |
| 8 | Presenting before full verification | Rule 1 + Presentation Rules |
| 9 | Aggregator URLs assumed valid | Rule 2 + Accuracy Rules |
| 10 | Missing skills not on CV | Onboarding step 6 |
| 11 | Context exhaustion | Rule 6 + UX Rules |
| 12 | Inconsistent dates | Rule 2 + Accuracy Rules + Outputs |

## Success Criteria

V11 succeeds when a live session shows:
1. Agent verifies ALL promising jobs before presenting any results
2. All job titles in output match source listings exactly
3. All URLs in output resolve (no 404s from fabrication)
4. All role types from `## Target` appear in `## Search Progress` as "searched"
5. Every presented job appears in `## Verification Log`
6. Dates use correct year throughout
7. Agent asks one question at a time during onboarding
8. Agent asks about skills not on CV
9. Agent handles .env setup silently
10. Agent saves state before context exhaustion

## Risks

| Risk | Mitigation |
|------|------------|
| Agent ignores MUST/NEVER rules | Rules are binary, Verification Log creates paper trail |
| Verification batching adds overhead | Batch of 5 is small; V10 already did verification, just inconsistently |
| 135 lines pushes context higher | ~3K tokens, negligible vs 200K window |
| Verification Log grows large | 20-30 rows max; can archive to file if needed |

## File Structure

```
03_agents/tests/v11/
├── CLAUDE.md                     # REWRITTEN (~135 lines)
├── context.md                    # Blank template + 2 new sections
├── .claude/settings.local.json   # From V10 (unchanged)
├── scripts/
│   ├── jobspy_search.py          # From V10 (unchanged)
│   ├── filter_jobs.py            # From V10 (unchanged)
│   ├── summarize_jobs.py         # From V10 (unchanged)
│   ├── send_email.py             # From V10 (unchanged)
│   └── create_briefs_pdf.py      # From V10 (unchanged)
├── tests/
│   ├── test_filter_jobs.py       # From V10 (unchanged)
│   └── test_summarize_jobs.py    # From V10 (unchanged)
└── output/
    ├── jobs/
    ├── briefs/
    └── digests/
```

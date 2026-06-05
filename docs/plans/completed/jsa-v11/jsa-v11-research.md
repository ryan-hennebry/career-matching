# Research: Job Search Agent V10 Session Failures

## Context

V10 was built to fix V9's 7 failures (universal filtering, deterministic scoring, digest/brief sync, context burn, source validation, credential handling). The V10 session completed onboarding, searched across 10+ job types, verified roles, generated a final top 10, and created 8 application briefs + PDF. The analysis identified **12 new failures** across 4 categories.

---

## V10 Environment Structure

```
03_agents/tests/v10/
├── CLAUDE.md                     # 90 lines — agent instructions
├── context.md                    # 97 lines — populated user profile
├── .claude/settings.local.json   # Permissions config
├── scripts/
│   ├── jobspy_search.py          # 127 lines — JobSpy wrapper with title filter
│   ├── filter_jobs.py            # 78 lines — Universal title filter (NEW in V10)
│   ├── summarize_jobs.py         # 84 lines — One-line summaries (NEW in V10)
│   ├── send_email.py             # 100 lines — Resend API email delivery
│   └── create_briefs_pdf.py      # 243 lines — PDF from brief markdowns
├── tests/
│   ├── test_filter_jobs.py       # 78 lines — 3 test cases
│   └── test_summarize_jobs.py    # 72 lines — 3 test cases
└── output/
    ├── jobs/                     # 22 files (11 jobspy JSONs, 3 web3 JSONs, 3 filtered, 2 markdown lists)
    ├── briefs/                   # 12 markdown briefs + 1 PDF
    └── digests/                  # 7 digest files across both sessions
```

---

## The 12 V10 Failures (from jsa-v10-analysis.md)

### Category: Verification Shortcuts (Failures 1, 3, 5, 8)

**Pattern:** Agent prioritises showing quick results over thorough verification. User corrected multiple times.

| # | Failure | What Happened | Root Cause |
|---|---------|---------------|------------|
| 1 | Title matching without requirement verification | Matched by title/salary only, didn't read full requirements | Agent shortcutting to save time/context |
| 3 | Stale jobs presented as active | Horizenlabs 3-month-old role shown as active | Relied on aggregator data without freshness check |
| 5 | Cherry-picking verification | Agent admitted skipping some to "save context" | Context pressure led to incomplete work |
| 8 | Presenting before full verification | Showed "Top 10" before verifying all candidates | Premature presentation for perceived responsiveness |

**Key code references:**
- `CLAUDE.md:7` — Principle 1 "Verify fit before presenting" exists but was violated
- `CLAUDE.md:46` — Context management guidance exists but didn't prevent shortcuts
- No mechanism in CLAUDE.md forces verification to complete before presentation

---

### Category: Incomplete Coverage (Failures 2, 10)

| # | Failure | What Happened | Root Cause |
|---|---------|---------------|------------|
| 2 | Incomplete search coverage | Only searched 3 of user's role types initially | Didn't extract all target roles from onboarding |
| 10 | Missing AI agent skill from profile | User had to ask about unlisted skills | Didn't ask about skills not on CV |

**Key code references:**
- `context.md:29` — Target roles section stores broad categories but V10 CLAUDE.md doesn't enforce searching each
- `CLAUDE.md:22-29` — Onboarding steps don't include "ask about skills not on CV"
- `context.md:63-67` — Search Strategy section was populated mid-session after user correction

---

### Category: Accuracy Issues (Failures 6, 9, 12)

| # | Failure | What Happened | Root Cause |
|---|---------|---------------|------------|
| 6 | Wrong job titles in output | "Product Marketing - Agents @ ElevenLabs" vs actual "B2B Growth Marketing - Agents" | Constructed from memory, not actual listing |
| 9 | Aggregator URLs assumed valid | Web3.Career URLs returned 404 | Fabricated URLs instead of extracting from source |
| 12 | Inconsistent date handling | Files created with 2025-02-04 instead of 2026-02-04 | Agent used wrong year |

**Evidence in output files:**
- `output/jobs/long-list-2025-02-04.md:1` — Filename and header say "4 Feb 2025" (wrong year)
- `output/digests/2025-02-04-final.md` and `2025-02-04.md` — Both use wrong year
- `output/digests/2026-02-04-verified-top10.md:185` — ElevenLabs listed as excluded ("Product marketing experience required") in verified top10, but included as #1 in final-top10
- `output/digests/2026-02-04-final-top10.md:10` — Title "Product Marketing - Agents @ ElevenLabs" — analysis says actual title was different

---

### Category: UX & Operational Issues (Failures 4, 7, 11)

| # | Failure | What Happened | Root Cause |
|---|---------|---------------|------------|
| 4 | Asked user to do technical work | "Copy .env.example to .env, edit and add RESEND_API_KEY" | Didn't adapt to non-technical user |
| 7 | Multiple questions at once | Asked 2 questions on startup | Not following onboarding UX guidance |
| 11 | Context exhaustion before completion | Ran out of context before completing verification | Too many web fetches without batching |

**Key code references:**
- `CLAUDE.md:23` — "One question at a time" exists but failure 7 still happened
- `CLAUDE.md:86-89` — Security section tells agent to use `.env` pattern, but guidance frames it as user task
- `CLAUDE.md:42-46` — Context management section exists but lacks quantitative guardrails

---

## What V10 CLAUDE.md Currently Has (and What's Missing)

### Present in CLAUDE.md (90 lines)

| Section | Lines | Status |
|---------|-------|--------|
| Principles (4) | 6-11 | Generic — "verify fit" but no enforcement mechanism |
| On Startup | 13-17 | OK |
| Constraint Derivation | 19-29 | OK — stores exclusions, scoring weights |
| Source Discovery | 31-38 | OK — includes fit verification step |
| Context Management | 40-46 | Weak — no quantitative thresholds |
| Capabilities | 48-52 | OK |
| Outputs | 54-58 | OK |
| Job Schema | 60-64 | OK |
| Briefs | 66-68 | Minimal — no match breakdown requirement |
| Dream Companies | 70-72 | OK |
| Scheduled Runs | 74-83 | Has sync verification step (#6) |
| Security | 85-89 | Frames .env setup as user task |

### Missing from CLAUDE.md

1. **Mandatory verification workflow** — No step-by-step process that prevents presentation before verification
2. **Full role type search enforcement** — No instruction to search ALL target role types from context.md
3. **Onboarding: skills not on CV** — No step asking about unlisted skills
4. **Non-technical user guidance** — No instruction to do technical setup silently
5. **URL handling rules** — No instruction against fabricating URLs
6. **Date accuracy** — No instruction to use correct date
7. **Title accuracy** — No instruction to copy exact titles from source
8. **Context budget guardrails** — No threshold-based rules for when to save state
9. **Batch verification workflow** — No structure for verifying jobs in groups
10. **One-question-at-a-time enforcement** — Exists as onboarding step but violated in practice

---

## Scripts Analysis

### filter_jobs.py (V10 NEW)
- `filter_jobs.py:25-43` — `filter_jobs()` function: case-insensitive partial match against title
- Works correctly for its scope (title keyword exclusion)
- **Gap:** Only filters by title keywords — no filtering by requirements, salary, or location
- Agent must still manually verify requirements after filtering

### summarize_jobs.py (V10 NEW)
- `summarize_jobs.py:41-50` — `summarize_job()`: one-line `title | company | location | salary`
- `summarize_jobs.py:19-38` — `format_salary()`: handles None, NaN, numeric values
- Works correctly for context burn prevention
- **Gap:** Doesn't include match score, status, or date_posted in summary

### jobspy_search.py (from V9)
- `jobspy_search.py:33-54` — `filter_jobs_by_title()`: comma-separated exclusion (duplicates filter_jobs.py logic)
- `jobspy_search.py:80-127` — `main()`: searches Indeed, LinkedIn, Glassdoor
- **Note:** Has its own title filter that overlaps with filter_jobs.py

### create_briefs_pdf.py (V10 session output)
- `create_briefs_pdf.py:190-198` — Hardcoded role list on cover page
- `create_briefs_pdf.py:226-234` — Hardcoded brief file paths
- **Gap:** Not parameterized — only works for this specific session's output

### send_email.py (from V9)
- `send_email.py:45-50` — Reads RESEND_API_KEY from env var (correct pattern)
- `send_email.py:63-67` — Constructs email params
- Works as expected

---

## Test Coverage

### What's Tested (6 tests)

| Test | File | What it Tests |
|------|------|---------------|
| `test_excludes_matching_titles_case_insensitive` | test_filter_jobs.py:38-49 | Title exclusion works case-insensitively |
| `test_preserves_all_fields` | test_filter_jobs.py:51-67 | Filtered jobs keep all fields |
| `test_no_exclusions_returns_all` | test_filter_jobs.py:69-78 | Empty exclusion list = no filtering |
| `test_output_format` | test_summarize_jobs.py:31-47 | Summary contains title, company, location |
| `test_max_jobs_limit` | test_summarize_jobs.py:49-56 | Respects --max parameter |
| `test_handles_nan_values` | test_summarize_jobs.py:58-72 | NaN salary = no "nan" in output |

### What's NOT Tested

- `jobspy_search.py` — No tests (external API dependency)
- `send_email.py` — No tests (external API dependency)
- `create_briefs_pdf.py` — No tests (hardcoded, session-specific)
- Agent behavior / CLAUDE.md compliance — No automated tests (manual session testing only)

---

## Output File Analysis — Evidence of Failures

### Wrong Dates (Failure 12)
- `output/jobs/long-list-2025-02-04.md` — File header: "4 Feb 2025" (should be 2026)
- `output/digests/2025-02-04-final.md` — Filename uses 2025
- `output/digests/2025-02-04.md` — Filename uses 2025

### Inconsistent Rankings Across Digests (Failures 1, 5, 8)
- `output/digests/2026-02-04-verified-top10.md` — ElevenLabs EXCLUDED (line 185: "Product marketing experience required")
- `output/digests/2026-02-04-final-top10.md` — ElevenLabs included as #1
- The same job was excluded then re-included between digest versions, showing verification wasn't consistent

### Title Inaccuracy (Failure 6)
- `output/digests/2026-02-04-final-top10.md:10` — "Product Marketing - Agents @ ElevenLabs"
- Analysis says actual title was "B2B Growth Marketing - Agents"

### Stale Job (Failure 3)
- `output/briefs/horizenlabs-community-manager-brief.md` — Brief generated for Horizenlabs
- Analysis says role was 3 months old and actually closed on company career page

---

## Patterns Found

### The Core Pattern (Same as V9)

**Agent optimises for perceived responsiveness over actual value.** The V10 analysis explicitly states:
> "The agent was optimizing for perceived responsiveness rather than actual value."

V10's CLAUDE.md added "Verify fit before presenting" as Principle 1, but the principle was aspirational — no enforcement mechanism existed.

### What V10 Fixed from V9 (Working)

1. **Universal filtering** — `filter_jobs.py` works for any source (Failures V9-1, V9-5: FIXED)
2. **Scoring rubric storage** — context.md has `## Scoring Rubric` section (Failure V9-2: FIXED)
3. **Context burn prevention** — `summarize_jobs.py` works (Failure V9-4: FIXED)
4. **Source content validation** — CLAUDE.md:35 includes fit check (Failure V9-6: FIXED)
5. **Credential handling** — CLAUDE.md:85-89 has .env guidance (Failure V9-7: PARTIALLY FIXED — still frames as user task)
6. **Digest/brief sync** — CLAUDE.md:82 has sync verification step (Failure V9-3: FIXED)

### What V10 Introduced New

1. **Constraint derivation** — Agent derives exclusions from conversation (CLAUDE.md:19-29)
2. **Blank context.md template** — Populated through onboarding, not hardcoded

### What V10 Didn't Address

The 12 new failures are mostly **behavioural** rather than **structural**:
- The agent has the right principles but doesn't follow them
- The CLAUDE.md lacks enforcement mechanisms (mandatory workflows, quantitative thresholds)
- Accuracy issues (titles, URLs, dates) need explicit "copy exactly from source" rules

---

## Historical Context

| Version | Focus | Failures Found | Key Win |
|---------|-------|----------------|---------|
| V7 | Initial architecture | N/A | First working agent |
| V8 | Multi-source, briefs | N/A | Complete workflow |
| V9 | Clean test environment | 7 | Discovered failure modes |
| V10 | Fix V9 failures | 12 | Fixed V9 scripts (filter, summarize), new failures are behavioural |

**Trend:** Script-level fixes work. Behavioural failures need CLAUDE.md workflow constraints.

---

## Related Files

### V10 Test Environment
All files listed in structure above.

### Documentation
- `docs/plans/active/jsa-v10-analysis.md` — Full session analysis (12 failures, 5 wins)
- `docs/plans/active/jsa-v10-research.md` — V10 codebase research (covers V9→V10 transition)
- `docs/plans/active/jsa-v10-design.md` — V10 design doc (6 failure fixes from V9)

### Production Agent
- `03_agents/career-matching/CLAUDE.md` — 248 lines (much more detailed than test V10's 90 lines)
- `03_agents/career-matching/context.md` — 164 lines with full section structure
- `03_agents/career-matching/references/` — algorithms.md, sources.md, templates.md

---

## Summary

V10 successfully fixed V9's structural issues (universal filtering, scoring storage, context burn, source validation). The 12 new failures are predominantly **behavioural** — the agent has correct principles but lacks:

1. **Mandatory verification workflows** with enforcement (not just aspirational principles)
2. **Accuracy rules** for titles, URLs, and dates
3. **Coverage enforcement** for searching all target role types
4. **Context budget thresholds** with quantitative triggers
5. **Non-technical user adaptation**
6. **Onboarding completeness** (skills beyond CV)

The analysis recommends these as CLAUDE.md constraint additions and a verification workflow redesign — not new scripts or architectural changes.

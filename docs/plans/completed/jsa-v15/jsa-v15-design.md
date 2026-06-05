# Design: JSA V15 Review Fixes

## Context

6-agent review of V15 codebase (2026-02-10) identified 20 findings across Critical/High/Medium/Low. Scope for this iteration: **Critical (1) + High (3) + Medium (7) = 11 fixes**. Low-priority items deferred.

The critical blocker is **C1 (v14 path references)** — all agents/skills/workflow hardcode `03_agents/tests/v14/` causing complete pipeline failure on a clean V15 deployment. Everything else is improvement.

Source: `docs/plans/active/jsa-v15-reviews.md`

## Options Considered

### Option 1: Fix Everything (All 20 findings)
- Pros: Clean codebase, zero tech debt
- Cons: Large scope, many low-priority items add little value (version labels, gitignore patterns, YAGNI cleanup). Risk of regressions.

### Option 2: Critical + High + Medium (11 findings)
- Pros: Addresses all correctness and security issues plus meaningful improvements. Skips cosmetic cleanup.
- Cons: Leaves 9 low-priority items as known debt.

### Option 3: Critical + High only (4 findings)
- Pros: Minimal, fast, unblocks deployment
- Cons: Leaves real improvements on the table (expired job growth, CSS bloat, dead code)

## Chosen Approach

**Option 2: Critical + High + Medium.** The Critical + High fixes are mandatory. The Medium items include real functional improvements: expired jobs growing unbounded (M1), brief parallelization saving 1.5-3.5 min per run (M2), ~320 lines of CSS dedup (M3), status file consistency (M4), dead code removal (M5).

**CSS dedup strategy:** Single canonical CSS block stays in `jsa-design-system.md`. Output skills (`jsa-digest-email.md`, `jsa-briefs-html.md`) get duplicated CSS blocks removed and replaced with "use the design system CSS exactly" instruction. The design system skill is already preloaded via `skills:` frontmatter — no parsing needed.

## Architecture

No structural changes. The three-layer architecture (orchestrator -> agents -> skills) is sound per all 6 reviewers. All changes are within existing files.

## Implementation Phases

### Phase 1: Path Fix (C1) — must be first

Find-replace `v14` -> `v15` across 9 files (22 occurrences):

| File | Occurrences |
|------|-------------|
| `.claude/agents/brief-generator.md` | 2 |
| `.claude/agents/search-verify.md` | 2 |
| `.claude/agents/briefs-html.md` | 2 |
| `.claude/agents/digest-email.md` | 2 |
| `.claude/agents/onboarding.md` | 2 |
| `.claude/skills/jsa-search-verify.md` | 2 |
| `.claude/skills/jsa-brief-generator.md` | 2 |
| `.github/workflows/daily-digest.yml` | 5 |
| `CLAUDE.md` line 346 | 1 |
| `scripts/manage_state.py` lines 1, 251 | 2 |
| `tests/conftest.py` line 1 | 1 |

### Phase 2: Security (H1, H2)

**H1:** Add HTML-escape instruction to `jsa-digest-email.md` and `jsa-briefs-html.md` — escape all external job data before HTML insertion, validate URL schemes.

**H2:** In `scripts/preview.sh` — add `--bind 127.0.0.1` and cleanup trap.

### Phase 3: Housekeeping (H3, M2, M5)

**H3:** Remove stale Phase 5 note from `.claude/agents/digest-email.md`.

**M2:** Add parallel dispatch instruction to CLAUDE.md Step 17.

**M5:** Remove dead `filter_jobs_by_title()`, `--exclude-titles` arg, and conditional call from `scripts/jobspy_search.py` (~31 lines).

### Phase 4: CSS Dedup (M3)

**`jsa-digest-email.md`:** Remove Email HTML Skeleton section, Link Styling section, and redundant CSS blocks (~80-100 lines). Replace with references to design system skill. Keep card/table HTML template examples (subagent needs inline style examples for email rendering).

**`jsa-briefs-html.md`:** Remove brief separator CSS and link style duplicates (~15 lines). Replace with references.

### Phase 5: Python + Agent (M1, M4)

**M1:** Add `purge_expired()` to `manage_state.py` with 90-day retention. Call in `_cli_sync()`. Add 2 tests.

**M4:** Change `brief-generator.md` failure behavior from "exit silently" to "write `_status.json` then exit" — matches all other 4 agents.

### Phase 6: Infrastructure (M6, M7)

**M6:** Add staged-file verification to `daily-digest.yml` before commit.

**M7:** Narrow permissions in `settings.local.json`: `rm:output/*`, `curl:http://localhost:*`.

## Files to Modify (17 total)

| File | Fixes |
|------|-------|
| `.claude/agents/brief-generator.md` | C1, M4 |
| `.claude/agents/search-verify.md` | C1 |
| `.claude/agents/briefs-html.md` | C1 |
| `.claude/agents/digest-email.md` | C1, H3 |
| `.claude/agents/onboarding.md` | C1 |
| `.claude/skills/jsa-search-verify.md` | C1 |
| `.claude/skills/jsa-brief-generator.md` | C1 |
| `.claude/skills/jsa-digest-email.md` | H1, M3 |
| `.claude/skills/jsa-briefs-html.md` | H1, M3 |
| `.github/workflows/daily-digest.yml` | C1, M6 |
| `CLAUDE.md` | C1, M2 |
| `scripts/manage_state.py` | C1, M1 |
| `scripts/preview.sh` | H2 |
| `scripts/jobspy_search.py` | M5 |
| `tests/test_manage_state.py` | M1 |
| `tests/conftest.py` | C1 |
| `.claude/settings.local.json` | M7 |

## Success Criteria

1. Zero `v14`/`V14` references in V15 codebase
2. All 16 tests pass (14 existing + 2 new purge tests)
3. No `--exclude-titles` in jobspy_search.py
4. No duplicated CSS blocks in output skills
5. All 5 agents write `_status.json` on failure
6. Preview server binds to localhost only
7. CI workflow verifies staged files before commit
8. Permissions scoped to `output/` for rm, `localhost` for curl

## Risks

1. **CSS dedup visual regression** — mitigated by: design system skill preloaded via frontmatter, post-render verification in Step 18b unchanged
2. **Purge date math error** — mitigated by: 2 explicit unit tests with date assertions
3. **Dead code removal** — safe: skill explicitly prohibits `--exclude-titles`

## Handoff Contract

- **Approach:** Single-pass fix iteration, 6 phases, 11 fixes, 17 files
- **Components:** No new components — modifications to existing files only
- **Success criteria:** 8 measurable checks (see above)
- **Risks requiring mitigation:** CSS dedup visual regression (verify with preview.sh), purge date math (unit tests)

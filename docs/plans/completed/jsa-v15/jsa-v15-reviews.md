# JSA V15 Reviews

## Round 2 — Plan Review (2026-02-10)

**Reviewers:** DHH (Rails philosophy), Kieran (Rails conventions), CS (Code Simplicity)
**Scope:** Updated plan file after Round 1 fixes

### Verdict: APPROVED for build

All 5 Required Changes and 5 Recommended Changes from Round 1 have been correctly applied. The plan is now internally consistent, complete, and ready for implementation.

**Verification of Round 1 fixes:**
- [x] R1: `SERVER_PID=""` initialization added before cleanup function definition
- [x] R2: `excluded_count` print logic removal (item 4) added to Step 3.3, count updated to "Five deletions"
- [x] R3: Step 5.2 expected output corrected to "2 ERRORS" (collection errors)
- [x] R4: Dead `ALLOWED` variable removed from CI verification script
- [x] R5: Phase 4 note about line number drift added with content-anchor guidance
- [x] RC1: try/except ValueError added around date parse in `purge_expired()`
- [x] RC2: Note explaining `_brief_generator_status.json` naming rationale added
- [x] RC3: Phase 5 commit message changed from `feat()` to `fix()`
- [x] RC5: Bottom-up deletion order note integrated into Step 3.3 header

### Remaining observations (informational only, no action needed)

- [x] **Step 5.4 line numbers (232-234) are approximate** — actual `_cli_sync` content starts at line 240 in the source file. The content-based match (`load_state` / `update_state` / `save_state` sequence) is correct and sufficient for implementation. No fix needed.

- [x] **Step 3.4 verification grep does not check for `excluded_count`** — intentional. The grep checks for the dead feature (`exclude.titles`, `filter_jobs_by_title`), not local variables that could appear in other contexts. No fix needed.

### Approval Status

- **DHH:** APPROVED — All correctness issues resolved. Plan is clean and actionable.
- **Kieran:** APPROVED — Naming conventions addressed, deletion order specified, line number drift documented.
- **CS:** APPROVED — Dead code/variables removed, error handling added, commit messages consistent.

---

## Round 1 — Plan Review (2026-02-10)

**Reviewers:** DHH (Rails philosophy), Kieran (Rails conventions), CS (Code Simplicity)
**Scope:** Plan file `docs/plans/active/jsa-v15-plan.md`
**Source files verified:** `manage_state.py`, `preview.sh`, `jobspy_search.py`, `brief-generator.md`, `digest-email.md`, `jsa-digest-email.md`, `jsa-briefs-html.md`, `daily-digest.yml`, `settings.local.json`, `test_manage_state.py`, `conftest.py`, `CLAUDE.md`

### Verdict: Needs Changes

The plan is well-structured with clear phases, correct dependency ordering, and sensible fix groupings. The critical path fix (C1) is rightfully Phase 1. Line numbers and file references are almost entirely accurate against the actual codebase. However, there are several issues: incomplete dead code removal in `jobspy_search.py` that would cause a `NameError`, a cleanup function variable initialization gap in `preview.sh`, a dead variable in the CI verification script, and minor accuracy issues in expected test output.

### Required Changes

- [x] **R1: `preview.sh` cleanup function should initialize `SERVER_PID` (Step 2.3)**
  The plan places `cleanup() { kill "$SERVER_PID" 2>/dev/null || true; }` right after `set -e`, but `SERVER_PID` is not assigned until later. If the script exits between the function definition and the assignment (e.g., during the `lsof` kill or `cd`), `cleanup()` will attempt `kill ""` which produces an error (suppressed by `|| true`, but still incorrect). **Fix:** Add `SERVER_PID=""` initialization on the line before the cleanup function definition.

- [x] **R2: Dead code removal in Step 3.3 misses `excluded_count` print logic (lines 114-116)**
  The plan removes the `filter_jobs_by_title` function, the `--exclude-titles` argument, the conditional filter call, and updates `build_output`. But it does NOT remove lines 114-116 in `jobspy_search.py`:
  ```python
            if excluded_count:
                msg += f" (excluded {excluded_count} by title)"
  ```
  After the plan's changes, `excluded_count` is no longer defined in `main()`, so this code would cause a `NameError` at runtime when `args.output` is set. **Fix:** Add removal of the `excluded_count` conditional (lines 114-116) and simplify the message line to `msg = f"Wrote {len(results)} jobs to {args.output}"`.

- [x] **R3: Step 5.2 expected test failure output is inaccurate**
  Step 5.2 says: `Expected: 2 FAILED — ImportError: cannot import name 'purge_expired' from 'manage_state'`. In reality, pytest will report `2 ERRORS` (collection errors), not `2 FAILED`. The distinction matters for someone verifying the TDD red-green cycle. **Fix:** Change expected output to `2 ERRORS — ImportError during collection`.

- [x] **R4: Step 6.1 CI verification has dead `ALLOWED` variable**
  The staged-file verification script defines `ALLOWED="state.json output/session-state.md"` but never uses it — the `case` statement hardcodes the filenames. **Fix:** Remove the `ALLOWED` line since it's unused.

- [x] **R5: Phase 4 line numbers will be wrong after Phase 2 insertions**
  Step 2.1 inserts a new rule (rule 10) into `jsa-digest-email.md`. Step 2.2 inserts a new bullet into `jsa-briefs-html.md`. These insertions shift all subsequent line numbers in both files, making Phase 4's line references (e.g., "lines 158-197", "lines 199-213", "lines 32-44") incorrect. **Fix:** Add a note at the start of Phase 4 that line numbers assume the file state BEFORE Phases 2-3, or use content-based anchors (section headers like "## Email HTML Skeleton") for find-replace instead of line numbers.

### Recommended Changes

- [x] **RC1: Step 5.3 `purge_expired()` has no error handling for malformed dates**
  The `datetime.strptime(entry.expired_date, "%Y-%m-%d")` call will raise `ValueError` on corrupt date strings. A single corrupt entry would prevent all expired jobs from being purged. **Fix:** Wrap the date parse in try/except ValueError and skip entries with unparseable dates, logging a warning.

- [x] **RC2: Step 5.6 status file path breaks naming convention**
  The plan sets the brief-generator failure status path to `output/briefs/_brief_generator_status.json`. Other agents use `output/{type}/_status.json` (e.g., `output/digests/_status.json`, `output/briefs/_status.json`). Using a different name creates a lookup inconsistency for the parent orchestrator. **Fix:** Use `output/briefs/_brief_generator_status.json` as planned (since `output/briefs/_status.json` is used by the briefs-html subagent), but add a note in CLAUDE.md Step 17 documenting this filename so the parent knows where to check.

- [x] **RC3: Commit message for Phase 5 uses `feat()` prefix instead of `fix()`**
  Phase 5 commit uses `feat(jsa-v15)` for what is a fix iteration (M1 addresses unbounded growth, M4 fixes missing status). All other phases correctly use `fix()`. **Fix:** Change to `fix(jsa-v15): add purge_expired() with tests, fix brief-generator status (M1, M4)`.

- [x] **RC4: `purge_expired()` only runs via CLI sync, not inline Python in Step 16** (logged as Reviewer Note — accepted limitation, confidence 55)
  Interactive runs use inline Python (CLAUDE.md Step 16) which calls `load_state`, `record_action`, `save_state` but not `purge_expired`. Purge only runs in the `_cli_sync()` path (scheduled runs). This means interactive-only users never get expired jobs purged. **Fix:** Note this as an accepted limitation, or add `purge_expired` call to the inline Python example in CLAUDE.md Step 16.

- [x] **RC5: Step 3.3 should specify bottom-up deletion order**
  The 4 deletions in `jobspy_search.py` should be applied from highest line numbers first to preserve line stability for earlier deletions. The plan lists them top-down. **Fix:** Add a note: "Apply deletions from highest line numbers to lowest."

### Nice-to-Have

- [ ] **N1: Step 1.5 grep verification could check `.yaml` extension too**
  The grep checks `--include="*.yml"` but some repos use `.yaml`. Not an issue here since the file is `.yml`, but adding `--include="*.yaml"` costs nothing.

- [ ] **N2: Phase 7 success criteria could be wrapped in a single script**
  The 8 verification commands are listed as manual steps. A `scripts/verify_v15_fixes.sh` would make re-verification trivial.

- [ ] **N3: Step 4.3 verification grep is weak**
  Checking for `border-radius:3px` or `font-family:'DM Sans'` doesn't distinguish inline styles (which are expected) from standalone CSS blocks (which should be removed). A better check would grep for the specific section headers that were removed.

### Approval Status

- **DHH:** Needs Changes (R1, R2 — correctness issues that would cause runtime errors)
- **Kieran:** Needs Changes (R2, R5 — incomplete removal, line number drift)
- **CS:** Needs Changes (R2, R4 — dead code, dead variable)

---

## Round 0 — Codebase Review (2026-02-10)

**Date:** 2026-02-10
**Reviewers:** 6 parallel agents (code-reviewer, architecture-strategist, security-sentinel, performance-oracle, pattern-recognition-specialist, code-simplicity-reviewer)
**Scope:** `03_agents/tests/v15/` (full codebase)
**Codebase:** 3,318 lines across ~30 meaningful files

---

## Consolidated Summary

### Verdict

The three-layer architecture (orchestrator -> agents -> skills) is sound. Separation of concerns is clean, tool scoping per agent is well-designed, and the post-render verification (Step 18b) is a strong defense-in-depth pattern. The Python scripts and test suite are already lean. All 14 regression items from V14 are properly addressed in the instructions. All 20 tests pass.

**The critical blocker is C1 (v14 paths).** Everything else is improvement rather than correctness.

### Risk Profile

| Severity | Count |
|----------|-------|
| Critical | 1 |
| High | 3 |
| Medium | 7 |
| Low | 9 |

### Potential LOC Reduction

| Area | Lines Saved |
|------|-------------|
| Design system CSS dedup | ~320 |
| Dead code in jobspy_search.py | 31 |
| YAGNI in algorithms.md | 44 |
| Digest-email duplicated content | ~96 |
| CLAUDE.md consolidation | ~15 |
| **Total** | **~428 (13%)** |

---

## Findings by Priority

### Critical (Must Fix)

**C1: All v14 path references must be updated to v15**
- *Source: All 6 reviewers*
- Every agent definition (5 files), 2 skill files, and the GitHub Actions workflow hardcode `03_agents/tests/v14/` as the working directory
- Subagents will `cd` into the wrong directory, causing complete pipeline failure on a clean v15 deployment
- Files affected (18 occurrences): `brief-generator.md`, `search-verify.md`, `briefs-html.md`, `digest-email.md`, `onboarding.md` (agents); `jsa-search-verify.md`, `jsa-brief-generator.md` (skills); `daily-digest.yml` (workflow, 5 occurrences)
- **Fix:** find-and-replace `03_agents/tests/v14` -> `03_agents/tests/v15` across ~10 files

### High Priority

**H1: HTML injection via job data in email digests**
- *Source: Security Sentinel*
- Severity: HIGH
- Job titles, company names, and locations scraped from external boards are inserted into HTML email bodies without sanitization
- A malicious job listing could inject phishing links or manipulate email layout
- **Fix:** Add `html.escape()` to all job data fields before HTML embedding. Consider Jinja2 with autoescape.

**H2: Preview server binds to 0.0.0.0**
- *Source: Security Sentinel, Code Reviewer*
- `preview.sh` starts `python3 -m http.server` without `--bind 127.0.0.1`, exposing career data to the local network
- Also missing `trap` for cleanup on exit
- **Fix:** Add `--bind 127.0.0.1` and `trap "kill $SERVER_PID 2>/dev/null" EXIT INT TERM`

**H3: Stale "Phase 5 placeholder" note in digest-email agent**
- *Source: Pattern Recognition, Code Reviewer, Simplicity Reviewer*
- Line 21 of `digest-email.md` claims the agent is "non-functional" when it's fully implemented
- Could cause the orchestrator to skip dispatching it
- **Fix:** Remove the stale note

### Medium Priority

**M1: `expired_jobs` grows without bound**
- *Source: Performance Oracle*
- Jobs move from `jobs` -> `expired_jobs` but are never purged
- After 6 months: `state.json` reaches ~5-7 MB. After 2 years: ~25 MB, 1-2s load/save
- **Fix:** Add `purge_expired()` function with 90-day retention, called at end of `update_state()`

**M2: Brief generation should be explicitly parallelized**
- *Source: Performance Oracle, Architecture Strategist*
- Step 17 has no batching instruction. Adding "dispatch all brief agents in parallel" saves 1.5-3.5 minutes per run
- Briefs have no shared state or external API calls
- **Fix:** Add explicit parallel dispatch instruction to Step 17 in CLAUDE.md

**M3: Design system CSS duplicated across 3 files**
- *Source: Simplicity Reviewer, Pattern Recognition*
- Same CSS appears in `jsa-design-system.md`, `jsa-digest-email.md`, and `jsa-briefs-html.md`
- ~320 lines could be cut by having output skills reference design tokens instead of embedding full CSS blocks
- Gmail override, link styling, brief separator CSS, HTML skeleton all duplicated
- **Fix:** Flatten design system to ~150 lines (tokens + components). Output skills reference tokens by name.

**M4: `brief-generator` has no `_status.json` failure protocol**
- *Source: Pattern Recognition, Code Reviewer*
- All other 4 agents write a status file on failure. The brief-generator silently exits.
- Creates asymmetric failure detection (parent must rely on file-absence detection)
- **Fix:** Add `_status.json` failure writing to match other agents

**M5: Dead `filter_jobs_by_title` code in `jobspy_search.py`**
- *Source: Simplicity Reviewer, Pattern Recognition*
- The skill explicitly says "Do NOT use `--exclude-titles`" -- the function, flag, and conditional call are 31 lines of dead code
- **Fix:** Remove `filter_jobs_by_title`, `--exclude-titles` arg, and conditional call

**M6: GitHub Actions pushes directly to main**
- *Source: Security Sentinel*
- No branch protection or file verification step
- `permissions: contents: write` grants broad repository write access
- **Fix:** Add `git diff --staged --name-only` verification step. Consider PR-based merge strategy.

**M7: Overly broad `Bash(rm:*)` permission**
- *Source: Security Sentinel*
- Could be scoped to `Bash(rm:output/*)` to reduce blast radius from prompt injection
- Similarly, `Bash(curl:*)` allows arbitrary HTTP requests
- **Fix:** Narrow permissions to specific directories/domains

### Low Priority

**L1: Version labels say "V14"** in `manage_state.py` (line 1, 251), `conftest.py` (line 1), CLAUDE.md SESSION MANAGEMENT (line 346)

**L2: `.gitignore` has PDF patterns** but the system never produces PDFs (hard constraint). Should add HTML patterns instead.

**L3: Learning System section in `algorithms.md`** (34 lines) is not implemented anywhere -- pure YAGNI.

**L4: Dedup rules in `algorithms.md`** are explicitly overridden by the search-verify skill -- contradictory.

**L5: Hardcoded GBP currency** in `summarize_jobs.py` despite schema supporting a `currency` field.

**L6: CLAUDE.md Steps 1-6 duplicate the ON STARTUP section** (~15 lines).

**L7: `send_email.py` uses sandbox `onboarding@resend.dev`** -- deployment blocker for production.

**L8: No test coverage for `jobspy_search.py` or `send_email.py`**.

**L9: `manage_state.py` missing JSON error handling in `_scan_verified_dir`** -- a corrupt verified JSON file would crash state sync.

---

## Individual Review Reports

### 1. Code Review (code-reviewer)

**Focus:** Regression item verification, correctness, test coverage

**Key findings:**
- All 14 regression items properly addressed in instructions
- All 20 tests pass (0 failures, 0.24s)
- Clean onboarding state confirmed (empty context.md, null last_run_date)
- Design system is comprehensive -- fonts, colors, layout, component patterns, Gmail override all present
- Critical: C1 (v14 paths), C2 (GitHub Actions v14 paths)
- Important: stale Phase 5 note, PDF gitignore patterns, preview.sh cleanup, sandbox email sender
- Suggestion: design system `<body>` template missing `id="body"` for Gmail override consistency

### 2. Architecture Review (architecture-strategist)

**Focus:** Layering, data flow, failure modes, hard constraint enforceability

**Key findings:**

**Strengths:**
- Clean three-layer separation (orchestrator / agent / skill) follows Dependency Inversion
- `disallowedTools` in agent frontmatter enforces speed constraints at tool-access layer
- `_status.json` completion signals provide clean parent-child contract
- Atomic writes in `manage_state.py` via tempfile+os.replace
- Email idempotency via `sent_at` field check

**Concerns (17 total):**
- C1: v14 paths (critical)
- session-state.md serves confusing dual purpose (progress tracking AND final summary)
- Implicit key-to-path coupling between manage_state.py and digest-email skill
- No timeout handling for subagent dispatch
- State corruption window between Steps 15-16 (user feedback collected but not yet saved)
- No rollback mechanism for partial subagent completion
- Hard Constraints rely heavily on LLM compliance rather than mechanical enforcement
- Memory write mechanism undefined (read-only from JSA's perspective)
- Step 18b verification narrowly scoped (checks 4 properties, design system defines far more)
- Scheduled run path skips verification of context.md existence

**Parallelization assessment:**
- Current batching (Steps 8, 18) is correct
- Step 17 (brief generation) is the main parallelization opportunity
- The 20-step sequencing is otherwise well-justified

### 3. Security Review (security-sentinel)

**Focus:** OWASP compliance, input validation, access control, secrets management

**Severity Summary:** 0 Critical, 1 High, 4 Medium, 4 Low, 3 Informational

**Detailed findings:**
- F1 (HIGH): Stored XSS / HTML injection via job data in email digests
- F2 (MEDIUM): Preview server exposes entire directory without access control, binds 0.0.0.0
- F3 (MEDIUM): GitHub Actions pushes directly to main without branch protection
- F4 (MEDIUM): Overly broad tool permissions (rm:*, curl:*, python3:*)
- F5 (MEDIUM): v14/v15 directory confusion -- state corruption risk
- F6 (LOW): No CLI input validation on manage_state.py (date format, verified-dir existence)
- F7 (LOW): Test temp files created with delete=False, never cleaned up
- F8 (LOW): Resend sandbox domain (onboarding@resend.dev) -- deliverability issue
- F9 (LOW): No email address validation on --to argument
- F10 (INFO): .env.example properly handled (positive finding)
- F11 (INFO): state.json tracked in git -- PII concern after onboarding fills context.md
- F12 (INFO): Atomic write pattern in manage_state.py is sound (positive finding)

**Positive findings:** No hardcoded secrets, no SQL injection surface, no shell=True in production code, atomic writes correct

### 4. Performance Review (performance-oracle)

**Focus:** Scalability, bottlenecks, runtime estimates, data volume projections

**Runtime estimate:** 12-22 min per run (excluding human interaction)

| Phase | Duration |
|-------|----------|
| Startup (steps 1-6) | 5-10s |
| Search-verify (steps 8-9) | 8-15 min |
| Brief generation (step 17) | 2-4 min sequential, 30-45s parallel |
| Digest + briefs-html (step 18) | 1-2 min |
| Email send (step 19) | 5-10s |

**Scalability projections:**

| Metric | Day 1 | 6 Months | 2 Years |
|--------|-------|----------|---------|
| Active jobs | 0-50 | 50-100 | 50-100 |
| Expired jobs | 0 | ~4,500 | ~18,000 |
| state.json size | 200B | ~3.5 MB | ~14 MB |
| Load time | <1ms | ~200ms | ~800ms |

**Key findings:**
- Brief <60s target IS achievable with current config (disallowedTools enforcement)
- Subagent dispatch overhead: ~7-14s per dispatch
- Search-verify has no WebFetch timeout or concurrency guard (15-120 requests per role type)
- Expired jobs dictionary is a one-way sink (critical growth issue)
- Brief parallelization saves 1.5-3.5 minutes
- Consider capping verbose fields in verified JSON to control brief-generator input size

### 5. Pattern & Consistency Review (pattern-recognition-specialist)

**Focus:** Naming, structural patterns, code duplication, anti-patterns

**Key findings:**

**Naming:** Internally consistent (agents: kebab-case, skills: jsa-prefix kebab-case, scripts: snake_case). One outlier: `jobspy_search.py` breaks verb_noun convention.

**Agent definitions:** All 5 follow identical structural template. One asymmetry: brief-generator has no `_status.json` on failure (all others do).

**Code duplication (6 instances):**
1. Title filtering logic in jobspy_search.py AND filter_jobs.py
2. Design system CSS in 3 overlapping blocks within jsa-design-system.md
3. Gmail link color override in design system AND digest-email skill
4. Link styling in design system AND digest-email skill
5. Filename slugification rules in search-verify AND brief-generator skills
6. Brief separator CSS in design system AND briefs-html skill

**Anti-patterns:**
- Contradictory dedup rules between skill (exact match) and algorithms.md (Jaccard 80%)
- GBP hardcoded despite schema having currency field
- Stale version refs (V13 in conftest, V14 everywhere else)

**Python style inconsistencies:**
- `from __future__ import annotations` in 3/5 scripts
- Missing shebang in manage_state.py
- No type hints in send_email.py
- Inconsistent test method return type annotations

### 6. Simplicity Review (code-simplicity-reviewer)

**Focus:** YAGNI violations, unnecessary complexity, LOC reduction opportunities

**Total codebase:** 3,318 lines. **Potential reduction:** ~428 lines (13%).

**Primary bloat sources:**
1. Design system CSS duplication (3 overlapping blocks, ~320 lines recoverable)
2. Agent definitions are boilerplate beyond YAML frontmatter (~60 lines across 5 files)
3. Dead --exclude-titles code in jobspy_search.py (31 lines)
4. YAGNI Learning System spec in algorithms.md (34 lines)
5. Overridden dedup rules in algorithms.md (10 lines)
6. CLAUDE.md Steps 1-6 duplicate ON STARTUP section (15 lines)
7. Presentation table example over-specified (25 lines reducible)

**YAGNI violations:** Learning System (unimplemented), filter_jobs_by_title (explicitly prohibited), Jaccard dedup (explicitly overridden), full CSS blocks (derivable from tokens), Phase 5 note (stale)

**What is already minimal (no changes needed):** Python scripts, test suite, preview.sh, GitHub Actions workflow, context.md template

---

## Handoff Contract

**Status:** Review complete. 6/6 agents returned.

**Critical blockers (1):**
- C1: v14 -> v15 path references (7 agent/skill files + 1 workflow file)

**High-priority fixes (3):**
- H1: HTML sanitization for job data in email digests
- H2: Preview server localhost binding + cleanup trap
- H3: Remove stale Phase 5 note from digest-email agent

**Medium-priority improvements (7):**
- M1: Expired job purging (90-day retention)
- M2: Parallel brief dispatch instruction
- M3: Design system CSS dedup (~320 lines)
- M4: brief-generator status file protocol
- M5: Remove dead filter code from jobspy_search.py
- M6: GitHub Actions branch protection
- M7: Permission scoping (rm:output/*)

**Low-priority cleanup (9):** Version labels, .gitignore patterns, YAGNI sections, GBP hardcoding, CLAUDE.md consolidation, sandbox email sender, missing test coverage, JSON error handling

**Next phase:** `/design` or `/plan` to implement fixes

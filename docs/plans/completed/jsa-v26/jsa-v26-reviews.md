# JSA V26 Reviews

## Round 3 — 2026-03-23

### Reviewers Active
architecture-strategist, code-simplicity-reviewer, regression-checker

### Required Changes
None.

### Recommended Changes
None.

### Nice-to-Have
- [ ] **[Conf: 70] [code-simplicity-reviewer]** `test_verify_and_commit_check_only.py` (Step 15b) and `test_gate_chains.py` (Step 30) both contain identical 6-line git-init boilerplate (init, config email, config name, mkdir output, add, commit). Two test files repeating the same setup pattern. -> Extract a `git_repo_with_output` fixture into `conftest.py` that returns a `tmp_path` pre-initialized as a git repo with `output/` directory. Use it in both test files to eliminate ~20 lines of duplication.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** `verify-session-state-written` validates `run_date` presence but not temporal freshness — a stale session-state.md from a previous run on the same date would pass. Risk is low since same-date reruns are intended and cross-date staleness would fail the date check. (Conf: 55)
- **[architecture-strategist]** `verify-and-commit --check-only` shells out to `git status --porcelain` — if working directory context differs from git repo root, check could silently return empty. Tests mitigate this by setting `cwd=str(tmp_path)`. (Conf: 52)
- **[code-simplicity-reviewer]** Step 30 `TestVerifyBeforeArchiveGate.test_aggregator_url_returns_unverified` is functionally similar to Step 5's equivalent, but tests the gate-chain integration path specifically. Minor overlap (1 test). (Conf: 55)
- **[code-simplicity-reviewer]** Phase 3 grep-count verification remains inherently fragile; /revise improved patterns to use path-like expressions. Acceptable given alternatives would be over-engineering. (Conf: 50)
- **[regression-checker]** V22 session resume guard remains unaddressed but the plan does not introduce code that worsens this gap — deferred item, not regression introduction. (Conf: 55)
- **[regression-checker]** V24 "ux-cli" regressions are out of scope for this infrastructure-focused plan. No regression introduced. (Conf: 55)

### Round 2 Fix Verification (regression-checker)
| Round 2 Finding | Status |
|-----------------|--------|
| Required: `--check-only` flag not implemented | FIXED — Step 15b |
| Recommended: Haiku scoring not covered by IF11 | FIXED — Step 25 Sonnet tier |
| Recommended: validate-presentation not in CLAUDE.md HC | FIXED — Step 24 HC13 |
| Recommended: preflight.sh sync test missing | FIXED — Step 31 test_preflight_sync.py |

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: APPROVED

### Statistics
- Total findings collected: 1
- Final actionable findings: 1 (0 Required, 0 Recommended, 1 Nice-to-Have)

---

## Round 2 — 2026-03-23

### Reviewers Active
architecture-strategist, code-simplicity-reviewer, regression-checker

### Required Changes
- [x] **[Conf: 95] [regression-checker]** Step 18 references `--check-only` flag for `verify-and-commit` subcommand as the batch progression gate mechanism, but no step in the plan implements this flag and it does not exist in the current `manage_state.py`. The batch progression gate — the core structural enforcement for the 9x incremental commit+push regression (V14-V24) — depends on a flag that will not exist after build. -> Add an implementation step (between Steps 15 and 16) to add `--check-only` to the `verify-and-commit` argparse registration and handler logic (check git status for uncommitted output files, exit non-zero without committing), with at least one test confirming behavior.

### Recommended Changes
- [x] **[Conf: 78] [architecture-strategist]** [ipc-contract] manage_state.py dual-copy sync enforcement relies on byte-identical comparison (`test_manage_state_sync.py`), but no CI pipeline or pre-commit hook runs this test automatically. The sync enforcement is advisory only. -> Add a pre-commit hook or Makefile target that runs `test_manage_state_sync.py` before any commit touching `manage_state.py`. Alternatively, consider eliminating the dual-copy entirely by symlinking.
- [x] **[Conf: 78] [code-simplicity-reviewer]** `test_verify_before_archive.py` (Step 5) still manually constructs job dicts inline instead of using `make_valid_job` from conftest.py, despite the conftest consolidation directive. -> Replace all inline job dicts in `test_verify_before_archive.py` with `make_valid_job(...)` calls, matching the pattern used in other test files.
- [x] **[Conf: 78] [regression-checker]** V23 Haiku scoring regression: Step 25 (IF11) covers data reads tier but not scoring itself — search-verify agents performing profile-matching scoring could still be dispatched at Haiku tier. -> Add explicit text to Step 25 or a CLAUDE.md constraint: "Search-verify subagents that perform profile-matching scoring MUST use Sonnet tier minimum."
- [x] **[Conf: 75] [architecture-strategist]** [ipc-contract] preflight.sh also has a dual-copy pattern (Step 31) but unlike manage_state.py there is NO `test_preflight_sync.py` to enforce byte-identity. Sync enforcement is asymmetric. -> Add a `test_preflight_sync.py` mirroring `test_manage_state_sync.py`. (overlaps with regression-checker Recommended #3)
- [x] **[Conf: 75] [code-simplicity-reviewer]** `test_safety_bound_gap.py` (Step 11) defines its own `_make_jobs_and_archive` helper with ad-hoc keys instead of using conftest's `make_valid_job`. Second instance of fixture-duplication pattern. -> Refactor to use `make_valid_job` from conftest for the base job dict.
- [x] **[Conf: 75] [regression-checker]** V25 expired-jobs-in-rankings regression: `validate-presentation` is wired in orchestration.md (Step 19) but not as a CLAUDE.md hard constraint. If the agent doesn't read orchestration.md, the gate is missed. -> Add a HC entry in CLAUDE.md requiring `validate-presentation` to pass before any user-facing output.
- [x] **[Conf: 72] [architecture-strategist]** [configuration] `_check_safety_bound` gap detection (Step 12) silently falls back to default 50% threshold when called outside CLI entrypoint because `last_run_date`/`today` default to None. -> Add a test exercising the default-args path, or have `_check_safety_bound` read `state.json` itself as fallback.
- [x] **[Conf: 72] [code-simplicity-reviewer]** Steps 34-35 (Phase 5) still exist as separate steps despite Round 1 recommendation to merge into Step 32. The /revise added a disclaimer but kept both steps. Step 35 is often a no-op. -> Fold Step 34's commands into Step 32 and remove Step 35 entirely.
- [x] **[Conf: 72] [regression-checker]** Step 31 mirrors preflight.sh to career-matching but unlike manage_state.py (which gets `test_manage_state_sync.py`), there is no test enforcing preflight.sh byte-identity. Sync enforcement is incomplete. (overlaps with architecture-strategist Recommended #2)
- [x] **[Conf: 71] [architecture-strategist]** [data-integrity] `verify-before-archive` uses HTTP HEAD with `allow_redirects=True`. Some ATS systems redirect expired listings to generic "no longer accepting" pages returning HTTP 200. Source redirect-to-generic-page case is not handled. -> Add a check: if source URL returns 200 after redirect and final URL domain/path root changed significantly, flag as "unverified-redirect" rather than "live".

### Nice-to-Have
- [x] **[Conf: 70] [architecture-strategist]** Step 35 uses `git add -A 03_agents/tests/v25/ 03_agents/career-matching/` which could sweep in unintended files. Earlier commits correctly enumerate specific files. -> Replace with explicit file list or add `git diff --cached --name-only` verification step.
- [x] **[Conf: 70] [code-simplicity-reviewer]** `_is_specific_job_url` (Step 8) maintains its own `_GENERIC_CAREER_PATTERNS` list alongside `classify_url`. The delegation to `classify_url` at the top handles the common case, but the fallback path still uses three parallel classification strategies. -> Flag for future cleanup if the unknown-URL heuristics grow.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** The source-first strategy for aggregator URLs (V25 regression fix) is well-addressed in Steps 5-6. Enforcement depends on the agent following the orchestration doc — no structural prevention of bypassing the gate. (Conf: 65)
- **[architecture-strategist]** `verify-session-state-written` (Step 15) checks file existence and content grep for run_date, but does not validate that session-state was written *after* the most recent search batch. A stale session-state from a previous run with the same date would pass. (Conf: 55)
- **[code-simplicity-reviewer]** Phase 3 grep-count verification (Steps 18-25) is inherently fragile. The /revise improved sentinel path grep patterns to use path-like patterns, partially addressing the concern. (Conf: 55)
- **[code-simplicity-reviewer]** Step count (35) is appropriate for the scope after /revise removed the old no-op. (Conf: 50)
- **[regression-checker]** V24 "ux-cli" regressions (status table reprinted 8 times, no proactive status, no visual separators) are out of scope for this infrastructure-focused plan. Not a regression introduction. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: Needs Changes

### Statistics
- Total findings collected: 16
- Final actionable findings: 13 (1 Required, 10 Recommended, 2 Nice-to-Have)

---

## Round 1 — 2026-03-23

### Reviewers Active
architecture-strategist, code-simplicity-reviewer, regression-checker

### Required Changes
- [x] **[Conf: 95] [architecture-strategist]** [verification] verify-before-archive uses HTTP HEAD only, which does not follow the source-first verification strategy from V25 regression. Aggregator pages (StudySmarter, Indeed) return HTTP 200 for expired listings. The V25 regression explicitly states: "Liveness verification must follow source-first strategy." HTTP HEAD to an aggregator URL will return 200 even when the job is expired (V25 confirmed this with Linda AI via StudySmarter). -> verify-before-archive must classify the URL via validate-url-type first. If the URL is an aggregator, it must either (a) attempt to find and verify the source ATS URL, or (b) return status="unverified" instead of "live". Only source URLs should produce a definitive "live" status from HTTP HEAD alone.
- [x] **[Conf: 92] [architecture-strategist]** [ipc-contract] manage_state.py is maintained as two identical copies (`03_agents/tests/v25/scripts/` and `03_agents/career-matching/scripts/`). Steps 3, 15, and 31 say "apply identical changes" and verify with diff, but there is no automated enforcement — it relies on the builder remembering to copy. -> Either symlink career-matching's manage_state.py to the v25 copy, or add a CI step / test that asserts the two files are byte-identical. Add a comment in both files referencing the canonical source. (overlaps with code-simplicity-reviewer Required #1 below)
- [x] **[Conf: 90] [architecture-strategist]** [data-integrity] verify-before-archive writes active_status back to the JSON file as a side effect of checking liveness (Step 6). If the HTTP HEAD check is wrong (confirmed in V25: aggregator returned 200 for expired listing), the file is now silently corrupted with incorrect status. -> Separate the "check" from the "write". Return the verdict without modifying the file. Add a separate `--write` flag or a distinct `mark-expired` subcommand that requires explicit confirmation before mutating the file.
- [x] **[Conf: 85] [code-simplicity-reviewer]** Steps 3/15/31 are copy-paste mirror steps with no logic — they duplicate manage_state.py and preflight.sh to career-matching with "apply identical changes" and a diff check. This doubles the maintenance surface and risks drift. -> Extract manage_state.py and preflight.sh into a shared location (e.g., `shared/scripts/`) and symlink or import from both agents. If that is out of scope for V26, at a minimum add a CI check that diffs the two copies and fails on mismatch. (overlaps with architecture-strategist Required #2 above)
- [x] **[Conf: 82] [code-simplicity-reviewer]** Step 22 is a no-op placeholder ("No file changes in this step — it's a dependency marker for Phase 4"). Empty steps add noise and break the principle that each step produces a verifiable change. -> Delete Step 22 entirely and add a note to Step 28 that it fulfills the IF5 requirement. Renumber subsequent steps.

### Recommended Changes
- [x] **[Conf: 78] [architecture-strategist]** [configuration] The `_is_specific_job_url` function (Step 8) returns False for unknown domains without a 4+ digit or UUID path segment, even if they are legitimate company career subdomains (e.g., `https://careers.stripe.com/listing/senior-engineer`). -> Add a heuristic for path depth (>2 segments after domain) or allow an allowlist of known company career domains in a configuration file.
- [x] **[Conf: 78] [regression-checker]** Session-state.md structural enforcement gate (V14-V24, 10th occurrence) — the plan references a `verify-session-state-written` gate in orchestration.md (Step 17), but the subcommand is never implemented in manage_state.py. The gate calls a subcommand that does not exist. -> Add a step to implement `verify-session-state-written` in manage_state.py with a corresponding test, or change the gate to use an existing mechanism.
- [x] **[Conf: 78] [code-simplicity-reviewer]** `_make_valid_job` helper is duplicated across 4+ test files (Steps 1, 5, 7, 9, 14, 30) with slight variations. When the schema changes, 4+ fixtures need updating. -> Extract a shared `conftest.py` fixture with `_make_valid_job` and `_write_job` helpers.
- [x] **[Conf: 76] [code-simplicity-reviewer]** `test_gate_chains.py` (Step 30) duplicates tests already covered in `test_validate_presentation.py` (Step 7) — specifically `test_generic_url_fails` and `test_valid_url_passes` are near-identical. -> Remove duplicated tests from `test_gate_chains.py` and keep only the verify-and-commit gate test that exercises unique behavior.
- [x] **[Conf: 75] [architecture-strategist]** [configuration] Preflight sentinel path validation (Step 29) uses grep count to check for `_status.json` and `_summary.md` references. This is fragile — breaks if documentation uses different casing or backtick-wrapped references. -> Use a more specific pattern or maintain a separate sentinel registry file that preflight validates against.
- [x] **[Conf: 75] [regression-checker]** Post-batch commit gate structural enforcement (V14-V24, 9th occurrence) — Step 17 references `verify-and-commit --phase-label search` but adds no NEW structural mechanism that blocks next-batch dispatch until commit completes. Documented constraints have failed 9 times. -> Add a Python-level gate in manage_state.py (e.g., `verify-batch-committed` that checks git status for uncommitted output files and exits non-zero).
- [x] **[Conf: 75] [code-simplicity-reviewer]** Steps 34-35 (Phase 5) repeat the exact same verification commands already run incrementally in Steps 1-16. -> Merge Steps 34-35 into Step 32 ("Run full test suite") and note that it is a final sanity check only.
- [x] **[Conf: 72] [architecture-strategist]** [interaction] The plan adds 3 new manage_state.py subcommands and modifies 2, but does not verify that existing subcommands still produce the same output format after modifications. -> Add a regression test that runs validate-schema against a known-good fixture file and asserts unchanged output for pre-existing validation rules.
- [x] **[Conf: 72] [regression-checker]** .done sentinel path hardcoding in dispatch variables (V14-V25, 5th occurrence) — Step 21 clarifies sentinel types in documentation but does not hardcode the path in dispatch variables template. -> Add sentinel path as a mandatory dispatch variable (e.g., `sentinel_path: "{working_dir}/output/.channels/{channel_name}.done"`).
- [x] **[Conf: 72] [code-simplicity-reviewer]** `verify-before-archive` uses HTTP HEAD for liveness, but V25 regressions document aggregator unreliability. HTTP HEAD is even less reliable than Playwright for aggregator-hosted expired listings. -> Document the known limitation and consider adding `classify_url` check to skip HTTP verification for aggregator URLs. (overlaps with architecture-strategist Required #1)
- [x] **[Conf: 70] [regression-checker]** HC10 mandatory dispatch variable checklist (V23/V24) — the plan does not add working_dir, output_directory, or dashboard_url as mandatory dispatch variables. -> Add a step to update the dispatch template with mandatory variables and a preflight or gate-check that validates their presence.

### Nice-to-Have
- [x] **[Conf: 70] [architecture-strategist]** [configuration] The `requests` import uses a try/except fallback to `None` (Step 6). If requests is not installed, verify-before-archive raises ImportError at runtime. Preflight.sh does not check for the requests dependency. -> Add `python3 -c "import requests"` to preflight.sh dependency checks.
- [x] **[Conf: 70] [code-simplicity-reviewer]** The `_GENERIC_CAREER_PATTERNS` list (Step 8) and `_is_specific_job_url` have overlapping logic with `classify_url` (Step 2). Two parallel URL-knowledge systems must stay in sync. -> Consider having `_is_specific_job_url` delegate entirely to `classify_url` and remove the redundant generic pattern list.
- [ ] **[Conf: 65] [regression-checker]** The plan does not add a session resume guard (V22 regression) — checking `_status.json` for `sent_at` matching today before re-initializing. -> Add a preflight check that reads `_status.json` and surfaces resume-or-abort if `sent_at` matches today.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** The plan resolves the foreground/background contradiction (Step 20, IF4) by switching to "background dispatch with sequential gate enforcement." Architecturally sound but depends on the parent reliably blocking on gate-checks after background completion notifications — a behavioral constraint, not structural. Worth monitoring. (Conf: 60)
- **[architecture-strategist]** Step 36 uses `git add -A 03_agents/tests/v25/ 03_agents/career-matching/` which could sweep in unintended files. Narrow to specific paths. (Conf: 55)
- **[code-simplicity-reviewer]** Step 36 uses `git add -A` on broad directories which could accidentally stage unrelated changes. Per project conventions, prefer explicit file listing. (Conf: 65)
- **[code-simplicity-reviewer]** The plan has 36 steps across 5 phases for 3 new CLI subcommands, 2 enhancements, 2 bug fixes, and documentation updates. Well-structured but may be over-granular — several test-then-implement pairs could each be a single step. (Conf: 55)
- **[code-simplicity-reviewer]** Phase 3 (Steps 17-26) is entirely documentation changes with grep-count verification. The verification is fragile — counting occurrences with `grep -c` doesn't verify correctness, only presence. (Conf: 58)
- **[regression-checker]** Many V14-V19 regressions (PDF generation, hyperlink colors, digest scoring, email formatting) are out of scope for this infrastructure-focused plan and are not violated by it. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: Needs Changes
- code-simplicity-reviewer: Needs Changes
- regression-checker: Needs Changes

### Statistics
- Total findings collected: 22
- Final actionable findings: 18 (5 Required, 11 Recommended, 3 Nice-to-Have, minus 1 Nice-to-Have below threshold moved from regression-checker)

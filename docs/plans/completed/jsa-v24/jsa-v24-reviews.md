# JSA V24 Reviews

## Round 2 — 2026-02-25

### Reviewers Active
architecture-strategist, code-simplicity-reviewer, regression-checker

### Required Changes
None.

### Recommended Changes
- [x] **[Conf: 75] [regression-checker]** Background subagent `background: true` deferral is documented in Step 13 note but not in the Handoff Contract's "Known out-of-scope regression" section. Next version's delta-mode /research won't pick it up. -> Add `background: true` permission failures to the Handoff Contract's known out-of-scope list alongside send_email.py.
- [x] **[Conf: 74] [architecture-strategist]** Step 28 explicit file list includes `output/verified/` and `output/archive/` as git-added paths. These are data directories that grow unboundedly. Committing them alongside code changes conflates code artifacts with runtime data, making `git revert` revert data mutations too. -> Move `output/verified/` and `output/archive/` to a separate data-only commit (Step 27.5) or exclude from code commits entirely.
- [x] **[Conf: 72] [architecture-strategist]** `_check_safety_bound` only runs in `auto_scope` mode. Explicit `--role-types` mode has no safety net against mass-archive scenarios. -> Apply safety bound check unconditionally (or add `--no-safety-bound` opt-out flag).
- [x] **[Conf: 72] [code-simplicity-reviewer]** Step 1 embeds the full `tests/helpers.py` source as a comment block inside `test_manage_state.py` rather than its own step. Confusing for build execution. -> Move `tests/helpers.py` creation to its own explicit Step 0 or Step 1a with a proper code block.
- [x] **[Conf: 70] [architecture-strategist, code-simplicity-reviewer]** `SCHEMA_FIELD_DEFAULTS` (Step 10) is a pure alias for `CANONICAL_FIELD_DEFAULTS` with no transformation. Two names for the same object adds unnecessary indirection. -> Remove the alias; use `CANONICAL_FIELD_DEFAULTS` directly in `_migrate_one_file`. (overlaps between architecture-strategist and code-simplicity-reviewer)

### Nice-to-Have
None. (Two findings at Conf 68 moved to Reviewer Notes as informational.)

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** `run_date` comparison in `_derive_active_role_types` uses exact string match. Non-zero-padded dates (e.g. "2026-2-25") would cause misclassification. Consider enforcing ISO 8601 in Output Schema Contract. (Conf: 68)
- **[code-simplicity-reviewer]** `_write_verified_json` in Step 23's `test_workflow.py` duplicates `_write_job` from `tests/helpers.py`. Consider using `_write_job` instead. (Conf: 68)
- **[architecture-strategist]** Deployment Verification runs `manage_state.py` from shell commands — these are manual reference steps, not parent-orchestrated dispatches, so Context Budget is not violated. (Conf: 55)
- **[architecture-strategist]** Rollback plan uses `git revert HEAD --no-edit` which only reverts one commit. If all 3 layer commits pushed, rollback requires reverting 3 commits. (Conf: 52)
- **[architecture-strategist]** Plan scopes deployment verification to `03_agents/tests/v23/` but plan is V24 — presumably V24 code lives in V23 directory (patch, not new version directory). (Conf: 58)
- **[code-simplicity-reviewer]** Deployment Verification shell snippets could be misinterpreted as parent-context steps. Worth noting distinction for clarity. (Conf: 55)
- **[regression-checker]** Plan is intentionally narrow-scoped. Many regression items legitimately out of scope. All Round 1 regression-checker findings were adequately addressed. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: APPROVED

### Statistics
- Total findings collected: 12
- Final actionable findings: 5 (0 Required, 5 Recommended, 0 Nice-to-Have)

---

## Round 1 — 2026-02-25

### Reviewers Active
architecture-strategist, code-simplicity-reviewer, regression-checker

### Required Changes
- [x] **[Conf: 95] [architecture-strategist]** Plan lacks explicit "Context Budget" section. V18 regression mandates parent must NEVER execute manage_state.py directly, but Step 27 runs migration+validation from parent. -> Add a "Context Budget" section specifying: (1) parent may only read status files and dispatch subagents, (2) all manage_state.py invocations are subagent-delegated, (3) Step 27 must dispatch a subagent to run migration+validation.
- [x] **[Conf: 92] [architecture-strategist]** HC10 violated — new gate-check dispatches in Schema Validation Gate (Step 15) don't specify mandatory variables (working_dir, output_directory, dashboard_url). -> Add mandatory dispatch variables to the Schema Validation Gate specification in Step 15 per HC10. (overlaps with regression-checker Recommended #3 below)
- [x] **[Conf: 90] [architecture-strategist]** `REQUIRED_SCHEMA_FIELDS` duplicated in 3 locations (validate-schema in manage_state.py, `REQUIRED_FIELDS` in tests, `SCHEMA_FIELD_DEFAULTS` keys in migrate-schema). Will drift without single source of truth. -> Define canonical field list once as module-level constant in manage_state.py (`CANONICAL_FIELDS`), import in tests, derive `SCHEMA_FIELD_DEFAULTS` keys from it.
- [x] **[Conf: 88] [architecture-strategist]** Step 28 uses `git add -A` risking commit of gitignored files (settings.local.json, .playwright-mcp logs). V21 regression prohibits this. -> Replace `git add -A` in Step 28 with explicit file list matching Handoff Contract's "Files modified" section. (overlaps with regression-checker Nice-to-Have below)
- [x] **[Conf: 82] [code-simplicity-reviewer]** Four duplicate test helper factories (`_make_valid_job`, `_make_job_with_score_field`, `_make_canonical_job`, `_make_verified_json`) across test files construct nearly identical verified JSON dicts. Maintenance burden when schema changes. -> Extract single `_make_job(**overrides)` factory into shared `tests/conftest.py` or `tests/helpers.py`.
- [x] **[Conf: 78] [code-simplicity-reviewer]** Steps 23-24 in `test_workflow.py` duplicate test logic already covered by unit tests in Steps 1-6. `test_validate_schema_catches_bad_output` duplicates `test_validate_schema_missing_field`; `test_dedup_safety_bound_prevents_mass_archive` duplicates `test_dedup_safety_bound_aborts`. -> Remove duplicate unit-level assertions from integration tests. Keep only integration-specific chained test (`test_dedup_after_validation_uses_canonical_score`).

### Recommended Changes
- [x] **[Conf: 80] [regression-checker]** Agent-memory startup read (HC4) not addressed — 3-version recurrence (V14/V17/V19). V24 doesn't define startup sequence, orchestration.md changes don't add agent-memory read step. -> Add note in orchestration.md changes (Step 15) or search-verify prompt (Step 14) that startup must include reading agent-memory files, or confirm already present and unchanged.
- [x] **[Conf: 78] [architecture-strategist]** `_extract_score()` silently returns 0 for missing/invalid scores. Callers treat 0 as valid low score, archiving the job. If migration hasn't run, legitimate high-scoring legacy files get archived with no error signal. -> Have `_extract_score()` raise ValueError or return sentinel when score missing/non-int, or make validate-schema a hard prerequisite of dedup enforced in CLI.
- [x] **[Conf: 78] [regression-checker]** `send_email.py --body-file` vs `--html` regression (V21/V23) not acknowledged even as out-of-scope. -> Add note to Handoff Contract that send_email.py CLI interface correctness is not addressed and remains known regression.
- [x] **[Conf: 75] [architecture-strategist]** Inconsistent CLI flag naming: orchestration.md Step 15 uses `--verified-dir` but Step 2 implements `--output-dir`. -> Fix orchestration.md to use `--output-dir` consistently.
- [x] **[Conf: 72] [architecture-strategist]** 10-field canonical schema hardcoded in 4+ locations. Adding 11th field requires modifying manage_state.py, tests, subagent-search-verify.md, and orchestration.md. -> Consider single `CANONICAL_SCHEMA` dict in manage_state.py that all consumers reference, document extension procedure.
- [x] **[Conf: 72] [code-simplicity-reviewer]** `_run_dedup_autoscope` (Step 5) and `_run_dedup` (Step 3) are separate helpers calling same script with slightly different flags. Doesn't scale. -> Use single `_run_dedup(output_dir, *, role_types=None, auto_scope=False, run_date=None, dry_run=False)` helper with optional kwargs.
- [x] **[Conf: 72] [regression-checker]** Background subagent permission failures (V20-V23, 8-version recurrence). Search-verify agent promoted to Sonnet still has `background: true` — V23 regression mandates removing background dispatch entirely. -> Confirm whether Step 13 should change `background: true` to `background: false`, or document deferral.
- [x] **[Conf: 70] [code-simplicity-reviewer]** Step 17 (`test_search_verify_model_is_sonnet`) is pytest-level config grep test that duplicates Step 21's preflight.sh runtime check. -> Consider removing pytest config grep and relying on preflight.sh, or acknowledge redundancy.

### Nice-to-Have
- [ ] **[Conf: 68] [code-simplicity-reviewer]** `_slugify` fix in Step 8 adds `re.sub(r"-{2,}", "-", slug)` but preceding `re.sub(r"[^a-z0-9]+", "-", slug)` with `+` quantifier may already handle all cases. -> Verify whether double-collapse regex is actually needed with test inputs.
- [x] **[Conf: 65] [regression-checker]** Step 28 `git add -A` could stage sensitive files. -> Replace with explicit file list. (overlaps with architecture-strategist Required #4 above — applied via Required #4)
- [ ] **[Conf: 65] [code-simplicity-reviewer]** Step 21 preflight.sh uses `$RUN_ENV` guard but plan doesn't specify what sets this variable. -> Add one-line note clarifying when `RUN_ENV=true` is set.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** Step 15 shows nested markdown code fences (triple-backtick inside triple-backtick) which may cause rendering issues. (Conf: 55)
- **[architecture-strategist]** Safety bound percentage (50%) is a magic number with no configuration path. (Conf: 58)
- **[architecture-strategist]** `_derive_active_role_types` reads every JSON file in every role directory — O(files) on every dedup. Unlikely issue at current scale. (Conf: 52)
- **[code-simplicity-reviewer]** Three-layer decomposition is clean and well-scoped with clear commit boundaries. (Conf: 55)
- **[code-simplicity-reviewer]** 28 steps for a "targeted patch" is on the higher end, but each step is small/atomic with TDD red-green pattern. Defensible for 8+ versions of schema drift. (Conf: 52)
- **[code-simplicity-reviewer]** `_migrate_one_file` score normalization handles 4 legacy paths — inherent complexity from schema drift, not over-engineering. (Conf: 50)
- **[regression-checker]** Plan is intentionally narrow-scoped. Many regression items legitimately out of scope: PDF generation, digest email styling, brief speed, preview.sh, Vercel deployment, GitHub Actions, settings.local.json bloat, CR4. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: Needs Changes
- code-simplicity-reviewer: Needs Changes
- regression-checker: APPROVED

### Statistics
- Total findings collected: 20
- Final actionable findings: 17 (6 Required, 8 Recommended, 3 Nice-to-Have)

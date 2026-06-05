# JSA V25 Reviews

## Round 3 — 2026-03-02

### Reviewers Active
architecture-strategist, code-simplicity-reviewer, regression-checker, ux-reviewer

### Required Changes
None.

### Recommended Changes
- [x] **[Conf: 75] [architecture-strategist]** `send_email.py` is invoked directly by the parent in Phase 5 Tier 1 Step 3, but the Context Budget section in CLAUDE.md only lists `manage_state.py` and `preflight.sh` as parent-allowed script executions. Latent HC-5 violation. -> Add `send_email.py` explicitly to the Context Budget parent-allowed list in CLAUDE.md, or convert Step 3 to a subagent dispatch with HC-10 variables.
- [x] **[Conf: 75] [ux-reviewer]** Session resume prompt (Step 23) lacks a prescribed format in the UX Protocol. The prompt wording is inline prose in ON STARTUP, not codified as a UX Protocol rule with a standardized template. -> Add a 7th UX Protocol rule for session resume messaging with exact format string: `"A digest was already sent today ({sent_at}). Resume this session or abort? (resume/abort)"`.
- [x] **[Conf: 73] [code-simplicity-reviewer]** `_read_dispatch_count` (Step 21) uses a 12-line stateful line-by-line parser while `_write_dispatch_count` uses regex. Asymmetric. -> Replace with 2-line regex: `m = re.search(r'dispatch_count:\s*(\d+)', content); return int(m.group(1)) if m else 0`.
- [x] **[Conf: 72] [architecture-strategist]** Vercel deploy dispatch fires "after every successful git push" including per-channel commit gate pushes. With 5 channels, this triggers up to 5 Vercel deploys during Phase 1 alone. -> Scope mandatory Vercel deploy to fire once after Phase 1's final channel commit gate (or after Phase 5 send), not after every individual push.
- [x] **[Conf: 72] [ux-reviewer]** Verify-and-commit raw stderr surfaces to user during gate failures but does not follow `[GATE FAILED]` alert format. -> Add note in gate-check dispatch (Step 15) that the parent MUST reformat exit-code-1/2 output into `[GATE FAILED] {gate-name} — {reason}. Action: {next}.` format before displaying.
- [x] **[Conf: 70] [code-simplicity-reviewer]** Step 23 prescribes 6 separate additions across two files as a single step. Builder will struggle to apply atomically. -> Split Step 23 into 2 steps: (a) CLAUDE.md startup + core rules, (b) orchestration.md constraint compliance additions.
- [x] **[Conf: 70] [ux-reviewer]** No end-of-session completion summary format defined. -> Add completion summary format to UX Protocol: `"Session complete: {N} new jobs found, {M} briefs generated, digest sent to {email}."`.

### Nice-to-Have
- [ ] **[Conf: 68] [architecture-strategist]** `_get_active_role_types` helper (Step 11b) lacks concrete code snippet showing refactored delegation. -> Provide code diff showing `_cli_list_active_role_types` delegating to `_get_active_role_types`.
- [ ] **[Conf: 68] [ux-reviewer]** Post-compaction recovery (Step 22) only provides one example status line. -> Add 1-2 more example templates for mid-brief and mid-delivery compaction points.
- [ ] **[Conf: 68] [code-simplicity-reviewer]** `_extract_section` in test_orchestration.py is over-generic for its single use case. -> Simplify to direct index-based slice or inline it.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** Three-layer architecture remains sound after two revision rounds. Dependency direction correct, no circular dependencies. (Conf: 55)
- **[architecture-strategist]** Vercel deploy frequency is the only new architectural issue introduced by R2 revisions. (Conf: 60)
- **[code-simplicity-reviewer]** R2 revisions cleaned up main complexity issues: verify-session-state 2-tier, dedup internal helper, --check-session-state removal. (Conf: 55)
- **[code-simplicity-reviewer]** Step count at ~27 is reasonable. No further merges obvious. (Conf: 50)
- **[code-simplicity-reviewer]** 4-class consolidation in test_orchestration.py well-organized. (Conf: 52)
- **[code-simplicity-reviewer]** `import re` inside `_write_dispatch_count` remains unfixed from R2 Nice-to-Have. (Conf: 65)
- **[regression-checker]** All regression items from V14-V24 are covered after three rounds. Zero violations. (Conf: 60)
- **[regression-checker]** Preflight partial matches sidestepped by rewrite (ambiguous but low-risk). (Conf: 55)
- **[regression-checker]** CI preflight SCHEDULED_RUN skip — deployment-time concern, likely in v24 codebase copy. (Conf: 55)
- **[ux-reviewer]** R2 timed status, gate failure format, CR-4, and tier-skip findings all adequately addressed. (Conf: 60)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: APPROVED
- ux-reviewer: APPROVED

### Statistics
- Total findings collected: 7 Recommended + 3 Nice-to-Have + 10 informational
- Final actionable findings: 10 (0 Required, 7 Recommended, 3 Nice-to-Have)
- Note: All 4 reviewers APPROVED — zero Required changes, findings are incremental improvements

---

## Round 2 — 2026-03-02

### Reviewers Active
architecture-strategist, code-simplicity-reviewer, regression-checker, ux-reviewer

### Required Changes
None.

### Recommended Changes
- [x] **[Conf: 78] [architecture-strategist]** Gate-check and recovery dispatch templates (Steps 15, 22) do not include all three HC-10 mandatory variables in their prompt JSON. The channel dispatch shows HC-10 vars for search-verify, but verify-and-commit gate-check dispatch template is a bare bash command with no Task tool prompt JSON containing `working_dir`, `output_directory`, `dashboard_url`. Step 23 mentions "HC-10 audit" as prose but provides no concrete template. -> Add explicit Task tool prompt JSON for every gate-check and recovery dispatch in orchestration.md, each containing all three HC-10 mandatory variables. Convert Step 23 prose audit into concrete templates.
- [x] **[Conf: 75] [regression-checker]** V21/V22 regression: Vercel dashboard must be redeployed after data push as a mandatory orchestration step. No `vercel link` or `vercel --prod` command appears anywhere in orchestration.md or the tiered delivery sequence. -> Add a mandatory post-push Vercel deploy step to orchestration.md (e.g., after Phase 1 commit gate or Phase 5 send), dispatching a subagent to run `vercel link --project jsa-dashboard --yes && vercel --prod --yes`.
- [x] **[Conf: 75] [architecture-strategist]** Non-fast-forward push rejection handling missing: `verify-and-commit` treats all push failures identically as transient retries. -> Add a distinct handling path for non-fast-forward rejection (attempt `git pull --ff-only` before retry), or document that the gate-check retry should attempt pull before retrying push.
- [x] **[Conf: 75] [code-simplicity-reviewer]** `verify-session-state-written` has a 4-tier fallback chain that ultimately matches the date as a plain substring anywhere in the file, making earlier tiers dead code. -> Simplify to: check for `## {date}` heading OR plain string match. Remove intermediate tiers (field match, section-scoped match).
- [x] **[Conf: 75] [ux-reviewer]** UX Protocol rule 2 (Proactive Timed Status) lacks enforcement mechanism — says "emit after 90 seconds" but Claude Code has no timer primitive. -> Add concrete implementation note: "Parent counts tool-call round-trips as proxy. After ~3 consecutive subagent dispatches or gate-checks with no user-visible output, emit the timed status line."
- [x] **[Conf: 72] [architecture-strategist, code-simplicity-reviewer]** `--check-session-state` and `--run-date` flags on `verify-and-commit` couple two independent verification concerns into a single CLI invocation. The orchestration already runs both gates as independent sequential dispatches. -> Remove `--check-session-state` and `--run-date` from `verify-and-commit` to maintain single responsibility. (overlaps with code-simplicity-reviewer finding below)
- [x] **[Conf: 72] [regression-checker]** V23 regression: CR-4 one-question-at-a-time rule violated. The UX Protocol defines 5 rules but does not include this constraint. -> Add a 6th UX Protocol rule: "Ask one question per message. Never combine multiple questions in a single user-facing message (CR-4)."
- [x] **[Conf: 72] [code-simplicity-reviewer]** Step 11b dedup `--active-only` calls back into `manage_state.py list-active-role-types` via `subprocess.run`, spawning a child Python process from within a Python process. -> Call the internal function directly (factor out `_get_active_role_types(context_path)` helper) instead of shelling out to self.
- [x] **[Conf: 72] [ux-reviewer]** No error message templates for gate failures surfaced to user. Gate exit codes are defined but no user-facing message format is prescribed. -> Add to UX Protocol: "Gate failure alert format: `[GATE FAILED] {gate-name} — {reason}. Action: {what happens next}.`"
- [x] **[Conf: 70] [regression-checker]** V23 regression: `list-active-role-types` produced full-sentence slugs. Step 24 validates slug count but not slug format. -> Add slug format assertion (regex `^[a-z0-9-]+$` per line) to the validation step, or add a test in test_manage_state.py.
- [x] **[Conf: 70] [ux-reviewer]** Tiered delivery skip notification is silent from user perspective. When briefs-html is deferred due to budget exhaustion (Step 6), only session-state.md is updated. -> Add a user-facing message when Tier 2 is skipped: "Briefs HTML deferred — dispatch budget reached. Will generate next session."

### Nice-to-Have
- [ ] **[Conf: 68] [ux-reviewer]** Startup decision prompts lack standardized format. Plan says `prompt user: "A digest was already sent today..."` but no UX Protocol rule standardizes decision-prompt formatting. -> Consider adding UX Protocol rule: "Decision prompts: present situation in one sentence, then options as a numbered list."
- [ ] **[Conf: 65] [architecture-strategist, code-simplicity-reviewer]** `_write_dispatch_count` imports `re` inside the function body rather than at module top level — inconsistent with module style. -> Move `import re` to module-level imports.
- [ ] **[Conf: 65] [ux-reviewer]** Post-compaction recovery (Step 22) mandates a 1-2 sentence status summary but only provides one example style. Different compaction points would benefit from 2-3 example templates. -> Add example templates for mid-delivery and mid-brief-generation compaction.

### Reviewer Notes (informational only, no action)
- **[code-simplicity-reviewer]** Merged TDD steps (test + implementation in single steps for sentinel/schema in Steps 8-9) are a good simplification from Round 1. (Conf: 55)
- **[code-simplicity-reviewer]** Dispatch counter now uses regex-replace approach per Round 1 feedback. Clean implementation. (Conf: 52)
- **[code-simplicity-reviewer]** 4 consolidated test classes in test_orchestration.py well-organized. Good structural improvement. (Conf: 55)
- **[code-simplicity-reviewer]** Step count reduced from 31 to ~27 with verify+commit merges. Acceptable. (Conf: 50)
- **[architecture-strategist]** `_extract_section` helper uses heading-level matching that could false-match sub-headings. Low risk since test data is controlled. (Conf: 55)
- **[architecture-strategist]** Dedup `--active-only` calls `list-active-role-types` via subprocess — architecturally clean (CLI contract preserved) but adds process overhead. (Conf: 52)
- **[regression-checker]** Preflight structural greps with partial matches — not explicitly addressed but plan rewrites preflight schema tier block which may sidestep the issue. (Conf: 55)
- **[ux-reviewer]** Five UX Protocol rules directly address all five V24 ux-cli regressions. Well-targeted. (Conf: 60)
- **[ux-reviewer]** Post-compaction recovery includes "State absolute file paths" sub-section, satisfying CR-7. Good coverage. (Conf: 55)
- **[ux-reviewer]** No end-of-session completion summary format defined (e.g., "Session complete: X jobs found, Y briefs generated"). Not a regression but would improve closure UX. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: Needs Changes
- ux-reviewer: APPROVED

### Statistics
- Total findings collected: 12 actionable (Recommended) + 3 Nice-to-Have + 10 informational
- Final actionable findings: 12 (0 Required, 11 Recommended, 3 Nice-to-Have — after dedup: 0 Required, 11 Recommended, 3 Nice-to-Have)
- Note: 1 finding overlaps between architecture-strategist and code-simplicity-reviewer (--check-session-state removal)

---

## Round 1 — 2026-03-02

### Reviewers Active
architecture-strategist, code-simplicity-reviewer, regression-checker

### Required Changes
- [x] **[Conf: 97] [regression-checker]** Session resume guard missing (V22): No startup check for `output/digests/_status.json` with `sent_at` matching today to surface a resume-or-abort prompt. -> Add a startup step that reads `_status.json` and prompts the user if `sent_at` matches today's date before re-initializing.
- [x] **[Conf: 96] [regression-checker]** Agent memory read on startup missing (V14/V17/V19 — 3-version recurrence): ON STARTUP sequence does not include explicit step to read `.claude/agent-memory/*/MEMORY.md` per HC4. -> Add explicit startup step: "Read `.claude/agent-memory/*/MEMORY.md` and treat documented failures as hard constraints."
- [x] **[Conf: 95] [architecture-strategist]** Missing explicit Context Budget boundary (V18 HC5): Plan adds `list-active-role-types` to parent-allowed list but never defines the full context budget (parent-allowed vs subagent-only tools). -> Add a "Context Budget" section to CLAUDE.md enumerating parent-allowed tools (manage_state.py subcommands, preflight.sh, git) vs subagent-only tools (WebFetch, WebSearch, search, filter, dedup, source file reads).
- [x] **[Conf: 95] [regression-checker]** No `model:` parameter check in dispatch templates (V19 HC1): Step 15 gate-check dispatch says `(model: haiku)` in prose — orchestration.md dispatch blocks must never include `model:` as a Task tool parameter. -> Verify actual Task tool dispatch blocks do not include `model:` parameter; remove or clarify `(model: haiku)` notation.
- [x] **[Conf: 95] [regression-checker]** Parent script execution ambiguity (V19): Step 23 adds `list-active-role-types` to parent-allowed subcommands but V19 regression says parent must NEVER run `python3 scripts/*` directly. -> Clarify that `manage_state.py` CLI subcommands are explicitly parent-allowed exceptions per existing context budget rules.
- [x] **[Conf: 95] [regression-checker]** Subagent absolute working directory missing from dispatch prompts (V19): Templates show `working_dir` but don't enforce it resolves to v25 absolute path. -> Add explicit validation that `working_dir` resolves to `03_agents/tests/v25/` (absolute), not relative or previous version.
- [x] **[Conf: 92] [architecture-strategist]** Missing mandatory 5-channel parallel dispatch rule (V22): Plan references "per-channel" gates but does not mandate all 5 search channels as unconditional parallel dispatches. -> Add mandatory "Channel Dispatch" rule in orchestration.md Phase 1 enumerating all 5 channels as MUST-dispatch on every run.
- [x] **[Conf: 90] [architecture-strategist]** Missing `--role-types` scoping for dedup operations (V22): Plan does not add role-type scoping to dedup subcommand — stale directories will interfere. -> Add `--role-types` parameter or `--active-only` flag to manage_state.py dedup subcommand with corresponding test.
- [x] **[Conf: 88] [architecture-strategist]** Missing additive merge logic for settings.local.json (V18): Plan does not address settings.local.json handling — no merge logic, no validation. -> Add step ensuring settings.local.json modifications read existing file and merge, preserving existing permissions.
- [x] **[Conf: 85] [code-simplicity-reviewer]** Dispatch counter `_write_dispatch_count` is a 50-line hand-rolled markdown parser with 6 boolean flags for updating a single line — fragile and hard to maintain. -> Replace with regex-replace approach (`dispatch_count: \d+` → new value) or append if missing. ~15 lines instead of 50.
- [x] **[Conf: 80] [code-simplicity-reviewer]** Steps 8-11 split into 4 separate steps for sentinel/schema tests that only check string presence in markdown — TDD ceremony adds no value for static text checks. -> Merge Steps 8+9 into one step and Steps 10+11 into one step (2 steps instead of 4).
- [x] **[Conf: 78] [code-simplicity-reviewer]** test_orchestration.py has 11 separate test classes and 25+ tests all doing keyword-in-file checks — over-structured for the task. -> Consolidate into 3-4 test classes max (one per layer concern). Cuts file by ~40% without losing coverage.

### Recommended Changes
- [x] **[Conf: 85] [regression-checker]** No test asserting `--body-file` used in send_email.py instead of `--html` (V21/V23 recurrence). -> Add grep-based test asserting `--body-file` appears and `--html` does not in orchestration.md.
- [x] **[Conf: 80] [regression-checker]** Background subagent dispatch not explicitly prohibited (V23 regression). -> Add explicit rule: "All subagent dispatches MUST be foreground-only."
- [x] **[Conf: 78] [architecture-strategist]** `verify-and-commit` couples local commit to remote push — network failure blocks entire pipeline. -> Separate commit and push into distinct exit code paths or make push optional.
- [x] **[Conf: 78] [regression-checker]** Dedup safety bound missing (V23): No abort threshold if >50% would be archived, no `--dry-run` flag. -> Add dedup safety bound and `--dry-run` flag.
- [x] **[Conf: 75] [architecture-strategist]** Dispatch counter stored as fragile plain-text in session-state.md. -> Consider JSON sidecar file or add edge-case tests (trailing whitespace, duplicate headings). (overlaps with code-simplicity-reviewer Required #1 above)
- [x] **[Conf: 75] [regression-checker]** No test verifying search-verify agent specifies Sonnet tier (V23 Haiku scoring regression). -> Add test checking model tier in agent file.
- [x] **[Conf: 75] [regression-checker]** Retry counter enforcement missing (V23): No max 2 attempts per auto-retry tracking. -> Add retry counter tracking in orchestration.md gate-check sections.
- [x] **[Conf: 72] [architecture-strategist]** `verify-session-state-written` date check too broad — date appearing in unrelated section causes false positive. -> Check date within structured section (e.g., `## {date}` heading).
- [x] **[Conf: 72] [code-simplicity-reviewer]** Steps 14-17 (gate tests + implementation) follow identical patterns — could merge from 4 to 2 steps. -> Merge Steps 14+16 and Steps 15+17.
- [x] **[Conf: 72] [regression-checker]** Title exclusion logic not addressed (V23): Newsletter subagent may still filter associate-level roles as executive. -> Add positive examples for associate-level titles in scoring rubric.
- [x] **[Conf: 70] [architecture-strategist]** HC10 mandatory variables not prescribed for ALL dispatch types — only "dispatch templates" mentioned, not gate-check/recovery/brief agents. -> Audit all Task dispatches and ensure each includes working_dir, output_directory, dashboard_url.
- [x] **[Conf: 70] [code-simplicity-reviewer]** `verify-session-state-written` is 12 lines for `date_string in file.read()` — over-factored as separate subcommand. -> Fold into verify-and-commit as a `--check-session-state` flag.
- [x] **[Conf: 70] [code-simplicity-reviewer]** 6 of 31 steps (19%) are pure "run tests" or "commit" steps with no implementation. -> Remove standalone test-suite steps; commit steps already include verification. Drop to ~25 steps.
- [x] **[Conf: 70] [regression-checker]** settings.local.json bloat cap not addressed (V23): File grew to 34+ entries. -> Add post-run cleanup or entry count cap.

### Nice-to-Have
- [ ] **[Conf: 65] [architecture-strategist]** `verify-and-commit` name misleading — actually does stage+commit+push. -> Consider `commit-and-push` or `stage-commit-push`.
- [ ] **[Conf: 65] [code-simplicity-reviewer]** `_extract_section` helper uses fragile heading split — simpler direct string slicing with explicit heading names would suffice. -> Use direct string slicing instead of generic section extractor.
- [ ] **[Conf: 65] [regression-checker]** Vercel redeployment not included as mandatory post-push step (V21/V22 recurrence). -> Add `vercel link && vercel --prod` as post-push step.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** Three-layer approach (Infrastructure → Orchestration → UX) provides good separation of concerns with correct dependency direction. (Conf: 55)
- **[architecture-strategist]** Test strategy is grep-based for orchestration rules — appropriate for constraint enforcement but won't catch runtime integration failures. (Conf: 52)
- **[code-simplicity-reviewer]** Three-layer commit strategy adds process overhead; single end commit would be simpler but loses rollback granularity. (Conf: 55)
- **[code-simplicity-reviewer]** Dispatch counter in markdown vs JSON sidecar — JSON simpler to parse but may conflict with session-state.md convention. (Conf: 52)
- **[regression-checker]** Structural commit gate (`verify-and-commit`) is the strongest enforcement yet for 9-version recurrence. Will need live validation. (Conf: 60)
- **[regression-checker]** Structural session-state gate (`verify-session-state-written`) follows same pattern. Will need live validation. (Conf: 60)

### Per-Reviewer Verdicts
- architecture-strategist: Needs Changes
- code-simplicity-reviewer: Needs Changes
- regression-checker: Needs Changes

### Statistics
- Total findings collected: 29 actionable + 6 informational
- Final actionable findings: 29 (12 Required, 14 Recommended, 3 Nice-to-Have)

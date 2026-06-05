# JSA V22 Reviews

## Round 3 — 2026-02-23

### Reviewers Active
architecture-strategist, code-simplicity-reviewer, regression-checker

### Required Changes
None.

### Recommended Changes
- [x] **[Conf: 70] [architecture-strategist]** Step 16 workflow YAML `if: steps.claude-run.outputs.conclusion == 'success'` for the Vercel deploy step depends on undocumented beta action output schema. If `claude-code-base-action@beta` does not emit a `conclusion` output, the Vercel deploy step silently skips every run with no error. -> Add a fallback condition such as `if: always() && steps.claude-run.outcome == 'success'` (uses GitHub's native step outcome), or add a YAML comment documenting the beta dependency and expected output key so the builder can verify.

### Nice-to-Have
None.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** The `committed` field in checkpoint JSON is always `True` with no code path to set it `False`, making the `if not data.get("committed", False)` branch in `_cli_checkpoint_validate` dead code. Harmless extensibility point. (Conf: 55)
- **[architecture-strategist]** All Round 1 and Round 2 architecture-domain findings confirmed resolved. (Conf: 65)
- **[code-simplicity-reviewer]** Step 12 `test_no_model_parameter_in_dispatch_templates` uses 5-line lookahead block slicing — slightly more complex than a single regex scan, but scope narrowing to orchestration.md makes false positives unlikely. Acceptable tradeoff. (Conf: 55)
- **[code-simplicity-reviewer]** `committed` field in checkpoint JSON remains always-True YAGNI. Harmless, no action needed. (Conf: 52)
- **[code-simplicity-reviewer]** Step 10 `_setup_passing_tree` modifications use prose+snippet format rather than single unified code block. Round 2 revision added explicit example — sufficiently addresses buildability. (Conf: 53)
- **[regression-checker]** Many V14-V20 regressions (email styling, brief formatting, salary penalty, dedup normalization) are outside V22 plan scope (checkpoint infrastructure). Preserved from v21 orchestration.md copy. (Conf: 55)
- **[regression-checker]** V19 retry logic regression (`nick-fields/retry`) not explicitly present, but `claude-code-base-action` may handle retries internally. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: APPROVED

### Statistics
- Total findings collected: 8 (1 actionable, 7 informational)
- Final actionable findings: 1 (0 Required, 1 Recommended, 0 Nice-to-Have)

---

## Round 2 — 2026-02-23

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
- [x] **[Conf: 85] [code-simplicity-reviewer]** Test boilerplate duplication: Every checkpoint test class (Steps 2-4) repeats the same 3-line scaffold (`output_dir = tmp_path / "output"`, `output_dir.mkdir(parents=True)`, `(output_dir / ".checkpoints").mkdir()`). This appears 12+ times. -> Extract a shared pytest fixture `cp_output_dir` that creates and returns the `tmp_path/output/.checkpoints` structure.
- [x] **[Conf: 80] [code-simplicity-reviewer]** Steps 6+7, 8+9, 10+11 are mechanical TDD pairs that double the step count for single concerns. -> Merge each pair into one step: "Add pre-gate wrappers to orchestration.md with test," "Add background:true to agents with test," "Remove foreground-fallback with test." Reduces 6 steps to 3.
- [x] **[Conf: 78] [code-simplicity-reviewer]** Step 20 is a no-op — says "already included in Step 19" and performs zero file modifications. -> Delete Step 20 entirely. Move its verify command into Step 19's verify section. Update handoff contract step count.

### Recommended Changes
- [x] **[Conf: 78] [architecture-strategist]** Phase 3 POST-CHECKPOINT `git add` includes broad `output/` glob that could accidentally commit raw/unverified files. -> Narrow Phase 3 POST-CHECKPOINT to `git add output/.checkpoints/ output/verified/ output/_delta.json state.json`.
- [x] **[Conf: 75] [architecture-strategist]** Phase 5 POST-CHECKPOINT also uses broad `output/` in `git add`. -> Narrow to `git add output/.checkpoints/ output/session-state.md state.json` or specific deliver outputs.
- [x] **[Conf: 75] [code-simplicity-reviewer]** `test_clear_only_runs_in_phase1_context` parses orchestration.md with regex position math to enforce checkpoint clear placement — tests markdown layout, not Python logic, and breaks on heading renames. -> Move to `test_workflow.py` alongside other structural tests, or drop since preflight.sh covers the concern.
- [x] **[Conf: 75] [regression-checker]** V15 regression: email idempotency guard (`_status.json` `sent_at` check) not explicitly addressed in plan. -> Add note in Phase 5 POST-CHECKPOINT or entry criteria referencing the idempotency check, or add a test verifying orchestration.md Phase 5 references this safeguard.
- [x] **[Conf: 72] [architecture-strategist]** `_cli_checkpoint_validate` reads checkpoint JSON but does not validate schema — missing keys with `committed: true` would pass. -> Add minimal schema check: assert `phase`, `count`, and `timestamp` keys exist.
- [x] **[Conf: 72] [code-simplicity-reviewer]** Step 5 subprocess benchmark (10 cycles, 2s) provides marginal value over direct-call benchmark — subprocess overhead is OS constant, not app logic. -> Keep only `test_direct_call_under_500ms`. Drop subprocess benchmark or mark `@pytest.mark.slow`.
- [x] **[Conf: 72] [regression-checker]** V20/V21 regression: pre-run cleanup must cross-reference state.json before deleting files — plan does not verify this is preserved from v21 copy. -> Add test or manual verification confirming orchestration.md Phase 1 contains state.json cross-reference before file deletion.
- [x] **[Conf: 70] [architecture-strategist, code-simplicity-reviewer]** Step 13 describes `_setup_passing_tree` modifications vaguely — no code provided unlike every other step. -> Provide explicit `_setup_passing_tree` modifications: add checkpoint commands to orchestration.md fixture, create `.checkpoints/` dir, add sample agent with `background: true`. (overlaps between architecture-strategist and code-simplicity-reviewer)
- [x] **[Conf: 70] [code-simplicity-reviewer]** Step 15 regex `(?:Task|dispatch|subagent).*?model\s*:` in `test_no_model_parameter_in_dispatch_templates` will false-positive on workflow YAML prompt and agent frontmatter. -> Narrow regex to dispatch-block patterns or scope search to `orchestration.md` only.
- [x] **[Conf: 70] [regression-checker]** V21 regression: `send_email.py` uses `--body-file` not `--html` — plan does not verify this is preserved. -> Add test confirming orchestration.md Phase 5 uses `--body-file` when referencing send_email.py.

### Nice-to-Have
- [x] **[Conf: 70] [architecture-strategist]** `_cli_checkpoint_status` uses hardcoded column width (`{phase:<12}`) — breaks if phase name exceeds 12 chars. -> Use `max(len(p) for p in VALID_CHECKPOINT_PHASES)` for dynamic padding.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** Round 1 Context Budget, settings.local.json merge, VALID_CHECKPOINT_PHASES source-of-truth, --output-dir dedup, datetime.utcnow(), benchmark subprocess, and checkpoint clear concerns all properly addressed in revision. (Conf: 55-65)
- **[architecture-strategist]** Step 19 `claude-code-base-action@beta` output schema is undocumented (beta) — `if: steps.claude-run.outputs.conclusion == 'success'` for Vercel deploy may silently skip if action doesn't emit `conclusion`. (Conf: 60)
- **[code-simplicity-reviewer]** `committed` field in checkpoint JSON is always True and never set to False anywhere — pure YAGNI but harmless. (Conf: 55)
- **[regression-checker]** Many V14-V20 regressions (email styling, brief formatting, salary penalty, etc.) are outside plan scope — already addressed in v21 orchestration.md copied to v22 as prerequisite. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: Needs Changes
- regression-checker: APPROVED

### Statistics
- Total findings collected: 19
- Final actionable findings: 15 (3 Required, 11 Recommended, 1 Nice-to-Have)
- Informational notes: 4

---

## Round 1 — 2026-02-23

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
- [x] **[Conf: 97] [regression-checker]** Incremental commit+push after each search batch NOT addressed — 6-version recurrence (V14/V16/V18/V19/V20/V21). Plan adds checkpoint at phase boundaries but not after each search *batch* within Phase 1. -> Add explicit batch-level commit step in orchestration.md Phase 1 that runs `git add && git commit && git push` after each search batch, plus a test verifying orchestration.md contains commit language within Phase 1 search batch instructions.
- [x] **[Conf: 96] [regression-checker]** Orchestration.md POST-CHECKPOINT shows direct `python3 scripts/manage_state.py` execution. V19 regression: "Parent must NEVER run python3 scripts/* directly." -> Clarify in orchestration.md PRE-GATE/POST-CHECKPOINT sections that checkpoint commands are executed by the active subagent, never by the parent orchestrator directly.
- [x] **[Conf: 95] [architecture-strategist, regression-checker]** Step 16b replaces `settings.local.json` entirely — violates V18 regression "modifications must be additive, never overwrite." -> Change Step 16b to read-then-merge: load existing JSON, merge new `permissions.allow` entries, write back. Add a test asserting pre-existing entries survive the update. (overlaps with code-simplicity-reviewer Recommended finding below)
- [x] **[Conf: 95] [regression-checker]** session-state.md after EVERY search batch not addressed — 5-version recurrence (V14/V16/V18/V19/V21). -> Add test or orchestration instruction requiring session-state.md update after each search batch within Phase 1.
- [x] **[Conf: 95] [regression-checker]** No explicit step verifying agent startup reads `.claude/agent-memory/*/MEMORY.md` (HC4 — V14/V17/V19 recurrence). -> Add test in test_claude_md.py verifying CLAUDE.md ON STARTUP references reading agent-memory files.
- [x] **[Conf: 95] [regression-checker]** No `model:` parameter validation in dispatch templates (V19 HC1 regression). -> Add test verifying no Task dispatch in orchestration.md or CLAUDE.md passes a `model:` parameter.
- [x] **[Conf: 92] [architecture-strategist]** Plan lacks explicit "Context Budget" section listing parent-allowed vs subagent-only tools (V18 review addition). -> Add Context Budget table clarifying checkpoint CLI calls are parent-allowed (lightweight state), while search/filter/dedup/WebFetch/WebSearch remain subagent-only.
- [x] **[Conf: 90] [architecture-strategist]** Step 16b's settings.local.json removes per-domain WebFetch entries and replaces with wildcard — unrelated permission scope expansion bundled into checkpoint plan. -> Decouple settings.local.json simplification into separate step with own test, or document as deliberate scope change.
- [x] **[Conf: 88] [architecture-strategist]** Checkpoint `clear` deletes all `.json` in `.checkpoints/` with no recovery path for partial runs. -> Add `--confirm-full-clear` flag or document that clear is intentionally destructive and only runs at pipeline start. Add test verifying clear only runs in Phase 1 context.
- [x] **[Conf: 88] [code-simplicity-reviewer]** `--output-dir` argument duplicated across all 4 checkpoint subparsers with identical definition. -> Add `--output-dir` to parent `cp_parser` once; argparse propagates to subparsers. Removes ~24 lines of duplication. (overlaps with architecture-strategist Recommended finding)
- [x] **[Conf: 82] [code-simplicity-reviewer]** Steps 2-8 use over-granular write-failing-test / implement decomposition — 8 steps for what could be 4. -> Merge Steps 2+3, 4+5, 6+7 into single steps each. Reduces Layer 1 from 8 to 4 steps.
- [x] **[Conf: 78] [code-simplicity-reviewer]** `--committed` flag with `BooleanOptionalAction` is premature generalization — no orchestration path ever writes uncommitted checkpoints. -> Remove `--committed` flag entirely; always write `committed: true`. Eliminates one test, one flag, and the validate branch.
- [x] **[Conf: 75] [code-simplicity-reviewer]** `--batch` flag on checkpoint write has no consumer — written to JSON but never read by downstream code. -> Remove `--batch` unless there is a concrete consumer. Simplifies checkpoint JSON schema.

### Recommended Changes
- [x] **[Conf: 85] [regression-checker]** V21 regression: search-verify subagent needs hard time/tool-use budget with checkpoint-and-return on budget exhaustion — not enforced. -> Add orchestration instruction or agent frontmatter enforcing budget for search-verify subagents.
- [x] **[Conf: 82] [regression-checker]** V21 regression: Vercel dashboard re-link on version transition — CI handles it but no explicit step for initial v21→v22 transition. -> Add prerequisite step to run `vercel link` + `vercel --prod` from v22 directory after version copy.
- [x] **[Conf: 80] [regression-checker]** Commented-out archive block in Step 18 still references v20 — may confuse future maintainers. -> Note that archived comment references are expected.
- [x] **[Conf: 78] [architecture-strategist]** `VALID_CHECKPOINT_PHASES` duplicated as Python constant and implicitly in orchestration.md/tests — 3 locations to sync. -> Extract to single source of truth (constant in manage_state.py that tests reference, or shared phases.json).
- [x] **[Conf: 78] [regression-checker]** V17 regression: GH Actions must create settings.local.json — claude-code-base-action may handle permissions differently. -> Verify action handles permissions via `allowed_tools` param; add workflow comment confirming settings.local.json not needed.
- [x] **[Conf: 75] [regression-checker]** V19 regression: subagent dispatch prompts must include explicit absolute working directory variable — not verified. -> Add test verifying orchestration.md dispatch templates include absolute working directory.
- [x] **[Conf: 74] [architecture-strategist]** `datetime.utcnow().isoformat()` deprecated in Python 3.12+. -> Use `datetime.now(datetime.timezone.utc).isoformat()`.
- [x] **[Conf: 72] [architecture-strategist]** Workflow YAML Step 18 "Commit state" step may race with commits from claude-code-base-action. -> Document expected git state after Claude action completes.
- [x] **[Conf: 72] [regression-checker]** CLAUDE.md <=300 lines (V20 regression, Agent Decomposition Pattern) — plan modifies CLAUDE.md but does not verify line count. -> Add test asserting CLAUDE.md line count <= 300.
- [x] **[Conf: 72] [code-simplicity-reviewer]** settings.local.json full overwrite conflicts with V18 regression. -> Use merge strategy or document as version-transition exception. (overlaps with Required #3 above)
- [x] **[Conf: 70] [architecture-strategist]** Benchmark test spawns 200 subprocesses testing CLI overhead, not checkpoint logic. -> Add direct-call benchmark alongside subprocess one.
- [x] **[Conf: 70] [code-simplicity-reviewer]** Performance benchmark tests subprocess overhead, not checkpoint I/O. -> Test checkpoint logic via function import or reduce to 10 cycles / 500ms budget. (overlaps with architecture-strategist finding above)
- [x] **[Conf: 70] [code-simplicity-reviewer]** Archived `claude --print` block in workflow YAML is 16 lines of dead commented-out code. -> Remove entirely; it's in git history if needed.
- [x] **[Conf: 70] [regression-checker]** Existing preflight.sh checks may use exact heading matches — verify partial matches. -> Verify existing checks use partial matches, not just the new ones.

### Nice-to-Have
- [x] **[Conf: 70] [architecture-strategist]** Benchmark test spawns 200 subprocesses — a unit-level benchmark testing Python functions directly would be faster and more meaningful. -> Add direct-call benchmark alongside subprocess one.
- [ ] **[Conf: 65] [code-simplicity-reviewer]** Step 9 test uses fragile string position arithmetic. -> Use regex to extract phase sections.
- [ ] **[Conf: 65] [regression-checker]** V19 regression: retry logic in scheduled workflow not included — claude-code-base-action may handle retries internally. -> Consider adding retry wrapper or documenting.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** `.gitkeep` in Step 1 is redundant at runtime since write command creates `.checkpoints/` automatically — exists only for git tracking. (Conf: 55)
- **[architecture-strategist]** `test_status_shows_all_phases` uses fragile string parsing (`lines[0].split()[0]`). (Conf: 60)
- **[code-simplicity-reviewer]** `_run_checkpoint` helper spawns full subprocess per test — idiomatic for CLI integration tests but ~0.1s per call. (Conf: 55)
- **[code-simplicity-reviewer]** `datetime.utcnow()` deprecated since Python 3.12 — triggers deprecation warnings. (Conf: 52)
- **[regression-checker]** V21 `send_email.py --body-file` vs `--html` regression not directly relevant to V22 scope (infrastructure only). (Conf: 55)
- **[regression-checker]** V20 pre-run cleanup cross-referencing state.json before deleting verified files not addressed — plan scope is checkpoint infrastructure, not search/cleanup. (Conf: 52)

### Per-Reviewer Verdicts
- architecture-strategist: Needs Changes
- code-simplicity-reviewer: Needs Changes
- regression-checker: Needs Changes

### Statistics
- Total findings collected: 34
- Final actionable findings: 30 (13 Required, 14 Recommended, 3 Nice-to-Have)
- Informational notes: 6

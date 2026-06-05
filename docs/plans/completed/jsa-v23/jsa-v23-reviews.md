# JSA V23 Plan Reviews

## Round 2 — 2026-02-24

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
None.

### Recommended Changes
- [x] **[Conf: 78] [regression-checker]** Pre-search archival (Step 2.3, Change 2, item 2) specifies preserving entries active in state.json, but no test covers this cross-reference path. If the archival logic silently skips the state.json check, V20/V21 regression (blind archive breaks dashboard) recurs. -> Add at least one test case verifying that pre-search archival preserves directories referenced by active state.json entries even when the directory's role-type slug is not in the active list.
- [x] **[Conf: 78] [code-simplicity-reviewer]** `preflight.sh` wraps 3 Python-backed checks (session-resume, model-settings, dashboard-url) that are pure pass-throughs: call `manage_state.py` subcommand, check exit code, print message. This two-layer indirection is justified for the 2 shell-native checks (git-pull, agent-memory grep) but adds unnecessary complexity for the Python-backed ones. -> Have the orchestrator (or gate-check subagent) call `manage_state.py check-*` subcommands directly for the 3 Python-backed checks. Let `preflight.sh` focus on the 2 shell-native checks only.
- [x] **[Conf: 75] [code-simplicity-reviewer]** Step 3.1 creates 9 tests in `test_preflight.py` and Step 3.2 creates 10 tests in `test_manage_state_preflight.py` that test the same 3 behaviors (session-resume, model-settings, dashboard-url) at two layers with substantial overlap. -> Consolidate to one test layer per check. Test `manage_state.py` subcommands directly (Step 3.2 tests), limit `test_preflight.py` to the 2 shell-native checks (~3-4 tests). Cuts ~6 redundant tests.
- [x] **[Conf: 75] [regression-checker]** `check-model-settings` (Step 3.2) validates agents with an allowlist of `haiku, sonnet` only. Any new agent added without updating this check will fail preflight. No exclusion mechanism exists. -> Add a note that `check-model-settings` should accept an exclusion list parameter or document that new agents must use `haiku` or `sonnet` to pass preflight.
- [x] **[Conf: 74] [architecture-strategist]** Gate-check subagent is referenced throughout (Steps 1.4, 2.3 items 7-9) but has no named agent definition (`.claude/agents/gate-check.md`) in Files to Modify. Without an agent file and model tier assignment, gate checks default to Opus — undermining cost reduction for purely mechanical work. -> Add `gate-check.md` to `.claude/agents/` with `model: haiku` in Files to Modify, or specify in orchestration.md that gate checks use inline general-purpose subagent with explicit `model: haiku`.
- [x] **[Conf: 72] [architecture-strategist]** Pre-search archival (Step 2.3 item 2) and `dedup --role-types` (Step 1.2) both depend on knowing the "active role types list" but no single authoritative source or extraction mechanism is defined for runtime. -> Specify the single source of truth for active role-type slugs (e.g., context.md `## Target`) and the extraction mechanism (e.g., `manage_state.py list-active-role-types` or explicit parent parsing). Ensure both archival and dedup consume the same list.
- [x] **[Conf: 72] [regression-checker]** V21 regression: "send_email.py uses `--body-file` not `--html`". Plan does not modify email orchestration but no verification step checks that email CLI flags in orchestration.md match `send_email.py` interface. -> Add a grep in `verify_deploy.sh` confirming `--body-file` appears (and `--html` does not) in orchestration references to `send_email.py`.
- [x] **[Conf: 72] [code-simplicity-reviewer]** Pre-search cleanup step has a compound conditional (not in active role-types list AND not referenced by state.json) that introduces subtle coupling between two concerns. -> Simplify to single condition: archive directories not in the active `--role-types` list. If state.json consistency matters, handle it in a separate dedicated step.

### Nice-to-Have
- [x] **[Conf: 70] [architecture-strategist]** `manage_state.py` now has 7 new subcommands in one version. Grouping under sub-parsers (`verify {clean-working-tree,...}` and `check {session-resume,...}`) would improve discoverability. -> Group verify-* under a `verify` subparser and check-* under a `check` subparser. Not blocking.
- [x] **[Conf: 70] [code-simplicity-reviewer]** Step 2.3 Change 2 has 10 numbered sub-items with sub-bullets and copy specs — the densest step in the plan. -> Split Step 2.3 into two steps: one for Context Budget (Change 1) and one for Phase 1 rewrite (Change 2).
- [x] **[Conf: 70] [regression-checker]** V20 regression: within-role URL-based dedup assumed inherited from V22 but no test validates this survives the copy. -> Consider adding a test verifying two jobs with identical URLs but different scores in the same role directory are deduplicated.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** Per-channel gate pattern creates 10 additional subagent dispatches per run (5 commit + 5 session-state). With Haiku, cost is negligible. Acceptable tradeoff given 7-version regression history. (Conf: 55)
- **[architecture-strategist]** Parallel dispatch of 5 channels followed by per-channel sequential gates creates implicit fan-out/fan-in. Plan doesn't specify event-driven vs polling for channel completions — orchestration detail for build phase. (Conf: 60)
- **[code-simplicity-reviewer]** `manage_state.py` approaching point where it should split into subcommand-per-file pattern. Not a V23 blocker. (Conf: 55)
- **[code-simplicity-reviewer]** All round 1 fixes were thoroughly applied. No inadequate fixes found. (Conf: 65)
- **[regression-checker]** Many V14-V20 regressions (design system, email, briefs, score threshold, preview.sh) inherited from V22, not modified. Assumed preserved. (Conf: 55)
- **[regression-checker]** MEMORY.md lists scheduled-run cost guard ($2.00 budget cap) as V23 requirement. Plan does not implement this. Not a regression item — out of scope for this reviewer. (Conf: 50)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: APPROVED

### Statistics
- Total findings collected: 22 (across 3 reviewers)
- Final actionable findings: 0 Required, 8 Recommended, 3 Nice-to-Have
- Informational notes: 6

---

## Round 1 — 2026-02-24

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
- [x] **[Conf: 97] [regression-checker]** Post-batch commit gate is documented but not structurally enforced as a blocking mechanism. `verify-batch-committed` exists as a script but nothing blocks next-batch dispatch until it passes. After 7 consecutive violations (V14-V22), documentation-only enforcement is insufficient. -> Add a concrete enforcement mechanism: either (a) the parent orchestrator calls `verify-batch-committed` and exits non-zero before dispatching the next batch, or (b) a wrapper function that gates dispatch. Must be a code-level blocking call, not just orchestration.md prose.
- [x] **[Conf: 97] [regression-checker]** Session-state.md write-after-batch has no structural enforcement. Plan addresses commit gates and channel verification but does NOT add any enforcement mechanism for session-state.md writes after each search batch. 6-version recurrence (V14/V16/V18/V19/V21/V22). -> Add a `verify-session-state-updated` check that confirms session-state.md was modified after each batch, enforced the same way as the commit gate.
- [x] **[Conf: 95] [architecture-strategist]** Plan lacks explicit "Context Budget" listing which tools parent may call directly vs subagent-only. V18/V19/V20/V21 regressions show parent executing search, dedup, WebFetch, or scripts directly. -> Add a "Context Budget" section to orchestration.md (or CLAUDE.md) explicitly listing parent-callable tools (Task, Read status files, git add/commit/push) vs subagent-only (all manage_state.py subcommands, WebFetch, WebSearch, script execution). Step 2.3 must include this.
- [x] **[Conf: 95] [regression-checker]** Plan reverses HC1 ("Never pass model: to Task tool") but this directly contradicts V19 regression item. Must acknowledge the conflict and confirm V19 item is being intentionally superseded. -> Add explicit note in the plan that V19 regression re: HC1 is superseded by V23 model-tiering design decision, and update regression file after build.
- [x] **[Conf: 95] [regression-checker]** Vercel dashboard redeployment not included as a plan step. V21/V22 regressions require mandatory Vercel redeploy after data pushes and version transitions. -> Add a deployment step that runs `vercel link --project jsa-dashboard --yes && vercel --prod --yes` from V23 directory.
- [x] **[Conf: 95] [regression-checker]** GitHub Actions workflow update missing. V19/V21/V22 regressions require repo-root `.github/workflows/daily-digest.yml` to reference current version (v23). -> Add a step to update `.github/workflows/daily-digest.yml` to reference `03_agents/tests/v23/`.
- [x] **[Conf: 92] [architecture-strategist]** `verify-batch-committed` and `verify-channels-dispatched` are new gates but plan doesn't specify WHO executes them. If parent runs `python scripts/manage_state.py verify-batch-committed` directly, it violates V19 regression (parent must never run scripts directly). -> Clarify that gates are invoked by a subagent, or explicitly exempt gate scripts from the context budget with rationale.
- [x] **[Conf: 90] [architecture-strategist]** Step 2.3 describes 5-channel dispatch but does not include mandatory HC10 variables (output_directory, dashboard_url) in each Task dispatch JSON blob. V21 regression requires these. -> Add mandatory fields `output_directory` and `dashboard_url` to channel-specific dispatch JSON blobs in Step 2.3.
- [x] **[Conf: 88] [code-simplicity-reviewer]** Deployment Verification sections (34 manual bash snippets) are gold-plating beyond the stated goal of "enforcement gates + cost reduction". -> Remove the Deployment Verification / Rollback section. If needed, write a single `scripts/verify_deploy.sh` that runs all checks (one step, one script).
- [x] **[Conf: 88] [architecture-strategist]** No pre-dedup cleanup pathway to archive stale role-type directories before search begins. If `--role-types` is accidentally omitted, V22 failure recurs. -> Add a pre-search step that archives role-type directories NOT in the active list before search begins — defense in depth alongside the flag.
- [x] **[Conf: 85] [code-simplicity-reviewer]** `verify-channels-dispatched` overspecifies a bespoke JSON protocol for "did 5 things run?". -> Replace with simpler check: each search subagent writes a `.done` file; verify command checks 5 `.done` files exist with today's mtime. Eliminates JSON parsing overhead.
- [x] **[Conf: 85] [architecture-strategist]** `verify-batch-committed` runs end-of-phase, not per-batch. Cannot enforce the 7x-recurring incremental commit+push regression. -> Run `verify-batch-committed` per-channel (after each search-verify subagent returns), not just end-of-phase. (overlaps with regression-checker Required #1 above)
- [x] **[Conf: 82] [code-simplicity-reviewer]** Phase 4 "Integration Validation" (Steps 4.1-4.2) duplicates what Phase 1 and Phase 3 already verify. -> Eliminate Phase 4 entirely. The full-suite run at end of Phase 3 is sufficient.

### Recommended Changes
- [x] **[Conf: 85] [regression-checker]** No explicit startup step reads `.claude/agent-memory/*/MEMORY.md` (HC4). V14/V17/V19 three-time recurrence. -> Verify copied V22 CLAUDE.md retains agent-memory startup read step; add deployment verification grep.
- [x] **[Conf: 80] [regression-checker]** Dashboard URL mandatory enforcement not addressed. V18/V19/V20 regressions require no null fallbacks. -> Add a preflight or deployment check that `context.md` contains the dashboard URL.
- [x] **[Conf: 80] [regression-checker]** No subagent absolute working directory variable in dispatch prompts. V19 regression. -> Ensure orchestration.md Phase 1 dispatch templates include `working_dir: /absolute/path/to/v23/` in every subagent JSON blob.
- [x] **[Conf: 78] [architecture-strategist]** `verify-channels-dispatched` reads `.channels/{name}.json` but no step specifies WHO writes these files. -> Step 2.3 should specify that each search-verify dispatch writes the channel status file on completion.
- [x] **[Conf: 78] [code-simplicity-reviewer]** `preflight.sh` uses inline Python for session resume and model validation. Mixing bash+Python is a maintenance hazard. -> Move checks into `manage_state.py` subcommands; have `preflight.sh` call them.
- [x] **[Conf: 75] [architecture-strategist]** Plan doesn't verify `settings.local.json` modifications are additive (V18 regression). -> Confirm no settings.local.json changes needed for model tiering, or add additive merge step.
- [x] **[Conf: 75] [code-simplicity-reviewer]** 7 tests for `verify-channels-dispatched` is over-testing. -> 3-4 tests suffice: all present (pass), one missing (fail), stale date (fail), no directory (fail).
- [x] **[Conf: 75] [regression-checker]** CI workflow doesn't create `settings.local.json` or propagate `SCHEDULED_RUN` env var. V17/V19/V20/V22 recurrence. -> Include CI workflow update ensuring these.
- [x] **[Conf: 72] [architecture-strategist]** Archival/cleanup interaction with downstream readers unaddressed. V21 regression. -> Ensure archival preserves entries state.json lists as active, or runs only before search begins.
- [x] **[Conf: 72] [code-simplicity-reviewer]** Step 2.4 hardcodes 18 company names, 5 boards, 10 queries as implementation spec. This is config masquerading as code. -> Replace with placeholder ("populate from current context at build time").
- [x] **[Conf: 72] [regression-checker]** Parent orchestrator never runs `python3 scripts/*` directly (V19 regression). Orchestration.md rewrite must preserve this delegation. -> Verify orchestration.md Phase 1 delegates all `manage_state.py` calls to subagents.
- [x] **[Conf: 70] [architecture-strategist]** Model tier table hardcoded in CLAUDE.md can drift from agent frontmatter. -> Consider making CLAUDE.md table reference agent frontmatter as source of truth.
- [x] **[Conf: 70] [code-simplicity-reviewer]** `--force` flag adds unnecessary second code path. User can delete `_status.json` to re-run. -> Drop `--force` flag.

### Nice-to-Have
- [x] **[Conf: 70] [architecture-strategist]** `verify-batch-committed` name implies batch-level granularity but checks all of `output/verified/`. -> Consider `verify-clean-working-tree` or parameterize scope.
- [x] **[Conf: 70] [code-simplicity-reviewer]** Step numbering skips 3.3 and 3.4. -> Renumber to 3.1-3.4 for clarity.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** The Three-Layer architecture (Scripts -> Orchestration+Config -> Validation) is structurally sound — clean separation of concerns. (Conf: 60)
- **[architecture-strategist]** Step numbering jumps from 3.2 to 3.5. Likely cosmetic but could confuse the build agent. (Conf: 55)
- **[code-simplicity-reviewer]** `manage_state.py` is becoming a monolithic CLI with 3 new subcommands. Not a problem at V23 scope but worth watching. (Conf: 55)
- **[code-simplicity-reviewer]** V17 regression ("Agent must never ask user to do technical work") is not violated by this plan. Post-deploy checks are developer-facing. (Conf: 60)
- **[regression-checker]** Many V14-V20 regressions (design system, email, briefs, score threshold, preview.sh) are inherited from V22 copy and not modified. Assumed preserved. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: Needs Changes
- code-simplicity-reviewer: Needs Changes
- regression-checker: Needs Changes

### Statistics
- Total findings collected: 36 (across 3 reviewers)
- Final actionable findings: 13 Required, 13 Recommended, 2 Nice-to-Have
- Informational notes: 5

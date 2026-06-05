# JSA V19 Reviews

## Round 2 — 2026-02-17

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
None.

### Recommended Changes
None.

### Nice-to-Have
- [ ] **[Conf: 60] [code-simplicity-reviewer]** Steps 4-10 still run individual pytest after each CLAUDE.md edit — since all edits are independent text insertions that cannot interfere, a single test run after Step 10 would suffice -> Consolidate verify steps for Steps 4-9 to "visually confirm edit applied" and run full pytest once after Step 10
- [ ] **[Conf: 58] [architecture-strategist]** Step 11 manage_state.py fix says "ensure title and company fields are normalized" but leaves verification to the builder rather than prescribing exact old/new text — inconsistent with the precise edit pattern used elsewhere -> Provide explicit old/new text for title/company normalization or state "verify existing code already normalizes these; if not, add `.lower().strip()` to both fields in the dedup key computation"

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** Context Budget "Parent-allowed operations" lists specific status files — if new status files are added in future versions, the allowlist must be updated. An extensible pattern would be more maintainable but is not blocking. (Conf: 52)
- **[architecture-strategist]** The foreground-fallback guard tests on "the first real subagent dispatch" which is loosely defined — if the first dispatch succeeds but a later dispatch fails due to different tool restrictions, the guard won't trigger. Acceptable for V19 scope. (Conf: 55)
- **[code-simplicity-reviewer]** The "No escape hatch" language in Context Budget is an excellent simplification — removes an entire state-tracking obligation with no loss of safety. (Conf: 55)
- **[code-simplicity-reviewer]** The `test_never_directs_user_to_perform_technical_actions` test checks a fixed list of 5 phrases — adequate for a regression gate but won't catch novel phrasings. Acceptable as best-effort heuristic. (Conf: 52)
- **[regression-checker]** Pre-deploy grep checks now cover agent-memory and key constraints but do not verify score >= 70 or email link color. These are outside V19 scope (no email/briefs changes), so not actionable. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: APPROVED

### Statistics
- Total findings collected: 7
- Final actionable findings: 2 Nice-to-Have (0 Required, 0 Recommended)

---

## Round 1 — 2026-02-17

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
- [x] **[Conf: 92] [architecture-strategist]** Context Budget escape hatch lacks ownership tracking — the "3 failures" counter is undefined in terms of state management (where stored, how persisted across dispatches, how reset) -> Add explicit state tracking for the failure counter or simplify/remove the escape hatch
- [x] **[Conf: 88] [architecture-strategist]** Foreground-fallback guard (Step 4) sets `DISPATCH_MODE` but Context Budget section (Step 5) does not reference or enforce this mode — the two features are architecturally disconnected -> Add a sentence to Context Budget linking to `DISPATCH_MODE`: "When `DISPATCH_MODE=foreground`, all subagent dispatches use foreground mode. Escape hatch counter still applies."
- [x] **[Conf: 85] [architecture-strategist]** Escape hatch allows parent to run subagent-only operations after 3 failures, directly contradicting V18 regression [subagent-coordination] ("parent must NEVER execute search, filter, dedup, WebFetch, WebSearch directly") -> Narrow escape hatch scope to ONLY file reads and script execution — NEVER WebFetch, WebSearch, filter, dedup, or brief generation
- [x] **[Conf: 85] [code-simplicity-reviewer]** Step 4 foreground-fallback guard is over-engineered: dedicated test subagent, output file, state variable, and branching logic for a single edge case -> Simplify to: attempt dispatch normally on first real subagent; if denied, switch to foreground. Eliminate dedicated test subagent, test output file, and ceremony. (overlaps with architecture-strategist finding on DISPATCH_MODE disconnection above)
- [x] **[Conf: 78] [code-simplicity-reviewer]** Step 5 CONTEXT BUDGET escape hatch 3-failure counting adds unverifiable complexity -> Either remove escape hatch entirely (strict subagent-only, fail loudly) or simplify to binary: "If DISPATCH_MODE=foreground, parent may execute directly." Remove counting obligation. (overlaps with architecture-strategist finding on escape hatch state above)
- [x] **[Conf: 75] [code-simplicity-reviewer]** Step 10 session-state checkpoint template is overly prescriptive — mandates exact markdown heading format, 5 specific fields, and append-only semantics creating brittle test contracts -> Reduce to semantic requirements: "Append checkpoint after each batch with: batch number, role types, jobs processed, cumulative count. Don't overwrite earlier checkpoints." Let agent format naturally.

### Recommended Changes
- [x] **[Conf: 80] [regression-checker]** V14/V17 agent-memory startup read: no verification step confirms the startup read survived copy + CLAUDE.md edits -> Add grep verification: `grep -c "agent-memory" 03_agents/tests/v19/CLAUDE.md` (expect >= 1)
- [x] **[Conf: 78] [architecture-strategist]** Test helpers `_write_verified_job` and `_run_dedup` (Step 2) referenced but never defined in plan — risk NameError at test time -> Add verification sub-step: confirm helpers exist in file before appending new test class, define if missing
- [x] **[Conf: 76] [architecture-strategist]** Test helper `_extract_section` (Step 3) referenced but not defined -> Same mitigation: verify existence or define
- [x] **[Conf: 75] [regression-checker]** V17 GitHub Actions + settings.local.json: plan adds merge protocol but doesn't check whether any workflow references settings.local.json without a preceding creation step -> Add verification that no `.github/workflows/*.yml` references `settings.local.json` as if committed
- [x] **[Conf: 74] [architecture-strategist]** Test helper `_read_claude_md` (Step 3) referenced across all three CLAUDE.md tests but not defined -> Same mitigation: verify existence or define
- [x] **[Conf: 72] [architecture-strategist]** Session-state checkpoint format (Step 10) uses nested markdown code fences inside CLAUDE.md — inner triple-backtick may corrupt parsing -> Use different delimiter (indented block or HTML comment) or escape inner backticks
- [x] **[Conf: 72] [code-simplicity-reviewer]** Regex forbidden-pattern tests against CLAUDE.md prose (Step 3) are brittle — will break on rewording -> Test for presence of required concepts ("stdin", "pipe", "never inline") rather than specific CLI patterns
- [x] **[Conf: 72] [regression-checker]** V18 dedup normalized title+company: plan fixes domain normalization but regression calls out title+company specifically — `.lower().strip()` may only apply to domain -> Verify existing `_compute_dedup` normalizes title/company, or extend fix to include those fields
- [x] **[Conf: 70] [code-simplicity-reviewer]** Steps 4-10 each modify CLAUDE.md independently with individual verify steps — 7 edit-then-verify cycles are redundant since tests are cumulative -> Batch all CLAUDE.md edits into one step, run tests once after all applied

### Nice-to-Have
- [x] **[Conf: 68] [architecture-strategist]** `DISPATCH_MODE` SCREAMING_SNAKE_CASE suggests environment variable but it's in-context — naming ambiguity -> Use `dispatch_mode` or `_session_dispatch_mode`
- [x] **[Conf: 65] [code-simplicity-reviewer]** Step 9 settings.local.json merge protocol is a 4-step algorithm in prose inside CLAUDE.md — reads like code masquerading as prose -> Condense to: "When modifying settings.local.json, read-merge-write — never overwrite existing keys"
- [x] **[Conf: 60] [regression-checker]** Pre-deploy grep checks could verify additional regression items (agent-memory, score >= 70) for broader safety net -> Add grep checks for known constraints

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** Plan copies entire v18 directory before targeted edits — architecturally clean (immutable versioning) but v18 bugs not addressed in v19 are carried forward silently. (Conf: 55)
- **[architecture-strategist]** Domain normalization fix applies `.lower().strip()` only — does not handle `www.` prefix. Two URLs `www.linkedin.com` and `linkedin.com` would produce different dedup keys. (Conf: 60)
- **[code-simplicity-reviewer]** Plan is 14 steps for 1 file copy, 7 text insertions, 1 code fix, 4 test additions. Step count appropriate for verification needs but per-step verify pattern inflates apparent complexity. (Conf: 55)
- **[code-simplicity-reviewer]** V17 "never direct user to perform technical actions" not explicitly addressed in plan steps though fabricated UI constraint (Step 7) partially covers it. No test added for the broader requirement. (Conf: 60)

### Per-Reviewer Verdicts
- architecture-strategist: Needs Changes
- code-simplicity-reviewer: Needs Changes
- regression-checker: APPROVED

### Statistics
- Total findings collected: 18
- Final actionable findings: 15 (6 Required, 9 Recommended)

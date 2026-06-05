# JSA V20 Plan Reviews

## Round 2 — 2026-02-18

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
None.

### Recommended Changes
- [x] **[Conf: 74] [code-simplicity-reviewer]** Step 15 `settings.local.json` heredoc indentation may produce invalid JSON — the `cat > .claude/settings.local.json << 'SETTINGS_EOF'` block is inside a YAML `run: |` scalar, and the JSON content appears indented with leading whitespace. The existing `python3 -c json.load(...)` line catches this at runtime but the plan should acknowledge this explicitly. -> Add a note in Step 15 acknowledging the heredoc indentation risk and that the `python3 -c "import json; json.load(...)"` validation gate intentionally catches this at deploy time.

### Nice-to-Have
- [ ] **[Conf: 68] [code-simplicity-reviewer]** Step 10 cleanup rationale cites the wrong failure mode — says "glob expansion fails silently when too many files match" but the actual V19 regression was zsh treating unmatched globs as errors. -> Change the comment to: "Never use `rm -f dir/*` for cleanup — zsh treats unmatched globs as errors, causing cleanup to fail on empty directories. `find -delete` handles empty-or-full directories reliably."
- [ ] **[Conf: 65] [regression-checker]** Post-deploy monitoring for 5 consecutive scheduled runs mentioned in design but post-deploy checks only verify single workflow_dispatch. -> Add a note in post-deploy checks to monitor first 5 scheduled runs before declaring V20 stable.
- [ ] **[Conf: 60] [architecture-strategist]** Context Budget lists `python3 scripts/manage_state.py` CLI as parent-allowed, and HC5 (Step 7) carves out the same exception, but wording differs slightly — HC5 says "Steps 13-14" while Context Budget doesn't reference specific steps. -> Align HC5 exception wording with Context Budget row by referencing "manage_state.py CLI subcommands (state sync)" in both locations.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** The `cd 03_agents/tests/v20` inside nick-fields/retry is the correct resolution — retry actions run in a fresh shell context. The explanatory comment added in revise is helpful. (Conf: 55)
- **[architecture-strategist]** Dual-source permissions sync check (R6) is manual. If permissions grow significantly over future versions, this could become a maintenance burden. No action needed now. (Conf: 52)
- **[code-simplicity-reviewer]** Step 3 dedup tests: `TestLocationNormalization` still tests `.lower().strip()` behavior more than dedup logic. Noted in Round 1, unchanged — informational only. (Conf: 52)
- **[code-simplicity-reviewer]** Round 1 POST-BATCH/POST-PRESENTATION script extraction was deferred as "Future improvement (Rec7)" — acceptable. (Conf: 55)
- **[regression-checker]** V17 Vercel-compatible API handler regression is out of scope — no dashboard changes in V20. (Conf: 55)
- **[regression-checker]** V14 "No ad-hoc HTTP servers" not re-stated but not contradicted. (Conf: 50)
- **[regression-checker]** nick-fields/retry `cd` with explanatory comment adequately addresses Round 1 Rec6. (Conf: 52)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: APPROVED

### Statistics
- Total findings collected: 9 (across all reviewers)
- Final actionable findings: 4 (0 Required, 1 Recommended, 3 Nice-to-Have)
- Informational notes: 7
- Overlap instances: 0

### Round 1 Fix Verification
All 17 findings from Round 1 (7 Required + 10 Recommended) were verified as properly applied by all 3 reviewers. No regressions introduced by revisions.

---

## Round 1 — 2026-02-18

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
- [x] **[Conf: 96] [regression-checker]** session-state.md not committed after each search batch — Step 11b stages `output/ state.json` but not `output/session-state.md`. V14/V16/V18 triple recurrence makes this highest-risk. -> Add explicit instruction in Step 11b: write session-state.md and include `output/session-state.md` in the `git add` command after each search batch.
- [x] **[Conf: 95] [regression-checker]** settings.local.json additive-merge rule not reinforced in CLAUDE.md for interactive mode — CI creates from scratch (OK), but agent instructions lack explicit "merge, don't overwrite" constraint. -> Add a hard constraint in CLAUDE.md: "settings.local.json edits in interactive mode must merge into existing permissions, never overwrite the file."
- [x] **[Conf: 95] [regression-checker]** API keys must never appear as CLI arguments (V15/V18 regression) — Step 18 correctly uses env vars for CI, but no CLAUDE.md hard constraint guards interactive sessions. -> Add hard constraint: "API keys must never appear in Bash command arguments — use environment variables or stdin redirection."
- [x] **[Conf: 92] [architecture-strategist]** Step 17 settings.local.json edit removes 3 existing permission entries and replaces with 2 new ones — violates V18 additive-only regression guard. -> Change Step 17 to ADD `Bash(git log:*)` and `Bash(git diff:*)` to the permissions array without removing ANY existing entries. Stale entries are harmless; removing them violates the guard. (overlaps with regression-checker finding above)
- [x] **[Conf: 88] [architecture-strategist]** Missing explicit Context Budget table — V18 regression requires clear parent-allowed vs. subagent-only tool enumeration. Step 7 (HC5) strengthens Python restriction but no consolidated enforcement artifact. -> Add a Context Budget section to CLAUDE.md enumerating: parent-allowed tools (git, Task dispatch, Bash for commit/push, send_email.py, manage_state.py CLI) vs. subagent-only tools (WebFetch, WebSearch, python3 for data processing, file reads of source/verified JSONs).
- [x] **[Conf: 85] [architecture-strategist, code-simplicity-reviewer]** Dual-source permission lists — Step 17 modifies local settings.local.json, Step 18 hardcodes a separate 30+ line inline permissions list in GH Actions YAML. Two independent sources of truth will drift. -> Extract canonical permission list to a single source, or document that GH Actions inline is authoritative for CI and add a sync verification step. (overlaps noted between both reviewers)
- [x] **[Conf: 85] [code-simplicity-reviewer]** Steps 13-16 are nearly identical repetitive edits — 4 plan steps doing the same mechanical find-and-replace (swap `v18` to `{working_dir}`, update variable count) across 6 agent files. -> Merge Steps 13-16 into a single step with a table listing each file and its specific variable count change. Describe the working_dir and first-action patterns once, then "apply to all agent files."

### Recommended Changes
- [x] **[Conf: 78] [architecture-strategist]** No validation that `working_dir` points to an existing directory before subagent work begins — typo or stale value causes deep failure. -> Add startup assertion in agent preamble: `test -d {working_dir} || exit 1` before file operations.
- [x] **[Conf: 78] [regression-checker]** V14 regression: parent must verify visual output after digest-email and briefs-html subagents complete (post-render check) — plan adds POST-PRESENTATION and POST-BATCH but no post-render visual check. -> Add verification note after Step 19 dispatches: "verify output HTML files exist and contain expected content markers."
- [x] **[Conf: 75] [architecture-strategist]** POST-BATCH COMMIT VERIFICATION (Step 6b) has no retry bound or escalation — persistent git failure loops indefinitely. -> Add max-retry count (2) and escalation: if commit fails after retries, write warning to session-state.md and continue.
- [x] **[Conf: 75] [code-simplicity-reviewer]** Dashboard URL concern scattered across Steps 5, 15, and 16b — builder must touch 3 steps to understand the full fix. -> Consolidate all dashboard URL changes into one step or add explicit cross-references.
- [x] **[Conf: 75] [regression-checker]** V17 regression: post-deploy smoke test must verify /api/jobs returns 200 — Step 18 preflight checks claude CLI and API key but not dashboard API health. -> Add /api/jobs health check to preflight step in daily-digest.yml.
- [x] **[Conf: 72] [architecture-strategist]** Step 18 retry action uses `cd 03_agents/tests/v20` duplicating `working-directory` default — drift vector if version path changes. -> Remove redundant `cd` since `working-directory` is already set as job default.
- [x] **[Conf: 72] [code-simplicity-reviewer]** POST-PRESENTATION and POST-BATCH COMMIT verifications are prose-based enforcement in CLAUDE.md — fragile given prior regression history. -> Consider extracting to verification scripts (e.g., `scripts/verify_commit.sh`) returning non-zero on failure.
- [x] **[Conf: 72] [regression-checker]** Bash permissions audit incomplete — Step 17 adds git log/diff and removes stale entries but doesn't verify full subagent command coverage. -> Audit settings.local.json covers all known subagent Bash commands (python3, find, ls, git, etc.).
- [x] **[Conf: 70] [code-simplicity-reviewer]** Step 12 agent memory FATAL assertion is 3 lines of verbose prose. -> Simplify to single-line: "FATAL: 0 agent memory files found — check .claude/agent-memory/ paths."
- [x] **[Conf: 70] [code-simplicity-reviewer]** Step 4 has 6 sub-edits (4a-4f) quoting each dispatch template in full — verbose. -> Use summary table showing pattern once, then list locations. Builder applies to each without full before/after.

### Nice-to-Have
- [ ] **[Conf: 65] [architecture-strategist]** Dedup collision key fields are inline in `_compute_dedup` — adding fields requires editing function body. -> Extract key fields to a configurable constant.
- [ ] **[Conf: 65] [regression-checker]** Plan could add post-deploy monitoring for 5 consecutive scheduled runs, not just single workflow_dispatch. -> Add note in post-deploy checks about monitoring first 5 runs.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** `nick-fields/retry@v3` `command:` field may run outside job-level `defaults.run.working-directory` scope — verify retry action respects job defaults. (Conf: 58)
- **[architecture-strategist]** Plan doesn't address stale v18 references already present in v19 files beyond explicitly listed ones; grep check exists in deployment verification but not as a gated step. (Conf: 55)
- **[code-simplicity-reviewer]** Step 18 full YAML rewrite means opaque diff in review — consider a comment block at top listing what changed. (Conf: 55)
- **[code-simplicity-reviewer]** Step 3 dedup tests (80+ lines) — `TestLocationNormalization` tests Python's `.lower().strip()` more than dedup logic. (Conf: 52)
- **[regression-checker]** V17 Vercel-compatible API handlers regression is out of scope (no dashboard changes planned). (Conf: 55)
- **[regression-checker]** V14 "No ad-hoc HTTP servers" regression not re-stated but not contradicted. (Conf: 50)

### Per-Reviewer Verdicts
- architecture-strategist: Needs Changes
- code-simplicity-reviewer: Needs Changes
- regression-checker: Needs Changes

### Statistics
- Total findings collected: 22 (across all reviewers)
- Final actionable findings: 19 (7 Required, 10 Recommended, 2 Nice-to-Have)
- Informational notes: 6
- Overlap instances: 2 (settings.local.json additive + dual-source permissions)

# JSA V21 Reviews

## Round 3 — 2026-02-19

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
None.

### Recommended Changes
- [x] **[Conf: 74] [architecture-strategist]** manage_state.py dedup operates on two distinct dimensions (cross-role company+title, within-role same-URL) with different key extraction logic, yet both share the same archive-or-keep flow. Step 4 describes them inline as prose with no structural separation. -> Extract matching logic into separate functions: `_find_cross_role_duplicates()` and `_find_same_url_duplicates()` each return a list of (keep, archive) pairs, and a single `_apply_archive()` processes them. Prescribe this in Step 4's implementation spec.
- [x] **[Conf: 73] [code-simplicity-reviewer]** Step 20 preflight.sh "CLI flag validation" tier parses `manage_state.py dedup --help` output for expected flags — help text is not a stable interface and any argparse formatting change breaks the check. -> Replace CLI flag validation with a direct invocation test: `python3 scripts/manage_state.py dedup --dry-run --verified-dir output/verified --archive-dir output/archive` exits 0. Validates flags actually work rather than parsing help text.

### Nice-to-Have
- [x] **[Conf: 70] [architecture-strategist]** preflight.sh flag dispatch (`--env` / `--structure` / no flag = all) has no dedicated tests verifying each flag correctly limits which checks run. -> Add two tests to Step 19: `test_preflight_env_only_skips_structure_checks` and `test_preflight_structure_only_skips_env_checks`.
- [ ] **[Conf: 65] [code-simplicity-reviewer]** Step 7 orchestration.md copy spec for incremental commits prescribes exact verbatim text that "must appear" — pinning exact prose makes future wording edits require plan amendments. -> Prescribe semantic requirement (per-batch commit+push with git commands) but verify via grep pattern rather than mandating verbatim prose.
- [ ] **[Conf: 65] [regression-checker]** V16 regression: score threshold inclusive (>=70 not >70). No explicit boundary test for score exactly 70. -> Add `test_dedup_preserves_score_exactly_70` to Step 3. (Carried from Round 1, still unaddressed, low priority.)

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** preflight.sh exit code conflates state-management failure (manage_state.py) with structural-validation failure. Separating exit codes or distinct output prefixes would help debugging. (Conf: 58)
- **[architecture-strategist]** jsa-config.json `roles` array item schema (required fields per role object) remains unspecified. Config drift between JSON and consuming code will be silent until runtime. (Conf: 55)
- **[code-simplicity-reviewer]** Step 6 still exists as a pure requirements-definition step producing no artifact — all its content feeds into Step 20. Merging into Step 20 would reduce step count. Not re-flagged. (Conf: 55)
- **[code-simplicity-reviewer]** Step 14 verification commands remain dense one-liners with nested Python `-c` invocations. Low impact. (Conf: 52)
- **[regression-checker]** V17 deployment regressions (Vercel), V19 GH Actions timeout (>=90 min), and V19 retry logic are not addressed — out of V21 scope (code infrastructure, not deployment). (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: APPROVED

### Statistics
- Total findings collected: 8 (across all reviewers)
- Final actionable findings: 5 (0 Required, 2 Recommended, 3 Nice-to-Have)
- Informational notes: 5

---

## Round 2 — 2026-02-19

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
- [x] **[Conf: 96] [regression-checker]** Step 9 states manage_state.py calls in ON STARTUP "are executed by preflight.sh" but Step 20 (preflight.sh spec) lists only validation checks — no invocation of manage_state.py. Cleanup/dedup will never execute at startup. V19 regression: parent must NEVER run `python3 scripts/*` directly. -> Either (a) add `python3 scripts/manage_state.py cleanup && python3 scripts/manage_state.py dedup` to the preflight.sh spec in Step 20 (after critical checks pass), or (b) remove the parenthetical claim in Step 9 and document ON STARTUP manage_state.py invocation as an explicit exception to the V19 rule with rationale. Add a test in Step 19 confirming the behavior.
- [x] **[Conf: 95] [regression-checker]** V20 regression requires settings.local.json include Read, Write, Glob, Grep tool permissions for background subagent operation. Step 14 only adds Bash command permissions (`python3 scripts/*`, `bash scripts/*`). These are different permission types — Bash commands vs Claude Code tools. -> Add Read, Write, Glob, Grep tool permissions to the Step 14 merge list, matching V20's requirement for background subagent tool access.
- [x] **[Conf: 88] [architecture-strategist]** Archive manifest `_manifest.json` (Step 4) has no consumer anywhere in the plan — not in State Architecture section, not read by any step, not tested. Orphaned write with no read path. -> Either (a) add `_manifest.json` to State Architecture in Step 7 with owner=manage_state.py, consumers=TBD, lifecycle=append-only, or (b) remove the manifest requirement from Step 4 entirely since no V21 component reads it. (overlaps with code-simplicity-reviewer finding below)
- [x] **[Conf: 85] [architecture-strategist]** CLI flag names pinned in two places: manage_state.py argparse (Step 4) and orchestration.md Phase 3 (Step 7). No mechanism validates they match — mismatch causes silent runtime failure. -> Add a preflight.sh check that runs `python3 scripts/manage_state.py dedup --help` and validates expected flags appear in output. Or remove duplicated flag names from orchestration.md and reference `manage_state.py --help` instead.
- [x] **[Conf: 82] [architecture-strategist, code-simplicity-reviewer]** Email idempotency gate (Step 17) lives exclusively in digest-email subagent reference file. If parent dispatches via recovery path or different subagent, gate is bypassed. Also: _manifest.json is write-only complexity per code-simplicity-reviewer (Conf: 82). -> Move `_status.json` email-sent check to orchestration.md Phase 5 entry criteria. Subagent retains defensive check, but orchestration owns the authoritative gate. For _manifest.json: remove from Step 4 (no current consumer).

### Recommended Changes
- [x] **[Conf: 78] [code-simplicity-reviewer]** jsa-config.json schema validated in both preflight.sh (Step 20) AND Python assertions in Step 11 verify block — duplicate enforcement. -> Let preflight.sh be the single config validation authority. Remove inline Python assertions from Step 11's verify block (keep only basic parse check at creation time).
- [x] **[Conf: 75] [architecture-strategist, code-simplicity-reviewer]** preflight.sh (Step 20) conflates environment validation and structural linting. CLAUDE.md structure checks only change when developer modifies plan artifacts — they always pass during normal runs. -> Either (a) add flag-based dispatch (`preflight.sh --env` / `preflight.sh --structure`), or (b) split structural checks into separate `lint.sh` and keep preflight.sh focused on runtime prerequisites.
- [x] **[Conf: 75] [regression-checker]** V17 regression: GH Actions workflows must live at repo root `.github/workflows/`. Plan modifies nested `03_agents/tests/v21/.github/workflows/daily-digest.yml`. -> Add a note in Step 12 clarifying whether nested workflow is development copy or production location, acknowledging V17 regression.
- [x] **[Conf: 72] [architecture-strategist]** Step 9 Context Budget section adds heading but no verification that content actually lists correct parent-allowed vs subagent-only tools. -> Add verify: `grep -q "WebFetch" CLAUDE.md` within Context Budget section to confirm subagent-only tools are enumerated.
- [x] **[Conf: 72] [regression-checker]** V19 regression: model: parameter grep check (Step 7) covers orchestration.md and subagent-*.md but not CLAUDE.md itself. Step 9 adds dispatch table to CLAUDE.md which could contain dispatch patterns. -> Extend the model: grep verification to also check CLAUDE.md.
- [x] **[Conf: 72] [code-simplicity-reviewer]** orchestration.md `## State Architecture` section (Step 7) maps every state file's owner/consumers/lifecycle — documentation overhead that drifts immediately. -> Drop State Architecture section or reduce to one-liner comments per file.
- [x] **[Conf: 70] [regression-checker]** V14/V16/V18/V19/V20 5-version recurrence: incremental commit+push per batch. Step 7 grep pattern (`commit.*push|incremental commit|per-batch commit`) is loose — could match comment rather than actionable instruction. -> Prescribe exact copy spec in Step 7 for the commit instruction in orchestration.md Phase 1 (e.g., "After each search batch: `git add output/ && git commit -m 'batch N complete' && git push`").

### Nice-to-Have
- [x] **[Conf: 70] [architecture-strategist]** Step 4 archive directory `output/archive/{role}/{filename}` does not mention `os.makedirs(exist_ok=True)` for creating subdirectories — could cause FileNotFoundError. -> Add explicit `os.makedirs` to Step 4 implementation spec.
- [ ] **[Conf: 65] [code-simplicity-reviewer]** Archive directory uses role-partitioned structure. A flat `output/archive/` with no subdirectories would be simpler. -> Consider flat archive unless role-partitioned browsing is a real use case.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** Step 12 says "create settings.local.json during CI setup" but doesn't specify template copy vs inline heredoc generation. V20 regression about heredoc producing invalid JSON makes mechanism choice important. (Conf: 65)
- **[architecture-strategist]** jsa-config.json nested object schema (e.g., `roles` array item shape) is unspecified. Config drift between JSON and consuming code will be silent. (Conf: 60)
- **[architecture-strategist]** manage_state.py dedup normalization (`.lower().strip()`) may diverge from search-verify subagent normalization. No single source of truth for normalization is designated. (Conf: 55)
- **[code-simplicity-reviewer]** Step 6 defines requirements for Step 20 but produces no artifact — exists purely as requirements spec step. Merging into Step 20 would reduce step count by one. (Conf: 55)
- **[code-simplicity-reviewer]** Plan tracks 10 implementation constraints (I1-I10) distributed across 6 steps. Reader must cross-reference Handoff Contract footnote to locate each. (Conf: 52)
- **[regression-checker]** V17 regressions about Vercel deployment and V19 GH Actions timeout (>=90 min) are not addressed, but V21 scope is code infrastructure, not deployment. Likely out of scope. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: Needs Changes
- code-simplicity-reviewer: Needs Changes
- regression-checker: Needs Changes

### Statistics
- Total findings collected: 24 (across all reviewers)
- Final actionable findings: 19 (5 Required, 7 Recommended, 2 Nice-to-Have, 5 overlapping — deduplicated into combined entries)
- Informational notes: 6

---

## Round 1 — 2026-02-19

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
- [x] **[Conf: 96] [regression-checker]** Step 14 `settings.local.json` update lacks additive-merge instruction — V18 regression requires modifications be additive, never overwrite. -> Add explicit instruction in Step 14: "Read existing settings.local.json, merge new permissions into existing `allow` array, write back. Do NOT overwrite the file." (overlaps with architecture-strategist finding below)
- [x] **[Conf: 92] [architecture-strategist]** Context Budget section mentioned (Step 9, test_claude_md_has_context_budget) but plan never specifies its contents — V18 regression requires explicit listing of which tools parent may call directly vs subagent-only. -> Step 9 must include the exact Context Budget content: list parent-allowed tools (dispatch, read status files, present results, git) vs subagent-only tools (WebFetch, WebSearch, search, filter, dedup, file reading).
- [x] **[Conf: 95] [regression-checker]** Incremental commit+push per search batch has no verification step in orchestration.md — 5-version recurrence (V14/V16/V18/V19/V20). -> Add verification step after Step 7: `grep -q "commit.*push.*batch\|incremental commit" references/orchestration.md` to confirm per-batch commit+push is documented with explicit enforcement.
- [x] **[Conf: 95] [regression-checker]** Plan does not verify parent orchestrator never runs `python3 scripts/*` directly (V19 regression). Step 9 ON STARTUP has manage_state.py call. -> Clarify in Step 9 that ON STARTUP `python3 scripts/manage_state.py pre-run` is either (a) executed by preflight.sh (not parent), or (b) explicitly exempted with justification. Add verification: CLAUDE.md must not contain direct `python3 scripts/*` calls outside ON STARTUP.
- [x] **[Conf: 95] [regression-checker]** No verification that `model:` parameter is absent from Task tool dispatch templates (V19 HC1). -> Add verification in Step 7 or Step 9: `grep -rq "model:" references/orchestration.md references/subagent-*.md` should return no matches in dispatch blocks.
- [x] **[Conf: 88] [architecture-strategist]** manage_state.py dedup archives duplicates but no interface contract for archive directory structure or how downstream consumers discover archived vs active jobs. V20 warns: dedup must not break dashboard API. -> Define archive directory contract: path structure (`output/archive/{role}/{filename}`), manifest/metadata linking archived files to replacements, dashboard API excludes archived files.
- [x] **[Conf: 85] [architecture-strategist]** settings.local.json merge strategy unspecified (Step 14). V18 regression: must be additive-only. -> Step 14 must specify: read existing JSON, merge new permission entries into existing `allow` array, write back. Include verification that existing permissions count >= pre-modification count. (overlaps with regression-checker Conf 96 finding above)
- [x] **[Conf: 85] [code-simplicity-reviewer]** 4 separate test files for manage_state — `test_manage_state_cleanup.py` and `test_manage_state_dedup.py` split across 2 files for a single CLI tool. -> Merge into single `test_manage_state.py`. They test the same script and share fixture setup.
- [x] **[Conf: 82] [code-simplicity-reviewer]** `test_claude_md_structure.py` — 14 Python tests that grep markdown headings and count lines is over-engineered for a linting concern. -> Replace with inline checks in `preflight.sh` (which already validates structural properties). Add "CLAUDE.md structure" tier to preflight.sh. Delete separate test file.
- [x] **[Conf: 78] [code-simplicity-reviewer]** `pre-run` subcommand in manage_state.py is just an alias calling cleanup then dedup sequentially — third code path for zero logic. -> Remove `pre-run`. In ON STARTUP, call `python3 scripts/manage_state.py cleanup && python3 scripts/manage_state.py dedup`. Two explicit commands are clearer.

### Recommended Changes
- [x] **[Conf: 85] [regression-checker]** Step 4 dedup does not mention within-role same-URL dedup — V20 regression requires catching same-URL duplicates within a role. -> Add test case `test_dedup_same_url_within_role` in Step 3 and implement URL-based dedup in Step 4.
- [x] **[Conf: 80] [regression-checker]** No verification that cross-role dedup preserves at least one copy per unique job (V20 dashboard API dependency). -> Add test case `test_dedup_preserves_at_least_one_copy` in Step 3.
- [x] **[Conf: 80] [regression-checker]** No verification that presentation-rules.md (Step 8) enforces identical table format for ALL role types (V19/V20 recurrence). -> Add verification: `grep -q "identical.*table\|same.*format\|uniform.*table" references/presentation-rules.md`.
- [x] **[Conf: 78] [architecture-strategist]** orchestration.md Phase 3 (Dedup) calls manage_state.py but interface is implicit — CLI argparse flags may not match orchestration references. -> orchestration.md Phase 3 must include exact CLI invocations with correct flags. Pin flag names in one place.
- [x] **[Conf: 78] [regression-checker]** ON STARTUP does not verify `.claude/agent-memory/*/MEMORY.md` read (V14/V17/V19 recurrence — HC4). -> Add verification in Step 9: CLAUDE.md ON STARTUP must include explicit agent-memory read step.
- [x] **[Conf: 75] [architecture-strategist]** State ownership split across 4 files (`_status.json`, checkpoint JSONs, `session-state.md`, `state.json`) with no documented relationships. -> Add "State Architecture" section to orchestration.md mapping each state file to owner, consumers, and lifecycle.
- [x] **[Conf: 75] [code-simplicity-reviewer]** Phase dispatch table in CLAUDE.md uses `§` section references — no tooling support, adds indirection without enforcement. -> Use simple file references without section notation. Agent finds sections naturally by phase headings.
- [x] **[Conf: 75] [regression-checker]** Cleanup doesn't cross-reference state.json before deleting verified files (V20 regression). -> Add test `test_cleanup_never_touches_verified_with_active_jobs` in Step 2.
- [x] **[Conf: 73] [code-simplicity-reviewer]** Checkpoint JSON protocol in orchestration.md is premature generalization — no evidence of failure mode it solves. -> Drop checkpoint JSON protocol. Continue using session-state.md. Add checkpointing in future version if needed.
- [x] **[Conf: 72] [architecture-strategist]** preflight.sh validates structure but not content — reference files could exist but lack required sections. -> Add content-level checks: verify each phase heading in orchestration.md, verify presentation-rules.md has table format section.
- [x] **[Conf: 72] [regression-checker]** GH Actions must create `settings.local.json` during CI setup since it's gitignored (V17/V19 regression). Step 12 doesn't mention this. -> Add instruction in Step 12: workflow creates `settings.local.json` before running preflight.
- [x] **[Conf: 72] [code-simplicity-reviewer]** Deployment Verification section duplicates preflight.sh — three blocks totaling ~50 lines of redundant bash. -> Consolidate: preflight.sh for pre-deploy, 3-line post-deploy smoke test, keep rollback as-is.
- [x] **[Conf: 70] [architecture-strategist]** jsa-config.json (Step 11) schema is unspecified — no validation beyond "is valid JSON." -> Define expected top-level keys and add schema check to preflight.sh or a test.

### Nice-to-Have
- [ ] **[Conf: 65] [architecture-strategist]** Dispatch table `§` notation references not cross-referenced against actual file headings. -> Add test in test_claude_md_structure.py (or preflight.sh) that cross-references dispatch table references against actual headings. (overlaps with code-simplicity-reviewer Recommended on `§` notation)
- [ ] **[Conf: 65] [code-simplicity-reviewer]** Step 14 verification is deeply nested one-liner, hard to read. -> Replace with simpler `grep -q "scripts" .claude/settings.local.json && echo "ok"`.
- [ ] **[Conf: 65] [regression-checker]** Could add test verifying score threshold is inclusive (>=70 not >70) per V16 regression. -> Add `test_dedup_preserves_score_exactly_70`.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** Plan sequences Phases 1-5 linearly but notes Phase 3 "can run in parallel" with Phase 2 — ambiguity about intended execution order. (Conf: 55)
- **[architecture-strategist]** manage_state.py dedup logic may duplicate normalization rules in subagent-search-verify.md — if normalization diverges, dedup misses matches. (Conf: 60)
- **[code-simplicity-reviewer]** 9 new files + 6 modified across 22 steps for a refactoring version (no new capabilities) — high file count but each file serves distinct purpose. (Conf: 55)
- **[code-simplicity-reviewer]** `--dry-run` flag on all manage_state subcommands adds test surface (3 dry-run tests) — could defer if only used in development. (Conf: 52)
- **[regression-checker]** Brief generation speed addressed (Step 16 I10) — covers V14/V20 performance regressions. (Conf: 60)
- **[regression-checker]** Dashboard URL addressed in Steps 13 and 20 — covers V18/V19/V20 mandatory dashboard regressions. (Conf: 55)

### Per-Reviewer Verdicts
- architecture-strategist: Needs Changes
- code-simplicity-reviewer: Needs Changes
- regression-checker: Needs Changes

### Statistics
- Total findings collected: 28 (across all reviewers)
- Final actionable findings: 26 (10 Required, 13 Recommended, 3 Nice-to-Have)
- Informational notes: 6

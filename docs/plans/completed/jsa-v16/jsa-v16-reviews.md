# JSA V16 Reviews

## Round 3 — 2026-02-11

### Reviewer 1: DHH (Rails Pragmatist)

#### Required Changes

(none)

#### Recommended Changes

(none)

#### Nice-to-Have

- [ ] **The overview claims "8-10 queries/industry" but the actual skill template yields 7-11.** (Carried from Rounds 1-2, still unfixed.) Category 1: 0, Category 2: 2-3, Category 3: 2-3, Category 4: 1-2, Category 5: 2-3. The overview should say "up to ~11 queries/industry" for accuracy. Not a blocker — the subagent will do what the skill says regardless of what the overview claims.

- [ ] **Step 31's `.gitkeep` survival during output cleanup is still not guaranteed.** (Carried from Rounds 1-2, still unfixed.) `rm -f 03_agents/tests/v16/output/verified/*/*` will delete `.gitkeep` files in subdirectories of `verified/`. The builder should be aware and either exclude `.gitkeep` or re-create them after cleanup.

#### Approval Status: **APPROVED for build**

Round 2's recommended findings have all been cleanly addressed. Step 2b's `sources_for_role` pre-build verification is exactly the right pattern — turns a build-time surprise into a plan-time decision with clear branching. The `cwd=scripts_dir.parent` addition to the subprocess test closes the CI portability gap. No new concerns.

---

### Reviewer 2: Kieran (Execution & Completeness)

#### Required Changes

(none)

#### Recommended Changes

(none)

#### Nice-to-Have

- [ ] **Commit messages still don't include phase numbers.** (Carried from Rounds 1-2, still unfixed.) e.g., "feat(jsa): [P2] add brief_requested action type". This is a navigation aid, not a blocker.

- [ ] **Step 29's `.gitignore` verification could be more precise.** (Carried from Rounds 1-2, still unfixed.) Checking `grep -c "output/" .gitignore` is a loose proxy. A more precise check would verify `output/_source_research*.json` is covered. Builder can handle this at build time.

#### Approval Status: **APPROVED for build**

All Round 2 recommended findings resolved. The `record-action` CLI now has an explicit comment documenting that `record_action()` validates against `VALID_ACTIONS` internally (Step 25, lines 1016-1017) — clear enough for the builder to understand the design decision. Phase 5 title now includes "(Fix #2 continuation — CLI-only state mutations)" which closes the cross-reference gap. No new concerns.

---

### Reviewer 3: Code Simplicity

#### Required Changes

(none)

#### Recommended Changes

(none)

#### Nice-to-Have

- [ ] **Step 23 (API key piping for scheduled runs) is still orphaned in the orchestration workflow.** (Carried from Rounds 1-2, still unfixed.) It belongs in the SCHEDULED RUNS section since it only applies during scheduled run setup. Having it as an orchestration step implies it runs every session. The builder can relocate it if desired.

- [ ] **The source researcher skill's output file naming uses underscore prefix (`_source_research.json`) which is consistent with other internal outputs, but the status file (`_source_research_status.json`) duplicates the "source_research" prefix.** (Carried from Round 2, still unfixed.) Consider `_source_status.json` for brevity. Not a blocker.

#### Approval Status: **APPROVED for build**

Round 2's single recommended finding — git pull duplication in orchestration Step 2 — is now resolved cleanly. Step 2 reads: "**Step 2: Git pull (interactive mode only).** See ON STARTUP step 3." No redundant restatement, single source of truth. The plan is tight. Remaining nice-to-haves are cosmetic preferences that the builder can address opportunistically.

---

### Round 3 Summary

| Reviewer | Status |
|----------|--------|
| DHH | APPROVED |
| Kieran | APPROVED |
| Code Simplicity | APPROVED |

**Consensus: APPROVED for build.**

All Round 2 recommended findings have been addressed. Zero required changes, zero recommended changes across all three reviewers. The remaining nice-to-have items (6 total, all carried from previous rounds) are cosmetic preferences scored below 70 confidence. The plan is ready for `/build`.

<!-- STAGE COMPLETE: /review round 3, 2026-02-11 -->

---

## Round 2 — 2026-02-11

### Reviewer 1: DHH (Rails Pragmatist)

#### Required Changes

(none)

#### Recommended Changes

- [x] **Step 9's `sources_for_role` handling defers verification to build time, which creates a silent-failure risk.** The note says "V15's search-verify agent already receives and uses `sources_for_role` in its template — verify this during build." This is better than Round 1 (where it was unacknowledged), but "verify during build" is a weak contract. If the builder discovers during Step 15 that V15's search-verify agent does NOT consume `sources_for_role`, they'll need to stop and create a new step mid-build. The plan should include a pre-build verification step in Phase 1 (after copying V15 to V16): `grep "sources_for_role" 03_agents/tests/v16/.claude/agents/search-verify.md 03_agents/tests/v16/.claude/skills/jsa-search-verify.md`. If found, proceed. If not found, the plan needs a step to add it. This turns a build-time surprise into a plan-time decision.

- [x] **The `record-action` CLI test (Step 24) uses `subprocess.run` but doesn't set a working directory or `PYTHONPATH`.** The test resolves `scripts_dir` via `Path(__file__).resolve().parent.parent / "scripts"`, which is correct for finding the script file. But when `manage_state.py` runs as a subprocess, it needs to import its own modules. If `manage_state.py` has any relative imports or reads files from CWD, the test could pass locally but fail in CI depending on where pytest is invoked from. The existing V15 tests presumably work without subprocess (they import directly), so this is a new pattern. Consider adding `cwd=scripts_dir.parent` to the `subprocess.run` call to match the expected working directory.

#### Nice-to-Have

- [ ] **The overview claims "8-10 queries/industry" but the actual skill template yields 7-11.** (Carried from Round 1, still unfixed.) Category 1: 0, Category 2: 2-3, Category 3: 2-3, Category 4: 1-2, Category 5: 2-3. Range is 5-11 if you count the minimums and maximums. The overview should say "7-11 queries/industry" or round to "up to ~11 queries/industry" for accuracy.

- [ ] **Step 31's `.gitkeep` survival during output cleanup is still not guaranteed.** (Carried from Round 1, still unfixed.) `rm -f 03_agents/tests/v16/output/verified/*/*` will delete `.gitkeep` files in subdirectories of `verified/`. Either add `! -name ".gitkeep"` logic or add a post-cleanup verify that `.gitkeep` files still exist in each output subdirectory.

#### Approval Status: **APPROVED for build**

The Round 1 required changes have been properly addressed. The `save-after-feedback` reference is gone, version references are enumerated, the builder note disambiguates nested code fences, and the cross-reference uses section anchors. The remaining recommended items are genuine improvements but not blockers — the builder can handle them.

---

### Reviewer 2: Kieran (Execution & Completeness)

#### Required Changes

(none)

#### Recommended Changes

- [x] **The `record-action` CLI implementation (Step 25) doesn't validate that `--action` is a valid action.** The `_cli_record_action` function calls `record_action(state, args.job_key, args.action)` — if the underlying `record_action` function validates against `VALID_ACTIONS`, this is fine. But the plan doesn't confirm that. If someone calls `manage_state.py record-action --action "typo"`, does it fail gracefully or silently write bad data? The plan should note that `record_action` already validates, or add validation in the CLI wrapper.

- [x] **Phase 5 title still says "Add CLI Subcommand to manage_state.py" (singular) but the Phase 2 title references "(Fix #1 + Fix #2)".** This is cosmetic but creates an asymmetry — Phase 2 clearly cross-references which design fixes it addresses, while Phase 5 doesn't. Adding "(Fix #2 continuation)" or similar would help the builder track which of the 7 fixes each phase covers.

#### Nice-to-Have

- [ ] **Commit messages still don't include phase numbers.** (Carried from Round 1, still unfixed.) e.g., "feat(jsa): [P2] add brief_requested action type". This is a navigation aid, not a blocker.

- [ ] **Step 29's `.gitignore` verification could be more precise.** (Carried from Round 1, still unfixed.) Checking `grep -c "output/" .gitignore` is a loose proxy. A more precise check would verify `output/_source_research*.json` is covered.

#### Approval Status: **APPROVED for build**

All Round 1 required changes are resolved. The `save-after-feedback` ghost is gone — Step 17 explicitly documents that `record-action` persists state internally. The nested code fence ambiguity is resolved with the builder note. The `sources_for_role` handling is documented (though I'd prefer a pre-build check as DHH suggests). The test count is now verified in Phase 1. Ready to build.

---

### Reviewer 3: Code Simplicity

#### Required Changes

(none)

#### Recommended Changes

- [x] **The orchestration workflow Step 2 still contains git pull instructions alongside the ON STARTUP reference.** Step 2 says: "Git pull (interactive mode only). See ON STARTUP step 3 for full git pull protocol. Execute and verify success before proceeding." This is improved from Round 1 (it now references ON STARTUP step 3 instead of duplicating), but it still restates "Execute and verify success before proceeding" — which is already covered in the referenced step. For maximum clarity, Step 2 should be just: "**Step 2: Git pull (interactive mode only).** See ON STARTUP step 3." No additional instructions needed since the referenced step is authoritative.

#### Nice-to-Have

- [ ] **Step 23 (API key piping for scheduled runs) is still orphaned in the orchestration workflow.** (Carried from Round 1, still unfixed.) It belongs in the SCHEDULED RUNS section since it only applies during scheduled run setup. Having it as an orchestration step implies it runs every session, which is misleading.

- [ ] **The source researcher skill's output file naming uses underscore prefix (`_source_research.json`) which is consistent with other internal outputs (`_status.json`, `_delta.json`, `_summary.md`), but the status file (`_source_research_status.json`) duplicates the "source_research" prefix.** Consider just `_source_status.json` for brevity, or keep as-is for explicitness. Not a blocker.

#### Approval Status: **APPROVED for build**

The plan is materially sound. All Round 1 blockers are resolved cleanly. The `save-after-feedback` phantom is eliminated with a clear note about `record-action` auto-persisting. The WebFetch budget is now count-based (15 sources) instead of time-based — pragmatic and enforceable. The nested code fence builder note removes ambiguity. The remaining items are polish, not substance.

---

### Round 2 Summary

| Reviewer | Status |
|----------|--------|
| DHH | APPROVED |
| Kieran | APPROVED |
| Code Simplicity | APPROVED |

**Consensus: APPROVED for build.**

All Round 1 required changes have been addressed. The remaining findings are recommended improvements and nice-to-haves — none are blockers. The plan is ready for `/build`.

<!-- STAGE COMPLETE: /review round 2, 2026-02-11 -->

---

## Round 1 — 2026-02-11

### Reviewer 1: DHH (Rails Pragmatist)

#### Required Changes

- [x] **Step 18 references `save-after-feedback` CLI subcommand that is never implemented.** Step 17 in the orchestration workflow calls `python3 scripts/manage_state.py save-after-feedback --state state.json`, and Step 18 (the plan step) mentions it in the SCHEDULED RUNS section. But Phase 5 only implements `record-action`. There's no test, no implementation, and no definition of what `save-after-feedback` even does. Either implement it (add a step) or remove all references to it.

- [x] **Step 2 version reference update is underspecified.** The step says to find-and-replace `v15` → `v16` in `.claude/agents/*.md` and `.claude/skills/*.md`, but doesn't enumerate which files exist. If V15 has 5 agent files and 4 skill files, you need to know which ones. The verify step only checks `.claude/` but the plan also mentions updating `manage_state.py` docstring — what about other Python files, the workflow YAML, or `context.md` itself? Step 35 catches this at the end, but catching it in Phase 7 means you've been building on a broken foundation for 33 steps.

#### Recommended Changes

- [x] **Step 12 adds a CORE RULE #9 but the numbering collision isn't addressed.** The existing V15 CLAUDE.md likely already has rules numbered 1-8. Step 12 appends rule 9 after rule 8, but doesn't verify that rules 1-7 are untouched. If the existing file already has a rule 9 (perhaps from a different section), this creates ambiguity. The plan should explicitly state the current rule count and confirm no collision.

- [x] **Phase 4 (Steps 11-22) is a monolithic CLAUDE.md rewrite split across 12 micro-steps, but the final content is only shown for the orchestration workflow.** Steps 11-14 and 16-22 each modify small sections, but the plan shows the old → new diff for each. The risk is that when building, you're doing 12 separate edits to the same file with no intermediate verification that the whole file still parses correctly. Consider adding a mid-phase structural verification after Step 15 (the largest edit) — run the section heading check from Step 36 at that point too.

- [x] **The scheduled run step sequence in Step 18 (plan step) skips Steps 16-19 entirely.** The new sequence is `Steps 1, 3-5, 7, 9-15, 20, 21, 22`. This means scheduled runs skip presentation, user feedback, state save, and brief generation. That's correct for a scheduled run (no user present), but the plan doesn't explain this reasoning. A one-line comment would help the builder.

#### Nice-to-Have

- [ ] **The source researcher skill (Step 8) specifies 8-10 queries per industry across 5 categories, but the actual query templates only add up to ~7-11 per industry.** Category 1 has 0 queries (JobSpy), Category 2 has 2-3, Category 3 has 2-3, Category 4 has 1-2, Category 5 has 2-3. The overview says "8-10 queries/industry" — the math is close enough, but the overview should match the spec.

- [ ] **Step 31 uses `rm -f` with glob patterns but no verification that `.gitkeep` files survive.** The verify step checks that non-gitkeep files are gone, but `rm -f 03_agents/tests/v16/output/verified/*/*` could delete `.gitkeep` files if they're in subdirectories of `verified/`. The globs should exclude `.gitkeep` or the verify step should confirm `.gitkeep` files still exist.

#### Approval Status: **Needs Changes**

---

### Reviewer 2: Kieran (Execution & Completeness)

#### Required Changes

- [x] **`save-after-feedback` CLI subcommand is referenced in Steps 17-18 of the orchestration workflow but never implemented in Phase 5.** Phase 5 title says "Add CLI Subcommands" (plural) but only implements `record-action`. Either: (a) add Steps 25b-25c to implement and test `save-after-feedback`, or (b) remove all references to it from the orchestration workflow and clarify what happens after recording actions — does `record-action` auto-save? The current `record_action` function in the plan's Step 25 implementation does call `save_state()` at the end, so maybe `save-after-feedback` is redundant. If so, remove it explicitly.

- [x] **Step 15 (plan step) replaces the ENTIRE ORCHESTRATION WORKFLOW section, but the replacement content contains nested markdown code fences.** The content itself contains nested markdown code fences (for bash commands, JSON examples, and the session-state.md template). The builder needs to know: is the orchestration content meant to be pasted literally (including the code fences), or are the code fences part of the plan's formatting? This ambiguity could result in malformed CLAUDE.md.

- [x] **Step 14 creates a reference to "Step 7 in workflow" from the ON STARTUP section, but ON STARTUP has its own step numbering (1-8).** The ON STARTUP step 8 now says "proceed to source research gate (Step 7 in workflow)". This cross-reference is fragile. Use a section anchor instead: "proceed to source research gate (see ORCHESTRATION WORKFLOW, Step 7)".

#### Recommended Changes

- [x] **The test count claims don't account for the existing test suite.** Step 5 says "all 17 tests PASSED (14 existing + 3 new)", Step 26 says "all 18 tests PASSED (14 existing + 3 brief_requested + 1 CLI)". But the plan never verifies that V15 currently has exactly 14 tests. If V15 has a different count, these expected counts are wrong and the builder will be confused. Add a verify step in Phase 1 to count existing tests.

- [x] **Step 22 (plan step) is a no-op verification step that says "this is already addressed in the Step 15 rewrite above."** If it's already handled, don't include it as a separate step — it creates confusion about whether additional work is needed. Either merge it into Step 15's verify section or remove it and relabel as "Verify only — no implementation needed."

- [x] **The orchestration workflow Step 9 lists 14 template variables, but `sources_for_role` is new and the search-verify agent definition isn't updated.** The plan modifies CLAUDE.md to reference `sources_for_role` in the template variable blob, but doesn't update the search-verify agent definition or skill to consume this new variable. If the search-verify agent doesn't know about `sources_for_role`, it will be passed but ignored. Either add a step to update the search-verify agent/skill, or note that it already handles this variable.

#### Nice-to-Have

- [ ] **Commit messages could include the phase number for easier git log navigation.** e.g., "feat(jsa): [P2] add brief_requested action type".

- [ ] **Step 29 verifies `.gitignore` handles source research outputs but could be more precise.** Check for the specific pattern that would match `_source_research*.json` files.

#### Approval Status: **Needs Changes**

---

### Reviewer 3: Code Simplicity

#### Required Changes

- [x] **The `save-after-feedback` subcommand referenced in the orchestration workflow (Step 18) has no implementation anywhere in the plan.** This is not a style issue — it's a missing feature. The orchestration says to run `python3 scripts/manage_state.py save-after-feedback --state state.json` but Phase 5 never builds it. The `record-action` implementation in Step 25 already calls `save_state()` after each action, so every `record-action` call persists immediately. If that's the intent, `save-after-feedback` is redundant — remove the reference. If it's meant to do something different (batch save, finalize feedback round), define and implement it.

#### Recommended Changes

- [x] **The source researcher skill has a 3-minute budget for WebFetch verifications but no mechanism to track elapsed time.** The skill says "Maximum 3 minutes total for all WebFetch verifications. If approaching limit, skip remaining." But the subagent has no timer — it's a Claude agent making sequential tool calls. It cannot measure elapsed wall-clock time. Either remove the time budget (rely on the agent's natural pacing) or replace it with a count-based budget ("verify at most 15 sources; skip the rest").

- [x] **The orchestration workflow duplicates git pull logic.** Step 2 says "Git pull (interactive mode only)" and ON STARTUP step 3 also says "Git pull (interactive mode only — MANDATORY)." The CLAUDE.md will have git pull instructions in two places. When the builder writes this, they'll need to ensure both are consistent. Consider having the orchestration workflow Step 2 reference ON STARTUP step 3 to avoid duplication.

#### Nice-to-Have

- [ ] **Step 24 (API key piping) feels orphaned as the last orchestration step.** It's about scheduled run setup, which only happens after Step 23 (the prompt). It would be cleaner as part of the SCHEDULED RUNS section rather than an orchestration workflow step.

- [x] **The source researcher output schema table at the end of Step 8 (skill file) has an unclosed code fence.** Line 366 of the plan shows a closing ` ``` ` after the schema table but there's no opening fence for it — the table is in markdown pipe format, not a code block. This stray fence could cause rendering issues in the skill file.

#### Approval Status: **Needs Changes**

---

### Round 1 Summary

| Reviewer | Status |
|----------|--------|
| DHH | Needs Changes |
| Kieran | Needs Changes |
| Code Simplicity | Needs Changes |

**Consensus: NOT approved for build.**

All three reviewers independently flagged the same blocking issue: the `save-after-feedback` CLI subcommand is referenced in the orchestration workflow but never implemented in the plan. This must be resolved (implement it or remove the reference).

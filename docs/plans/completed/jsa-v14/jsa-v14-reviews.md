# JSA V14 Reviews

## Round 3

---

### DHH (Rails-style Simplicity Reviewer)

**Overall Assessment:** Round 2 cleaned up the remaining specification gaps — step ordering is correct, redundant count variables removed, CLI parsing specified, checkpoint moved to the right place. The plan is now tight and implementation-ready. One remaining inconsistency in the summary table and one minor specification clarity issue.

#### Required Changes

- [x] **R-DHH-1: Summary table says "All 8 commit messages" but then lists 10 commit messages (numbered 1-10).** The heading says "8" but the list contains 10 entries. This is a leftover from a previous iteration where the commit count was 8. Update the heading to say "All 10 commit messages" to match the actual list. Also update the summary table row for the total: it says "8 phases, 25 tasks, 10 commits" — the 10 commits is correct, but the heading above the list contradicts it.

#### Recommended Changes

- [x] **RC-DHH-1: Task 6.1 step 15 says "Collect user feedback, record_action in loop, save state" and step 16 says "Save state after user feedback (call save_state)".** Steps 15 and 16 both mention saving state. The prose after step 20 says "call `record_action(state, job_key, action)` in a loop for each user decision... then save state." This means step 15 collects feedback + calls record_action, and step 16 is the actual save_state call. But step 15's description includes "save state" which is misleading — it suggests state is saved within step 15 itself. Reword step 15 to: "Collect user feedback, record_action in loop" (remove "save state" from step 15's description since step 16 handles the save).

#### Nice-to-Have

- [x] **N-DHH-1: Task 6.1 "Keep unchanged" list includes "SESSION MANAGEMENT" but Task 6.1 also has a "SESSION MANAGEMENT" modification described earlier in the same task.** The "Modify sections" area says to rewrite SESSION MANAGEMENT (replacing V13's resume-via-session-state.md with state.json tracking). The "Keep unchanged" list then includes SESSION MANAGEMENT. This is contradictory. Remove SESSION MANAGEMENT from the "Keep unchanged" list since it IS being modified.

**Verdict:** APPROVED with minor changes (no blocking issues remain)

---

### Kieran (Rails Architecture Reviewer)

**Overall Assessment:** The plan is now architecturally sound. Data flow is clean (delta carries keys only, agents read verified JSONs for rendering), the orchestration workflow is fully enumerated at 20 steps with correct ordering, and the state management module is well-specified with 14 TDD tests. The onboarding agent boundaries are clear, and the skills-based architecture cleanly replaces reference templates. Ready for build.

#### Required Changes

None.

#### Recommended Changes

- [x] **RC-KR-1: Task 4.2 `update_state` post-processing step says "reset `reappeared = False` for all jobs in `state.jobs` that were seen in the current scan but were NOT newly resurrected this run."** The phrase "seen in the current scan" is slightly ambiguous — does it mean jobs whose verified JSON files were found in `verified_dir`, or jobs in `state.jobs` whose role type is in `searched_role_types`? These are different sets if a job was previously added from a role type that is not searched in the current run. Clarify: "seen in the current scan" means "a verified JSON file for this job key exists in `verified_dir` during this run." Jobs in `state.jobs` whose role type was not searched are untouched (including their `reappeared` flag).

#### Nice-to-Have

- [x] **N-KR-1: Task 8.3 manual smoke test checklist item 8 says "Scheduled run produces valid email with zero briefs, no PDF attachment line."** This is a good test but the plan does not specify HOW to trigger a scheduled run locally for smoke testing. The GitHub Actions workflow runs on `ubuntu-latest` with CI secrets. For local testing, the implementer would need to set `SCHEDULED_RUN=true` as an environment variable and invoke Claude directly. Consider adding a note: "Local scheduled mode test: `SCHEDULED_RUN=true claude --model claude-opus-4-6 --print 'Run scheduled daily digest.'`"

**Verdict:** APPROVED for build

---

### Code Simplicity Reviewer

**Overall Assessment:** The plan has converged to a clean, buildable state. The delta is minimal (key lists only), test coverage is comprehensive (14 tests covering all state transitions), conditional rendering rules are extracted into clear sections, and the session management transition from V13 checkpoint to V14 state.json is explicitly documented. One unchecked finding from Round 1 (N-CS-2, inline verification commands) was left intentionally — the per-task verification provides value for the implementer and the trade-off is acceptable. No new issues found.

#### Required Changes

None.

#### Recommended Changes

None.

#### Nice-to-Have

- [x] **N-CS-1: Task 1.2 verification command `grep -r "v13" ... | grep -v "output/"` will catch references in the CLAUDE.md file, but Task 1.2 explicitly says CLAUDE.md paths are deferred to Phase 6.** The verification step will report false positives from CLAUDE.md during Phase 1. Add `| grep -v "CLAUDE.md"` to the verification grep to avoid confusion during Phase 1 implementation. This filter can be removed in Phase 8's cross-file check (Task 8.1) where CLAUDE.md should be updated.

**Verdict:** APPROVED for build

---

### Approval Status

- **DHH:** APPROVED with minor changes (1 required, 1 recommended, 1 nice-to-have)
- **Kieran:** APPROVED for build (0 required, 1 recommended, 1 nice-to-have)
- **Code Simplicity:** APPROVED for build (0 required, 0 recommended, 1 nice-to-have)

**Overall: APPROVED for build — 1 required change (non-blocking), 2 recommended changes, 3 nice-to-have**

---

## Round 2

---

### DHH (Rails-style Simplicity Reviewer)

**Overall Assessment:** Round 1 addressed the major structural issues — delta output is now key-lists-only, step count is explicit at 20, factory duplication removed, and commit messages are enumerated. The plan is substantially cleaner. A few remaining issues around specification completeness and one inconsistency that slipped through Round 1 fixes.

#### Required Changes

- [x] **R-DHH-1: Task 1.6 search-verify agent definition says "13 template variables (upgraded to 14 in Phase 3)" but this creates ambiguity during implementation.** The agent body text says "Parse the compact JSON blob provided in the task prompt for your 13 template variables (upgraded to 14 in Phase 3)." When the implementer builds Phase 1, they write the agent with "13". Then in Phase 3 (Task 3.2), they change it to "14". But the Phase 1 agent definition already contains the parenthetical "(upgraded to 14 in Phase 3)" — this is a comment to the plan reader, not a runtime instruction. It will confuse the subagent if left in the deployed file. Remove the parenthetical from the agent definition body. Task 3.2 handles the update from 13 to 14 separately.

- [x] **R-DHH-2: Task 6.1 ORCHESTRATION WORKFLOW step 16 says "Checkpoint after every 3 role types" but this step is placed AFTER steps 14-15 (user feedback and record_action).** In V13, checkpointing happens after each search-verify batch (after every 3 role types searched), before presentation. In V14's step ordering, the checkpoint at step 16 comes after user feedback collection (step 15) but before brief dispatch (step 17). This means if the session crashes between search completion and user feedback, the checkpoint at step 16 was never reached. Move the checkpoint to after step 9 (after each search-verify batch completes and status is collected), consistent with V13's "checkpoint after every 3 role types" pattern. Step 16's current position should be removed or repurposed as "save state after user feedback."

#### Recommended Changes

- [x] **RC-DHH-1: Task 4.2 `update_state` says "For all jobs present in the current verified scan that already exist in `state.jobs`, reset `reappeared` to `False`."** This reappeared-reset logic is correct but is described in the middle of the `update_state` function spec, mixed in with expiry and resurrection logic. It would be clearer as a separate bullet point or a post-processing step: "After all updates: reset `reappeared = False` for all jobs in `state.jobs` that were seen in the current scan (not newly resurrected)." This makes the two-phase behavior explicit: (1) resurrect expired jobs with `reappeared = True`, (2) reset reappeared for all other returning jobs.

- [x] **RC-DHH-2: Task 5.1 says the digest-email agent receives `new_today_count` and `still_active_count` as separate variables, plus `new_today` and `still_active` arrays.** The counts are redundant — they are just `len(new_today)` and `len(still_active)`. Passing both the arrays and their lengths creates a consistency risk (what if the count doesn't match the array length?). Remove `new_today_count` and `still_active_count` from the variable list and have the agent compute counts from the arrays. This reduces the variable count from 9 to 7.

#### Nice-to-Have

- [x] **N-DHH-1: Task 7.1 GitHub Actions workflow installs `npm install -g @anthropic-ai/claude-code` but does not verify the installation succeeded.** Consider adding a verification step: `claude --version` after the install. If the install fails silently, the "Run scheduled digest" step will fail with a confusing error about `claude` not being found.

**Verdict:** Needs Changes

---

### Kieran (Rails Architecture Reviewer)

**Overall Assessment:** The plan is in good shape after Round 1. The orchestration workflow is now fully enumerated, data flow is clean (delta carries keys, agents read verified JSONs for rendering), and the onboarding agent has clear boundaries. Two structural issues remain around the orchestration step ordering and a specification gap in the CLI wrapper.

#### Required Changes

- [x] **R-KR-1: Task 4.2 CLI wrapper `sync` subcommand takes `--searched-role-types type1,type2,...` as a comma-separated string.** But the library function `update_state` takes `searched_role_types: list[str]`. The plan does not specify how the CLI parses the comma-separated string into a list. Add: "Parse `--searched-role-types` by splitting on comma: `args.searched_role_types.split(',')`. If the argument is empty string, pass an empty list."

- [x] **R-KR-2: Task 6.1 step 9 says "After each batch: read `_status.json`, collect role types with 'complete'/'partial' status into `searched_role_types` list. Pass to manage_state.py sync." But step 12 says "Update state via `manage_state.py sync` (passes `searched_role_types`)."** This creates confusion about WHEN state is updated — after each batch (step 9) or after all batches complete (step 12)? If state is updated after each batch, then `searched_role_types` is incrementally built. If updated once after all batches, then `searched_role_types` is the full list. Clarify: step 9 only COLLECTS role types into the list; step 12 is the single state update call after all search-verify batches are complete. Reword step 9 to make it clear it is collection, not invocation.

#### Recommended Changes

- [x] **RC-KR-1: Task 2.1 onboarding agent definition says "Parse the compact JSON blob provided in the task prompt for your 5 template variables (`cv_text`, `existing_context_path`, `run_date`, `target_industries`, `target_roles`)."** The variable `cv_text` is described as text content, but the agent definition does not specify how CV text is obtained. Does the parent read the CV file and pass the text inline? Or does it pass a file path (like `existing_context_path`)? For large CVs, passing the full text inline in a JSON blob is problematic — same issue that was fixed for `existing_context_path` in Round 1. Consider changing `cv_text` to `cv_path` and having the onboarding agent read the file itself.

- [x] **RC-KR-2: Task 6.1 ORCHESTRATION WORKFLOW step 3 says "Git pull (interactive mode only)" but step 1 says "Load state.json".** If `git pull` updates `state.json`, loading it before pulling gives stale data. Reorder: step 1 should be "Capture run date", step 2 "Git pull (interactive mode only)", step 3 "Load state.json". This ensures state.json is current before loading.

#### Nice-to-Have

- [x] **N-KR-1: Task 8.1 check #4 validates `state.json` with `assert 'schema_version' not in s and 'run_history' not in s`.** These negative assertions guard against design doc fields that were intentionally excluded. This is good defensive checking, but the assertion error messages are not descriptive. If the check fails, the developer gets `AssertionError` with no context. Consider using explicit if-checks with `raise ValueError` for clarity.

**Verdict:** Needs Changes

---

### Code Simplicity Reviewer

**Overall Assessment:** The plan is significantly improved from Round 1 — the delta is now minimal (key lists only), the test suite is well-specified at 14 tests, and conditional rendering rules are cleanly extracted. Two remaining concerns around step ordering consistency and a minor specification gap.

#### Required Changes

- [x] **R-CS-1: Task 6.1 step ordering has a logical dependency issue.** Step 1 loads state.json, step 3 does git pull. But git pull may update state.json. This means step 1 loads potentially stale state. The correct order is: (1) capture run date, (2) git pull (interactive only), (3) load state.json. This was noted by Kieran (RC-KR-2) but bears emphasizing as a Required change because loading stale state can cause data loss — if a scheduled run expired jobs and the interactive run loads pre-pull state, those expirations are lost when state is saved.

- [x] **R-CS-2: Task 5.4 jsa-briefs-pdf skill says "Python Playwright render script (same pattern as V13 but with new PDF options)" but does not specify the critical PDF options.** The plan mentions `width: "800px"` and `prefer_css_page_size: True` but does not show the Playwright `page.pdf()` call with these options. Since V13 used `format: "A4"`, the implementer needs to know exactly what replaces it. Specify: `page.pdf(path=output_path, width="800px", prefer_css_page_size=True)` — no `format` parameter, no `height` parameter (height determined by content).

#### Recommended Changes

- [x] **RC-CS-1: Task 4.1 `verified_dir` fixture description says "creates role-type subdirectories" but does not specify which subdirectories to create.** The test descriptions reference `community-manager` and `devrel`. Specify that the fixture creates `tmp_path / "community-manager"` and `tmp_path / "devrel"` as the default subdirectories, matching the role types used in tests 7, 8, and 9.

- [x] **RC-CS-2: Task 6.1 PRESENTATION WORKFLOW says "quick notes — a one-line company summary appended as a footnote below the URL list for every company."** But the specification says "Sourced from the `notes` field in verified JSON. Max 15 words per note." The V13 verified JSON `notes` field is a full paragraph (60+ words). The plan says to truncate to 15 words, but does not specify how. Clarify: "The orchestrator extracts the first sentence of the `notes` field and truncates to 15 words if needed."

#### Nice-to-Have

- [x] **N-CS-1: Task 6.1 SCHEDULED RUNS section describes a known limitation: "if a user runs interactively and a scheduled run fires before the interactive session ends, the scheduled run's state update will not include the interactive session's actions."** This is a correct analysis. Consider adding a mitigation note about the limited conflict window.

**Verdict:** Needs Changes

---

### Approval Status

- **DHH:** Needs Changes (2 required, 2 recommended, 1 nice-to-have)
- **Kieran:** Needs Changes (2 required, 2 recommended, 1 nice-to-have)
- **Code Simplicity:** Needs Changes (2 required, 2 recommended, 1 nice-to-have)

**Overall: NOT APPROVED — 6 required changes, 6 recommended changes, 3 nice-to-have**

---

## Round 1

---

### DHH (Rails-style Simplicity Reviewer)

**Overall Assessment:** This plan is well-structured with clear phases, solid TDD for state management, and good separation of concerns. The migration from reference templates to skills is a clean architectural improvement. However, there are areas where complexity has crept in unnecessarily, and a few implementation details need tightening.

#### Required Changes

- [x] **R-DHH-1: Remove `conftest.py` factory duplication.** `make_verified_job` and `make_verified_json` have overlapping fields. The plan describes `make_verified_job` as "returns dict matching the subset `manage_state.py` extracts into `JobEntry`" and `make_verified_json` as "represents what `search-verify` writes to disk (V13 shape)." Since `make_verified_json` copies a real V13 fixture and overrides fields, and `make_verified_job` is a subset of those same fields — `make_verified_job` is unnecessary. Tests should use `make_verified_json` to write fixtures to disk, then let `update_state` extract `JobEntry` fields naturally. Remove `make_verified_job` from Task 4.1.

- [x] **R-DHH-2: Task 6.1 specifies "~15 steps" but V13 has 15 explicit steps and V14 adds state management, delta computation, presentation formatting, and session-state writing.** Count the actual steps listed in the plan and use the real number instead of "~15". The tilde makes it sound like the author didn't finish the design. Enumerate all steps precisely.

- [x] **R-DHH-3: Task 4.2 `compute_delta` includes `requirements_met` in the delta output.** The plan says it's a `list[str]` carried through from verified JSON. But `JobEntry` stores `requirements_met` as `list[str]`, and the delta output includes it for every job in `new_jobs` and `still_active`. This is redundant data — the digest-email agent already reads verified JSON files directly for full rendering data (stated in Task 5.1: "Reads verified JSON files from `output/verified/` for full job rendering data"). Remove `requirements_met` from `compute_delta` output to keep the delta lean. The delta should only carry classification data (which jobs are new vs still-active), not rendering data.

- [x] **R-DHH-4: Task 7.1 GitHub Actions workflow has `working-directory` on some steps but not all.** The "Verify settings.local.json permissions" step has `working-directory: 03_agents/tests/v14` but the "Install dependencies" and "Install Claude Code" steps don't need it (they're global). However, the NOTE at the top says "copy this file to the repo root `.github/workflows/` and add `working-directory: 03_agents/tests/v14` to all `run:` steps." This contradicts the template — some steps already have it, some don't. Standardize: add `working-directory` to ALL `run:` steps in the template itself, so when copied to repo root it works without modification.

#### Recommended Changes

- [x] **RC-DHH-1: Task 4.2 `save_state` uses `tempfile.NamedTemporaryFile` + `os.rename` for atomic writes.** This is good practice, but the plan also specifies `json.dump(data, f, indent=2)` inside the tempfile context. Clarify that the tempfile should be opened with `suffix='.json'` to avoid confusion if the rename fails and leaves a temp file behind. Also specify `encoding='utf-8'` (already mentioned) and that `os.replace` should be used instead of `os.rename` for cross-platform atomicity (rename can fail on Windows if target exists).

- [x] **RC-DHH-2: Task 2.1 onboarding agent definition says "Parse the compact JSON blob provided in the task prompt for your 5 template variables" but then says "`existing_context` is the full text of `references/context.md` if it exists, or `null` on first run."** Passing full context.md text as a JSON string variable is problematic — context.md can be large with special characters that need escaping. Instead, pass `existing_context_path` (path to the file) and let the onboarding agent read it. This is how the other agents handle large data (e.g., `job_json_with_verification` in brief-generator is already the full JSON, but that's structured data, not free-form markdown).

- [x] **RC-DHH-3: Task 8.2 says "Expected: 6 passed (3 filter + 3 summarize)" for V13 tests, but the test file is named `test_summarize_jobs.py` in V13.** The plan references `test_summarize.py` (without `_jobs`). This will fail. Use the correct filename: `test_summarize_jobs.py`.

- [x] **RC-DHH-4: Task 1.5 says "create a corresponding skill file by copying content and prepending YAML frontmatter" for all 4 reference templates.** But the digest-email and briefs-pdf skills are completely rewritten in Phase 5 (Tasks 5.1, 5.4). Creating them in Phase 1 just to overwrite them in Phase 5 is wasted work. Instead, create only search-verify and brief-generator skills in Phase 1. For digest-email and briefs-pdf, create placeholder skills in Phase 1 (frontmatter only + "Placeholder — rewritten in Phase 5") and do the full content in Phase 5.

#### Nice-to-Have

- [x] **N-DHH-1: Task 4.1 specifies 12 tests, which is thorough.** Consider adding a 13th test: `test_compute_delta_excludes_rejected` — verify that `compute_delta`'s `still_active` list excludes jobs where `user_action == "rejected"`. This behavior is specified in Task 4.2 but has no dedicated test. The `test_user_action_preserved` test only checks that user_action survives update_state calls, not that rejected jobs are filtered from the delta.

- [x] **N-DHH-2: The plan summary table (bottom) says "25 tasks, 8 commits" but actual task count is: Phase 1 (7) + Phase 2 (1) + Phase 3 (3) + Phase 4 (3) + Phase 5 (5) + Phase 6 (2) + Phase 7 (1) + Phase 8 (3) = 25.** This checks out. But the commit count shows 3 commits for Phase 1 in the Phase column but only lists individual commits for the other phases. The summary should explicitly list all 8 commit messages to make the scope clear.

**Verdict:** Needs Changes

---

### Kieran (Rails Architecture Reviewer)

**Overall Assessment:** The plan demonstrates good architectural thinking — the skills migration eliminates the dual-instruction-delivery problem, TDD for state management is the right call, and the delta-based email rendering avoids state.json coupling in subagents. A few structural issues need resolution before this is build-ready.

#### Required Changes

- [x] **R-KR-1: Task 6.1 ORCHESTRATION WORKFLOW says "~15 steps" but the plan lists specific additions (state loading, industry_qualifiers, _summary.md, state update, delta computation, presentation formatting, checkpoint, brief dispatch, 9-variable digest, state recording, session-state.md).** Counting V13's 15 steps plus these additions, the actual step count is likely 19-20. The design doc says 19 steps. Either enumerate all steps explicitly in the plan or state the definitive count. "~15" is a planning smell.

- [x] **R-KR-2: Task 4.2 `update_state` signature takes `searched_role_types: list[str]` and the plan says "The caller (orchestrator) is responsible for filtering this list based on `_status.json`."** But the plan never specifies WHERE in the CLAUDE.md orchestration workflow the orchestrator reads `_status.json` and constructs this filtered list. Task 6.1 lists "state update" as an orchestration step but doesn't describe the `_status.json` filtering logic. Add explicit orchestration step: "After batch completes, read each `_status.json`. Collect role types with status 'complete' or 'partial' into `searched_role_types`. Pass to `manage_state.py sync`."

- [x] **R-KR-3: Task 5.1 says the digest-email agent receives `verified_dir` as a template variable but Task 5.2 only updates the variable count from 4 to 9.** The 9 variables listed in Task 5.1 are: `run_date`, `user_email`, `user_name`, `total_briefs`, `new_today_count`, `still_active_count`, `new_today`, `still_active`, `verified_dir`. But `new_today` and `still_active` are described as "list of job keys" — these are arrays, not simple strings. Clarify the JSON format: are these arrays of strings (job keys) or arrays of objects? The plan says "list of job keys classified as new" which implies string arrays. Make this explicit in the variable spec: `"new_today": ["community-manager/acme-corp-growth-lead", ...]`.

- [x] **R-KR-4: Task 4.1 test `test_key_derived_from_filename` says "given verified JSON at `verified_dir/community-manager/acme-corp-growth-lead.json`, the resulting key should be `community-manager/acme-corp-growth-lead`."** But Task 4.2 says `update_state` derives keys from `{role_type_slug}/{filename_without_json}`. This works when scanning the verified_dir, but there's no test for key collision — what happens if two different role types have a file with the same company-title slug? The key format `{role_type_slug}/{filename}` prevents this, but add a brief note confirming that key uniqueness is guaranteed by the directory structure (one file per company-title per role type).

#### Recommended Changes

- [x] **RC-KR-1: Task 6.1 SCHEDULED RUNS says "state committed to main (pushes directly to main)" and "Non-overlap constraint: Interactive runs do not commit state."** But what about the inverse: if a scheduled run commits state.json, and then the user runs interactively, the user's `state.json` on disk may be stale (behind the remote main). Add a note to ON STARTUP: "If running interactively, `git pull` to ensure `state.json` is current before loading."

- [x] **RC-KR-2: Task 4.2 specifies `record_action` validates action is "accepted" or "rejected" and raises ValueError if not.** But there's no mention of an "applied" or "briefed" action for jobs that the user accepted and had briefs generated for. Is "accepted" the terminal state, or could you track "accepted -> briefed -> applied"? If "accepted" is sufficient for V14, add a note: "V14 tracks two states only (accepted/rejected). Richer lifecycle tracking deferred."

- [x] **RC-KR-3: Task 1.2 says "Replace all `v13` -> `v14`" in 5 listed files.** But it doesn't list `CLAUDE.md` among the files — yet Task 6.1 says "All paths: v13 -> v14" for CLAUDE.md. This creates ambiguity: does Task 1.2 handle CLAUDE.md path updates, or does Task 6.1? Since CLAUDE.md is getting a major rewrite in Phase 6, it makes sense to defer path updates to Phase 6. But state this explicitly in Task 1.2: "CLAUDE.md paths updated in Phase 6 (Task 6.1), not here."

- [x] **RC-KR-4: Task 2.1 creates the onboarding agent with 5 variables but the skill content description is vague.** It says "Skill contains: CV parsing workflow, extraction steps..." but doesn't specify the skill's output format or how `_onboarding_draft.json` maps to `context.md`. The schema is shown in the agent definition, but the skill should define the mapping: which draft fields become which context.md sections. Add a note: "Skill must define the mapping from `_onboarding_draft.json` fields to `context.md` sections (e.g., `profile.skills` -> `## Skills`, `discovered_sources` -> `## Sources`)."

#### Nice-to-Have

- [x] **N-KR-1: The plan doesn't mention what happens to `context.md` location.** V13 has `context.md` in the root (`03_agents/tests/v13/context.md`). Task 1.7 says "Keep `references/context.md`" but V13's context.md is at root, not in `references/`. Task 2.1 says the onboarding agent writes to `references/context.md`. Clarify: is context.md moving from root to `references/`? If yes, update Task 1.2 to include this move. If no, fix Task 2.1's path.

- [x] **N-KR-2: Task 4.2 specifies `EXPIRY_DAYS = 14` as a module-level constant.** Consider also adding `VALID_ACTIONS = {"accepted", "rejected"}` as a module-level constant for `record_action` validation, rather than hardcoding the strings in the function body.

**Verdict:** Needs Changes

---

### Code Simplicity Reviewer

**Overall Assessment:** The plan is thorough and well-organized with clear phase boundaries, TDD approach for the core state module, and good traceability between design decisions and implementation tasks. The main concerns are around unnecessary complexity in a few areas and some specification gaps that could lead to implementation ambiguity.

#### Required Changes

- [x] **R-CS-1: Task 4.1 `test_expired_job_reappears` specifies "7 assertions total" and describes a two-call sequence.** This is testing two distinct behaviors in one test: (a) resurrection from expired, and (b) `reappeared` flag reset on subsequent run. Split into two tests: `test_expired_job_reappears` (resurrection, 5 assertions) and `test_reappeared_flag_resets_on_next_run` (flag reset, 2 assertions). This makes failures more diagnostic. Update the test count from 12 to 13.

- [x] **R-CS-2: Task 6.1 PRESENTATION WORKFLOW says "Add only these deltas: (1) 'New Today' and 'Still Active' subsections, (2) `dagger` marker for unverified listings with footnote, (3) quick notes requirement for every company."** But the existing V13 PRESENTATION WORKFLOW has no "quick notes" requirement. This is a new feature being slipped into a "modify existing" instruction. Define what "quick notes" means: is it a one-line company summary below each table row? A column in the table? A footnote? Specify the format explicitly.

- [x] **R-CS-3: Task 4.2 `compute_delta` output includes `source` and `active_status` fields for each job in `new_jobs` and `still_active`.** But Task 5.1 says the digest-email agent reads verified JSON files directly for full rendering data. If the delta is only used for classification (new vs still-active), why include `source`, `active_status`, `location`, `job_url`, `score`, `title`, `company`, and `requirements_met` in the delta output? The delta should be minimal: `{"new_jobs": ["key1", "key2"], "still_active": ["key3"]}`. The digest agent already reads verified JSONs for everything else. Simplify the delta to just job key lists + counts.

- [x] **R-CS-4: Task 1.6 shows the complete agent definition for all 4 agents.** The `digest-email.md` definition says "Parse the compact JSON blob provided in the task prompt for your 4 template variables (upgraded to 9 in Phase 5)."** This creates a broken intermediate state — if someone builds Phase 1 and tests digest-email before Phase 5, the agent expects 4 variables but the skill expects 9 (or vice versa). Either write the agent definition with 9 variables from the start (since Phase 5 is the first time digest-email is actually used), or add a note that digest-email is non-functional until Phase 5 is complete.

#### Recommended Changes

- [x] **RC-CS-1: Task 4.2 `update_state` has a complex signature with 4 parameters.** The `searched_role_types` parameter is described as "a list of role type slugs" but there's no validation — what happens if an empty list is passed? Document the behavior: "If `searched_role_types` is empty, no jobs are expired (no role types were searched, so no absence signal exists). State is still updated with any new jobs found in `verified_dir`." Or raise ValueError for empty list if that's a caller bug.

- [x] **RC-CS-2: Task 7.1 GitHub Actions "Commit state" step does `git add state.json output/session-state.md`.** But if the scheduled run fails partway through, `session-state.md` may not exist or may be incomplete. The `git diff --staged --quiet || git commit` pattern handles the "nothing to commit" case, but not the "partial state" case. Add a conditional: only commit if `state.json` was actually modified (the `git diff --staged --quiet` check covers this). But also consider: should a failed run commit state? If search-verify succeeded but email failed, the state has valid new jobs but the email wasn't sent. Clarify: "State is committed regardless of email delivery success. Email delivery is tracked separately in `_status.json`."

- [x] **RC-CS-3: Task 6.1 says the orchestrator writes `output/session-state.md` with a specific format.** But V13 already has `output/session-state.md` with a different purpose (resume state). The V14 plan repurposes it as a "human-readable run log." This is a breaking change from V13's session management. The V13 CLAUDE.md says "Write progress to session-state.md after completing each role type. On startup, if session-state.md exists, read it and resume where you left off." V14's version is a final summary, not a checkpoint. Clarify: does V14 still support mid-session resume via session-state.md, or is the checkpoint functionality replaced by state.json? If replaced, state that explicitly and update the SESSION MANAGEMENT section in Task 6.1.

- [x] **RC-CS-4: Task 5.1 says "When `total_briefs == 0`, omit 'Application briefs attached as PDF' footer line."** This is a conditional rendering detail buried in a dense paragraph. Extract this as a separate rendering rule in the skill spec, not inline prose. The skill should have a clear "Conditional Sections" area listing what varies by mode.

#### Nice-to-Have

- [x] **N-CS-1: Task 4.1 `conftest.py` says `make_verified_json` "Uses a real V13 verified JSON file as the template for default values."** This creates a test dependency on V13 output files. If V13 output is cleaned or the file structure changes, tests break. Consider extracting the fixture data into a `tests/fixtures/` directory as a static JSON file that won't be affected by cleanup operations.

- [ ] **N-CS-2: The plan has extensive inline verification commands (`grep`, `ls`, `wc -l`) after each task.** These are good for the implementer but add visual noise to the plan. Consider consolidating all verification into Phase 8 (which already has cross-file checks) and keeping per-task verification to just a "Verify: [what to check]" one-liner that references the Phase 8 check.

**Verdict:** Needs Changes

---

### Approval Status

- **DHH:** Needs Changes (4 required, 4 recommended, 2 nice-to-have)
- **Kieran:** Needs Changes (4 required, 4 recommended, 2 nice-to-have)
- **Code Simplicity:** Needs Changes (4 required, 4 recommended, 2 nice-to-have)

**Overall: NOT APPROVED — 12 required changes, 12 recommended changes, 6 nice-to-have**

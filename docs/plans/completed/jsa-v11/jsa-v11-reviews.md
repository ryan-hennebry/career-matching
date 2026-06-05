# JSA V11 Reviews

## Round 6 - 2026-02-05 (Ship-or-Simplify Review)
**Reviewers:** DHH Architecture Critic, Kieran Quality Reviewer (source-verified), Code Simplicity Reviewer

### Summary

All 3 reviewers agree: **the plan is correct and ready to ship.** Every HIGH item from rounds 1-5 is verified as incorporated. Script invocations match actual argument parsers. Template variable contracts are complete. No new runtime-error-level bugs found.

The central tension is philosophical, not technical: DHH argues the entire template-based subagent architecture is over-engineered (recommends ~150-line CLAUDE.md, no template files); Simplicity reviewer confirms template variables are all load-bearing (subagents can't read files, only their prompt); Kieran confirms zero discrepancies between plan and source code.

**1 new MEDIUM finding** (Kieran): `--remote` flag never passed to `jobspy_search.py` despite `{remote_pref}` existing as a template variable. 3 additional MEDIUM items (specialty source consistency risk, default result count, exclude-titles format difference between scripts).

**2 simplification recommendations** with consensus: (1) Replace formal session management (4-phase state machine, Resume Dispatch Table, schema) with 3-line instruction; (2) Remove cross-role-type deduplication protocol.

### Findings

#### DHH Architecture Critic

**Core thesis:** "You built a framework. You needed a better feature."

The plan produces 574 lines of deliverable content via 790 lines of plan, after 584 lines of reviews across 5 rounds. V10 was 89 lines and produced real output. The response to V10's behavioral failures was an architectural revolution (3-tier agent hierarchy, template variable substitution engine, formal completion signals, 4-phase state machine) when a behavioral fix (better MUST/NEVER rules + "use the Task tool when it runs long") would suffice.

**Specific criticisms:**

1. **Template variables are a "stringly-typed API debugged in prose."** 4 of 5 review rounds found bugs in the variable contract (R4-H1, R4-H2, R4-PH1, R4-PH2, R5-H3). The template system created more bugs than the behavioral problems it was supposed to fix.

2. **Session state management is a state machine for a system that has never run.** The 4-phase state machine, Resume Dispatch Table, and checkpoint protocol are predictions about failure modes, not responses to observed failures.

3. **`_status.json` is ceremony.** Task tool returns on completion. Parent can check if output files exist. No formal completion signal needed.

4. **The review process introduced more complexity than it removed.** Each round found template variable bugs that existed because of the template approach, validated the fixes, then found new bugs introduced by the fixes.

**Recommended alternative:** ~150-line CLAUDE.md with MUST/NEVER rules + onboarding + "use Task tool for each role type, pass the user profile and role type." No template files, no variable contracts, no `_status.json`, no formal session state schema. ~200 lines total vs 574.

**Assessment:** Philosophical challenge to the entire approach. The counter-argument (V10 failed precisely because the LLM was given flexibility) remains valid. Design judgment call, not a blocking issue.

#### Kieran Quality Reviewer (Source Code Verified)

**All prior HIGH items: VERIFIED as incorporated.**

| Item | Status | Evidence |
|------|--------|----------|
| R5-H3 (positional arg) | PASS | Line 459: `jobspy_search.py "{role_type}"` — no `--query` flag |
| R5-H1 (specialty split) | PASS | Line 461: explicit "processed in-context" note |
| R5-H2 (salary mapping) | PASS | Line 511: `min_amount`/`max_amount` → `salary_min`/`salary_max` |
| R4-H1/H2 (exclude_titles) | PASS | Line 205: 13th variable; line 462: space-separated format |
| R4-PH1/PH2 (brief slugs) | PASS | Lines 226-227: both `{company_slug}` and `{title_slug}` defined |
| R2-1/R2-2 (slugification) | PASS | Lines 427-431, 625-629: identical rules in both templates |
| C1-C15 (Round 1) | ALL PASS | Every change traceable in plan text |

**Script-to-plan alignment: CLEAN.**

| Script | Plan Invocation | Actual Parser | Match |
|--------|----------------|---------------|-------|
| `jobspy_search.py` | Positional query, `--location`, `--country`, `--output` | Positional `query`, optional `--location`, `--country`, `--output` | CLEAN |
| `filter_jobs.py` | Positional input, `--output`, `--exclude-titles` space-separated | Positional `input`, required `--output`, `nargs="*"` | CLEAN |
| `summarize_jobs.py` | Positional input, stdout note | Positional `input`, stdout only | CLEAN |

**New findings:**

1. **(MEDIUM — R6-M1) `--remote` flag never passed to `jobspy_search.py`.** Script accepts `--remote` as boolean flag (line 25). Plan defines `{remote_pref}` as template variable (line 202) and includes it in subagent User Profile (line 445), but the search command (line 459) never uses it. Remote-preference users get on-site jobs that waste context during filtering.

2. **(MEDIUM — R6-M2) Default `--results 25` never discussed.** Script defaults to 25 results per job board site (up to 75 total). Plan never acknowledges whether this is sufficient for Core Rule 3's thoroughness requirement.

3. **(MEDIUM — R6-M3) Specialty source title exclusion is "manual" LLM work.** Plan tells subagent to "apply title exclusion logic manually." Risk of inconsistency vs `filter_jobs.py`'s case-insensitive substring matching.

4. **(MEDIUM — R6-M4) `--exclude-titles` format difference between scripts undocumented.** `jobspy_search.py` accepts comma-separated; `filter_jobs.py` accepts space-separated. Plan correctly only uses `filter_jobs.py` for filtering (no bug), but difference is undocumented.

#### Code Simplicity Reviewer

**R5 bloat removal status:** 3 of 4 items removed. One 2-line note survives at line 75 (trivial).

**Template variables: All load-bearing.** "Subagents dispatched via the Task tool cannot read arbitrary files — they only receive their prompt. Every variable exists because the subagent has no other way to access this data." This is the key rebuttal to DHH's "let the LLM construct prompts naturally" argument.

**Two recommended simplifications (consensus with DHH):**

1. **Replace session management section with 3 lines (~30 deliverable lines saved).** Current: 4-phase state machine, Resume Dispatch Table, session-state.md schema, checkpoint rules, progressive offloading. Replace with: "Write progress to session-state.md after completing each role type. On startup, if session-state.md exists, read it and resume where you left off. Tell user: 'Progress saved. Say continue to resume.'"

2. **Remove cross-role-type deduplication (step 8) (~4 deliverable lines saved).** Duplicates across role types are rare. Cost of a duplicate is presenting the same job twice — minor UX annoyance, not system failure. Saves runtime context.

**What is NOT bloat (confirmed):**
- Template variables (all load-bearing — subagents can't read files)
- MUST/NEVER rules (the entire point of V11)
- Verified JSON schema (integration contract)
- Brief template structure (core user deliverable)
- Slugification in both templates (standalone files must be self-contained)

**Final assessment:** "Stop reviewing. Ship V11. The ROI has inverted. The plan is ready."

### Required Changes

**MEDIUM (address during implementation):**
- [ ] **R6-M1: Pass `--remote` flag conditionally** — If `{remote_pref}` indicates remote-only, add `--remote` to search command
- [ ] **R6-M2: Acknowledge `--results` default** — Add note that default is 25 per site (~75 total), sufficient for V11
- [ ] **R6-M3: Note specialty source exclusion consistency risk** — Already documented in plan (R5-H1 fix); no action needed beyond awareness
- [ ] **R6-M4: Note `--exclude-titles` format difference** — Documentation only, no runtime risk

**SIMPLIFICATION (recommended — consensus across reviewers):**
- [ ] **Simplify session management** — Replace 4-phase state machine + Resume Dispatch Table + schema with 3-line instruction. Defer formal session management to V12 based on observed behavior.
- [ ] **Remove cross-role-type deduplication** (step 8) — Accept duplicates in V11. Fix in V12 if observed as a real problem.

**ARCHITECTURAL (design judgment — not blocking):**
- [ ] **DHH challenge: Template files vs natural language dispatch.** Template variables are confirmed load-bearing (subagents can't read files). The counter-argument holds. Revisit after V11 runs — if subagent adherence is high, templates proved their value; if variable bugs recur at runtime, simplify toward natural language in V12.

### Approval Status

**Approved.** All prior HIGH items verified as incorporated. Script invocations match actual source code. No new runtime-error-level issues. The 4 MEDIUM items are addressable during implementation. The 2 simplification recommendations (session management, cross-role-type dedup) are the only remaining changes worth making — both reduce complexity without losing functionality.

The unanimous reviewer recommendation: **ship V11 now and iterate from reality.**

---

## Round 5 - 2026-02-05 (Three-Perspective Review)
**Reviewers:** DHH Architecture Critic, Kieran Quality Reviewer (with source code verification), Code Simplicity Reviewer

### Summary

3 new HIGH issues found by Kieran reviewer (all verified against actual V10 source code). 1 fundamental architecture challenge from DHH reviewer. Simplicity reviewer confirms the plan is lean after 4 prior rounds of cuts (~16 lines of remaining bloat). R5-H3 is the most critical: `jobspy_search.py` uses a positional argument for query, not `--query` flag — guaranteed runtime error missed in all 4 prior rounds. All prior HIGH/MEDIUM items (C1-C15, R2-1 through R2-12, R3-1 through R3-3, R4-H1/H2, R4-PH1/PH2, R4-M1 through M6) confirmed addressed.

### Findings

#### DHH Architecture Critic

**Fundamental challenge:** The plan builds a framework where it needs a feature. 574 lines of instruction markdown across 4 files, with 20 template variables and a formal completion signal protocol, to tell an LLM to search for jobs and write briefs. The 3-tier agent model (parent + search subagents + brief subagents) responds to V10's behavioral failure (not following instructions) with an architectural revolution (template variable substitution engine).

**Key arguments:**

1. **(Architectural) Template variable substitution is over-engineered.** 13 variables for search, 7 for briefs. Four review rounds were needed partly to debug this templating system (R4-H1/H2, R4-PH1/PH2 were all template variable bugs). The parent agent is an LLM — it can read context.md and construct a natural language prompt for the Task tool without a formal variable contract.

2. **(Architectural) Slugification repeated 3 times is a DRY violation.** Appears in CLAUDE.md orchestration, subagent-search-verify.md, and subagent-brief.md. Each repetition creates divergence risk. Could define once in `references/algorithms.md` and reference everywhere.

3. **(YAGNI) Session-state schema + Resume Dispatch Table are premature.** Formal state machine with 4 phases and recovery paths for a system that has never run. "Write your progress and read it on resume" is sufficient for V11.

4. **(YAGNI) `_status.json` completion signals are unnecessary.** The Task tool returns when the subagent completes. Parent can check if output files exist. No formal completion signal file needed.

5. **(YAGNI) Cross-role-type deduplication protocol is over-engineered.** Plan acknowledges it could consume 70-140K tokens (R4-M5). Accept a few duplicates or do filename scan. Don't build a dedup protocol.

6. **(Process) Reviews have become self-referential.** 1,257 lines of planning/review for 574 lines of output. "Ship something, learn from it, and iterate."

**Recommended alternative:** ~150-line CLAUDE.md (keep MUST/NEVER rules + onboarding + "use Task tool for each role type"), no subagent template files, no session-state schema, no `_status.json`. Let the LLM construct prompts naturally. ~200 lines total vs 574.

**Assessment:** This is a philosophical challenge to the entire approach, not a bug report. The template-based architecture adds rigidity where the LLM's strength is flexibility. However, the counter-argument is that V10's failures were precisely because the LLM was given flexibility and used it to skip steps, cherry-pick results, and exhaust context. The templates exist to constrain behavior at known failure points. Whether that constraint should be formal (templates with variables) or behavioral (better MUST/NEVER rules) is a design judgment call.

#### Kieran Quality Reviewer (Source Code Verified)

**Prior items: All confirmed addressed.** Every R4 HIGH and MEDIUM item traceable in current plan text (verified line-by-line).

**New findings (HIGH — fix before implementation):**

1. **(HIGH — R5-H3) `--query` flag does not exist on `jobspy_search.py` — guaranteed runtime error.** Plan line 459 specifies `python3 scripts/jobspy_search.py --query "{role_type}"` but `jobspy_search.py` uses a positional argument (`parser.add_argument("query", ...)`). Verified against actual source code at `03_agents/tests/v10/scripts/jobspy_search.py` line 23. The script's own usage line confirms: `python3 jobspy_search.py "software engineer" --location "London"`. **Fix:** Change to `python3 scripts/jobspy_search.py "{role_type}" --location "{location_prefs}" --country "{country}" --output output/jobs/{role_type_slug}-aggregator.json`.

2. **(HIGH — R5-H1) Specialty source jobs bypass the filter/summarize pipeline.** Search workflow: step 1 runs `jobspy_search.py` → aggregator JSON. Step 3 WebFetches specialty sources (results stay in subagent context, never written to file). Step 4 runs `filter_jobs.py` on aggregator only. Specialty jobs are never filtered or summarized via scripts. The subagent must process them ad-hoc in context. Plan never acknowledges this split path. **Fix:** Add note between steps 3 and 4: "Specialty source jobs from step 3 are processed in-context (not via scripts). Apply title exclusion logic manually. Proceed directly to verification for promising candidates."

3. **(HIGH — R5-H2) Salary field name mismatch between JobSpy output and verified JSON schema.** JobSpy (via pandas) outputs `min_amount`/`max_amount`. Verified JSON schema specifies `salary_min`/`salary_max`. `summarize_jobs.py` already handles both names (lines 47-48). But the subagent could copy wrong field names. **Fix:** Add mapping note to Verification Workflow Step 5: "Aggregator data uses `min_amount`/`max_amount` — map to `salary_min`/`salary_max` in verified JSON."

**New findings (MEDIUM):**

4. **(MEDIUM — R5-M1) `"id": "unique-id"` generation unspecified.** Flagged as edge case E3 in R4, never addressed. Filename already serves as unique identifier. **Fix:** Define as `{company_slug}-{title_slug}` matching filename stem.

5. **(MEDIUM — R5-M3) Special characters in role types need shell escaping.** "Founder's Associate" contains an apostrophe that breaks shell parsing. **Fix:** Add escaping guidance to search workflow.

6. **(MEDIUM — R5-M4) Checkpoint trigger "every 2 role types" doesn't specify which phase milestone.** Does it mean 2 verified? 2 presented? 2 with briefs? **Fix:** Clarify: "after 2 role types reach 'verified' status during searching phase."

7. **(MEDIUM — R5-M5) `create_briefs_pdf.py` has hardcoded V10 filenames, username, and date.** Copied as dead code. Either exclude from copy or note as vestigial.

**New findings (LOW):**

8. **(LOW — R5-L1) API key sanitization instruction has no exact string to replace.**
9. **(LOW — R5-L2) No company slug truncation rule (title truncates at 50 chars).**
10. **(LOW — R5-L3) `zero_result_retry` field in `_status.json` is dead data (never read by parent).**
11. **(LOW — R5-L4) Task 7 file count estimate "~17" is wrong — actual count is ~22.**

#### Code Simplicity Reviewer

**Key finding: 68.6% of the plan (542 lines) is verbatim deliverable content.** Only 248 lines are plan scaffolding. The plan looks large at 790 lines, but most of it IS the product.

**What 4 prior rounds already cut:** ~400+ lines (Employed Mode, Jaccard dedup, pre-created session-state.md, ASCII tree, duplicated scoring rubrics, Template Variable Sources table, per-task verify checklists, grep checks, V10 cross-reference). The fat is gone.

**What still remains (~16 lines of genuine bloat):**

1. **(6 lines) Anti-Gaming Rules section** — Restates Core Rule 2 and scoring rubric. Every bullet is stated elsewhere. S6 from R4 was never applied.
2. **(2 lines) Review artifact tags** on lines 5 and 75 — "(C6: slugified paths, C12: no pre-created session-state.md)" provenance tags. Implementer doesn't need review round IDs.
3. **(2 lines) Task 1 explanatory note** — Explains what is NOT being done. Absence speaks for itself.
4. **(8 lines) Task 7 Steps 2-3** — File count verification (~17 estimate is wrong anyway) and "commit if fixes needed" are unnecessary. pytest (Step 1) is the real verification.

**What is NOT bloat (intentional):**
- Slugification in both templates (standalone files must be self-contained)
- "NEVER fabricate" in both templates (separate enforcement domains)
- Scoring table in subagent template (10 lines of cheap insurance at known failure point)
- Verified JSON schema (48 lines, integration contract between subagents and parent)
- Brief template structure (64 lines, core user deliverable)

**Task count: 7 is correct.** No merges recommended.

**Assessment:** Plan LOC reduction ~16 lines (2%). Architecture and scaffolding are lean. Ready to implement after addressing HIGH items.

### Required Changes

**HIGH (fix before implementation):**
- [ ] **R5-H3: Fix `jobspy_search.py` invocation** — Remove `--query` flag, use positional argument: `python3 scripts/jobspy_search.py "{role_type}" --location ...` (guaranteed runtime error without fix)
- [ ] **R5-H1: Document specialty source split pipeline** — Add note that WebFetch results are processed in-context, not via filter/summarize scripts
- [ ] **R5-H2: Document salary field name mapping** — Add `min_amount`/`max_amount` → `salary_min`/`salary_max` note to Verification Step 5

**MEDIUM (address during implementation):**
- [ ] **R5-M1: Define `id` field** — Use `{company_slug}-{title_slug}` matching filename stem
- [ ] **R5-M3: Add shell escaping guidance** for role types with special characters
- [ ] **R5-M4: Clarify checkpoint phase milestone** — "after 2 role types reach verified status"
- [ ] **R5-M5: Handle `create_briefs_pdf.py`** — Exclude from copy or note as vestigial

**Simplification (recommended, ~16 lines):**
- [ ] **S6 (carried from R4): Remove Anti-Gaming Rules section** — Restates existing rules
- [ ] Clean review artifact tags from lines 5 and 75
- [ ] Remove Task 1 explanatory note (line 75)
- [ ] Remove Task 7 Steps 2-3 (keep only pytest)

**Architectural (design judgment — not blocking):**
- [ ] **DHH challenge: Consider whether template files are necessary.** The counter-argument (V10 failed precisely due to unconstrained LLM behavior) is valid, but the template variable substitution contract has been the source of most review-round bugs. Revisit after V11 runs: if subagent adherence is high, templates proved their value; if not, simplify toward natural language dispatch in V12.

**LOW (optional):**
- [ ] R5-L1: Provide exact API key string to replace
- [ ] R5-L4: Correct file count from ~17 to ~22

### Approval Status

**Approved with changes.** R5-H3 is the most critical finding — a guaranteed `argparse` runtime error that would break every search, missed in 4 prior rounds. R5-H1 and R5-H2 are documentation clarity issues that the LLM subagent may handle implicitly but should be explicit. The DHH architectural challenge is noted as a valid design tension to revisit after V11 runs, not a blocking issue — the templates exist to constrain behavior at V10's known failure points. After fixing the 3 HIGH items, this plan is ready for implementation.

---

## Round 4 - 2026-02-05 (Post-Review Plan Validation)
**Reviewers:** Architecture Strategist, Code Simplicity Reviewer, Pattern Recognition Specialist

### Summary

3 HIGH issues found — all would cause runtime failures. The brief template variable contract is broken (`{title_slug}` isn't in the parent's brief variable list, and `{company}` gets substituted as raw text with spaces into filenames), title exclusion keywords have no mechanism to reach subagents (`{exclude_titles}` variable missing), and `filter_jobs.py` CLI format is unspecified (space-separated `nargs="*"` vs comma-separated in `jobspy_search.py`). 6 MEDIUM items cover consistency gaps and defensive hardening. Recommended simplifications: remove the 40-line Review Changes Mapping table (served the review cycle, not implementation) and duplicated Accuracy Rules sections.

All prior items (C1-C15, R2-1 through R2-12, R3-1 through R3-3, N1-N7, S1-S4) confirmed as addressed. The overall 3-tier architecture, file-based coordination model, template variable substitution approach, session management, and V10 failure coverage are all sound.

### Findings

#### Architecture Strategist

**Prior items: All confirmed addressed.** All 15 Round 1 changes (C1-C15), 12 Round 2 changes (R2-1 through R2-12), and 5 Round 3 changes (R3-1 through R3-3, N2, N3, N5, N7) are traceable in the current plan text.

**New concerns (HIGH):**

1. **(HIGH — R4-H1) `filter_jobs.py` CLI interface mismatch in subagent template.** The subagent search workflow step 4 specifies `--exclude-titles [exclusions from context.md]` but the actual `filter_jobs.py` uses `nargs="*"` expecting space-separated words, not a bracketed list. Meanwhile `jobspy_search.py` has its own `--exclude-titles` that accepts comma-separated. Plan doesn't clarify which format. **Fix:** Specify exact format: `--exclude-titles senior lead head director vp principal chief staff manager` (space-separated). Better: add `{exclude_titles}` template variable.

2. **(HIGH — R4-H2) No mechanism for parent to pass title exclusion keywords to subagents.** Orchestration step 4 lists 12 template variables — none include exclusions. context.md stores them but subagent can't read context.md (dispatched via Task tool with only filled template). **Fix:** Add 13th variable `{exclude_titles}` sourced from `context.md ## Constraints`, formatted as space-separated keywords.

**New concerns (MEDIUM):**

3. **(MEDIUM — R4-M1) `summarize_jobs.py` has no `--output` flag.** Only prints to stdout. Plan should clarify subagent reads stdout output in context, not a file.

4. **(MEDIUM — R4-M2) `jobspy_search.py` has redundant `--exclude-titles` that conflicts with pipeline.** Two filtering passes with different formats. **Fix:** Omit `--exclude-titles` from `jobspy_search.py` call; filter exclusively via `filter_jobs.py`.

5. **(MEDIUM — R4-M3) Subagent working directory assumption is fragile.** The passive "Working directory" note doesn't ensure the subagent executes from `03_agents/tests/v11/`. **Fix:** Add explicit `cd 03_agents/tests/v11/` as first subagent action.

6. **(MEDIUM — R4-M4) No scoring weight template variable.** Weights are hardcoded in subagent but "default" language implies customizability. Custom weights from onboarding never reach subagents. **Fix:** Remove "adjust" language and hardcode as canonical, or add template variable.

7. **(MEDIUM — R4-M5) Cross-role-type dedup consumes parent context.** Step 8 requires reading all verified files (70+ JSON files, 70-140K tokens) — partially defeating subagent context savings. **Fix:** Implement dedup via filename comparison rather than full JSON parsing, or add a dedup script.

8. **(MEDIUM — R4-M6) `{job_id}` in session-state schema has no source.** After R3-3 removed it from brief variables, nothing populates this field. **Fix:** Replace with `{company_slug}-{title_slug}` for consistency with file naming.

**Low concerns:**

9. **(LOW — R4-L1) `settings.local.json` contains hardcoded API key.** Task 1 copies it to V11. **Fix:** Sanitize during copy.
10. **(LOW — R4-L2) `create_briefs_pdf.py` carried forward without defined V11 use case.**
11. **(LOW — R4-L3) GBP currency hardcoded in `summarize_jobs.py`.** Known limitation for non-UK users.
12. **(LOW — R4-L4) Task 6 README update missing `jsa-v11-plan-post-review.md`.**

**Subagent coordination: Sound.** File-based model is correct. SOLID principles largely satisfied. Dependency Inversion is partial (implicit file contracts) but acceptable.

**V10 failure coverage: All 12 traceable.** Weakest fix is Failure 12 (date handling) — relies on subagent instruction compliance with no enforcement.

#### Code Simplicity Reviewer

**Plan reduction opportunities (~80 lines combined):**

1. **(HIGH — S5) Review Changes Mapping table (~40 lines).** The 33-row mapping table (C1-C15, R2-1 through R2-12, etc.) served the review cycle. Now that every change is baked into verbatim file contents, this is dead weight. **Remove entire section.**

2. **(MEDIUM — S6) Accuracy Rules in subagent-search-verify.md (~7 lines).** Restates Core Rule 2 verbatim. Same content, two sections, same file. **Remove.**

3. **(MEDIUM — S7) Accuracy Rules in subagent-brief.md (~6 lines).** Same pattern — repeats Core Rules 1-3. **Remove.**

4. **(MEDIUM — S8) Worked Example in subagent-search-verify.md (~10 lines).** Demonstrates scoring math, but V10 showed no scoring calculation errors. Belt-and-suspenders for a non-demonstrated problem. **Remove if no evidence of math mistakes.**

5. **(MEDIUM — S9) context.md HTML comments over-specify (~8 lines).** Instructions-for-agent embedded in a data file. Agent reads CLAUDE.md for instructions. **Reduce to single-line comments or remove.**

6. **(MEDIUM — S10) Task 1 Step 5 "Verify directory structure" (~6 lines).** Same verification theater pattern as previously removed S1 checklists. **Remove.**

**YAGNI:**

7. **(YAGNI — Y1) Glassdoor as mandatory research step in brief template.** Round 1 flagged this; survived 3 rounds. Adds guaranteed-to-fail WebFetch call to every brief. **Merge into general research query; reduce to 3 steps.**

**What is NOT bloat:** Anti-Gaming Rules (address real V10 failure), session-state schema (resume contract), slugification in both templates (independent files), CLAUDE.md at ~222 lines (well-trimmed), 7 tasks (correct granularity).

**Assessment:** Plan LOC reduction ~46 lines (861→~815). Generated file LOC reduction ~34 lines. Combined ~80 lines (~7%). Architecture and task structure are sound.

#### Pattern Recognition Specialist

**New findings (HIGH):**

1. **(HIGH — R4-PH1) Brief template output path uses raw `{company}` after parent substitution.** Parent substitutes `{company}` with raw value (e.g., "Acme Corp"). After substitution, path becomes `output/briefs/Acme Corp-senior-product-manager-brief.md` — a space in the filename. Parent verification (step 11) expects slugified path. They will never match. **Fix:** Add `{company_slug}` as parent-prepared variable in step 11.

2. **(HIGH — R4-PH2) `{title_slug}` in brief template output path not in parent variable list.** Parent's brief variables (step 11) define 5 variables; `{title_slug}` is not among them. Parent substitution either leaves literal `{title_slug}` in path or errors. **Fix:** Add `{title_slug}` and `{company_slug}` as parent-prepared variables.

**New findings (MEDIUM):**

3. **(MEDIUM — R4-PM1) No mapping between `_status.json` values and Search Progress vocabulary.** Search Progress uses `not started | searching | verified | presented`; `_status.json` uses `complete | partial | failed`. No defined translation. Resume Dispatch Table depends on Search Progress. **Fix:** Add explicit mapping in step 7.

4. **(MEDIUM — R4-PM2) `{job_id}` remains in session-state schema despite R3-3 removal.** Parent has no value to write here. **Fix:** Replace with filename-based identifier.

5. **(MEDIUM — R4-PM3) Subagent filter command references `context.md` for exclusions but has no data.** `[exclusions from context.md]` is prose, not a variable. No `{title_exclusions}` in variable list. **Fix:** Add `{title_exclusions}` variable.

6. **(MEDIUM — R4-PM4) `{country}` unquoted in search command.** Multi-word countries ("United Kingdom") break shell parsing. **Fix:** Quote it: `--country "{country}"`.

**New findings (LOW):**

7. **(LOW — R4-PL1) OUTPUTS paths use ambiguous `{company}` (raw vs slug).**
8. **(LOW — R4-PL2) Brief Company Research claims 4 steps but step 4 is duplicated instruction.**
9. **(LOW — R4-PL3) OUTPUTS raw jobs path pattern doesn't match actual subagent output.** Pattern says `{source}-{role_type_slug}.json` but subagent writes `{role_type_slug}-aggregator.json`.

**Edge cases (informational):**
- E1: No truncation rule for company slugs (title truncates at 50 chars).
- E2: Slug collisions possible — titles differing only in special characters slugify identically.
- E3: `"id": "unique-id"` generation is unspecified in verified JSON.

### Required Changes

**High (fix before implementation):**
- [ ] **R4-H1 + R4-H2: Add `{exclude_titles}` template variable** — 13th variable in Orchestration step 4, sourced from `context.md ## Constraints`, formatted as space-separated keywords. Update subagent filter command to `--exclude-titles {exclude_titles}`
- [ ] **R4-H1: Fix `filter_jobs.py` argument format** — Specify space-separated keywords, not bracketed placeholder
- [ ] **R4-PH1 + R4-PH2: Fix brief template variable contract** — Add `{company_slug}` and `{title_slug}` as parent-prepared variables in step 11. Use `{company_slug}` in brief template output path

**Medium (address during implementation):**
- [ ] **R4-M1: Clarify `summarize_jobs.py` stdout-only output**
- [ ] **R4-M2: Choose single filtering point** — Omit `--exclude-titles` from `jobspy_search.py` call
- [ ] **R4-M3: Add explicit `cd` as first subagent action**
- [ ] **R4-M4: Clarify scoring weights as fixed** — Remove "adjust" language
- [ ] **R4-M5: Implement lightweight cross-role-type dedup** — Filename comparison or dedup script
- [ ] **R4-M6 + R4-PM2: Replace `{job_id}` in session-state schema** — Use `{company_slug}-{title_slug}`
- [ ] **R4-PM1: Add `_status.json` to Search Progress mapping**
- [ ] **R4-PM4: Quote `{country}` in search command**

**Simplification (recommended):**
- [ ] **S5: Remove Review Changes Mapping table** (~40 lines, no risk)
- [ ] **S6 + S7: Remove duplicated Accuracy Rules sections** (~13 lines)
- [ ] **S8: Remove Worked Example** if no evidence of scoring math errors (~10 lines)
- [ ] **S9: Simplify context.md HTML comments** (~8 lines)
- [ ] **S10: Remove Task 1 Step 5 verification** (~6 lines)
- [ ] **Y1: Merge Glassdoor into general research step**

**Low (optional):**
- [ ] **R4-L1: Sanitize API key from `settings.local.json`**
- [ ] **R4-L2: Decide on `create_briefs_pdf.py`**
- [ ] **R4-PL1: Use `{company_slug}` in OUTPUTS paths**
- [ ] **R4-PL2: Fix brief research step count (4→3)**
- [ ] **R4-PL3: Align OUTPUTS raw jobs path pattern**
- [ ] **R4-L4: Add `jsa-v11-plan-post-review.md` to README update**

### Approval Status

**Approved with changes.** R4-H1/H2 and R4-PH1/PH2 must be addressed before implementation — the title exclusion pipeline and brief template variable contract are broken without them. M1 through M6 and PM1-PM4 should be addressed during implementation; none require architectural changes. S5 (mapping table removal) is a clear win with no risk. The overall architecture, coordination model, session management, and V10 failure coverage remain sound.

---

## Round 3 - 2026-02-05 (Final Validation)
**Reviewers:** Architecture Strategist, Code Simplicity Reviewer, Pattern Recognition Specialist

### Summary

All Round 2 HIGH items (R2-1, R2-2) and all MEDIUM items (R2-3 through R2-9) are confirmed resolved. The plan's architecture, session management, and error handling are sound. Round 3 found 3 medium-severity issues (presentation timing contradiction, parent slugification gap, and algorithms.md dedup conflict), plus plan-level simplification opportunities (~150 lines of redundant verification content). No architectural changes needed — the plan is ready for implementation after addressing the 3 medium items during implementation.

All 12 V10 failures remain adequately addressed. Template variables are complete (12/12 for search, 5/6 for brief — 1 orphan). Filename conventions, slug syntax, and status vocabulary are fully consistent across all files.

### Findings

#### Architecture Strategist

**Round 2 fixes: All 12 verified as properly integrated.**

- R2-1/R2-2 (slugification): Both subagent templates have "Filename Slugification" sections with explicit derivation rules
- R2-3 (slug syntax): `{role_type_slug}` used consistently everywhere, zero instances of hyphenated form
- R2-4 (Core Rule 3): Reworded to "before presenting any results"
- R2-5 (status vocabulary): Explicitly defined in context.md and session-state schema
- R2-6/R2-7 (_status.json handling): Orchestration step 7 covers missing/partial/failed
- R2-8 (country follow-up): Onboarding step 7 includes conditional question
- R2-9 (brief completion check): Orchestration step 11 verifies file existence
- R2-10/R2-11/R2-12 (simplifications): All applied

**New concerns (3):**

1. **(Medium — N2) Subagent search commands missing file output arguments.** The search command `python3 scripts/jobspy_search.py --query "{role_type}" --location "{location_prefs}" --country {country}` omits the `--output` flag. Without it, results print to stdout. Subsequent filter and summarize steps also need explicit input file paths. **Fix:** Add `--output output/jobs/{source}-{role_type_slug}.json` to the search command, and specify input files for filter/summarize steps.

2. **(Medium — N3) algorithms.md dedup conflict.** Task 1 copies production `algorithms.md` unchanged, which contains Jaccard similarity dedup (80% threshold). The subagent template correctly uses exact-match dedup per C12. When subagents reference `algorithms.md` for scoring (per C13), they encounter conflicting dedup rules. **Fix:** Add override note to subagent template: "For deduplication, use the rules in this template, NOT algorithms.md."

3. **(Medium — N7) No specification of subagent working directory.** Subagent templates use relative paths (`python3 scripts/jobspy_search.py`). When dispatched via the Task tool, the subagent may not inherit the parent's working directory. **Fix:** Add note specifying all paths are relative to `03_agents/tests/v11/`.

**Low concerns (2):**

4. **(Low — N1) Orchestration step 9 says "present as they become available" but Core Rule 3 says "ALL before presenting."** The R2-4 fix changed "ranking" to "presenting" but didn't resolve the semantic conflict with step 9. **Fix:** Reword step 9 to: "After all batches complete and cross-role-type dedup runs (step 8), present results per role type."

5. **(Low — N5) Missing `.env.example` and `.gitignore` from V10 copy.** Task 1 doesn't copy these files. **Fix:** Add copy steps in Task 1.

**Subagent coordination: Sound.** File-based model is correct. `_status.json` provides clean signaling. Sequential batching is appropriate.

**Session management: Deterministic and complete.** No aspirational language. Checkpoint trigger is hard-coded. Resume Dispatch Table is concrete.

**Error handling: Substantially complete.** Only missing: subagent timeout/hang detection (acceptable for V11).

#### Code Simplicity Reviewer

**Round 2 simplifications: All applied.** Template Variable Sources table removed from context.md. Scheduled Runs stubbed. Grep checks expanded.

**New simplification opportunities (~150 lines of plan bloat):**

1. **(50 lines) Per-task "Verify completeness" checklists (Tasks 2-5)** — The plan contains verbatim file contents. The checklists verify that strings exist in files the plan just specified. If the implementer writes the content from the plan, the strings are there by definition. **Remove all "Step 2: Verify completeness" substeps.**

2. **(45 lines) Task 7 Step 3 grep checks** — Same reasoning. Verification theater for verbatim-specified content. The only meaningful checks are "run tests" (Step 1) and "verify file counts" (Step 2). **Remove Task 7 Step 3.**

3. **(37 lines) V10 Failure Cross-Reference + Review Change Verification Checklist** — The V10 cross-reference was useful during design, not during implementation. The Verification Checklist duplicates the Review Changes Mapping table at the top. **Remove both; keep the mapping table.**

4. **(6 lines) Per-task "Review changes addressed" headers** — Already captured in the Review Changes Mapping table. **Remove.**

5. **(12 lines) Task 1 over-specified gitkeep/verify steps** — Collapse into the main copy step. **Simplify.**

**Total plan reduction: ~150 lines (15%), from 991 to ~841 lines.**

**Generated file sizes: Appropriate.**
- CLAUDE.md: ~222 lines (within 200-225 target after R2-11 stub)
- subagent-search-verify.md: ~188 lines
- subagent-brief.md: ~108 lines
- context.md: ~56 lines

**Task granularity: 7 tasks is correct.**

**No YAGNI remaining in the generated files.** All prior YAGNI items (Employed Mode, Jaccard, inline scoring, pre-created session-state) are removed.

#### Pattern Recognition Specialist

**All Round 2 HIGH items resolved:**
- R2-1 (`{title_slug}` derivation): Both templates have "Filename Slugification" section
- R2-2 (`{company}` slugification): Both templates include company slug rules

**All Round 2 MEDIUM items resolved:**
- R2-3: `{role_type_slug}` consistent everywhere (zero instances of hyphenated form)
- R2-4: Core Rule 3 uses "presenting" not "ranking"
- R2-5: Status vocabulary `not started → searching → verified → presented` defined consistently
- R2-6: Missing `_status.json` → treat as failed
- R2-7: partial/failed handling specified
- R2-8: Country follow-up in onboarding step 7
- R2-9: Brief completion check in step 11

**Template variable audit:**

| Template | Variables Defined | Variables Used | Status |
|----------|------------------|----------------|--------|
| subagent-search-verify.md | 12 (CLAUDE.md step 4) | 12/12 | Complete |
| subagent-brief.md | 6 (CLAUDE.md step 11) | 5/6 | `{job_id}` orphaned |

**New findings (2 medium, 3 low):**

1. **(Medium — R3-1) Parent cannot construct slugified filenames for brief verification.** CLAUDE.md Orchestration step 11 checks for `output/briefs/{company}-{title_slug}-brief.md` but defines `{company}` and `{job_title}` as raw values from JSON. The parent needs slugification instructions to construct the expected path. **Fix:** Add note to step 11: "Apply same slugification rules as subagents when constructing expected output paths."

2. **(Medium — R3-2) Core Rule 3 vs Orchestration step 9 contradiction persists.** Core Rule 3: "ALL before presenting." Step 9: "present as they become available." These are semantically incompatible. Cross-role-type dedup (step 8) requires all role types verified before running, reinforcing the gated approach. **Fix:** Reword step 9 to "After all batches complete and cross-role-type dedup runs, present results per role type."

3. **(Low — R3-3) `{job_id}` orphaned in brief variables.** Defined in step 11 but unused in brief template (data available via `{job_json_with_verification}`). **Fix:** Remove from variable list or add to brief header.

4. **(Low — R3-4) Brief template uses `{curly braces}` for both real template variables and instructional placeholders.** `{company}` in the heading is substituted by parent; `{score}` in the brief structure is an instruction for the subagent. Not a functional issue since parent substitution resolves all real variables before the subagent sees it.

5. **(Low — R3-5) `{company}` serves double duty in brief template.** Both a parent-substituted variable and an instructional placeholder. Works correctly because parent substitution happens first.

**Consistency audit: All pass.**
- Filename conventions: Consistent across CLAUDE.md, subagent-search-verify.md, subagent-brief.md
- `_status.json` path: Consistent between CLAUDE.md and subagent template
- Slug syntax: `{role_type_slug}` everywhere
- Status vocabulary: `not started | searching | verified | presented` everywhere
- Country variable flow: Complete (onboarding → context.md → CLAUDE.md step 4 → subagent template → search command)

### Required Changes

**Medium (address during implementation):**
- [ ] **R3-1: Add parent slugification for brief path verification** — In Orchestration step 11, add: "Apply same slugification rules as subagents (lowercase, hyphens, no special chars, title truncated to 50 chars) when constructing expected output path"
- [ ] **R3-2: Resolve Core Rule 3 vs step 9 contradiction** — Reword step 9 to: "After all batches complete and cross-role-type dedup runs (step 8), present results per role type, ranked by score"
- [ ] **N2: Add --output flag to search command** — In subagent template Search Workflow step 1, specify output file path
- [ ] **N3: Add algorithms.md dedup override** — In subagent template Deduplication section, add: "For deduplication, use the rules in this template, NOT algorithms.md"
- [ ] **N7: Specify subagent working directory** — Add note that all paths are relative to `03_agents/tests/v11/`

**Simplification (recommended):**
- [ ] **S1: Remove per-task "Verify completeness" checklists** — Content is specified verbatim; checklists are redundant
- [ ] **S2: Remove Task 7 Step 3 grep checks** — Same reasoning
- [ ] **S3: Remove V10 Failure Cross-Reference + Review Change Verification Checklist** — Design artifacts, not implementation guidance
- [ ] **S4: Remove per-task "Review changes addressed" headers** — Covered by mapping table at top

**Low (optional):**
- [ ] **R3-3: Remove orphaned `{job_id}` from brief variable list**
- [ ] **N1: Reword step 9 explicitly** (covered by R3-2)
- [ ] **N5: Copy `.env.example` and `.gitignore` from V10**

### Approval Status

**Approved** — The plan is ready for implementation. R3-1, R3-2, N2, N3, and N7 are medium-severity clarifications that should be addressed during implementation — none require plan revision or architectural changes. The simplification items (S1-S4) would reduce plan length by ~150 lines but are optional. All 15 original changes and 12 Round 2 changes are properly integrated. Architecture, session management, error handling, template variables, filename conventions, and status vocabulary are all sound.

---

## Round 2 - 2026-02-05 (Post-Review Plan)
**Reviewers:** Architecture Strategist, Code Simplicity Reviewer, Pattern Recognition Specialist

### Summary

All 15 Round 1 changes (C1-C15) are properly integrated into the post-review plan. The architecture is sound, YAGNI content is removed, and content deduplication is largely achieved. However, Round 2 identified 2 high-severity issues (undefined filename slug variables), 7 medium-severity issues (mostly consistency and error handling gaps), and 6 low-severity items. The plan is ready for implementation after addressing the high and medium items — none require architectural changes, only clarifications and small additions.

CLAUDE.md is 235 lines (slightly over the 200-225 target, fixable by stubbing Scheduled Runs). All 12 V10 failures remain adequately addressed.

### Findings

#### Architecture Strategist

**Round 1 fixes: All 15 verified as properly integrated.** Each change has a traceable location in the revised plan.

**New concerns (3):**

1. **(Moderate) Cross-role-type dedup timing vs presentation.** Orchestration step 8 (dedup) runs "before presenting," but step 6 launches subagents in batches and step 9 says "present results per role type as they become available." If a duplicate spans two batches, early presentation could show a job that is later deleted. **Fix:** Change step 9 to "present results after all batches complete and dedup runs," or accept per-role-type presentation with dedup only within completed batches.

2. **(Moderate) Core Rule 3 "before ranking" ambiguity.** Round 1 flagged this; the post-review partially addressed it via step sequencing but the Core Rule text still says "before ranking" not "before presenting." **Fix:** Reword to "MUST search ALL target role types before presenting any results."

3. **(Moderate) Brief subagent has no completion signal.** Search subagents have `_status.json` (C8), but brief subagents have no equivalent. Parent cannot distinguish successful brief from silent failure. **Fix:** Add a simple existence check: "After dispatching brief subagent, verify expected output file exists and is non-empty."

**Subagent coordination: Sound.** File-based coordination avoids shared mutable state. Each subagent writes to its own directory. `_status.json` provides adequate success/failure signaling for search subagents.

**Session management: Deterministic and complete.** Checkpoint trigger is hard-coded (every 2 role types). Resume Dispatch Table maps 4 phases to concrete actions. Progressive offloading is mechanical ("do NOT re-read").

#### Code Simplicity Reviewer

**Round 1 bloat removal: Complete.** All C12 (YAGNI), C13 (deduplication), C14 (trim) items verified as addressed.

**New bloat found (~64 lines across 3 areas):**

1. **(29 lines) context.md Template Variable Sources table** — duplicates CLAUDE.md Orchestration steps 4 and 11, which already list all variables with sources. Context.md is a data store, not an instruction manual. **Recommendation: Remove.**

2. **(20 lines) Review Change Verification Checklist** in plan — duplicates the Review Changes Mapping table in different format. **Recommendation: Merge into one table.**

3. **(18 lines) Verification Plan section** — duplicates Task 7 Step 3 grep checks. **Recommendation: Remove.**

**YAGNI remaining: Scheduled Runs section (13 lines of CLAUDE.md).** Describes untested headless behavior with 8 steps. **Recommendation: Replace with one-line stub** ("Scheduled runs: Not yet implemented."). This brings CLAUDE.md from 235 to ~222 lines (within target).

**Line counts:**
- CLAUDE.md: 235 lines (target 200-225, fixable to ~222)
- subagent-search-verify.md: 188 lines (appropriate)
- subagent-brief.md: 108 lines (appropriate)
- context.md: 85 lines (reducible to ~56 without Template Variable Sources table)

**Task granularity: 7 tasks is correct.**

#### Pattern Recognition Specialist

**Critical findings (2 HIGH):**

1. **`{title-slug}` / `{title_slug}` used in both subagent templates but never defined.** Appears in filenames (`{company}-{title-slug}.json`, `{company}-{title-slug}-brief.md`) in subagent-search-verify.md and subagent-brief.md. Not listed in context.md Template Variable Sources or CLAUDE.md Orchestration variable lists. No derivation rules specified. **Fix: Add derivation rule** (e.g., "Derived from job title: lowercase, spaces to hyphens, strip special characters, truncate to 50 chars"). Note: this is a subagent-derived variable (not parent-prepared), so it belongs in the subagent templates, not the orchestration variable list.

2. **`{company}` used raw in filenames without slugification.** Filenames like `{company}-{title-slug}.json` will contain spaces if company name has spaces (e.g., "Acme Corp-senior-developer.json"). **Fix: Add a note** to both subagent templates: "In filenames, slugify company and title (lowercase, spaces to hyphens, strip special characters)."

**Medium findings (5):**

3. **Slug placeholder syntax inconsistency.** CLAUDE.md Outputs section uses `{role-type-slug}` (hyphenated) while Orchestration Workflow and subagent templates use `{role_type_slug}` (underscored). **Fix: Standardize on `{role_type_slug}` everywhere.**

4. **Search Progress status vocabulary misaligned.** Core Rule 3 references status "searched," session-state schema uses "not started|searching|verified." Is "searched" = "verified"? **Fix: Define status progression explicitly.**

5. **Task 7 grep checks only verify 7 of 15 review changes.** Missing checks for C2, C4, C5, C6, C9, C10, C11, C13. **Fix: Add grep checks for remaining 8 changes.**

6. **No error handling for missing `_status.json`** (subagent dispatch failure). Parent has no instruction when file doesn't exist. **Fix: Add "If `_status.json` missing, treat as failed."**

7. **No explicit country follow-up in onboarding.** Step 7 asks "Location preferences?" with country as a parenthetical hint. If user says "Remote" without a country, `{country}` is empty. **Fix: Add conditional follow-up step 7b.**

**Low findings (4):**

8. `{job_id}` defined in brief variables but orphaned after C7 filename change — unused in brief template.
9. V10 Failure cross-reference has minor inaccuracies (Failures 5 and 12 cite wrong Core Rules).
10. No CV fallback in onboarding step 1.
11. No subagent batch timeout specified.

**V10 failure coverage: All 12 adequately addressed.** No regressions from Round 1.

### Required Changes

**High (fix before implementation):**
- [ ] **R2-1: Define `{title_slug}` derivation rules** — Add to both subagent templates: "In filenames, derive title-slug from job title: lowercase, spaces to hyphens, strip special characters, truncate to 50 chars"
- [ ] **R2-2: Define `{company}` slugification for filenames** — Add to both subagent templates: "Slugify company name in filenames using the same rules as title-slug"

**Medium (fix during implementation):**
- [ ] **R2-3: Standardize slug syntax** — Change CLAUDE.md Outputs and Presentation Workflow from `{role-type-slug}` to `{role_type_slug}`
- [ ] **R2-4: Reword Core Rule 3** — "MUST search ALL target role types before presenting any results" (replace "ranking")
- [ ] **R2-5: Align status vocabulary** — Define progression: `not started` → `searching` → `verified` → `presented`. Use consistently in Core Rule 3, Search Progress, and session-state schema
- [ ] **R2-6: Add parent error handling for `_status.json`** — "If `_status.json` missing after batch completes, treat role type as failed"
- [ ] **R2-7: Add parent error handling for partial/failed states** — "partial: present available results with note. failed: notify user, ask if they want to adjust parameters"
- [ ] **R2-8: Add country follow-up** — Onboarding step 7b: "If user doesn't mention a country, ask 'What country are you based in?'"
- [ ] **R2-9: Add brief completion check** — "After brief subagent completes, verify output file exists and is non-empty"

**Simplification (recommended):**
- [ ] **R2-10: Remove context.md Template Variable Sources table** — Duplicates CLAUDE.md Orchestration steps 4 and 11
- [ ] **R2-11: Stub Scheduled Runs section** — Replace 13-line section with one-line stub (brings CLAUDE.md to ~222 lines)
- [ ] **R2-12: Add missing Task 7 grep checks** — Cover C2, C4, C5, C6, C9, C10, C11, C13

### Approval Status

**Approved with changes** — R2-1 and R2-2 (filename slugification) must be addressed. R2-3 through R2-9 should be addressed during implementation. R2-10 through R2-12 are recommended simplifications. No architectural changes needed — all fixes are clarifications and small additions to existing plan content.

---

## Round 1 - 2026-02-05 15:30
**Reviewers:** Architecture Strategist, Code Simplicity Reviewer, Pattern Recognition Specialist

### Summary

The V11 plan is architecturally sound. The 3-tier agent model (parent + search subagents + brief subagents) is well-motivated by V10's context exhaustion failure. The MUST/NEVER enforcement rules are a significant structural upgrade. However, the plan has 7 critical gaps (mostly around template variable handling and resume logic), several YAGNI violations, and ~30% content bloat from duplicated scoring rubrics, premature features, and oversized sections.

10 of 12 V10 failures are adequately addressed. Failures 5 (cherry-picking) and 11 (context exhaustion) are structurally improved but retain residual risk.

### Findings

#### Architecture Strategist

**Strengths:**
- 3-tier agent model is justified by demonstrated context exhaustion (V10 Failure 11)
- File-based coordination via `output/verified/{role_type}/` is correct for Claude Code
- Template-based subagent dispatch is a clean separation of concerns
- MUST/NEVER rules at the top of CLAUDE.md are high-signal placement
- Failure-to-fix mapping is thorough — all 12 V10 failures have traceable fixes

**Weaknesses:**
- Template variable substitution is the critical bridge between parent and subagents, but the plan never demonstrates how it works (no Task tool invocation example, no variable-to-source mapping)
- Session management uses aspirational language ("if context running low") rather than deterministic triggers — the exact pattern that caused V10 failures
- Resume flow is underspecified — no dispatch table mapping phase values to resumption actions
- No subagent completion signal — parent can't distinguish empty results from silent failure
- Role-type directory names will contain spaces ("Community Manager/"), creating fragile paths

**Key risk:** Rate limiting from concurrent subagents hitting Indeed/LinkedIn/Glassdoor. The plan mentions batching to "avoid rate limiting" but has no retry logic or detection instructions.

#### Code Simplicity Reviewer

**Over-engineering found:**
- CLAUDE.md is ~300 lines vs design's ~180 estimate. Bloat from: File Structure ASCII tree (28 lines), per-job presentation format (duplicates subagent output), unchanged V10 sections presented as new, verbose Scheduled Runs section
- Subagent-search-verify.md duplicates scoring rubric (~30 lines) and skill normalization table (~13 lines) that already exist in `references/algorithms.md`
- context.md includes Employed Mode (YAGNI — user doesn't have a job yet), Workflow section (duplicates CLAUDE.md), and a third copy of the Scoring Rubric
- session-state.md schema defined in two places (CLAUDE.md + Task 6)
- Pre-created session-state.md template provides no value — agent creates it at first checkpoint

**YAGNI violations:**
- Employed Mode in context.md (3 operational modes for after user gets a job)
- Scheduled Runs conservative defaults (no scheduled run has been tested)
- Jaccard similarity deduplication (agent can't compute this reliably; no script supports it)
- Glassdoor as mandatory research step (frequently blocks automated access)

**Estimated reduction:** ~180 lines across all files (30% of planned content), achieving closer alignment with design estimates.

#### Pattern Recognition Specialist

**Critical patterns found:**
- Hardcoded `--country UK` in subagent search command — no template variable for country. Silent wrong results for non-UK users.
- Brief subagent variable preparation completely missing from Orchestration Workflow — 6 variables (`{profile_extract}`, `{job_json_with_verification}`, `{job_id}`, etc.) never defined
- Brief filename convention conflicts: CLAUDE.md says `{company}-{title-slug}-brief.md`, brief template says `{job_id}-brief.md`
- Core Rule 3 says "MUST search ALL before ranking" but Orchestration step 7 says "present as each subagent completes" — the word "ranking" creates ambiguity about whether per-role-type incremental presentation is allowed
- Scheduled Runs step 4 generates briefs at 80%+ but conservative defaults include jobs at 70%+ — digest would reference non-existent briefs
- No cross-role-type deduplication — same job found by two subagents appears in both verified directories

**V10 failure coverage:**
- 10/12 fully addressed
- Failure 5 (cherry-picking): structurally improved by subagent model but parent cannot audit completeness
- Failure 11 (context exhaustion): structurally improved by subagents but progressive offloading is aspirational, not mechanical

### Required Changes

- [ ] **C1: Add `{country}` template variable** — Replace hardcoded `--country UK` in subagent template with `{country}` derived from location preferences
- [ ] **C2: Add brief subagent variable preparation** — Explicit step in Orchestration Workflow listing 6 variables and their sources (especially `{profile_extract}` and `{job_json_with_verification}`)
- [ ] **C3: Add resume dispatch table** — Map each session-state phase to specific resumption actions in On Startup section
- [ ] **C4: Add Task tool invocation example** — Show how parent reads template, fills variables, dispatches via Task tool in Orchestration Workflow
- [ ] **C5: Add variable-to-source mapping** — Table showing where each of the 10 search template variables comes from in context.md, including extraction format
- [ ] **C6: Slugify directory names** — Use `{role-type-slug}` (e.g., `community-manager/`) instead of `{role_type}` for output directory paths
- [ ] **C7: Fix brief filename convention** — Align CLAUDE.md Outputs section with brief subagent template (choose one pattern)
- [ ] **C8: Add subagent completion signal** — `_status.json` per role type with total_searched, total_verified, status (complete/partial/failed)
- [ ] **C9: Add rate-limit handling** — Retry-once logic for zero-result searches in subagent template
- [ ] **C10: Replace aspirational context trigger** — Change "if context running low" to deterministic rule (e.g., checkpoint after every 2 role types)
- [ ] **C11: Specify progressive offloading mechanically** — "Do NOT re-read verified files after recording feedback. Reference session-state.md summaries only."
- [ ] **C12: Remove YAGNI content** — Employed Mode from context.md, Scheduled Runs conservative defaults, pre-created session-state.md template, Jaccard dedup (use exact match)
- [ ] **C13: Deduplicate content** — Reference `algorithms.md` for scoring rubric and skill normalization instead of inlining in subagent template. Remove Workflow and Scoring Rubric from context.md. Define session-state schema once.
- [ ] **C14: Trim CLAUDE.md** — Remove File Structure ASCII tree, per-job presentation format, collapse unchanged V10 sections. Target ~200-225 lines.
- [ ] **C15: Add cross-role-type dedup rule** — Parent checks for duplicates across role-type directories before presenting

### Approval Status

**Needs Changes** — 7 critical gaps (C1-C7) must be addressed in the plan before implementation. Simplification items (C12-C14) are recommended but not blocking.

---

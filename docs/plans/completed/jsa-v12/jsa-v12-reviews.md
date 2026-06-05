# JSA V12 Reviews

## Round 6 - 2026-02-06 (Final Validation)
**Reviewers:** architecture-strategist, code-simplicity-reviewer, pattern-recognition-specialist

### Summary

Round 6 validates the plan after all 11 changes from Round 5 were incorporated. Three reviewers found **0 required changes** and **0 recommended changes**. The plan is approved for `/build`.

The architecture reviewer performed a deep trace of all variable paths, error handling branches, parallel execution safety, and status file contracts — finding no remaining defects. The pattern reviewer validated all 7 focus areas (compact dispatch consistency, field names, status contracts, template structure, variable counts, step numbering, Task 10 checks) — all confirmed correct. The simplicity reviewer confirmed the plan is proportional to the work after 5 rounds of trimming.

All Round 5 changes confirmed correctly incorporated.

### Findings

#### Architecture Review

**Approved — 0 required changes.** Thorough validation of:

1. **Compact dispatch pattern:** All 4 subagent types follow identical structural pattern. Variable counts (13, 7, 5, 1) verified against JSON blobs. Variable validation failure behavior specified for all dispatches.

2. **Schema standardization:** V12 schema matches actual Schema B output (greenpixie reference file). Score values internally consistent (32+13+15+15+10=85, matching both `score: 85` and `total: 85`). All old V11 field names absent.

3. **Status file contracts:** Well-defined for all 4 subagent types. Parent error handling branches complete (3-branch for digest, 2-branch for briefs-PDF, file-exists for brief).

4. **Parallel execution (steps 13-14):** Confirmed safe — no write-write or read-write conflicts between digest (writes to `output/digests/`) and briefs-PDF (writes `.pdf` + `_briefs-pdf-status.json` to `output/briefs/`). Digest reads only `.md` files from `output/briefs/`, skipping `_`-prefixed and `.pdf` files.

5. **Variable tracing:** All 26 variables (13+7+5+1) traced from source (context.md) through parent preparation to subagent consumption. No missing or orphaned variables.

3 informational observations (non-blocking):
- Digest subagent has the most complex workflow (6 steps) — monitor for context constraints at runtime with many verified jobs
- Copied test files may contain relative imports — verify at build time
- Checkpoint interval change (2→3 role types) is a reasonable tradeoff given V11's successful completion

#### Simplicity Review

**Approved — 0 required changes, 0 YAGNI violations remaining.** Detailed assessment:

- **Plan proportionality:** 694 lines for 13 changes across 15 files with 2 new templates is appropriate. Not bloated.
- **Task 10 verification:** 6 checks is well-calibrated (trimmed from 25 in Round 4).
- **JSON schema in Task 4:** Full 55-line schema is justified — V11→V12 was a fundamental restructure (nested wrapper removed, fields renamed), not a diff-friendly change.
- **Compact dispatch repetition:** 4 dispatches repeat the same pattern. Justified — prompt templates can't reference shared functions. The executing agent reads CLAUDE.md linearly.
- **1 minor observation:** "All titles hyperlinked" rule stated twice (table example + standalone rule, lines 175/181). ~1 line redundancy. Not worth the risk of removing.
- **Design constraints in Task 6:** Borderline over-specified (4 lines of typography/color rules), but prevents round-trip corrections at runtime.
- **Prior YAGNI kills confirmed effective:** Freshness 3-tier (R1), CONTEXT CONSERVATION (R1), dead script copy (R1), 25-check matrix (R4), post-implementation test plan (R5), review metadata (R3), negative `skipped_stale` instruction (R5) — all correctly removed.
- **Total additional simplification possible:** ~5-10 lines (<2%). Not worth the ambiguity risk.

#### Pattern Review

**Approved — 0 required changes.** Comprehensive validation across all 7 focus areas:

| Focus Area | Status |
|------------|--------|
| 1. Compact dispatch pattern (4 types) | CONSISTENT |
| 2. Field names across templates | CONSISTENT |
| 3. Status file contracts | CONSISTENT |
| 4. Template structural pattern | CONSISTENT |
| 5. Variable counts (13, 7, 5, 1) | CORRECT |
| 6. Step numbering (1-14) | CORRECT, no gaps or overlaps |
| 7. Task 10 verification checks | CORRECT, all 6 target right patterns |

Specific validations:
- COMPACT PATTERN grep: 4 hits confirmed (steps 5, 11, 13, 14)
- HARD RULE grep: 2 hits confirmed (steps 3, 12)
- Schema example: 32+13+15+15+10=85, top-level and breakdown total both 85
- Field names: `job_url`, `work_arrangement`, `date_posted`, `score` (integer) used consistently throughout. No old V11 field names present.

---

### Required Changes

None.

### Recommended Changes

None.

### Approval Status

**Approved.** The plan is ready for `/build`. Five rounds of review have resolved all inconsistencies. All 33+ changes are correctly incorporated. No remaining architectural, simplicity, or pattern issues.

---

## Round 5 - 2026-02-06 (Final Validation)
**Reviewers:** architecture-strategist, code-simplicity-reviewer, pattern-recognition-specialist

### Summary

Round 5 validates the plan after all 10 changes from Round 4 were incorporated. Three reviewers found **3 required changes** (schema example score mismatch, digest cleanup condition, digest partial-branch under-specified) and **8 recommended changes** (deduplicated from 17 raw recommendations). The pattern reviewer found **0 required changes** — confirming all structural patterns are consistent.

All Round 4 changes confirmed correctly incorporated.

### Findings

#### Architecture Review

**2 required changes found:**

1. **Schema example score mismatch.** Task 4 Step 4.3 schema shows `"score": 75` at top level but `"score_breakdown": { ... "total": 80 }` inside the breakdown — different values in the same example. Additionally, the individual breakdown components (32+13+15+15+10=85) don't sum to either stated total. Actual V11 Schema B files always have matching values (e.g., greenpixie: `"score": 90`, `"total": 90`). Subagents using this schema as a reference will produce inconsistent data.

2. **Digest cleanup deletes email debug artifact.** Task 6 Step 6 condition is "ONLY IF `pdf_generated: true`: delete intermediate files" — but when status is `"partial"` (PDF succeeded, email failed), this deletes `_email-body.md` which is needed to debug the email failure.

7 recommended improvements documented — all non-blocking. Confirmed steps 13-14 parallel execution is genuinely safe (no mutual dependency). Architecture is well-designed.

#### Simplicity Review

**1 required change found:**

1. **Digest `"partial"` branch under-specified.** Lines 258-262: the `"partial"` instruction says "check which fields succeeded" without specifying WHICH fields to check. Compare with `"complete"` which lists `pdf_generated`, `email_sent`, etc. The executing agent will improvise. Either specify the fields or simplify to 2 branches.

5 recommended improvements documented. Overall assessment: plan is proportional to the work after 4 rounds of trimming. Task 10's 6 checks are well-calibrated. Variable validation repetition is justified (prompt templates, not shared code).

#### Pattern Review

**0 required changes found.** All 33 changes from Rounds 1-4 correctly incorporated. Compact dispatch pattern consistent across all 4 subagent types. Schema reconciled with actual Schema B output. Field naming (`job_url`, `work_arrangement`, `date_posted`, `verified_at`) consistent throughout. Template structural sections follow uniform pattern. `send_email.py` interaction (`--html --file`) correctly designed.

5 recommended pattern improvements documented — all non-blocking.

---

### Required Changes

- [x] **R5-RC-1: Fix schema example score values to be internally consistent.** Task 4 Step 4.3 schema (lines 323-373): top-level `"score": 75` does not match `"score_breakdown.total": 80`. Individual components (32+13+15+15+10=85) don't sum to either value. **Fix:** Pick one consistent total (e.g., 85) and set both `"score": 85` and `"total": 85`. Adjust individual component values to sum correctly. Actual Schema B files always have matching values.

- [x] **R5-RC-2: Tighten digest cleanup condition to preserve email debug artifacts.** Task 6 Step 6 currently: "ONLY IF `pdf_generated: true`: delete intermediate files." This deletes `_email-body.md` even when email failed (`"status": "partial"`). **Fix:** Change condition to "ONLY IF `status` is `\"complete\"`: delete intermediate files." This preserves all intermediates when anything failed.

- [x] **R5-RC-3: Specify digest `"partial"` branch fields.** Lines 258-262: `"partial"` branch says "check which fields succeeded, notify user with partial status" without listing the fields. **Fix:** Replace with: "If `\"partial\"` → PDF generated but email failed. Notify user: 'Digest PDF saved to output/digests/{run_date}.pdf but email send failed. Check .env for RESEND_API_KEY.' Offer to retry email only."

### Recommended Changes

- [x] **R5-REC-1: Add "skip files starting with `_`" to cross-role dedup scan (step 8).** Consistency with skip-prefix pattern used by digest and briefs-PDF subagents. Low risk without it (filename pattern wouldn't match `_status.json` as a company+title), but explicit is better. *(Architecture + Pattern)*

- [x] **R5-REC-2: Add explicit top-level field extraction note to brief template.** Beyond the one-line R3-REC-5 note, add: "Extract `score` from the top-level `score` field (integer). Extract breakdown from `score_breakdown` (top-level object). Do NOT look inside a `verification` wrapper." Eliminates schema migration ambiguity. *(Architecture)*

- [x] **R5-REC-3: Specify brief dispatch failure behavior explicitly.** Step 11 says "write failure status and exit" without specifying WHERE to write. Other 3 dispatches have explicit file paths and JSON format. Either add a status file path or change to "exit without writing any output files." *(Simplicity + Pattern)*

- [x] **R5-REC-4: Add `pip3 install markdown` to digest subagent pre-checks.** `send_email.py` imports `markdown` for HTML conversion (line 36). Without it, falls back to `<pre>` wrapping — poorly formatted email. *(Architecture)*

- [x] **R5-REC-5: Add guard or fallback for digest dispatch when zero briefs exist.** Step 14 (briefs-PDF) has "If any briefs generated" guard. Step 13 (digest) has no equivalent guard. If user rejects all jobs, digest's "Top Opportunities" section would be empty. Either add parent guard or template fallback. *(Architecture)*

- [x] **R5-REC-6: Remove post-implementation verification plan (lines 694-708).** 15-line section duplicates Task 10's checks in vaguer form. These are runtime testing concerns, not implementation verification. Move to separate `jsa-v12-test-plan.md` if needed. *(Simplicity)*

- [x] **R5-REC-7: Add explicit source mapping for digest dispatch variables.** `{user_email}` and `{user_name}` lack source mapping (unlike search-verify's detailed variable sourcing). Add: `user_email` from context.md `## Delivery`, `user_name` from context.md `## Profile`. *(Pattern)*

- [x] **R5-REC-8: Remove negative instruction about `skipped_stale` (lines 378-379).** Step 4.4 tells the executing agent NOT to add a field from a system removed in Round 1. Review-process artifact, not implementation instruction. *(Simplicity)*

### Approval Status

**Approved with 3 required changes** — R5-RC-1 (schema score consistency), R5-RC-2 (cleanup condition), R5-RC-3 (partial branch specification). All three are small, targeted fixes. 8 recommended changes would improve robustness but are not blocking.

---

## Round 5 Changes Incorporated — 2026-02-06

All 3 required + 8 recommended changes from Round 5 have been incorporated into `jsa-v12-plan.md`. The plan is now ready for `/build`.

| Change | Status |
|--------|--------|
| R5-RC-1: Fix schema example score values (75/80 → 85/85) | Incorporated |
| R5-RC-2: Tighten digest cleanup condition (pdf_generated → status complete) | Incorporated |
| R5-RC-3: Specify digest partial branch fields | Incorporated |
| R5-REC-1: Add skip `_` prefix to cross-role dedup scan | Incorporated |
| R5-REC-2: Explicit top-level field extraction note in brief template | Incorporated |
| R5-REC-3: Brief dispatch failure exits without writing files | Incorporated |
| R5-REC-4: Add `pip3 install markdown` to digest pre-checks | Incorporated |
| R5-REC-5: Guard for digest dispatch when zero briefs | Incorporated |
| R5-REC-6: Remove post-implementation verification plan | Incorporated |
| R5-REC-7: Add variable source mapping for digest dispatch | Incorporated |
| R5-REC-8: Remove negative `skipped_stale` instruction | Incorporated |

---

## Round 4 Changes Incorporated — 2026-02-06

All 3 required + 7 recommended changes from Round 4 have been incorporated into `jsa-v12-plan.md`. The plan is now ready for `/build`.

| Change | Status |
|--------|--------|
| R4-RC-1: Schema reconciliation (preferred_met + notes) | Incorporated |
| R4-RC-2: Fix step number prose 10→11 | Incorporated |
| R4-RC-3: Retain brief variable preparation | Incorporated |
| R4-REC-1: Add "confirm 7 variables" to brief dispatch | Incorporated |
| R4-REC-2: Remove "partial" branch from briefs-PDF | Incorporated |
| R4-REC-3: Clarify digest PDF vs email outputs | Incorporated |
| R4-REC-4: date_posted check 1→1+ hits | Incorporated |
| R4-REC-5: Status file handling note | Incorporated |
| R4-REC-6: Simplify Task 10 to 6 essential checks | Incorporated |
| R4-REC-7: Add WebFetch permission | Incorporated |

---

## Round 4 - 2026-02-06 (Final Validation)
**Reviewers:** architecture-strategist, code-simplicity-reviewer, pattern-recognition-specialist

### Summary

Round 4 validates the plan after all 33 changes from Rounds 1-3 were incorporated. The architecture reviewer approved with **0 required changes**. The simplicity reviewer found **2 required changes** (schema reconciliation, stale status files). The pattern reviewer found **5 required changes** (step numbering prose, brief variable preparation, brief variable count, PDF/email clarification, Task 10 check count).

After cross-referencing and deduplication: **3 required changes** (one is a clear bug, two are meaningful clarifications) and **7 recommended changes**. The plan is architecturally sound and nearly ready for `/build`.

### V11 Schema Analysis (New Finding)

Three reviewers independently examined actual V11 verified JSON output and found **three distinct schemas** in production:

| Schema | Example File | `score` | `url` field | `remote` field |
|--------|-------------|---------|-------------|----------------|
| A (nested) | alchemy-web3-product-marketing-manager.json | `verification.score` (nested) | `url` | `remote: true` |
| B (flat) | greenpixie-founder-associate.json | `score: 90` (integer) | `job_url` | `work_arrangement` |
| C (object) | dia-growth-marketing-associate.json | `score: {total: 78}` (object) | `url` | none |

The V12 plan correctly standardizes on **Schema B**. Since V12 creates a clean directory with fresh `context.md` (all progress reset), V12 subagents will only produce Schema B output. The schema heterogeneity is a V11 artifact, not a V12 concern.

However, the plan's proposed schema (Task 4, lines 310-359) has minor divergences from actual Schema B output — see RC-1 below.

### Findings

#### Architecture Review

**Approved — 0 required changes.** All 33 review changes correctly incorporated. Compact dispatch consistent across all 4 subagent types. `_status.json` contracts well-defined with 3-branch error handling. Cross-role dedup correctly placed. Step numbering verified correct (1-7 original, 8 new dedup, 9-12 renumbered, 13-14 new). Variable count (13) verified against JSON blob. `--html --file` email interaction verified correct (markdown input, single conversion).

6 recommended improvements documented — all non-blocking.

#### Simplicity Review

**2 required changes found:**

1. **Schema reconciliation:** The plan's proposed V12 schema includes `notes` field not present in actual Schema B output, and omits `preferred_met` field that IS present in Schema B output. Minor drift that could cause subagent confusion.

2. **Stale status files:** The ON STARTUP sequence doesn't mention clearing leftover `_status.json` files from previous runs. Mitigated by subagent overwrite behavior, but worth a clarifying note.

Also flagged: Task 10's 25 grep checks are disproportionate for prompt engineering, variable validation boilerplate is repeated 4 times, and the `"partial"` status branch in briefs-PDF dispatch is dead logic (that template only produces `"complete"` or `"failed"`).

#### Pattern Review

**3 required changes found:**

1. **Change 9 prose says "Rewrite step 10" but content is labeled step 11.** The renumbering (Change 4) moved old step 10 to step 11. The content block correctly starts with "11." but the prose header conflicts. An executing agent could create a duplicate step 10.

2. **Brief variable preparation instructions dropped.** V11's step 10 (lines 118-127) contains both variable preparation (where to get `profile_extract`, `job_json_with_verification`, etc.) AND dispatch logic. Change 9 replaces with compact dispatch only — the variable source definitions are lost. The executing agent building V12 CLAUDE.md won't know where brief variables come from.

3. **Brief dispatch lacks explicit variable count.** Search-verify says "confirm 13 variables", digest says "confirm 5", briefs-PDF says "confirm 1", but brief says only "if any variable missing" — no count. Pattern inconsistency.

Also flagged: digest Step 4 ("create HTML" for PDF) adjacent to Step 5 ("write markdown" for email) could confuse the executing agent. Task 10 check #7 expects exactly "1 hit" for `date_posted` in CLAUDE.md — fragile if the executing agent adds additional references.

---

### Required Changes

- [x] **R4-RC-1: Reconcile V12 schema with actual Schema B output.** The plan's schema (Task 4, lines 310-359) includes `"notes"` which is absent from Schema B files (e.g., greenpixie). It also omits `"preferred_met"` which IS present in Schema B files. **Fix:** Add `"preferred_met": []` to the schema. Either add `"notes"` as an optional field with a comment ("optional context") or remove it. Verify by diffing the proposed schema against `greenpixie-founder-associate.json`.

- [x] **R4-RC-2: Fix Change 9 prose header from "step 10" to "step 11".** Line 204 says "Rewrite step 10 (brief dispatch)" but the content block starts with "11." per the renumbering from Change 4. Change to "Rewrite step 11 (brief dispatch, renumbered from V11 step 10)". This prevents the executing agent from numbering it as step 10.

- [x] **R4-RC-3: Retain brief variable preparation instructions in Change 9.** V11's step 10 (lines 118-126) defines where each brief variable comes from (`{profile_extract}` = copy from context.md `## Profile`, `## Skills`, `## Experience`; `{job_json_with_verification}` = complete verified JSON file contents; etc.). Change 9 replaces step 10 with compact dispatch only, dropping these definitions. **Fix:** Add a note before the dispatch block: "Retain the variable preparation instructions from V11 step 10 — define where each of the 7 brief variables comes from before the dispatch block." Or include the variable source list explicitly.

### Recommended Changes

- [x] **R4-REC-1: Add "confirm 7 variables parsed" to brief dispatch.** Pattern consistency with the other 3 dispatches (13, 5, 1). Currently brief dispatch says only "if any variable missing" — no explicit count.

- [x] **R4-REC-2: Remove "partial" status branch from briefs-PDF dispatch (step 14).** The briefs-PDF template (Task 7) defines only `"complete"` and `"failed"` — no `"partial"` state. The parent dispatch's 3-branch check for briefs-PDF is dead logic.

- [x] **R4-REC-3: Add clarifying note in digest template between Steps 4 and 5.** Step 4 creates HTML (for PDF). Step 5 writes markdown (for email). Add one line: "Note: The PDF (Step 4) and email body (Step 5) are separate outputs. The email body is markdown, NOT the HTML from Step 4."

- [x] **R4-REC-4: Change Task 10 check #7 expected count from "1 hit" to "1+ hits".** Fragile exact-count check — the executing agent may add additional `date_posted` references during CLAUDE.md assembly.

- [x] **R4-REC-5: Add note about stale status files.** Either add "Delete any `_status.json` / `_briefs-pdf-status.json` files in output directories" to ON STARTUP, or add a clarifying note that subagents overwrite status files per-run.

- [x] **R4-REC-6: Simplify Task 10 verification to essential checks.** 25 grep checks is disproportionate for prompt engineering. Reduce to 5-6 essentials: (1) no v11 references, (2) COMPACT PATTERN count, (3) HARD RULE count, (4) schema field names in search template, (5) new template files exist, (6) no create_briefs_pdf.py.

- [x] **R4-REC-7: Confirm `WebFetch` permission in settings.local.json.** Task 9 includes `WebSearch` but not `WebFetch`. Subagent templates use WebFetch extensively for company research and job verification. If it requires explicit allowlisting (separate from WebSearch), add it.

### Approval Status

**Approved with 3 required changes** — R4-RC-1 (schema reconciliation), R4-RC-2 (step number prose fix), R4-RC-3 (brief variable preparation). All three are small, targeted fixes. 7 recommended changes would improve robustness but are not blocking.

---

## Round 3 Changes Incorporated — 2026-02-06

All 3 required + 6 recommended changes from Round 3 have been incorporated into `jsa-v12-plan.md`. The plan is now ready for `/build`.

| Change | Status |
|--------|--------|
| R3-RC-1: Step number 10→11 | Incorporated |
| R3-RC-2: _status.json write ordering | Incorporated |
| R3-RC-3: Duplicate _email-body.md deletion | Incorporated |
| R3-REC-1: Bare _status.json paths | Incorporated |
| R3-REC-2: Conditional cleanup for briefs-PDF | Incorporated |
| R3-REC-3: Variable validation for digest/briefs-PDF | Incorporated |
| R3-REC-4: (job_url) in example tables | Incorporated |
| R3-REC-5: Schema migration note in Task 5 | Incorporated |
| R3-REC-6: Strip review metadata from plan | Incorporated |

---

## Round 3 - 2026-02-06 (Final Validation)
**Reviewers:** architecture-strategist, code-simplicity-reviewer, pattern-recognition-specialist

### Summary

Round 3 validates the plan after all 24 changes from Rounds 1-2 were incorporated. The architecture reviewer approved with 0 required changes. The simplicity and pattern reviewers converged on **3 required changes** — two are runtime ordering bugs in the digest template, one is a step-numbering conflict. Additionally, **6 recommended changes** were identified across all three reviewers (deduplicated from 15 raw recommendations).

All three reviewers confirmed that the 24 Round 1-2 changes are correctly incorporated.

### Round 2 Change Verification

All 9 Round 2 changes confirmed incorporated:

| Change | Status | Notes |
|--------|--------|-------|
| R2-RC-1: Fix variable count 12→13 | Verified | "13 variables" in Change 3, JSON blob, and Task 10 check |
| R2-RC-2: Fix --html --file email | Verified | Writes markdown to `.md`, `send_email.py` converts once |
| R2-RC-3: Brief template remote→work_arrangement | Verified | Task 5 changes line 51 correctly |
| R2-REC-1: Error state handling for _status.json | Verified | Steps 13-14 read status field first with 3-branch logic |
| R2-REC-2: Standardize skip pattern (prefix _) | Verified | Both templates use "skip files starting with `_`" |
| R2-REC-3: Score must be integer note | Verified | Explicit comment in schema |
| R2-REC-4: Consolidate verification to Task 10 | Verified | Task 3 defers to Task 10 |
| R2-REC-5: Conditional cleanup on PDF success | Verified | Step 6 checks `pdf_generated: true` |
| R2-REC-6: Variable validation failure behavior | Verified | Write `_status.json` with failed status and exit |

### Findings

#### Architecture Review

**Approved — 0 required changes.** All 24 review changes correctly incorporated. Compact dispatch consistent across all 4 subagent types. `_status.json` contracts well-defined with proper error handling. Cross-role dedup correctly placed. Schema alignment complete.

Minor notes: digest cleanup ordering has a sequencing ambiguity (Completion Signal after Step 6). Brief subagent remains the only one without `_status.json` — acceptable for V12 since briefs are atomic.

#### Simplicity Review

**2 required changes found**, both in the digest template (Task 6):

1. **Status-write ordering:** Step 6 reads `_status.json` to decide on cleanup, but the Completion Signal section writes it "after all steps." The file doesn't exist when Step 6 tries to read it.

2. **Duplicate email-body deletion:** Step 5 unconditionally deletes `_email-body.md`. Step 6 conditionally deletes the same file. Dead conditional logic.

Overall assessment: plan is proportional to the work. Remaining complexity is review-process metadata (provenance tags, mapping tables) that could be stripped but is not blocking.

#### Pattern Review

**2 required changes found** (1 overlaps with simplicity):

1. **Step numbering conflict:** Change 9 labels brief dispatch as step 10, but Change 4 renumbers old step 10 to step 11. The executing agent would produce a CLAUDE.md with duplicate step 10s.

2. **Digest cleanup ordering** (same as simplicity RC-1): Step 6 reads `_status.json` before the Completion Signal writes it.

Schema consistency confirmed across all templates. Template structural patterns match. Naming conventions consistent. `--html --file` interaction verified correct against `send_email.py` source.

---

### Required Changes

- [x] **R3-RC-1: Fix brief dispatch step number from 10 to 11.** Change 4 inserts step 8 (cross-role dedup) and renumbers old 8→9, 9→10, 10→11, 11→12. But Change 9 labels brief dispatch as step "10." — it should be "11." to match the renumbering. Also update Task 10 check #2 parenthetical from "(steps 5, 10, 13, 14)" to "(steps 5, 11, 13, 14)".

- [x] **R3-RC-2: Fix digest `_status.json` write ordering.** In Task 6's digest template, move the Completion Signal (`_status.json` write) to happen between Step 5 (email) and Step 6 (cleanup). Step 6 reads `_status.json` for conditional cleanup, so the file must exist before Step 6 runs. Restructure: Steps 1-5 → write `_status.json` → Step 6 reads it for cleanup decisions.

- [x] **R3-RC-3: Remove duplicate `_email-body.md` deletion.** Task 6 Step 5 unconditionally deletes `_email-body.md` (line 500). Step 6 conditionally deletes it again (line 505). Remove the unconditional delete from Step 5 — let Step 6's conditional cleanup handle all intermediate file deletion in one place.

### Recommended Changes

- [x] **R3-REC-1: Fix bare `_status.json` paths in pre-check sections.** Digest pre-check (line 444) says `write _status.json` without directory prefix — should be `output/digests/_status.json`. Briefs-PDF pre-check (line 564) same issue — should be `output/briefs/_briefs-pdf-status.json`. Both line 446 and 566 use the correct full paths; the earlier references should match.

- [x] **R3-REC-2: Apply conditional cleanup to briefs-PDF template.** Digest (Task 6) has conditional cleanup per R2-REC-5. Briefs-PDF (Task 7) Step 4 unconditionally deletes `.html` files. Apply same pattern: "ONLY IF `pdf_generated: true`, delete intermediates."

- [x] **R3-REC-3: Add variable validation to digest and briefs-PDF dispatches.** Search-verify and brief dispatches include "if any variable missing, write status and exit." Digest and briefs-PDF dispatches omit this. Low risk (5 and 1 variables respectively) but adding consistency.

- [x] **R3-REC-4: Use `(job_url)` in example table rows.** Presentation workflow (line 208) and digest template (line 471) show `[Title](url)` in examples. Should be `[Title](job_url)` to match the schema field name.

- [x] **R3-REC-5: Add schema migration note to Task 5 (brief template).** V12 schema changed from nested (`verification.score`) to flat (`score`). Brief subagent receives full JSON via `{job_json_with_verification}`. One-line note clarifying top-level field extraction reduces ambiguity.

- [x] **R3-REC-6: Strip review-process metadata from plan.** The 28-line "Review Changes Applied" mapping table (lines 37-64), inline `[RC-X]`/`[REC-X]` tags, and review-round accounting in the goal line are useful for reviewers but noise for the executing agent. Non-blocking but would reduce plan from ~735 to ~635 lines.

### Approval Status

**Approved** — All 3 required + 6 recommended changes incorporated. Plan is ready for `/build`.

---

## Round 2 - 2026-02-06 (Post-Review Plan)
**Reviewers:** architecture-strategist, code-simplicity-reviewer, pattern-recognition-specialist

### Summary

Round 2 reviews the **post-review plan** — the version that incorporated all 6 required and 9 recommended changes from Round 1. The plan is significantly improved. All Round 1 issues are addressed. However, three reviewers converged on **3 new required changes** and **6 recommended changes**. Two of the required changes are bugs that would cause visible failures at runtime.

### Round 1 Change Verification

All 15 Round 1 changes are incorporated in the post-review plan:

| Change | Status | Notes |
|--------|--------|-------|
| RC-1: `_status.json` for new templates | Applied | Steps 13-14 read status files |
| RC-2: pdfkit/wkhtmltopdf pre-check | Applied | Both templates have Pre-checks section |
| RC-3: `date_posted` not `posted_date` | Applied | Schema aligned correctly |
| RC-4: Compact dispatch for briefs | Applied | Step 10 uses compact pattern |
| RC-5: Standard structural sections | Applied | Both templates have Your Task/Working directory/Core Rules/Completion Signal |
| RC-6: `.gitignore` PDFs | Applied | `output/briefs/*.pdf` and `output/digests/*.pdf` added |
| REC-1: Simplify freshness filter | Applied | Single rule: >30 days = present last with note |
| REC-2: Cut CONTEXT CONSERVATION | Applied | One line in SESSION MANAGEMENT |
| REC-3: Don't copy create_briefs_pdf.py | Applied | 4 of 5 scripts copied |
| REC-4: Simplify HARD RULE wording | Applied | Condensed to one instruction |
| REC-5: Steps 13-14 parallel | Applied | Note added |
| REC-6: Empty results fallback | Applied | "No strong matches found" fallback |
| REC-7: Variable count validation | Applied | "12 variables parsed" check added (but see RC-1 below) |
| REC-8: File-based email body | Applied | `--file` flag used (but see RC-2 below) |
| REC-9: Schema alignment | Applied | Full Schema B with `job_url`, `work_arrangement`, `date_posted` |

### Findings

#### Architecture Review

The architecture is sound. Compact dispatch, new subagent templates, cross-role dedup, and `_status.json` contracts are all correctly integrated. The plan addresses all 8 V11 failures and all 15 Round 1 review changes.

**New concerns:**
- The parent orchestrator checks `pdf_generated: true` and `email_sent: true` but has no defined behavior for error states (`"status": "failed"` with an `"error"` field). Should check `status` first.
- No PDF validation after generation (file size > 0 check).
- The brief subagent remains the only subagent without a `_status.json` — minor inconsistency.

#### Simplicity Review

The post-review plan is meaningfully leaner than the pre-review version. Freshness 3-tier classification is gone, CONTEXT CONSERVATION is gone, dead code copy is gone. Residual complexity:
- Task 10 verification (18 positive + 7 negative grep checks) is heavy for a prompt engineering task. Could be cut to 4-5 essential checks.
- Task 3 inline verification (14 greps at end) duplicates Task 10. Pick one approach.
- The full 50-line JSON schema in Task 4 could be a diff description instead.

**Overall:** The plan is proportional to the work. Not blocking.

#### Pattern Review

**Critical finding confirmed and verified against source code:** The `send_email.py` script's `--html` flag runs content through `markdown_to_html()` (line 70). The digest template writes an HTML file and passes it with `--html --file`. This will double-convert HTML through a markdown converter, producing garbled email output.

**Second critical finding verified:** The `subagent-brief.md` template at line 51 uses `Remote: {remote}` but the V12 canonical schema uses `work_arrangement` instead of `remote`. Brief subagents receiving Schema B JSON will not find a `remote` field.

**Variable count confirmed:** The JSON blob has 13 keys but the plan says "confirm 12 variables parsed." The plan's note rationalizes this as intentional, but it is a bug — the validation count must match reality.

---

### Required Changes

- [ ] **RC-1: Fix variable count from "12" to "13".** The JSON blob in Change 3 has 13 keys (`role_type` through `exclude_titles`). The instruction "confirm 12 variables parsed" will cause the subagent to either count 13 and be confused, or silently ignore the check. Change to "confirm 13 variables parsed." Update all references: line 157 ("12 variables parsed"), line 161 ("ALL 12 template variables"), and Task 10 check #12 (`grep "12 variables parsed"` → `grep "13 variables parsed"`). Delete the historical note about "originally 12" — it serves no purpose for the executing agent.

- [ ] **RC-2: Fix `--html --file` email interaction.** `send_email.py` line 70: `params["html"] = markdown_to_html(body)`. When `--html` and `--file` are both set, the file content is run through `markdown_to_html()`. The digest template (Task 6, step 5) writes raw HTML to `_email-body.html` and passes `--html --file` — this will double-convert the HTML. **Fix:** Change the temp file to markdown format (`_email-body.md`), write the email body as markdown (not HTML), and let `send_email.py` handle the HTML conversion. This aligns with the script's design without requiring Python changes.

- [ ] **RC-3: Update `subagent-brief.md` to use `work_arrangement` instead of `remote`.** Task 5 says "copy and update two path references" but the template at line 51 contains `Remote: {remote}`. The V12 canonical schema uses `work_arrangement`. Change to `Arrangement: {work_arrangement}`. Without this fix, brief subagents receiving Schema B JSON will not find a `remote` field and will either fabricate a value or leave it blank.

### Recommended Changes

- [ ] **REC-1: Define parent behavior for `_status.json` error states.** Add to steps 13-14: "Read `status` field first. If `failed` → notify user with the error message. If `partial` → check which fields succeeded, notify user. If `complete` → verify specific fields." Currently the parent only checks for success fields.

- [ ] **REC-2: Standardize directory scan skip pattern.** Multiple subagents scan directories and "skip `_status.json` files." But the briefs-PDF status is named `_briefs-pdf-status.json`. Change the skip pattern to "skip files starting with `_`" (prefix pattern) rather than exact filename matching. This handles all status/metadata files consistently.

- [ ] **REC-3: Add explicit "score MUST be a top-level integer" note to search-verify schema.** V11's growth-marketing-associate subagent produced `"score": { "total": 81, ... }` (nested object). The V12 schema shows `"score": 75` (integer) but does not explicitly prohibit the nested pattern. One line prevents drift.

- [ ] **REC-4: Consolidate verification — pick inline OR final, not both.** Task 3 ends with 14 grep checks. Task 10 re-checks many of the same strings. Recommend: keep Task 10 as the single verification pass, remove inline greps from Task 3. Or vice versa.

- [ ] **REC-5: Preserve digest markdown source on PDF failure.** Task 6 step 6 deletes `{run_date}.md` before the status file is written. If PDF generation produced a corrupt file, the source is already gone. Change cleanup to: "Delete intermediates ONLY IF `_status.json` shows `pdf_generated: true`."

- [ ] **REC-6: Specify subagent behavior when variable validation fails.** Change 3 says subagents should "confirm 13 variables parsed" but does not say what to do if validation fails. Add: "If any variable is missing, write `_status.json` with `status: failed` and exit. Do NOT proceed with partial variables."

### Approval Status

**Needs 3 Changes** — RC-1 (variable count bug), RC-2 (email body format), and RC-3 (brief template `remote` → `work_arrangement`) must be fixed. All three are small, targeted fixes. 6 recommended changes would improve robustness but are not blocking.

---

## Round 1 - 2026-02-06
**Reviewers:** architecture-strategist, code-simplicity-reviewer, pattern-recognition-specialist

### Summary

The V12 plan is architecturally sound and correctly addresses all 8 V11 failures. The compact dispatch pattern is the highest-impact improvement. Three reviewers surfaced **6 required changes** and **9 recommended changes**. No architectural revision needed — all findings are refinements to the existing plan.

### Findings

#### Architecture Review

The parent-orchestrator / subagent-template pattern is maintained correctly. Compact dispatch reduces context consumption while improving separation of concerns. New subagent templates follow the established contract. Cross-role dedup is correctly placed between batch completion and presentation.

**Key concerns:**
- New subagent templates (digest, briefs-PDF) lack `_status.json` completion signals that the search-verify template has
- pdfkit/wkhtmltopdf dependency not validated in template pre-checks
- Steps 13-14 (digest + briefs-PDF) could run in parallel but plan doesn't state this
- Should add fallback for role types with zero results above 70 threshold

#### Simplicity Review

8 of 13 changes are clearly justified. Two areas are over-engineered:

1. **Freshness filter (changes 7 + 13):** Three-tier classification (`fresh`/`apply_soon`/`unknown`) built on unreliable data. Most jobs will be `"unknown"` since posted dates are rarely available. The >30 day skip is dangerous — silently drops jobs that could be reposted or have rolling deadlines.

2. **CONTEXT CONSERVATION section (change 9):** 5 rules where 4 restate things already specified in the orchestration steps. The concrete mechanisms (compact dispatch, subagent delegation) already achieve context conservation.

Additional: plan copies `create_briefs_pdf.py` "for completeness" despite being replaced — YAGNI violation. The plan itself is ~30% longer than needed.

#### Pattern Review

**Critical finding: Schema drift.** The verified JSON schema in the template differs from what subagents actually produce. Field names diverge (`url` vs `job_url`, `remote` vs `is_remote`, `discovered_at` vs `date_posted`). The V12 plan adds `posted_date` but actual output already uses `date_posted`.

**Inconsistent dispatch patterns.** Compact dispatch applied to search-verify, digest, and briefs-PDF — but NOT to brief dispatch (step 10). This means V12 will have mixed dispatch patterns.

**Template structure missing.** New templates (digest, briefs-PDF) don't specify standard structural sections: "Your Task", "Working directory", "First action", "Core Rules", "Completion Signal".

**Naming inconsistency.** `subagent-briefs-pdf.md` uses plural ("briefs") while `subagent-brief.md` uses singular.

**.gitignore gap.** V12 will generate PDFs in `output/briefs/` and `output/digests/` that aren't covered by the current `.gitignore`.

---

### Required Changes

- [x] **RC-1: Add `_status.json` to both new subagent templates.** Digest writes `output/digests/_status.json` (with `pdf_generated`, `email_sent`, `total_jobs_in_digest`). Briefs-PDF writes `output/briefs/_briefs-pdf-status.json` (with `pdf_generated`, `briefs_compiled`). Update parent steps 13-14 to read these instead of just checking file existence.

- [x] **RC-2: Add pdfkit/wkhtmltopdf pre-check to both new templates.** `which wkhtmltopdf` + `pip3 install pdfkit` check before any HTML→PDF conversion. Do not proceed without confirming both dependencies.

- [x] **RC-3: Use `date_posted` instead of `posted_date`.** Actual subagent output already uses `date_posted`. Align the plan and template schema to match reality.

- [x] **RC-4: Apply compact dispatch to brief subagents too.** Currently only search-verify, digest, and briefs-PDF use compact dispatch. Brief dispatch (step 10) still uses the old inline pattern — inconsistent and wastes parent context.

- [x] **RC-5: Add standard structural sections to new templates.** Both subagent-digest.md and subagent-briefs-pdf.md need: "Your Task", "Working directory / First action", "Core Rules", and "Completion Signal" sections to match existing template patterns.

- [x] **RC-6: Update `.gitignore` to exclude generated PDFs.** Add `output/briefs/*.pdf` and `output/digests/*.pdf`.

### Recommended Changes

- [x] **REC-1: Simplify freshness filter to one rule.** Drop 3-tier classification. Instead: "If `date_posted` is available and >30 days ago, deprioritize (present last with a note). Do not skip entirely." Drop `freshness_flag` field. Just store `date_posted` if available.

- [x] **REC-2: Cut CONTEXT CONSERVATION section.** Keep only rule 1 ("After presenting results, do NOT re-read verified files") as a single line in SESSION MANAGEMENT. The rest restates what compact dispatch and subagent steps already specify.

- [x] **REC-3: Don't copy `create_briefs_pdf.py` to V12.** It's explicitly replaced by subagent-briefs-pdf.md and contains hardcoded values from V11's first run. Dead code.

- [x] **REC-4: Simplify template-read HARD RULE wording.** Current is 4 lines saying the same thing 3 ways. Condense to: "Read `references/subagent-search-verify.md` in full BEFORE dispatching any subagents. Confirm you understand the workflow: jobspy first, then specialty sources, then filter, then summarize, then verify."

- [x] **REC-5: Note steps 13-14 can run in parallel.** Digest and briefs-PDF have no mutual dependency.

- [x] **REC-6: Add empty-results fallback for 70 threshold.** "If a role type has zero jobs above 70, present top 3 regardless of score with a note: 'No strong matches found. Here are the closest.'"

- [x] **REC-7: Add variable count validation to compact dispatch.** Subagent should confirm 12 variables parsed before executing.

- [x] **REC-8: Use file-based approach for email body.** Write HTML summary to temp file, pass via `--file` flag to `send_email.py` to avoid shell escaping issues.

- [x] **REC-9: Acknowledge verified JSON schema divergence.** Either update the template schema to match what subagents actually produce, or add a note that the schema is advisory.

### Approval Status

**Needs Changes** — 6 required changes must be addressed before implementation. 9 recommended changes are strongly suggested but not blocking.

---

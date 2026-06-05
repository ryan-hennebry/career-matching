# JSA V13 Reviews

## Round 11 - 2026-02-08 03:00
**Reviewers:** dhh-rails-reviewer, kieran-rails-reviewer, code-simplicity-reviewer

### Summary

Three reviewers conducted Round 11 review of the review-adjusted V13 plan (post Round 10 approval). **0 HIGH findings. 1 MEDIUM (downgraded to LOW on analysis). 3 INFO items.** All previous findings (Rounds 1-10) remain integrated. No regressions. Plan approved for build by all three reviewers independently.

### Findings — Consolidated

#### Low (2)

**K-R11-1 (MEDIUM→LOW): Per-run cleanup `rm -f output/verified/*/*` leaves empty subdirectories behind.**
The pre-run cleanup step (Task 3.2) uses `rm -f output/verified/*/*` which deletes files inside role-type subdirectories but leaves empty directories. If a new run has different role types than the prior run, stale empty directories persist. On analysis: functionally harmless — search-verify agent creates its own subdirectory regardless. `rm -f` handles the empty-directory case gracefully.
**No action needed.**
*Found by: kieran-rails-reviewer*

**K-R11-2 (LOW): `subagent_type` field name in Task tool calls should be verified at implementation time.**
Plan lines 531, 553, 578, 601 all use `subagent_type: "search-verify"` (and equivalent for other agents). If the actual Claude Code Task tool parameter is named differently (e.g., `agent`), all four dispatch calls silently fall back to general-purpose subagent — losing named agent constraints, preloaded skills, and startup instructions.
**Recommendation:** Implementor should verify the correct Task tool field name before Phase 2 build. 30-second check, not a plan revision.
*Found by: kieran-rails-reviewer*

#### Informational (3)

**K-R11-3 (INFO): `Skill` in `disallowedTools` for search-verify and brief-generator is belt-and-suspenders.** Neither agent has any skill preloaded. Harmless defensive measure.

**K-R11-4 (INFO): `send_email.py` mixes `pathlib` and `os.path`.** `Path(__file__).parent.parent / ".env"` alongside `os.path.exists()` and `os.path.basename()`. Style inconsistency in a 75-line script. Not worth changing.

**DHH-R11-1 (INFO): Email idempotency ceremony (Step 15, 35 lines) is over-engineered for a single-user CLI tool.** Previously noted in SIM-R9-3 (Round 9). Implementation is correct. "Did I get the email?" is trivially observable. Accepted as design choice.

### Cross-Reviewer Agreement

| Topic | DHH | Kieran | Simplicity |
|-------|-----|--------|------------|
| Plan ready for build | **YES** | **YES** | **YES** |
| Cleanup leaves empty dirs | — | **LOW** (R11-1) | — |
| `subagent_type` field name | — | **LOW** (R11-2) | — |
| Email idempotency over-engineering | **INFO** (R11-1) | — | Design choice |

### Plan-to-Output Metrics (Simplicity)

| Metric | Value |
|--------|-------|
| Plan-to-output ratio | 1.7:1 (acceptable) |
| YAGNI violations | 2 trivial (`memory: project`, `model: inherit` — single YAML keys) |
| Unnecessary abstractions | 0 |
| Phase 5 verification | Right-sized (8 targeted checks) |
| Complexity score | Low |

### All Previous Findings — Verified Integrated

All 10 rounds of findings (Rounds 1-10) remain integrated. No regressions. Key confirmations:
- Variable counts: 13/7/4/1 consistent across all three layers
- Status file paths: `_status.json` everywhere, no remnants
- Sentinel mechanism: defined in producer (Task 2.4), verified in consumer (Step 11), grep-checked (Task 5.1)
- Idempotency: `sent_at` + `run_date` comparison (DI-9 fix verified correct)
- Design system: single source of truth via skill, no duplication
- All agent-to-template naming consistent
- Producer-consumer contracts verified across all 4 agent types
- Per-run cleanup: conditioned on `session-state.md` existence/date (DI-R10-1)
- Three-way briefs-pdf gate: success/failed/never-dispatched (ARCH-R10-1)
- `match_reason` eliminated, `total_verified` dropped
- Stale files deleted in Task 1.2 (templates.md, sources.md, subagent-digest.md)

### Required Changes
None. No blocking issues.

### Approval Status

**APPROVED for build.** 0 HIGH findings. No blocking issues. All previous findings (Rounds 1-10) verified integrated. Architecture sound, contracts complete, variable counts match, naming consistent, edge cases handled.

DHH summary: "Stop reviewing. Start building."
Kieran summary: "The plan is ready for build."
Simplicity summary: "Proceed with build as-is."

**Ready for `/build`.**

---

## Round 10 - 2026-02-08 01:30
**Reviewers:** architecture-strategist, code-simplicity-reviewer, data-integrity-guardian

### Summary

Three reviewers conducted Round 10 review of the review-adjusted V13 plan (post Round 9 integration). **0 HIGH findings. 2 MEDIUM items. 4 LOW/INFO items.** All previous findings (Rounds 1-9) remain integrated. No regressions. DI-9 fix (stale `run_date`) verified correct by all three reviewers. Cross-file consistency verified — variable counts 13/7/4/1 match, status paths consistent, producer-consumer contracts aligned.

Both MEDIUM findings affect edge cases (zero-briefs scenario, multi-run contamination) rather than the happy path. Neither blocks the build.

### Findings — Consolidated

#### Recommended (2)

**ARCH-R10-1 (MEDIUM): Step 15 gate logic does not distinguish "briefs-pdf failed" from "briefs-pdf was never dispatched (zero briefs)."**
Step 14 (line 573) is conditional: "If any briefs generated." When the user rejects all jobs, Step 14 is never dispatched and `output/briefs/_status.json` is never written. Step 15 gate logic (line 599) says "If briefs-pdf failed but digest succeeded, notify user" — but a missing status file from a skipped Step 14 could be misinterpreted as a failure (matching the hang detection pattern used elsewhere). Line 611 handles the output side correctly ("If no briefs PDF...omit `--attachment` flag"), but the gate logic at 599 creates ambiguity.
**Fix:** Add to Step 15: "If Step 14 was skipped (zero briefs generated), proceed directly to email send without attachment — do not treat missing `output/briefs/_status.json` as a failure."
*Found by: architecture-strategist*

**DI-R10-1 (MEDIUM): Stale output files from prior runs persist and contaminate new runs — briefs PDF compiles briefs from ALL prior runs.**
Task 1.1 cleans output during the initial V12-to-V13 copy, but this is a one-time build step, not a per-run cleanup. On the second run of V13, `output/briefs/` still contains first-run brief `.md` files. The briefs-pdf agent discovers ALL `.md` files (Task 2.3, line 352), so Tuesday's PDF includes Monday's briefs. DIG-R7-3 (Round 7) flagged stale verified file counts as INFO/cosmetic, but the brief contamination of the PDF is functionally impactful.
**Fix:** Add cleanup step to CLAUDE.md ORCHESTRATION WORKFLOW before Step 1: clean `output/jobs/*`, `output/verified/*`, `output/briefs/*`, `output/digests/*` when starting a new run (not when resuming). Condition: only clean if `session-state.md` does not exist or its `run_date` differs from today.
*Found by: data-integrity-guardian*

#### Nice-to-Have (1)

**SIM-R10-1 (MEDIUM→LOW): `--attachment action="append"` in `send_email.py` builds multi-attachment list machinery for a single-attachment tool.**
ARCH-R9-1 (INFO) noted this in Round 9. The `action="append"` with `default=[]` creates a list, then iterates and base64-encodes each file. For zero or one attachments, a simple optional string is sufficient. ~4 lines of YAGNI.
**Fix (optional):** Change `--attachment` from `action="append", default=[]` to simple optional `default=None`. Replace loop with single-file encode.
*Found by: code-simplicity-reviewer*

#### Informational (3)

**ARCH-R10-2 (LOW): Asymmetric stale-data protection between digest and briefs status files.** Digest `_status.json` has `run_date` comparison (DI-9 fix); briefs `_status.json` has no equivalent guard. Latent debt — no immediate impact since Step 14 is conditional and its status file is overwritten each run.

**SIM-R10-2 (INFO): Step 15 idempotency ceremony is more than the risk warrants for a single-user CLI tool.** Already addressed by SIM-R9-3. Current implementation is clean and correct. Noted for completeness.

**SIM-R10-3 (INFO): `model: inherit` in all 4 agent definitions specifies the default behavior.** Added per DHH-R5-4 recommendation. Harmless documentation-as-code.

### Cross-Reviewer Agreement

| Topic | Architecture | Simplicity | Data Integrity |
|-------|-------------|------------|----------------|
| Step 15 zero-briefs ambiguity | **MEDIUM** (R10-1) | — | — |
| Stale output across runs | — | — | **MEDIUM** (R10-1) |
| Multi-attachment YAGNI | — | **LOW** (R10-1) | — |
| Asymmetric status protection | **LOW** (R10-2) | — | — |

### DI-9 Fix — Verified Correct

All three reviewers independently verified the DI-9 fix at plan line 598. The `sent_at` + `run_date` two-predicate guard correctly handles:
- Same-run re-send attempt: `sent_at` present + `run_date` matches = SKIP (prevents duplicate)
- New-day run: `sent_at` present + `run_date` differs = proceed (stale status ignored)
- Crashed mid-send: `sent_at` absent = proceed (retries send)

The write-ahead `send_requested` pattern was correctly replaced with post-send `sent_at`-only, which is both simpler and correct.

### All Previous Findings — Verified Integrated

All 9 rounds of findings (Rounds 1-9) remain integrated. No regressions. Key confirmations:
- Variable counts: 13/7/4/1 consistent across all three layers
- Status file paths: `_status.json` everywhere, no remnants
- Sentinel mechanism: defined in producer (Task 2.4), verified in consumer (Step 11), grep-checked (Task 5.1)
- Idempotency: `sent_at` + `run_date` comparison (DI-9 fix verified correct)
- Design system: single source of truth via skill, no duplication
- All agent-to-template naming consistent
- Producer-consumer contracts verified across all 4 agent types
- `match_reason` eliminated, `total_verified` dropped
- Stale files (templates.md, sources.md) deleted in Task 1.2

### Required Changes
None. No blocking issues.

### Recommended Changes
- [x] ARCH-R10-1: Add three-way discriminator to Step 15 for briefs-pdf status (success/failed/not dispatched)
- [x] DI-R10-1: Add output directory cleanup for new runs to CLAUDE.md ORCHESTRATION WORKFLOW

### Nice-to-Have Changes
- [x] SIM-R10-1: Simplify `--attachment` from list to optional string

### Approval Status

**APPROVED for build.** No HIGH findings. No blocking issues. All previous findings (Rounds 1-9) verified integrated. DI-9 fix verified correct by all three reviewers. Architecture sound, contracts defined, variable counts match, paths consistent.

Both MEDIUM findings affect edge cases (zero-briefs gate logic, multi-run output contamination) rather than the happy path. They can be addressed during build with minimal plan changes — a 2-sentence addition to Step 15 (ARCH-R10-1) and a cleanup step in CLAUDE.md (DI-R10-1).

**Ready for `/build`.**

---

## Round 9 - 2026-02-07 22:00
**Reviewers:** architecture-strategist, code-simplicity-reviewer, data-integrity-guardian

### Summary

Three reviewers conducted Round 9 review of the review-adjusted V13 plan (post Round 8 integration). **1 HIGH finding (DI-9: stale run_date blocks future runs). 4 MEDIUM items. 6 LOW/INFO items.** All previous findings (Rounds 1-8) remain integrated. Cross-file consistency verified across all 5 layers — variable counts 13/7/4/1 match, status paths consistent, producer-consumer contracts aligned.

The HIGH finding is a real multi-day usage bug: the `send_requested` idempotency check doesn't compare `run_date`, so a previous day's completed status permanently blocks email sending on all future runs.

### Findings — Consolidated

#### Must-Fix (1)

**DI-9 (HIGH): No `run_date` validation in `send_requested` idempotency check — stale status blocks future runs.**
Step 15 (plan line 584) checks `send_requested: true` in `output/digests/_status.json` without comparing the file's `run_date` against the current session's `run_date`. In multi-day usage (the intended use case), the first run's status persists with `send_requested: true` and blocks all subsequent runs. User sees "Email already sent for this run" on every future run — even for different dates with different results. Same issue applies to `output/briefs/_status.json`.
**Fix:** Change the idempotency guard to: "If `send_requested: true` AND `run_date` matches current session's `run_date`, SKIP. If `run_date` differs, treat as stale (previous run) and proceed."
*Found by: data-integrity-guardian*

#### Recommended (4)

**DI-13 (MEDIUM): Unrewritten V12 CLAUDE.md Step 3 contradicts named-agent architecture.**
V12 CLAUDE.md Step 3 (line 87) says "Read `references/subagent-search-verify.md` in full BEFORE dispatching any subagents." In V13, named agents read their own templates on startup — the parent no longer needs to read them. Task 3.2 rewrites Steps 5, 11, 13-16 but does NOT touch Step 3. The unrewritten instruction wastes parent context window (the primary motivation for named agents) and creates confusion about who reads the template.
**Fix:** Rewrite Step 3 to remove the template-reading instruction, or replace with: "Named agents read their own templates on startup. Parent only needs to read `references/context.md` for user profile data."
*Found by: data-integrity-guardian*

**DI-16 (MEDIUM): Phase 5 verification doesn't grep for old `_briefs-pdf-status.json` filename.**
The 4 cross-file checks (plan lines 785-798) catch `v12` path remnants and `match_reason` but not the renamed status filename. If any V12 CLAUDE.md section referencing `_briefs-pdf-status.json` survives the Phase 3 rewrites, it creates a consumer-producer mismatch that would only surface at runtime.
**Fix:** Add a 5th check: `grep -r "_briefs-pdf-status" 03_agents/tests/v13/ --include="*.md" --include="*.json"  # expect: no output`
*Found by: data-integrity-guardian*

**F-1 (MEDIUM): Post-send `_status.json` update shows bare JSON snippet without explicit merge instruction.**
Plan line 589 (pre-send) correctly says "Read existing...add `send_requested: true`...write back" — merge intent is clear. But plan lines 601-605 (post-send) show `{"sent_at": "...", "to": "..."}` as a JSON snippet, which an implementor clearing context between phases could read as "write only these two fields" — destroying the original subagent-written fields.
**Fix:** Change lines 601-605 to explicitly say: "Read existing `output/digests/_status.json`, add `sent_at` and `to` fields to the existing object, write back."
*Found by: architecture-strategist*

**SIM-R9-3 (MEDIUM): Step 15 write-ahead idempotency is over-engineered for single-user CLI.**
The `send_requested` → send → `sent_at` pattern is a distributed-systems write-ahead log applied to a tool one person runs manually. The false-positive recovery path ("delete a JSON field") contradicts the V12 CLAUDE.md Core Rule 5 ("NEVER ask user to do technical work"). For a personal tool, "did I get the email?" is trivially observable.
**Fix:** Accept as-is (already reviewed in DIG-R7-2) or simplify to: write `sent_at` after successful send only. No pre-send guard.
*Found by: code-simplicity-reviewer*

#### Nice-to-Have (2)

**SIM-R9-2 (LOW): Error-handling protocol repeated 4 times in agent definitions.**
All 4 agent definitions specify: "Parse JSON blob, confirm N variables present, if missing → write _status.json with error → exit." This is defined 4 times with minor variations. Could be defined once in templates with agent definitions reduced to 5 lines each (frontmatter + "Read instructions from references/subagent-{name}.md").
**Fix (optional):** Move error-handling to templates. Reduces agent definitions to ~5 lines each, saving ~40 lines.
*Found by: code-simplicity-reviewer*

**SIM-R9-5 (LOW): `memory: project` on ephemeral workers with no learning loop.**
All 4 agent definitions set `memory: project` but neither the reference templates nor CLAUDE.md define any memory-based behavior (reading/acting on accumulated memory). Search-verify and brief-generator are ephemeral workers that don't adapt between runs.
**Fix (optional):** Remove `memory: project` from search-verify and brief-generator, or define the learning loop.
*Found by: code-simplicity-reviewer*

#### Informational (4)

**DI-7 (INFO): Brief sentinel whitespace tolerance not specified.** "Last non-whitespace line must be exactly `<!-- BRIEF COMPLETE -->`" — the word "exactly" could reject a line with leading/trailing spaces. Low risk (Claude writes exact strings).

**SIM-R9-1 (INFO): Digest-email template "Do not rely on a pre-counted variable" instruction is vestigial.** `total_verified` no longer exists as a variable. The instruction warns against a ghost. Harmless.

**F-2 (INFO): Briefs-PDF filename fallback can't reliably split `{company_slug}-{title_slug}` since both use hyphens.** Best-effort fallback for a rare edge case (H1 unparseable). Cosmetic only.

**ARCH-R9-1 (INFO): `--attachment` uses `action="append"` (multi-value) but only one attachment is ever passed.** 4 extra lines of future-proofing. No functional impact.

### Cross-Reviewer Agreement

| Topic | Architecture | Simplicity | Data Integrity |
|-------|-------------|------------|----------------|
| Stale run_date blocks future runs | — | — | **HIGH** (DI-9) |
| Unrewritten Step 3 | — | — | **MEDIUM** (DI-13) |
| Missing _briefs-pdf-status grep | — | — | **MEDIUM** (DI-16) |
| Post-send merge ambiguity | **MEDIUM** (F-1) | — | **MEDIUM** (DI-1) |
| Write-ahead idempotency YAGNI | — | **MEDIUM** (R9-3) | — |
| Error-handling 4x repetition | — | **LOW** (R9-2) | — |
| memory:project on ephemeral agents | — | **LOW** (R9-5) | — |

### All Previous Findings — Verified Integrated

All 8 rounds of findings (Rounds 1-8) remain integrated. No regressions. Key confirmations from all three reviewers:
- Variable counts: 13/7/4/1 consistent across all three layers
- Status file paths: `_status.json` everywhere, no `_briefs-pdf-status.json` remnants in plan
- Sentinel mechanism: defined in producer (Task 2.4), verified in consumer (Step 11), grep-checked (Task 5.1)
- Idempotency: `send_requested: true` written BEFORE send (DIG-R7-2 fix)
- Design system: single source of truth via skill, no duplication
- All agent-to-template naming consistent
- Producer-consumer contracts verified across all 4 agent types
- `match_reason` eliminated, replaced with `requirements_met` + `score_breakdown` synthesis
- `total_verified` dropped, agent counts files itself

### Required Changes
- [ ] DI-9: Add `run_date` comparison to `send_requested` idempotency guard

### Recommended Changes
- [ ] DI-13: Rewrite Step 3 to remove parent template-reading instruction
- [ ] DI-16: Add `_briefs-pdf-status` grep to Phase 5 verification
- [ ] F-1: Make post-send `_status.json` merge instruction explicit
- [ ] SIM-R9-3: Simplify write-ahead idempotency or accept as-is

### Nice-to-Have Changes
- [ ] SIM-R9-2: Move error-handling from agent definitions to templates
- [ ] SIM-R9-5: Remove `memory: project` from ephemeral workers

### Approval Status

**Needs Changes** — 1 HIGH must-fix item (DI-9). The stale `run_date` blocking future runs is a real multi-day usage bug that would surface on the second-ever run. Trivially fixable by adding `run_date` comparison to the idempotency guard. All other findings are MEDIUM or below.

After fixing DI-9, plan is ready for `/build`.

---

## Round 8 - 2026-02-07 18:30
**Reviewers:** dhh-rails-reviewer, kieran-rails-reviewer, code-simplicity-reviewer

### Summary

Three reviewers conducted Round 8 review of the review-adjusted V13 plan (post Round 7 integration). **No HIGH findings. 0 blocking issues.** All previous findings (Rounds 1-7) remain integrated. DHH and Kieran independently found the same MEDIUM issue — `references/templates.md` survives the V12 copy but is never deleted. Simplicity reviewer confirmed diminishing returns: only 4 lines of potential LOC reduction found. Plan-to-output ratio is 1.6:1, which is reasonable.

### Findings — Consolidated

#### Recommended (1)

**R8-1 (MEDIUM): `references/templates.md` survives V12 copy but is never deleted.**
Task 1.1 copies all of V12 to V13. Task 1.2 deletes `subagent-digest.md`. But `templates.md` — confirmed to have zero consumers across 7 rounds (S-1 Round 2) — is never removed. It sits in V13 with stale V12 content: `wkhtmltopdf`, `pdfkit`, `{job_id}` placeholders, old design specs. Seven rounds checked "nothing references it" but nobody checked "the file still exists."
**Fix:** Add `rm 03_agents/tests/v13/references/templates.md` to Task 1.2.
*Found independently by: dhh-rails-reviewer, kieran-rails-reviewer*

#### Nice-to-Have (4)

**R8-2 (LOW): `references/sources.md` may be dead weight.**
Copied from V12, never mentioned in any V13 agent definition or CLAUDE.md step. Not referenced by any V13 template. Harmless but adds confusion.
**Fix:** Verify consumers. If none, add to Task 1.2 deletion list.

**YAGNI-R8-1 (LOW): 25MB attachment size warning in `send_email.py` will never fire.**
A 3-5 brief PDF will never approach 25MB. The 2-line size check (Task 4.1, lines 747-748) is dead code.
**Fix:** Remove the size check, or accept as harmless defensive code.

**YAGNI-R8-2 (LOW): HTML content sniff in `send_email.py` adds no value.**
The `<table`/`<html` check (Task 4.1, lines 728-729) prints a stderr warning nobody reads. If digest-email failed, `_status.json` already catches it. If it succeeded, the HTML is valid.
**Fix:** Remove the 2-line check, or accept as harmless.

**R8-3 (LOW): `algorithms.md` is an implicit dependency of search-verify.**
Still referenced by `subagent-search-verify.md` (lines 78, 90). Correctly retained via Task 1.1 copy. Not documented as a dependency anywhere.
**Fix (optional):** No action for V13. Note as implicit dependency for future versions.

#### Informational (1)

**SIM-R8-1 (INFO): Review-finding traceability tags remain throughout the plan.**
Lines like "Review findings addressed: A-1, RC5..." at start of each phase. SIM-R5-1 flagged this in Round 5. Resolution was "add implementor note to ignore" (line 11). Not worth removing.

### Cross-Reviewer Agreement

| Topic | DHH | Kieran | Simplicity |
|-------|-----|--------|------------|
| Stale templates.md survives copy | **MEDIUM** (R8-1) | **MEDIUM** (R8-1) | — |
| Dead sources.md | **LOW** (R8-2) | — | — |
| send_email.py size check YAGNI | — | — | **LOW** (R8-1) |
| send_email.py HTML sniff YAGNI | — | — | **LOW** (R8-2) |

### All Previous Findings — Verified Integrated

All 7 rounds of findings (Rounds 1-7) remain integrated. No regressions. Key confirmations from all three reviewers:
- Variable counts: 13/7/4/1 consistent across all three layers
- Status file paths: `_status.json` everywhere, no remnants
- Sentinel mechanism: defined in producer (Task 2.4), verified in consumer (Step 11), grep-checked (Task 5.1)
- Idempotency: `send_requested: true` written BEFORE send (DIG-R7-2 fix)
- Design system: single source of truth via skill, no duplication
- All agent-to-template naming consistent
- Producer-consumer contracts verified across all 4 agent types

### Required Changes
None. No blocking issues.

### Recommended Changes
- [x] R8-1: Add `rm 03_agents/tests/v13/references/templates.md` to Task 1.2

### Nice-to-Have Changes
- [x] R8-2: Verify `sources.md` has consumers; delete if dead (confirmed zero consumers — added to Task 1.2)
- [x] YAGNI-R8-1: Remove 25MB size check from send_email.py (2 lines)
- [x] YAGNI-R8-2: Remove HTML content sniff from send_email.py (2 lines)

### Approval Status

**APPROVED for build.** No HIGH findings. No blocking issues. All previous findings (Rounds 1-8) verified integrated. Architecture sound, contracts defined, variable counts match, paths consistent. Cross-file consistency verified across all 5 layers.

All Round 8 findings integrated: R8-1 and R8-2 added to Task 1.2 deletion list; YAGNI-R8-1 and YAGNI-R8-2 removed from send_email.py in Task 4.1.

**Ready for `/build`.**

---

## Round 7 - 2026-02-07 16:00
**Reviewers:** architecture-strategist, code-simplicity-reviewer, data-integrity-guardian

### Summary

Three reviewers conducted Round 7 review of the review-adjusted V13 plan (post Round 6 integration). **No HIGH findings. 0 blocking issues.** All previous findings (Rounds 1-6) remain integrated. The architecture is confirmed sound — cross-file consistency verified across all 5 layers (agent definitions, reference templates, CLAUDE.md, OUTPUTS, send_email.py). Variable counts 13/7/4/1 match everywhere.

Reviewers found 1 MEDIUM simplification, 3 MEDIUM edge-case hardening items, 4 LOW items, and 4 INFO observations. None affect correctness of the happy path. The plan has been approved for build in Rounds 5, 6, and now 7. Diminishing returns are evident — Round 7 found no architectural gaps that prior rounds missed.

### Findings — Consolidated

#### Recommended (4)

**SIM-R7-1 (MEDIUM): Agent definition "BANNED (belt-and-suspenders)" blocks are redundant prose.**
Both `digest-email.md` and `briefs-pdf.md` contain multi-line BANNED paragraphs listing 5 forbidden tools by name, then noting `settings.local.json` is the real enforcement. The design system skill already says "Playwright + Chromium ONLY. No fpdf2, reportlab, pdfkit, wkhtmltopdf, WeasyPrint." Two enforcement layers (skill instruction + settings) are sufficient; three (+ prose ban) is belt-and-suspenders-and-a-second-pair-of-suspenders.
**Fix:** Delete BANNED blocks from both agent definitions. ~6 lines saved.

**DIG-R7-2 (MEDIUM): Read-modify-write of `_status.json` after email send is not atomic.**
If parent crashes between `send_email.py` completing and `_status.json` being rewritten with `send_requested: true`, the idempotency guard is lost. On resume, email gets sent again. This is the exact scenario E-1 was designed to prevent.
**Fix (optional):** Write `send_requested: true` BEFORE calling `send_email.py`. Then update `sent_at`/`to` after success. False-positive (marked but never sent) is preferable to false-negative (sent but not marked, causing duplicate). Or accept the narrow crash window as tolerable for a personal tool.

**DIG-R7-7 (MEDIUM): Briefs-pdf agent has no defined behavior for valid-sentinel-but-malformed-H1 briefs.**
Sentinel check passes but H1 line is missing or unparseable. The fallback "attempt to parse by stripping" is vague — no guidance on what to do if parsing fails entirely. Skip? Fail? Placeholder?
**Fix:** Add to Task 2.3 Step 1: "If H1 cannot be parsed after fallback attempt, use filename-derived title (extract from `{company_slug}-{title_slug}-brief.md`) and log a warning. Do not skip the brief."

**ARCH-R7-2 (LOW→MEDIUM): Duplicate rename instruction in Task 1.5 and Task 2.4.**
Task 1.5 renames `subagent-brief.md` → `subagent-brief-generator.md`. Task 2.4 repeats the same rename. Since phases execute sequentially with context clears, Phase 2 builder will attempt to rename an already-renamed file — either no-op or error.
**Fix:** Remove rename from Task 2.4. Replace with: "File: `subagent-brief-generator.md` (renamed in Phase 1)."

#### Nice-to-Have (4)

**ARCH-R7-11 (LOW): `load_dotenv()` does not strip quotes from `.env` values.**
If `.env` contains `RESEND_API_KEY="re_abc123"`, the value includes surrounding quotes, causing API auth failure. Agent writes the `.env` file itself (controls format), so mitigated — but fragile if user pastes a quoted value.
**Fix:** Add `value = value.strip().strip('"').strip("'")` or add comment noting unquoted assumption.

**SIM-R7-3 (LOW): Step 13 "Status enum" explanatory paragraph is design rationale, not implementation instruction.**
The CLAUDE.md shouldn't explain why digest-email uses two values vs search-verify's three. The template already defines only `complete`/`failed`.
**Fix:** Delete the paragraph from Task 3.2. Behavior is fully specified by the template's Completion Signal.

**SIM-R7-4 (LOW): Step 15 pre-send corrupt-JSON checks duplicate Steps 13/14.**
Steps 13 and 14 already validate their respective status files (including corrupt JSON handling, hang detection). Step 15 re-reads and re-validates the same files.
**Fix:** Simplify Step 15 to: "Gate on Steps 13 and 14 having passed. Check `send_requested` for idempotency. If briefs-pdf failed but digest succeeded, notify user."

**DIG-R7-3 (LOW): No exclusion rule for stale verified files from prior partial runs.**
Digest-email agent counts all files in `output/verified/*/` indiscriminately. On crash-recovery resume, stale files could inflate the count. Cosmetic only — no downstream logic depends on the count.
**Fix:** Add note to digest-email template: "All files assumed from current run."

#### Informational (4)

**SIM-R7-5 (INFO): Plan is 820 lines. Reviews file is 585 lines. Combined review overhead is 72% of the plan. Diminishing returns evident.**

**SIM-R7-6 (INFO): Task 1.5 path update uses line-number references.** Files are small — "find and replace all `v12` with `v13`" is clearer.

**DIG-R7-5 (INFO): Two-writer lifecycle for digest `_status.json` only documented in OUTPUTS section.** Optional: add note to digest-email template about parent mutation.

**DIG-R7-6 (INFO): No cross-agent `run_date` consistency validation.** Design is correct (captured once at session start). Noting for completeness.

### Cross-Reviewer Agreement

| Topic | Architecture | Simplicity | Data Integrity |
|-------|-------------|------------|----------------|
| BANNED prose redundancy | — | **MEDIUM** (R7-1) | — |
| Email send atomicity | — | — | **MEDIUM** (R7-2) |
| Malformed H1 fallback | — | — | **MEDIUM** (R7-7) |
| Duplicate rename instruction | **LOW** (R7-2) | — | — |
| load_dotenv quote handling | **LOW** (R7-11) | — | — |
| Step 15 redundant validation | — | **LOW** (R7-4) | — |

### All Previous Findings — Verified Integrated

All 6 rounds of findings (Rounds 1-6) remain integrated. No regressions. Key confirmations:
- Variable counts: 13/7/4/1 consistent across all three layers
- Status schemas defined on both producer and consumer sides
- File paths consistent (`_status.json` everywhere)
- All stale-doc content inlined per Round 5
- All Round 6 recommendations integrated (headless, corrupt JSON, sentinel position, merged status, simplified failure menu, score 80-89)
- Sentinel, hang detection, idempotency guard all present
- Agent-to-template naming convention: all 4 agents match `{name}` → `subagent-{name}.md`

### Required Changes
None. No blocking issues.

### Recommended Changes
- [x] SIM-R7-1: Delete BANNED blocks from digest-email and briefs-pdf agent definitions
- [x] DIG-R7-2: Write `send_requested: true` before email send (or accept crash-window risk)
- [x] DIG-R7-7: Add filename-derived fallback for malformed H1 in briefs-pdf
- [x] ARCH-R7-2: Remove duplicate rename from Task 2.4

### Nice-to-Have Changes
- [x] ARCH-R7-11: Add quote-stripping to load_dotenv
- [x] SIM-R7-3: Delete Status enum paragraph from Step 13
- [x] SIM-R7-4: Simplify Step 15 pre-send checks (addressed by DIG-R7-2 rewrite)
- [x] DIG-R7-3: Add stale verified files assumption note

### Approval Status

**APPROVED for build.** No HIGH findings. No blocking issues. All previous findings (Rounds 1-7) verified integrated. Architecture sound, contracts defined, variable counts match, paths consistent. Cross-file consistency verified across all 5 layers.

All 4 recommended changes and all 4 nice-to-have changes integrated into the plan.

**Ready for `/build`.**

---

## Round 6 - 2026-02-07 17:00
**Reviewers:** architecture-strategist, code-simplicity-reviewer, data-integrity-guardian

### Summary

Three reviewers conducted Round 6 review of the review-adjusted V13 plan (post Round 5 approval). **No HIGH findings. 0 blocking issues.** All previous findings (Rounds 1-5) remain integrated. The architecture is confirmed sound. Reviewers found 4 MEDIUM edge-case hardening items, 3 MEDIUM simplification opportunities, and 4 LOW/INFO items. None affect correctness of the current plan — they improve robustness against edge cases (corrupt JSON, truncated writes, large PDFs) and reduce minor redundancies.

### Findings — Consolidated

#### Recommended (7)

**ARCH-R6-1 (MEDIUM): Playwright `headless: true` not specified in briefs-pdf template.**
Task 2.3 JavaScript snippet shows `chromium.launch()` without headless flag. Default varies across Playwright versions. On macOS, a headed launch during a background subagent steals window focus.
**Fix:** Change to `chromium.launch({ headless: true })` in Task 2.3 template. One-word addition.

**DIG-R6-1 (MEDIUM): Corrupt JSON in status files has no error handling.**
All status files are written via direct `Write` tool or `open()`. If a process crashes mid-write, partial JSON exists on disk. Parent reads it, gets a parse error. Plan only handles missing files (hang detection) and valid-but-failed status — not malformed JSON.
**Fix:** Add one line to each status file read instruction in CLAUDE.md: "If status file exists but cannot be parsed as valid JSON, treat as failed (corrupted write)."

**DIG-R6-4 (MEDIUM): Brief sentinel checked by existence, not position.**
Step 11 says "File must contain `<!-- BRIEF COMPLETE -->` sentinel at end" but the check is a grep/contains, not a last-line check. If agent writes sentinel midway then crashes, contains check passes but brief is truncated.
**Fix:** Change Step 11 verification from "file contains sentinel" to "file's last non-whitespace line must be `<!-- BRIEF COMPLETE -->`."

**SIM-R6-1 (MEDIUM): Dual status file approach (`_delivery-status.json`) is unjustified.**
Plan line 612 justifies separate `_delivery-status.json` by citing a race condition between parent and subagent. But by Step 15, the digest-email subagent is already complete (verified in Step 13). No race exists. Parent can safely append `email_sent` and `sent_at` to `output/digests/_status.json`.
**Fix:** Merge `_delivery-status.json` into `_status.json`. After email send, parent reads existing status, adds `email_sent: true` and `sent_at`, writes back. Eliminates 1 output file, ~8 lines of pre-send check logic, 1 OUTPUTS entry.

**SIM-R6-2 (MEDIUM): Three-option partial failure menu is over-engineered for a personal tool.**
Lines 586-590 pre-script a numbered menu for briefs-pdf failure. This is a Claude Code CLI agent — the user can type "send it anyway" or "retry" naturally. Claude already knows both operations.
**Fix:** Replace with: "If briefs-pdf failed but digest succeeded, notify user and ask how to proceed." Delete the numbered options.

**SIM-R6-4 (MEDIUM): Phase 5 verification is 65 lines verifying your own just-written code.**
Previously flagged (SIM-1 Round 4, SIM-R5-1 Round 5) but not resolved. One-shot verification suite for a one-shot implementation. Only 4 checks catch non-obvious cross-file bugs: v12 path grep, match_reason grep, BRIEF COMPLETE sentinel grep, Playwright version check.
**Fix:** Collapse Phase 5 to ~10 lines keeping those 4 high-value checks. Drop the rest (file existence, UTF-8 encoding, belt-and-suspenders text presence).

**ARCH-R6-4 (MEDIUM): Score accent color for 80-89 range undefined in design system skill.**
Task 1.3 defines colors for 90+ (green), 70-79 (amber), below salary min (red). The 80-89 range — common in real output — has no specified color. Visual agents will independently choose, reintroducing the inconsistency the design system exists to prevent.
**Fix:** Add one line to Task 1.3 skill: `- Default (80-89): #1a1a1a` (primary text color, no accent).

#### Nice-to-Have (4)

**DIG-R6-3 (LOW): `email_sent` field name implies delivery confirmation; reality is API acceptance.**
Resend's API confirms request acceptance, not delivery. `email_sent: true` is misleading. Low impact for a personal tool.
**Fix:** Rename to `send_requested: true` or add inline comment.

**DIG-R6-5 (LOW): `load_dotenv()` uses `setdefault` — existing env vars silently win.**
If a stale `RESEND_API_KEY` exists in shell env, `.env` value is ignored. Standard dotenv behavior but confusing to debug.
**Fix:** Add comment in script: `# Note: shell env vars take precedence over .env values`.

**ARCH-R6-2 (LOW): No HTML validation on `--body-file` input in `send_email.py`.**
If digest-email agent writes malformed HTML, email sends with broken rendering. Low priority — `_status.json` check partially mitigates.
**Fix (optional):** Add 2-line guard: if content lacks `<table` or `<html`, print stderr warning.

**ARCH-R6-3 (LOW): No max-size guard on base64-encoded PDF attachments.**
Resend has 40MB limit. Base64 inflates by ~33%. Unlikely to hit with 3-5 briefs, but possible with 15+.
**Fix (optional):** Add size check before base64 encoding — warn if >25MB.

#### Informational (2)

**SIM-R6-3 (INFO): "Saves ~60% parent context per dispatch" on line 501 is speculative.**
Nobody measured this. Real reason is architectural (named agents read own templates). Delete the percentage claim.

**ARCH-R6-6 (INFO): Design doc remains stale.**
Same as NEW-6 (Round 3). Plan inlined all content per Round 5 recommendations, so design doc is not a build dependency. Update after V13 build.

### Cross-Reviewer Agreement

| Topic | Architecture | Simplicity | Data Integrity |
|-------|-------------|------------|----------------|
| Playwright headless mode | **MEDIUM** (R6-1) | — | — |
| Corrupt JSON handling | — | — | **MEDIUM** (R6-1) |
| Sentinel position check | — | — | **MEDIUM** (R6-4) |
| Merge delivery status | — | **MEDIUM** (R6-1) | — |
| Simplify failure menu | — | **MEDIUM** (R6-2) | — |
| Phase 5 verification bloat | — | **MEDIUM** (R6-4) | — |
| Score color 80-89 gap | **MEDIUM** (R6-4) | — | — |
| PDF attachment size | **LOW** (R6-3) | — | **LOW** (R6-6) |

### All Previous Findings — Verified Integrated

All 5 rounds of findings (Rounds 1-5) remain integrated. No regressions detected. Key confirmations:
- Variable counts: 13/7/4/1 consistent across all three layers
- Status schemas defined on both producer and consumer sides
- File paths consistent (`_status.json` everywhere)
- All stale-doc content inlined per Round 5 recommendations
- Sentinel, hang detection, idempotency guard all present

### Required Changes
None. No blocking issues.

### Recommended Changes
- [ ] ARCH-R6-1: Add `{ headless: true }` to Playwright launch in Task 2.3
- [ ] DIG-R6-1: Add JSON parse error handling for status file reads (treat malformed as failed)
- [ ] DIG-R6-4: Check sentinel is last line, not just present
- [ ] SIM-R6-1: Merge `_delivery-status.json` into `_status.json`
- [ ] SIM-R6-2: Replace 3-option failure menu with natural language prompt
- [ ] ARCH-R6-4: Add score color for 80-89 range to design system skill

### Approval Status

**APPROVED for build.** No HIGH findings. No blocking issues. All previous findings (Rounds 1-5) verified integrated. Architecture sound, contracts defined, variable counts match, paths consistent.

The 7 recommended changes are edge-case hardening (corrupt JSON, sentinel position, headless mode, score color gap) and simplification (merge status files, simplify failure menu, trim Phase 5). None affect runtime correctness of the current plan. They can be addressed during build or deferred to V14.

**Ready for `/build`.**

---

## Round 5 - 2026-02-08 00:15
**Reviewers:** dhh-rails-reviewer, kieran-rails-reviewer, code-simplicity-reviewer

### Summary

Three reviewers conducted a final pre-build review of the review-adjusted V13 plan (post Round 4 integration). **No HIGH findings. 0 blocking issues.** All previous findings across 4 rounds are confirmed integrated. The architecture is sound, status JSON contracts are defined on both producer and consumer sides, variable counts match across all three layers, and file paths are consistent.

The remaining findings are quality-of-life items: the plan sends implementors to a stale design doc for base content (fragile cross-reference pattern), one redundant orchestration step, and two unused status JSON fields.

### Findings — Consolidated

#### Recommended (4)

**DHH-R5-1 (MEDIUM): Task 1.3 design system skill cross-references stale design doc by line numbers.**
Task 1.3 says "Read `jsa-v13-design.md` lines 105-119." The design doc is confirmed stale (NEW-6). Line numbers may have shifted. The design system skill is the single most important V13 file — its content should not depend on navigating a stale document.
**Fix:** Inline the complete skill file content in Task 1.3, or reference by section heading ("Design System Skill" section) instead of line numbers. The section is only ~15 lines of bullet points.

**DHH-R5-2 (MEDIUM): Task 2.2 digest-email template assembled from scattered fragments.**
Task 2.2 says "Read `jsa-v13-design.md` lines 121-167" for base content, then apply 4 separate patches (D-2, D-4, D-3b, footer conditional). The design doc section at lines 121-167 contains 5 stale references (`total_verified`, `match_reason`, unconditional footer, `_briefs-pdf-status.json`, 3-value status enum). The implementor must mentally merge a stale base with 4 overrides — the same scattered-source pattern that caused V12 failures.
**Fix:** Write the complete `subagent-digest-email.md` content inline in Task 2.2 (as Task 4.1 already does for `send_email.py` and Task 2.1 does for agent definitions). Or add explicit warning: "Design doc lines 121-167 contain 5 stale fields. Use ONLY for high-level content structure. All field names, variable counts, and status logic come from THIS task."

**K-R5-1 (MEDIUM): V12 briefs-pdf template has 5 stale references; Task 2.3 sends implementor there.**
Task 2.3 says "Read V12's `references/subagent-briefs-pdf.md` for structure." The V12 template contains 5 `_briefs-pdf-status.json` references and 3 `pdfkit`/`wkhtmltopdf` references — all banned in V13. Plan specifies the overrides but doesn't enumerate the stale references the implementor must find and replace.
**Fix:** Add note to Task 2.3: "V12 template contains 5 references to `_briefs-pdf-status.json` and 3 to `pdfkit`/`wkhtmltopdf`. All must be replaced." Or provide complete V13 template inline.

**SIM-R5-2 (MEDIUM): Step 15 is redundant with Steps 13, 14, and 16.**
Step 15 reads both status files and handles failures. But Steps 13 and 14 each already verify their own status files (including hang detection), and Step 16's pre-send checks gate on both status files again. Step 15 is a third redundant verification pass.
**Fix:** Delete Step 15. Renumber Step 16 → Step 15.

#### Nice-to-Have (7)

**SIM-R5-1 (MEDIUM): ~80 lines of review artifacts remain in the plan.**
Traceability table (lines 13-54), task mapping appendix (lines 829-845), and "Changes vs original plan" annotations are review artifacts. The implementor note (line 9) says to ignore them, but they're interspersed throughout tasks.
**Fix:** Strip before build, or accept builder will skip them.

**K-R5-4 (MEDIUM): Task 2.2 design doc lines 121-167 contain 5 stale fields.**
Same root cause as DHH-R5-2. The design doc's digest-email section references `total_verified`, `match_reason`, unconditional footer, `_briefs-pdf-status.json`, and 3-value status enum — all superseded by plan changes.
**Fix:** Covered by DHH-R5-2 fix. If inlining full template, this is resolved automatically.

**DHH-R5-3 (LOW): Task 2.3 briefs-pdf template has same cross-reference fragility.**
Same pattern as DHH-R5-2 but lower severity — V12 briefs-pdf template is simpler and changes are more straightforward.
**Fix:** Inline complete rewritten template, or accept builder reads V12 and applies patches.

**DHH-R5-4 (LOW): `model: inherit` silently dropped from all 4 agent definitions.**
Design doc specifies `model: inherit` in all agent YAML. Plan omits `model:` entirely. Claude Code likely defaults to parent model inheritance, but the design doc explicitly documented this as a decision.
**Fix:** Add `model: inherit` to match design doc, or add one-line note explaining the omission.

**SIM-R5-3 (LOW): Unused `total_jobs_in_digest` in digest-email status schema.**
No consumer reads this field. Step 13 only checks `status` and `html_generated`.
**Fix:** Remove from schema. Keep `status`, `html_generated`, `run_date`.

**SIM-R5-4 (LOW): Unused `briefs_compiled` in briefs-pdf status schema.**
Same pattern. No consumer reads this field.
**Fix:** Remove from schema. Keep `status`, `pdf_generated`, `run_date`.

**K-R5-2 (LOW): Digest-email template never specifies output HTML filename.**
The filename `{run_date}-email.html` is defined in Step 13 and OUTPUTS but not in the Task 2.2 template spec itself. Implementor must infer from other locations.
**Fix:** Add to Task 2.2: "Output file: `output/digests/{run_date}-email.html`"

#### Informational (3)

**DHH-R5-5 (INFO): V12 cleanup steps (intermediate file deletion) not addressed in V13.**
V12 templates had cleanup steps for intermediate `.md` and `.html` files. V13 templates don't mention cleanup. Leftover files are harmless.
**Fix:** Add note: "No cleanup step. Intermediate files retained for debugging." Or ignore.

**DHH-R5-7 (INFO): Design doc lists `send_alert.py` for deletion but file doesn't exist in V12.**
Non-issue — the file was never copied.

**K-R5-6 (LOW/INFO): Brief-generator hang detection not addressed by E-3.**
E-3 added hang detection for digest-email and briefs-pdf but not brief-generator. Low risk since individual brief failures are non-blocking.
**Fix (optional):** Add to Step 11: "If Task tool hangs for a brief subagent, treat that specific brief as failed and continue."

### Cross-Reviewer Agreement

| Topic | DHH | Kieran | Simplicity |
|-------|-----|--------|------------|
| Stale design doc cross-references | **MEDIUM** (R5-1, R5-2) | **MEDIUM** (R5-1, R5-4) | — |
| Redundant Step 15 | — | — | **MEDIUM** (R5-2) |
| Review artifacts in plan | — | — | **MEDIUM** (R5-1) |
| Unused status schema fields | — | — | **LOW** (R5-3, R5-4) |
| `model: inherit` omission | **LOW** (R5-4) | — | — |

### All Previous Findings — Verified Integrated

All 4 rounds of findings (Rounds 1-4) have been verified as integrated into the plan:
- **Round 4 HIGH items (K-R4-1, K-R4-2):** Completion Signal sections added to Tasks 2.2 and 2.3. Schemas match parent verification.
- **Variable counts:** 13/7/4/1 consistent across agent defs, templates, and CLAUDE.md dispatch.
- **File paths:** `_status.json` used consistently. No `_briefs-pdf-status.json` remnants.
- **All Round 1-3 findings:** RC1-RC9, A-1/A-2, D-1-D-4, E-1-E-3, S-1-S-3, NEW-1-NEW-6 — all addressed.

### Required Changes
None. No blocking issues.

### Recommended Changes
- [ ] DHH-R5-1 + DHH-R5-2 + K-R5-1: Inline complete file content for Tasks 1.3, 2.2, 2.3 (or add explicit stale-doc warnings)
- [ ] SIM-R5-2: Delete redundant Step 15
- [ ] SIM-R5-3 + SIM-R5-4: Remove unused `total_jobs_in_digest` and `briefs_compiled` from status schemas
- [ ] K-R5-2: Add output filename to Task 2.2 template spec

### Approval Status

**APPROVED for build.** No HIGH findings. No blocking issues. All previous findings (Rounds 1-4) verified integrated. Architecture is sound, contracts are defined, variable counts match, paths are consistent.

The 4 recommended changes (inline stale-doc content, delete Step 15, trim unused schema fields, add output filename) are quality-of-life improvements that reduce implementor confusion but do not affect runtime correctness. They can be addressed during build or ignored.

**Ready for `/build`.**

---

## Round 4 - 2026-02-07 22:30
**Reviewers:** dhh-rails-reviewer, kieran-rails-reviewer, code-simplicity-reviewer

### Summary

Three reviewers conducted a final pre-build review of the review-adjusted V13 plan. **No CRITICAL findings. 2 HIGH contract gaps (both from Kieran), 4 MEDIUM process/consistency items, 8 LOW/INFO polish items.** The architecture is sound and all prior findings remain fixed. The two HIGH items are genuine: the parent orchestrator verifies `html_generated` and `pdf_generated` fields in status JSON files that are never defined on the producer side — a contract gap that will cost debugging time at build.

### Findings — Consolidated

#### Must-Fix (2)

**K-R4-1 (HIGH): Digest-email `_status.json` schema is never defined.**
Step 13 tells the parent to verify `html_generated: true` in `output/digests/_status.json`, but nowhere in the plan — not in the digest-email agent definition (Task 2.1), not in the reference template (Task 2.2) — is the actual JSON schema specified. The implementing agent will have to guess what fields to write.
**Fix:** Add a "Completion Signal" section to Task 2.2 with the exact JSON schema: `{"status": "complete", "html_generated": true, "total_jobs_in_digest": N, "run_date": "..."}` and the `"failed"` variant.

**K-R4-2 (HIGH): Briefs-pdf `_status.json` schema is never defined.**
Same issue. Step 14 verifies `pdf_generated: true` but the briefs-pdf agent definition and template never specify what to write.
**Fix:** Add a "Completion Signal" section to Task 2.3 with the exact JSON schema.

#### Recommended (4)

**K-R4-3 (MEDIUM): `partial` status silently dropped for digest-email.**
V12's digest agent used `complete`/`partial`/`failed`. V13 drops `partial` without acknowledgment. Search-verify still uses 3 values. The asymmetry will confuse implementers.
**Fix:** Explicitly state in Phase 3 that digest-email uses two-value enum and why.

**K-R4-4 (MEDIUM): "Original plan" references unresolvable during build.**
Task 1.3 (line 70) and Task 2.2 (line 240) reference "original plan" content by stale line numbers. Builder clearing context between phases cannot find this content.
**Fix:** Pin exact file references: "Read `jsa-v13-design.md` Task 2 for design system skill content" and "Read `jsa-v13-design.md` Task 4 for digest-email template base content."

**D-R4-1 (MEDIUM): Plan is 830 lines for ~300 lines of actual content changes.**
Traceability tables, "Changes vs original plan" annotations, and task mapping appendix are review artifacts, not implementation instructions. Builder will spend time parsing cross-references instead of building.
**Fix:** Add note: "Implementor: ignore traceability tables. Each task contains its complete specification."

**D-R4-2 (MEDIUM): Prose pip bans in agent definitions create false confidence.**
`settings.local.json` is the actual enforcement mechanism. The prose "BANNED: Do NOT run pip..." is advisory only. Round 1 RC2 identified this; plan keeps prose bans anyway.
**Fix:** Keep prose bans (belt-and-suspenders) but acknowledge settings.local.json as the real enforcement.

#### Nice-to-Have (8)

**K-R4-5 (MEDIUM): Phase 2 H1 verification grep insufficiently specific (NEW-5 regression).**
`grep "^# {job_title} at {company}" ...` matches any H1. Should use `$` anchor or `head -1` pipe.
**Fix:** Change to `grep -c "^# {job_title} at {company}$"` with end anchor.

**SIM-1 (MEDIUM): Per-phase verification steps are checkbox theater.**
~60 lines of grep commands that verify the implementer wrote what they were just told to write. Only Phase 5 cross-file checks add real value.
**Fix:** Keep Phase 5 verification. Drop per-phase verification blocks during build.

**K-R4-6 (LOW): `brief-generator` breaks agent-to-template naming pattern.**
`brief-generator.md` → `subagent-brief.md` while all others follow `{agent-name}.md` → `subagent-{agent-name}.md`.
**Fix:** Rename template to `subagent-brief-generator.md` or agent to `brief.md`. Cosmetic.

**K-R4-7 (LOW): `Skill` in disallowedTools inconsistent across agents.**
search-verify disallows Skill; brief-generator does not. Neither uses skills.
**Fix:** Add `Skill` to brief-generator's disallowedTools to match search-verify.

**K-R4-8 (LOW): Missing UTF-8 encoding on file read in send_email.py.**
`open(args.body_file)` should be `open(args.body_file, encoding="utf-8")` for HTML files.
**Fix:** Add `encoding="utf-8"` to both file opens.

**D-R4-4 (LOW): Hardcoded Resend sandbox sender domain.**
`onboarding@resend.dev` is inherited from V12. Will hit spam filters in production.
**Fix:** Add `# TODO: Replace with verified custom domain` comment in script.

**SIM-4 (LOW): Cover page + TOC is speculative scope.**
Already marked "cut if friction" — should just be cut. A 3-5 brief PDF doesn't need a TOC.
**Fix:** Remove cover/TOC from briefs-pdf template. Add in V14 if wanted.

**SIM-5 (LOW): `_delivery-status.json` could merge into existing `_status.json`.**
Three status files for the email path. Could append `email_sent`/`sent_at` to `output/digests/_status.json` instead of creating a new file.
**Fix:** Consider merging during implementation. Separate file is defensible (different lifecycle) but adds complexity.

### Cross-Reviewer Agreement

| Topic | DHH | Kieran | Simplicity |
|-------|-----|--------|------------|
| Status JSON schemas undefined | — | **HIGH** (R4-1, R4-2) | — |
| Plan verbosity / review artifacts | **MEDIUM** (R4-1) | — | **MEDIUM** (SIM-3) |
| Prose pip bans vs settings enforcement | **MEDIUM** (R4-2) | — | — |
| Skill disallowedTools inconsistency | **LOW** (R4-3) | **LOW** (R4-7) | **LOW** (SIM-8) |
| Per-phase verification bloat | — | — | **MEDIUM** (SIM-1) |
| "Original plan" unresolvable refs | — | **MEDIUM** (R4-4) | — |
| Cover/TOC YAGNI | — | — | **LOW** (SIM-4) |
| Delivery status file merging | — | — | **LOW** (SIM-5) |

### Required Changes
- [ ] K-R4-1: Define digest-email `_status.json` schema in Task 2.2
- [ ] K-R4-2: Define briefs-pdf `_status.json` schema in Task 2.3

### Recommended Changes
- [ ] K-R4-3: Explicitly acknowledge `partial` status removal
- [ ] K-R4-4: Pin "original plan" references to exact file paths
- [ ] K-R4-5: Fix H1 verification grep with `$` anchor
- [ ] K-R4-7: Add `Skill` to brief-generator disallowedTools
- [ ] K-R4-8: Add `encoding="utf-8"` to send_email.py file opens

### Approval Status

**Needs Changes** — 2 HIGH must-fix items (K-R4-1, K-R4-2). Both are contract gaps where the parent verifies JSON fields that no producer defines. Trivially fixable by adding "Completion Signal" sections to Tasks 2.2 and 2.3. All other findings are MEDIUM or below and can be addressed during implementation.

After fixing K-R4-1 and K-R4-2, plan is ready for `/build`.

---

## Round 3 - 2026-02-07 20:45
**Reviewers:** architecture-strategist, code-simplicity-reviewer, data-integrity-guardian

### Summary

Three reviewers verified the review-adjusted V13 plan against all 17 Round 2 findings. **All 17 findings are confirmed FIXED.** No blocking issues remain. 2 MEDIUM cleanup items and 4 LOW/INFO items were identified — all resolvable during implementation without a plan revision.

### Round 2 Verification — All 17 Fixed

| Finding | Severity | R3 Status | Verification |
|---------|----------|-----------|--------------|
| RC1 | HIGH | FIXED | Steps 5/11 rewritten — no `cd to v12`, named agent handles cd |
| D-1 | HIGH | FIXED | Sentinel `<!-- BRIEF COMPLETE -->` in brief template + parent verifies |
| D-2 | HIGH | FIXED | `match_reason` eliminated, replaced with `requirements_met` + `score_breakdown` synthesis |
| E-1 | HIGH | FIXED | `_delivery-status.json` written after send, checked on resume |
| E-2 | HIGH | FIXED | Step 16 gates on both status files, 3 options on partial failure |
| S-1 | HIGH/YAGNI | FIXED | Task 13 deleted, no templates.md references anywhere |
| A-1 | MEDIUM | FIXED | All 4 agent defs use comma-separated tools format |
| A-2 | MEDIUM | FIXED | Phase 5 includes `npx playwright --version` check |
| D-3 | MEDIUM | FIXED | Exact H1: `# {job_title} at {company}`, no "or similar" |
| D-4 | MEDIUM | FIXED | Null job_url → plain text + "(URL unavailable)" in #525252 |
| S-2 | MEDIUM | FIXED | send_email.py stripped — no --body/--file/--html/--test/markdown_to_html |
| RC5 | MEDIUM | FIXED | No Playwright reference in digest-email agent |
| E-3 | LOW | FIXED | Hang detection guidance for both digest and briefs-pdf |
| S-3 | LOW | FIXED | `source .env` removed from CLAUDE.md, Python dotenv only |
| RC8 | LOW | FIXED | `_status.json` used consistently, no `_briefs-pdf-status.json` |
| D-3b | LOW | FIXED | `total_verified` removed, agent counts files itself |
| Cover/TOC | LOW | FIXED | Kept with "cut if friction" graceful degradation |

### New Findings

#### Must-Fix During Implementation (2)

**NEW-1 (MEDIUM): Dead `Bash(source .env)` permission in settings.local.json.**
S-3 removes all `source .env` calls from CLAUDE.md and send_email.py, but `settings.local.json` line 75 still includes `"Bash(source .env)"` in the allow list. Dead permission that contradicts S-3 intent.
**Fix:** Remove `"Bash(source .env)"` from the allow array during Phase 1 Task 1.4.
*Found by: architecture-strategist, code-simplicity-reviewer, data-integrity-guardian (all three)*

**NEW-2 (MEDIUM): brief-generator writes `_brief-FAILED-*` marker files that parent never reads.**
Agent definition (line 156) writes `output/briefs/_brief-FAILED-{company_slug}-{title_slug}.json` on failure. But Step 11 (lines 444-448) only checks for the brief `.md` file + sentinel. The marker files are orphaned data. The sentinel approach (D-1) is the actual mechanism.
**Fix:** Remove the `_brief-FAILED-*` marker from agent definition. On failure, write nothing — parent detects via missing file or missing sentinel.
*Found by: architecture-strategist*

#### Informational (4)

**NEW-3 (LOW): Line count claims inconsistent.** Plan says "~45 lines" (line 638), actual script is ~77 lines, verification expects "~65 lines" (line 736). Script is already minimal — just fix the estimates.

**NEW-4 (LOW): search-verify agent failure status path ambiguous.** Line 134 says `_status.json` without directory prefix. Other agents specify full paths. Should be `output/verified/{role_type_slug}/_status.json`.

**NEW-5 (LOW): Phase 2 verification line 333 checks wrong thing.** `head -1` of subagent-brief.md checks the file's first line, not the H1 format instruction. Should grep for the pattern instead.

**NEW-6 (LOW/INFO): Design doc stale.** `jsa-v13-design.md` still has: 5 digest variables (should be 4), `_briefs-pdf-status.json` (should be `_status.json`), `pip`/`pip3` in disallowedTools, `--test` flag. Plan is authoritative — no runtime impact.

### Cross-File Consistency — Verified

| Item | Agent Def | Template | CLAUDE.md | OUTPUTS | Match? |
|------|-----------|----------|-----------|---------|--------|
| Digest status | `output/digests/_status.json` | Task 2.2 | Steps 13, 15, 16 | Line 555 | YES |
| Briefs-PDF status | `output/briefs/_status.json` | Task 2.3 | Steps 14, 15, 16 | Line 556 | YES |
| Delivery status | N/A (parent) | N/A | Step 16 | Line 557 | YES |
| Digest variables | 4 | 4 | 4 (Step 13) | N/A | YES |
| Brief variables | 7 | 7 | 7 (Step 11) | N/A | YES |
| Search variables | 13 | 13 | 13 (Step 5) | N/A | YES |
| Briefs-PDF variables | 1 | 1 | 1 (Step 14) | N/A | YES |
| `match_reason` | absent | prohibited | absent | N/A | YES |
| `total_verified` | absent | absent | absent | N/A | YES |

### Agent Definition Assessment — Not Bloated

Each prose block in the 4 agent definitions was examined. Every line serves a purpose YAML frontmatter alone cannot enforce:
- BANNED pip/pip3 text — only agent-level guard (YAML disallowedTools blocks Claude tools, not bash commands)
- "CRITICAL: follow design system" — YAML preloads skill but doesn't set priority
- "Working directory / First action: cd" — the RC1 fix itself
- "On startup: Read references/..." — bridges agent identity to template
- "If any variable is missing: Write _status.json" — D-1/E-3 error handling

### Approval Status

**APPROVED for implementation.** All 17 Round 2 findings verified fixed. 2 MEDIUM items (NEW-1, NEW-2) to fix during implementation — no plan revision needed. Architecture is sound, cross-file consistency verified, no YAGNI violations, no dead code, no race conditions.

**Implementation notes:**
1. Phase 1 Task 1.4: Remove `"Bash(source .env)"` from settings.local.json (NEW-1)
2. Phase 2 Task 2.1: Remove `_brief-FAILED-*` marker from brief-generator agent def (NEW-2)
3. Phase 4 Task 4.1: Update line count estimate to ~75 lines (NEW-3)

---

## Round 2 - 2026-02-07 18:15
**Reviewers:** architecture-strategist, code-simplicity-reviewer, data-integrity-guardian

### Summary

Three reviewers conducted deep analysis of the V13 plan against Round 1's 9 findings. Result: **RC1 (v12 paths) is confirmed NOT FIXED and remains the top-priority bug.** RC2 (pip in disallowedTools) IS fixed in the plan. Several new findings emerged, particularly around data integrity: silent brief-generator failures, a missing `match_reason` field in the verified JSON schema, and no idempotency guard on email sending. **6 must-fix items, 6 recommended, 5 informational.**

### Round 1 Status Check

| R1 Finding | R1 Severity | R2 Status |
|-----------|------------|-----------|
| RC1: v12 path in steps 5/11 prompt | HIGH | **NOT FIXED** — Task 11 only swaps `subagent_type`, does not touch `cd` instruction |
| RC2: pip in disallowedTools | HIGH | **FIXED** — plan YAML correctly omits pip/pip3 |
| RC3: briefs footer when total_briefs=0 | MEDIUM | **NOT FIXED** — and problem is worse than R1 identified (see E2) |
| RC4: send_email.py simplification | MEDIUM | **NOT FIXED** — plan still has 7 flags, only 4 needed |
| RC5: digest-email mentions PDF rendering | MEDIUM | **NOT FIXED** — copy-paste error remains |
| RC6: templates.md duplication | MEDIUM | **ESCALATED TO DELETE** — file has zero consumers, Task 13 is wasted effort |
| RC7: brief-generator silent failure | LOW | **ESCALATED TO HIGH** — allows corrupt/truncated briefs downstream |
| RC8: status file naming | LOW | **CONFIRMED LOW** — cosmetic |
| RC9: templates.md file locations | LOW | **MOOT** — if Task 13 is deleted per RC6 escalation |

### New Findings

#### Architecture

**A-1 (MEDIUM): YAML list syntax vs documented comma-separated format.** The plan uses YAML list syntax for `tools`/`disallowedTools`:
```yaml
tools:
  - Bash
  - Read
```
Official Claude Code docs use comma-separated strings: `tools: Bash, Read, Write`. If the parser doesn't handle list format, tool restrictions silently fail (agent gets all tools). **Fix:** Use comma-separated string format to match documentation.

**A-2 (MEDIUM): No Playwright availability check in Task 14.** The verification steps check file existence and grep patterns but never verify `npx playwright --version` or Chromium installation. A missing Playwright would only surface at runtime during digest/briefs PDF generation.

#### Data Integrity

**D-1 (HIGH): brief-generator silent failure allows corrupt data downstream.** The plan says brief-generator "exits without writing any output files" on failure. But if it crashes AFTER partially writing a brief .md file, the parent sees a non-empty file and considers the brief complete. The truncated brief flows into the briefs PDF and email. **Fix:** brief-generator must write `_brief-status.json` on failure, or write a sentinel line (`<!-- BRIEF COMPLETE -->`) at the end of each brief that the parent can grep for.

**D-2 (HIGH): digest-email template references `match_reason` field that doesn't exist.** The template instructs the agent to show "Match reason: 1-2 sentences" for Top 5 and "One-line match reason" in the table. But the verified JSON schema has no `match_reason` field — only `requirements_met`, `gaps`, `preferred_met`, and `score_breakdown`. The agent will either fabricate data (violating Core Rule 2) or leave the column empty. **Fix:** Either (a) add `match_reason` to the verified JSON schema in `subagent-search-verify.md`, or (b) explicitly instruct the digest-email agent to synthesize a reason from `requirements_met` + `score_breakdown`.

**D-3 (MEDIUM): Brief H1 format ambiguity.** The briefs-pdf template says "Extract title and company from each brief's first line (format: `# {title} at {company}` or similar)." The phrase "or similar" is dangerous — the brief-generator actually writes `# Brief Generation: {job_title} at {company}`. The "Brief Generation:" prefix will appear in the TOC. **Fix:** Define the exact H1 format.

**D-4 (MEDIUM): No fallback for null `job_url` in digest.** If a verified job has `"job_url": null` (WebFetch failed), the digest generates `<a href="null">Title</a>`. **Fix:** Add instruction: "If job_url is null, display title as plain text with '(URL unavailable)'."

#### Email Safety

**E-1 (HIGH): No idempotency guard on email sending.** If the session crashes after `send_email.py` succeeds but before `session-state.md` is updated, the next resume re-sends the email. V12 had `"email_sent": true` in `_status.json` (written by the digest subagent). V13 moves email to the parent but adds no delivery status file. **Fix:** After successful send, parent writes `output/digests/_delivery-status.json` with `{"email_sent": true, "sent_at": "..."}`. On resume, check this file first.

**E-2 (HIGH): Briefs-pdf failure doesn't gate email send.** If briefs-pdf fails but digest-email succeeds, step 16 sends the email without the PDF attachment. The email body still says "Application briefs attached as PDF." **Fix:** Step 16 must gate on BOTH status files showing `"complete"`. If briefs-pdf failed, ask user: "Send without attachment, retry PDF, or abort?"

**E-3 (MEDIUM): No timeout/hang detection for subagents.** The plan says "Verify completion: Read status file" but has no guidance for when the Task tool returns and no status file exists (agent crashed without writing status).

#### Simplicity

**S-1 (HIGH/YAGNI): Delete Task 13 entirely.** `templates.md` has zero consumers — not referenced by CLAUDE.md, not referenced by any subagent template. Updating a dead file is wasted effort. The design system skill is the canonical source.

**S-2 (MEDIUM): Strip send_email.py to V13-only path.** Zero callers for `--body`, `--file --html`, `--test`, or `markdown_to_html()` in V13. Target: ~45 lines instead of ~140.

**S-3 (LOW): Deduplicate .env loading.** Plan adds Python `load_dotenv()` while V12 used `source .env &&` in bash. Step 16 omits `source .env`, so Python loader compensates. Pick one mechanism.

### Required Changes (Consolidated)

#### Must-Fix (6)

- [ ] **RC1 (HIGH): Rewrite steps 5/11 prompt text to remove `cd to '03_agents/tests/v12/'`.** The named agent definition handles `cd`. The prompt should contain only the compact JSON blob. Currently Task 11 only swaps `subagent_type` without touching surrounding prompt text.

- [ ] **D-1 (HIGH): Add failure status to brief-generator.** Write `output/briefs/_brief-{company_slug}-{title_slug}-status.json` on failure, or write `<!-- BRIEF COMPLETE -->` sentinel at end of each brief. Silent exit allows corrupt data downstream.

- [ ] **D-2 (HIGH): Fix `match_reason` in digest-email template.** Either add a `match_reason` field to the verified JSON schema, or instruct the digest-email agent to synthesize from `requirements_met` + `score_breakdown`. Currently references a nonexistent field.

- [ ] **E-1 (HIGH): Add email delivery status file.** Parent writes `output/digests/_delivery-status.json` after successful send. On resume, check this before re-sending.

- [ ] **E-2 (HIGH): Gate email send on both subagent statuses.** Step 16 must check both `_status.json` (digest) and `_briefs-pdf-status.json` (briefs) show `"complete"` before sending. If briefs-pdf failed, ask user how to proceed.

- [ ] **S-1 (HIGH/YAGNI): Delete Task 13.** `templates.md` has zero consumers. Don't update a dead file.

#### Recommended (6)

- [ ] **A-1 (MEDIUM): Use comma-separated string format for tools/disallowedTools in agent YAML.** Match documented format to avoid silent parsing failure.

- [ ] **A-2 (MEDIUM): Add Playwright check to Task 14 verification.** Run `npx playwright --version` to verify availability before first test run.

- [ ] **D-3 (MEDIUM): Define exact brief H1 format.** Remove "or similar" from briefs-pdf template. Specify: `# {job_title} at {company}` (no prefix).

- [ ] **D-4 (MEDIUM): Add null job_url fallback in digest-email.** Display plain text title with "(URL unavailable)" when job_url is null.

- [ ] **S-2 (MEDIUM): Strip send_email.py.** Remove unused flags. Make `--body-file` required. Target ~45 lines.

- [ ] **RC5 (MEDIUM): Fix digest-email agent prose.** Remove "Playwright + Chromium for PDF rendering" — this agent generates HTML only.

#### Nice-to-Have (5)

- [ ] **E-3 (MEDIUM→LOW): Add hang detection guidance.** "If Task tool returns but no status file exists, treat as failed."

- [ ] **S-3 (LOW): Deduplicate .env loading.** Keep Python `load_dotenv()`, remove `source .env` references.

- [ ] **RC8 (LOW): Standardize status file naming.** Use `_status.json` everywhere.

- [ ] **D-3b (LOW): Pre-counted `total_verified` may drift from actual file count.** Let digest-email agent count files itself.

- [ ] **Cover page + TOC (LOW): Nice-to-have feature addition.** Not a V12 failure fix — cut if it causes implementation friction.

### Approval Status

**Needs Changes** — 6 must-fix items before implementation. RC1 (v12 paths) and D-2 (match_reason) are the highest risk: one sends subagents to the wrong directory, the other produces fabricated or empty data in the primary user-facing output. E-1 and E-2 prevent duplicate/misleading emails. D-1 prevents corrupt briefs. S-1 removes wasted work.

After addressing must-fix items, plan is ready for `/build`.

---

## Round 1 - 2026-02-07 16:30
**Reviewers:** architecture-strategist, code-simplicity-reviewer, pattern-recognition-specialist

### Summary

The V13 plan is architecturally sound. The named agent + preloaded skill pattern is the correct structural fix for V12's delivery failures. All 8 failures map to concrete fixes. Three reviewers identified **1 HIGH-priority bug, 5 MEDIUM issues, and 4 simplification opportunities**. The plan is ready to implement after addressing the required changes below.

### Findings

#### Architecture Review

**Sound decisions:**
- Named agents (`.claude/agents/`) shift constraints from advisory (prose suggestions) to structural (YAML frontmatter). This directly fixes V12's F3-F6 where subagents ignored design instructions.
- Design system skill as single source of truth — mirrors the proven competitor-intel pattern.
- Parent-orchestrated email — correct boundary given platform Bash permission constraints.
- Clean separation of concerns: agent defs (identity) / reference templates (instructions) / skills (shared knowledge) / scripts (utilities).

**Key risk validated:** All YAML frontmatter fields (`tools`, `disallowedTools`, `skills`, `memory`, `model`) are confirmed supported by Claude Code named agents. However, `disallowedTools` operates on Claude Code tool names, not bash commands — so `pip`/`pip3` in `disallowedTools` will be silently ignored (see Required Change 1).

#### Simplicity Review

**Over-engineering found:**
- `send_email.py` has 3 body input modes but V13 only uses `--body-file`. The `--body`, `--file --html`, `markdown_to_html()`, HTML auto-detection, and `--test` flag are unused legacy code.
- `templates.md` Task 13 duplicates design system specs that already live in the skill file.
- Agent definition body text repeats BANNED/CRITICAL paragraphs that the YAML frontmatter and skill already enforce.

**Task consolidation proposed:**
- Tasks 1 + 6 + 7 (copy + delete obsolete + path updates) are one logical operation.
- Tasks 10 + 11 + 12 already share one commit — could be one task.
- Net: 14 tasks could be 10.

#### Pattern Recognition Review

**Consistency issues found:**
- Status enum: search-verify uses 3 values (`complete`/`partial`/`failed`), new agents use 2 (`complete`/`failed`).
- Status file naming: `_status.json` (generic) vs `_briefs-pdf-status.json` (qualified).
- `brief-generator` exits silently on failure; all other agents write `_status.json`.
- Agent-to-template naming: `brief-generator.md` → `subagent-brief.md` breaks the `{agent-name}` = `{template-suffix}` pattern.

### Required Changes

- [ ] **RC1 (HIGH): Fix v12 path in CLAUDE.md steps 5 and 11 prompt text.** Task 11 changes `subagent_type` from `"general-purpose"` to `"search-verify"` / `"brief-generator"` but does NOT update the `cd to '03_agents/tests/v12/'` path in the prompt text (V12 CLAUDE.md lines 108 and 138). The named agent definition says `cd 03_agents/tests/v13/` while the prompt says `cd to 03_agents/tests/v12/` — contradictory instructions to the same subagent. **Fix:** Remove the `cd` instruction from the prompt text entirely (the named agent definition handles it), or update to v13.

- [ ] **RC2 (HIGH): Remove `pip` and `pip3` from `disallowedTools` in agent definitions.** `disallowedTools` blocks Claude Code tools (Bash, Read, Write, etc.), not bash commands. `pip` and `pip3` are not tool names and will be silently ignored. Pip blocking is enforced by: (a) `settings.local.json` removing pip permissions (Task 9), and (b) prose bans in agent body text. Remove from YAML to avoid false confidence.

- [ ] **RC3 (MEDIUM): Add `briefs_available` boolean to digest-email compact JSON.** Currently the digest-email agent has no signal about whether briefs were generated. It will always include "Application briefs attached as PDF" in the footer. When `total_briefs` is 0, this is misleading. **Fix:** Either use `total_briefs > 0` as the signal (already available — just add a conditional to the template) or add an explicit boolean.

- [ ] **RC4 (MEDIUM): Simplify `send_email.py` — strip to only the V13 path.** Remove `--body`, `--file --html`, `markdown_to_html()`, HTML auto-detection, and `--test` flag. Make `--body-file` required. Keep `--attachment` (repeatable) and `.env` auto-loading. ~65 lines instead of ~140.

- [ ] **RC5 (MEDIUM): Fix digest-email agent body text.** The agent definition (plan lines 331-333) mentions "Use Playwright + Chromium for PDF rendering" but this agent generates HTML only, not PDF. Copy-paste error from briefs-pdf agent.

- [ ] **RC6 (MEDIUM): Eliminate `templates.md` design spec duplication.** Task 13 creates a condensed copy of the design system in `templates.md`. Since the skill is the canonical source, replace the entire "PDF Design Requirements" section with: `See .claude/skills/jsa-design-system.md (preloaded into visual subagents).`

- [ ] **RC7 (LOW): Make brief-generator write `_status.json` on failure.** Currently it "exits without writing any output files" — the only agent that doesn't write a status signal. Add failure status file for consistency.

- [ ] **RC8 (LOW): Standardize status file naming.** Use `_status.json` everywhere (digest already does this). Rename `_briefs-pdf-status.json` → `_status.json` in `output/briefs/`.

- [ ] **RC9 (LOW): Update `templates.md` File Locations table.** The table uses `{job_id}` placeholders and `.pdf` extensions that don't match actual conventions (`{company_slug}-{title_slug}`, `.md`). Task 13 should update this too.

### Approval Status

**Needs Changes** — RC1 and RC2 are must-fix before implementation. RC3-RC6 are strongly recommended. RC7-RC9 are nice-to-haves.

---

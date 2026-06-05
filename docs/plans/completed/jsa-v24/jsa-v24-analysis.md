# Session Analysis: Job Search Agent V24

## Summary
7 wins, 15 failures (1 critical, 10 major, 4 minor), 4 edge cases. UX/CLI issues surface as a new failure category with 5 findings. Recurring regressions (commit+push, session-state.md) hit 9th and 10th occurrence respectively — constraint-based enforcement is provably insufficient and requires structural gates.

## What Went Well

1. **Parallel channel dispatch with live progress table** — All 5 search-verify channels launched simultaneously with rolling table updates as each completed. Clear, efficient orchestration pattern.
2. **Self-correcting context.md format fix** — Agent detected slug parser failure, diagnosed compound-bullet root cause, rewrote to one-role-per-line, and re-validated — all without user intervention.
3. **On-demand re-verification for user-requested jobs** — When user listed 10 jobs from memory (some not in current results), agent dispatched a targeted lookup+verify subagent rather than failing or guessing.
4. **Graceful compaction recovery** — After rate limit + compaction, agent reconstructed session state from artifact existence checks and resumed at the correct step without repeating work.
5. **Immediate user signal acceptance** — When user said "just send me the digest email," agent dropped briefs-html without friction or re-confirmation.
6. **Auto-retry protocol worked for API errors** — Both briefs-html and digest-email succeeded on second dispatch after API connection failures.
7. **Schema migration gate preserved data** — 86 files migrated to canonical schema without data loss; all gates passed after migration.

## What Failed

### Failure 1: Preflight exits with error code 1 on fresh build
- **What happened:** `bash scripts/preflight.sh` returned exit code 1 with "ERROR: Safety bound exceeded" (100% archive rate) on first run after V24 build. Agent continued but the error cascaded to a sibling `date` call.
- **Root cause:** Safety bounds fire at 100% when no prior-run data exists — script doesn't distinguish fresh build from data corruption.
- **Category:** configuration
- **Prevention:** Automated: Yes — add first-run detection to preflight.sh
- **Principle violated:** Startup reliability
- **Fix type:** Implementation

### Failure 2: context.md bullet format breaks slug parser
- **What happened:** Agent wrote compound bullets (`- **Role types:** X, Y, Z`); `list-active-role-types` slugified the entire line instead of individual names.
- **Root cause:** No format validation on context.md Target section writes. Parser expects one item per line.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — post-write validation of slug extraction
- **Principle violated:** Write-then-validate pattern
- **Fix type:** Implementation

### Failure 3: Search-verify agents don't write .done sentinels
- **What happened:** All 5 search-verify agents completed but none created `.done` sentinel markers. Gate-check failed; required 2 extra recovery dispatches.
- **Root cause:** Sentinel write step missing from search-verify agent definition. 4th occurrence (V14/V16/V18/V24).
- **Category:** subagent-coordination
- **Prevention:** Automated: Yes — `for d in output/verified/*/; do [ -f "$d/.done" ] || echo "MISSING: $d"; done`
- **Principle violated:** Agent output contract completeness
- **Fix type:** Implementation

### Failure 4: Schema validation failure on 16/23 verified JSONs
- **What happened:** Verified JSONs written in legacy format. Required schema migration gate before downstream ops could proceed.
- **Root cause:** Search-verify agents produce output in pre-V24 format; canonical schema enforcement added in build but not propagated to agent output contract.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — data-integrity-guardian reviewer prompt added
- **Principle violated:** Schema-first enforcement (V24 design principle)
- **Fix type:** Implementation

### Failure 5: briefs-html and digest-email API connection errors
- **What happened:** Both agents failed on first dispatch with API connection errors. Succeeded on retry.
- **Root cause:** Transient API errors. Auto-retry handled it, but error reporting to user lacked detail.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — deployment-verifier reviewer prompt added (error reporting quality)
- **Principle violated:** Error transparency to user
- **Fix type:** Implementation

### Failure 6: Rate limit mid-session caused delivery failure
- **What happened:** Usage limit hit during delivery phase. Both briefs-html and digest-email aborted. Required full session restart.
- **Root cause:** Token budget exceeded by 8 brief-generators + compilation agents in single session. No graceful pause mechanism.
- **Category:** performance
- **Prevention:** Automated: No — requires human judgment on session structure
- **Principle violated:** Session budget awareness
- **Fix type:** Architectural

### Failure 7: Post-compaction file reads violate context budget
- **What happened:** After compaction, parent read `_delta.json` and `_summary.md` files directly instead of dispatching recovery subagent.
- **Root cause:** No documented recovery protocol for post-compaction. P2 rule exists but isn't operationalized as a dispatch pattern.
- **Category:** subagent-coordination
- **Prevention:** Automated: No — requires human judgment on recovery pattern
- **Principle violated:** P2 (post-compaction rule), context budget
- **Fix type:** Implementation

### Failure 8: No commit/push after search batch (9th occurrence)
- **What happened:** HC-7 requires commit+push after each search batch. No commit confirmed after Phase 1.
- **Root cause:** Constraint exists but no structural gate enforces it. 9th occurrence across V14-V24.
- **Category:** subagent-coordination
- **Prevention:** Automated: Yes — gate-check after search phase that verifies git status shows no uncommitted changes
- **Principle violated:** HC-7 (incremental commit+push)
- **Fix type:** Implementation — needs structural commit gate, not just constraint

### Failure 9: Briefs HTML skipped due to token cost
- **What happened:** User complained briefs-html was "using up way too many tokens." Agent dropped briefs entirely.
- **Root cause:** briefs-html compilation is too token-heavy when run in same session as 8 brief-generators.
- **Category:** performance
- **Prevention:** Automated: No — requires architectural decision on session structure
- **Principle violated:** Delivery completeness within budget
- **Fix type:** Architectural

### Failure 10: Status table reprinted after every brief completion
- **What happened:** Full 8-row status table reprinted 8 times (once per brief completion). 7 near-identical tables creating wall of text.
- **Root cause:** Live progress pattern reprints full table on every event. No delta-only update logic.
- **Category:** ux-cli
- **Prevention:** Automated: Yes — one-liner per completion, full table only at end
- **Principle violated:** Minimal output, maximum signal
- **Fix type:** Implementation

### Failure 11: No proactive status during long-running ops
- **What happened:** User asked "still going?" 3 times during multi-minute background agent runs. Agent had no proactive update cadence.
- **Root cause:** No timed polling or proactive status protocol for long-running background operations.
- **Category:** ux-cli
- **Prevention:** Automated: Partial — deployment-verifier reviewer prompt added (proactive cadence)
- **Principle violated:** User never has to ask for status
- **Fix type:** Implementation

### Failure 12: Agent lost task IDs after compaction
- **What happened:** Task IDs for background agents became invalid after context compaction. Agent couldn't poll status; discovered completion only via filesystem check.
- **Root cause:** Task IDs stored only in conversation context, lost on compaction.
- **Category:** subagent-coordination
- **Prevention:** Automated: Yes — persist task IDs in session-state.md
- **Principle violated:** State persistence across compaction
- **Fix type:** Implementation

### Failure 13: No session-state.md checkpoint after search (10th occurrence)
- **What happened:** CR-10 requires writing session-state.md after every search batch. Never written for Feb 26 run.
- **Root cause:** Same as 9 prior versions — write deferred and never executed. Constraint alone is insufficient.
- **Category:** subagent-coordination
- **Prevention:** Automated: Yes — structural write gate at search phase exit
- **Principle violated:** CR-10 (session-state checkpoint)
- **Fix type:** Implementation — needs structural gate, not just constraint

### Failure 14: No visual separators between role sections
- **What happened:** Four role-type result sections separated only by `---` and bold heading. No spacing, counts, or hierarchy for terminal readability.
- **Root cause:** Presentation template uses minimal markdown separators.
- **Category:** ux-cli
- **Prevention:** Automated: No — requires human judgment on presentation design
- **Principle violated:** Output readability
- **Fix type:** Implementation

### Failure 15: User typed job names instead of using numbered selection
- **What happened:** Agent offered numbered selection ("1, 3, 5") but user typed company names from memory, including prior-run jobs not in current tables.
- **Root cause:** Selection prompt didn't include prior-run active jobs. User had context the agent didn't surface.
- **Category:** ux-cli
- **Prevention:** Automated: No — requires design decision on selection UX
- **Principle violated:** Selection should include all eligible jobs
- **Fix type:** Implementation

## Constraint Compliance Failures (Additional)

- **HC-5:** `list-active-role-types` run in parent context — not in allowed subcommand list. Implementation fix: delegate to subagent or add to allowed list.
- **HC-10:** `working_dir`, `output_directory`, `dashboard_url` not passed to any subagent dispatch (V23 recurrence). Implementation fix: add to dispatch templates.
- **CR-7:** Relative paths used when citing output files. Implementation fix: enforce absolute paths in orchestration.
- **CR-12:** No post-dispatch directory verification. Implementation fix: add verification step after each dispatch.
- **Startup git pull:** Preflight.sh git pull is implicit; required explicit parent `git pull` with success verification not performed.

## Fixes Needed

### Architectural Fixes

**1. Decouple brief generation from briefs-html compilation**
- **What needs to change:** briefs-html should be a separate session or pre-compiled step, not run in the same context window as 8 brief-generators. Options: (a) generate briefs in session 1, compile HTML in session 2; (b) pre-compile briefs into a lightweight format that briefs-html can process without full-context cost.
- **Files affected:** CLAUDE.md (Phase Dispatch), references/orchestration.md (Phase 5), briefs-html agent definition
- **Verification criteria:** Full delivery (briefs + digest) completes without hitting rate limits in a single workflow execution

**2. Token budget awareness / rate limit detection**
- **What needs to change:** Agent needs awareness of remaining token budget and a graceful pause mechanism when approaching limits. Options: (a) hard cap on subagent dispatches per session; (b) detect rate limit response and checkpoint for resume; (c) split delivery into mandatory (digest) and optional (briefs-html) tiers.
- **Files affected:** CLAUDE.md (new section), references/orchestration.md (Phase 5 budget protocol)
- **Verification criteria:** Session never fails silently due to rate limit; user always gets at least the digest email

### Implementation Fixes

**1. Add .done sentinel write to search-verify agent**
- **What needs to change:** search-verify agent definition must include sentinel file creation as its final step.
- **Files affected:** search-verify agent definition (SKILL.md or agent prompt)
- **Verification criteria:** Gate-check passes on first attempt without recovery dispatches

**2. Add canonical schema validation inside search-verify agent**
- **What needs to change:** search-verify agent must validate output against canonical 10-field schema before writing verified JSON.
- **Files affected:** search-verify agent definition, canonical schema reference
- **Verification criteria:** Zero schema validation failures in post-search gates

**3. Add structural commit gate at Phase 1 exit**
- **What needs to change:** A blocking gate-check step after all search channels complete that verifies `git status` shows no uncommitted changes. If uncommitted, commit and push before proceeding.
- **Files affected:** references/orchestration.md (Phase 1 exit gate), gate-check agent prompt
- **Verification criteria:** `git log` shows a commit with today's date after search phase completes

**4. Add structural session-state.md write gate at Phase 1 exit**
- **What needs to change:** A blocking gate-check step that verifies session-state.md was written with today's date before proceeding past search phase.
- **Files affected:** references/orchestration.md (Phase 1 exit gate)
- **Verification criteria:** `output/session-state.md` exists with today's date after search phase

**5. Fix preflight.sh first-run detection**
- **What needs to change:** Safety bound checks should detect when no prior-run data exists and skip bounds (or use a different threshold for first runs).
- **Files affected:** scripts/preflight.sh
- **Verification criteria:** Preflight exits 0 on fresh build with no prior-run data

**6. Add context.md Target format validation**
- **What needs to change:** After writing context.md Target section, run `list-active-role-types` and verify output contains expected number of clean slugs.
- **Files affected:** CLAUDE.md (Constraint Derivation section or onboarding)
- **Verification criteria:** `list-active-role-types` returns N clean slugs matching N target roles

**7. Add post-compaction recovery dispatch protocol**
- **What needs to change:** Document a specific recovery dispatch pattern: after compaction, dispatch a recovery subagent to read status files and return a structured state summary — parent never reads files directly.
- **Files affected:** CLAUDE.md (new subsection under Context Budget)
- **Verification criteria:** Post-compaction, parent dispatches subagent and receives state summary (no direct file reads in parent)

**8. UX: One-liner brief progress, full table at end**
- **What needs to change:** During parallel brief generation, print "Brief 3/8 done — [company name]" per completion. Print full status table only once when all complete.
- **Files affected:** references/orchestration.md (Phase 5 brief generation), CLAUDE.md (UX Rules)
- **Verification criteria:** Terminal output shows one-liners during generation, single table at end

**9. UX: Proactive timed status updates during long-running ops**
- **What needs to change:** When dispatching background agents expected to take >2 minutes, commit to a timed check cadence (e.g., "I'll check back every 90 seconds") and implement it.
- **Files affected:** CLAUDE.md (UX Rules), references/orchestration.md (all parallel dispatch sections)
- **Verification criteria:** User never needs to ask "still going?" — agent proactively updates

**10. UX: Immediate post-compaction status message**
- **What needs to change:** After context compaction, first user-visible output must be a 1-2 sentence status summary (what completed, what's pending) before any file reads.
- **Files affected:** CLAUDE.md (Recovery Protocol or new post-compaction section)
- **Verification criteria:** First message after compaction is a status summary, not silence followed by file reads

**11. UX: Unified numbered job selection including prior-run active jobs**
- **What needs to change:** When asking user to select jobs for briefs, include all eligible jobs (today's new + still-active from prior runs) in a single numbered list.
- **Files affected:** references/presentation-rules.md, references/orchestration.md (Phase 4)
- **Verification criteria:** User can select any eligible job by number, including prior-run actives

**12. UX: Clear section headers with counts in results presentation**
- **What needs to change:** Each role type section should have a prominent header with count: `## Founder's Associate (3 new, 1 active)` with blank line spacing between sections.
- **Files affected:** references/presentation-rules.md
- **Verification criteria:** Results presentation has clear visual hierarchy between role type sections

**13. Persist task IDs in session-state.md**
- **What needs to change:** When dispatching background agents, write their task IDs to session-state.md so they survive context compaction.
- **Files affected:** CLAUDE.md (Session Management), references/orchestration.md (all dispatch sections)
- **Verification criteria:** After compaction, agent can poll background tasks using IDs from session-state.md

**14. Fix remaining constraint compliance gaps**
- **What needs to change:** HC-5 (add `list-active-role-types` to parent-allowed subcommands or delegate), HC-10 (add mandatory variables to dispatch templates), CR-7 (enforce absolute paths), CR-12 (add post-dispatch verification), startup git pull (add explicit step).
- **Files affected:** CLAUDE.md (Context Budget, Core Rules, ON STARTUP), references/orchestration.md
- **Verification criteria:** Next session's constraint compliance audit shows 0 failures on these items

## Solutions Extracted

1. **Self-correcting config format** — When CLI output is wrong, diagnose format mismatch, rewrite, re-validate. Transferable to any agent with format-sensitive config parsing.
2. **Parallel dispatch with live table** — Dispatch all items simultaneously, update table per completion. Works for any multi-item parallel workload.
3. **Sentinel recovery without data loss** — Create missing sentinels from existing output, then resume gates. Avoids discarding valid data on partial failure.
4. **Schema migration gate** — Validate → migrate → re-validate preserves data through format changes. Applicable to any pipeline with evolving output schemas.
5. **User-intent lookup before expensive dispatch** — When user references items by name, dispatch a lookup subagent first to find/validate before committing to expensive downstream work.
6. **Immediate scope-reduction acceptance** — When user asks to skip optional deliverables mid-run, accept and proceed without re-confirmation.
7. **Subagent writes initial status, parent appends post-action fields** — Clean separation for status file management after parent-executed actions (email send).

## Patterns Identified

1. **Schema Normalization Gate (Validate-Migrate-Revalidate)** — 3-step guard for schema drift. Appeared in V24 search→gates flow. Skill candidate: Yes.
2. **Parallel Dispatch with Live Progress Table** — Dispatch all, update table per completion, gate at end. Appeared in search (5 channels) and briefs (8 generators). Skill candidate: Yes.
3. **Failure Recovery with Re-dispatch (Detect-Check-Redispatch)** — Check partial output, redispatch (not inline), verify. Appeared in sentinel recovery, API error retry. Skill candidate: Yes.
4. **Config-Format Mismatch Detect-and-Fix Loop** — Run → diagnose → fix format → re-run. Appeared in context.md slug parsing. Skill candidate: No (too agent-specific).

## Build Metrics

- **Steps completed:** 29/29
- **Verification pass rate:** 29/29 (100%)
- **Regression count (new):** 0
- **Regression count (repeat):** 2 pre-existing (settings.local.json, orchestration.md model parameter)
- **Review cycles:** 2 (plan revised once before build)
- **Timing data:** Unavailable (phased-build step timing not yet enabled)
- **Session failures:** 15 (1 critical, 10 major, 4 minor)
- **Failure trend:** V22: 8 → V23: 20 → V24: 15 (25% reduction from V23, but still above V22 baseline)
- **New category:** ux-cli (5 findings) — first version to systematically track CLI UX issues

## Handoff Contract
- Architectural fixes: 2 — (1) decouple brief generation from briefs-html compilation, (2) token budget awareness / rate limit detection
- Implementation fixes: 14 — sentinel writes, schema validation, commit gate, session-state gate, preflight first-run, context.md format validation, post-compaction recovery, UX: one-liner progress, UX: proactive status, UX: post-compaction message, UX: unified numbered selection, UX: section headers with counts, task ID persistence, constraint compliance gaps
- New constraints: 0 (existing constraints sufficient; enforcement mechanism needs structural upgrade)
- Regression tests to include: sentinel file existence, schema validation pass, commit after search, session-state write after search, one-role-per-bullet format
- Prevention artifacts written: 2 reviewer prompt additions (data-integrity-guardian, deployment-verifier), 19 regression checklist entries
- Metrics recorded: V24 — 29/29 steps, 15 failures (1C/10M/4m), 100% verification pass rate

<!-- STAGE COMPLETE: /analyze, 2026-02-27 -->

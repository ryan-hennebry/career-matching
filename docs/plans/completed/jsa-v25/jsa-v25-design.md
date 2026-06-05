# Design: JSA V25 — Full Fix (Structural Gates + Delivery Decoupling + UX)

## Context

V24 achieved 25% failure reduction (20 → 15) via Schema-First Fix, but two chronic regressions (commit+push: 9th occurrence, session-state.md: 10th occurrence) persisted despite text constraints. Delivery phase hit rate limits when 8 brief-generators + briefs-html ran in the same session. A new UX/CLI failure category surfaced with 5 findings. V25 addresses the full backlog: 2 architectural fixes + 14 implementation fixes across three build layers.

**Research inputs:**
- V24 research: 7 agents, 7 skills, 8 scripts, 195 tests, 11 hard constraints, 5 search channels
- V24 analysis: 15 failures (1C/10M/4m) — 2 architectural + 14 implementation fixes
- V24 compound: 7 decisions, 7 solutions, 6 proposals
- Decision log: V18-V23 entries (6 prior versions)
- Regressions: 164 total entries across V14-V24

## Options Considered

### Option 1: Three-Layer (Infrastructure → Orchestration → UX)
- **Pros:** Proven in V21 (22/22 steps) and V23. Clean failure isolation by artifact type. Layer 1 tasks parallelizable. Each layer testable independently.
- **Cons:** Three phases add coordination overhead. Layer boundaries may need judgment calls for cross-cutting fixes.
- **Chosen**

### Option 2: Domain-Grouped (Data-Integrity → Subagent-Coord → UX)
- **Pros:** Domain-coherent — all data-integrity fixes together. Natural mental model.
- **Cons:** Cross-cutting artifact changes within each group (scripts + orchestration + CLAUDE.md in same group). Makes failure isolation harder than Three-Layer. No precedent in this codebase.
- **Rejected:** Cross-cutting artifact changes within domains reduce bisectability. Three-Layer has proven track record.

### Option 3: Single-Phase Enforcement Blitz
- **Pros:** Simplest — no phase coordination. V19/V20 succeeded with single-phase.
- **Cons:** V19/V20 were same-artifact-type (constraint text edits). V25 mixes code creation, text edits, and UX changes — three distinct artifact types. V21 showed single-phase fails for mixed artifacts.
- **Rejected:** Mixed artifact types need layer separation per V21 lesson. Single-phase only proven for same-artifact edits.

## Prototyping Results

Prototyping skipped — no triggers met. No new technology, no unverifiable external APIs, no 3+ component concurrent state management. All fixes extend existing patterns (manage_state.py, orchestration.md, gate-check agent).

## Chosen Approach

**Three-Layer (Infrastructure → Orchestration → UX)** — the proven pattern for mixed-artifact builds in this codebase (V21, V23).

## Architecture

### Layer 1: Scripts (Code)

Fix and extend scripts to provide structural enforcement:

1. **preflight.sh first-run detection** — Detect when no prior-run data exists (empty output/verified/). Skip safety bound checks on first run. Exit 0 instead of 1.

2. **manage_state.py `verify-and-commit`** — New subcommand that: (a) checks `git status --porcelain output/`, (b) if dirty: stages, commits with phase label, pushes, (c) if clean: exits 0, (d) on failure: exits 1. Gate-check agent dispatches this instead of parent doing git commands.

3. **manage_state.py `verify-session-state-written`** — New subcommand (or enhance existing `verify-session-state-updated`) to confirm session-state.md has today's date entry after each search batch.

4. **Search-verify agent sentinel enforcement** — Add `.done` sentinel write as mandatory final step in search-verify agent definition. Gate-check validates presence.

5. **Search-verify agent schema validation** — Add canonical 10-field schema validation as a pre-write step inside search-verify agent. Invalid output = agent exits with error, not silent write.

### Layer 2: Orchestration + Config

Wire structural gates and implement architectural changes:

6. **Structural commit gate at Phase 1 exit** — After each search channel completes, gate-check dispatches `verify-and-commit`. Blocks progression. No skip option.

7. **Structural session-state write gate at Phase 1 exit** — After each search channel, gate-check dispatches `verify-session-state-written`. Blocks progression.

8. **Tiered delivery (architectural fix #1)** — Phase 5 reordered:
   - Step 1: Generate briefs (brief-generator x N) — mandatory
   - Step 2: Dispatch digest-email — mandatory, first
   - Step 3: Parent sends email via send_email.py — mandatory
   - Step 4: Budget check — read dispatch counter from session-state.md
   - Step 5: If budget allows, dispatch briefs-html — optional tier
   - Step 6: If budget exhausted, log "deferred to next session" and skip

9. **Dispatch counter (architectural fix #2)** — Track total subagent dispatches in session-state.md `## Budget` section. Ceiling: 25 dispatches (configurable in CLAUDE.md). Before each dispatch, increment counter. Before optional work (briefs-html), check if at ceiling.

10. **Post-compaction recovery protocol** — Document in CLAUDE.md + orchestration.md:
    - On dispatch: persist task IDs in session-state.md `## Active Tasks`
    - Post-compaction: (a) print immediate 1-2 sentence status, (b) dispatch recovery subagent to read session-state.md + output status files, (c) parent uses structured summary to resume

11. **Constraint compliance fixes:**
    - HC-5: Add `list-active-role-types` to parent-allowed subcommands in CLAUDE.md Context Budget
    - HC-10: Add mandatory `working_dir`, `output_directory`, `dashboard_url` to all dispatch templates in orchestration.md
    - CR-7: Add explicit "state absolute file paths" reminders in orchestration.md output steps
    - CR-12: Add post-dispatch directory verification step after each subagent that writes files
    - Startup: Add explicit `git pull` step BEFORE preflight (separate from preflight's implicit pull)

12. **Context.md Target format validation** — After writing context.md Target section, orchestration requires running `list-active-role-types` and verifying output contains expected number of clean slugs.

13. **Task ID persistence** — All dispatch sections in orchestration.md include: "After dispatching, append task ID to session-state.md `## Active Tasks`."

### Layer 3: UX (Presentation)

Add UX Protocol section to orchestration.md:

14. **One-liner brief progress** — During parallel brief generation, print `Brief {N}/{total} done — {company name}` per completion. Full status table only once at end.

15. **Proactive timed status** — During background ops expected to take >2 minutes, check every 90 seconds and print: `Still running: {N}/{total} complete` or similar one-liner.

16. **Post-compaction immediate status** — First user-visible output after compaction must be a 1-2 sentence summary of completed/pending work. No silent file reads before status.

17. **Unified numbered selection** — When asking user to select jobs for briefs, include all eligible jobs (today's new + still-active from prior runs) in a single numbered list across all role types.

18. **Section headers with counts** — Each role type section gets: `## {Role Type} ({N} new, {M} active)` with blank line spacing between sections.

### Data Flow

```
Search channels (5 parallel)
    → gate-check: verify-and-commit (per channel)
    → gate-check: verify-session-state-written (per channel)
    → dispatch counter incremented in session-state.md

Verification + Dedup
    → gate-check: schema validation pass
    → gate-check: sentinel files present

Presentation
    → unified numbered selection (new + prior active)
    → section headers with counts

Delivery (tiered)
    → brief-generator x N (mandatory)
    → digest-email (mandatory, dispatched first)
    → send_email.py (mandatory)
    → budget check (dispatch counter vs ceiling)
    → briefs-html (optional, only if budget allows)

Post-compaction
    → immediate status message
    → recovery subagent reads session-state.md
    → resume from structured summary
```

## Design Approval Questions

1. **Hardest decision:** Delivery decoupling — tiered vs split-session vs pre-compiled. Tiered chosen because it's pragmatic (user always gets digest), doesn't require manual session restart, and aligns with existing Phase 5 structure. The dispatch counter ceiling (25) needs empirical tuning.

2. **Rejected alternatives:**
   - Domain-Grouped: Cross-cutting artifact changes reduce bisectability compared to Three-Layer.
   - Single-Phase: Mixed artifact types (code + config + UX) need layer separation per V21 lesson.
   - Split sessions for delivery: Requires manual restart; tiered approach is automatic.
   - Rate limit detection: Reactive rather than proactive; dispatch counter prevents the problem.
   - Filesystem-only recovery: Loses task ID information; persist + re-dispatch is more robust.

3. **Least confident aspect:** UX protocol compliance — the 5 UX rules in orchestration.md are text instructions the agent follows. If the agent doesn't follow them (like it didn't follow commit+push for 9 versions), we get the same problem. Unlike commit+push (which got script-enforced gates), UX output formatting is inherently harder to enforce structurally. Mitigation: clear, specific templates with exact format strings rather than vague guidelines.

## Success Criteria

1. **Failure count: <=10** (down from V24's 15 — 33% reduction)
2. **Zero chronic regression recurrence:** commit+push and session-state.md regressions must not recur
3. **Delivery completes:** Digest email always sent; briefs-html completed or gracefully deferred
4. **Gate effectiveness:** All structural gates fire and block on violation (zero gate skips)
5. **UX improvements observable:** One-liner progress, proactive status, numbered selection visible in session transcript

## Risks

1. **Dispatch counter ceiling (25) may be wrong** — Too low = agent stops too early. Too high = still hits rate limits. Mitigation: make ceiling configurable in CLAUDE.md, tune after V25 session.
2. **manage_state.py complexity** — Adding `verify-and-commit` to an 800+ line script increases maintenance burden. Mitigation: keep the new subcommand simple (10-15 lines of shell-out to git).
3. **UX rules may not be followed** — Text instructions for output formatting have lower enforcement than code gates. Mitigation: provide exact format strings, not vague descriptions.
4. **Three-layer coordination overhead** — Three build phases require more planning than single-phase. Mitigation: proven pattern (V21 22/22, V23 22/22); well-understood coordination model.

## Known Risks Passed to /plan

1. **UX protocol compliance risk** — `/plan` must define exact format strings for all 5 UX patterns (not "print progress" but the exact output format). Include a UX regression test that greps orchestration.md for format templates.
2. **Dispatch counter tuning** — `/plan` must include a step to set initial ceiling at 25 and document how to adjust. Include a test that validates the budget section exists in session-state.md schema.
3. **verify-and-commit edge cases** — `/plan` must handle: (a) nothing to commit, (b) push fails (auth), (c) merge conflict. Include error codes for each case.
4. **Layer 1 → Layer 2 dependency** — Layer 2 wires gates that call Layer 1 scripts. `/plan` must sequence Layer 1 before Layer 2 with explicit verification that Layer 1 commands work before Layer 2 integrates them.

## Handoff Contract

- Approach: Three-Layer (Infrastructure → Orchestration → UX)
- Components: Layer 1 (5 script fixes), Layer 2 (8 orchestration + config fixes), Layer 3 (5 UX protocol rules)
- Success criteria: <=10 failures, zero chronic regression recurrence, delivery always completes, all gates fire
- Risks requiring mitigation: UX compliance (exact format strings), dispatch counter tuning (configurable ceiling), verify-and-commit edge cases (error codes)
- Known risks for /plan: UX format string enforcement, dispatch counter initial value, verify-and-commit error handling, Layer 1→2 dependency sequencing

<!-- STAGE COMPLETE: /design, 2026-02-27 -->

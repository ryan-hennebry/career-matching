# Design: Job Search Agent V18 — Iteration 2

## Context

V18 iteration 1 built successfully (21/21 steps, 100% verification), but the first runtime session exposed 8 failures — all implementation-level. The analysis (jsa-v18-analysis.md) documented 8 specific fixes. The subsequent /research (full) confirmed the V18 codebase already partially addresses 3 of the 8 fixes (dedup uses domain:company:title, API keys pipe via stdin, session-state per-batch is a core rule). User chose to re-validate all 8 fixes rather than only the remaining gaps.

**From research handoff (iteration 2):**
- Files to modify: CLAUDE.md, scripts/manage_state.py, settings handling, test files
- Patterns to preserve: Named agent pattern, state management via CLI, design system, status file protocol, parent-sends-email
- Hard constraints: No PDF, no inline Python, no blue, no fabricated UI guidance, API keys via stdin only, additive settings.local.json, session-state per-batch, parent never reads source files directly
- Open questions: (1) Should V19 restructure given 64 cumulative regressions? (2) Pre-populate agent-memory from regressions? (3) Vercel Hobby 10s timeout sufficient?

**From decision log (V18 iteration 1):**
- Previously chose three-phase sequential (Infrastructure → Backend → Frontend) — appropriate for iteration 1 which mixed infrastructure, backend, and frontend changes
- Pre-flight script (preflight.sh) was the least confident aspect — acknowledged risk of brittleness

## Options Considered

### Option 1: Single Phase — All Constraints + Regression Tests
All 8 fixes in one phase. CLAUDE.md edits (5), script validation (1), test assertions (2). No phase coordination needed.

- Pros: Simplest structure; no phase coordination overhead; all changes land in one testable unit; fits the nature of the work (constraint additions and test assertions, not behavioral changes); independent fixes with no cross-dependencies
- Cons: ~8 files touched simultaneously; if one CLAUDE.md edit is incorrect, it ships with everything else
- Failure mode: A CLAUDE.md constraint worded too broadly could prevent legitimate parent operations (e.g., context budget too restrictive). Mitigated by including escape hatch language.
- **Chosen**

### Option 2: Two-Phase — CLAUDE.md Constraints vs Script/Test Hardening
Phase 1: CLAUDE.md changes (foreground-fallback, context budget, dashboard link, fabricated UI, settings.local.json, API key). Phase 2: Script changes (dedup validation, regression tests).

- Pros: Clean separation of prompt changes vs code changes; CLAUDE.md reviewable as single diff
- Cons: CLAUDE.md edits reference script behavior — testing prompts without corresponding test assertions is meaningless; adds 1 extra test cycle + commit checkpoint for no debuggability gain
- Failure mode: Phase 1 CLAUDE.md references "manage_state.py dedup" behavior that Phase 2 validates — if Phase 2 reveals an issue, Phase 1 may need re-editing
- **Rejected:** CLAUDE.md constraints and their regression tests are the same logical unit — splitting them adds coordination overhead without improving debuggability

### Option 3: Fix-by-Fix Sequential with Micro-Commits
8 mini-steps: implement fix, add test, commit. Each fix gets its own commit for git bisect traceability.

- Pros: Maximum traceability; easy git bisect; natural stopping points
- Cons: 8 separate commit cycles is significant overhead; CLAUDE.md gets 5 separate edits which may conflict; test suite runs 8 times; git bisect adds no value when changes are plain-text constraints
- Failure mode: CLAUDE.md edit 3 may conflict with edit 1 if they modify adjacent sections — more likely with 5 separate edits than 1 consolidated edit
- **Rejected:** Overkill for constraint text additions and test assertions — git bisect is valuable for behavioral code changes, not plain-text edits

## Prototyping Results

Prototyping skipped — no triggers met. All changes use existing technologies (Python CLI, CLAUDE.md constraints, pytest assertions). No new libraries, no concurrent state across 3+ components, no unverifiable external APIs.

## Chosen Approach

**Single Phase — All Constraints + Regression Tests**

All 8 fixes land in one phase because they share the same failure domain (constraint enforcement) and the same debugging workflow (read the diff, check the text). The three-phase split from iteration 1 was justified by three distinct failure domains (infrastructure, backend, frontend). Iteration 2 has one domain.

The 8 fixes decompose as:
1. **Foreground-fallback guard** — CLAUDE.md startup: dispatch trivial test agent, switch to foreground-only on denial
2. **Context budget section** — CLAUDE.md: explicit parent-allowed vs subagent-only operation list
3. **Dedup validation** — Verify manage_state.py dedup uses title+company, add regression test
4. **Dashboard link in terminal** — CLAUDE.md presentation workflow: add dashboard URL after job list
5. **Fabricated UI constraint** — CLAUDE.md: hard constraint against guessing Claude Code UI features
6. **API key handling validation** — Verify stdin piping, add regression test for no key echoing
7. **Additive settings.local.json** — CLAUDE.md: merge instructions + regression test
8. **Session-state per-batch validation** — Verify core rule exists, add regression test

## Architecture

### Single Phase: Constraint Enforcement + Regression Hardening

**Components:**

| Component | Responsibility | Fixes Addressed |
|-----------|---------------|-----------------|
| `CLAUDE.md` | Agent behavior constraints | 1 (foreground-fallback), 2 (context budget), 4 (dashboard link), 5 (fabricated UI), 6 (API key instruction), 7 (settings merge instruction), 8 (session-state enforcement) |
| `scripts/manage_state.py` | Dedup logic validation | 3 (dedup collision key) |
| Test files (pytest) | Regression assertions | 3, 6, 7, 8 (regression tests) |

**Data flow:**

1. Agent starts → reads CLAUDE.md → **foreground-fallback guard** dispatches a trivial test subagent (`echo ok` via Bash) → if tool denied, sets `DISPATCH_MODE=foreground` for all subsequent dispatches
2. **Context budget** section lists parent-allowed operations (Task dispatch, Read status/state files, Bash for git only, AskUserQuestion) and subagent-only operations (WebFetch, WebSearch, python3 scripts/, filter, summarize, Read source files)
3. After presenting ranked jobs, **dashboard link** step outputs: "View and manage all jobs at: {dashboard_url}" (reading URL from Vercel config or context.md)
4. **Fabricated UI constraint** in Hard Constraints section: "Never give instructions about Claude Code UI features unless 100% certain. If unsure, say 'I'm not sure — please check Claude Code documentation.'"
5. **Settings.local.json merge**: CLAUDE.md Step 22-23 instructions changed from "write settings file" to "read existing → parse JSON → merge new entries → write back"
6. **Regression tests**: pytest assertions verifying dedup collision key format, no API key patterns in bash command templates, settings.local.json merge preserves existing entries, session-state.md template includes per-batch checkpoint markers

**Interfaces:**
- Foreground-fallback guard: Sets a session variable (`DISPATCH_MODE`) read by all subsequent Task dispatches
- Context budget: Pure constraint text — enforced by the LLM reading CLAUDE.md, not by code
- Dashboard link: Reads `dashboard_url` from the same variable used by digest-email (Step 19)
- Settings merge: Python inline or jq — reads file, merges, writes back

**Dependencies:** None between the 8 fixes — all are independent and can be implemented in any order.

## Design Approval Questions

1. **Hardest decision:** Whether to add a proactive foreground-fallback guard (dispatch trivial test agent on startup) vs relying on the existing auto-retry protocol to handle tool denials reactively. Chose proactive because the V18 runtime wasted ~5 minutes and 4 dispatch cycles discovering background mode was broken — a 10-second upfront check saves minutes of reactive recovery. Rejected reactive-only because the auto-retry protocol retries the same dispatch mode instead of escalating to foreground.

2. **Rejected alternatives:** Two-phase (CLAUDE.md constraints and their regression tests are the same logical unit — splitting adds coordination overhead without debuggability gain). Micro-commits (git bisect adds no value for plain-text constraint edits — overkill for this work type).

3. **Least confident aspect:** The foreground-fallback guard's reliability. A trivial `echo ok` test agent may succeed while a real subagent with different tool requirements (WebFetch, Bash with specific commands) still gets denied. The guard validates "can dispatch subagents" but not "all tool types available in subagents." Would change approach if this proves insufficient: replace single upfront test with per-tool-type probes (one Bash test, one WebFetch test), or simply document that the guard catches the most common failure mode (background dispatch denial) while the auto-retry protocol handles tool-specific denials.

## Success Criteria

1. CLAUDE.md startup sequence includes foreground-fallback guard that dispatches a test agent and sets DISPATCH_MODE on failure
2. CLAUDE.md contains explicit Context Budget section listing parent-allowed vs subagent-only operations
3. `manage_state.py dedup` collision key verified as `{domain}:{company}:{title}` — regression test passes
4. CLAUDE.md presentation workflow includes dashboard URL output step after job list
5. CLAUDE.md Hard Constraints includes "no fabricated UI guidance" rule
6. CLAUDE.md API key handling uses stdin piping only — regression test verifies no key echoing patterns
7. CLAUDE.md settings.local.json instructions specify merge (read → parse → add → write), not overwrite — regression test verifies merge preserves existing entries
8. CLAUDE.md session-state per-batch rule confirmed in Core Rules — regression test verifies per-batch write instruction exists
9. All existing tests continue to pass (0 regressions)
10. `git diff` shows only constraint additions and test assertions — no behavioral code changes

## Risks

1. **Foreground-fallback false sense of security** — Test agent succeeds but real agents still fail due to tool-specific denials. Mitigation: Auto-retry protocol remains as second line of defense; guard catches the most common failure (background dispatch denial).
2. **Context budget too restrictive** — Edge cases where parent legitimately needs a tool marked "subagent-only." Mitigation: Include escape hatch: "If subagent dispatch fails 3x for the same operation, parent may execute directly with an explicit log message explaining why."
3. **CLAUDE.md growing too large** — 5 edits add ~50-80 lines. Current CLAUDE.md is already substantial. Mitigation: Consolidate where possible (merge context budget into existing Hard Constraints rather than adding a new section).
4. **Regression test brittleness** — Tests that grep CLAUDE.md for specific strings will break if instructions are reworded. Mitigation: Test for semantic patterns (e.g., "contains 'foreground' AND 'fallback'" rather than exact string match).

## Known Risks Passed to /plan

1. **Foreground-fallback guard implementation** — Plan must specify: what does the test agent dispatch look like? What tool does it test? How does it communicate DISPATCH_MODE to subsequent steps (environment variable? session-state field? in-context variable)?
2. **Context budget wording** — Plan must define the exact list of parent-allowed vs subagent-only operations and where this section goes in CLAUDE.md (new section vs merged into Hard Constraints).
3. **Settings.local.json merge mechanism** — Plan must specify: Python script? jq? Inline bash? The merge logic needs to handle both "file exists with content" and "file doesn't exist yet" cases.
4. **Regression test location** — Plan must specify which test files get new assertions and what exactly each assertion checks (string patterns? JSON structure? file existence?).

## Handoff Contract
- Approach: Single Phase — All Constraints + Regression Tests
- Components:
  - CLAUDE.md: 7 edits (foreground-fallback guard, context budget, dashboard link, fabricated UI constraint, API key instruction, settings merge instruction, session-state enforcement)
  - scripts/manage_state.py: validation + potential hardening of dedup collision key
  - Test files: 4+ regression assertions (dedup key, API key handling, settings merge, session-state per-batch)
- Success criteria: 10 measurable items (see Success Criteria section)
- Risks requiring mitigation: foreground-fallback false security, context budget restrictiveness, CLAUDE.md size growth, regression test brittleness
- Known risks for /plan: foreground-fallback implementation details, context budget wording/placement, settings.local.json merge mechanism, regression test file locations and assertion specifics

<!-- STAGE COMPLETE: /design, 2026-02-17 -->

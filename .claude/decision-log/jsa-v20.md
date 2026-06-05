# Decision Log: JSA V20

## Decisions

### Phase Structure: Single Phase vs Multi-Phase

- Chosen: Single Phase — all 13 fixes (scheduling + constraints + regression prevention) in one build session
- Rejected: Two-Phase (infrastructure + constraints) — scheduling fix is too small (one YAML file, ~5 changes) to warrant its own phase; adds coordination overhead without debuggability gain
- Rejected: Three Layers (Scheduling, Regressions, New Fixes) — heavyweight phase structure for what are mostly text constraint additions
- Rationale: V19 proved single-phase works for constraint-type fixes (14/14 steps, 101 tests pass). The scheduling fix is small enough to include alongside the 12 implementation fixes.
- Context: 13 total failures — 1 architectural (scheduling) + 12 implementation fixes. Most fixes are text constraint additions in the same failure domain.

### Regression Enforcement: Text Constraints vs Code/Assertion Enforcement

- Chosen: Upgrade from text constraints to code/assertion enforcement for the 4 regression recurrences (dedup, dashboard URL, incremental commit, agent memory)
- Rejected: Text constraints alone — V19 added text constraints for all 4 patterns; all 4 recurred in V20, proving text constraints are necessary but insufficient
- Rationale: The pattern is "text constraints -> code/assertion enforcement" for recurring failures. Active checks that STOP execution cannot be silently bypassed.
- Context: 4 failures had been "fixed" in prior versions but kept recurring. Each recurrence indicates a structural enforcement gap, not a missing constraint.

### Scheduling Fix: GitHub Actions Repair

- Chosen: Fix the existing GitHub Actions workflow (version path reference, timeout, permissions flag, inline settings, retry logic, preflight checks)
- Rejected: Alternative scheduling approaches (evaluated in V19 — this design carries forward the recommendation)
- Rationale: Lowest-effort path to fix scheduling. The 0% success rate was caused by fixable configuration issues rather than a fundamental architectural problem.
- Context: Scheduling is the single highest-impact fix — without it, the agent never runs autonomously.

### Regression Enforcement Confidence Level

- Chosen: Proceed with assertion-based enforcement while explicitly flagging durability risk
- Rationale: `manage_state.py` content-based dedup is genuine code enforcement. CLAUDE.md assertion steps (grep, git log, glob count) still rely on the agent following text instructions — acknowledged as least confident aspect.
- Context: Full code enforcement for all 4 regressions would require a pre-run validation script; scoped to V21 if V20 assertion-based enforcement fails again.

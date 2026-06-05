# Decision Log: Job Search Agent

## V18 — 2026-02-16

**Chosen:** Three-Phase Sequential (Infrastructure → Backend → Frontend)
**Reason:** Clean separation between three distinct failure domains (infrastructure, state logic, visual) enables independent testing and easy bisection of issues.

**Rejected:**
- Two-Phase (All Fixes → Visual Polish): Mixes infrastructure and state logic failure modes in Phase 1, making debugging harder if issues arise.
- Single Unified Phase: 15+ files across three domains with no isolation — impossible to bisect failures.

**Least confident:** Pre-flight validation script (preflight.sh) — checking Vercel API health requires knowing deployment URL, and checking GH Actions secrets isn't scriptable locally. May need to split into local-only and CI-only checks.

## V19 — 2026-02-17

**Chosen:** Single Phase — All Constraints + Regression Tests
**Reason:** All 8 fixes from V18 analysis are constraint additions and test assertions in the same failure domain — no benefit from phase isolation unlike V18 which mixed infrastructure, backend, and frontend.

**Rejected:**
- Two-Phase (CLAUDE.md vs Script/Test): CLAUDE.md constraints and their regression tests are the same logical unit — splitting adds coordination overhead without debuggability gain.
- Fix-by-Fix Micro-Commits: Git bisect adds no value for plain-text constraint edits — overkill for this work type.

**Least confident:** Foreground-fallback guard reliability — a trivial `echo ok` test agent may succeed while real subagents with different tool requirements still get denied. May need per-tool-type probes instead of single upfront test.

## V20 — 2026-02-18

**Chosen:** Single Phase — All 13 Fixes (scheduling + 12 implementation)
**Reason:** Scheduling fix is small (one YAML file, ~5 changes) — same failure domain as V19's constraint edits. Single-phase proven in V19 (14/14 steps). Key innovation is enforcement upgrade: text constraints → code/assertion enforcement for 4 recurring regressions.

**Rejected:**
- Two-Phase (Infrastructure + Constraints): Scheduling fix too small to warrant its own phase — adds coordination overhead without debuggability gain.
- Three Layers (Scheduling → Regressions → New Fixes): Heavyweight for text edits — regressions need enforcement mechanism changes, not separate build phases.

**Least confident:** Regression enforcement durability — CLAUDE.md assertion steps (grep, git log, glob count) still rely on agent following text instructions. Content-based dedup in manage_state.py is genuine code enforcement, but other assertions may still be skipped. If regressions recur in V20, V21 should add a preflight.sh validation script.

## V21 — 2026-02-18

**Chosen:** Three-Layer (Code Infrastructure → Constraint Promotion → Validation Harness)
**Reason:** V21's scope is fundamentally different from V19/V20 — it includes greenfield code (manage_state.py, preflight.sh), structural refactoring (CLAUDE.md decomposition from 677→~266 lines), and 10 compound proposal promotions. Three layers respect three distinct artifact types (code → text → validation) and provide clean failure bisection. Layer 1 tasks are parallelizable.

**Rejected:**
- Single Phase: V19/V20's single-phase approach was for constraint text edits. V21 mixes code creation, structural refactoring, and validation infrastructure — single phase makes failure isolation impossible.
- Two-Phase (Infrastructure + Constraints): Doesn't address V20's explicit flag for code-enforced validation (preflight.sh). Mixes code creation with structural refactoring in Phase 1, reducing bisectability.

**Least confident:** CLAUDE.md decomposition — extracting 411 lines of orchestration and presentation to references/ without breaking the agent's runtime behavior. Phase-based dispatch requires the agent to read reference files on-demand, adding a read-before-act dependency on every phase transition. Mitigation: preflight.sh validates reference files exist; dispatch table explicitly names files to load.

## V22 — 2026-02-23

**Chosen:** Checkpoint-Driven Architecture
**Reason:** Makes enforcement imperative (code gates) not declarative (text constraints) — 6 versions of escalating text constraints failed to prevent commit+push and session-state regressions.

**Rejected:**
- Incremental Hardening: Adds more gates the agent can skip — doesn't break the regression cycle after 6 recurrences.
- Pipeline Simplification: Loses V21's clean failure domain separation, would regress architecture without solving enforcement.

**Least confident:** claude-code-action@v1 reliability — v1.0 action with no production track record in this codebase. Mitigation: keep --print as commented-out fallback, test with workflow_dispatch, monitor first 3 runs.

## V23 — 2026-02-24

**Chosen:** Three-Layer (Scripts → Orchestration+Config → Validation)
**Reason:** Matches V21's proven three-layer pattern (22/22 steps). V23 mixes code creation (manage_state.py), text edits (CLAUDE.md, orchestration.md), and validation (preflight.sh) — three distinct artifact types requiring layer isolation. Tasks parallelizable within layers.

**Rejected:**
- Enforcement Layer (Single Phase): Mixes code creation with config edits — V21 showed single phase makes failure isolation impossible for mixed artifact types.
- Two-Layer (Code + Config): Conflates validation code (preflight.sh) with orchestration text edits, reducing bisectability within Layer 2.

**Least confident:** Model tiering savings estimate — <$1.00 target assumes Haiku search-verify quality is sufficient. If Haiku misses good jobs or produces garbage scores, would need to bump to Sonnet, reducing savings from ~70% to ~50%.

## V25 — 2026-02-27

**Chosen:** Three-Layer (Infrastructure → Orchestration → UX)
**Reason:** Proven pattern (V21 22/22, V23 22/22) for mixed-artifact builds. V25 mixes code creation (manage_state.py verify-and-commit), orchestration edits (structural gates, tiered delivery), and UX formatting — three distinct artifact types requiring layer isolation.

**Rejected:**
- Domain-Grouped (Data-Integrity → Subagent-Coord → UX): Cross-cutting artifact changes within domains reduce bisectability compared to Three-Layer.
- Single-Phase Enforcement Blitz: Mixed artifact types need layer separation per V21 lesson — single-phase only proven for same-artifact edits (V19/V20).

**Least confident:** UX protocol compliance — the 5 UX rules in orchestration.md are text instructions. Unlike commit+push (which got script-enforced gates), UX output formatting is inherently harder to enforce structurally. Mitigation: exact format strings, not vague guidelines.

## V26 — 2026-03-23

**Chosen:** Gate Chaining + Verification Infrastructure (Three-Layer build)
**Reason:** V25 analysis revealed constraints exist but agent ignores them (6-10 consecutive versions of same regressions). Core insight: text constraints fail because agent can skip them; code gates work when chained so skipping one blocks the next step. Builds genuinely missing verification tools (verify-before-archive, validate-presentation) + chains existing gates into mandatory sequences.

**Rejected:**
- Constraint Layering (Add More Text): 9-10 consecutive versions prove text constraints don't prevent regressions. Definitionally insanity.
- External Enforcement (Pre-commit/CI): Agent orchestration happens in-session, not CI. External checks can't prevent in-session violations.

**Least confident:** Gate chain bugs could block entire sessions if a gate has an edge case. Mitigated by --check-only flags and clear error messages.

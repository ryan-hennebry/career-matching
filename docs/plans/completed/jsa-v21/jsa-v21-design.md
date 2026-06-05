# Design: JSA V21 — Code Infrastructure + Structural Decomposition + Validation Harness

## Context

V20 build completed 15/15 steps with 100% verification pass rate, but runtime testing revealed 17 failures (6 critical, 5 major, 6 minor). The V20 analysis identified 3 architectural fixes, 10 implementation fixes, and the V20 compound doc produced 10 proposals for promotion. V20's decision log explicitly flagged: "If regressions recur in V20, V21 should add a preflight.sh validation script."

Key findings from V20:
- **Data integrity failures (F1, F7, F15-F17):** Pre-run cleanup destroys active job files; dedup misses cross-role duplicates; score threshold violated
- **Configuration failures (F2, F4):** Dashboard URL silently missing; background subagent permissions denied
- **Deployment failure (F3):** All 4 scheduled runs failed since Feb 13 — YAML heredoc indentation produces invalid JSON
- **Performance (F5, F14):** CLAUDE.md at 677 lines (2.7x the 250-line target); search-verify subagents take 40+ minutes due to excessive external company research
- **Context compaction (F6):** Parent fabricated findings from compacted summary instead of re-dispatching subagents

Sources: V20 analysis handoff contract, V20 research handoff contract, V20 compound proposals P1-P10, decision log V18-V20.

## Options Considered

### Option 1: Three-Layer — Code Infrastructure → Constraint Promotion → Validation Harness
- **How it works:** Layer 1 creates code artifacts (manage_state.py for cleanup/dedup, CLAUDE.md decomposition to references/, GH Actions config file). Layer 2 promotes 10 compound proposals into the decomposed structure (parent patterns → CLAUDE.md, subagent patterns → reference files) plus adds 10 implementation constraints. Layer 3 creates preflight.sh validation script with tiered enforcement.
- Pros: Each layer has a distinct artifact type (code → text → validation). Layer 3 directly addresses V20's explicit flag for preflight.sh. Clean bisection of failures. Layers 1 tasks are independent (parallelizable).
- Cons: Three layers is more coordination than V19/V20's single-phase approach. Most structurally ambitious JSA version.
- **Chosen**

### Option 2: Two-Phase — Infrastructure + Constraints
- Phase 1: Architectural fixes (manage_state.py, dedup refactor, CLAUDE.md decomposition). Phase 2: Implementation constraints (all 10 I-fixes + proposals).
- Pros: Clean separation between code changes and text changes.
- Cons: Misses the validation layer entirely. V20 explicitly flagged preflight.sh for V21 — two-phase doesn't address this. Mixes code creation (manage_state.py) with structural refactoring (CLAUDE.md decomposition) in Phase 1.
- **Rejected:** Doesn't address V20's explicit flag for code-enforced validation (preflight.sh). Two artifact types in Phase 1 reduces bisectability.

### Option 3: Single Phase — All Fixes Sequential
- All 13 fixes plus 10 proposals in one phase, ordered by dependency.
- Pros: Proven in V19 (14/14 steps) and V20 (15/15 steps). No phase coordination.
- Cons: V19/V20 had no code artifacts — they were constraint text edits. V21 creates new Python scripts, decomposes CLAUDE.md, and builds a validation harness. Mixing code creation with text edits in one phase makes failure bisection impossible. Blast radius too high for this scope.
- **Rejected:** V21's scope is fundamentally different from V19/V20 — it includes greenfield code, structural refactoring, and validation infrastructure. Single phase makes failure isolation impossible.

## Prototyping Results

Prototyping skipped — no triggers met. manage_state.py uses standard Python (os, json, glob) without new libraries. preflight.sh uses standard bash. CLAUDE.md decomposition is text refactoring. No new technology, no unverifiable external APIs, no concurrent state across 3+ components.

## Chosen Approach

**Three-Layer — Code Infrastructure → Constraint Promotion → Validation Harness**

This is the first JSA version that creates code enforcement artifacts (manage_state.py, preflight.sh) alongside structural refactoring (CLAUDE.md decomposition). The three-layer approach respects the three distinct artifact types and provides clean failure bisection. Each layer's success criteria are independently verifiable.

## Architecture

### Layer 1: Code Infrastructure (parallelizable)

Three independent tasks that can execute in parallel:

**1a. manage_state.py** — New Python CLI script for pre-run data hygiene
- Subcommands: `cleanup`, `dedup`, `pre-run` (alias for cleanup + dedup)
- `cleanup`: Removes temp/intermediate files only (output/raw/, output/search-results/, output/unverified/). NEVER touches verified/. Eliminates F1 entirely by removing the dangerous operation.
- `dedup`: Scans output/verified/* directories (filesystem as source of truth for roles). Cross-role dedup on `(company.lower().strip(), title.lower().strip())`. Keeps highest-scoring copy in verified/, archives lower-scoring duplicates to output/archive/. Also archives jobs scoring <70 (F9 score threshold enforcement as data quality rule).
- `--dry-run` flag on all subcommands for developer testing (not used in production — agent trusts the script's internal safety).
- Agent calls `python3 scripts/manage_state.py pre-run` once at session start. Fire-once pattern matching existing scripts (jobspy_search.py, filter_jobs.py).

**1b. CLAUDE.md Decomposition** — Reduce 677-line monolith to ~266-line compact orchestrator
- Extract orchestration workflow (325 lines, 48%) → `references/orchestration.md`
- Extract presentation workflow (86 lines, 13%) → `references/presentation-rules.md`
- Parent CLAUDE.md retains: Hard Constraints, Context Budget, Core Rules, ON STARTUP, Onboarding (stays inline — boot-time config, not a workflow phase), Constraint Derivation, Auto-Retry Protocol, Recovery Protocol, UX Rules, Session Management, Scheduled Runs, Security, Capabilities, Outputs
- Replace orchestration section with phase-based dispatch table (~15 lines):
  - 5 phases: Search → Verify → Dedup → Present → Deliver
  - Each phase: entry criteria, exit criteria, reference to load
  - Agent reads `references/orchestration.md § [Phase Name]` for step-level detail
- ON STARTUP updated to include: run preflight.sh, run manage_state.py pre-run, read context.md, derive constraints

**1c. GH Actions Config File** — Eliminate heredoc fragility
- Create `.github/jsa-config.json` as standalone JSON config
- Update `.github/workflows/daily-digest.yml` to read config from file (`config=$(cat .github/jsa-config.json)`)
- Delete heredoc JSON block from workflow YAML
- Eliminates F3 (all 4 scheduled runs failing since Feb 13) permanently

### Layer 2: Constraint Promotion + Proposal Integration (after Layer 1)

Two task groups executed after Layer 1 completes:

**2a. Parent-facing proposals → decomposed CLAUDE.md**
- P2 (Post-Compaction Redispatch) → Context Budget section
- P3 (Mandatory Variable Propagation) → Hard Constraints section
- P8 (Regression Enforcement Escalation) → add new section or append to Hard Constraints
- P10 (Post-Dispatch Directory Verification) → add to Core Rules or ON STARTUP

**2b. Subagent-facing proposals → reference files (append only)**
- P1 (Foreground Fallback Guard) → references/subagent-search-verify.md
- P4 (Idempotent Email Gate) → references/subagent-digest-email.md
- P5 (Incremental Session Checkpointing) → references/orchestration.md (each phase writes checkpoint JSON via Write tool; on entry, check for existing checkpoint to skip completed phases)
- P6 (Selective Cleanup via State.json) → references/orchestration.md (pre-run phase references manage_state.py)
- P7 (Heredoc JSON Validation) → N/A (eliminated by config file approach in Layer 1c)
- P9 (Zsh Safe Directory Cleanup) → references/orchestration.md

**2c. Implementation constraints (10 fixes)**
- I1 (Dashboard URL mandatory): Add to context.md `## Delivery` section + agent ON STARTUP validation
- I2 (GH Actions heredoc): Resolved by Layer 1c config file
- I3 (Missing permissions): Update .claude/settings.local.json with directory-level wildcard (`python3 scripts/*`, `bash scripts/*`)
- I4 (Post-compaction constraint): Covered by P2 in 2a
- I5 (Score threshold enforcement): Covered by manage_state.py dedup in Layer 1a
- I6 (Table format standardization): Add to references/presentation-rules.md
- I7 (Cross-role dedup normalization): Covered by manage_state.py dedup in Layer 1a
- I8 (Incremental commit enforcement): Add to references/orchestration.md per-phase instructions
- I9 (Read-before-Write on session-state): Add to CLAUDE.md Core Rules
- I10 (Subagent speed optimization): Update references/subagent-search-verify.md — keep full listing analysis for fit scoring, drop external company lookups (Crunchbase, hiring manager, funding rounds). Move deep company research to brief phase for top-scoring jobs only. Target <120s per job.

### Layer 3: Validation Harness (after Layer 2)

**3a. preflight.sh** — Tiered pre-session validation
- Critical checks (hard block — exit 1):
  - Dashboard URL present in context.md
  - .claude/settings.local.json has required permissions
  - .github/jsa-config.json is valid JSON
  - scripts/manage_state.py exists and is executable
- Non-critical checks (warn):
  - .claude/agent-memory/ files are non-empty
  - references/ files exist for all phases
  - No stale version references in GH Actions workflow
- Runs in both contexts: GH Actions workflow (before agent launch), agent ON STARTUP (for manual runs). Idempotent — double-run is harmless.

**3b. GH Actions workflow integration**
- Add `bash scripts/preflight.sh` step before agent launch step
- If preflight exits non-zero, workflow aborts (no Claude API call wasted)

### Data Flow

```
Session Start
  ├─ GH Actions: preflight.sh → abort if critical fail
  ├─ Agent ON STARTUP:
  │   ├─ preflight.sh → halt if critical fail
  │   ├─ manage_state.py pre-run
  │   │   ├─ cleanup: rm temp/intermediate dirs
  │   │   └─ dedup: scan verified/*, cross-role dedup, archive <70 scores, archive lower-scoring dupes
  │   ├─ Read context.md (validate Dashboard URL present)
  │   └─ Derive constraints
  │
  ├─ Phase 1: Search → Read references/orchestration.md § Search
  │   └─ Check checkpoint → dispatch search subagents → write checkpoint
  ├─ Phase 2: Verify → Read references/orchestration.md § Verify
  │   └─ Check checkpoint → dispatch verify subagents (moderate trim) → write checkpoint → git commit
  ├─ Phase 3: Dedup → Read references/orchestration.md § Dedup
  │   └─ Check checkpoint → run manage_state.py dedup (mid-session) → write checkpoint → git commit
  ├─ Phase 4: Present → Read references/presentation-rules.md
  │   └─ Check checkpoint → format tables (standardized) → user feedback → write checkpoint
  └─ Phase 5: Deliver → Read references/orchestration.md § Deliver
      └─ Check checkpoint → briefs → digest email (with dashboard URL) → write checkpoint → git commit
```

## Design Approval Questions

1. **Hardest decision:** Whether to create manage_state.py as a new standalone script vs keeping dedup logic inline in CLAUDE.md. Chose standalone script because inline dedup has failed across V17-V20 (F15, F16, F17 cross-role dedup misses) — text instructions can't enforce `(company.lower().strip(), title.lower().strip())` normalization consistently. A Python script provides deterministic dedup that the agent can't accidentally skip. Rejected alternative: inline CLAUDE.md dedup instructions — proven insufficient across 4 versions.

2. **Rejected alternatives:** Single Phase rejected because V21's scope is fundamentally different from V19/V20 (greenfield code + structural refactoring + validation infrastructure vs text constraint edits). Two-Phase rejected because it doesn't address V20's explicit flag for code-enforced validation (preflight.sh) and mixes code creation with structural refactoring in Phase 1, reducing bisectability.

3. **Least confident aspect:** CLAUDE.md decomposition — extracting 411 lines of orchestration and presentation to references/ without breaking the agent's runtime behavior. The agent currently reads CLAUDE.md as a monolith and has the full picture. Phase-based dispatch requires the agent to read reference files on-demand, adding a read-before-act dependency on every phase transition. If the agent fails to load the reference file or loads the wrong section, the phase executes without instructions. Mitigation: preflight.sh validates all reference files exist; each phase's entry criteria in the dispatch table explicitly names the file to load. Would change my mind if: testing shows the agent consistently fails to load referenced files despite explicit instructions.

## Success Criteria

1. manage_state.py `cleanup` removes only temp/intermediate files — verified/ untouched (regression test: count verified files before/after)
2. manage_state.py `dedup` detects cross-role duplicates via normalized `(company, title)` — test with known duplicate pair
3. manage_state.py `dedup` archives jobs scoring <70 — test with known below-threshold job
4. CLAUDE.md line count <=280 lines after decomposition (from 677)
5. references/orchestration.md contains all 23 workflow steps organized by 5 phases
6. references/presentation-rules.md contains all table formatting and presentation rules
7. Agent successfully loads reference files during phase transitions (manual test: run agent, verify it reads orchestration.md)
8. preflight.sh hard-blocks on missing dashboard URL, missing permissions, invalid JSON config
9. preflight.sh warns on empty agent memory, missing reference files
10. GH Actions workflow reads config from .github/jsa-config.json and produces valid JSON
11. Checkpoint files written after each phase with timestamp (P5 verification)
12. All 10 compound proposals placed in correct target files (4 in CLAUDE.md, 6 in reference files)
13. Subagent search-verify completes in <120s per job (moderate trim — no external company lookups)

## Risks

1. **CLAUDE.md decomposition breaks agent behavior** — Agent fails to load reference files during phase transitions, executing phases without instructions. Mitigation: preflight.sh validates reference files exist; dispatch table explicitly names files; test with manual run before scheduled deployment.
2. **manage_state.py has edge cases** — Dedup normalization misses edge cases (Unicode, special characters in company names). Mitigation: --dry-run for dev testing; archive not delete ensures recoverability.
3. **Phase-based dispatch loses step granularity** — Agent gets confused about which step within a phase to execute. Mitigation: orchestration.md preserves numbered steps within each phase section; agent reads the full phase section, not individual steps.
4. **Scope inflation** — V21 is the most ambitious JSA version. Risk of incomplete implementation. Mitigation: parallel execution within Layer 1 saves time; strict layer dependencies prevent partial states.
5. **P5 checkpointing adds complexity** — Agent must check for existing checkpoints on phase entry and write them on exit. If checkpoint logic is wrong, agent may skip phases or repeat them. Mitigation: checkpoint is a simple JSON file read/write; no complex state machine.

## Known Risks Passed to /plan

1. CLAUDE.md decomposition: reference file loading reliability — plan must include a manual verification step after decomposition
2. manage_state.py edge cases: plan must include test cases for Unicode company names, empty directories, missing state.json
3. Phase dispatch table format: plan must define exact syntax the agent follows to load the right reference section
4. Checkpoint recovery logic: plan must define what happens when a checkpoint exists but is corrupted or incomplete
5. Layer ordering: plan must enforce Layer 1 complete before Layer 2, Layer 2 before Layer 3

## Handoff Contract
- Approach: Three-Layer (Code Infrastructure → Constraint Promotion → Validation Harness)
- Components:
  - manage_state.py: pre-run CLI (cleanup, dedup, pre-run alias), scan dirs for roles, preserve verified, archive dupes + <70 scores
  - CLAUDE.md decomposition: extract orchestration + presentation to references/, phase-based dispatch table, ~266 lines target
  - GH Actions config: .github/jsa-config.json replaces heredoc
  - Proposal promotion: 4 parent proposals to CLAUDE.md, 6 subagent proposals to reference files (append only)
  - 10 implementation constraints across CLAUDE.md, references/, context.md, settings.local.json
  - preflight.sh: tiered validation (critical hard-block, non-critical warn), runs in GH Actions + agent ON STARTUP
  - P5 checkpointing: per-phase checkpoint JSON in references/orchestration.md instructions
  - P8 regression escalation: formalized via preflight.sh (text → code enforcement)
- Success criteria: 13 measurable items (see above)
- Risks requiring mitigation: 5 items (see above)
- Known risks for /plan: 5 items — reference loading reliability, manage_state.py edge cases, dispatch table syntax, checkpoint recovery, layer ordering
- Layer parallelism: Layer 1 tasks (1a, 1b, 1c) are independent — parallel execution allowed. Layers 2 and 3 are sequential after Layer 1.
- Deferred to V22: P5 granularity improvements (per-subagent timing), reference file restructuring (currently append-only)

<!-- STAGE COMPLETE: /design, 2026-02-18 -->

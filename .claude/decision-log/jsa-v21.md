# Decision Log: JSA V21

## Decisions

### Standalone Script vs Inline CLAUDE.md for Dedup
- Chosen: manage_state.py as a standalone Python CLI script
- Rejected: Inline dedup logic in CLAUDE.md — proven insufficient across V17-V20 (F15, F16, F17 cross-role dedup misses). Text instructions cannot enforce normalized `(company.lower().strip(), title.lower().strip())` consistently.
- Rationale: A Python script provides deterministic dedup that the agent cannot accidentally skip. Inline instructions have failed four consecutive versions.
- Context: Cross-role dedup failures were recurring regressions; text-based constraints cannot substitute for code enforcement when normalization precision is required.

### Three-Layer Architecture vs Two-Phase or Single Phase
- Chosen: Three-Layer — Code Infrastructure, Constraint Promotion, Validation Harness
- Rejected (Two-Phase): Omits the validation layer entirely, violating the explicit V20 flag for preflight.sh. Also mixes code creation with structural refactoring in Phase 1, reducing bisectability.
- Rejected (Single Phase): V21's scope is categorically different from V19/V20 — it includes greenfield Python code, structural CLAUDE.md refactoring, and validation infrastructure. Mixing these in one phase makes failure isolation impossible.
- Rationale: Three distinct artifact types (code, text, validation) map cleanly to three layers. Each layer's success criteria are independently verifiable. V20 explicitly flagged preflight.sh for V21.
- Context: V19/V20 used single phase successfully, but those were text-only constraint edits. V21 creates new scripts, restructures CLAUDE.md, and builds a validation harness — a fundamentally higher scope.

### CLAUDE.md Decomposition to Reference Files
- Chosen: Extract 411 lines (orchestration + presentation) to references/orchestration.md and references/presentation-rules.md, leaving a ~266-line compact orchestrator
- Rejected: Keeping CLAUDE.md as a 677-line monolith (2.7x the 250-line target)
- Rationale: Reduces token load on every session. Phase-based dispatch table replaces verbose inline steps. Agent reads reference files on-demand per phase.
- Context: CLAUDE.md at 677 lines was identified as a performance failure (F5) in V20 analysis.

### GH Actions Config File vs YAML Heredoc
- Chosen: Standalone .github/jsa-config.json file read by the workflow via `config=$(cat .github/jsa-config.json)`
- Rejected: Heredoc JSON block embedded in the YAML workflow file
- Rationale: YAML heredoc indentation produced invalid JSON, causing all 4 scheduled runs to fail since Feb 13 (F3). A standalone JSON file is validated by preflight.sh and eliminates the YAML/JSON quoting fragility entirely.
- Context: 100% scheduled run failure rate traced directly to heredoc indentation; this is a permanent structural fix.

### Tiered Validation in preflight.sh (Hard-Block vs Warn)
- Chosen: Two tiers — critical checks exit 1 (halt session), non-critical checks emit warnings only
- Rejected: Uniform treatment of all checks (all hard-block or all warn)
- Rationale: Missing dashboard URL, invalid permissions, and invalid config JSON are unrecoverable at runtime and waste Claude API calls if the session proceeds. Missing agent memory files and stale version references are recoverable warnings.
- Context: V20 failures included both unrecoverable config errors and soft warnings being conflated; tiered enforcement matches failure severity.

### Parallel vs Sequential Execution Within Layer 1
- Chosen: Tasks 1a (manage_state.py), 1b (CLAUDE.md decomposition), and 1c (GH Actions config) execute in parallel within Layer 1
- Rejected: Sequential execution across all layers and tasks
- Rationale: The three Layer 1 tasks have no dependencies on each other — they touch different files and different concerns. Parallel execution reduces build time for the most ambitious JSA version.
- Context: Scope inflation risk (V21 is the most ambitious version) makes time savings from parallelism especially valuable.

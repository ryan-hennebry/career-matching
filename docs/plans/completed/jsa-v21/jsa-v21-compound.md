# Compound: JSA V21

## Run Info
- Date: 2026-02-19
- Analysis: jsa-v21-analysis.md
- Decisions extracted: 6
- Solutions promoted: 7
- Instruction proposals: 10

## Metrics Regression Check

| Metric | V21 | V20 (baseline) | Delta |
|--------|-----|-----------------|-------|
| Failure count | 14 | 17 | -3 |
| Solutions promoted | 7 | 6 | +1 |
| Decisions extracted | 6 | 4 | +2 |

Failure count down 18% — V21 three-layer architecture reduced failures despite being the most ambitious JSA version (greenfield Python + CLAUDE.md restructure + validation harness). More decisions extracted reflects the higher architectural complexity of three-layer vs single-phase builds.

## Decisions Extracted

6 decisions logged to `.claude/decision-log/jsa-v21.md`:

1. **Standalone Script vs Inline CLAUDE.md for Dedup** — Code enforcement (manage_state.py) over text constraints after 4 consecutive versions of dedup failures
2. **Three-Layer Architecture** — Code Infrastructure / Constraint Promotion / Validation Harness, chosen for independent verifiability of three distinct artifact types
3. **CLAUDE.md Decomposition** — Extract 411 lines to reference files, reducing from 677 to ~266 lines for lower token load
4. **GH Actions Config File vs YAML Heredoc** — Standalone JSON eliminates YAML/JSON quoting fragility that caused 100% scheduled run failure
5. **Tiered Validation (Hard-Block vs Warn)** — Critical checks halt session, non-critical emit warnings only
6. **Parallel Execution Within Layer 1** — Three independent tasks run simultaneously to reduce build time

## Solutions Promoted

7 solutions across 4 domains:

| Solution | Domain | Status |
|----------|--------|--------|
| preflight-debug-pattern | configuration | proposed |
| search-redispatch-with-special-instructions | subagent-coordination | proposed |
| parallel-multi-source-dispatch | subagent-coordination | proposed |
| completion-sentinel-tail-check | subagent-coordination | proposed |
| verify-before-brief-guard | data-integrity | proposed |
| vercel-link-before-deploy | deployment | proposed |
| jsonl-transcript-recovery | uncategorized | proposed |

## Instruction Proposals

10 proposals written to `.claude/compound-proposals/jsa-v21.md`:

1. Preflight debug sequence — read script, read file, fix mismatch
2. Verify-before-brief guard — gate brief dispatch on verified JSON existence
3. Vercel link before deploy — always link before prod deploy on version transitions
4. Search redispatch with special instructions — career pages + domain queries when aggregator fails
5. Parallel multi-source dispatch — self-contained prompts for 3+ simultaneous search subagents
6. Completion sentinel tail check — `tail -3` verification before downstream dispatch
7. Standalone script for dedup — code enforcement over text constraints
8. JSONL transcript recovery — parser for pre-compaction content
9. Three-layer build architecture — when to use 1 vs 2 vs 3 build layers
10. Tiered preflight validation — hard-block vs warn classification

## Skill Extraction Candidates

| Pattern | Frequency | Domains | Recommendation |
|---------|-----------|---------|----------------|
| Completion Sentinel Verification | 3 | subagent-coordination | **extract** — Three independent rediscoveries (v17, v18, v21). Ready to codify. |
| Idempotency Gate via Status File | 2 | email-delivery | **extract** — Same pattern in v19 and v20. Generalizes beyond email. |
| Deduplication at Multiple Pipeline Layers | 3 | deduplication, data-integrity | **extract** — Three solutions across two categories. Multi-stage pipeline pattern. |
| Foreground Fallback for Denied Background Dispatch | 2 | subagent-coordination | **extract** — Same failure mode in v18 and v20. Actionable detection logic. |
| Post-Dispatch Output Verification | 2 | subagent-coordination, data-integrity | **monitor** — Needs one more instance before extracting. |
| Stateful Checkpointing for Resumability | 2 | data-integrity | **monitor** — Related but not identical enough yet. |
| Mandatory Variable Propagation | 2 | configuration | **monitor** — Partial overlap. Monitor for third instance. |

4 patterns extraction-ready, 3 monitoring.

<!-- STAGE COMPLETE: /compound, 2026-02-19 -->

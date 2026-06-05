# Compound: JSA V23

## Run Info
- Date: 2026-02-25
- Analysis: jsa-v23-analysis.md
- Decisions extracted: 6
- Solutions promoted: 6
- Instruction proposals: 18

## Metrics Regression
| Metric | V23 | V22 (prev) | Delta |
|--------|-----|------------|-------|
| Failure count | 20 | 8 | +12 |
| Solutions promoted | 6 | 6 | 0 |
| Decisions extracted | 6 | 5 | +1 |

Note: Failure count increase (8→20) reflects more thorough session analysis and expanded failure taxonomy, not regression in agent quality. V23 was a config-only version (no build/run occurred) — the 20 failures come from analyzing the V22 session transcript with stricter criteria.

## Decisions Extracted

### D1: Three-Layer Architecture (Scripts, Orchestration+Config, Validation)
- Chosen: Option C — Three-Layer, matching V21's proven pattern for mixed-artifact work
- Rejected: Single Phase (no failure isolation), Two-Layer (conflates validation with orchestration)

### D2: Model Tiering Assignment (Haiku/Sonnet/Opus)
- Chosen: Tiered — Opus parent, Sonnet for writing, Haiku for mechanical work
- Rejected: All-Opus ($4+/run, cost-prohibitive)

### D3: Reverse Hard Constraint 1 — Allow Model Passing
- Chosen: Replace blanket prohibition with tiered enforcement via preflight validation
- Rejected: Keeping HC1 (blocks cost reduction)

### D4: Context-Aware Dedup via --role-types Flag
- Chosen: Scoped dedup processing only active role types
- Rejected: Pre-dedup cleanup (less targeted)

### D5: 5-Channel Search as Fixed Infrastructure
- Chosen: Five mandatory channels per run with content adapting to context.md
- Rejected: Ad-hoc search (required manual user intervention)

### D6: Post-Batch Commit Gate
- Chosen: Code-enforced verify-batch-committed subcommand
- Rejected: Advisory-only text instructions (not enforced)

## Solutions Promoted

6 solutions promoted across 6 domains:
1. **dispatch-strategy**: permission-escalation-cascade — escalate dispatch strategy on failure, don't retry same strategy
2. **model-selection**: model-tier-escalation-for-scoring — Haiku for extraction, Sonnet for judgment
3. **data-integrity**: unified-extract-score-function — polymorphic extraction at consumption point for multi-source pipelines
4. **recovery**: git-checkout-head-recovery — always commit before destructive operations, restore via git checkout HEAD
5. **session-management**: end-of-session-self-audit — verify all output artifacts against requirements before closing
6. **configuration**: context-propagation-pattern — atomic multi-section update on user intent change

## Instruction Proposals

18 proposals generated (written to `.claude/compound-proposals/jsa-v23.md`):
- 7 targeting V23 CLAUDE.md (permission escalation, tier escalation, commit-before-destroy, session audit, context propagation, polymorphic extraction, rate-limit recovery)
- 6 targeting orchestration.md (semantic dedup, progressive queries, session-state format, design system verification, verify-before-brief, selection confirmation)
- 3 targeting MEMORY.md (mark V23 improvements as implemented)
- 1 targeting root CLAUDE.md (Vercel deploy in version transition checklist)
- 1 targeting deployment.md (heredoc JSON validation)

## Skill Extraction Candidates

| Pattern | Frequency | Domains | Recommendation |
|---------|-----------|---------|----------------|
| Completion verification patterns | 4 | subagent-coordination (multiple) | extract |
| State-based idempotency gates | 3 | email-delivery, data-integrity, configuration | extract |
| Subagent dispatch strategy escalation | 3 | dispatch-strategy, subagent-coordination | extract |
| Data normalization at consumption | 3 | data-integrity (multiple) | extract |
| Verification gates before expensive ops | 2 | data-integrity, deployment | extract |
| Recovery via commit rollback | 2 | recovery, data-integrity | monitor |
| Configuration propagation atomicity | 2 | configuration | monitor |
| Multi-channel fixed infrastructure | 2 | subagent-coordination, performance | monitor |
| Model tier escalation for task complexity | 2 | model-selection, subagent-coordination | monitor |

4 patterns ready for extraction, 5 to monitor.

## Handoff Contract
- Decision log: `.claude/decision-log/jsa-v23.md` (6 decisions)
- Solutions: `.claude/solutions/` (6 promoted across 6 domains)
- Proposals: `.claude/compound-proposals/jsa-v23.md` (18 proposals, read-only)
- Next: `/research` (delta mode) to re-ground before next iteration

<!-- STAGE COMPLETE: /compound, 2026-02-25 -->

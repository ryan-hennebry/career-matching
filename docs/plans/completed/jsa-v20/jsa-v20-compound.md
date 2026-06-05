# Compound: JSA V20

## Run Info
- Date: 2026-02-18
- Analysis: jsa-v20-analysis.md
- Decisions extracted: 4
- Solutions promoted: 6 (across 5 domains)

## Metrics Regression

| Metric | V20 | V19 | Delta |
|--------|-----|-----|-------|
| Failure count | 17 | 12 | +5 |
| Solutions promoted | 6 | 7 | -1 |
| Decisions extracted | 4 | 6 | -2 |

Note: Failure count increased because V20 analysis was more granular — it identified 6 critical, 5 major, and 6 minor failures including 4 regression recurrences from V19. The increase reflects improved detection rather than degraded quality. Solutions and decisions decreased slightly because V20 was a constraint-enforcement iteration (fixes to existing patterns) rather than an architectural exploration.

---

## Decisions Summary

4 decisions extracted covering: phase structure (single phase — all 13 fixes share one failure domain), regression enforcement (text constraints -> code/assertion enforcement for 4 recurrences), scheduling fix (repair existing GH Actions workflow), enforcement confidence (assertion-based with escalation path to preflight script in V21).

Full decision log: `.claude/decision-log/jsa-v20.md`

---

## Solutions Promoted

6 solutions promoted across 5 domains:

**subagent-coordination:**
- `foreground-fallback-guard` — detect tool denial on first dispatch, switch all subsequent subagents to foreground mode
- `post-compaction-redispatch` — re-dispatch subagents from scratch after compaction; never reconstruct from compacted summary

**data-integrity:**
- `selective-cleanup-via-state-json` — cross-reference state.json before pre-run cleanup; preserve files for still-active entities

**configuration:**
- `mandatory-variable-propagation` — mandatory config must fail loudly when missing; remove all silent null/empty fallbacks

**email-delivery:**
- `idempotent-email-gate` — check sent_at + run_date match before send; write both fields immediately after successful delivery

**deployment:**
- `heredoc-json-validation` — validate JSON immediately after heredoc expansion in CI to catch silent indentation errors

---

## Instruction Proposals

10 proposals generated targeting CLAUDE.md (4 proposals) and references/agent-patterns.md (7 proposals):

**Subagent Orchestration (3):** foreground fallback guard, post-compaction redispatch, post-dispatch directory verification
**Config Safety (1):** mandatory config validation with loud failures
**Delivery Resilience (2):** idempotent email gate, incremental session checkpointing
**Data/Cleanup Safety (2):** selective cleanup via state.json, zsh-safe directory cleanup
**CI/CD (2):** heredoc JSON validation, regression enforcement escalation path

Full proposals: `.claude/compound-proposals/jsa-v20.md`

---

## Skill Extraction Candidates

| Pattern | Frequency | Domains | Recommendation |
|---------|-----------|---------|----------------|
| Completion Sentinel Verification | 2 | subagent-coordination | extract |
| Idempotency Gate via Status File | 2 | email-delivery | extract |
| Multi-Layer Deduplication | 3 | deduplication, data-integrity | extract |
| Foreground Dispatch Fallback | 2 | subagent-coordination | extract |
| State File as Persistence Layer | 3 | data-integrity, configuration | monitor |
| Post-Dispatch Verification | 2 | subagent-coordination | monitor |
| Progressive Broadening + Filter | 1 | performance | monitor |
| JSON Validation at Write Time | 1 | deployment | monitor |

4 patterns meet extraction threshold; 4 under monitoring.

---

## Handoff Contract

- **Produced:** jsa-v20-compound.md, decision-log/jsa-v20.md, 5 solution domain files, compound-proposals/jsa-v20.md
- **Key context for next phase:** 17 failures (6 critical, 5 major, 6 minor), 10 actionable proposals ready, 4 skill extraction candidates ready for evaluation, regression enforcement escalation path documented
- **Next:** Run `/research` (delta mode) to re-ground, then user decides: `/design` for architectural changes or `/plan` for implementation fixes

<!-- STAGE COMPLETE: /compound, 2026-02-18 -->

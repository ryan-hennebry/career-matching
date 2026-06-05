# Compound: JSA V22

## Run Info
- Date: 2026-02-24
- Analysis: jsa-v22-analysis.md
- Decisions extracted: 5
- Solutions promoted: 6
- Instruction proposals: 10

## Metrics Regression Check

| Metric | V22 | V21 (baseline) | Delta |
|--------|-----|----------------|-------|
| Failure count | 8 | 14 | -6 |
| Solutions promoted | 6 | 7 | -1 |
| Decisions extracted | 5 | 6 | -1 |

Failure count dropped 43% (14 to 8) — the checkpoint-driven architecture significantly reduced regressions. Fewer solutions/decisions extracted reflects the narrower scope: V22 was an infrastructure hardening iteration (checkpoint gates, CI migration) rather than a greenfield architectural expansion like V21. The 3 critical failures remaining (missing 5-channel search, context-unaware dedup, missing post-batch commit gate) are all enforcement gaps, not design gaps — confirming the checkpoint architecture thesis.

## Decisions Extracted

5 decisions logged to `.claude/decision-log/jsa-v22.md`:

1. **Imperative over Declarative Enforcement** — Checkpoint gates instead of text constraints. 6 versions of declarative enforcement failed; imperative enforcement makes progress structurally impossible without passing gates.
2. **Preserve 5-Phase Pipeline** — Adding checkpoint gates at each transition rather than collapsing phases. V18 showed phase merging makes failure attribution 2-3x harder.
3. **manage_state.py Checkpoint Extension** — Single source of truth over separate scripts. Python testability over shell fragility.
4. **Native `background: true` Flag** — Replaces 4-version foreground-fallback workaround. SDK native support eliminates technical debt.
5. **claude-code-action@v1 for Scheduling** — Replaces `claude --print` after 100% failure rate since V20. Least-confident decision mitigated by 3-run confidence gate.

## Solutions Promoted

6 solutions promoted across 4 domains:

| Domain | Solutions |
|--------|----------|
| subagent-coordination | rate-limit-recovery, multi-channel-search-assembly, selection-confirmation-before-dispatch |
| data-integrity | recovery-subagent-for-data-corruption |
| configuration | ci-debug-read-then-fix-pattern |
| design-system | design-system-skill-preloading |

## Instruction Proposals

10 proposals written to `.claude/compound-proposals/jsa-v22.md`:

| # | Theme | Target |
|---|-------|--------|
| 1 | Checkpoint-driven phase gates | CLAUDE.md |
| 2 | Deprecate foreground-fallback; adopt `background: true` | CLAUDE.md |
| 3 | 5-channel search as mandatory infrastructure | references/orchestration.md |
| 4 | Tiered model assignment (Opus/Sonnet/Haiku) | CLAUDE.md |
| 5 | Run-scoped dedup with `--role-types` flag | references/orchestration.md |
| 6 | CI debug sequence pattern | CLAUDE.md |
| 7 | Scheduled runs: claude-code-action@v1 | MEMORY.md (manual) |
| 8 | Pre-dispatch selection confirmation | references/orchestration.md |
| 9 | Recovery subagent pattern | CLAUDE.md |
| 10 | Vercel project.json on version transition | CLAUDE.md |

## Skill Extraction Candidates

| Pattern | Frequency | Domains | Recommendation |
|---------|-----------|---------|----------------|
| Completion Verification & Handoff Signaling | 5 | subagent-coordination, data-integrity, testing | extract |
| Idempotency Gating via State Files | 3 | email-delivery, data-integrity, configuration | extract |
| Graceful Degradation via Fallback Paths | 3 | data-integrity, subagent-coordination, deployment | extract |
| Foreground Dispatch Recovery | 2 | subagent-coordination, configuration | monitor |
| Pre-Operation Validation & Guards | 3 | data-integrity, configuration, deployment | monitor |

3 patterns mature enough for extraction (completion verification, idempotency gating, graceful degradation). 2 patterns need further observation.

## Handoff Contract

**What was extracted:**
- 5 decisions in `.claude/decision-log/jsa-v22.md`
- 6 solutions in `.claude/solutions/{subagent-coordination,data-integrity,configuration,design-system}.md`
- 10 proposals in `.claude/compound-proposals/jsa-v22.md`
- 3 skill extraction candidates identified (none auto-extracted)

**Key insight:** V22's 43% failure reduction validates the checkpoint-driven thesis. The remaining 3 critical failures are all enforcement gaps (search breadth, dedup scoping, commit gating) — exactly the type of gap that checkpoint gates are designed to catch. V23 should close these by adding checkpoint assertions for each.

**Next step:** Run `/research` (delta mode) to re-ground against current state, then user decides: `/design` for architectural changes or `/plan` for implementation fixes.

<!-- STAGE COMPLETE: /compound, 2026-02-24 -->

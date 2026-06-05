# Compound: JSA V24

## Run Info
- Date: 2026-02-27
- Analysis: jsa-v24-analysis.md
- Decisions extracted: 7
- Solutions promoted: 7
- Proposals generated: 6

## Metrics Regression Check

| Metric | V24 | V23 (baseline) | Delta |
|--------|-----|-----------------|-------|
| Failure count | 15 | 20 | -5 |
| Solutions promoted | 7 | 6 | +1 |
| Decisions extracted | 7 | 6 | +1 |

Failure count decreased 25% (20 → 15). Schema-First Fix scope reduced cascading failures while maintaining solution/decision extraction volume.

---

## Decisions (7)

### 1. Schema Validation Approach
- **Chosen:** Simple Python dict validation in `manage_state.py` with `validate-schema` subcommand
- **Rejected:** Pydantic v2 or jsonschema library — overkill for 10 fields
- **Rationale:** Minimal dependency, same prevention of schema drift
- **Context:** Schema inconsistency was root cause of 4+ downstream failures

### 2. Scope: Targeted Patch vs Full Overhaul
- **Chosen:** Schema-First Fix — address only schema inconsistency and enforcement gaps
- **Rejected:** Full overhaul (cost + scheduling + all open questions) — too large
- **Rationale:** Highest-leverage root cause first; scheduling failed across 8 versions
- **Context:** V23 22/22 build but 20 interactive failures, all schema-traceable

### 3. Search-Verify Agent Model Tier
- **Chosen:** Promote search-verify from Haiku to Sonnet
- **Rejected:** Keep Haiku — insufficient reasoning for schema compliance
- **Rationale:** Correctness-first; normalize-on-write eliminates multi-path extraction
- **Context:** ~12x cost increase per search, but fixes cascading failures

### 4. Phase Gate Enforcement
- **Chosen:** Blocking gate-check prerequisites between phases
- **Rejected:** Advisory gates (status reporting only)
- **Rationale:** 3 chronic recurrences persisted 6-9 versions despite text constraints
- **Context:** V23 had 5 Critical failures traceable to skipped validation gates

### 5. Schema Normalization Strategy
- **Chosen:** Normalize on write (search-verify writes canonical schema immediately)
- **Rejected:** Normalize on read (validation spread across consumers)
- **Rationale:** Single validation point, no intermediate inconsistent data
- **Context:** Canonical 10-field JSON with single top-level `score` integer

### 6. Backward Compatibility
- **Chosen:** `migrate-schema` subcommand to normalize existing verified JSONs
- **Rejected:** Fresh start — would lose historical data
- **Rationale:** Continuity with V23 data, testable against actual JSONs
- **Context:** V23 verified JSONs across 5 channels need normalization

### 7. Background Dispatch Model
- **Chosen:** Keep background dispatch with comprehensive settings.local.json
- **Rejected:** Foreground-only — would lose parallelism
- **Rationale:** V23 evidence confirms it works; preflight validation + gate-check canary mitigate risk
- **Context:** 8 versions of historical failures, but V23 working implementation

---

## Solutions Promoted (7 across 6 domains)

| # | Solution | Domain | Status |
|---|----------|--------|--------|
| 1 | Self-correcting config format | configuration | proposed |
| 2 | Parallel dispatch with live table | dispatch-strategy | proposed |
| 3 | Sentinel recovery without data loss | recovery | proposed |
| 4 | Schema migration gate | data-integrity | proposed |
| 5 | User-intent lookup before expensive dispatch | dispatch-strategy | proposed |
| 6 | Immediate scope-reduction acceptance | ux-cli | proposed |
| 7 | Subagent writes initial status, parent appends | ipc | proposed |

New domain: `ux-cli` (first V24 contribution — UX/CLI issues tracked for first time in analysis).

---

## Instruction Proposals (6)

1. **Phase gates mandatory and blocking** — Add Core Rule 13 to CLAUDE.md
2. **Document validate-schema and migrate-schema** — Update Capabilities section
3. **Create references/verified-job-schema.md** — Canonical 10-field schema documentation
4. **Add startup gate-check canary** — Validate schema on Phase 1 resume
5. **Create references/schema-migration.md** — V23→V24 migration documentation
6. **Search-verify Sonnet tier** — Already implemented (no edit needed)

Full proposals: `.claude/compound-proposals/jsa-v24.md`

---

## Skill Extraction Candidates

| Pattern | Frequency | Domains | Recommendation |
|---------|-----------|---------|----------------|
| Status file idempotency gates | 3 | email-delivery, ipc, data-integrity | **Extract** |
| Subagent-parent handoff via sentinels | 4 | subagent-coordination, testing | **Extract** |
| Schema validate-migrate-revalidate | 2 | data-integrity, deployment | **Extract** |
| Model tier escalation for task difficulty | 2 | model-selection, subagent-coordination | Monitor |
| Config format recovery | 2 | configuration, data-integrity | Monitor |
| Parallel dispatch with progress feedback | 2 | dispatch-strategy, subagent-coordination | Monitor |
| Recovery via version control | 2 | recovery, configuration | Monitor |

2 patterns ready for extraction, 1 emerging extraction candidate, 4 under monitoring.

---

## Handoff Contract

**For next `/research` (delta mode):**
- 7 decisions logged at `.claude/decision-log/jsa-v24.md`
- 7 solutions promoted across 6 domains in `.claude/solutions/`
- 6 proposals at `.claude/compound-proposals/jsa-v24.md` (none auto-applied)
- 2 skill extraction candidates ready, 4 monitoring
- Key metric: failures dropped 25% (20 → 15) — schema-first approach validated
- New domain tracked: `ux-cli`

<!-- STAGE COMPLETE: /compound, 2026-02-27 -->

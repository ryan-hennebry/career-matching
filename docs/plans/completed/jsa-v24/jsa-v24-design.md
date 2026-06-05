# Design: JSA V24 — Schema-First Fix

## Context

V23 completed its full cycle (research → design → plan → review → build → analyze → compound). The build succeeded (22/22 steps, 165 tests), but the interactive session revealed 20 failures (5 Critical, 9 Major, 6 Minor). The single biggest root cause is **inconsistent verified JSON schemas across search channels**, which cascaded into 4+ downstream failures (dedup, digest builder, API endpoint, state sync). Additionally, 3 chronic recurrences (session-state updates, commit gates, channel dispatch verification) have persisted across 6-9 versions despite text-based constraints.

From V23 research handoff:
- 10 hard constraints, 13 manage_state.py subcommands, 5-phase checkpoint architecture
- Three-layer architecture (Scripts → Orchestration+Config → Validation) proven at 22/22 completion
- 143 regression items tracked across V14-V23
- 6 decisions and 6 solutions extracted from V23 compound

## Options Considered

### Option 1: Schema-First Fix (Targeted Patch)
- Fix verified JSON schema inconsistency as the single highest-leverage change
- Canonical schema with normalize-on-write approach
- Fix chronic enforcement gates with blocking gate-check prerequisites
- Fix scoring tier (Haiku → Sonnet)
- Pros: Low risk, targeted, builds on proven V23 infrastructure
- Cons: Doesn't address scheduling, cost guards, or open questions
- **Chosen**

### Option 2: Validation Layer Architecture (Pydantic/jsonschema)
- Formal schema validation using Pydantic v2 or jsonschema library
- Every search-verify agent validates output before write
- Pros: Permanent schema drift prevention, industry-standard validation
- Cons: Adds dependency, increases agent prompt complexity, overkill for 10 required fields
- **Rejected:** Pydantic adds unnecessary complexity for a 10-field schema. Simple Python dict validation in manage_state.py achieves the same result without a new dependency.

### Option 3: Structural Enforcement Overhaul (Gates + Schema + Cost + Scheduling)
- Everything from Option 2 plus cost guard, scheduled run architecture, all 5 open questions
- Pros: Addresses everything at once
- Cons: High risk, large scope, scheduling has failed 8 versions
- **Rejected:** Scope too large for a targeted iteration. Scheduling and cost guards are separate concerns that should be their own version. Fix the data integrity issues first.

## Prototyping Results

Prototyping skipped — no triggers met. All changes build on existing manage_state.py patterns and proven V23 infrastructure. No new technologies or libraries introduced.

## Chosen Approach

**Option 1: Schema-First Fix** — targeted patch addressing the root cause (schema inconsistency) and chronic enforcement gaps, using the proven Three-Layer implementation pattern.

## Architecture

### Components

1. **manage_state.py** — Schema validation, dedup fixes, slug extraction fix, migration script
   - New: `validate-schema` subcommand (checks 10 required fields on all verified JSONs)
   - Fix: `dedup` — replace `overall_score` references with canonical `score` field, auto-derive active role types via `list-active-role-types`
   - Fix: `list-active-role-types` — produce clean `[a-z0-9-]` slugs instead of full-sentence text
   - New: `migrate-schema` subcommand — normalize existing verified JSONs to canonical format
   - Fix: `_extract_score()` — simplify to read canonical `score` field (normalize-on-write eliminates multi-path extraction)

2. **Search-verify agent** — Promoted from Haiku to Sonnet tier, writes canonical schema
   - Agent frontmatter: `model: sonnet` (was `model: haiku`)
   - Prompt template: include canonical field list (10 required fields) as output contract
   - Score field: single top-level `score` integer, no nested variants

3. **Gate-check agent** — Blocking prerequisite between phases (existing, enhanced)
   - Phase 1 exit: verify session-state updated, verify all channels dispatched, verify batch committed
   - Gate-check success REQUIRED before parent proceeds — failure blocks phase transition
   - Orchestration.md updated to make gate-check dispatch mandatory, not advisory

4. **Orchestration.md** — Phase gate text updated for blocking semantics
   - Post-search: `validate-schema` gate added between search and dedup
   - Gate-check results read by parent — proceed only on success
   - Failure path: parent re-dispatches gate-check, does NOT skip

5. **Preflight.sh** — Schema validation added to startup checks
   - Verify `validate-schema` subcommand exists and runs
   - Verify search-verify agent frontmatter has `model: sonnet`

### Data Flow

```
Search-verify (Sonnet) → writes canonical JSON (10 required fields, score: int)
         ↓
Gate-check → validate-schema (all verified JSONs pass?)
         ↓ (blocked if validation fails)
Gate-check → verify-channels-dispatched (all 5 .done files?)
         ↓ (blocked if channels missing)
Gate-check → verify-session-state-updated
         ↓ (blocked if not updated)
Gate-check → verify-batch-committed
         ↓ (blocked if uncommitted)
Dedup (auto-scoped to active role types) → reads canonical 'score' field
         ↓
Present → reads canonical fields
         ↓
Deliver (digest/briefs) → reads canonical fields
```

### Canonical Verified JSON Schema

Required fields (ALL channels MUST produce these):
```json
{
  "job_id": "string",
  "title": "string",
  "company": "string",
  "job_url": "string",
  "role_type": "string",
  "score": 0,
  "source_channel": "string",
  "run_date": "YYYY-MM-DD",
  "location": "string",
  "status": "string"
}
```

Optional fields (channels may include):
- `salary`, `description`, `scoring_breakdown`, `requirements`, `preferred_qualifications`
- `user_profile_match`, `verification_notes`, `posted_date`
- Channel-specific fields (JobSpy raw data, etc.)

### Implementation Phases (Three-Layer)

**Layer 1: Scripts (manage_state.py)**
- `validate-schema` subcommand + tests
- Dedup bug fixes (score field, role-type auto-scoping, safety bound) + tests
- `list-active-role-types` slug extraction fix + tests
- `migrate-schema` subcommand + tests
- `_extract_score()` simplification

**Layer 2: Orchestration + Configuration**
- Search-verify agent: `model: haiku` → `model: sonnet` in frontmatter
- Search-verify prompt: canonical field list as output contract
- Orchestration.md: blocking gate-check semantics, validate-schema gate
- CLAUDE.md: update Agent Model Tiers table (search-verify → Sonnet)

**Layer 3: Validation + Preflight**
- Preflight.sh: validate search-verify model tier, validate-schema subcommand
- Integration tests: schema validation gate, dedup scoping, gate-check blocking
- Full test suite pass

## Design Approval Questions

1. **Hardest decision:** Background dispatch — whether to keep it (evidence says V23 fixed it) or remove it (analysis says 8 versions of failures). User chose to keep it based on V23 evidence, but flagged it as least confident aspect. Research confirmed V23 background dispatch worked with comprehensive settings.local.json.

2. **Rejected alternatives:**
   - Pydantic validation: adds unnecessary dependency for 10-field validation
   - Full overhaul: scope too large, scheduling is a separate concern
   - Normalize on read: spreads complexity to every consumer
   - Full union schema: harder to validate, preserves inconsistency
   - Explicit --role-types flag: orchestration failed to pass it in V22/V23
   - Foreground-only dispatch: loses parallelism, contradicts working V23 evidence
   - Fresh start (no migration): user chose migration script for backward compatibility
   - Two-layer phases: less bisectable than three-layer

3. **Least confident aspect:** Background dispatch reliability. Despite V23 evidence showing it works, the analysis documented 8 versions of failures and the user has experienced failures. /plan must include specific mitigation: (a) preflight validation that settings.local.json has all required tool permissions, (b) gate-check subagent as the first background dispatch (canary test), (c) clear fallback instructions if background fails.

## Success Criteria

1. **All verified JSONs pass schema validation** — `validate-schema` returns 0 for every JSON in output/verified/
2. **Dedup processes only active role types** — never archives >50% of jobs (safety bound), uses canonical `score` field
3. **Gate-checks block phase transitions** — session-state, commit, and channel gates are mandatory prerequisites
4. **Search-verify uses Sonnet tier** — agent frontmatter confirmed, preflight validates
5. **All 170+ existing tests pass** plus new tests for schema validation, dedup fixes, slug extraction, migration, and gate enforcement
6. **Successful interactive session** — all 5 channels complete, dedup works correctly, digest sends with correct scores, zero schema-related errors

## Risks

1. **Background dispatch may fail in fresh sessions** despite V23 evidence. Mitigation: preflight validates settings.local.json permissions, gate-check canary test, clear escalation path.
2. **Sonnet cost increase** — search-verify moves from Haiku ($0.25/$1.25) to Sonnet ($3/$15). With 5 channels, per-run search cost increases ~12x. Mitigation: search-verify prompt should be concise, limit tool use budget, and checkpoint frequently.
3. **Migration script may lose data** if old verified JSONs have fields not in canonical schema. Mitigation: migration preserves all original fields, only adds/normalizes the 10 required ones.
4. **Slug extraction fix** may change directory names, breaking references. Mitigation: migration handles directory renames, tests validate slug format.

## Known Risks Passed to /plan

1. **Background dispatch canary test** — /plan must include a step where gate-check is dispatched first as a background canary before the 5 search channels. If canary fails, provide clear fallback instructions.
2. **Sonnet cost estimation** — /plan must estimate per-run cost with Sonnet search-verify and compare against V22's $4.09 Opus baseline.
3. **Migration script edge cases** — /plan must test migration against actual V23 verified JSONs from `output/verified/` and `output/archive/`.
4. **Dedup safety bound** — /plan must define the exact threshold (>50% proposed) and the behavior when triggered (abort with error, not silent skip).

## Handoff Contract
- Approach: Schema-First Fix (targeted patch)
- Components: manage_state.py (validate-schema, dedup fix, slug fix, migration), search-verify (Sonnet), gate-check (blocking), orchestration.md (gate semantics), preflight.sh (validation)
- Success criteria: all tests pass + interactive session with zero schema errors
- Risks requiring mitigation: background dispatch canary, Sonnet cost, migration edge cases, dedup safety bound
- Known risks for /plan: background dispatch canary test, Sonnet cost estimation, migration edge cases, dedup safety bound threshold

<!-- STAGE COMPLETE: /design, 2026-02-25 -->

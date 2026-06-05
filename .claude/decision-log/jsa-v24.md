# Decision Log: JSA V24

## Decisions

### Schema Validation Approach
- **Chosen:** Simple Python dict validation in `manage_state.py` with a new `validate-schema` subcommand checking 10 required fields on all verified JSONs
- **Rejected:** Pydantic v2 or jsonschema library validation; adds unnecessary complexity and a new dependency for a small, fixed schema
- **Rationale:** Industry-standard validation is overkill for 10 required fields. A simple validation subcommand achieves the same schema-drift prevention without introducing dependencies
- **Context:** Schema inconsistency across search channels was the root cause of 4+ downstream failures (dedup, digest, API, state sync)

### Scope: Targeted Patch vs Full Overhaul
- **Chosen:** Option 1 — Schema-First Fix addressing only schema inconsistency and chronic enforcement gaps
- **Rejected:** Full structural overhaul (cost guards, scheduling, all open questions); scope too large and scheduling has failed across 8 versions
- **Rationale:** Fix the highest-leverage root cause first (data integrity), then scheduling and cost concerns as separate versions
- **Context:** V23 build was 22/22 but interactive session showed 20 failures, all traceable to schema inconsistency

### Search-Verify Agent Model Tier
- **Chosen:** Promote search-verify from Haiku to Sonnet tier for improved verification scoring and template-following accuracy
- **Rejected:** Keep Haiku tier; insufficient reasoning quality for consistent schema compliance
- **Rationale:** Sonnet provides better writing quality and reasoning for verification scoring; normalize-on-write eliminates multi-path extraction complexity
- **Context:** Moved from cost-first to correctness-first; per-run search cost increases ~12x but fixes cascading failures

### Phase Gate Enforcement
- **Chosen:** Make gate-check a mandatory blocking prerequisite between phases (not advisory), enforced by parent refusing to proceed on failure
- **Rejected:** Keep gates advisory; status reporting only without blocking
- **Rationale:** 3 chronic recurrences (session-state updates, commit gates, channel dispatch verification) persisted across 6-9 versions despite text-based constraints; blocking gates enforce the policy
- **Context:** V23 had 5 Critical failures, many traceable to skipped validation gates

### Schema Normalization Strategy
- **Chosen:** Normalize on write (search-verify agents write canonical schema immediately)
- **Rejected:** Normalize on read (spread validation logic to every downstream consumer)
- **Rationale:** Single point of validation reduces complexity and prevents intermediate consumers from working with inconsistent data
- **Context:** Canonical JSON schema defines 10 required fields with single top-level `score` integer field, eliminating multi-path score extraction

### Backward Compatibility
- **Chosen:** Include `migrate-schema` subcommand to normalize existing verified JSONs to canonical format, preserving all original fields
- **Rejected:** Fresh start without migration; would lose historical data
- **Rationale:** Maintains continuity with V23 data, allows testing against actual verified JSONs, reduces risk of regressions
- **Context:** V23 produced verified JSONs across 5 channels that must be normalized without data loss

### Background Dispatch Model
- **Chosen:** Keep background dispatch (`background: true` for all subagents) based on V23 evidence showing it works with comprehensive settings.local.json
- **Rejected:** Switch to foreground-only dispatch; would lose parallelism and contradicts V23 evidence
- **Rationale:** V23 background dispatch succeeded with proper permissions configuration; mitigate risk via preflight validation and gate-check canary test
- **Context:** Analysis documented 8 versions of failures but V23 evidence shows working implementation when settings are correct; user least confident aspect flagged for plan mitigations

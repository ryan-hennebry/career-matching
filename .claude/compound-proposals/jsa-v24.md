# Compound Proposals: JSA V24

## Proposal 1: Promote search-verify to Sonnet tier
- **Target:** `03_agents/tests/v24/CLAUDE.md` (Agent Model Tiers table)
- **Action:** modify
- **Rationale:** Decision log decision: "Search-verify agents need Sonnet for improved verification scoring accuracy and template-following; correctness-first approach justifies cost increase ~12x per run"
- **Proposed edit:**
  ```
  OLD (line 32):
  | Sonnet | `sonnet` | brief-generator, digest-email, briefs-html, onboarding, search-verify | Good writing quality and reasoning for verification scoring; template-following |

  NEW (no change — search-verify already in Sonnet tier ✓)
  ```
  **Status:** Already implemented in current CLAUDE.md. No edit needed.

---

## Proposal 2: Enforce phase gates as mandatory blocking prerequisite
- **Target:** `03_agents/tests/v24/CLAUDE.md` (Core Rules section)
- **Action:** add
- **Rationale:** Decision log decision: "3 chronic recurrences persisted across 6-9 versions despite text constraints; blocking gates enforce the policy at orchestration level"
- **Proposed edit:**
  Add as new **Core Rule 13** (after line 85):
  ```
  13. **Phase gates are mandatory and blocking.** Before proceeding between phases, run gate-check (parent refuses to proceed on failure). Gates validate: session-state.md updates, commit state, channel dispatch verification. No exceptions.
  ```

---

## Proposal 3: Document schema validation subcommand
- **Target:** `03_agents/tests/v24/CLAUDE.md` (Capabilities section)
- **Action:** modify
- **Rationale:** Decision log decision: "Add new `validate-schema` subcommand to manage_state.py to check 10 required fields on all verified JSONs, preventing schema inconsistency downstream"
- **Proposed edit:**
  ```
  OLD (line 222):
  - State management: `manage_state.py sync` for daily delta, `dedup` for cross-role dedup, `cleanup` for temp dirs

  NEW:
  - State management: `manage_state.py sync` for daily delta, `dedup` for cross-role dedup, `cleanup` for temp dirs, `validate-schema` for schema drift prevention, `migrate-schema` for backward compatibility
  ```

---

## Proposal 4: Document canonical JSON schema for verified jobs
- **Target:** Create `references/verified-job-schema.md`
- **Action:** create (new reference file)
- **Rationale:** Decision log decision: "Canonical JSON schema defines 10 required fields with single top-level `score` integer field, eliminating multi-path score extraction. normalize-on-write eliminates complexity"
- **Proposed edit:**
  ```
  Create new file: references/verified-job-schema.md

  Content:
  # Verified Job JSON Schema

  ## Canonical Format (V24+)

  All verified jobs MUST conform to this schema. Search-verify agents normalize on write.

  ### Required Fields (10)
  1. `job_id` (string) — unique identifier from source
  2. `title` (string) — exact title from listing
  3. `company` (string) — company name as written on their website
  4. `location` (string) — location from listing
  5. `url` (string) — job listing URL (extracted, never constructed)
  6. `description` (string) — full job description or summary
  7. `source` (string) — where found (jobspy channel or specialty source)
  8. `status` (string) — "active" or reason for rejection
  9. `verified_at` (ISO 8601 timestamp) — when verification completed
  10. `score` (integer) — composite score (0–100) with breakdown attached

  ### Score Object Structure
  ```json
  {
    "score": 87,
    "breakdown": {
      "required": 40,
      "preferred": 20,
      "experience": 15,
      "industry": 10,
      "location": 2
    },
    "math": "40 + 20 + 15 + 10 + 2 = 87"
  }
  ```

  ### Migration Rule
  - V23 and earlier verified JSONs MAY have multiple score fields or nested structures
  - `migrate-schema` subcommand normalizes these to canonical format
  - All new verified JSONs (V24+) MUST use canonical format on write
  ```

---

## Proposal 5: Add schema validation to startup checklist
- **Target:** `03_agents/tests/v24/CLAUDE.md` (ON STARTUP section)
- **Action:** add
- **Rationale:** Decision log: "Gate-check canary test validates schema before proceeding; mitigates risk of background dispatch with comprehensive settings"
- **Proposed edit:**
  ```
  OLD (after line 96):
  5. **Git pull (interactive mode only):** If `$SCHEDULED_RUN` NOT set, `git pull` and verify success BEFORE any file reads. Fail = stop.

  NEW (insert as new step 5):
  5. **Git pull (interactive mode only):** If `$SCHEDULED_RUN` NOT set, `git pull` and verify success BEFORE any file reads. Fail = stop.
  5b. **Gate-check canary (Phase 1 only):** If resuming Phase 1 after previous run, dispatch gate-check to validate existing verified JSONs conform to canonical schema. Failure = escalate.
  ```

---

## Proposal 6: Document backward compatibility migration strategy
- **Target:** `references/schema-migration.md`
- **Action:** create (new reference file)
- **Rationale:** Decision log decision: "include `migrate-schema` subcommand to normalize existing verified JSONs to canonical format, preserving all original fields"
- **Proposed edit:**
  ```
  Create new file: references/schema-migration.md

  Content:
  # Schema Migration (V24+)

  ## Background
  V23 and earlier produced verified JSONs with inconsistent schema across 5 search channels.
  Common issues: score stored as integer, float, or nested object; missing required fields; extra fields with no standard name.

  ## Migration Command
  ```bash
  python3 scripts/manage_state.py migrate-schema \
    --input-dir output/verified \
    --output-dir output/verified-migrated \
    --preserve-originals
  ```

  ## Process
  1. Scan all verified JSONs in `output/verified/`
  2. For each file:
     - Extract all fields from original (preserve)
     - Map to canonical 10 required fields
     - Normalize score to integer if needed
     - Validate against schema
  3. Write canonical JSON to output directory
  4. Log failures (schema violations, unrecoverable fields)

  ## Validation
  After migration, run:
  ```bash
  python3 scripts/manage_state.py validate-schema --dir output/verified-migrated
  ```

  ## No Data Loss
  All original fields preserved in `_original_data` field if not part of canonical schema.
  ```

---

## Summary

**Generated 6 proposals:**
- 1 already implemented (Sonnet tier — no edit needed)
- 5 actionable edits:
  - 2 to CLAUDE.md (add Core Rule 13, update Capabilities)
  - 2 new reference files (verified-job-schema.md, schema-migration.md)
  - 1 addition to ON STARTUP section

**Targets:**
- `03_agents/tests/v24/CLAUDE.md` (2 edits + 1 startup add)
- `references/verified-job-schema.md` (create)
- `references/schema-migration.md` (create)

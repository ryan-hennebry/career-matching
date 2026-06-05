# Compound Proposals: jsa V19

## Proposal 1: Add zsh-safe cleanup to ON STARTUP pre-run cleanup
- Target: `03_agents/tests/v19/CLAUDE.md` (and future versions)
- Action: modify
- Rationale: V19 analysis identified that `rm -f dir/*` fails silently on zsh when directories are empty (glob expansion error). The `find` pattern handles empty dirs gracefully. This affects the pre-run cleanup in ON STARTUP step 5.
- Source: `.claude/solutions/configuration.md` — `zsh-safe-cleanup-with-find`
- Proposed edit:
  In section **ON STARTUP**, step 5, replace:
  ```
  rm -f output/jobs/*
  rm -f output/verified/*/*
  rm -f output/briefs/*
  rm -f output/digests/*
  ```
  With:
  ```
  find output/jobs -type f -delete 2>/dev/null
  find output/verified -mindepth 2 -type f -delete 2>/dev/null
  find output/briefs -type f -delete 2>/dev/null
  find output/digests -type f -delete 2>/dev/null
  ```

## Proposal 2: Add post-dispatch directory verification to ORCHESTRATION WORKFLOW
- Target: `03_agents/tests/v19/CLAUDE.md` (and future versions)
- Action: add
- Rationale: V19 analysis found subagents sometimes write output to wrong directories (e.g., previous version dirs). A post-dispatch verification step catches this and recovers files. Should be a standard step after any subagent that writes file artifacts.
- Source: `.claude/solutions/subagent-coordination.md` — `post-dispatch-directory-verification`
- Proposed edit:
  Add to **AUTO-RETRY PROTOCOL** section, after rule 4:
  ```
  5. **Post-dispatch directory verification.** After a subagent completes, verify output landed in the expected directory. If the expected directory is empty but the subagent reported success, check fallback directories (e.g., previous version output dirs) and copy files to the correct location. Log: "Post-dispatch verification: found output in {fallback_dir}, copied to {expected_dir}."
  ```

## Proposal 3: Add presentation-layer dedup safety net to ORCHESTRATION WORKFLOW
- Target: `03_agents/tests/v19/CLAUDE.md` (and future versions)
- Action: add
- Rationale: V19 analysis found that slug-based dedup misses cross-role duplicates when filenames differ slightly. A second dedup pass at presentation time (Step 16) catches what the data-layer dedup (Step 13) misses.
- Source: `.claude/solutions/data-integrity.md` — `presentation-layer-dedup-safety-net`
- Proposed edit:
  Add after Step 13 (Cross-role-type deduplication), as a new sub-step:
  ```
  **Step 13b: Presentation-layer dedup safety net.**
  When building the Unified Selection View (Step 16), deduplicate by normalized (company + title) pair. If the same company+title appears in multiple role types after Step 13, keep only the highest-scoring instance. Log duplicates removed at this stage to session-state.md. This is a safety net — Step 13 should catch most duplicates, but slug normalization edge cases may slip through.
  ```

## Proposal 4: Add idempotency gate to email delivery in ORCHESTRATION WORKFLOW
- Target: `03_agents/tests/v19/CLAUDE.md` (and future versions)
- Action: modify
- Rationale: V19 analysis identified double-send risk on retry/re-run. The idempotency gate is already partially described in Step 20 pre-send gate (a), but should be elevated as a hard constraint to prevent any future regression.
- Source: `.claude/solutions/email-delivery.md` — `idempotency-gate-via-status-file`
- Proposed edit:
  This is already implemented in Step 20 pre-send gate (a). No change needed — marking as already-addressed. The existing text correctly checks `_status.json` for `sent_at` before sending.

## Proposal 5: Add incremental session-state checkpointing to CORE RULES
- Target: `03_agents/tests/v19/CLAUDE.md` (and future versions)
- Action: modify
- Rationale: V19 decision log chose incremental checkpointing per batch (not just end-of-session). This is already codified in Core Rule 10 and Step 11, but the decision should be reflected in the solutions as "implemented" status.
- Source: `.claude/solutions/data-integrity.md` — `incremental-session-state-checkpointing`
- Proposed edit:
  Already implemented in Core Rule 10 and Step 11. Update solution status from `proposed` to `implemented` in `.claude/solutions/data-integrity.md`.

## Proposal 6: Update solution statuses to reflect V19 implementations
- Target: `.claude/solutions/configuration.md`, `.claude/solutions/subagent-coordination.md`, `.claude/solutions/data-integrity.md`, `.claude/solutions/email-delivery.md`
- Action: modify
- Rationale: Several solutions proposed across V17-V19 are now implemented in the V19 CLAUDE.md. Their status should be updated from `proposed` to `implemented` to prevent redundant re-proposal in future compound cycles.
- Proposed edits:
  - `.claude/solutions/subagent-coordination.md`:
    - `foreground-dispatch-recovery`: `proposed` -> `implemented` (V19 ON STARTUP step 2b)
    - `completion-sentinels-for-verification`: `proposed` -> `implemented` (V19 Step 18 sentinel check)
    - `batched-dispatch-with-checkpoints`: `proposed` -> `implemented` (V19 Step 10-11)
  - `.claude/solutions/data-integrity.md`:
    - `semantic-dedup-over-slugs`: `proposed` -> `implemented` (V19 Step 13 uses manage_state.py dedup on title+company)
    - `incremental-session-state-checkpointing`: `proposed` -> `implemented` (V19 Core Rule 10, Step 11)
  - `.claude/solutions/email-delivery.md`:
    - `idempotency-gate-via-status-file`: `proposed` -> `implemented` (V19 Step 20 pre-send gate)
  - `.claude/solutions/configuration.md`:
    - `git-add-force-for-ci-files`: `proposed` -> `implemented` (V18 build)

## Proposal 7: Add subagent return-message fallback to RECOVERY PROTOCOL
- Target: `03_agents/tests/v19/CLAUDE.md` (and future versions)
- Action: add
- Rationale: V19 analysis found that subagents sometimes complete work and return useful data in the Task tool return message, but fail to write the expected file artifact (e.g., `_summary.md`). The recovery protocol should check the return message as a data source before dispatching a recovery subagent.
- Source: `.claude/solutions/subagent-coordination.md` — `subagent-return-message-as-fallback`
- Proposed edit:
  In **RECOVERY PROTOCOL**, add as step 1 (shifting existing steps to 2-5):
  ```
  1. **Check subagent return message.** If the subagent's Task tool call returned a structured result (e.g., job counts, summaries), use that data to construct the missing `_status.json` or `_summary.md` directly. This avoids dispatching a recovery subagent when the data is already in the parent context from the return message.
  ```

## Proposal 8: Record V19 settings.local.json merge decision in CLAUDE.md cross-version memory
- Target: `CLAUDE.md` (root project instructions)
- Action: add
- Rationale: The V19 decision to use merge semantics (not overwrite) for settings.local.json is an important cross-version pattern. It is already codified in the V19 agent CLAUDE.md (SCHEDULED RUNS section) but should be referenced in the root CLAUDE.md cross-version memory section to ensure future agent versions inherit it.
- Proposed edit:
  This is already well-codified in the V19 agent CLAUDE.md SCHEDULED RUNS section ("settings.local.json write protocol"). No root CLAUDE.md change needed — the pattern lives correctly at the agent level. Mark as already-addressed.

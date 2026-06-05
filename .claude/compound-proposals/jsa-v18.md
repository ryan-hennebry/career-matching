# Compound Proposals: jsa V18

## Proposal 1: Add foreground dispatch recovery rule
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v18/CLAUDE.md`
- Action: modify
- Rationale: Solution `foreground-dispatch-recovery` (from v18 analysis) addresses a recurring failure where background subagents get tool permissions auto-denied. The AUTO-RETRY PROTOCOL currently only retries as another subagent dispatch but does not specify switching to foreground. Adding this as an explicit escalation step prevents repeated failures from the same dispatch mode.
- Proposed edit:
  In `## AUTO-RETRY PROTOCOL`, after item 2 ("Second failure: Log the error..."), add:

  ```
  2b. **Foreground escalation:** If the first retry also fails due to tool denial (Bash auto-denied), re-dispatch as a foreground subagent. Foreground subagents can receive interactive permission approvals. This is a one-time escalation — if foreground also fails, log and continue.
  ```

## Proposal 2: Add semantic dedup rule to CORE RULES
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v18/CLAUDE.md`
- Action: modify
- Rationale: Solution `semantic-dedup-over-slugs` (from v18 analysis) addresses a failure where filename-based dedup misses duplicates with slight title variations. The dedup CLI in Step 13 currently operates on filenames. Adding a note to the dedup step ensures the CLI or a follow-up check normalizes on title+company fields rather than relying solely on slugified filenames.
- Proposed edit:
  In `## ORCHESTRATION WORKFLOW`, Step 13, after "Never write inline python3 -c for dedup -- use this CLI subcommand only.", add:

  ```
  - **Semantic dedup:** If filename-based dedup misses duplicates (same company + similar title with slug variations), dedup on normalized title+company fields inside the JSON. Keep the highest-scoring version. The dedup CLI should handle this; if it does not, file a bug for `manage_state.py dedup`.
  ```

## Proposal 3: Add progressive query broadening to search strategy
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v18/CLAUDE.md`
- Action: modify
- Rationale: Solution `progressive-query-broadening` (from v18 analysis) addresses near-zero results from narrow industry-specific queries. Search-verify agents should start with broad terms and filter programmatically. This is a dispatch-level instruction that belongs in the parent CLAUDE.md so the correct variables are passed.
- Proposed edit:
  In `## ORCHESTRATION WORKFLOW`, Step 9 (Prepare 14 template variables), add after the `industry_qualifiers` bullet:

  ```
  - **Query strategy:** Instruct search-verify agents to start with broad role-title queries (e.g., "Marketing Associate"), NOT industry-qualified queries (e.g., "crypto marketing associate"). Industry filtering happens post-retrieval via `industry_qualifiers`. Narrow queries yield near-zero results on most boards.
  ```

## Proposal 4: Add idempotency gate to email delivery
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v18/CLAUDE.md`
- Action: modify
- Rationale: Solution `idempotency-gate-via-status-file` (from v18 analysis) is already partially implemented in Step 20 (pre-send gate check a). This proposal confirms the pattern is in place and proposes no change — the existing CLAUDE.md already covers this. No edit needed.
- Proposed edit: None. Already implemented in Step 20a.

## Proposal 5: Add Vercel project.json reuse to deployment knowledge
- Target: `/Users/ryanhennebry/Projects/autonomous1/.claude/agent-memory/deployment/MEMORY.md` (create if not exists)
- Action: add
- Rationale: Solution `vercel-project-json-reuse` (from v18 analysis) is a deployment pattern that should be recorded in agent memory so future version transitions reuse the `.vercel/project.json` rather than reconfiguring DNS.
- Proposed edit:
  Create or append to deployment memory:

  ```markdown
  ## Vercel Version Transitions
  - When deploying a new version directory to Vercel, copy `.vercel/project.json` (with existing project/org IDs) from the previous version directory. Then run `npx vercel --prod --yes`. This avoids DNS and project reconfiguration.
  - Never create a new Vercel project for a version bump — reuse the existing project binding.
  ```

## Proposal 6: Add completion sentinel verification to HARD CONSTRAINTS
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v18/CLAUDE.md`
- Action: modify
- Rationale: Solutions `sentinel-based-completion-verification` and `completion-sentinels-for-verification` (from v17 and v18 analyses) describe a pattern already partially used in Step 18 (brief sentinel check). Elevating this to a HARD CONSTRAINT ensures ALL subagent outputs are sentinel-verified, not just briefs.
- Proposed edit:
  In `## HARD CONSTRAINTS`, add as item 6:

  ```
  6. **Verify completion sentinels on all subagent outputs.** Every subagent must write a completion sentinel (e.g., `<!-- BRIEF COMPLETE -->`, `"status": "complete"` in _status.json). Parent verifies sentinel presence before proceeding. Missing sentinel = failed subagent.
  ```

## Proposal 7: Add post-render HTML verification to HARD CONSTRAINTS
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v18/CLAUDE.md`
- Action: modify
- Rationale: Solution `post-render-html-verification` (from v18 analysis) describes grepping for prohibited visual patterns in generated HTML. Step 19b already covers this partially but only checks specific color values. Elevating the principle (gate delivery on verification) ensures it is not skipped.
- Proposed edit:
  Step 19b already exists and covers this. No additional edit needed — the current implementation is sufficient. If future failures show Step 19b being skipped, elevate to HARD CONSTRAINTS.

## Proposal 8: Add batched dispatch checkpointing rule
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v18/CLAUDE.md`
- Action: modify
- Rationale: Solution `batched-dispatch-with-checkpoints` (from v17 analysis) recommends splitting subagents into batches of 2 with commits between batches. Step 10 already says "sequential batches of 2-3" and Step 11b commits after each batch. The existing CLAUDE.md already implements this pattern. No edit needed.
- Proposed edit: None. Already implemented in Steps 10, 11, and 11b.

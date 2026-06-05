# Compound Proposals: JSA V23

## Proposal 1: Add Permission Escalation Cascade to Auto-Retry Protocol
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/CLAUDE.md`
- Action: modify
- Rationale: Solution `permission-escalation-cascade` (dispatch-strategy.md) documents that on subagent permission failure, the agent should escalate the dispatch strategy rather than retrying the same approach. The current Auto-Retry Protocol simply says "retry once as subagent dispatch" without changing anything about the dispatch. V23 analysis confirmed this pattern: each retry must change the strategy, not repeat it.
- Proposed edit:
  In section `## Auto-Retry Protocol`, replace:
  ```
  1. **First failure:** Retry once as subagent dispatch (Task tool) — never inline in parent.
  2. **Second failure:** Log error, continue with remaining work. Do NOT retry again.
  3. **Never retry more than once per subagent per run.**
  4. **Never retry inline in parent.** All retries through Task tool dispatch.
  ```
  With:
  ```
  1. **First failure:** Retry once as subagent dispatch (Task tool) — never inline in parent. Each retry MUST escalate the dispatch strategy (e.g., add broader permission wildcards, switch from background to foreground). Never retry with identical parameters.
  2. **Second failure:** Log error, continue with remaining work. Do NOT retry again.
  3. **Never retry more than once per subagent per run.**
  4. **Never retry inline in parent.** All retries through Task tool dispatch.
  ```

## Proposal 2: Escalate Haiku to Sonnet for Scoring/Judgment Tasks in Model Tiers
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/CLAUDE.md`
- Action: modify
- Rationale: Solution `model-tier-escalation-for-scoring` (model-selection.md) documents that Haiku produces inflated/unreliable scores on judgment tasks like profile-matching evaluation. The V23 analysis confirmed the decision boundary: literal matching = Haiku, contextual judgment = Sonnet+. The current Agent Model Tiers table assigns Haiku to search-verify without noting this nuance.
- Proposed edit:
  After the Agent Model Tiers table, add a new subsection:
  ```
  **Tier escalation rule:** If a Haiku-tier subagent produces scoring or semantic evaluation output (e.g., fit scores against a rubric), and the scores appear inflated or unreliable, escalate that subagent to Sonnet for subsequent dispatches. Haiku is sufficient for mechanical extraction (fetch pages, parse fields, filter by keyword). Contextual judgment tasks (scoring against a multi-factor rubric, evaluating requirement match quality) require Sonnet at minimum.
  ```

## Proposal 3: Add Commit-Before-Destructive-Operation Rule
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/CLAUDE.md`
- Action: add
- Rationale: Solution `git-checkout-head-recovery` (recovery.md) documents that after a destructive operation (e.g., dedup archiving all files), recovery depends on restoring from the last git commit. This requires a commit BEFORE the destructive operation. The current CLAUDE.md has no explicit rule mandating pre-destructive-operation commits. Decision D6 (post-batch commit gate) partially addresses this but only for batch boundaries, not for arbitrary destructive operations.
- Proposed edit:
  In section `## Core Rules`, add new rule:
  ```
  13. **Commit before any bulk file operation.** Before any operation that deletes, moves, or archives files in bulk (dedup, cleanup, pre-search archival), ensure a git commit exists with the current state. This enables `git checkout HEAD -- <path>` recovery if the operation produces unexpected results. (V23 recovery pattern.)
  ```

## Proposal 4: Add End-of-Session Self-Audit to Session Management
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/CLAUDE.md`
- Action: modify
- Rationale: Solution `end-of-session-self-audit` (session-management.md) documents that long sessions accumulate incremental drift that is invisible in the moment but detectable through a systematic final pass. The current Session Management section has no audit step.
- Proposed edit:
  In section `## Session Management`, append:
  ```
  **End-of-session audit (MANDATORY for interactive mode):** Before closing a session that produced output artifacts, audit all outputs against documented requirements:
  - Check `_status.json` files for missing fields or stale data
  - Verify `session-state.md` reflects all phases completed
  - Confirm `state.json` run_date matches the session's run date
  - Check for bloated or orphaned files in `output/`
  Log any drift found in session-state.md under a `## Session Audit` heading.
  ```

## Proposal 5: Add Context Propagation Rule to Onboarding
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/CLAUDE.md`
- Action: modify
- Rationale: Solution `context-propagation-pattern` (configuration.md) documents that when a user changes search criteria, all dependent sections must be updated in a single pass. The V23 analysis confirmed this: partial updates to context.md caused downstream failures when only some sections reflected the new criteria.
- Proposed edit:
  In section `## Onboarding`, after step 11, add:
  ```
  **Context propagation rule (MANDATORY):** When the user changes their target focus (roles, industries, or constraints), update ALL dependent sections of context.md in a single atomic pass: `## Target`, `## Industries`, `## Sources`, `### Direct Career Pages`, `### Industry Job Boards`, `### JobSpy Aggregator`, `### Niche Newsletters`, `### Web Search Discovery`, and role type slugs in `## Search Progress`. Never update one section without propagating to all consumers. This prevents partial-update drift where some sections reflect old criteria. (V23 compound insight.)
  ```

## Proposal 6: Add Unified Score Extraction Rule to Core Rules
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/CLAUDE.md`
- Action: add
- Rationale: Solution `unified-extract-score-function` (data-integrity.md) documents that multiple upstream sources produce the same semantic field (score) in different schema locations (`score`, `scoring.total_score`, `score_breakdown.total`, `score.total`). The V23 analysis confirmed this was applied to manage_state.py and api/jobs.py. This needs to be codified as a rule so future code consuming verified JSONs uses the same polymorphic extraction.
- Proposed edit:
  In section `## Core Rules`, add new rule:
  ```
  14. **Polymorphic score extraction at every consumption point.** Verified JSONs may contain scores in multiple locations (`score`, `scoring.total_score`, `score_breakdown.total`, `score.total`). Any code that reads a score MUST use `manage_state.py`'s `extract_score()` function (or equivalent polymorphic lookup) rather than assuming a single field path. Never trust upstream schema consistency in a multi-source pipeline. (V23 data-integrity pattern.)
  ```

## Proposal 7: Add Semantic Dedup as Fallback to Orchestration Dedup Phase
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/references/orchestration.md`
- Action: modify
- Rationale: Solutions `semantic-dedup-over-slugs` (data-integrity.md) and `presentation-layer-dedup-safety-net` (data-integrity.md) document that slug-based dedup misses duplicates when filenames vary for the same job. The orchestration dedup phase currently only documents the CLI dedup. A secondary semantic dedup pass should be documented.
- Proposed edit:
  In Phase 3: Dedup, after step 2 ("Run dedup CLI"), add a new step:
  ```
  2b. **Semantic dedup safety net (Step 13b).** If presentation-layer duplicates persist after CLI dedup (same company + normalized title appearing in multiple role types), deduplicate at presentation time by keeping the highest-scoring instance per normalized company+title pair. This is a defense-in-depth measure — the CLI dedup should catch most cases, but slug normalization differences can cause misses.
  ```

## Proposal 8: Add Progressive Query Broadening to Search Channel Guidance
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/references/orchestration.md`
- Action: modify
- Rationale: Solution `progressive-query-broadening` (performance.md) documents that broad queries yield many results while narrow industry queries yield near-zero. The current orchestration search channels do not explicitly guide subagents on query breadth strategy.
- Proposed edit:
  In Phase 1: Search, after the "5 Search Channels" table, add:
  ```
  **Query strategy for all channels:** Start with broad terms (e.g., "marketing manager", "operations lead"), not narrow industry-specific terms (e.g., "crypto marketing manager"). Broad queries yield many results; narrow industry queries yield near-zero on most platforms. Filter results programmatically for industry relevance after retrieval. This applies especially to JobSpy Aggregator (Channel 3) and Web Search Discovery (Channel 5).
  ```

## Proposal 9: Add Incremental Session-State Checkpointing to Orchestration
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/references/orchestration.md`
- Action: modify
- Rationale: Solution `incremental-session-state-checkpointing` (data-integrity.md) documents writing session-state after each batch rather than only at session end, enabling resume on interruption. The current orchestration has per-channel session-state gates but does not explicitly mandate batch-level state in the session-state file format.
- Proposed edit:
  In Phase 1: Search, in the "Per-Channel Session-State Gate" section, append:
  ```
  **Session-state format per channel:** Each channel entry in session-state.md MUST include: channel name, batch number, role types processed, jobs found count, timestamp. This enables resume capability on interruption — the parent can read session-state.md on restart and identify which channels completed.
  ```

## Proposal 10: Add Design System Preloading Reminder to Deliver Phase
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/references/orchestration.md`
- Action: modify
- Rationale: Solution `design-system-skill-preloading` (design-system.md) documents that the parent must call the frontend-design skill before dispatching any visual output subagents. Hard Constraint 2 in CLAUDE.md references this but the orchestration Phase 5 steps do not explicitly remind the parent to verify design system loading.
- Proposed edit:
  In Phase 5: Deliver, before Step 1 ("Dispatch brief agents"), add:
  ```
  0. **Verify design system loaded (HC2 enforcement).** Before dispatching any visual output subagent (brief-generator, digest-email, briefs-html), confirm the `jsa-design-system` skill is preloaded in each agent's frontmatter. If any agent lacks the skill reference, add it before dispatch. Never allow visual output agents to generate HTML without the unified design system. (V22 compound insight — per-subagent style drift.)
  ```

## Proposal 11: Add Verify-Before-Brief Guard to Deliver Phase
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/references/orchestration.md`
- Action: modify
- Rationale: Solution `verify-before-brief-guard` (data-integrity.md) documents that before dispatching brief generators, the parent must glob for verified JSON existence. The current Phase 5 entry criteria check for user feedback but not for the actual existence of verified JSON files for the selected jobs.
- Proposed edit:
  In Phase 5: Deliver, in the "Entry Criteria" section, add:
  ```
  - **Verified JSON existence gate:** For each `brief_requested` job, confirm its verified JSON file exists at `output/verified/{role_type_slug}/{company_slug}-{title_slug}.json`. If any file is missing, dispatch a verification subagent first. Do not dispatch brief generators against missing upstream data.
  ```

## Proposal 12: Add Selection Confirmation Before Brief Dispatch
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/references/orchestration.md`
- Action: modify
- Rationale: Solution `selection-confirmation-before-dispatch` (subagent-coordination.md) documents that the parent should verify count and identity of selected jobs match user expectation before dispatching parallel brief agents. This catches miscounts before wasted parallel dispatch.
- Proposed edit:
  In Phase 5: Deliver, before Step 1 ("Dispatch brief agents"), add:
  ```
  0b. **Selection confirmation (MANDATORY before brief dispatch).** Read `state.json` to enumerate all jobs with `brief_requested` action. Confirm the count and list of jobs matches what the user selected in Phase 4. If there is a mismatch (e.g., user selected 5 but state shows 3), halt and resolve before dispatching. This prevents wasted parallel dispatch on incorrect selections.
  ```

## Proposal 13: Update MEMORY.md — Promote V23 Cost Reduction to "Implemented"
- Target: `/Users/ryanhennebry/Projects/autonomous1/.claude/projects/-Users-ryanhennebry-Projects-autonomous1/memory/MEMORY.md`
- Action: modify
- Rationale: The V23 CLAUDE.md now has explicit Agent Model Tiers (D2, D3) with Haiku for search-verify and Sonnet for briefs. The MEMORY.md section "V23 Required Improvement: Cost Reduction" is now implemented and should be updated to reflect this, preventing future sessions from treating it as an open item.
- Proposed edit:
  In section `### V23 Required Improvement: Cost Reduction (CRITICAL -- MUST FIX)`, change the header to:
  ```
  ### V23 Cost Reduction (IMPLEMENTED)
  ```
  And add at the top of the section:
  ```
  - **Status:** Implemented in V23 via Agent Model Tiers (D2/D3). Opus parent-only, Sonnet for briefs/email, Haiku for search-verify. HC1 reversed to allow model passing.
  ```

## Proposal 14: Update MEMORY.md — Promote V23 Dedup Context-Awareness to "Implemented"
- Target: `/Users/ryanhennebry/Projects/autonomous1/.claude/projects/-Users-ryanhennebry-Projects-autonomous1/memory/MEMORY.md`
- Action: modify
- Rationale: Decision D4 implemented context-aware dedup via `--role-types` flag. The MEMORY.md section "V23 Required Improvement: Dedup Must Be Context-Aware" is now implemented.
- Proposed edit:
  In section `### V23 Required Improvement: Dedup Must Be Context-Aware (MUST FIX)`, change the header to:
  ```
  ### V23 Dedup Context-Awareness (IMPLEMENTED)
  ```
  And add at the top:
  ```
  - **Status:** Implemented in V23 via `--role-types` flag on dedup subcommand (D4). Pre-search cleanup archives stale directories. Dedup only processes active role types.
  ```

## Proposal 15: Update MEMORY.md — Promote V23 Search Breadth to "Implemented"
- Target: `/Users/ryanhennebry/Projects/autonomous1/.claude/projects/-Users-ryanhennebry-Projects-autonomous1/memory/MEMORY.md`
- Action: modify
- Rationale: Decision D5 implemented 5-channel search as fixed infrastructure. The MEMORY.md section "V23 Required Improvement: Search Breadth" is now implemented.
- Proposed edit:
  In section `### V23 Required Improvement: Search Breadth (MUST FIX)`, change the header to:
  ```
  ### V23 Search Breadth (IMPLEMENTED)
  ```
  And add at the top:
  ```
  - **Status:** Implemented in V23 via 5-channel mandatory search infrastructure (D5). All channels dispatch in parallel with content adapted to user context. verify-channels-dispatched gate enforces completeness.
  ```

## Proposal 16: Add Rate-Limit Recovery to Auto-Retry Protocol
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/CLAUDE.md`
- Action: modify
- Rationale: Solution `rate-limit-recovery-pattern` (subagent-coordination.md) documents that on rate-limit failures, the parent should read summary files to detect stale output, surface options to the user (wait vs. continue with existing data), and re-dispatch using identical structure once the user signals to continue. The current Auto-Retry Protocol does not distinguish rate-limit failures from other failures.
- Proposed edit:
  In section `## Auto-Retry Protocol`, after rule 4, add:
  ```
  5. **Rate-limit failures are distinct from task failures.** On rate-limit, do NOT count it as a retry. Instead: read summary files to detect stale or missing output, surface options to user (wait for rate-limit reset vs. continue with existing data), and re-dispatch with identical parameters once user signals to continue.
  ```

## Proposal 17: Add Heredoc JSON Validation to Scheduled Runs
- Target: `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v23/CLAUDE.md`
- Action: modify
- Rationale: Solution `heredoc-json-validation` (deployment.md) documents that YAML heredoc indentation produces invalid JSON silently. The Scheduled Runs section references settings.local.json write protocol but does not mandate post-write validation.
- Proposed edit:
  In section `## Scheduled Runs`, after the "settings.local.json write protocol" line, add:
  ```
  **JSON validation after heredoc writes:** After generating any JSON file from a heredoc in CI, immediately validate with `python3 -c "import json; json.load(open('path/to/file.json'))"`. Heredoc indentation produces invalid JSON silently. (V20 deployment pattern.)
  ```

## Proposal 18: Add Vercel Deploy to Version Transition Checklist in Root CLAUDE.md
- Target: `/Users/ryanhennebry/Projects/autonomous1/CLAUDE.md`
- Action: modify
- Rationale: Solutions `vercel-link-before-deploy` and `vercel-project-json-reuse` (deployment.md) plus MEMORY.md document that on version transition the dashboard must be re-linked and deployed from the new version directory. The root CLAUDE.md Version Transition Checklist does not include this step, risking stale dashboards (V21 lesson).
- Proposed edit:
  In section `### Version Transition Checklist`, after step 2 ("Trigger"), add:
  ```
  3. **Re-deploy Vercel dashboard (if project has one):** `vercel link --project <dashboard-name> --yes && vercel --prod --yes` from the new version directory. Verify deployment serves current data. (V21 lesson: forgot to deploy, dashboard was stale for 2 days.)
  ```

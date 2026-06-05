# Compound Proposals: jsa V22

Sources: .claude/solutions/*.md (10 files), .claude/decision-log/jsa-v22.md

---

## Proposal 1: Add Checkpoint-Driven Enforcement to Agent Development Workflow
- Target: CLAUDE.md (Agent Development Workflow section)
- Action: modify
- Rationale: V22 decision log confirms 6 versions of declarative text constraints failed to prevent recurring regressions. The chosen fix is imperative checkpoint gates at phase transitions — managed via manage_state.py checkpoint subcommands. CLAUDE.md should document that phase transitions require a passing pre-gate, not just the pipeline sequence.
- Proposed edit:
  Under "Pipeline:" in the Agent Development Workflow section, add after the pipeline diagram:

  ```
  **Phase Gate Enforcement:**
  - Each phase transition requires a passing checkpoint gate before proceeding
  - Gates are enforced via `manage_state.py checkpoint write/validate` — progress is structurally impossible without them
  - Declarative text constraints alone are insufficient; enforcement must be architectural
  ```

---

## Proposal 2: Add background:true as Standard Agent Dispatch Pattern
- Target: CLAUDE.md (Named Agent Pattern section)
- Action: modify
- Rationale: V22 decision log chose `background: true` in agent YAML frontmatter as the canonical dispatch approach, replacing the foreground-fallback workaround that accumulated across 4 versions. CLAUDE.md still references the foreground-fallback guard; it should be updated to reflect the new standard.
- Proposed edit:
  In the "Named Agent Pattern (v13 Standard)" section, add:

  ```
  - Set `background: true` in agent YAML frontmatter for parallel dispatch — do NOT use foreground-fallback guard workarounds
  - The foreground-fallback pattern is deprecated; native background dispatch is the standard from V22 onward
  ```

  Remove or strike any reference to `foreground-fallback-guard` from CLAUDE.md if present.

---

## Proposal 3: Add 5-Channel Search as Mandatory Infrastructure
- Target: references/orchestration.md (or equivalent JSA orchestration reference)
- Action: add
- Rationale: Solution `multi-channel-search-assembly` (jsa-v22) and MEMORY.md "V23 Required Improvement: Search Breadth" both require 5 fixed search channels on every run. This is now a hard constraint, not a guideline. The orchestration reference must define all 5 channels as non-optional infrastructure with content adapting to context.md profile.
- Proposed edit:
  Add to Phase 1 (Search) in orchestration.md:

  ```
  **Mandatory 5-Channel Search (non-optional):**
  1. Direct career pages — known companies in user's target industry (from context.md)
  2. Industry job boards — boards matched to context.md `## Industries` (not hardcoded)
  3. JobSpy aggregator — 8+ varied queries across LinkedIn/Indeed/Glassdoor via scripts/jobspy_search.py
  4. Niche newsletters & curated lists — WebSearch to discover latest issues relevant to user's sector
  5. Web search discovery — queries adapted to user's industries and role types to surface new sources

  Dispatch all 5 channels as parallel subagents at search phase start. No channel is optional.
  Channel infrastructure is fixed; channel content adapts to context.md per run.
  ```

---

## Proposal 4: Add Tiered Model Assignment as Hard Constraint
- Target: CLAUDE.md (Named Agent Pattern section) and references/agents/ frontmatter templates
- Action: add
- Rationale: MEMORY.md "V23 Required Improvement: Cost Reduction (CRITICAL)" documents that `model: inherit` across all subagents caused a $4.09 run that didn't complete. The fix is explicit tiered model assignment. CLAUDE.md must codify the tier assignment so future versions don't regress to `model: inherit`.
- Proposed edit:
  Add to "Named Agent Pattern (v13 Standard)" section:

  ```
  **Model Tier Assignment (mandatory — never use `model: inherit`):**
  - Opus: Parent orchestrator only
  - Sonnet: Brief generation, digest email, briefs HTML
  - Haiku: Search-verify, source-researcher, recovery agents (mechanical/fetch tasks)

  Set `model:` explicitly in every agent frontmatter. `model: inherit` is prohibited.
  Target: <$0.50 per full run. Add cost guard — checkpoint and stop gracefully if cumulative spend exceeds $2.00.
  ```

---

## Proposal 5: Add Run-Scoped Dedup Constraint
- Target: CLAUDE.md (Cross-Version Memory section) or references/orchestration.md
- Action: add
- Rationale: Solution `recovery-subagent-for-data-corruption` and MEMORY.md "V23 Required Improvement: Dedup Must Be Context-Aware" document that context-unaware dedup archived live results in V22. The fix must be codified as a hard rule: dedup only across active role-type directories for the current run.
- Proposed edit:
  Add to orchestration.md dedup phase or CLAUDE.md Cross-Version Memory:

  ```
  **Dedup Scope Rule:**
  - `manage_state.py dedup` must accept `--role-types` flag listing active slugs for the current run
  - Dedup only operates on directories matching active role types — never touches prior-run directories
  - When user changes target focus between runs, archive old role-type directories BEFORE dispatching search agents
  - Dedup must never archive jobs it did not search for in the current run
  ```

---

## Proposal 6: Add CI Debug Pattern to Build Phase Notes
- Target: CLAUDE.md (Agent Development Workflow — /build phase) or references/build.md
- Action: add
- Rationale: Solution `ci-debug-read-then-fix-pattern` (jsa-v22) documents a repeatable 3-step debug sequence for CI env var failures: read the failing script → check env var propagation per step → re-trigger and verify advancement. This is generalizable and should be captured in build phase guidance.
- Proposed edit:
  Add to /build phase notes:

  ```
  **CI Debug Sequence (env var / guard failures):**
  1. Read the failing script before editing it
  2. Check env var propagation to each pipeline step independently
  3. Re-trigger CI run and verify the new run advances past the previous failure point before declaring fix complete
  ```

---

## Proposal 7: Add Scheduled Run Architecture Note
- Target: CLAUDE.md (Agent Development Workflow) or MEMORY.md (Scheduled Runs section)
- Action: modify
- Rationale: V22 decision log chose `claude-code-action@v1` over `claude --print` for scheduled runs due to 100% failure rate since V20. MEMORY.md currently documents the broken state; it should be updated to reflect the V22 architectural decision and the 3-consecutive-success confidence gate.
- Proposed edit:
  Update MEMORY.md "Scheduled Runs — Broken Since V20" section (note: MEMORY.md is in ~/.claude, not this repo — flag for user to apply):

  ```
  **V22 Decision:** Migrate repo-root daily-digest.yml to `claude-code-action@v1`.
  `claude --print` is kept as a commented-out fallback only.
  Confidence gate: require 3 consecutive successful scheduled runs before treating as stable.
  Repo-root workflow MUST be updated to point at current version directory on every version transition.
  ```

---

## Proposal 8: Add Selection Confirmation Guard Before Parallel Dispatch
- Target: CLAUDE.md (Agent Development Workflow — /build phase) or references/orchestration.md
- Action: add
- Rationale: Solution `selection-confirmation-before-dispatch` (jsa-v22) — reading source data to confirm selection mapping before firing parallel agents (e.g., brief generators) is a generalizable pattern. It prevents wasted parallel dispatch on miscounts and should be a standard pre-dispatch step.
- Proposed edit:
  Add to build phase or orchestration.md parallel dispatch notes:

  ```
  **Pre-Dispatch Selection Confirmation:**
  Before dispatching parallel subagents against a data set (e.g., brief generators over verified JSONs):
  1. Read source data to confirm selection count and identity
  2. Verify count matches user expectation
  3. Only then fire parallel agents
  Catches miscounts before wasted parallel dispatch.
  ```

---

## Proposal 9: Codify Recovery Subagent Pattern for Data Corruption
- Target: CLAUDE.md (Context Discipline section)
- Action: modify
- Rationale: Solution `recovery-subagent-for-data-corruption` (jsa-v22) establishes that when data corruption is detected mid-run, the fix must be isolated in a dedicated recovery subagent — not handled inline in parent context. This reinforces the existing "Parent context is ONLY for dispatch" rule with a concrete mid-run recovery pattern.
- Proposed edit:
  Add to "Context Discipline (ALL phases — no exceptions)" section:

  ```
  - When data corruption is detected mid-run, dispatch a dedicated recovery subagent — NEVER fix inline in parent context
  - Note the root cause as a version-level fix; recovery is a containment measure, not a permanent solution
  ```

---

## Proposal 10: Vercel Deploy — Mandate .vercel/project.json Copy on Version Transition
- Target: CLAUDE.md (Version Transition Checklist) or MEMORY.md (Vercel Dashboard Deployment)
- Action: modify
- Rationale: Solution `vercel-link-before-deploy` and `vercel-project-json-reuse` (v18, v21) both address the same failure: deploying to a new version directory creates a new Vercel project instead of updating the existing one. The version transition checklist should explicitly require copying .vercel/project.json before deploying.
- Proposed edit:
  Add to Version Transition Checklist, after the existing step 1:

  ```
  3. **Before deploying dashboard on version transition:**
     - Copy `.vercel/project.json` from previous version directory to new version directory
     - Run `vercel link --project jsa-dashboard --yes` to confirm linkage
     - Then run `vercel --prod --yes`
     - Verify: `curl -s https://jsa-dashboard.vercel.app/api/state` shows today's `run_date`
  ```

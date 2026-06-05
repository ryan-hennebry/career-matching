# Compound Proposals: JSA V21

Sources read:
- .claude/solutions/configuration.md
- .claude/solutions/data-integrity.md
- .claude/solutions/deduplication.md
- .claude/solutions/deployment.md
- .claude/solutions/email-delivery.md
- .claude/solutions/performance.md
- .claude/solutions/subagent-coordination.md
- .claude/solutions/testing.md
- .claude/solutions/uncategorized.md
- .claude/decision-log/jsa-v21.md

Note: Proposals from V20 compound run are NOT duplicated here. Only V21-new patterns are proposed.

---

## Proposal 1: Preflight Debug Pattern — Validation Harness Standard

- Target: `references/agent-patterns.md` (append under "Validation Patterns")
- Action: add
- Rationale: `preflight-debug-pattern` (read validation script → read file being validated → fix mismatch) is a reusable sequence for any agent with a preflight harness. Without documenting it, each version re-derives the same debug loop. Source: jsa-v21-analysis.md.
- Proposed edit:

```
### Preflight Debug Sequence

When a preflight validation script fails:
1. Read the validation script to understand what it checks.
2. Read the file or config being validated to see its actual state.
3. Fix the mismatch between what the script expects and what the file contains.
Apply to any agent with a validation harness that may drift from the codebase it checks.
```

---

## Proposal 2: Verify-Before-Brief Guard — Pipeline Gate Standard

- Target: `03_agents/tests/v21/CLAUDE.md` Hard Constraints section
- Action: add
- Rationale: `verify-before-brief-guard` (glob for verified JSON existence before dispatching brief generators; dispatch verification subagent first if missing) prevents wasted brief runs on incomplete upstream data. V21 analysis confirmed this as a failure pattern. Should be a named hard constraint.
- Proposed edit (add as Hard Constraint 12):

```
12. **Verify-before-brief guard.** Before dispatching brief-generator subagents, glob `output/verified/{role_type_slug}/` for verified JSON files. If the directory is empty or missing, dispatch a verification subagent first. Never generate briefs on unverified data.
```

---

## Proposal 3: Vercel Link Before Deploy — Deployment Standard

- Target: `references/agent-patterns.md` (append under "Deployment Patterns")
- Action: add
- Rationale: `vercel-link-before-deploy` was a concrete V21 failure: deploying without `vercel link` created a new project instead of updating the existing one. This is a persistent trap on version transitions.
- Proposed edit:

```
### Vercel Link Before Deploy

Always run `vercel link --project <name> --yes` before `vercel --prod --yes`.
- Without the link step, Vercel creates a new project instead of deploying to the existing one.
- Verify `.vercel/project.json` exists and contains the correct project/org IDs before any deploy.
- On version transitions: re-link from the new version directory before the first deploy.
```

---

## Proposal 4: Search Redispatch with Special Instructions — Search Recovery Standard

- Target: `references/orchestration.md` (Phase 1, Search section)
- Action: add
- Rationale: `search-redispatch-with-special-instructions` — when aggregator search returns generic/off-target results, re-dispatch with SPECIAL_INSTRUCTIONS directing the agent to use company career pages directly and domain-specific queries. V21 analysis confirmed this pattern recovers quality. Should be a named recovery step in Phase 1.
- Proposed edit (add to Phase 1 search instructions):

```
**Search Quality Recovery:**
If aggregator search returns generic results (consumer brands, off-industry):
- Re-dispatch search subagent with SPECIAL_INSTRUCTIONS: "Use company career pages directly and domain-specific queries (e.g., web3.career, cryptocurrencyjobs.co) rather than broad composite queries."
- Do not accept first-pass results if role-type coverage is below 30% industry match.
```

---

## Proposal 5: Parallel Multi-Source Dispatch — Search Architecture Standard

- Target: `references/orchestration.md` (Phase 1, Search section)
- Action: add
- Rationale: `parallel-multi-source-dispatch` (dispatch 3+ independent search subagents simultaneously with fully self-contained prompts) was validated in V21 as a performance and coverage improvement. Key constraint: each prompt must embed all required context so subagents are stateless.
- Proposed edit (add to Phase 1 search instructions):

```
**Parallel Multi-Source Dispatch:**
Dispatch 3+ independent search subagents simultaneously:
- Each subagent prompt must be fully self-contained: embed working_dir, output_directory, dashboard_url, profile summary, and role-type targets.
- Subagents must NOT depend on shared state or inter-subagent communication.
- Collect and merge results from all subagents before proceeding to Phase 2.
```

---

## Proposal 6: Completion Sentinel Tail Check — Subagent Handoff Standard

- Target: `03_agents/tests/v21/CLAUDE.md` Core Rules section (or `references/agent-patterns.md`)
- Action: add
- Rationale: `completion-sentinel-tail-check` — check for completion sentinel (e.g., `<!-- BRIEF COMPLETE -->`) using `tail -3` before dispatching downstream tasks. File-existence checks alone are insufficient; sentinel check confirms the subagent actually completed its output. V21 analysis source.
- Proposed edit (add to Core Rules or agent-patterns.md under "Subagent Coordination"):

```
**Completion sentinel tail check:** Before dispatching any downstream task that depends on subagent output, run `tail -3 <output_file>` and verify the completion sentinel is present (e.g., `<!-- BRIEF COMPLETE -->`). File existence alone does not confirm completion.
```

---

## Proposal 7: Standalone Script Enforcement for Dedup — V21 Decision

- Target: CLAUDE.md project-level (`/Users/ryanhennebry/Projects/autonomous1/CLAUDE.md`) — Cross-Version Memory section
- Action: add
- Rationale: V21 decision log records that text-based dedup constraints have failed four consecutive versions (V17–V20). The decision to enforce dedup via a standalone Python CLI (`manage_state.py`) rather than inline CLAUDE.md instructions is a cross-agent architectural lesson worth capturing in the project-level CLAUDE.md escalation pattern.
- Proposed edit (append to "Cross-Version Memory" bullet list):

```
- Dedup logic requires code enforcement (standalone Python CLI) — text constraints have failed 4 consecutive versions (V17-V20). Never rely on inline instructions for normalized (company, title) dedup. Use `manage_state.py dedup` or equivalent script.
```

---

## Proposal 8: JSONL Transcript Recovery — Operational Runbook

- Target: `references/agent-patterns.md` (append under "Debugging Patterns")
- Action: add
- Rationale: `jsonl-transcript-recovery` — when a session compacts, the pre-compaction transcript lives in raw JSONL and a Python parser can recover it. `/export` only captures the current compacted window. V21 analysis surfaced this as a non-obvious operational pattern worth documenting.
- Proposed edit:

```
### JSONL Transcript Recovery After Compaction

When a session compacts and pre-compaction content is needed:
- Raw JSONL file contains all pre-compaction user/assistant messages and tool blocks.
- Write a Python parser to extract messages by role and tool type into readable markdown.
- `/export` does NOT capture pre-compaction content — it reads the current (compacted) window only.
- Never claim `/export` can recover pre-compaction transcript.
```

---

## Proposal 9: Three-Layer Build Architecture — Build Pattern

- Target: CLAUDE.md project-level — Agent Development Workflow section
- Action: add
- Rationale: V21 decision log establishes the Three-Layer architecture (Code Infrastructure → Constraint Promotion → Validation Harness) as the appropriate pattern when a build involves greenfield code, structural text changes, AND validation infrastructure simultaneously. Documents when to use 3 layers vs 1-2.
- Proposed edit (add to "Agent Development Workflow" or a new subsection):

```
### Build Complexity Tiers

When the `/build` phase involves multiple artifact types, use layered execution:
- **Single layer:** Text-only constraint edits (V19/V20 pattern).
- **Two layers:** Code + text changes with no validation infrastructure.
- **Three layers:** Greenfield code + CLAUDE.md refactoring + validation harness. Each layer's success criteria must be independently verifiable. Parallel execution within a layer is allowed when tasks have no inter-dependencies.

Three-layer trigger: scope includes new scripts, structural CLAUDE.md changes, AND a validation harness — all three simultaneously.
```

---

## Proposal 10: Tiered Validation (Hard-Block vs Warn) — Preflight Standard

- Target: `references/agent-patterns.md` (append under "Validation Patterns")
- Action: add
- Rationale: V21 decision log establishes two tiers for preflight validation: critical checks exit 1 (halt), non-critical checks emit warnings. Uniform treatment (all halt or all warn) was explicitly rejected. This is broadly applicable to any agent with a preflight harness.
- Proposed edit:

```
### Tiered Preflight Validation

Classify preflight checks into two tiers:
- **Critical (exit 1, halt):** Missing dashboard URL, invalid permissions, invalid config JSON — unrecoverable at runtime.
- **Warning (emit, continue):** Missing agent memory files, stale version references — recoverable during the run.

Never treat all checks uniformly. Hard-blocking on recoverable warnings wastes API calls; soft-warning on unrecoverable errors causes downstream failures.
```

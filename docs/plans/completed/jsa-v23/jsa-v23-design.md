# Design: JSA V23 — Enforcement Gates + Cost Reduction

## Context

V22 achieved 43% failure reduction (14→8) with checkpoint-driven architecture. The remaining 3 critical failures are enforcement gaps: 5-channel search not mandated, dedup not context-aware, and post-batch commit not code-enforced. Additionally, all subagents run on Opus ($4+/run), making daily use cost-prohibitive. V22 research delta identified 6 hard constraints and 5 open questions. V22 compound extracted 5 decisions, 6 solutions, and 10 proposals.

**Source:** V22 research delta handoff (2026-02-24), V22 analysis handoff (8 failures: 3C/3M/2m), V22 compound handoff (5 decisions, 6 solutions).

## Options Considered

### Option A: Enforcement Layer (Single Phase)

All 6 fixes in a single phase — manage_state.py subcommands, HC1 reversal, model tiering, orchestration 5-channel mandate, preflight additions.

- **Pros:** Simple, minimal coordination overhead, proven in V19/V20 for same-domain fixes
- **Cons:** No failure isolation between code changes (manage_state.py) and config changes (CLAUDE.md, orchestration.md). If manage_state.py tests fail, config changes are blocked waiting.
- **Failure mode:** A broken manage_state.py subcommand blocks all other progress since everything is in one phase.
- **Risk level:** Medium
- **Complexity:** Simple
- **Decision log note:** V19 and V20 used single-phase for constraint edits. V23 mixes code creation with config edits — single phase may be insufficient (per V21 decision).
- **Rejected:** Mixes code creation with config edits. V21 showed that mixing artifact types in one phase makes failure isolation impossible.

### Option B: Two-Layer (Code + Config)

Layer 1: manage_state.py code (dedup --role-types, verify-batch-committed, verify-channels-dispatched + tests). Layer 2: config (HC1 reversal, model frontmatter, orchestration 5-channel, preflight, session guard).

- **Pros:** Clean code/config separation. Code tested before config depends on it.
- **Cons:** Preflight additions (Layer 2) are validation code, not config — conflating validation with orchestration text edits.
- **Failure mode:** Layer 2 mixes text edits (CLAUDE.md, orchestration.md) with code edits (preflight.sh), reducing bisectability within the layer.
- **Risk level:** Low-medium
- **Complexity:** Moderate
- **Decision log note:** New approach. Cleaner than A but doesn't fully separate validation from orchestration.
- **Rejected:** Doesn't fully separate validation (preflight.sh) from orchestration text edits. V21's three-layer provided better isolation.

### Option C: Three-Layer (Scripts → Orchestration+Config → Validation)

Layer 1: manage_state.py new subcommands + tests. Layer 2: CLAUDE.md + orchestration.md + agent frontmatter + context.md. Layer 3: preflight.sh additions + integration validation.

- **Pros:** Matches V21's proven three-layer pattern (code → text → validation). Each layer has a single artifact type. Tasks parallelizable within layers. Best failure isolation.
- **Cons:** Highest coordination overhead (3 sequential layers). If Layer 1 is fast, the sequential constraint adds unnecessary waiting.
- **Failure mode:** Layer coordination overhead — if Layer 1 completes quickly, waiting for sequential layer progression is wasteful. Mitigated by parallel tasks within layers.
- **Risk level:** Low
- **Complexity:** Moderate
- **Decision log note:** Matches V21 pattern (Three-Layer: Code Infrastructure → Constraint Promotion → Validation Harness). V21 had 22/22 steps completed successfully with this structure.

## Prototyping Results

Prototyping skipped — no triggers met. All technologies (manage_state.py argparse, git status check, JSON status files, agent frontmatter model field) are already used in the V22 codebase. No new libraries or unverified external APIs.

## Chosen Approach

**Option C: Three-Layer (Scripts → Orchestration+Config → Validation)**

Matches the V21 three-layer pattern that achieved 22/22 step completion. V23's scope mixes code creation (manage_state.py subcommands), structural text edits (CLAUDE.md, orchestration.md), and validation infrastructure (preflight.sh) — three distinct artifact types that benefit from layer isolation. Tasks are parallelizable within layers, mitigating coordination overhead.

## Architecture

### Layer 1: Script Enforcement (manage_state.py + tests)

**Tasks (parallelizable):**

1. **`dedup --role-types`** — Add `--role-types` flag to dedup subcommand. Accepts comma-separated role-type slugs. Only processes directories matching those slugs in `output/verified/`. Ignores all other directories.

2. **`verify-batch-committed`** — New subcommand. Runs `git status --porcelain output/verified/` — if any modified/untracked files exist, exits non-zero with list of uncommitted files. Called by orchestration between search batches.

3. **`verify-channels-dispatched`** — New subcommand. Reads `output/.channels/{channel-name}.json` for all 5 expected channels. Each status file contains `{"channel": "name", "timestamp": "ISO", "result_count": N}`. If any channel file is missing or has a stale date, exits non-zero listing missing channels.

4. **Tests** — New test cases for all 3 features:
   - Dedup with stale directories produces 0 false archives when --role-types scopes correctly
   - verify-batch-committed blocks when uncommitted changes exist, passes when clean
   - verify-channels-dispatched blocks when <5 channel files, passes when all 5 present

### Layer 2: Orchestration + Configuration

**Tasks (parallelizable):**

5. **Reverse HC1** — Replace "Never pass `model:` to Task tool" with "Pass `model:` to Task tool matching the agent's designated tier." Update HC text in CLAUDE.md.

6. **Agent frontmatter model tiering:**
   - `search-verify.md`: `model: haiku` (mechanical fetch+score)
   - `source-researcher.md`: `model: haiku` (mechanical source discovery)
   - `brief-generator.md`: `model: sonnet` (writing quality needed)
   - `digest-email.md`: `model: sonnet` (writing quality needed)
   - `briefs-html.md`: `model: sonnet` (writing quality needed)
   - `onboarding.md`: `model: sonnet` (user interaction quality)

7. **5-channel search mandate in orchestration.md** — Phase 1 rewrite. 5 channel types are fixed infrastructure:
   1. Direct career pages (companies from context.md)
   2. Industry-relevant job boards (boards from context.md)
   3. JobSpy aggregator queries (keywords from context.md)
   4. Niche newsletters & curated lists (discovered via WebSearch)
   5. Web search discovery (queries adapted to context.md industries)

   Each channel dispatches as a separate subagent. All 5 mandatory per run. Channel sources come from `context.md ## Search Channels`.

8. **context.md Search Channels section** — Add `## Search Channels` subsection listing the 5 channel types with user's industry-specific sources populated.

9. **Orchestration gates** — Add `manage_state.py verify-batch-committed` call between search batches. Add `manage_state.py verify-channels-dispatched` call after all Phase 1 search completes.

### Layer 3: Validation + Preflight

**Tasks (parallelizable):**

10. **preflight.sh: git pull** — Add git pull enforcement for interactive mode (skip in SCHEDULED_RUN mode where CI handles checkout).

11. **preflight.sh: session resume guard** — Check `output/digests/_status.json` for today's `sent_at`. If found, print warning and prompt user to confirm re-run or abort.

12. **preflight.sh: model setting validation** — Check each agent's frontmatter has an explicit `model:` field set to `haiku` or `sonnet` (not `inherit`). Fail if any agent is misconfigured.

13. **Integration validation** — End-to-end check: verify all 3 new manage_state.py subcommands work, preflight passes with correct configuration, channel status file structure is correct.

### Data Flow

```
context.md ## Search Channels
    ↓
orchestration.md Phase 1 (dispatches 5 channel subagents)
    ↓
Each channel writes: output/.channels/{channel-name}.json
    ↓
manage_state.py verify-channels-dispatched (reads all 5, fails if missing)
    ↓
Search batches produce: output/verified/{role-type}/*.json
    ↓
manage_state.py verify-batch-committed (git status check between batches)
    ↓
manage_state.py dedup --role-types (scoped to active role types only)
    ↓
Phases 2-5 proceed as before
```

### Dependencies

- Layer 2 depends on Layer 1 (orchestration references new manage_state.py subcommands)
- Layer 3 depends on Layer 2 (preflight validates model settings from agent frontmatter)
- Within each layer, tasks are independent and parallelizable

## Design Approval Questions

1. **Hardest decision:** Model tiering assignment (Opus/Sonnet/Haiku). The tradeoff between cost savings and output quality for search-verify on Haiku is real — if Haiku misses good jobs or produces garbage scores, the entire cost reduction thesis fails. User chose to proceed with the tiered approach, accepting the quality risk.

2. **Rejected alternatives:**
   - **Option A (Single Phase):** Rejected because it mixes code creation with config edits, making failure isolation impossible — lesson learned from V21.
   - **Option B (Two-Layer):** Rejected because it conflates validation code (preflight.sh) with orchestration text edits, reducing bisectability within Layer 2.

3. **Least confident aspect:** Model tiering savings estimate. The <$1.00 target assumes Haiku search-verify works well enough. If Haiku misses good jobs or produces garbage scores, search-verify would need to bump to Sonnet, reducing savings from ~70% to ~50%. /plan should include a quality comparison test step (run same search on Haiku vs Sonnet, compare results) before committing to Haiku for search-verify.

## Success Criteria

1. All 132 existing tests pass + new tests for dedup --role-types, verify-batch-committed, verify-channels-dispatched
2. Full run cost <$1.00 (down from $4+)
3. Dedup with stale directories produces 0 false archives when --role-types is used
4. Post-batch commit gate blocks execution when uncommitted changes exist in output/verified/
5. All 5 channel status files (output/.channels/*.json) written per run

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Haiku search-verify quality insufficient | Medium | High — cost reduction thesis fails | Quality comparison test in /plan Layer 1; fallback to Sonnet |
| 5-channel enforcement slows runs | Low | Medium — more subagents = more time | Channels dispatch in parallel; Haiku is fast |
| Session resume guard false positives | Low | Low — user prompted, not blocked | --force flag if needed in future version |
| HC1 reversal causes model drift | Low | Medium — wrong model = wasted spend or low quality | Preflight validates model settings on every startup |
| verify-batch-committed git check flaky | Low | Medium — false blocks between batches | Git status is reliable; test thoroughly |

## Known Risks Passed to /plan

1. **Haiku quality risk** — /plan must include a quality comparison step: run identical search on Haiku vs Sonnet, compare result quality before committing to Haiku for search-verify
2. **5-channel dispatch ordering** — /plan must define whether channels dispatch simultaneously or in a specific order (some channels may inform others, e.g., web search discovers new career pages)
3. **Session resume guard UX** — /plan must specify the exact user prompt text and the mechanism for the user to confirm re-run vs abort

## Handoff Contract

- Approach: Three-Layer (Scripts → Orchestration+Config → Validation)
- Components: manage_state.py (3 new features), CLAUDE.md (HC1 reversal), orchestration.md (5-channel mandate + gates), agent frontmatter (model tiers), context.md (Search Channels), preflight.sh (3 new checks)
- Success criteria: 132+ tests pass, <$1.00/run, 0 false dedup archives, commit gate blocks uncommitted, 5 channel files per run
- Risks requiring mitigation: Haiku quality (comparison test), HC1 drift (preflight model validation)
- Known risks for /plan: Haiku quality comparison step, 5-channel dispatch ordering, session resume guard UX

<!-- STAGE COMPLETE: /design, 2026-02-24 -->

# Design: JSA V22 — Checkpoint-Driven Architecture

## Context

V21 has the right agent architecture (6 named agents, 7 skills, 5-phase pipeline) but recurring regressions persist: commit+push after batch (6th recurrence), session-state writes (5th recurrence). Root cause: enforcement is declarative (text constraints in CLAUDE.md) not imperative (code gates). Additionally, scheduled GitHub Actions runs have 100% failure rate since V20 (claude --print timeouts at 80+ min). V22 research identified three external updates: `background: true` agent flag, `claude-code-action@v1`, and Task tool metrics.

## Options Considered

### Option A: Incremental Hardening
Add git hooks and phase-boundary validation scripts to V21's existing architecture. Minimal structural change.

- Pros: Low risk, directly targets top 2 regressions, minimal code changes
- Cons: Still relies on agent choosing to run gate scripts, hooks can be bypassed (--no-verify), doesn't address root cause of why checkpoints get skipped (context budget pressure)
- Failure mode: Agent ignores gate output under context pressure — same failure pattern as text constraints
- **Rejected:** Doesn't break the regression cycle. 6 versions of escalating text constraints haven't worked; adding more gates the agent can skip won't fix the structural problem.

### Option B: Checkpoint-Driven Architecture
Restructure orchestration so each phase reads inputs from checkpoint files written by the previous phase. Progress is impossible without checkpoints. manage_state.py becomes checkpoint gatekeeper.

- Pros: Structurally eliminates both recurring regressions (can't skip what's required to proceed), makes enforcement imperative not declarative, composable with existing manage_state.py, testable via unit tests
- Cons: Requires reworking orchestration.md phase transitions, more invasive than Option A, introduces coupling between manage_state.py and dispatch logic
- Failure mode: manage_state.py checkpoint bugs could block valid phase transitions; checkpoint overhead could slow pipeline
- **Chosen:** Makes enforcement imperative. The pattern of declaring constraints and hoping the agent follows them has failed 6 times. This approach makes the architecture itself enforce the constraint.

### Option C: Pipeline Simplification
Collapse 5-phase pipeline into fewer, larger phases with built-in checkpointing. Fewer transitions = fewer checkpoint failures.

- Pros: Fewer transitions means fewer checkpoint opportunities to miss, simpler orchestration, potentially faster
- Cons: Larger phases are harder to debug and bisect, loses V21's clean separation of failure domains, may reintroduce V18-era mixed-failure-domain problems
- Failure mode: Merging Search+Verify into one phase means a search bug and a verify bug look identical — V18 analysis showed this makes debugging take 2-3x longer
- **Rejected:** V21 specifically chose 5-phase separation to avoid V18's debugging problems. Trades checkpoint frequency for checkpoint reliability without addressing root cause (enforcement mechanism). Would regress V21's architecture without solving the actual problem.

## Prototyping Results

Prototyping skipped — no triggers met. All approaches use existing tools (Python CLI, YAML, Markdown). No new technology, no unverifiable APIs, no concurrent state across 3+ components.

## Chosen Approach

**Option B: Checkpoint-Driven Architecture.** Extend manage_state.py with checkpoint subcommands (write/validate/status). Each phase transition in orchestration.md gets a mandatory pre-gate (validate previous checkpoint) and post-checkpoint (write completion). Adopt `background: true` agent flag to eliminate 4 versions of foreground-fallback workaround. Migrate scheduled runs to `claude-code-action@v1` to fix 100% failure rate.

## Architecture

### Components

| Component | Responsibility |
|-----------|---------------|
| `manage_state.py` | State lifecycle (sync, dedup, cleanup) + **NEW:** checkpoint write/validate/status |
| `orchestration.md` | Phase dispatch templates with **NEW:** mandatory pre-gate + post-checkpoint wrappers |
| `preflight.sh` | Startup validation + **NEW:** checkpoint structure validation (orchestration.md has gate calls) |
| Agent `.md` files | Named agent definitions with **NEW:** `background: true` in YAML frontmatter |
| `CLAUDE.md` | Orchestrator rules — **UPDATED:** remove foreground-fallback guard, add checkpoint protocol |
| `settings.local.json` | Permissions — **SIMPLIFIED:** remove background tool workaround entries |
| `daily-digest.yml` | Scheduled runs — **REPLACED:** claude-code-action@v1 instead of claude --print |

### Data Flow

```
Data flow (unchanged from V21):
  search-agent → output/raw/*.json
  verify-agent → output/verified/*.json
  dedup (manage_state.py sync) → state.json
  present-agent → output/briefs.html
  deliver-agent → email sent

Checkpoint metadata layer (NEW):
  output/.checkpoints/search.json   ← written after search batch committed
  output/.checkpoints/verify.json   ← written after verify batch committed
  output/.checkpoints/dedup.json    ← written after dedup completed
  output/.checkpoints/present.json  ← written after briefs generated
  output/.checkpoints/deliver.json  ← written after email sent
```

Checkpoints validate that phase data exists and was committed. They do not carry the data itself.

### Interfaces

```bash
# Checkpoint CLI (manage_state.py extensions)
python3 manage_state.py checkpoint write <phase> --batch N --count N --committed true
python3 manage_state.py checkpoint validate <phase>   # exit 0=proceed, 1=blocked
python3 manage_state.py checkpoint status              # show all checkpoint states
python3 manage_state.py checkpoint clear               # reset for new run
```

### Phase Transition Pattern (orchestration.md)

```
### Phase N+1: [Phase Name]

**PRE-GATE (mandatory):**
  python3 manage_state.py checkpoint validate <previous-phase>
  If exit code != 0, STOP. Do not dispatch.

**Dispatch:**
  Dispatch <agent-name> with background: true ...

**POST-CHECKPOINT (mandatory):**
  python3 manage_state.py checkpoint write <current-phase> --count N --committed true
  git add ... && git commit ...
```

### Implementation Phases

**Layer 1: Checkpoint Infrastructure** (no dependencies)
- Extend manage_state.py: checkpoint write/validate/status/clear subcommands
- Add checkpoint unit tests (test each subcommand, test exit codes, test edge cases)
- Create output/.checkpoints/ directory structure
- Benchmark: validate call < 2s

**Layer 2: Orchestration Integration** (depends on Layer 1)
- Update orchestration.md with pre-gate/post-checkpoint wrappers for all 5 phases
- Add `background: true` to all 6 agent .md files
- Remove foreground-fallback guard from CLAUDE.md
- Update preflight.sh to validate: orchestration.md has gate calls, .checkpoints/ exists
- Simplify settings.local.json (remove background tool workaround entries)

**Layer 3: Scheduling & Deployment** (independent of Layer 2)
- Migrate repo-root daily-digest.yml to claude-code-action@v1
- Add Vercel deploy step to workflow (post-push)
- Keep claude --print as commented-out fallback
- Test with manual workflow_dispatch before enabling cron
- Auto-generate repo-root workflow from agent directory path

## Design Approval Questions

1. **Hardest decision:** Checkpoint enforcement mechanism — choosing between extending manage_state.py vs. separate script vs. preflight.sh. User chose manage_state.py extension because it keeps a single source of truth for all state and follows existing CLI patterns, accepting the scope growth trade-off.

2. **Rejected alternatives:**
   - Option A (Incremental Hardening): Rejected because 6 versions of escalating text constraints haven't broken the regression cycle. Adding more gates the agent can skip doesn't address the structural problem.
   - Option C (Pipeline Simplification): Rejected because V21 specifically chose 5-phase separation to avoid V18's mixed-failure-domain debugging problems. Would regress architecture without solving enforcement.
   - Separate checkpoint.py: Rejected to avoid two state tools with potential sync issues.
   - preflight.sh checkpoints: Rejected because shell JSON handling is fragile and less testable than Python.
   - Foreground-fallback guard: Rejected after 4 versions of workaround in favor of native `background: true` SDK support.
   - Defer scheduling: Rejected — another version with broken scheduling is unacceptable given 100% failure rate.

3. **Least confident aspect:** claude-code-action@v1 reliability — v1.0 action with no production track record in this codebase. May behave differently than expected. **Mitigation:** Keep --print as commented-out fallback. Test with workflow_dispatch before enabling cron. If first run times out, revert to --print fallback. Confidence gate: first 3 scheduled runs all succeed.

## Success Criteria

1. /analyze finds **0 recurrences** of HC7 (commit+push after batch) — currently at 6th recurrence
2. /analyze finds **0 recurrences** of session-state write failures — currently at 5th recurrence
3. Scheduled GitHub Actions run completes in **< 60 minutes** (currently 100% timeout at 80+ min)
4. `background: true` dispatch works **without foreground-fallback guard** activation
5. All **101 V21 tests still pass** (no regressions from checkpoint additions)

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Checkpoint overhead slows pipeline | Low | Low | Benchmark in /plan; 2s threshold per validate call; ~20s total vs 5+ min saved from regression retries |
| claude-code-action@v1 timeout/failure | Medium | Medium | Keep --print as commented-out fallback; test with workflow_dispatch first; monitor first 3 runs |
| manage_state.py scope creep | Low | Low | If exceeds 500 lines, split in V23 |
| Agent skips orchestration.md pre-gate | Low | High | preflight.sh validates orchestration.md has gate calls; structural pattern is reviewable in text; if V22 /analyze finds even 1 skip, V23 adds subagent pre-prompt injection |

## Known Risks Passed to /plan

1. **claude-code-action@v1 integration** — /plan must include a manual workflow_dispatch test step before enabling cron schedule. Must include fallback configuration.
2. **Checkpoint validate performance** — /plan must include a benchmark step with 2s threshold. If exceeded, optimize manage_state.py before proceeding to Layer 2.
3. **Orchestration.md pre-gate enforcement** — /plan must include a preflight.sh validation step that greps orchestration.md for gate calls. Missing gates = build failure.
4. **background: true compatibility** — /plan must include a test step that verifies background dispatch works with the new flag before removing foreground-fallback guard.

## Handoff Contract

- Approach: Checkpoint-Driven Architecture (Option B)
- Components: manage_state.py (checkpoint subcommands), orchestration.md (dispatch wrappers), preflight.sh (structure validation), agent .md files (background:true), CLAUDE.md (updated rules), daily-digest.yml (claude-code-action@v1)
- Success criteria: 0 HC7 regressions, 0 session-state regressions, scheduled run < 60min, background:true works, 101 tests pass
- Risks requiring mitigation: checkpoint overhead (benchmark 2s), claude-code-action@v1 (fallback + workflow_dispatch test), manage_state.py scope (500 line threshold), agent skipping pre-gate (preflight.sh validation)
- Known risks for /plan: claude-code-action@v1 test step, checkpoint benchmark step, preflight.sh gate validation step, background:true compatibility test step

<!-- STAGE COMPLETE: /design, 2026-02-23 -->

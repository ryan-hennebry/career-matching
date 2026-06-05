# Decision Log: JSA V22

## Decisions

### Enforcement Mechanism: Imperative vs. Declarative Constraints

- **Chosen:** Checkpoint-Driven Architecture (Option B) — manage_state.py extended with checkpoint subcommands; phase transitions require a passing pre-gate before proceeding
- **Rejected:** Incremental Hardening (Option A) — adding git hooks and validation scripts the agent can still choose to skip
- **Rationale:** 6 versions of escalating declarative text constraints failed to break the regression cycle. The recurring failures (HC7 commit+push and session-state writes at 5–6 recurrences each) persist because the agent can ignore text under context budget pressure. Imperative enforcement means progress is structurally impossible without checkpoints — the architecture itself enforces the constraint rather than relying on the agent to choose to follow a rule.
- **Context:** Both regressions traced to the same root cause: enforcement was declarative, not imperative. No amount of additional text constraints changes that structural fact.

### Pipeline Structure: Preserve 5-Phase Separation vs. Collapse

- **Chosen:** Preserve V21's 5-phase pipeline, adding checkpoint gates at each transition
- **Rejected:** Pipeline Simplification (Option C) — collapsing into fewer, larger phases
- **Rationale:** V21 specifically chose 5-phase separation to eliminate V18's mixed-failure-domain problem (merged Search+Verify phases made bugs from each domain look identical, causing debugging to take 2–3x longer). Collapsing phases trades checkpoint frequency for checkpoint reliability without addressing the actual enforcement problem. Would regress a deliberate architectural decision without solving the root cause.
- **Context:** V18 analysis showed that phase merging makes failure attribution significantly harder. The cost of fewer transitions is not worth re-introducing that debugging burden.

### Checkpoint Tool: manage_state.py Extension vs. Separate Script vs. preflight.sh

- **Chosen:** Extend manage_state.py with checkpoint write/validate/status/clear subcommands
- **Rejected:** Separate checkpoint.py script (risk of two state tools with potential sync issues); preflight.sh checkpoint logic (shell JSON handling is fragile and less testable than Python)
- **Rationale:** Keeps a single source of truth for all state management. Follows existing CLI patterns already in the codebase. Python is testable via unit tests; shell is not. Consolidation avoids split-brain state bugs.
- **Context:** manage_state.py already owns state lifecycle (sync, dedup, cleanup). Checkpoint metadata is another form of state — belonging in the same tool is the natural extension.

### Background Agent Dispatch: Native Flag vs. Foreground-Fallback Workaround

- **Chosen:** Adopt `background: true` in agent YAML frontmatter; remove foreground-fallback guard from CLAUDE.md; simplify settings.local.json
- **Rejected:** Continuing the foreground-fallback workaround pattern carried across 4 versions
- **Rationale:** Native SDK support for `background: true` eliminates the workaround entirely. Four versions of maintaining a fallback guard is compounding technical debt with no payoff. The workaround exists only because the flag did not previously exist; now that it does, maintaining the workaround is strictly worse.
- **Context:** V22 research identified `background: true` as a new external capability. Adopting it is the correct response to a solved problem.

### Scheduled Run Architecture: claude-code-action@v1 vs. claude --print

- **Chosen:** Migrate repo-root daily-digest.yml to `claude-code-action@v1`; keep `claude --print` as commented-out fallback
- **Rejected:** Continuing with `claude --print` (100% failure rate since V20, timing out at 80+ minutes)
- **Rationale:** Scheduled runs have a 100% failure rate under the current approach. Another version with broken scheduling is unacceptable. `claude-code-action@v1` is specifically designed for CI/GitHub Actions contexts and is more likely to handle the runtime constraints correctly. Deferral was explicitly rejected because the failure rate is already total.
- **Context:** Least-confident decision — v1.0 action with no production track record in this codebase. Mitigation: keep --print fallback, test with workflow_dispatch before enabling cron, require 3 consecutive successful scheduled runs as a confidence gate.

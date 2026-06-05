# Decision Log: Job Search Agent V19

## Decisions

### Single Phase vs Multi-Phase Build Structure
- Chosen: Single phase — all 8 constraint fixes and regression tests land in one phase
- Rejected: Two-phase (CLAUDE.md constraints vs script/test hardening) — CLAUDE.md constraints and their regression tests are the same logical unit; splitting adds coordination overhead without improving debuggability. Phase 1 would reference script behavior that Phase 2 validates, creating a dependency that defeats the purpose of splitting.
- Rejected: Fix-by-fix micro-commits — git bisect adds no value for plain-text constraint edits; 5 separate CLAUDE.md edits are more likely to conflict than 1 consolidated edit; 8 commit cycles is significant overhead for this work type
- Rationale: All 8 fixes share the same failure domain (constraint enforcement) and debugging workflow (read the diff, check the text). V18 justified three phases because it had three distinct failure domains (infrastructure, backend, frontend). V19 has one domain.
- Context: V18 analysis documented 8 implementation-level failures. All fixes are independent with no cross-dependencies — constraint text additions and test assertions, not behavioral code changes.

### Proactive Foreground-Fallback Guard vs Reactive Auto-Retry
- Chosen: Proactive guard — dispatch a trivial test agent (`echo ok`) on startup; if tool denied, set `DISPATCH_MODE=foreground` for all subsequent dispatches
- Rejected: Reactive-only (relying on existing auto-retry protocol) — the auto-retry protocol retries the same dispatch mode instead of escalating to foreground, so it never actually recovers from background denial
- Rationale: V18 runtime wasted ~5 minutes and 4 dispatch cycles discovering background mode was broken. A 10-second upfront check saves minutes of reactive recovery.
- Context: This was identified as the hardest decision. The least confident aspect is that the trivial test agent may succeed while real subagents with different tool requirements (WebFetch, Bash with specific commands) still get denied. The guard catches the most common failure mode (background dispatch denial) while the auto-retry protocol remains as second line of defense for tool-specific denials.

### Context Budget Enforcement via CLAUDE.md Text vs Code
- Chosen: Pure constraint text in CLAUDE.md — explicit list of parent-allowed operations (Task dispatch, Read status/state files, Bash for git only, AskUserQuestion) vs subagent-only operations (WebFetch, WebSearch, python3 scripts/, filter, summarize, Read source files)
- Rejected: No code-level enforcement considered — enforcement is by the LLM reading CLAUDE.md, not by runtime code
- Rationale: Context budget is a behavioral constraint best expressed as instructions the agent reads, not as code that blocks tool access. Includes escape hatch: if subagent dispatch fails 3x for the same operation, parent may execute directly with an explicit log message.
- Context: V18 sessions showed parent context bloating from pulling subagent work into parent. The constraint prevents this by explicitly listing what belongs where. Risk: may be too restrictive for edge cases — escape hatch mitigates this.

### Settings.local.json Merge vs Overwrite
- Chosen: Merge semantics — read existing file, parse JSON, merge new entries, write back
- Rejected: Overwrite (previous V18 behavior of "write settings file") — overwrites destroy user's existing settings
- Rationale: V18 runtime demonstrated that overwriting settings.local.json erases entries the user already configured. Merge preserves existing entries while adding new ones.
- Context: Plan must specify the merge mechanism (Python script, jq, or inline bash) and handle both "file exists with content" and "file doesn't exist yet" cases.

### Regression Test Strategy: Semantic Patterns vs Exact String Matching
- Chosen: Semantic pattern matching — test for patterns (e.g., "contains 'foreground' AND 'fallback'") rather than exact strings
- Rejected: Exact string matching — breaks when instructions are reworded, creating brittle tests
- Rationale: CLAUDE.md constraints will evolve across versions. Tests that grep for exact strings break on any rewording, even when the semantic intent is preserved.
- Context: 4+ regression tests needed: dedup collision key format, no API key echoing patterns, settings merge preserves existing entries, session-state per-batch checkpoint markers.

### Prototyping: Skipped
- Chosen: Skip prototyping
- Rejected: N/A — no triggers met
- Rationale: All changes use existing technologies (Python CLI, CLAUDE.md constraints, pytest assertions). No new libraries, no concurrent state across 3+ components, no unverifiable external APIs.
- Context: Prototyping triggers defined in the workflow were not activated by any of the 8 fixes.

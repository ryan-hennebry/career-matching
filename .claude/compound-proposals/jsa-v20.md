# Compound Proposals: jsa V20

Sources read:
- .claude/solutions/configuration.md
- .claude/solutions/data-integrity.md
- .claude/solutions/deduplication.md
- .claude/solutions/deployment.md
- .claude/solutions/email-delivery.md
- .claude/solutions/performance.md
- .claude/solutions/subagent-coordination.md
- .claude/solutions/testing.md
- .claude/decision-log/jsa-v20.md

---

## Proposal 1: Foreground Fallback Guard — Named Agent Standard

- Target: CLAUDE.md (Named Agent Pattern section) and `references/agent-patterns.md` (extract)
- Action: add
- Rationale: V20 confirmed that background subagent dispatch is unreliable (all tools auto-denied in some environments). The `foreground-fallback-guard` pattern — detect tool denial on first dispatch, then switch all subsequent dispatches to foreground — should be a standard step in the Named Agent Pattern section so future agents adopt it by default.
- Proposed edit (add to "Named Agent Pattern (v13 Standard)" section):

```
**Dispatch Mode Detection (v20 Standard):**
- On first subagent dispatch, detect if all tools are denied.
- If denied, set `dispatch_mode="foreground"` and re-dispatch all subsequent subagents in foreground mode.
- Pre-create all required output directories before dispatch to avoid secondary failures.
- Never assume background dispatch will succeed — always implement this guard.
```

---

## Proposal 2: Post-Compaction Redispatch Rule

- Target: CLAUDE.md (Context Discipline section)
- Action: add
- Rationale: V20 introduced the `post-compaction-redispatch` pattern. Compaction destroys subagent result fidelity; reconstructing findings from the compacted summary is unreliable. This needs a named rule in Context Discipline so it applies to all phases.
- Proposed edit (add to "Context Discipline (ALL phases — no exceptions)" bullet list):

```
- After context compaction, if subagent outputs are needed, re-dispatch the original subagents from scratch. NEVER reconstruct findings from the compacted conversation summary — compaction destroys fidelity.
```

---

## Proposal 3: Mandatory Variable Propagation — Config Validation Rule

- Target: CLAUDE.md (Agent Development Workflow section, or new `references/config-validation.md`)
- Action: add
- Rationale: V20 decision log and `mandatory-variable-propagation` solution confirm that silent null/empty fallbacks for required config values (e.g., dashboard URL) cause downstream failures. This pattern is general enough to apply to any agent, not just JSA.
- Proposed edit (add a new "Config Validation" subsection under "Agent Development Workflow"):

```
### Config Validation (ALL agents)

Mandatory config variables must fail loudly when missing — never degrade silently:
- Remove all null/empty fallbacks for required variables at every consumer location.
- Store mandatory variables in a persistent config file; validate at read time.
- Require non-null value before dispatching any subagent that depends on the variable.
- Example: dashboard URL must be present in context.md before digest-email subagent dispatch; if missing, abort and surface an error.
```

---

## Proposal 4: Idempotent Email Gate — Delivery Standard

- Target: `references/agent-patterns.md` (create or append)
- Action: add
- Rationale: The `idempotent-email-gate` pattern (check _status.json for sent_at + run_date match before sending) has been proven across V19 and V20. It should be documented as a delivery standard so future agents adopt it without re-deriving it.
- Proposed edit (append to `references/agent-patterns.md` under "Delivery Patterns"):

```
### Idempotent Email Gate

Before sending any digest or notification email:
1. Check `_status.json` for `sent_at` + `run_date` matching the current run.
2. If both match, skip send (already delivered for this run).
3. Write `sent_at` and `run_date` to `_status.json` immediately after successful send.
4. Gate is stateless across sessions — works cleanly on resume or re-run.
```

---

## Proposal 5: Incremental Session State Checkpointing — Build Standard

- Target: `references/agent-patterns.md` (create or append)
- Action: add
- Rationale: `incremental-session-state-checkpointing` (write state after each batch, not just at session end) is a broadly applicable resilience pattern for any multi-batch workflow. Documenting it as a standard prevents re-derivation.
- Proposed edit (append to `references/agent-patterns.md` under "Resilience Patterns"):

```
### Incremental Session State Checkpointing

For any multi-batch workflow:
- Write session-state file after each batch (not just at session end).
- Include: batch number, entities processed, cumulative counts.
- Enables resume capability on interruption without reprocessing completed batches.
```

---

## Proposal 6: Selective Cleanup via State JSON — Pre-Run Standard

- Target: `references/agent-patterns.md` (create or append)
- Action: add
- Rationale: `selective-cleanup-via-state-json` prevents destructive pre-run cleanup from deleting files that downstream systems depend on across runs. Should be a named pattern, not re-derived per agent.
- Proposed edit (append to `references/agent-patterns.md` under "Resilience Patterns"):

```
### Selective Cleanup via State JSON

Before pre-run cleanup of output files:
1. Read `state.json` to identify still-active entities.
2. Delete only files for entities NOT tracked as active.
3. Preserve files for active entities across runs.
Apply whenever cleanup could destroy data that downstream APIs or dashboards depend on.
```

---

## Proposal 7: Heredoc JSON Validation — CI Standard

- Target: `references/agent-patterns.md` (create or append)
- Action: add
- Rationale: `heredoc-json-validation` (validate JSON after heredoc generation in CI) prevents silent invalid-JSON failures. Applicable to any agent with CI/CD steps that write JSON via heredoc.
- Proposed edit (append to `references/agent-patterns.md` under "CI/CD Patterns"):

```
### Heredoc JSON Validation

After generating any JSON config file from a YAML heredoc in CI:
- Immediately validate: `python3 -c "import json; json.load(open('path/to/file.json'))"`
- YAML heredoc indentation produces invalid JSON silently.
- Validation catches the error before downstream failures occur.
```

---

## Proposal 8: Regression Enforcement Escalation Path

- Target: CLAUDE.md (Cross-Version Memory section)
- Action: add
- Rationale: V20 decision log establishes a clear pattern: text constraints alone are insufficient for recurring failures — escalate to code/assertion enforcement. This escalation path should be named in the Cross-Version Memory section so reviewers know to recommend it.
- Proposed edit (add to "Cross-Version Memory" bullet list):

```
- Recurring failures (same failure in 2+ versions) require escalation from text constraints to code/assertion enforcement. Active checks that STOP execution cannot be silently bypassed. Flag for `/review` when a regression recurs.
```

---

## Proposal 9: Zsh Safe Cleanup Pattern — Shell Standard

- Target: CLAUDE.md or `references/agent-patterns.md`
- Action: add
- Rationale: `zsh-safe-cleanup-with-find` solves a portability issue (zsh glob expansion fails on empty dirs) that will recur in any agent using shell cleanup. Should be a named standard.
- Proposed edit (append to `references/agent-patterns.md` under "Shell Patterns"):

```
### Zsh Safe Directory Cleanup

Use `find dir -type f -delete 2>/dev/null` instead of `rm -f dir/*` for portable cleanup.
- Zsh glob expansion fails silently on empty directories.
- `find` handles empty dirs gracefully across shells.
Apply to any shell cleanup command in agent definitions or CI steps.
```

---

## Proposal 10: Post-Dispatch Directory Verification — Subagent Standard

- Target: CLAUDE.md (Named Agent Pattern section) or `references/agent-patterns.md`
- Action: add
- Rationale: `post-dispatch-directory-verification` (verify output landed in expected directory after subagent completion; check fallback dirs if empty) has appeared in V19 and V20. Should be a named standard step.
- Proposed edit (append to "Named Agent Pattern" section or `references/agent-patterns.md`):

```
### Post-Dispatch Directory Verification

After any subagent that writes file artifacts:
1. Verify output landed in the expected directory.
2. If expected directory is empty, check fallback directories (e.g., previous version dirs).
3. Copy files to expected location if found in fallback.
Apply as a standard post-dispatch step for all file-writing subagents.
```

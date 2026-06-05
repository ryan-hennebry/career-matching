# Design: JSA V26 — Gate Chaining + Data Integrity

## Context

V25 analysis identified 18 failures (2C/7M/9m). Post-analysis research re-grounded the full codebase (7 agents, 7 skills, 8 scripts, 259 tests). Cross-referencing the analysis fixes against the actual V25 codebase revealed that many proposed fixes target constraints that **already exist but aren't followed**. The core insight: text constraints fail because the agent can choose to skip them. Code gates work when they're chained — skipping one blocks the next step.

V26's design shifts from "add more constraints" to "chain existing gates so violations are structurally impossible to proceed past" + build genuinely missing verification infrastructure.

## Options Considered

### Option 1: Constraint Layering (Add More Text)
- Pros: Simple to implement, low code risk, fast to build
- Cons: 9-10 consecutive versions prove text constraints don't prevent regressions. Agent memory not read (6x), parent inline Python (6x), commit+push skipped (9x), session-state not written (10x) — all had text constraints that were ignored.
- **Rejected:** Text-only enforcement has failed across 6-10 consecutive versions for every recurring regression. Adding more text is definitionally insanity.

### Option 2: Gate Chaining + Verification Infrastructure (Chosen)
- Pros: Makes violations structurally impossible by blocking the next step when a gate is skipped. Builds genuinely missing verification tools (verify-before-archive, validate-presentation). Resolves doc contradictions that cause .done path confusion. Minimal new code — mostly wiring existing gates into chains.
- Cons: Gate chain bugs could block entire sessions. Slightly more complex manage_state.py.
- **Chosen:** Evidence-backed — `verify-and-commit` and `verify-session-state-written` already work when called. The failure is calling them. Chaining makes calling them mandatory.

### Option 3: External Enforcement (Pre-commit Hooks / CI)
- Pros: Enforcement outside the agent's control entirely. Can't be skipped.
- Cons: Agent runs locally in a conversation — pre-commit hooks don't apply to the agent's workflow (it's not committing through git hooks, it's orchestrating subagents). CI checks are post-hoc, not preventive. Doesn't address in-session violations.
- **Rejected:** Agent orchestration happens inside a conversation, not in a CI pipeline. External enforcement can't prevent in-session violations like "present expired jobs" or "skip memory read."

## Prototyping Results
Prototyping skipped — no triggers met. All changes extend existing manage_state.py patterns and CLAUDE.md structure. No new technology, no unverifiable external APIs, no concurrent state management.

## Chosen Approach

**Gate Chaining + Verification Infrastructure** — organized as Three-Layer build (proven V21/V23/V25).

The key architectural idea: every recurring regression gets its enforcement **moved from text constraint to gate chain**. A gate chain means: the gate for step N+1 checks that step N's gate was passed. Skipping step N blocks step N+1.

## Architecture

### Layer 1 — Infrastructure (manage_state.py code changes)

**New subcommands:**

1. **`verify-before-archive`** — AF1. Takes a verified JSON file path. Checks `job_url` via HTTP HEAD/GET. Returns `{"status": "expired"|"live"|"unreachable", "evidence": "..."}`. Writes verdict to JSON's `active_status` field. Agent cannot recommend removal without calling this and getting `expired` verdict.

2. **`validate-presentation`** — IF12. Reads all verified JSONs for specified role types. Validates: (a) all `job_url` values match ATS patterns (not generic career pages), (b) all `active_status` values are non-null, (c) no `active_status=expired` entries in the active list. Returns pass/fail with specific violations. Agent must call before presenting results.

3. **`validate-url-type`** — AF2 support. Classifies a URL as `source` (greenhouse, ashby, lever, workable, rippling, company ATS) or `aggregator` (indeed, linkedin, studysmarter, glassdoor). Used by validate-schema and verify-before-archive. Allowlist-based with fallback to `unknown` (treated as aggregator for verification purposes).

**Enhanced existing subcommands:**

4. **`validate-schema` enhancement** — IF1. Add two new checks: (a) `job_url` must match known ATS URL patterns or contain a job-ID-like path segment (reject `/careers`, `/jobs` without ID), (b) `active_status` must be non-null after any verification run. Uses validate-url-type internally.

5. **`_check_safety_bound` enhancement** — IF9. Detect gap between last run date and today. If gap > 7 days, auto-adjust threshold from 50% to 90% with logged warning: "Long gap detected ({N} days), adjusting safety bound to 90%."

**Bug fixes:**

6. **SyntaxWarning fix** — IF7. Line 1408 docstring: escape `\d` → `\\d` in backtick string.

7. **Dedup --role-types investigation** — IF8. Analysis says "0 input files" but code looks correct. Investigate whether role_types value doesn't match directory slug format. Add test coverage.

### Layer 2 — Orchestration (CLAUDE.md + reference doc edits)

**Gate chaining (the core architectural change):**

8. **Chain commit+push gate** — Wire `verify-and-commit` into the search dispatch loop: before dispatching batch N+1, gate-check verifies batch N was committed. orchestration.md Phase 1 dispatch loop gets: "BEFORE next search batch dispatch, run `manage_state.py verify-and-commit --check-only` for previous batch. If it returns non-zero, STOP — previous batch not committed."

9. **Chain session-state gate** — Wire `verify-session-state-written` into the same loop: before dispatching batch N+1, verify session-state was updated for batch N. "BEFORE next search batch dispatch, run `manage_state.py verify-session-state-written`. If non-zero, STOP."

10. **Chain presentation gate** — Wire `validate-presentation` into the presentation phase: "BEFORE presenting results, run `manage_state.py validate-presentation --role-types {types}`. If non-zero, fix violations first."

11. **Chain verify-before-archive gate** — Wire into any removal recommendation: "BEFORE recommending removal of any job, run `manage_state.py verify-before-archive --input {json_path}`. If status is not `expired`, do NOT recommend removal."

**Resolve contradictions:**

12. **Foreground/background** — IF4. All three CLAUDE.md references already mandate `background: true`. No contradiction exists in the actual code (analysis was incorrect). Verify and leave as-is. If any stale "foreground-only" text exists, remove it.

13. **.done sentinel path** — IF2. Resolve contradiction between orchestration.md (`.channels/{channel}.done`) and search-verify.md (`output/verified/{role_type}/.done`). These are TWO DIFFERENT sentinels: channel-level completion (`.channels/`) and role-type-level completion (`output/verified/`). Clarify both in orchestration.md. Add explicit paths to dispatch variable template: `channel_done_path: "output/.channels/{channel_name}.done"`.

**Strengthen enforcement by design:**

14. **Agent memory via preflight stdout** — IF5. Instead of relying on the agent to read memory files, preflight.sh reads them and prints contents to stdout. Since preflight output is in the parent's context, memory is loaded whether the agent "decides" to read it or not. preflight.sh becomes the enforcement mechanism.

15. **Parent inline Python prevention** — IF6. Restructure CLAUDE.md recovery section: (a) move recovery protocol to immediately after the allowed-scripts list, (b) add explicit "On subagent truncation: re-dispatch with Sonnet tier. NEVER use parent inline Python." (c) remove any ambiguity about what "allowed scripts" means in recovery context.

16. **JobSpy hard constraint** — IF3. Add to channel definitions or search-verify agent: "JobSpy channel MUST run `scripts/jobspy_search.py`. WebSearch/WebFetch fallback is PROHIBITED."

17. **Subagent tier for data reads** — IF11. Add to dispatch guidelines: "Data extraction from multi-file JSON sets MUST use Sonnet tier. Haiku is for mechanical tasks only (gate-checks, file moves, single-file reads)."

### Layer 3 — Validation (tests + preflight enhancements)

**preflight.sh enhancements:**

18. **Touch session-state.md** — IF10. `touch output/session-state.md` if file doesn't exist, preventing Write tool failure on first attempt.

19. **Print agent memory contents** — IF5 enforcement. Read and print `.claude/agent-memory/*/MEMORY.md` to stdout during preflight so contents are in parent context.

20. **Validate no doc contradictions** — Check that orchestration.md and search-verify.md agree on sentinel paths.

**New tests:**

21. **test_verify_before_archive** — Test verify-before-archive subcommand with mocked HTTP responses: live URL, 404 URL, timeout, aggregator URL.

22. **test_validate_presentation** — Test validate-presentation catches: generic career page URLs, null active_status, expired jobs in active list.

23. **test_validate_url_type** — Test URL classification: known ATS patterns → source, aggregator patterns → aggregator, unknown → unknown.

24. **test_schema_url_validation** — Test enhanced validate-schema rejects generic career pages and null active_status.

25. **test_safety_bound_gap** — Test auto-adjustment: 1-day gap uses 50%, 8-day gap uses 90%, 30-day gap uses 90%.

26. **test_dedup_role_types** — IF8. Test dedup --role-types with actual directory slug format.

27. **Regression tests** — Tests that verify gate chaining: (a) verify-and-commit --check-only returns non-zero when no commit exists, (b) validate-presentation returns non-zero with generic URLs, (c) verify-before-archive returns non-zero without HTTP check.

### Data Flow

```
preflight.sh (prints memory, touches session-state, validates docs)
  → Parent context has memory + clean state
    → Phase 1 search dispatch (background subagents)
      → Gate chain: verify-session-state-written → verify-and-commit → next batch
        → Phase 3 verification
          → Gate chain: validate-presentation → present results
            → Gate chain: verify-before-archive → removal recommendations
```

Each gate checks the previous step completed. Skipping a step blocks the next.

## Design Approval Questions

1. **Hardest decision:** Whether to add new enforcement mechanisms (more code, more complexity) vs strengthening existing ones (gate chaining, which is mostly wiring). Chose gate chaining because the gates already work when called — the failure is always "didn't call the gate."

2. **Rejected alternatives:**
   - Constraint Layering: User rejected implicitly — 9-10 versions of text constraints failing is sufficient evidence.
   - External Enforcement: Doesn't apply to in-session agent orchestration.

3. **Least confident aspect:** User identified foreground/background dispatch — resolved by confirming no actual contradiction exists in CLAUDE.md (analysis was incorrect). Background dispatch stays. Second concern: gate chain bugs could block sessions — mitigated by `--check-only` flag on verify-and-commit (non-destructive check) and clear error messages that tell the agent exactly what to fix.

## Success Criteria

1. Zero presentations with generic career page URLs (validate-presentation gate)
2. Zero removal recommendations without verify-before-archive proof returning "expired"
3. No aggregator-only URLs accepted as primary verification source
4. Gate chain blocks next step when previous step skipped (testable via --check-only)
5. Agent memory contents appear in preflight stdout (no agent reading required)
6. All new subcommands have test coverage (>=5 tests each)
7. No SyntaxWarning from manage_state.py
8. Safety bounds auto-adjust for gaps >7 days
9. Session-state.md first write succeeds without error

## Risks

1. **Gate chain too strict** — If a gate has a bug or edge case, it blocks the entire session. Mitigation: all gates have `--check-only` or dry-run modes, and clear error messages.
2. **URL classification false positives** — Allowlist may miss unusual ATS providers. Mitigation: `unknown` type treated conservatively (as aggregator), not rejected outright.
3. **IF8 (dedup --role-types)** — May have a deeper bug than parsing. Mitigation: investigate during build, add comprehensive test coverage.
4. **verify-before-archive HTTP reliability** — URLs may timeout, return ambiguous status codes. Mitigation: `unreachable` verdict means "do NOT remove" — conservative default.

## Known Risks Passed to /plan

1. Gate chain ordering must be specified per-phase in the plan — wrong ordering could create deadlocks
2. URL classification allowlist needs to be comprehensive — plan must specify initial ATS patterns
3. verify-before-archive HTTP logic needs timeout handling and retry strategy
4. IF8 investigation may reveal the bug is in directory slug matching, not arg parsing — plan should include investigation step before fix

## Handoff Contract
- Approach: Gate Chaining + Verification Infrastructure, Three-Layer build
- Components: (L1) 3 new manage_state.py subcommands + 2 enhanced + 2 bug fixes, (L2) 4 gate chains + 2 contradiction resolutions + 4 enforcement strengthening, (L3) 3 preflight enhancements + 7 test suites
- Success criteria: zero generic URLs in presentations, zero unverified removals, gate chains block on skip, memory in preflight stdout, all new subcommands tested
- Risks requiring mitigation: gate chain ordering, URL allowlist completeness, HTTP reliability, IF8 investigation
- Known risks for /plan: gate chain deadlock ordering, ATS pattern list, timeout strategy, dedup bug investigation

<!-- STAGE COMPLETE: /design, 2026-03-23 -->

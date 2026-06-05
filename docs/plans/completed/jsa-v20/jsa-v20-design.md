# Design: JSA V20 — Scheduling Fix + Implementation Fixes

## Context

V19 build completed successfully (14/14 steps, 101 tests pass) but runtime exposed 13 failures: 1 architectural (scheduling — 0% success rate across 4 consecutive GitHub Actions runs) and 12 implementation fixes (CLAUDE.md constraint violations, script bugs, regression recurrences). The V19 analysis evaluated 4 scheduling alternatives and recommended fixing GitHub Actions (Option A) as the lowest-effort path. The V19 compound phase promoted 7 solutions and identified 4 regression recurrences that indicate constraint enforcement needs strengthening.

**Key inputs:**
- V19 analysis: 13 failures (3 critical, 6 major, 4 minor)
- V19 compound: 6 decisions, 7 promoted solutions, 5 actionable proposals
- 4 regression recurrences (dedup, dashboard URL, incremental commit, agent memory) — these have been "fixed" in prior versions but keep recurring
- Scheduling research: 4 options evaluated across 5 subagents

## Options Considered

### Option 1: Single Phase — All 13 Fixes
- All fixes (workflow YAML + 12 CLAUDE.md/script changes + regression tests) in one phase
- Pros: Simplest structure, no coordination overhead, V19 proved single-phase works for constraint-type fixes (14/14 steps), scheduling fix is small (one YAML file with ~5 changes)
- Cons: Mixes infrastructure (YAML) with constraint edits; if YAML syntax error breaks the workflow, it's caught by manual dispatch test, not by phase isolation
- Risk: Low — most fixes are text constraint additions (same domain as V19)
- Failure mode: YAML syntax error blocks scheduling but doesn't affect other fixes; can be tested independently via manual `workflow_dispatch`
- **Chosen**

### Option 2: Two-Phase (Infrastructure + Constraints)
- Phase 1: Scheduling fixes (GH Actions workflow repair, settings allowlist)
- Phase 2: 12 implementation fixes (CLAUDE.md constraints, script fixes, regression tests)
- Pros: Clean isolation; scheduling can be tested independently before proceeding
- Cons: Two build sessions; scheduling fix is too small (one YAML file) to warrant its own phase — the overhead of phase isolation exceeds the benefit
- Risk: Low — familiar pattern from V18
- Failure mode: Phase boundary creates artificial dependency between independent fixes
- **Rejected:** Scheduling fix is too small (one YAML file, ~5 changes) to warrant its own phase — adds coordination overhead without debuggability gain.

### Option 3: Three Layers (Scheduling → Regressions → New Fixes)
- Layer 1: Fix scheduling (workflow YAML, settings, timeout, permissions)
- Layer 2: Fix the 4 regression recurrences with stronger enforcement mechanisms
- Layer 3: Fix the remaining 8 new failures
- Pros: Prioritizes the most impactful issues; regressions get special treatment
- Cons: Heavyweight for text edits; three phases create artificial boundaries between fixes that are actually independent and can all be verified in a single test run
- Risk: Medium — more coordination overhead, potential for phase 1/2 blocking phase 3 unnecessarily
- Failure mode: Phase boundaries create artificial dependencies; regressions need enforcement mechanism changes (not phase isolation) to stop recurring
- **Rejected:** Three phases is heavyweight for what are mostly text constraint additions — regressions need stronger enforcement mechanisms, not separate phases.

## Prototyping Results
Prototyping skipped — no triggers met. All fixes use existing patterns (CLAUDE.md text edits, YAML workflow configuration, Python script modification). No new technologies, unverifiable APIs, or concurrent state management.

## Chosen Approach

**Option 1: Single Phase — All 13 Fixes.**

Rationale: V19 proved single-phase works for constraint-type fixes (14/14 steps, 101 tests pass). The scheduling fix is small enough to include alongside the 12 implementation fixes. The YAML workflow can be independently verified via manual `workflow_dispatch` regardless of phase structure.

The key insight for V20 is not phase structure but **enforcement strength**. The 4 regression recurrences show that simply adding constraints to CLAUDE.md is necessary but insufficient. V20 must implement stronger enforcement mechanisms for the recurring failures.

## Architecture

### Components

1. **Scheduling Infrastructure** (1 file: `daily-digest.yml`)
   - Fix version path reference (v18 → v20)
   - Increase timeout to 90 minutes (fits within GH Actions free tier at 5 runs/week)
   - Add `--dangerously-skip-permissions` flag for headless execution
   - Create `settings.local.json` inline instead of expecting it to exist
   - Add retry logic (`nick-fields/retry@v3`) with 2 attempts
   - Add preflight checks (Claude CLI available, API key set)

2. **CLAUDE.md Constraint Fixes** (1 file: `CLAUDE.md`)
   - Failure 1: Add `working_dir` variable to dispatch templates, enforce version path in subagent prompts
   - Failure 4: Add dashboard URL storage requirement to `context.md` and presentation steps
   - Failure 5: Elevate incremental commit+push to hard constraint with verification step
   - Failure 6: Add HC: no `python3 scripts/*` in parent context
   - Failure 8: Reinforce HC1 (no model param in Task tool) in dispatch templates
   - Failure 9: Add `_summary.md` requirement to CM subagent + recovery protocol fallback
   - Failure 10: Replace `rm -f dir/*` with `find -delete` in cleanup commands
   - Failure 11: Enforce table format for all role types in presentation
   - Failure 12: Fix agent memory Glob pattern + assert match count > 0

3. **Regression Prevention Layer** (new enforcement patterns for 4 recurrences)
   - Failure 3 (dedup): Content-based dedup in `manage_state.py` + presentation-layer dedup safety net
   - Failure 4 (dashboard URL): Post-presentation verification step asserting URL presence
   - Failure 5 (incremental commit): Post-batch verification step asserting commit happened
   - Failure 12 (agent memory): Startup assertion with count > 0 + failure-to-STOP if no memories loaded

4. **Script Fix** (1 file: `manage_state.py`)
   - Failure 3: Add content-based dedup (normalize company+title+location → hash → deduplicate)

5. **Agent Definition Updates** (named agents in `.claude/agents/`)
   - Update `search-verify.md`: Add `working_dir` variable
   - Update `brief-generator.md`: Add `working_dir` variable
   - Update `digest-email.md`: Add `working_dir` variable, dashboard URL requirement

6. **Settings Allowlist** (1 file: `.claude/settings.local.json`)
   - Failure 7: Ensure Bash command allowlist covers all commands agents need
   - Must be created by workflow in CI (not gitignored dependency)

7. **Regression Tests** (verification assertions in CLAUDE.md and test scripts)
   - Working directory assertion: All subagent outputs land in correct version directory
   - Workflow path assertion: `daily-digest.yml` references correct version
   - Content-based dedup test: Duplicate jobs with same content but different filenames are caught
   - Dashboard URL presence test: Presentation output includes Vercel URL
   - Scheduled run success assertion: Manual `workflow_dispatch` completes successfully

### Data Flow

```
GitHub Actions cron (6am UTC weekdays)
  → daily-digest.yml (preflight checks → create settings.local.json → invoke Claude CLI with --dangerously-skip-permissions)
    → CLAUDE.md orchestrator (reads agent memory → dispatches subagents with working_dir variable)
      → source-researcher → search-verify (content-based dedup via manage_state.py) → brief-generator → briefs-html + digest-email
        → Presentation output (dashboard URL verified) → Incremental commit+push (verified after each batch) → Email send
```

### Enforcement Mechanism Upgrade (Regression Prevention)

For the 4 regression recurrences, V20 adds **verification steps** — not just constraints but active checks that STOP execution if violated:

| Regression | V19 Approach (failed) | V20 Approach |
|------------|----------------------|--------------|
| Cross-role dedup | Text constraint in CLAUDE.md | Content-based dedup in `manage_state.py` (code enforcement) + presentation-layer safety net |
| Dashboard URL | Text constraint in CLAUDE.md | Post-presentation `grep` assertion: if URL missing, STOP and fix |
| Incremental commit | Text constraint in CLAUDE.md | Post-batch `git log` assertion: if no commit in last N minutes, STOP and commit |
| Agent memory | Text constraint in CLAUDE.md | Startup `glob count > 0` assertion: if no memories loaded, STOP with error |

The pattern: **text constraints → code/assertion enforcement** for recurring failures.

## Design Approval Questions

1. **Hardest decision:** Single-phase vs two-phase. Single-phase was chosen because the scheduling fix is small (one YAML file, ~5 changes) and all other fixes are CLAUDE.md text constraints — the same failure domain V19 proved works in single-phase. The rejected two-phase alternative adds coordination overhead without debuggability gain since the YAML fix can be independently verified via manual `workflow_dispatch` regardless of phase structure.

2. **Rejected alternatives:**
   - Two-Phase: Scheduling fix is too small (one YAML file, ~5 changes) to warrant its own phase — adds coordination overhead without debuggability gain.
   - Three Layers: Heavyweight phase structure for text edits — regressions need stronger enforcement mechanisms (code/assertions), not separate build phases.

3. **Least confident aspect:** Regression prevention enforcement. The 4 recurrences suggest constraints alone don't work. V20 upgrades to code/assertion enforcement, but the agent might still skip verification steps if they're text instructions rather than hard-coded checks. The `manage_state.py` content-based dedup is genuine code enforcement, but the CLAUDE.md assertion steps (grep for URL, git log for commits, glob count for memory) still rely on the agent following instructions. If these fail again in V20, V21 should consider a pre-run validation script that checks all invariants programmatically.

## Success Criteria

1. **Scheduled run success:** Manual `workflow_dispatch` completes without errors (exit code 0)
2. **5 consecutive scheduled runs without failure** (measured over 1 week after deployment)
3. **0 regression recurrences** for the 4 identified patterns (dedup, URL, commit, memory) in next test run
4. **Content-based dedup catches duplicates:** Test with 2 jobs having identical company+title+location but different filenames — both should resolve to 1 entry
5. **All 12 implementation fixes verified:** Each fix has a corresponding regression test that passes
6. **Timeout within free tier:** 90-minute timeout, 5 runs/week fits within 2,000 minutes/month

## Risks

1. **GH Actions environment flakiness:** Even with fixes, CI environments can have transient failures (network, rate limits). Mitigation: retry logic with 2 attempts.
2. **`--dangerously-skip-permissions` too permissive:** Bypasses all permission checks, not just the ones we need. Mitigation: this is acceptable for a scheduled headless run where the agent definition is trusted and version-controlled.
3. **90-minute timeout still too tight:** If the agent takes >90 min on a complex run, the job gets killed. Mitigation: 90 min is 2x the observed max (45 min); if consistently hitting timeout, increase to 120 min and accept going slightly over free tier.
4. **Assertion steps add runtime overhead:** Each verification step (grep, git log, glob) adds seconds. Mitigation: negligible overhead (<5 seconds total).

## Known Risks Passed to /plan

1. **Regression enforcement durability:** The CLAUDE.md assertion steps (grep for URL, git log for commits, glob count for memory) still rely on the agent following text instructions. If these fail again, `/plan` should include a fallback: a `preflight.sh` script that runs before the agent and checks invariants programmatically.
2. **Settings.local.json in CI:** The workflow must create this file inline. The format must match what the agent expects. `/plan` should specify the exact JSON content.
3. **Version path coordination:** Multiple files reference the version path (workflow YAML, CLAUDE.md, agent definitions). `/plan` must ensure all are updated atomically.
4. **Content-based dedup implementation:** The hashing/normalization logic in `manage_state.py` must handle edge cases (different formatting, extra whitespace, URL variations). `/plan` should specify the exact normalization rules.

## Handoff Contract

- Approach: Single Phase — All 13 Fixes
- Components: Scheduling infrastructure (daily-digest.yml), CLAUDE.md constraint fixes (9 fixes), regression prevention layer (4 assertion-based enforcement upgrades), script fix (manage_state.py content-based dedup), agent definition updates (3 agents), settings allowlist, regression tests (5 verification assertions)
- Success criteria: Manual workflow_dispatch completes, 5 consecutive scheduled runs without failure, 0 regression recurrences, content-based dedup catches test duplicates, all 12 implementation fixes verified, 90-min timeout fits free tier
- Risks requiring mitigation: GH Actions flakiness (retry logic), permissions bypass (acceptable for trusted agent), timeout tightness (2x buffer), assertion overhead (negligible)
- Known risks for /plan: Regression enforcement durability (text instructions may not be followed — consider preflight.sh fallback), settings.local.json exact format, version path coordination across files, content-based dedup normalization rules

<!-- STAGE COMPLETE: /design, 2026-02-18 -->

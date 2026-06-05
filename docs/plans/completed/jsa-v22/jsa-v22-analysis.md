# Session Analysis: JSA V22

## Summary
6 wins, 8 failures (3 critical, 3 major, 2 minor), 3 edge cases. 6/28 constraints failed, 2 partial. Session produced 14 verified roles at 70+ across 5 search channels, 4 briefs generated and emailed, but required heavy user prompting to achieve search breadth and suffered a critical dedup failure from stale prior-run directories.

## What Went Well

1. **5-channel search architecture delivered strong results once assembled**: JobSpy produced 9 of 14 qualifying roles (highest: Tessl 88, Pangaea Data 87). Newsletter channel found JigsawStack Founding GTM (84) via Early & Exec — neither would have appeared from career pages alone.
2. **Dedup failure detected and recovered quickly**: Parent dispatched a recovery subagent within ~2 minutes of detecting the dedup archived all results. Root cause (stale prior-run directories) was correctly diagnosed without reading individual verified JSONs in parent.
3. **CI preflight fix was surgical and verified**: The `settings.local.json` CI failure was root-caused from one `gh run view --log-failed` call, fixed with a 2-part patch (SCHEDULED_RUN guard in preflight.sh + env var propagation in workflow), and re-triggered to confirm the fix advanced past the previous failure point.
4. **Parallel brief generation worked cleanly**: 4 brief-generator agents ran concurrently and all completed successfully. Digest email and briefs HTML also dispatched in parallel without errors.
5. **User feedback integrated without re-search**: When user flagged "senior not similar" (Lead titles too senior), parent pivoted to reading summaries across completed batches and surfaced associate-level roles immediately.
6. **Memory writes were timely**: V23 improvement notes (5-channel mandate, context-aware dedup, search breadth) were written to agent memory during the session rather than deferred.

## What Failed

### Failure 1: Rate limit hit on first subagent dispatch
- **What happened:** Both search-verify Batch 1 and Batch 2 subagents hit the Claude Max usage rate limit ("You've hit your limit · resets 4pm") within ~80 seconds. Batch 1 returned stale Feb 19 data from prior run output files. Batch 2 wrote nothing at all.
- **Root cause:** No pre-dispatch check for rate limit headroom. Background subagents consume tokens immediately on dispatch; with two parallel agents, the cap was hit before either could complete meaningful work.
- **Category:** subagent-coordination
- **Prevention:** Automated: No — Rate limit timing is external to the agent; no static check can predict when the cap resets.
- **Principle violated:** No explicit constraint, but HC10 (mandatory dispatch variables) was violated — there is no rate-limit-aware dispatch protocol.
- **Fix type:** Implementation

### Failure 2: Search breadth defaulted to 2 batches — user had to prompt for all 5 channels
- **What happened:** Agent dispatched only 2 batches covering ~25 company career pages. User had to explicitly prompt 3 times for: job aggregators, JobSpy, and niche newsletters. The 5-channel search architecture was only assembled because of user intervention.
- **Root cause:** The orchestration layer treats search channels as optional additions rather than mandatory infrastructure. No enforcement mechanism ensures all 5 channels are dispatched on every run.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — architecture-strategist reviewer can verify Phase 1 mandates all 5 channels. Prompt added.
- **Principle violated:** V23 Required Improvement (Search Breadth) in agent memory — documented but not enforced in code.
- **Fix type:** Architectural

### Failure 3: Dedup archived all new results (context-unaware dedup)
- **What happened:** `manage_state.py dedup` archived ALL jobs including today's fresh results. Old role-type directories (community-manager, marketing-manager, etc.) from prior runs remained in `output/verified/`. The script cross-referenced new results against stale directories, treating today's findings as duplicates.
- **Root cause:** The dedup script scans all subdirectories in `output/verified/` with no awareness of which role types are active for the current run. When focus pivoted from 5 role types to "AI agent roles only," old directories interfered.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — can detect stale role-type dirs before dedup runs. Check: `find output/verified/ -maxdepth 1 -type d | grep -Ev "/(ai-agent-roles|_prior)" | grep -v "^output/verified/$"`
- **Principle violated:** V23 Required Improvement (Dedup Must Be Context-Aware) in agent memory — documented but not enforced.
- **Fix type:** Architectural

### Failure 4: CI preflight required settings.local.json in SCHEDULED_RUN context
- **What happened:** The workflow_dispatch test failed immediately with "CRITICAL: Required permissions missing from settings.local.json." The preflight script required the file even in CI, where claude-code-base-action handles permissions via `allowed_tools` instead.
- **Root cause:** Preflight script had no CI-mode guard. The `settings.local.json` check ran unconditionally. This was a known issue since V20 (documented in agent memory) that was not addressed during V22 build.
- **Category:** configuration
- **Prevention:** Automated: Yes — static check on preflight script: `grep -n "settings.local.json" scripts/preflight.sh | grep -v "SCHEDULED_RUN"`
- **Principle violated:** V19 regression: "GitHub Actions workflow must generate CI-only config files or use --dangerously-skip-permissions"
- **Fix type:** Implementation (fixed in-session)

### Failure 5: Workflow missing SCHEDULED_RUN env var for preflight step
- **What happened:** The fix to skip settings.local.json in CI relied on `$SCHEDULED_RUN`, but the workflow only passed it to the Claude action step — not to the preceding preflight bash step. Required a second patch commit.
- **Root cause:** Environment variable scoping in GitHub Actions was not checked holistically — the fix was applied to only one consumer of the variable.
- **Category:** configuration
- **Prevention:** Automated: Partial — deployment-verifier can check that all bash steps have necessary env vars. Prompt added.
- **Principle violated:** No explicit constraint — oversight in variable propagation.
- **Fix type:** Implementation (fixed in-session)

### Failure 6: Vercel dashboard not redeployed after data push
- **What happened:** The run committed and pushed new verified jobs and state files, but no Vercel redeploy was executed. The dashboard serves from bundled deployment files and does NOT auto-deploy from git pushes. This is a documented regression from V21.
- **Root cause:** No enforcement mechanism in the orchestration layer triggers redeploy after data pushes. The requirement exists only in agent memory, not as a coded step.
- **Category:** deployment
- **Prevention:** Automated: Partial — deployment-verifier can check for post-push Vercel deploy step. Prompt added.
- **Principle violated:** V21 regression: "Vercel dashboard must be re-linked and redeployed on every version transition" and agent memory Hard Constraint.
- **Fix type:** Implementation

### Failure 7: Incremental commit after each search batch was skipped
- **What happened:** HC7 requires committing and pushing after each search batch in interactive mode. All 5 batches ran, then dedup, presentation, briefs, and email — with only a single combined commit at the end.
- **Root cause:** No enforcement gate between search batches that requires a commit before the next batch can proceed. This is the 7th occurrence (V14/V16/V18/V19/V20/V21/V22).
- **Category:** uncategorized
- **Prevention:** Automated: Partial — regression-checker already has this item. Needs hard enforcement (post-batch commit gate in orchestration).
- **Principle violated:** HC7 (Incremental commit+push after every search batch)
- **Fix type:** Architectural (needs hard enforcement mechanism, not just a constraint)

### Failure 8: Session-state.md not written after each search batch
- **What happened:** session-state.md was written at startup and at delivery, but not after each search batch completed. This is the 6th occurrence (V14/V16/V18/V19/V21/V22).
- **Root cause:** Same as Failure 7 — no enforcement gate between batches. The requirement is documented but not enforced by any mechanism.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — regression-checker already has this item. Needs hard enforcement.
- **Principle violated:** Core Rule 10 (session-state.md after every search batch)
- **Fix type:** Architectural (needs hard enforcement, same mechanism as Failure 7)

## Constraint Compliance Summary

| Category | Pass | Fail | Partial | N/A |
|----------|------|------|---------|-----|
| Hard Constraints (HC1-HC11) | 7 | 3 | 0 | 0 |
| Core Rules (CR1-CR12) | 7 | 2 | 1 | 2 |
| Startup & Ops | 3 | 1 | 1 | 0 |
| **Total** | **19** | **6** | **2** | **2** |

Key recurring failures: HC7 (incremental commit — 7th occurrence), CR10 (session-state after batch — 6th occurrence), startup git pull (4th+ occurrence).

## Fixes Needed

### Architectural Fixes

**Fix A1: Mandatory 5-channel search dispatch**
- **What needs to change:** Phase 1 of the orchestration layer must define all 5 search channels as parallel dispatches that fire on every run with zero user prompting. Channel content adapts to context.md; channel existence is fixed infrastructure.
- **Files affected:** `references/orchestration.md`, `context.md` (## Search Channels section), agent CLAUDE.md (Phase 1 definition)
- **Verification criteria:** Dispatching search with no user prompts beyond "run" produces agents for all 5 channels: direct career pages, industry job boards, JobSpy aggregator, niche newsletters, web search discovery.

**Fix A2: Context-aware dedup with --role-types flag**
- **What needs to change:** `manage_state.py dedup` must accept a `--role-types` flag listing active role type slugs for the current run. It deduplicates only across those directories, ignoring others. Optionally, the parent archives stale directories before search begins when focus changes.
- **Files affected:** `scripts/manage_state.py`, orchestration references (dedup step), tests
- **Verification criteria:** After a focus pivot (e.g., 5 role types → 1), dedup with `--role-types ai-agent-roles` only processes that directory. Old directories are untouched.

**Fix A3: Hard enforcement gate for post-batch commit + session-state write**
- **What needs to change:** The orchestration layer needs a structural enforcement mechanism — not just a constraint, but a gate that prevents the next batch from dispatching until the previous batch's results are committed and session-state.md is updated. This is the 7th and 6th occurrence respectively.
- **Files affected:** `references/orchestration.md`, possibly `scripts/manage_state.py` (add a `verify-batch-committed` subcommand)
- **Verification criteria:** After each batch completes, `git status` shows no uncommitted verified files before the next batch dispatches. session-state.md has an entry for the batch.

### Implementation Fixes

**Fix I1: Add rate-limit recovery protocol to dispatch**
- **What needs to change:** The dispatch protocol should include: (a) a lightweight pre-dispatch check (e.g., a trivial test agent), (b) on rate limit detection, surface "Rate limit hit — wait until {reset_time} or continue with existing data?" instead of silently returning stale data.
- **Files affected:** Agent CLAUDE.md (dispatch protocol section), `references/orchestration.md`
- **Verification criteria:** When rate limit is hit, the parent detects it from the subagent output (no stale data presented as fresh) and offers options.

**Fix I2: Vercel redeploy as mandatory post-push step**
- **What needs to change:** The delivery phase must include `vercel link --project jsa-dashboard --yes && vercel --prod --yes` as a mandatory step after every commit+push that updates `output/verified/` or `output/_delta.json`. This should be a named step in orchestration.md, not a memory-only requirement.
- **Files affected:** `references/orchestration.md` (Phase 5 delivery), agent CLAUDE.md (HC or post-delivery checklist)
- **Verification criteria:** After push, `curl -s https://jsa-dashboard.vercel.app/api/state` returns today's `run_date`.

**Fix I3: Git pull enforcement on startup**
- **What needs to change:** Startup sequence must include `git pull` before any file reads. The preflight script should enforce this or the startup checklist should be a hard-coded sequence.
- **Files affected:** `scripts/preflight.sh` or agent CLAUDE.md startup section
- **Verification criteria:** `git log --oneline -1` output matches remote HEAD after startup completes.

**Fix I4: Absolute file paths in output presentation**
- **What needs to change:** When presenting output files to the user, the agent must use absolute paths (e.g., `/Users/.../output/briefs/briefs-2026-02-23.html`), not relative paths.
- **Files affected:** Agent CLAUDE.md (presentation section or CR7)
- **Verification criteria:** All file paths shown to user start with `/`.

**Fix I5: Session resume guard**
- **What needs to change:** On startup, if `output/digests/_status.json` has `sent_at` matching today, surface "Today's run already completed. Resume or start fresh?" instead of silently re-initializing. Prevents the duplicate session pattern observed in the transcript.
- **Files affected:** Agent CLAUDE.md (startup sequence), `scripts/preflight.sh`
- **Verification criteria:** Starting a second session on the same day shows a resume prompt.

## Solutions Extracted

1. **Rate limit recovery pattern**: Read summary files to detect stale/missing output → surface options to user → re-dispatch on user signal. No special retry logic needed — identical dispatch structure works. (Category: subagent-coordination, Transferable: Yes)

2. **Recovery subagent for data corruption**: Dispatch a recovery subagent to restore archived files rather than fixing inline in parent context. Note root fix for next version rather than improvising a mid-run patch. (Category: data-integrity, Transferable: Yes)

3. **CI debugging pattern**: Read failing script before editing → check env var propagation to each step independently → re-trigger and verify new run advances past previous failure point. (Category: configuration, Transferable: Yes)

4. **Multi-channel search assembly**: 5 fixed channels (direct sources, industry boards, JobSpy multi-query, niche newsletters, web discovery) with content adapted to user context. Career pages alone yield diminishing returns for non-engineering roles; aggregators and newsletters produce the strongest novel finds. (Category: subagent-coordination, Transferable: Yes)

5. **Design system skill preloading**: Call `Skill(compound-engineering:frontend-design)` in parent before dispatching visual output subagents to ensure cohesion. Avoids per-subagent style drift. (Category: design-system, Transferable: Yes)

6. **Selection confirmation before dispatch**: Read source data to confirm mapping before dispatching parallel brief generators. User's "7 not 6" correction was caught before any wasted agent dispatch. (Category: subagent-coordination, Transferable: Yes)

## Patterns Identified

1. **Parallel Batch Dispatch with Progressive Result Collection** (Skill candidate: Yes)
   - Dispatch N independent work units as background subagents → each writes `_summary.md` + `_status.json` → parent polls and reads only summaries → consolidate into ranked result set
   - Appeared in: search (5 batches), briefs (4 generators), delivery (2 agents)
   - Generalization: What changes per agent: subagent definition, output directory, summary format. What stays the same: fan-out with background:true, polling `_status.json`, reading only `_summary.md`.

2. **Detect-Diagnose-Note-Defer Error Recovery** (Skill candidate: Yes)
   - Observe unexpected outcome → diagnose root cause from minimal file reads → determine if in-session fixable or requires version increment → either fix+commit+verify OR write structured memory note and defer → continue session
   - Appeared in: dedup failure (defer), rate limit (wait+retry), CI preflight (fix in-session)

3. **Context Update Then State Sync Commit** (Skill candidate: No — JSA-specific file paths)
   - Read context → update context with new focus → update session-state → pipeline runs → read-before-write on session-state → append results → stage specific files → commit

4. **Test-First Infrastructure Build** (Skill candidate: Yes)
   - Fixture → test class → implementation → lint+test gate → next subcommand
   - Appeared in: Plan Steps 2-5 (checkpoint infrastructure)

## Build Metrics

- **Build duration (total):** Unavailable (no wall-clock timing in progress file)
- **Steps completed:** 18 / 18
- **Verification pass rate:** 3 / 3 phase capability checks passed
- **Regression count (new):** 0
- **Regression count (repeat):** 1 category (3 pre-existing ruff lint warnings)
- **Review cycle count:** 3 (from review-progress.md)
- **Test count progression:** 32 → 126 → 132 (monotonically increasing, no regressions between phases)
- **Session failures:** 8 (3 critical, 3 major, 2 minor)

## Handoff Contract
- Architectural fixes: 3 — (A1) Mandatory 5-channel search dispatch, (A2) Context-aware dedup with --role-types, (A3) Hard enforcement gate for post-batch commit + session-state write
- Implementation fixes: 5 — (I1) Rate-limit recovery protocol, (I2) Vercel redeploy as mandatory post-push step, (I3) Git pull enforcement on startup, (I4) Absolute file paths in output, (I5) Session resume guard
- New constraints: Session resume guard (I5), rate-limit pre-dispatch check (I1)
- Regression tests to include: dedup with stale directories, CI preflight in SCHEDULED_RUN mode, post-batch commit verification
- Prevention artifacts written: 3 reviewer prompt additions (architecture-strategist, deployment-verifier, regression-checker)
- Metrics recorded: V22 session — 18/18 steps, 132 tests, 8 failures (3C/3M/2m), 3 review cycles

<!-- STAGE COMPLETE: /analyze, 2026-02-24 -->

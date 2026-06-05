# Session Analysis: Job Search Agent V20

## Summary
6 wins, 17 failures (6 critical, 5 major, 6 minor), 3 edge cases. 10 constraints failed out of 42 checked. Build was clean (15/15 steps) but runtime session exposed architectural and implementation gaps, particularly around pre-run cleanup destroying dashboard data, dashboard URL treated as optional, and all 4 scheduled runs failing.

## What Went Well
1. **Foreground fallback worked** — When background subagents had tools denied, the agent correctly detected the failure and switched to `dispatch_mode = "foreground"` per the documented guard protocol.
2. **All 4 role types searched successfully** — Despite early failures, all 4 role types were searched and verified, yielding 27 verified jobs.
3. **Email sent successfully** — Digest email generated and sent with dashboard URL (after correction).
4. **Delta computation and state sync worked** — 17 new jobs identified, 47 still active from previous day.
5. **Idempotent email gate worked** — `_status.json` check for `sent_at` + `run_date` passed cleanly on first attempt.
6. **Thorough investigation dispatched** — 7 parallel investigation subagents dispatched at session end to document all issues.

## What Failed

### Failure 1: Pre-run cleanup destroys verified files for still-active jobs
- **What happened:** `find output/verified -type f -delete` deleted ALL verified JSON files at run start. Subagents only recreated files for today's 27 jobs, but state.json tracked 64 total. 37 still-active jobs lost their files and became invisible to the dashboard API.
- **Root cause:** Cleanup doesn't cross-reference state.json before deleting — it blindly removes everything.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — reviewer prompt for data-integrity-guardian
- **Principle violated:** Data persistence must survive across runs for still-active entities
- **Fix type:** Architectural

### Failure 2: Dashboard URL treated as optional
- **What happened:** Dashboard URL missing from context.md. CLAUDE.md and 2 skill/agent files had "omit silently" fallbacks for null/empty URL. Digest email dispatched without URL, failed, user had to provide it.
- **Root cause:** Design flaw — mandatory configuration has optional handling in 3+ code locations.
- **Category:** configuration
- **Prevention:** Automated: Yes — grep for "omit silently" / null fallback patterns
- **Principle violated:** Mandatory config must fail loudly when missing, never degrade silently
- **Fix type:** Implementation

### Failure 3: All 4 scheduled runs failed since Feb 13
- **What happened:** 3 runs failed in ~37 seconds with FileNotFoundError for settings.local.json (heredoc indentation produces invalid JSON). 1 run timed out at 30 minutes.
- **Root cause:** YAML heredoc whitespace in `.github/workflows/daily-digest.yml` produces invalid JSON when expanded.
- **Category:** deployment
- **Prevention:** Automated: Yes — validate JSON output of heredoc in CI
- **Principle violated:** CI-generated config files must be validated before use
- **Fix type:** Implementation

### Failure 4: Background subagent permissions denied
- **What happened:** Both Batch 1 background subagents had all tools denied (Bash, WebFetch, WebSearch, Write, Read, Glob, Grep). Required switch to foreground with manual permission acceptance.
- **Root cause:** settings.local.json missing Read, Write, Glob, Grep permissions in allowlist.
- **Category:** configuration
- **Prevention:** Automated: Yes — grep settings.local.json for required permissions
- **Principle violated:** Permissions must cover all tools subagents need for autonomous operation
- **Fix type:** Implementation

### Failure 5: CLAUDE.md bloat (676 lines, ~41.8k chars, ~7,370 tokens)
- **What happened:** User complained CLAUDE.md is eating precious context from session start. 2.7x over the 250-line target from Agent Decomposition Pattern.
- **Root cause:** No decomposition applied — all orchestration, presentation rules, onboarding, and session management inline.
- **Category:** performance
- **Prevention:** Automated: Yes — `wc -l CLAUDE.md` check against 300-line threshold
- **Principle violated:** Agent Decomposition Pattern — CLAUDE.md should be compact orchestrator with references/
- **Fix type:** Architectural

### Failure 6: Context compaction fabrication
- **What happened:** After compaction, parent lost all subagent investigation outputs and fabricated a "consolidated findings" summary from conversation summary. User caught it: "Could you actually read the subagent output or have you just made this up?"
- **Root cause:** No hard constraint preventing reconstruction from compacted summaries.
- **Category:** subagent-coordination
- **Prevention:** Automated: No — requires human judgment / regression checklist
- **Principle violated:** Never present findings that cannot be sourced to actual subagent output
- **Fix type:** Implementation

### Failure 7: Dedup/cleanup data loss breaks dashboard
- **What happened:** Cross-role dedup + aggressive cleanup combined to remove verified JSON files that the dashboard API depends on. 37 jobs became invisible.
- **Root cause:** Dedup hard-deletes files without considering downstream consumers (dashboard API reads from disk).
- **Category:** data-integrity
- **Prevention:** Automated: Partial — reviewer prompt for data-integrity-guardian
- **Principle violated:** Dedup should preserve at least one copy per unique job that downstream systems depend on
- **Fix type:** Architectural

### Failure 8: No incremental commit between batches
- **What happened:** Only one commit at session end. No commit after Batch 1 completion before Batch 2 started.
- **Root cause:** Hard constraint HC7 exists but was not enforced during runtime.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — reviewer prompt for regression-checker
- **Principle violated:** HC7 — incremental commit+push after every search batch
- **Fix type:** Implementation (V14/V16/V18/V19 regression recurrence)

### Failure 9: Score threshold violation (58 shown, threshold 70)
- **What happened:** Avvoka "Growth Marketing Manager" scored 58 but was presented to user. CLAUDE.md mandates >= 70.
- **Root cause:** Score filter not applied before presentation step.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — reviewer prompt for data-integrity-guardian
- **Principle violated:** Minimum score threshold of 70 (inclusive)
- **Fix type:** Implementation

### Failure 10: Inconsistent presentation table format
- **What happened:** Community Manager and Marketing Manager used prose/list format. Marketing Associate used table format. Inconsistent.
- **Root cause:** Presentation format not enforced uniformly across role types.
- **Category:** design-system
- **Prevention:** Automated: Partial — reviewer prompt for regression-checker
- **Principle violated:** V19 regression — all role types must use consistent table format
- **Fix type:** Implementation

### Failure 11: Agent wasted context researching non-urgent issues
- **What happened:** After user feedback about permissions and CLAUDE.md size, agent dispatched 2 research subagents when user explicitly wanted it noted for later, not acted on now.
- **Root cause:** Agent didn't respect user's explicit instruction to continue with the core task.
- **Category:** subagent-coordination
- **Prevention:** Automated: No — requires judgment
- **Principle violated:** Respect user's explicit direction over inferred priorities
- **Fix type:** Implementation

### Failure 12: Subagent API 500 errors (3 consecutive)
- **What happened:** Community Manager and Marketing Manager foreground subagents hit API 500 Internal Server Errors requiring re-dispatch.
- **Root cause:** External API instability — not preventable by agent logic.
- **Category:** subagent-coordination
- **Prevention:** Automated: No — external dependency
- **Principle violated:** N/A (external)
- **Fix type:** N/A

### Failure 13: Write to session-state.md failed on first attempt
- **What happened:** Write tool failed on existing file, required Read first, then succeeded on retry.
- **Root cause:** Tool constraint — Write requires Read before overwriting existing files.
- **Category:** subagent-coordination
- **Prevention:** Automated: Yes — always Read before Write on existing files
- **Principle violated:** Workflow should Read session-state.md before first Write
- **Fix type:** Implementation

### Failure 14: Search-verify subagents extremely slow (40+ minutes each)
- **What happened:** Marketing Manager took 40m23s, Founder's Associate took 41m14s.
- **Root cause:** Subagents perform excessive research per job (company context, multiple web fetches).
- **Category:** performance
- **Prevention:** Automated: No — requires subagent prompt tuning
- **Principle violated:** Brief generation <60s target (MEMORY.md)
- **Fix type:** Implementation

### Failure 15: Robinhood job appeared twice in Marketing Manager results
- **What happened:** Same Robinhood "Product Marketing Manager, Crypto - International" appeared with scores 84 and 80, same URL.
- **Root cause:** Within-role dedup not catching same-URL duplicates.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — data-integrity-guardian reviewer prompt
- **Principle violated:** No duplicate jobs in presentation
- **Fix type:** Implementation

### Failure 16: Crush job appeared in both Community Manager and Marketing Associate
- **What happened:** "Content & Community Manager" appeared in two role type categories with score 82.
- **Root cause:** Cross-role dedup logged "No duplicates — 27 in, 27 out" but missed this match.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — data-integrity-guardian reviewer prompt
- **Principle violated:** Cross-role dedup must catch same company+title across categories
- **Fix type:** Implementation

### Failure 17: Mercuryo job appeared in both Marketing Manager and Marketing Associate
- **What happened:** "B2C Product Marketing Manager" appeared in two role categories (scores 75 and 78).
- **Root cause:** Same cross-role dedup failure as Failure 16.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — same fix as Failure 16
- **Principle violated:** Cross-role dedup must normalize company+title matching
- **Fix type:** Implementation

## Fixes Needed

### Architectural Fixes

**Fix A1: Selective pre-run cleanup**
- **What needs to change:** Replace blind `find output/verified -type f -delete` with a selective cleanup that reads state.json first and only deletes files for jobs NOT tracked as active. Still-active jobs retain their verified JSON files across runs.
- **Files affected:** `03_agents/tests/v20/CLAUDE.md` (cleanup step), `03_agents/tests/v20/scripts/manage_state.py` (add `cleanup` subcommand)
- **Verification criteria:** After pre-run cleanup, `ls output/verified/*/` count >= number of active jobs in state.json. Dashboard API returns all active jobs.

**Fix A2: CLAUDE.md decomposition**
- **What needs to change:** Extract presentation rules, onboarding flow, session management, and workflow steps into `references/` files. CLAUDE.md becomes a compact orchestrator (~200-250 lines) that loads references on-demand via subagents.
- **Files affected:** `03_agents/tests/v20/CLAUDE.md`, new `03_agents/tests/v20/references/` files (presentation.md, onboarding.md, workflow.md, etc.)
- **Verification criteria:** CLAUDE.md <= 300 lines. All extracted content accessible via subagent dispatch. Agent behavior unchanged.

**Fix A3: Dedup soft-delete or preserve-one-copy**
- **What needs to change:** Cross-role dedup should not hard-delete verified JSON files. Either: (a) move duplicates to an archive directory, or (b) keep the highest-scoring copy on disk and only remove the lower-scoring copies, or (c) update dedup to operate on state.json metadata only without touching disk files.
- **Files affected:** `03_agents/tests/v20/scripts/manage_state.py` (dedup subcommand), `03_agents/tests/v20/CLAUDE.md` (dedup step description)
- **Verification criteria:** After dedup, every unique job in state.json has at least one verified JSON file on disk. Dashboard API can serve all jobs.

### Implementation Fixes

**Fix I1: Make dashboard URL mandatory everywhere**
- **What needs to change:** Remove all "omit silently" / null fallbacks for dashboard URL. Add validation in context.md reader that fails loudly if dashboard_url is empty. Update CLAUDE.md, digest-email skill, and agent definitions to require non-null dashboard_url.
- **Files affected:** `03_agents/tests/v20/CLAUDE.md`, `.claude/skills/digest-email.md` or equivalent, `.claude/agents/digest-email.md` or equivalent
- **Verification criteria:** Dispatching digest-email with empty dashboard_url produces an explicit error, not silent omission.

**Fix I2: Fix GitHub Actions heredoc indentation**
- **What needs to change:** Correct the YAML heredoc in daily-digest.yml so the expanded JSON for settings.local.json is valid. Add a validation step after file creation: `python3 -c "import json; json.load(open('.claude/settings.local.json'))"`.
- **Files affected:** `.github/workflows/daily-digest.yml`
- **Verification criteria:** `act` or manual workflow dispatch produces valid settings.local.json. Scheduled run gets past preflight.

**Fix I3: Add missing permissions to settings.local.json**
- **What needs to change:** Add Read, Write, Glob, Grep to the permissions allowlist in settings.local.json so background subagents have full tool access.
- **Files affected:** `03_agents/tests/v20/.claude/settings.local.json` (template), `.github/workflows/daily-digest.yml` (CI generation)
- **Verification criteria:** Background subagent dispatch succeeds without tool denials.

**Fix I4: Add post-compaction hard constraint**
- **What needs to change:** Add to CLAUDE.md: "After context compaction, if subagent outputs are needed, re-dispatch subagents. NEVER reconstruct findings from conversation summary."
- **Files affected:** `03_agents/tests/v20/CLAUDE.md`
- **Verification criteria:** Constraint listed in hard constraints section.

**Fix I5: Enforce score threshold in presentation**
- **What needs to change:** Add explicit filter step before presentation: any job with score < 70 is excluded from the unified view. Log filtered-out jobs to session-state.md.
- **Files affected:** `03_agents/tests/v20/CLAUDE.md` (presentation step)
- **Verification criteria:** No job below 70 appears in user-facing presentation.

**Fix I6: Standardize table format for all role types**
- **What needs to change:** Enforce that all role types use identical table format in presentation. Add explicit format template to CLAUDE.md presentation rules.
- **Files affected:** `03_agents/tests/v20/CLAUDE.md` (presentation step)
- **Verification criteria:** All role types render with same table columns and format.

**Fix I7: Fix cross-role dedup normalization**
- **What needs to change:** Dedup must normalize on `(company.lower().strip(), title.lower().strip())` from JSON content, not filename slugs. Same company+title across different role type directories must be detected as duplicates.
- **Files affected:** `03_agents/tests/v20/scripts/manage_state.py` (dedup subcommand)
- **Verification criteria:** Crush and Mercuryo duplicates would be caught in a re-run. Add test cases for cross-role duplicates.

**Fix I8: Enforce incremental commit after each batch**
- **What needs to change:** Strengthen enforcement of HC7. Add explicit step in workflow: after session-state.md write, immediately `git add output/ state.json && git commit && git push`. Add a verification check that confirms commit count matches batch count.
- **Files affected:** `03_agents/tests/v20/CLAUDE.md` (batch workflow)
- **Verification criteria:** `git log --oneline` shows one commit per completed batch, not just one at session end.

**Fix I9: Read before Write on session-state.md**
- **What needs to change:** First Write to session-state.md must be preceded by a Read (tool constraint). Add this to the workflow step explicitly.
- **Files affected:** `03_agents/tests/v20/CLAUDE.md` (session-state step)
- **Verification criteria:** First Write to session-state.md succeeds without error.

**Fix I10: Subagent speed optimization**
- **What needs to change:** Trim search-verify subagent scope — skip hiring manager research, Crunchbase lookups, and funding round research. Limit company context to what's already in the verified JSON. Target <120s per subagent.
- **Files affected:** `.claude/agents/search-verify-*.md` or equivalent agent definitions
- **Verification criteria:** Search-verify subagents complete in <2 minutes each.

## Solutions Extracted

### Solution 1: Foreground-Fallback Guard
- **Problem:** Background subagents had all tools denied.
- **Solution:** On first dispatch, observe if tools are denied. If denied, set `dispatch_mode = "foreground"` and re-dispatch all subsequent subagents in foreground mode. Create required output directories before dispatch.
- **Category:** subagent-coordination
- **Transferable:** Yes

### Solution 2: Selective Cleanup Diagnosis
- **Problem:** Pre-run cleanup destroyed dashboard data.
- **Solution:** Investigation correctly diagnosed the compounding issue: aggressive cleanup + subagents only recreating today's files = data gap. Recommended fix: read state.json before cleanup, preserve still-active files.
- **Category:** data-integrity
- **Transferable:** Yes

### Solution 3: Mandatory Variable Propagation
- **Problem:** Dashboard URL missing from digest email.
- **Solution:** User provided URL → agent wrote to context.md → recorded in memory → re-dispatched digest with URL. Investigation identified all 3 code locations needing fix.
- **Category:** configuration
- **Transferable:** Yes

### Solution 4: Post-Compaction Re-Dispatch
- **Problem:** Context compaction destroyed subagent outputs, parent fabricated findings.
- **Solution:** User caught fabrication → parent acknowledged data loss → re-dispatched all 7 investigation subagents from scratch → presented verified findings.
- **Category:** subagent-coordination
- **Transferable:** Yes

### Solution 5: Idempotent Email Gate
- **Problem:** Risk of duplicate digest emails on resume/re-run.
- **Solution:** Before sending, check `_status.json` for `sent_at` + `run_date` match. After send, update status immediately. Gate passed cleanly.
- **Category:** email-delivery
- **Transferable:** Yes

### Solution 6: Heredoc Root Cause Tracing
- **Problem:** Scheduled runs failing 4/4 since Feb 13.
- **Solution:** Subagent traced to YAML heredoc whitespace producing invalid JSON in settings.local.json creation step. FileNotFoundError was a symptom, not the cause.
- **Category:** deployment
- **Transferable:** Yes

## Patterns Identified

### Pattern 1: Background-to-Foreground Dispatch Fallback
- **Steps:** Dispatch background → detect tool denial → set foreground mode → mkdir -p output dirs → re-dispatch foreground → verify output
- **Appeared in:** Batch 1 search-verify agents
- **Skill candidate:** Yes
- **Generalization:** Any multi-subagent orchestrator with unreliable background permissions

### Pattern 2: Batched Subagent Dispatch with Incremental Checkpointing
- **Steps:** Dispatch batch → wait → read _status.json → update session-state.md → git commit+push → verify commit → next batch
- **Appeared in:** Steps 10-11b (search batches)
- **Skill candidate:** Yes
- **Generalization:** Any agent processing work in batches needing incremental persistence

### Pattern 3: Subagent Output Verification and Recovery
- **Steps:** Subagent completes → read _status.json → read _summary.md → if missing: dispatch recovery subagent → re-read
- **Appeared in:** Steps 11-12, recovery protocol
- **Skill candidate:** Yes
- **Generalization:** Any orchestrator using status-file protocols

### Pattern 4: Context Compaction Hallucination Recovery (ANTI-PATTERN)
- **Steps:** Compaction occurs → parent fabricates from summary → user catches → parent re-dispatches all subagents
- **Appeared in:** Investigation phase post-compaction
- **Skill candidate:** No — prevent this, don't codify it
- **Generalization:** Add hard constraint: never reconstruct from compacted summaries

### Pattern 5: Mandatory Variable Propagation Chain
- **Steps:** Capture variable → store in persistent config → pass to subagent dispatch → verify in output → verify in presentation → halt if missing
- **Appeared in:** Steps 5, 16b, 19 (dashboard URL)
- **Skill candidate:** Yes
- **Generalization:** Any agent with mandatory config flowing through multiple subagents

### Pattern 6: Dedup-Sync-Delta Pipeline
- **Steps:** All batches complete → dedup via CLI → state sync → read delta.json → read summaries → classify new/still-active
- **Appeared in:** Steps 13-16
- **Skill candidate:** Yes
- **Generalization:** Any agent searching multiple sources and tracking entities across runs

## Build Metrics
- **Build duration (total):** Unavailable (phased-build step timing not yet enabled)
- **Steps completed:** 15 / 15
- **Verification pass rate:** 15 / 15 (100%)
- **Regression count (new):** 0 during build
- **Regression count (repeat):** 0 during build
- **Review cycle count:** 2 (round 1 + round 2)
- **Runtime failures found in session:** 17

## Handoff Contract
- Architectural fixes: 3 — selective pre-run cleanup, CLAUDE.md decomposition, dedup soft-delete
- Implementation fixes: 10 — mandatory dashboard URL, fix GH Actions heredoc, add missing permissions, post-compaction constraint, score threshold enforcement, table format standardization, cross-role dedup normalization, incremental commit enforcement, Read-before-Write on session-state, subagent speed optimization
- New constraints: post-compaction re-dispatch (never reconstruct from summary), dashboard URL mandatory (fail loudly), Read-before-Write on existing files
- Regression tests to include: pre-run cleanup preserves active jobs, dedup preserves dashboard data, cross-role dedup catches same company+title, score <70 filtered from presentation, all role types use table format, incremental commit per batch
- Prevention artifacts written: 0 checks.sh entries (deferred to V2), 4 reviewer prompt additions
- Metrics recorded: V20 build metrics (15/15 steps, 100% pass, timing unavailable)

<!-- STAGE COMPLETE: /analyze, 2026-02-18 -->

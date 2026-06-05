# Session Analysis: Job Search Agent V19

## Summary

7 wins, 13 failures (3 critical, 6 major, 4 minor), 3 edge cases. V19 build was clean (14/14 steps, 101 tests pass), but the runtime session revealed that several V18 regressions recurred and new failures emerged around subagent directory resolution and workflow configuration. Post-build, 4 consecutive scheduled runs failed (Feb 13, 16, 17, 18) — 3 on missing `settings.local.json` in CI, 1 on 30-minute timeout — prompting a fundamental review of the scheduling approach.

## What Went Well

1. **Resume detection worked correctly** — Agent detected same-day `last_run_date` and handled the re-run scenario (lines 32-33)
2. **Batch orchestration succeeded** — All 4 role types searched in 2 batches of 2 with proper checkpointing between batches
3. **Dedup CLI used correctly** — Parent delegated to `manage_state.py dedup` subcommand (not inline Python)
4. **Email idempotency gate** — Checked `_status.json` for `sent_at` before sending, preventing duplicate sends
5. **Session-state checkpointing** — Written after each search batch (V14/V16/V18 fix confirmed working)
6. **Clean results presentation** — 27 unique jobs across 4 role types with reference footnote URLs, unified selection view, and 70+ threshold enforced
7. **File-based recovery from directory mismatch** — While a bug, the parent's detect-copy-verify pattern recovered gracefully every time

## What Failed

### Failure 1: Subagents wrote to v18 directory instead of v19
- **What happened:** All subagent types (search-verify, brief-generator, digest-email, briefs-html) wrote output to `03_agents/tests/v18/output/` instead of `03_agents/tests/v19/output/`. Parent had to manually copy files after every batch.
- **Root cause:** Agent definitions or dispatch prompts resolve working directory to v18. No explicit absolute path variable passed in dispatch.
- **Category:** subagent-coordination
- **Prevention:** Automated: Yes — post-dispatch file existence check on expected directory
- **Principle violated:** Subagent output must land in the active version directory
- **Fix type:** Implementation

### Failure 2: GitHub Actions workflow points to v18
- **What happened:** `.github/workflows/daily-digest.yml` references `03_agents/tests/v18`, so scheduled runs execute the old agent.
- **Root cause:** V19 build copied v18 files but never updated the workflow path reference.
- **Category:** configuration
- **Prevention:** Automated: Yes — `grep -r 'tests/v18' .github/workflows/`
- **Principle violated:** Deployment config must reference the active version
- **Fix type:** Implementation

### Failure 3: Cross-role dedup missed duplicates
- **What happened:** Dedup script reported "no duplicates removed" despite Crypto.com, Crush, Tether, 1inch DAO appearing across multiple role types. Delta JSON showed ~49 "new" when only ~27 were unique.
- **Root cause:** Dedup matches on filename slug, but same company+title produces different slugs under different role types. No content-based normalization.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — content-based dedup comparing `(company.lower(), title.lower())` from JSON
- **Principle violated:** Dedup must use normalized title+company (V18 regression recurrence)
- **Fix type:** Implementation

### Failure 4: Missing dashboard URL
- **What happened:** No dashboard URL shown to user after unified selection view. User had to explicitly ask where to view jobs online.
- **Root cause:** Dashboard URL not stored in `context.md ## Delivery` and not referenced in presentation workflow.
- **Category:** configuration
- **Prevention:** Automated: Partial — deployment-verifier reviewer prompt added
- **Principle violated:** V18 regression — dashboard URL must be proactively shown
- **Fix type:** Implementation

### Failure 5: Incremental commit+push skipped
- **What happened:** Step 11b requires commit after each batch for Vercel redeployment. Only committed once at session end, after user prompted twice.
- **Root cause:** Constraint not elevated to hard constraint (HC) status. Agent deferred it.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — regression-checker reviewer prompt added
- **Principle violated:** V14/V16/V18 regression recurrence — incremental commit after each batch
- **Fix type:** Implementation

### Failure 6: Parent ran scripts directly (context budget violation)
- **What happened:** Parent executed `python3 scripts/manage_state.py` directly for dedup, sync, and record-action (4 instances).
- **Root cause:** Context budget rule "python3 scripts/* only via subagent" not internalized. Rules added in V19 build but not enforced at runtime.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — regression-checker reviewer prompt added
- **Principle violated:** Context budget — parent must never run scripts directly
- **Fix type:** Implementation

### Failure 7: Permissions blocking autonomous operation
- **What happened:** Subagent Bash commands required manual user permission approval throughout session, making scheduled runs impossible.
- **Root cause:** No `.claude/settings.local.json` Bash allowlist configured for known subagent commands.
- **Category:** configuration
- **Prevention:** Automated: No — requires platform-level configuration
- **Principle violated:** Agent must be capable of autonomous scheduled execution
- **Fix type:** Implementation

### Failure 8: HC1 violated — model passed to Task tool
- **What happened:** Parent dispatched a Haiku 4.5 subagent for URL extraction with explicit `model:` parameter.
- **Root cause:** HC1 ("Never pass model: to Task tool") violated. Agent optimized for cost but broke a hard constraint.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — regression-checker reviewer prompt added
- **Principle violated:** HC1 — never pass model parameter to Task tool
- **Fix type:** Implementation

### Failure 9: Missing _summary.md from CM subagent
- **What happened:** Community Manager subagent did not write `_summary.md`. Parent worked around it using the subagent's return message.
- **Root cause:** Agent definition doesn't enforce summary file writing. Recovery protocol (dispatch recovery subagent) wasn't followed.
- **Category:** subagent-coordination
- **Prevention:** Automated: Yes — post-dispatch status file validation
- **Principle violated:** Recovery protocol — dispatch recovery subagent, don't workaround in parent
- **Fix type:** Implementation

### Failure 10: Zsh glob error on cleanup
- **What happened:** `rm -f output/jobs/*` failed with "no matches found" in zsh. Required `find -delete` fallback.
- **Root cause:** CLAUDE.md uses glob patterns that fail in zsh on empty directories.
- **Category:** configuration
- **Prevention:** Automated: Yes — `grep 'rm -f.*\*' CLAUDE.md`
- **Principle violated:** Shell-portable cleanup commands required
- **Fix type:** Implementation

### Failure 11: Inconsistent presentation format
- **What happened:** Community Manager and Marketing Associate used table format; Marketing Manager and Founder's Associate used non-table line format.
- **Root cause:** Presentation template in CLAUDE.md doesn't strictly enforce table format for all role types.
- **Category:** design-system
- **Prevention:** Automated: No — requires human judgment on presentation format
- **Principle violated:** Consistent visual presentation across role types
- **Fix type:** Implementation

### Failure 12: Agent memory not read on startup
- **What happened:** "Agent memory: read 0 MEMORY.md files" — despite HC4 requiring startup memory read.
- **Root cause:** MEMORY.md files may not exist at expected path, or Glob pattern didn't match.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — startup assertion checking file count > 0
- **Principle violated:** HC4 — read agent memory on startup (V14/V17 regression recurrence)
- **Fix type:** Implementation

### Failure 13: 4 consecutive scheduled run failures (Feb 13–18)
- **What happened:** GitHub Actions scheduled runs failed 4 times in a row. Feb 13, 16, 17: `FileNotFoundError: .claude/settings.local.json` — the file is gitignored and does not exist in CI. Feb 18: 30-minute timeout hit — Claude ran for 30 minutes but was cancelled by the job timeout before completing. The root workflow still references `v18` (Failure 2), but even with the correct path, the settings.local.json issue would have blocked execution.
- **Root cause:** Two compounding issues: (1) The workflow's "Verify settings.local.json" step expects a file that is gitignored and never exists in CI — it should CREATE the file, not verify it. (2) The 30-minute timeout is too aggressive for a full agent run that can take 20-45 minutes. (3) The workflow does not use `--dangerously-skip-permissions` or `--allowedTools`, so even if settings.local.json existed, permission prompts would block non-interactive execution.
- **Category:** deployment
- **Prevention:** Automated: Yes — workflow must generate CI config files and use `--dangerously-skip-permissions` for headless mode
- **Principle violated:** Scheduled runs must work without human intervention; CI config must be self-contained
- **Fix type:** Architectural — this is not a simple implementation fix; it requires evaluating whether GitHub Actions is the right scheduling platform for this agent
- **Severity:** Critical — the agent has a 0% scheduled run success rate

## Fixes Needed

### Architectural Fixes

1. **Redesign scheduling infrastructure**
   - What needs to change: Evaluate and select a scheduling approach that achieves >95% reliability. The current GitHub Actions approach has a 0% success rate across 4 runs. Options identified by research (ranked by recommendation):
     - **Option A: Fix GitHub Actions** — Generate settings.local.json in CI, use `--dangerously-skip-permissions`, increase timeout to 90min, add preflight checks and retry logic. Lowest effort, addresses root causes directly.
     - **Option B: Claude Agent SDK on local Mac** — Use `launchd` + `pmset` + `caffeinate` to schedule a Python script using the Claude Agent SDK. Eliminates CI environment setup entirely. ~95% reliable on laptop, ~99% with dedicated Mac Mini.
     - **Option C: Claude Agent SDK on cloud VPS** — Deploy to Railway ($5/mo), Hetzner ($3.50/mo), or Google Cloud Run Jobs ($0-1.50/mo). Persistent state, no timeout issues, enterprise-grade reliability.
     - **Option D: Direct Anthropic API** — Replace Claude Code CLI entirely with raw `anthropic` Python SDK + custom tool_use loop. Maximum control and portability but highest rewrite effort.
   - Files affected: `.github/workflows/daily-digest.yml` (all options), potentially new `run_agent.py` (Options B-D), new `Dockerfile` (Option C), LaunchAgent plist (Option B)
   - Verification criteria: 5 consecutive successful scheduled runs

### Implementation Fixes

1. **Add explicit working directory variable to subagent dispatch**
   - What needs to change: Add `working_dir` (absolute path) to the variable blob passed to all subagent dispatch templates. Each agent definition must use this path for all file operations.
   - Files affected: CLAUDE.md (dispatch templates), `.claude/agents/*.md` (agent definitions)
   - Verification criteria: Subagent output files land in `03_agents/tests/v19/output/` without manual copy

2. **Update GitHub Actions workflow path**
   - What needs to change: Replace all `tests/v18` references with `tests/v19` in `.github/workflows/daily-digest.yml`
   - Files affected: `.github/workflows/daily-digest.yml`
   - Verification criteria: `grep -r 'tests/v18' .github/workflows/` returns empty

3. **Fix cross-role dedup to normalize on content**
   - What needs to change: `manage_state.py dedup` must compare `(company.lower().strip(), title.lower().strip())` from JSON content, not filename slugs
   - Files affected: `scripts/manage_state.py`
   - Verification criteria: Same company+title under different role types is correctly flagged as duplicate

4. **Add dashboard URL to context.md and enforce post-selection display**
   - What needs to change: Store `dashboard_url` in `context.md ## Delivery`. Add explicit step in presentation workflow to show it after selection view.
   - Files affected: `context.md`, CLAUDE.md (presentation workflow section)
   - Verification criteria: Dashboard URL displayed to user after unified selection view

5. **Elevate incremental commit+push to hard constraint**
   - What needs to change: Add HC for "commit+push after each search batch" with explicit checkpoint language
   - Files affected: CLAUDE.md (hard constraints section)
   - Verification criteria: HC list includes incremental commit rule

6. **Strengthen context budget: parent must never run scripts**
   - What needs to change: Add explicit HC: "Never execute `python3 scripts/*` in parent context — always dispatch to subagent"
   - Files affected: CLAUDE.md (hard constraints and context budget sections)
   - Verification criteria: HC list includes script execution prohibition

7. **Configure .claude/settings.local.json Bash allowlist**
   - What needs to change: Create/update settings file with allowlist for `python3`, `git`, `find`, `mkdir`, `cp`, `cat` commands used by subagents
   - Files affected: `.claude/settings.local.json` (gitignored), CLAUDE.md (document allowlist)
   - Verification criteria: Subagent Bash commands execute without permission prompts

8. **Reinforce HC1 — no model parameter in Task dispatch**
   - What needs to change: Add explicit reminder in dispatch template section: "Do not set model: parameter"
   - Files affected: CLAUDE.md (dispatch templates section)
   - Verification criteria: No `model:` parameter in any dispatch template

9. **Add _summary.md to agent completion requirements + recovery protocol**
   - What needs to change: Agent definitions must list `_summary.md` as required output. Recovery protocol must be followed on missing summary.
   - Files affected: `.claude/agents/*.md`, CLAUDE.md (recovery protocol section)
   - Verification criteria: All subagents write `_summary.md`; missing files trigger recovery dispatch

10. **Replace glob-based cleanup with find-based cleanup**
    - What needs to change: Replace `rm -f output/jobs/*` with `find output/jobs -type f -delete 2>/dev/null` throughout CLAUDE.md
    - Files affected: CLAUDE.md (cleanup section)
    - Verification criteria: `grep 'rm -f.*\*' CLAUDE.md` returns empty

11. **Enforce consistent table format in presentation**
    - What needs to change: Presentation template must require table format for ALL role types, not just some
    - Files affected: CLAUDE.md (presentation template section)
    - Verification criteria: All 4 role types render as tables with identical column structure

12. **Fix agent memory startup read (HC4)**
    - What needs to change: Startup sequence must Glob for `**/.claude/agent-memory/*/MEMORY.md` relative to agent directory and assert count > 0 (or log warning if dir doesn't exist)
    - Files affected: CLAUDE.md (startup sequence)
    - Verification criteria: "Agent memory: read N MEMORY.md files" where N > 0 (or graceful warning if no memory dir exists)

## Solutions Extracted

1. **Zsh-safe cleanup with find** — Use `find dir -type f -delete 2>/dev/null` instead of `rm -f dir/*` for portable cleanup on empty directories. Category: configuration. Transferable: Yes.

2. **Post-dispatch directory verification** — After subagent completion, verify output landed in expected directory; if empty, check fallback directories and copy. Category: subagent-coordination. Transferable: Yes.

3. **Presentation-layer dedup as safety net** — When data-layer dedup has limitations, deduplicate at presentation time by keeping highest-scoring instance per company+title. Category: data-integrity. Transferable: Yes.

4. **Subagent return message as fallback data source** — When expected file artifact is missing, use the subagent's Task tool return message as data source (separate completion signal from data artifact). Category: subagent-coordination. Transferable: Yes.

5. **File-based email idempotency gate** — Check `_status.json` for `sent_at` before sending; update immediately after. Category: email-delivery. Transferable: Yes.

6. **Lightweight model subagent for data extraction** — Dispatch a fast subagent for pure data extraction tasks (URL extraction from JSONs); fall back to shell command if output truncated. Category: subagent-coordination. Transferable: Yes.

7. **Incremental session-state checkpointing** — Write `session-state.md` after each batch (not just at end) with batch number, role types, and cumulative counts for resume capability. Category: data-integrity. Transferable: Yes.

## Patterns Identified

1. **Batch-Dispatch-Checkpoint (BDC) Pattern** — Prepare variables → dispatch parallel subagents → read status files → checkpoint to session-state → repeat. Appeared in search batches. Skill candidate: Yes.

2. **Wrong-Directory Recovery Pattern** — List expected dir (empty) → list fallback dir (has files) → mkdir -p → copy → verify status. Appeared 4 times. Skill candidate: Yes (as post-dispatch verification step).

3. **Verify-Then-Present Pipeline** — Dedup → sync → read delta → read summaries → extract URLs → manual dedup → per-role tables → unified ranked list → user selection. Appeared in Steps 13-17. Skill candidate: No (too domain-specific).

4. **Parallel-Generate-Then-Deliver Pattern** — Record selections → dispatch content generators → verify outputs → dispatch formatters → pre-send gate → send → update status → commit. Appeared in Steps 17-20. Skill candidate: Yes.

5. **Startup-Resume-or-Clean Pattern** — Capture date → read memory → git pull → load state → compare dates → resume or clean → read profile → quick-change check. Appeared in Steps 1-8. Skill candidate: Yes.

## Build Metrics

- Build duration (total): unavailable (timing not yet enabled)
- Steps completed: 14 / 14
- Verification pass rate: 14 / 14 (100%)
- Regression count (new): 0
- Regression count (repeat): 0
- Review cycle count: unavailable
- Session failures: 12 (2 critical, 6 major, 4 minor)
- Regression recurrences in session: 4 (dedup V18, dashboard URL V18, incremental commit V14/V16/V18, agent memory V14/V17)

## Scheduling Alternatives Research

Research dispatched across 5 parallel subagents to evaluate whether the GitHub Actions approach should be fixed or replaced.

### Current State: 0% Success Rate

| Date | Run ID | Result | Root Cause |
|------|--------|--------|------------|
| Feb 13 | 21977786629 | failure | `FileNotFoundError: .claude/settings.local.json` |
| Feb 16 | 22053232141 | failure | `FileNotFoundError: .claude/settings.local.json` |
| Feb 17 | 22088967366 | failure | `FileNotFoundError: .claude/settings.local.json` |
| Feb 18 | 22129974670 | cancelled | 30-minute timeout exceeded |

### Option A: Fix GitHub Actions (Recommended — Lowest Effort)

The failures are all preventable configuration errors, not platform limitations:
- **settings.local.json**: Use `--dangerously-skip-permissions` flag (safe in CI's isolated container). Eliminates the settings file entirely.
- **30-minute timeout**: Increase to 90 minutes (GitHub allows up to 360 min).
- **v18 path**: Use env var `JSA_DIR` at top of workflow for single-point version management.
- **No preflight checks**: Add secret validation and file existence checks before the expensive Claude API call.
- **No retry**: Add `nick-fields/retry@v3` with `max_attempts: 2` for transient failures.
- **No caching**: Add pip cache, Playwright browser cache to cut ~90s from setup.
- **Estimated effort**: 1-2 hours to update the workflow YAML.

### Option B: Claude Agent SDK + Local Mac (launchd)

Replace the CI approach with a local Python script using the Claude Agent SDK:
- `pmset repeat wakeorpoweron MTWRF 06:55:00` — wakes Mac 5min before run
- LaunchAgent plist triggers `run_agent.py` at 7:00 AM
- `caffeinate -is` prevents sleep during execution
- Claude Agent SDK (`pip install claude-agent-sdk`) provides all built-in tools (Read, Write, Bash, WebSearch, etc.) with programmatic permission control
- No settings.local.json needed — `ClaudeAgentOptions(permission_mode="bypassPermissions")`
- Cost control via `max_budget_usd=5.00` and `max_turns=100`
- **Reliability**: ~95% on laptop (fails if powered off), ~99% on dedicated Mac Mini ($150-250 one-time)
- **Estimated effort**: 2-4 hours (write run_agent.py + configure launchd + pmset)

### Option C: Cloud VPS/PaaS

| Platform | Monthly Cost | Timeout | Persistent State | Reliability |
|----------|-------------|---------|-----------------|-------------|
| Google Cloud Run Jobs | $0-1.50 (free tier) | 168 hours | Cloud Storage mount | 5/5 |
| Railway.app | $5 (plan min) | Unlimited | Persistent volumes | 4/5 |
| Hetzner VPS | $3.50 | Unlimited | NVMe SSD | 4/5 |
| DigitalOcean | $4-6 | Unlimited | SSD | 4/5 |
| AWS EC2 t3.micro | $7.59 | Unlimited | EBS | 4/5 |

Best cloud option: **Google Cloud Run Jobs** (free tier covers this workload) or **Hetzner** (simplest mental model — it's just a Linux box with crontab).
- **Estimated effort**: 4-8 hours (Dockerfile, deploy, configure scheduling)

### Option D: Direct Anthropic API (No Claude Code CLI)

Replace Claude Code entirely with raw `anthropic` Python SDK + `tool_use`:
- Define 5-8 custom tools (@beta_tool): search_jobs, read_file, write_file, run_shell, send_email
- SDK `tool_runner` handles the agentic loop and token management (auto-compaction)
- Maximum portability — pure Python, runs anywhere
- **Tradeoff**: Must reimplement all tool execution (file I/O, shell, web fetch). Lose Claude Code's built-in Glob, Grep, Edit tools.
- **Estimated effort**: 2-3 days (rewrite agent orchestration)

### Recommendation for /design Phase

**Start with Option A** (fix GitHub Actions). The root causes are known and trivial to fix. If GitHub Actions proves unreliable after the fix (e.g., cron scheduling delays, environment flakiness), **fall back to Option B** (Claude Agent SDK + local Mac) which requires moderate effort and provides the highest day-to-day reliability for a personal agent.

Option C (cloud) and Option D (direct API) are valid but introduce new infrastructure that is premature given the simple root causes of current failures.

## Handoff Contract

- Architectural fixes: 1 — redesign scheduling infrastructure (evaluate Option A fix vs Option B/C/D alternatives)
- Implementation fixes: 12 — working directory variable in dispatch, workflow path update, content-based dedup, dashboard URL enforcement, incremental commit HC, script execution HC, settings allowlist, HC1 reinforcement, summary file requirement, find-based cleanup, table format enforcement, agent memory startup fix
- New constraints: HC for incremental commit+push, HC for no script execution in parent, HC1 reinforcement in dispatch templates
- Regression tests to include: working directory assertion, workflow path assertion, content-based dedup test, dashboard URL presence test, scheduled run success assertion (5 consecutive runs)
- Prevention artifacts written: 4 regression-checker reviewer prompt additions, 4 deployment-verifier reviewer prompt additions
- Metrics recorded: V19 — 14/14 steps, 100% verification, 13 session failures (3C/6M/4m), 4 regression recurrences, 4 consecutive scheduled run failures
- Scheduling research complete: 4 options evaluated (fix GH Actions, Agent SDK + local Mac, cloud VPS, direct API)

<!-- STAGE COMPLETE: /analyze (updated), 2026-02-18 -->

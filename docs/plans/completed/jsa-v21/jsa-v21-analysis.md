# Session Analysis: JSA V21

## Summary
6 wins, 14 failures (4 critical, 4 major, 6 minor), 8 constraint violations, 3 edge cases. Build was clean (22/22 steps, 101 tests). The session test revealed preflight validation drift, permissions gaps, and deployment automation gaps that the build itself could not surface.

## What Went Well
1. **Parallel subagent dispatch effective**: Triple-dispatch (JobSpy + archive + Substack) and dual-dispatch (fit analysis + verification) ran concurrently, maximizing throughput
2. **Search strategy self-correction**: After JobSpy returned generic results, parent correctly diagnosed the issue and re-dispatched with specialty-source-only instructions, yielding Anthropic/Cohere/ElevenLabs roles
3. **Context discipline maintained**: Parent never ran WebFetch/WebSearch directly; all web research delegated to subagents; after rate limit, dispatched new subagent rather than doing work in parent
4. **Honest strategic analysis**: Ranking table (HIGH/MODERATE/LOW), "Python wall" insight, and MSc assessment provided genuine value beyond job listing
5. **End-to-end delivery completed**: Full pipeline — search, verify, brief, HTML compile, digest email, git commit+push, Vercel deploy, dashboard verified via API
6. **Rate limit recovery clean**: After hitting rate limit at 12:26, session resumed at 14:20, checked partial output, and continued from where subagent left off

## What Failed

### Failure 1: Rate limit during search subagent
- **What happened:** First search-verify subagent consumed 24 tool uses over 16 minutes before hitting API rate ceiling. Produced aggregator + filtered files but zero verified JSONs.
- **Root cause:** Single long-running subagent with no token/time budget control. The search-verify agent's scope is unbounded — it searches, filters, AND verifies in one pass.
- **Category:** performance
- **Prevention:** Automated: No — rate limits are external and timing-dependent. Regression checklist only.
- **Principle violated:** No explicit constraint, but V19 regression notes search-verify should complete in <2 min
- **Fix type:** Architectural

### Failure 2: Permissions still prompting despite V21 settings
- **What happened:** User complained "still having to accept permissions regularly." The `settings.local.json` only had limited entries at session start; the V21 build added comprehensive permissions but the session ran before the build was tested.
- **Root cause:** `settings.local.json` created during V21 build was never tested in a live session before the user ran the agent. Only 1 Bash entry existed at session start.
- **Category:** configuration
- **Prevention:** Automated: Yes — preflight can validate that settings.local.json contains minimum required permission entries.
- **Principle violated:** V19 regression — Bash permissions must be pre-configured for autonomous runs
- **Fix type:** Implementation

### Failure 3: Vercel dashboard stale (showing v18 data)
- **What happened:** Dashboard showed `run_date: 2026-02-17` with v18 data. Vercel was still linked to v18 directory, not v21.
- **Root cause:** No automated re-link+deploy on version transition. Memory note exists but was not enforced programmatically.
- **Category:** deployment
- **Prevention:** Automated: Yes — post-push check can verify dashboard `run_date` matches today.
- **Principle violated:** Memory note: "After every commit+push that updates output/verified/, redeploy the dashboard"
- **Fix type:** Implementation

### Failure 4: GitHub Actions scheduled run broken (v20 hardcoded, Claude timeout)
- **What happened:** Repo-root `daily-digest.yml` hardcoded to v20. Claude with `--print` consistently times out at 80+ min. Cancelled at 90-min job timeout.
- **Root cause:** Architectural mismatch — `claude --print` within GH Actions is not viable for full agent runs. Also, workflow path not updated on version transition.
- **Category:** deployment
- **Prevention:** Automated: No — requires architectural decision about whether to use Claude CLI, Python orchestrator, or simpler pipeline for scheduled runs.
- **Principle violated:** V19 regression — GH Actions workflow must reference current version directory
- **Fix type:** Architectural

### Failure 5: Preflight wrong CLI flags for manage_state.py dedup
- **What happened:** preflight.sh tested `--verified-dir --archive-dir` but actual dedup subcommand only accepts `--output-dir --dry-run`. Three consecutive preflight failures at startup.
- **Root cause:** Preflight checks written against assumed flag names during V21 build, never validated against actual `--help` output.
- **Category:** testing
- **Prevention:** Automated: Yes — preflight self-validation can run `--help` and check that tested flags exist.
- **Principle violated:** No explicit constraint, but the preflight harness was built in V21 to prevent exactly this class of error
- **Fix type:** Implementation

### Failure 6: JobSpy generic results ("AI marketing community manager")
- **What happened:** First search used composite query "AI marketing community manager" which returned JPMorgan, eBay, Revere Agency — no AI agent startups.
- **Root cause:** Composite query dilutes domain specificity in aggregator searches. No query strategy in search-verify agent for domain-specific roles.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — reviewer can flag generic composite queries. Relevant reviewer: data-integrity-guardian.
- **Principle violated:** CR1 context — search should match user's intent for AI agent companies
- **Fix type:** Implementation

### Failure 7: Archived verified JSONs broke downstream consumers
- **What happened:** Preflight cleanup archived 27 verified JSONs. MAGIC AI and Linda AI (scored 95 each) were archived but still tracked in state.json as active. Brief generation and dashboard both broke.
- **Root cause:** Cleanup uses blind archive-all without cross-referencing state.json. No soft-delete mechanism.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — reviewer can check that archival operations preserve files for active state entries. Relevant reviewer: architecture-strategist.
- **Principle violated:** V20 regression — cleanup must cross-reference state.json before deleting/archiving
- **Fix type:** Implementation

### Failure 8: Accidental Vercel project creation
- **What happened:** `vercel --prod` without prior `vercel link` created a new project "v21" with alias `v21-ochre.vercel.app` instead of deploying to jsa-dashboard.
- **Root cause:** Running `vercel --prod` without a `.vercel/project.json` link creates a new project. Memory note documents the correct sequence but it wasn't followed.
- **Category:** deployment
- **Prevention:** Automated: Yes — check `.vercel/project.json` exists before deploying.
- **Principle violated:** Memory note: "vercel link --project jsa-dashboard --yes && vercel --prod --yes"
- **Fix type:** Implementation

### Failure 9: Preflight permissions check too strict
- **What happened:** settings.local.json only had one Bash entry. Preflight checked for tool name strings (`Read`, `Write`) that weren't in the file.
- **Root cause:** Preflight grep matched tool names in the permissions file, but the format used tool-specific patterns, not bare names.
- **Category:** configuration
- **Prevention:** Automated: Yes — preflight self-validation.
- **Principle violated:** V20 regression — settings.local.json must include Read, Write, Glob, Grep
- **Fix type:** Implementation

### Failure 10: Preflight heading grep too strict
- **What happened:** Grepped for `## Table Format` but actual heading was `## Uniform Table Format (I6 Standardization)`.
- **Root cause:** Exact heading match broke when heading text was annotated during V21 build.
- **Category:** testing
- **Prevention:** Automated: Yes — use partial/fuzzy matches in structural validation greps.
- **Principle violated:** No explicit constraint
- **Fix type:** Implementation

### Failure 11: send_email.py wrong flag (--html vs --body-file)
- **What happened:** First email send attempt used `--html` but actual flag is `--body-file`.
- **Root cause:** Orchestration references assumed flag name without checking `--help`.
- **Category:** configuration
- **Prevention:** Automated: Yes — CLI flag registry or preflight `--help` validation.
- **Principle violated:** No explicit constraint
- **Fix type:** Implementation

### Failure 12: git add gitignored file
- **What happened:** `git add` included `.claude/settings.local.json` which is in `.gitignore`. Commit failed.
- **Root cause:** Commit script included settings file without checking gitignore.
- **Category:** configuration
- **Prevention:** Automated: Yes — `git check-ignore` before adding.
- **Principle violated:** No explicit constraint
- **Fix type:** Implementation

### Failure 13: Sibling tool calls failing together
- **What happened:** When preflight Bash errored, parallel sibling tools (date capture, agent memory glob) also errored with "Sibling tool call errored."
- **Root cause:** Claude Code aborts all parallel tool calls when one fails.
- **Category:** subagent-coordination
- **Prevention:** Automated: No — platform behavior, not agent code.
- **Principle violated:** No explicit constraint
- **Fix type:** Architectural

### Failure 14: /export missing pre-compaction data
- **What happened:** `/export` only captured post-compaction content. Custom Python script needed to recover full transcript from JSONL.
- **Root cause:** `/export` reads current conversation window, not raw JSONL.
- **Category:** uncategorized
- **Prevention:** Automated: No — platform limitation.
- **Principle violated:** HC6 — gave uncertain UI feature claim initially
- **Fix type:** Implementation

### Constraint Violations (8)
1. **HC6:** Confidently told user `/export` would capture pre-compaction data, then backtracked
2. **HC7:** No incremental commit+push after search batches (V14/V16/V18/V19/V20 regression recurrence)
3. **HC10:** General-purpose dispatches missing `output_directory` and `dashboard_url` variables
4. **Context budget — parent read verified JSON directly:** Read `anthropic-customer-marketing-lead-startups-emea.json` in parent
5. **Context budget — parent read script internals:** Read `preflight.sh` source in parent to diagnose failures
6. **CR5/UX:** Told user to update Vercel Root Directory setting manually
7. **CR10:** session-state.md not updated after every search batch (V14/V16/V18/V19 regression recurrence)
8. **Recovery protocol:** Parent read individual verified JSON instead of `_summary.md`

## Fixes Needed

### Architectural Fixes

#### A1: Search subagent rate limit / time budget
- **What needs to change:** Split search-verify into search-only and verify-only phases, or add a hard time/tool-use budget. When the budget is exceeded, the subagent should checkpoint its progress and return partial results.
- **Files affected:** `.claude/agents/search-verify.md`, `references/subagent-search-verify.md`, CLAUDE.md orchestration section
- **Verification criteria:** Search subagent completes within 5 minutes; partial results are usable if interrupted

#### A2: GitHub Actions scheduled run architecture
- **What needs to change:** Decide whether to (a) replace `claude --print` with a Python script orchestrator that calls the Claude API directly with structured output and timeout control, (b) split the agent into smaller phases that each fit within GH Actions time limits, or (c) move to a different execution environment (e.g., a long-running server, Railway, etc.)
- **Files affected:** `.github/workflows/daily-digest.yml`, potentially new `scripts/scheduled_run.py`, `.github/jsa-config.json`
- **Verification criteria:** Scheduled run completes successfully within 90 minutes; produces verified JSONs + digest email

#### A3: Parallel tool call failure isolation
- **What needs to change:** Startup sequence should not run preflight in parallel with other startup tasks. Preflight must complete successfully before date capture / agent memory load.
- **Files affected:** CLAUDE.md startup sequence, `references/orchestration.md`
- **Verification criteria:** Preflight failure does not abort date capture or agent memory loading

### Implementation Fixes

#### I1: Preflight self-validation against actual CLI interfaces
- **What needs to change:** preflight.sh checks must validate that tested CLI flags exist in the actual `--help` output. Add a meta-validation step that runs `--help` on each script and confirms the flags referenced in preflight.sh are valid.
- **Files affected:** `scripts/preflight.sh`, potentially new `scripts/validate_preflight.py`
- **Verification criteria:** `preflight.sh` passes on a clean v21 directory; all flag references match `--help` output

#### I2: Preflight heading greps use partial matches
- **What needs to change:** Structural validation greps should use partial/fuzzy matches (e.g., `Table Format` not `## Table Format`). Section heading checks should tolerate annotations.
- **Files affected:** `scripts/preflight.sh`
- **Verification criteria:** Preflight passes when headings contain parenthetical annotations

#### I3: Archival must cross-reference state.json
- **What needs to change:** Cleanup/archival must check state.json `active_jobs` before archiving. Verified JSONs for still-active jobs must be preserved. Consider soft-delete (status flag) instead of file move.
- **Files affected:** `scripts/manage_state.py` (archive/cleanup subcommand), `references/orchestration.md`
- **Verification criteria:** After cleanup, all jobs in state.json with active status have corresponding verified JSONs in `output/verified/`

#### I4: Vercel deploy automation on version transition
- **What needs to change:** Add `vercel link --project jsa-dashboard --yes && vercel --prod --yes` as a mandatory post-push step. Preflight should verify `.vercel/project.json` exists and points to the correct project.
- **Files affected:** `scripts/preflight.sh`, `references/orchestration.md`, CLAUDE.md delivery section
- **Verification criteria:** After push, `curl -s https://jsa-dashboard.vercel.app/api/state` shows today's `run_date`

#### I5: Incremental commit+push after search batches (regression recurrence x5)
- **What needs to change:** Orchestration must enforce commit+push after each search batch completes, not defer to session end. This has recurred in V14, V16, V18, V19, V20 — it needs a hard enforcement mechanism, not just a checklist item.
- **Files affected:** `references/orchestration.md`, CLAUDE.md search workflow
- **Verification criteria:** `git log` shows separate commits for each search batch within a session

#### I6: session-state.md after every search batch (regression recurrence x5)
- **What needs to change:** Same enforcement mechanism as I5. Write session-state.md after every search batch, not just the first and last.
- **Files affected:** `references/orchestration.md`, CLAUDE.md
- **Verification criteria:** session-state.md updated timestamp matches each search batch completion

#### I7: send_email.py flag in orchestration references
- **What needs to change:** orchestration.md email delivery section must use `--body-file` not `--html`. Add `--help` validation to preflight.
- **Files affected:** `references/orchestration.md`, `scripts/preflight.sh`
- **Verification criteria:** Email sends on first attempt without flag errors

#### I8: General-purpose dispatch must include mandatory variables
- **What needs to change:** Every Task dispatch (not just named agents) must include `output_directory` and `dashboard_url` as explicit variables. Add to orchestration template.
- **Files affected:** `references/orchestration.md`, CLAUDE.md HC10
- **Verification criteria:** No general-purpose dispatch in a session lacks these variables

#### I9: settings.local.json comprehensive permissions
- **What needs to change:** settings.local.json must include permissions for all tools used by subagents (Read, Write, Glob, Grep, WebFetch, WebSearch, plus all known Bash script invocations). Preflight must validate minimum permission count.
- **Files affected:** `.claude/settings.local.json`, `scripts/preflight.sh`
- **Verification criteria:** Full session runs without any permission prompts for standard operations

#### I10: CR5 — never ask user to do technical work
- **What needs to change:** Vercel Root Directory changes, GH Actions config changes, and any other platform settings must be handled by the agent via CLI tools, not delegated to the user.
- **Files affected:** `references/orchestration.md` (delivery section)
- **Verification criteria:** No user complaint about being asked to do technical work

#### I11: Export transcript awareness
- **What needs to change:** CLAUDE.md should document that `/export` only captures post-compaction content. For full transcripts, use the JSONL conversion script. Never claim `/export` captures everything.
- **Files affected:** CLAUDE.md or `references/orchestration.md`
- **Verification criteria:** Agent correctly describes `/export` limitations when asked

## Solutions Extracted

### S1: Preflight debug pattern (read validator → read target → fix gap)
- When preflight fails, the effective debug sequence is: read the validation script to understand what it checks, read the file being validated to see the actual state, then fix the mismatch.
- **Category:** configuration
- **Transferable:** Yes

### S2: Search re-dispatch with SPECIAL_INSTRUCTIONS
- When aggregator search returns generic results, re-dispatch with `SPECIAL_INSTRUCTIONS` directing the agent to use company career pages directly and domain-specific queries.
- **Category:** subagent-coordination
- **Transferable:** Yes

### S3: Parallel multi-source dispatch
- Dispatch 3+ independent search subagents simultaneously with fully self-contained prompts. Collect and merge results. Key: each prompt must embed all required context (paths, profile, instructions).
- **Category:** subagent-coordination
- **Transferable:** Yes

### S4: Verify-before-brief guard
- Before dispatching brief generators, glob for verified JSON existence. If missing, dispatch verification subagent first. Prevents wasted brief runs.
- **Category:** data-integrity
- **Transferable:** Yes

### S5: Completion sentinel verification
- Check `<!-- BRIEF COMPLETE -->` sentinel with `tail -3` before dispatching downstream tasks. Machine-readable completion markers prevent dispatching on incomplete output.
- **Category:** subagent-coordination
- **Transferable:** Yes

### S6: Vercel link-before-deploy sequence
- Always `vercel link --project <name> --yes` before `vercel --prod --yes`. Without the link step, Vercel creates a new project.
- **Category:** deployment
- **Transferable:** Yes

### S7: JSONL transcript recovery
- When session compacts, the full pre-compaction transcript lives in raw JSONL. A Python script can parse user/assistant messages and tool blocks into readable markdown.
- **Category:** uncategorized
- **Transferable:** Yes

## Patterns Identified

### P1: Preflight Validation Recovery Loop
- **Steps:** Run preflight → observe failure → read script/config to understand mismatch → edit to fix → re-run preflight
- **Appeared in:** Session startup (3 consecutive cycles)
- **Skill candidate:** Yes — a "preflight repair" skill that diffs expectations against actual file state
- **Generalization:** Any agent with a validation harness will hit drift between checks and codebase

### P2: Subagent Reference Loading Triad
- **Steps:** Read agent def → dispatch explore to read reference doc → collect input data → construct JSON blob → dispatch named agent
- **Appeared in:** search-verify, brief-generator x3, briefs-html, digest-email dispatches
- **Skill candidate:** Yes — "load agent context" takes (agent_name, working_dir) and returns merged def + reference + variables
- **Generalization:** Any orchestrator with named agents and reference files

### P3: Search-Refine-Verify Pipeline
- **Steps:** Broad search → evaluate relevance → identify what went wrong → re-dispatch with corrected parameters → verify results
- **Appeared in:** First AI agent search → specialty source re-dispatch
- **Skill candidate:** No — refinement logic requires domain-specific judgment
- **Generalization:** Any search agent using aggregators + specialty sources

### P4: Verify-Before-Brief Guard
- **Steps:** Glob for verified JSONs → find missing → dispatch verification → then dispatch briefs
- **Appeared in:** Brief generation for ElevenLabs, MAGIC AI, Linda AI
- **Skill candidate:** Yes — "pre-brief verification check" prevents wasted downstream runs
- **Generalization:** Any pipeline with data-dependency gates between stages

### P5: CLI Flag Discovery and Correction
- **Steps:** Invoke CLI with assumed flags → observe error → run `--help` → re-invoke with correct flags
- **Appeared in:** manage_state.py dedup, send_email.py, manage_state.py sync
- **Skill candidate:** No — code smell indicating plan/implementation drift
- **Generalization:** Preflight should validate CLI flags at build time, not discover them at runtime

### P6: Deliver Phase (Generate-Verify-Send-Commit)
- **Steps:** Dispatch HTML generators → verify outputs exist → send email → update state → commit+push
- **Appeared in:** Delivery phase of session
- **Skill candidate:** Yes — mechanical and repeatable sequence
- **Generalization:** Any agent that generates artifacts, sends notifications, and commits to git

## Build Metrics

- **Build duration (total):** Unavailable — no timestamps recorded
- **Steps completed:** 22 / 22
- **Verification pass rate:** 5 / 5 capability checks passed
- **Regression count (new):** 0
- **Regression count (repeat):** 0
- **Review cycle count:** 3 (round 1 → revise → round 2 → revise → round 3 approved)
- **Session failures (runtime):** 14 (4 critical, 4 major, 6 minor)
- **Constraint violations:** 8
- **Session duration (test run):** ~5h 20min (including ~2h rate limit gap)
- **Subagent dispatches (test run):** ~18

## Handoff Contract
- Architectural fixes: 3 — (A1) search subagent rate/time budget, (A2) GH Actions scheduled run architecture, (A3) parallel tool call failure isolation
- Implementation fixes: 11 — (I1) preflight CLI self-validation, (I2) partial heading matches, (I3) archival cross-references state.json, (I4) Vercel deploy automation, (I5) incremental commit+push enforcement, (I6) session-state after every batch, (I7) send_email flag fix, (I8) mandatory dispatch variables, (I9) comprehensive settings.local.json, (I10) CR5 no user technical work, (I11) export transcript awareness
- New constraints: HC7 incremental commit enforcement mechanism (beyond checklist), HC10 apply to all dispatches not just named agents
- Regression tests to include: HC7 recurrence (5th time), CR10 recurrence (5th time), V20 archival cross-reference, Vercel deploy on transition
- Prevention artifacts written: 3 reviewer prompt additions (data-integrity-guardian, architecture-strategist, deployment-verifier)
- Metrics recorded: V21 — 22/22 steps, 14 session failures, 8 constraint violations

<!-- STAGE COMPLETE: /analyze, 2026-02-19 -->

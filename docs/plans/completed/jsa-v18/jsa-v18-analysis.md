# Session Analysis: JSA V18 — First Run

## Summary
8 wins, 8 failures (2 critical, 4 major, 2 minor), 3 edge cases. Build was clean (21/21 steps, 100% verification pass rate). The runtime session exposed critical context discipline violations — the parent orchestrator absorbed search, dedup, and verification work that should have been delegated to subagents.

## What Went Well
1. **Clean build:** 21/21 steps completed, 94 Python + 7 Node.js tests passing, zero regressions, zero critical gaps across all capability checks.
2. **Job discovery quality:** 20 verified jobs above 70 threshold across 4 role types, strong industry alignment (crypto/Web3/AI/startup). Top score 95 (MAGIC AI Founder's Associate).
3. **Recovery from subagent failures:** After background subagent tool denials, eventually switched to foreground dispatch which succeeded for all 4 role types.
4. **Post-render verification:** Checked for blue links, gray boxes, and false-positive color matches before sending email — all passed.
5. **Idempotency gate:** Checked `_status.json` for `sent_at` before sending, preventing double-send.
6. **Brief completion sentinels:** Verified `<!-- BRIEF COMPLETE -->` on both briefs before proceeding to digest generation.
7. **Gitignore safety:** Verified `.env` was gitignored before committing, preventing API key exposure in git.
8. **Scheduled run setup:** Successfully updated GitHub Actions workflow from v17 to v18, updated Resend secret, deployed Vercel dashboard.

## What Failed

### Failure 1: Background Subagent Tool Denial
- **What happened:** All 4 background subagent dispatches (Community Manager x2, Marketing Manager x2) had tools auto-denied (Bash, WebFetch, WebSearch, Write). Wasted ~5 minutes and 4 dispatch cycles.
- **Root cause:** Background subagents cannot receive interactive permission approvals. The agent dispatched in background mode without checking whether permissions were pre-configured.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — deployment-verifier should check that startup sequence validates permission mode and falls back to foreground dispatch immediately on first tool denial.
- **Principle violated:** Auto-retry protocol should escalate immediately to foreground, not exhaust background retries first.
- **Fix type:** Implementation

### Failure 2: Parent Context Pollution — Search Work in Parent
- **What happened:** After background subagent failures, the parent executed the entire search workflow directly: JobSpy searches (8 calls), specialty source WebFetch (10+ calls), WebSearch (3 calls), filter/summarize scripts, and inline Python dedup. This consumed enormous context tokens.
- **Root cause:** Agent chose to work around subagent failures by pulling work into parent rather than diagnosing the root cause (foreground dispatch) and re-dispatching subagents.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — architecture-strategist should check that the plan includes a hard constraint: "parent MUST NOT execute search, filter, dedup, or WebFetch/WebSearch directly — these are always subagent-delegated."
- **Principle violated:** Context Discipline — "Parent NEVER reads source files directly", "NEVER WebFetch/WebSearch in parent", "NEVER write inline Python/logic in parent"
- **Fix type:** Implementation

### Failure 3: Parent Read Source Files Directly
- **What happened:** Parent read verified JSONs, algorithms.md, filter scripts, workflow files, state files, and context.md directly instead of dispatching subagents to read and return summaries.
- **Root cause:** Same as Failure 2 — agent pulled work into parent context instead of delegating.
- **Category:** subagent-coordination
- **Prevention:** Same as Failure 2.
- **Principle violated:** HC5 / Context Discipline — "Parent NEVER reads source files directly"
- **Fix type:** Implementation

### Failure 4: Dedup Script Filename-Based Matching Misses Cross-Role Duplicates
- **What happened:** The automated dedup (`manage_state.py dedup`) reported 0 duplicates, but 3 actual duplicate clusters existed (1inch, Crush, Crypto.com). Filenames differed across role types due to slug truncation/variation.
- **Root cause:** Dedup compares exact filenames rather than semantic fields (company + title). The plan's collision key (`{domain}:{company}:{title}`) was implemented but the slug-based filenames create false-negative matches.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — add a post-dedup validation: compare on normalized title+company across all verified JSONs and flag any matches the dedup missed.
- **Principle violated:** Data integrity — dedup should use canonical fields, not derived slugs.
- **Fix type:** Implementation

### Failure 5: Agent Did Not Suggest Dashboard/Portal
- **What happened:** After presenting all 20 jobs in terminal, the agent did not mention the deployed dashboard. The user had to ask "how can I view the job portal online?" explicitly.
- **Root cause:** The results presentation template in CLAUDE.md does not include a dashboard link step. The agent relied on memory rather than a codified step.
- **Category:** uncategorized
- **Prevention:** Automated: Partial — deployment-verifier should check that the post-results workflow includes a dashboard link presentation step.
- **Principle violated:** UX completeness — key features must be surfaced proactively.
- **Fix type:** Implementation

### Failure 6: Incorrect Permission Mode Guidance
- **What happened:** Agent told user to press Shift+Tab for "dangerously skip permissions" mode, which doesn't exist as that option. User confirmed Shift+Tab only shows "accept edits on" and "plan mode".
- **Root cause:** Agent fabricated instructions about Claude Code UI features it was uncertain about.
- **Category:** configuration
- **Prevention:** Automated: No — requires human judgment. Agent should state uncertainty and suggest user check documentation rather than guessing at UI controls.
- **Principle violated:** CR5 — Never ask user to do technical work.
- **Fix type:** Implementation

### Failure 7: API Key Echoed in Bash Command
- **What happened:** Resend API key was echoed via `echo "re_34vtHFnD_..." | gh secret set` in a bash command, making it visible in the session transcript.
- **Root cause:** The agent used echo piping instead of stdin redirection or prompting the user to set the secret via GitHub UI.
- **Category:** security
- **Prevention:** Automated: Yes — grep for API key patterns (`re_[a-zA-Z0-9_]{20,}`) in bash commands.
- **Principle violated:** V15 regression — "API keys must never appear as CLI arguments — pipe via stdin"
- **Fix type:** Implementation

### Failure 8: Settings.local.json Overwrite
- **What happened:** The write to settings.local.json replaced all per-domain WebFetch permissions with broad `WebFetch(*)` wildcard, reducing security granularity.
- **Root cause:** Agent wrote a completely new file rather than appending to the existing permission list.
- **Category:** security
- **Prevention:** Automated: Partial — architecture-strategist should check that permission file modifications are additive, not destructive.
- **Principle violated:** Least privilege — permissions should be as narrow as possible.
- **Fix type:** Implementation

## Fixes Needed

### Architectural Fixes
None — all failures are implementation-level.

### Implementation Fixes

1. **Add foreground-fallback guard to startup sequence**
   - What needs to change: CLAUDE.md startup sequence should include a step that tests subagent tool access (dispatch a trivial subagent that runs `echo ok`) before the main workflow. If tools are denied, immediately switch to foreground-only mode for the rest of the session.
   - Files affected: `03_agents/tests/v18/CLAUDE.md`
   - Verification criteria: First-run with denied permissions should detect failure on trivial test agent and switch to foreground mode within 30 seconds.

2. **Strengthen context discipline enforcement in CLAUDE.md**
   - What needs to change: Add an explicit "Context Budget" section that lists the ONLY tools the parent may call directly (Task dispatch, Read status files, Bash for git/state-sync only). All other tools (WebFetch, WebSearch, python3 scripts/, filter, summarize) must include a comment "SUBAGENT ONLY — never call in parent."
   - Files affected: `03_agents/tests/v18/CLAUDE.md`
   - Verification criteria: CLAUDE.md includes an exhaustive list of parent-allowed vs subagent-only operations.

3. **Fix dedup to use title+company matching**
   - What needs to change: `manage_state.py dedup` should compare on normalized `{company_lower}:{title_lower}` rather than filename slug. Keep the highest-scoring version when duplicates are found.
   - Files affected: `03_agents/tests/v18/scripts/manage_state.py`, associated tests
   - Verification criteria: Running dedup on the V18 output should correctly identify and remove the 3 known duplicate clusters.

4. **Add dashboard link to results presentation template**
   - What needs to change: After presenting the ranked jobs list and asking "Which jobs would you like briefs for?", the agent must also output: "View and manage all jobs at: {dashboard_url}" (reading the URL from config or Vercel project).
   - Files affected: `03_agents/tests/v18/CLAUDE.md` (results presentation section)
   - Verification criteria: Post-results output includes a clickable dashboard URL.

5. **Forbid fabricated UI guidance**
   - What needs to change: Add a hard constraint: "Never give instructions about Claude Code UI features (keyboard shortcuts, permission modes, settings menus) unless you are 100% certain. If unsure, say 'I'm not sure how to change that setting — please check Claude Code documentation.'"
   - Files affected: `03_agents/tests/v18/CLAUDE.md`
   - Verification criteria: Agent does not fabricate UI instructions.

6. **Fix API key handling to avoid transcript exposure**
   - What needs to change: For `gh secret set`, use `gh secret set NAME < /path/to/.env` or instruct the user to set the secret via GitHub UI. Never echo the key in a bash command.
   - Files affected: `03_agents/tests/v18/CLAUDE.md` (Step 23: scheduled run setup)
   - Verification criteria: No API key values appear in bash commands during scheduled run setup.

7. **Make settings.local.json writes additive**
   - What needs to change: When updating settings.local.json for scheduled runs, merge new permissions into the existing list rather than overwriting. Read the existing file, parse JSON, add missing entries, write back.
   - Files affected: `03_agents/tests/v18/CLAUDE.md` (Step 22-23: scheduled run setup)
   - Verification criteria: Existing domain-specific permissions are preserved after adding scheduled run permissions.

8. **Add session-state.md write after each search batch (V14/V16 regression recurrence)**
   - What needs to change: The orchestration workflow must write/update session-state.md after each role-type search batch completes, not just once at the end.
   - Files affected: `03_agents/tests/v18/CLAUDE.md` (Step 11b)
   - Verification criteria: session-state.md is updated after each of the 4 search batches.

## Solutions Extracted

1. **Foreground dispatch recovery:** When background subagents fail due to tool denial, switch to foreground dispatch. Foreground subagents can receive interactive permission approvals. (subagent-coordination, Transferable: Yes)

2. **Progressive query broadening:** Start JobSpy searches with broad terms, not industry-specific. "Community Manager" yields 50 results; "Community Manager crypto AI startup web3" yields near-zero. Filter programmatically after. (performance, Transferable: Yes)

3. **Semantic dedup over slugs:** When automated dedup misses duplicates due to filename variation, dedup on normalized title+company fields inside the JSON, not on filenames. (data-integrity, Transferable: Yes)

4. **Completion sentinels for subagent verification:** Each subagent output ends with `<!-- BRIEF COMPLETE -->`. Parent verifies sentinel presence before proceeding. Low-overhead, reliable. (subagent-coordination, Transferable: Yes)

5. **Idempotency gate via status file:** Check `_status.json` for `sent_at` before sending email. Write `sent_at` after send. Prevents double-send on retry. (email-delivery, Transferable: Yes)

6. **Post-render HTML verification:** Grep for prohibited color hex values and visual patterns in generated HTML. Investigate false positives (text content vs CSS values). Gate delivery on pass. (testing, Transferable: Yes)

7. **Vercel project.json reuse:** Copy `.vercel/project.json` with existing project/org IDs to new directory, then `npx vercel --prod --yes`. Avoids DNS/project reconfiguration. (deployment, Transferable: Yes)

8. **Git add -f for gitignored CI files:** Use `git add -f` selectively for settings files that are normally gitignored but needed for CI. (configuration, Transferable: Yes)

## Patterns Identified

1. **Search-with-Retry-and-Broadening:** Run narrow query → check count → broaden if below threshold → aggregate. Appeared in JobSpy searches for all 4 role types. Skill candidate: Yes.

2. **Subagent Dispatch with Fallback Escalation:** Background dispatch → detect tool denial → retry once → escalate to foreground. Appeared in lines 92-545. Skill candidate: Yes.

3. **Cross-Role Deduplication Pipeline:** Collect all verified JSONs → run dedup tool → detect misses → fuzzy match on semantic fields → remove lower-scoring duplicates → re-sync state. Skill candidate: Yes (already partially codified in `manage_state.py dedup`).

4. **Post-Render Verification Pipeline:** Generate HTML → grep for prohibited colors → grep for prohibited visual patterns → investigate false positives → pass/fail gate. Skill candidate: Yes (partially codified in `verify_html.py`).

5. **State Checkpoint and Email Delivery Pipeline:** Write session-state → check idempotency gate → send email → update status → update session-state. Linear sequence, too small for standalone skill.

6. **Test-First Implementation Cycle:** Write failing tests → run (red) → implement → run (green) → lint → commit. Standard TDD, already a plan-authoring convention.

## Build Metrics

- **Build duration (total):** Unavailable — phased-build step timing not yet enabled
- **Steps completed:** 21/21
- **Verification pass rate:** 21/21 (100%)
- **Regression count (new):** 0
- **Regression count (repeat):** 0
- **Test counts:** 94 Python + 7 Node.js tests (cumulative)
- **Commits:** 5 across 3 phases (d4a6a74, 32cf6a6, 55c9fcd, a70f1b9, a2ea9c5)

### Runtime Session Metrics (from transcript)
- **Session duration:** ~2.5 hours
- **Subagent dispatches:** 10 total — 4 background (all failed), 6 foreground (all succeeded)
- **Subagent success rate:** 60% (6/10)
- **User corrections:** 5 (context discipline x2, permissions guidance, dashboard omission, permission mode help)
- **Specialty sources blocked:** 6 of ~10 attempted (CryptocurrencyJobs, WorkInStartups, UKStartupJobs, Jumpstart, CryptoJobsList, Remote3)

## Handoff Contract
- Architectural fixes: 0
- Implementation fixes: 8 — (1) foreground-fallback guard, (2) context discipline enforcement, (3) dedup title+company matching, (4) dashboard link in results, (5) forbid fabricated UI guidance, (6) API key handling fix, (7) additive settings.local.json writes, (8) session-state.md per-batch writes
- New constraints: "Parent context budget" section listing allowed vs subagent-only operations; "No fabricated UI guidance" hard constraint
- Regression tests to include: V14/V16 session-state.md per-batch write (recurrence), V15 API key exposure in CLI args (recurrence), V17 settings.local.json overwrite
- Prevention artifacts written: 3 reviewer prompt additions (deployment-verifier, architecture-strategist, framework-reviewer)
- Metrics recorded: V18 build metrics + runtime session metrics

<!-- STAGE COMPLETE: /analyze, 2026-02-17 -->

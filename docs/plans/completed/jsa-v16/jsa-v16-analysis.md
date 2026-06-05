# Session Analysis: JSA V16

## Summary

First interactive run of V16. 7 wins, 9 failures (3 major, 6 minor), 2 edge cases. End-to-end pipeline completed: 16 jobs found, 5 briefs generated, email sent. Session duration ~80 minutes.

## What Went Well

1. **Onboarding was clean** — one question at a time, every turn waited for response. User added Marketing Associate organically and it was picked up immediately.
2. **Source research produced 17 accessible sources** across all 3 target industries. Blocked sources (4) correctly identified and separated.
3. **User feedback acted on immediately** — role type addition, source removal, and format corrections all applied within the same turn.
4. **Deduplication caught correctly** — 1inch Social Media Manager in two role types; higher-scoring copy kept (95 vs 88).
5. **Rate limit recovery succeeded** — Founder's Associate had 7/7 verified before limit; Marketing Associate retried and produced 4 verified jobs.
6. **Email pipeline completed end-to-end** — digest HTML + briefs HTML generated, email sent with attachment, state persisted.
7. **Scheduled run setup was seamless** — both GitHub secrets already existed, workflow file confirmed, no user technical work required.

## What Failed

### Failure 1: Off-by-one score threshold
- **What happened:** Jobs scoring exactly 70 (Kernel, Aztec) were presented as "below threshold" and excluded. User corrected: "70 isn't below the threshold?"
- **Root cause:** Comparison used `> 70` instead of `>= 70`. The CLAUDE.md says "Minimum score threshold: 70. Only present jobs scoring 70+."
- **Principle violated:** PRESENTATION WORKFLOW — minimum score threshold
- **Fix type:** Implementation

### Failure 2: No unified numbered list for job selection
- **What happened:** Results grouped by role type in 4 separate tables without unified numbering. User had to ask twice for numbered lists (once for sources, once for jobs).
- **Root cause:** Presentation format follows the CLAUDE.md template which groups by role type with per-group footnotes. But no instruction exists to provide a unified numbered list when asking "which jobs do you want briefs for?"
- **Principle violated:** UX RULES — ease of selection. CLAUDE.md presentation template lacks a unified selection view.
- **Fix type:** Architectural (needs a new presentation step: after per-role-type tables, show a unified numbered summary for selection)

### Failure 3: Parent read verified JSONs into context after rate limit
- **What happened:** After batch 2 rate limit, parent read all 7 Founder's Associate verified JSONs directly (bloating context). User called this out: "you should be using a subagent to do this."
- **Root cause:** No graceful partial-recovery path when a subagent completes work but fails to write `_status.json`. Parent fell back to manual inspection.
- **Principle violated:** CORE RULE 6 (batch work within context limits). Step 12 says read `_summary.md`, not individual JSONs.
- **Fix type:** Implementation (add explicit instruction: on subagent failure, dispatch a recovery subagent to read outputs and write summary — never read verified JSONs in parent)

### Failure 4: Marketing Associate retry ran inline in parent
- **What happened:** The Marketing Associate retry was dispatched as a `search-verify` named agent call but within the parent context rather than as a proper background subagent. User flagged this.
- **Root cause:** After rate limit, parent treated the retry as a quick fix rather than following the batch dispatch protocol. The auto-retry protocol says "Retry once. Same variables, same agent type" but doesn't explicitly say "as a subagent."
- **Principle violated:** CORE RULE 6 (batch work dispatched to subagents)
- **Fix type:** Implementation (clarify auto-retry protocol: "Retry as a subagent dispatch via Task tool — never inline in parent")

### Failure 5: preview.sh kills server on exit
- **What happened:** `scripts/preview.sh` uses `trap cleanup EXIT` which kills the HTTP server immediately when the script exits. Agent had to start an ad-hoc `python3 -m http.server` as workaround, violating Core Rule 8.
- **Root cause:** Script design flaw — the trap pattern is correct for interactive shells but doesn't work when called from a subagent's ephemeral Bash session.
- **Principle violated:** CORE RULE 8 (use preview.sh, no ad-hoc servers). Also regression from V14: "No ad-hoc HTTP servers."
- **Fix type:** Implementation (fix preview.sh to background the server and not kill it on script exit; or use `nohup`)

### Failure 6: Agent asked for email send confirmation
- **What happened:** Agent asked "let me know if you're happy for me to send" before emailing. User said: "you should just go ahead and send them once you've run your checks."
- **Root cause:** Step 20 has pre-send gates (idempotency, briefs-html check) but no explicit "do not ask user for confirmation" instruction. The agent added an unnecessary confirmation gate.
- **Principle violated:** UX RULES — never ask user to do technical work extends to unnecessary confirmations. The pre-send gate IS the confirmation mechanism.
- **Fix type:** Implementation (add explicit instruction to Step 20: "Do NOT ask user for confirmation. The pre-send gate checks are sufficient. Send immediately after checks pass.")

### Failure 7: Session-state.md not written after batch 1
- **What happened:** session-state.md was only written once after all batches and dedup, not after batch 1 completed.
- **Root cause:** Step 11 says "MANDATORY: Write output/session-state.md after every search batch completes" but this was ignored.
- **Principle violated:** ORCHESTRATION WORKFLOW Step 11. Also regression from V14: "session-state.md must be written after every search batch."
- **Fix type:** Implementation (already specified in CLAUDE.md — need to make it more prominent or add a checkpoint assertion)

### Failure 8: Onboarding skipped explicit "target roles" question
- **What happened:** Agent inferred 3 role types from CV and presented them. Never asked "What types of roles are you targeting?" as the onboarding sequence requires (step 5). User had to volunteer "Marketing Associate" correction organically.
- **Root cause:** The onboarding subagent inferred roles from CV and the parent presented them for confirmation, but never posed the explicit question from the onboarding sequence.
- **Principle violated:** ONBOARDING step 5: "Ask: What types of roles are you targeting?"
- **Fix type:** Implementation (ensure onboarding flow asks the question explicitly, not just presents inferred roles)

### Failure 9: No salary filtering/demotion in presentation
- **What happened:** Re7 Capital (score 92, Marketing Manager) was presented at #2 ranking despite salary ($39-45K USD / ~£31-36K) being below the user's £40K minimum. Flagged with asterisk footnote but not demoted or filtered.
- **Root cause:** Scoring algorithm doesn't penalize below-minimum salary. CLAUDE.md has no explicit rule to filter or demote below-salary jobs — only to present the salary concern as a footnote.
- **Principle violated:** User constraint (minimum salary £40,000). The constraint was derived and confirmed during onboarding but not enforced in scoring or presentation ordering.
- **Fix type:** Architectural (add salary validation: either exclude below-salary jobs or apply a score penalty that pushes them below higher-scoring jobs that meet salary requirements)

## Fixes Needed

### Architectural Fixes

1. **Add unified numbered selection view after role-type tables**
   - **What needs to change:** After presenting per-role-type tables (Step 16), add a new presentation step: "Unified Selection View" — a single ranked-by-score table with row numbers 1-N across all role types. Use this for brief selection (Step 17).
   - **Files affected:** `03_agents/tests/v16/CLAUDE.md` (PRESENTATION WORKFLOW section + Step 16-17)
   - **Verification criteria:** User can select jobs by number from a single list; no need to cross-reference role-type tables

2. **Add salary validation to scoring or presentation**
   - **What needs to change:** Jobs with salary below the user's minimum should either (a) receive a score penalty (e.g., -15 points) or (b) be grouped separately as "Below Salary Minimum" after the main results. The user confirmed £40K minimum — jobs clearly below should not rank alongside compliant jobs.
   - **Files affected:** `03_agents/tests/v16/CLAUDE.md` (PRESENTATION WORKFLOW + CONSTRAINT DERIVATION), potentially `scripts/filter_jobs.py`
   - **Verification criteria:** Below-salary jobs are visually separated or score-penalized; never rank above salary-compliant jobs of similar quality

### Implementation Fixes

3. **Fix off-by-one score threshold**
   - **What needs to change:** CLAUDE.md already says "70+" but the agent applied `> 70`. Add explicit clarification: "Threshold is inclusive: score >= 70."
   - **Files affected:** `03_agents/tests/v16/CLAUDE.md` (PRESENTATION WORKFLOW)
   - **Verification criteria:** Score-70 jobs appear in results without user correction

4. **Fix auto-retry to always use subagent dispatch**
   - **What needs to change:** AUTO-RETRY PROTOCOL should explicitly state: "Retry as a subagent dispatch via Task tool. Never retry inline in parent context."
   - **Files affected:** `03_agents/tests/v16/CLAUDE.md` (AUTO-RETRY PROTOCOL section)
   - **Verification criteria:** Rate limit recovery dispatches a new subagent; parent context doesn't grow

5. **Add recovery subagent instruction for partial failures**
   - **What needs to change:** When a subagent completes work but fails to write `_status.json`, the parent must dispatch a lightweight recovery subagent to: read the verified directory, count files, write `_status.json` and `_summary.md`. Parent must never read individual verified JSONs.
   - **Files affected:** `03_agents/tests/v16/CLAUDE.md` (AUTO-RETRY PROTOCOL or new RECOVERY PROTOCOL section)
   - **Verification criteria:** After subagent failure, parent dispatches recovery subagent; no verified JSONs read into parent context

6. **Fix preview.sh server persistence**
   - **What needs to change:** `scripts/preview.sh` must not kill the server on script exit. Use `nohup` or background the process and write PID to a file. Remove `trap cleanup EXIT` or make it conditional.
   - **Files affected:** `03_agents/tests/v16/scripts/preview.sh`
   - **Verification criteria:** After `preview.sh` exits, the HTTP server remains accessible at localhost:8800

7. **Add "no confirmation" instruction to Step 20**
   - **What needs to change:** Step 20 should explicitly state: "Do NOT ask user for email send confirmation. The pre-send gate checks (idempotency + briefs-html check) are the safety mechanism. Send immediately after checks pass."
   - **Files affected:** `03_agents/tests/v16/CLAUDE.md` (Step 20)
   - **Verification criteria:** Email is sent automatically after post-render verification; no "are you happy to send?" prompt

8. **Make session-state checkpoint more prominent**
   - **What needs to change:** Step 11's "MANDATORY" instruction was ignored. Add it as a CORE RULE or HARD CONSTRAINT to increase compliance: "MUST write session-state.md after every search batch — not just at end of all batches."
   - **Files affected:** `03_agents/tests/v16/CLAUDE.md` (Step 11, possibly promote to CORE RULES)
   - **Verification criteria:** session-state.md updated after each batch of search-verify subagents completes

9. **Fix onboarding to ask target roles explicitly**
   - **What needs to change:** The onboarding flow presents inferred roles but never asks the explicit question "What types of roles are you targeting?" The parent must ask this question even if roles were inferred from CV — the inferred list is a suggestion, not a final answer.
   - **Files affected:** `03_agents/tests/v16/CLAUDE.md` (ONBOARDING step 5)
   - **Verification criteria:** Onboarding conversation includes explicit "What types of roles are you targeting?" question with inferred roles as suggestion

## Handoff Contract
- Architectural fixes: 2 — unified numbered selection view, salary validation in scoring/presentation
- Implementation fixes: 7 — off-by-one threshold, auto-retry subagent dispatch, recovery subagent protocol, preview.sh fix, no-confirmation email send, session-state checkpoint promotion, explicit target roles question
- New constraints: "Threshold is inclusive (>=70)", "Auto-retry always via subagent", "No email confirmation prompt", "Ask target roles explicitly even when inferred"
- Regression tests to include: off-by-one threshold, parent context bloat on subagent failure, preview.sh server persistence, email sent without confirmation, session-state.md written per-batch

My comments:

- Currently the agent researches sources twice, there's no need for this. Only the deep search should persist to the next version. The first search just slows things down and uses unnessary tokens. 

- The next version should itegrate /Users/ryanhennebry/Projects/autonomous1/docs/plans/active/jsa-v17-dashboard-design.md so it's a considerable update, make sure that is documented aswell. 

For anything you're unsure on, interview me in detail during the /design phase using the AskUserQuestionTool about literally anything: 
- Technical implementation
- UI & UX
- Concerns
- Tradeoffs, etc. 

But make sure the questions are not obvious

Be very in-depth and continue interviewing me continually until it's complete, then write the spec to the file.

<!-- STAGE COMPLETE: /analyze, 2026-02-11 -->

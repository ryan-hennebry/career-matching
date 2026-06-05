# Session Analysis: Job Search Agent V15

## Summary
7 wins, 7 failures, 2 edge cases. First interactive run of V15 completed end-to-end (onboarding through email delivery and scheduled run setup). Core search/verify/brief/email pipeline works. Failures are concentrated in UX polish and operational protocol compliance.

## What Went Well
1. **Onboarding flow was smooth** — guided single-question interview, CV parsing via onboarding subagent, profile confirmation with user edits
2. **Parallel search-verify dispatch** — both role types searched simultaneously, 14 jobs above threshold from 17 total
3. **Scoring and filtering quality** — good signal-to-noise, salary flags (*) and unverified markers (†) used correctly
4. **Design system preloading worked** — frontend-design skill invoked once, passed to both HTML subagents, post-render verification passed all 4 checks
5. **Graceful state correction** — user interrupted bulk rejection, agent correctly undid rejections and kept other jobs neutral
6. **Context window discipline** — user enforced subagent pattern, agent complied immediately
7. **Scheduled run setup completed** — cron, secrets, commit, push all handled by agent

## What Failed

### Failure 1: Accept/Reject Semantics Misinterpretation
- **What happened:** User listed 4 jobs for briefs. Agent interpreted as "accept these 4, reject all others" instead of "generate briefs for these 4 only." Required user interruption and manual rollback.
- **Root cause:** Workflow only offers binary accept/reject. No third option for "brief these without rejecting the rest."
- **Principle violated:** User intent preservation — agent assumed reject when user only meant "brief these"

### Failure 2: State Object API Misuse
- **What happened:** `TypeError: 'State' object is not subscriptable` when trying to clear rejections via ad-hoc Python one-liner using `state['jobs']` dict syntax
- **Root cause:** manage_state.py uses a typed State object, not a dict. Agent wrote inline Python using wrong API.
- **Principle violated:** Use scripts via CLI interface, not ad-hoc Python against internal APIs

### Failure 3: Git Pull Skipped at Startup
- **What happened:** Interactive mode startup protocol requires git pull (step 2). Agent skipped it, went straight to state load.
- **Root cause:** Startup sequence not followed strictly
- **Principle violated:** 20-step orchestration workflow — step 2 (git pull) mandatory in interactive mode

### Failure 4: Email Idempotency Check Missing
- **What happened:** Email sent without first checking `_status.json` for existing `sent_at` field (pre-send gate)
- **Root cause:** No idempotency guard in the email send flow
- **Principle violated:** Pre-send gate constraint — must check `_status.json` before sending

### Failure 5: API Key Exposure in Bash Output
- **What happened:** RESEND_API_KEY and ANTHROPIC_API_KEY visible as CLI arguments in `gh secret set --body "..."` commands
- **Root cause:** Keys passed via `--body` flag instead of stdin piping
- **Principle violated:** API key security — keys should never appear in command output

### Failure 6: Missing Proactive Scheduled Run Prompt
- **What happened:** After completing first interactive run, agent did not ask user if they want to set up scheduled runs. User had to bring it up.
- **Root cause:** Not in the agent's post-run flow (step 20 only writes session-state.md)
- **Principle violated:** Agent should proactively offer scheduled run setup after first successful interactive session

### Failure 7: Missing API Key Source Guidance
- **What happened:** When asking for Anthropic API key, agent didn't provide the URL (console.anthropic.com/settings/keys). User had to ask "where can I find it?"
- **Root cause:** No instruction in CLAUDE.md for API key onboarding UX
- **Principle violated:** "Never ask user to do technical work" — should provide exact instructions when requesting credentials

## Fixes Needed

### Implementation Fixes

1. **Add "brief only" action distinct from accept/reject**
   - What needs to change: When user selects jobs for briefs, record as "brief_requested" not "accepted". Do not reject unselected jobs. Only reject when user explicitly says "reject."
   - Files affected: CLAUDE.md (step 15 instructions), manage_state.py (add `brief_requested` action type)
   - Verification criteria: User can select jobs for briefs without other jobs being rejected. Unselected jobs remain in neutral state.

2. **Remove ad-hoc Python one-liners for state management**
   - What needs to change: All state mutations must go through `scripts/manage_state.py` CLI. Add a `clear-rejections` subcommand if needed.
   - Files affected: CLAUDE.md (add constraint: "never write inline Python for state mutations"), scripts/manage_state.py (add clear-rejections command if missing)
   - Verification criteria: No `python3 -c` calls that import manage_state internals

3. **Enforce git pull at startup**
   - What needs to change: Add explicit check in CLAUDE.md startup protocol that git pull is verified before proceeding
   - Files affected: CLAUDE.md (startup section)
   - Verification criteria: Transcript shows `git pull` execution before any file reads

4. **Add email idempotency guard**
   - What needs to change: Before calling send_email.py, check `_status.json` for `sent_at` field matching today's date. If already sent, skip and inform user.
   - Files affected: CLAUDE.md (step 19 instructions)
   - Verification criteria: Running email send twice in same session does not send duplicate email

5. **Pipe API keys via stdin instead of CLI args**
   - What needs to change: Use `echo "$KEY" | gh secret set NAME --body -` or heredoc instead of `--body "value"` to avoid key exposure in command history/output
   - Files affected: CLAUDE.md (scheduled run setup instructions)
   - Verification criteria: API keys not visible in bash command arguments in transcript

6. **Add post-run scheduled run prompt**
   - What needs to change: After step 20 (final checkpoint), if this is the first interactive run (no previous `sent_at` in state), ask: "Would you like to set up a daily scheduled run?"
   - Files affected: CLAUDE.md (add step 21 or post-run hook)
   - Verification criteria: Agent proactively offers scheduled run setup after first interactive session

7. **Add API key onboarding UX with source URLs**
   - What needs to change: When requesting any API key, always provide the exact URL where user can find/create it. Resend: resend.com/api-keys. Anthropic: console.anthropic.com/settings/keys.
   - Files affected: CLAUDE.md (delivery/email section)
   - Verification criteria: Every API key request includes the source URL in the same message

## Handoff Contract
- Architectural fixes: 0
- Implementation fixes: 7 — (1) brief-only action type, (2) no ad-hoc state Python, (3) enforce git pull, (4) email idempotency guard, (5) stdin for API keys, (6) post-run scheduled prompt, (7) API key source URLs
- New constraints: "Never write inline Python for state mutations", "Always provide source URL when requesting API keys", "Always offer scheduled run setup after first interactive session"
- Regression tests to include: accept/reject semantics, email idempotency, git pull at startup, API key not in bash args

My Comments: 

- The subagent that researched job boards produced thin output. The sources were correct, but there wasn't many of them and they weren't yet unique/niche, not really giving the candidate an edge. I'd like more effort to go into this stage as it ultimately determines the quality of the output for the rest of the agent. It should do research on the best job boards for the specific industries the user has mentioned, including niche job boards such as email/substack newsletters that aren't obvious but are high value (https://earlyandexec.substack.com is a good example but the agent should do the research, not just use this source.). Once the agent is done it should then come back to the user and ask them whether they're happy with the sources and if they want to add any specific ones that weren't mentioned before proceeding. 

<!-- STAGE COMPLETE: /analyze, 2026-02-11 -->


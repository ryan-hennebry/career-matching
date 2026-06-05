# Session Analysis: Job Search Agent V17

## Summary
7 wins, 11 failures (3 critical, 4 major, 4 minor), 4 edge cases. Build was clean (46/46 steps, 0 regressions), but the interactive session exposed 3 critical infrastructure failures and 2 constraint violations. The GitHub Actions scheduled run also failed (settings.local.json missing in CI).

## What Went Well
1. **Batched search execution**: 4 role types searched in 2 batches of 2, all completing cleanly with 28 jobs above threshold
2. **Cross-role deduplication**: 3 duplicates detected and resolved deterministically by highest score
3. **Checkpoint commits**: 3 incremental commits (batch 1, batch 2 + dedup, briefs + digest) creating recoverable state trail
4. **Parallel brief generation**: 4 briefs dispatched simultaneously, all passed sentinel verification
5. **Email delivery**: Digest email sent successfully via Resend API with tracked message ID
6. **Context-preserving debugging**: Used Explore + Task subagent pattern for all 5 debugging investigations, keeping parent context lean
7. **Design system verification**: Post-render checks on briefs HTML and digest email caught no real styling violations

## What Failed

### Failure 1: Vercel API 404 on all routes
- **What happened:** All 8 Python API handlers used BaseHTTPRequestHandler (incompatible with Vercel serverless) + legacy `builds` key in vercel.json + missing cleanUrls config. Every /api/* route returned 404.
- **Root cause:** Build phase created API files with the wrong handler pattern and Vercel config was never tested against a live deployment.
- **Category:** deployment
- **Prevention:** Automated: Yes — `grep -r "BaseHTTPRequestHandler" api/ && echo "FAIL: Vercel requires ASGI/WSGI handlers"`
- **Principle violated:** No post-deploy smoke test existed in the build pipeline
- **Fix type:** Implementation

### Failure 2: GitHub Actions workflow in wrong directory
- **What happened:** Workflow file was at `03_agents/tests/v17/.github/workflows/` instead of repo root `.github/workflows/`. Scheduled daily email never triggered.
- **Root cause:** Build step placed the workflow relative to the agent directory, not the repo root. No CI validation.
- **Category:** configuration
- **Prevention:** Automated: Yes — `find . -path '*/.github/workflows/*.yml' ! -path './.github/workflows/*.yml' -exec echo "FAIL: {}" \;`
- **Principle violated:** Infrastructure files must be validated against their deployment target
- **Fix type:** Implementation

### Failure 3: Dashboard showed no briefs (Redis fallback missing)
- **What happened:** API read user actions only from Upstash Redis with no fallback to state.json. Without Redis configured on Vercel, all jobs displayed as "new".
- **Root cause:** API assumed Upstash would always be available. No graceful degradation path.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — data-integrity-guardian reviewer prompt: "Verify every external data dependency has an explicit local fallback path."
- **Principle violated:** External service dependencies must have local fallbacks
- **Fix type:** Implementation

### Failure 4: Subagent hit rate limit mid-fix
- **What happened:** First Vercel API fix subagent exhausted Claude rate limit before completing, requiring a second dispatch.
- **Root cause:** External rate limit constraint. Workaround (re-dispatch) was correct but added delay.
- **Category:** subagent-coordination
- **Prevention:** Automated: No — external constraint requiring human judgment
- **Principle violated:** N/A (external constraint)
- **Fix type:** N/A (operational)

### Failure 5: GitHub Actions run failed — settings.local.json missing
- **What happened:** The scheduled GH Actions run at 07:02 UTC on 2026-02-16 failed in 32 seconds. The workflow step `python3 -c "import json; c=json.load(open('.claude/settings.local.json'))..."` threw `FileNotFoundError` because `.claude/settings.local.json` is in `.gitignore` and never committed to the repo.
- **Root cause:** Workflow assumes the file exists in the repo, but it's a local-only file. The workflow must create it during CI setup.
- **Category:** configuration
- **Prevention:** Automated: Yes — `grep -q 'settings.local.json' .gitignore && grep -L 'settings.local.json' .github/workflows/*.yml | xargs -I{} echo "FAIL: {} references gitignored file without creating it"`
- **Principle violated:** CI workflows must not depend on gitignored files without creating them
- **Fix type:** Implementation

### Failure 6: Vercel not auto-deploying from git pushes
- **What happened:** Git pushes to main did not trigger Vercel auto-deploys. Required manual `npx vercel --prod`.
- **Root cause:** Vercel project configuration not set for auto-deploy from main branch.
- **Category:** deployment
- **Prevention:** Automated: Partial — deployment-verifier reviewer prompt: "Confirm Vercel project is configured for automatic deployments from main branch."
- **Principle violated:** Deployment should be automated, not manual
- **Fix type:** Implementation

### Failure 7: RESEND_API_KEY empty in .env
- **What happened:** Even if the scheduled workflow had triggered correctly, the email send would have failed because RESEND_API_KEY was empty.
- **Root cause:** Key not set as GitHub Actions secret. Local .env was empty for this key.
- **Category:** configuration
- **Prevention:** Automated: Partial — deployment-verifier reviewer prompt: "Verify all required secrets are configured in GitHub Actions settings before enabling scheduled workflows."
- **Principle violated:** Secrets must be validated before enabling automated workflows
- **Fix type:** Implementation

### Failure 8: Agent did not read agent memory on startup (HC4 violation)
- **What happened:** No evidence in transcript that `.claude/agent-memory/*/MEMORY.md` files were read during startup.
- **Root cause:** Constraint exists in CLAUDE.md but startup sequence skipped it. V14 regression recurrence.
- **Category:** configuration
- **Prevention:** Automated: Partial — regression-checker reviewer prompt: "Verify agent reads agent-memory files on startup per HC4."
- **Principle violated:** HC4: Read agent memory on startup
- **Fix type:** Implementation

### Failure 9: Inline Python used for state-affecting operations (HC5 violation)
- **What happened:** `python3 -c "import json, os..."` used for dedup score comparison and data extraction from verified JSONs, violating the "never write inline Python for state mutations" constraint.
- **Root cause:** No CLI subcommand exists for cross-role dedup score comparison. Agent improvised with inline Python.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — `grep -n 'python3 -c' session-transcript.txt | grep -v 'manage_state' && echo "FAIL: inline python detected"`
- **Principle violated:** HC5: All state changes must go through scripts/manage_state.py
- **Fix type:** Implementation (add dedup subcommand to manage_state.py)

### Failure 10: Agent asked user to do technical work (CR5 violation)
- **What happened:** Agent told user to "Hard refresh: Cmd+Shift+R", "open URL in browser", and "check Vercel dashboard" — all technical tasks.
- **Root cause:** When encountering the dashboard 404, agent gave debugging suggestions instead of handling them via subagents.
- **Category:** uncategorized
- **Prevention:** Automated: Partial — code-simplicity-reviewer prompt: "Verify agent never directs the user to perform technical actions like refreshing browsers, checking URLs, or inspecting dashboards."
- **Principle violated:** CR5: Never ask user to do technical work
- **Fix type:** Implementation

### Failure 11: Post-render color regex false positives
- **What happened:** Amber/red color check matched substrings in words like "preferred", "credible", "prepared" — 13 false positives.
- **Root cause:** Regex matched color-like strings in HTML body text, not just CSS contexts.
- **Category:** testing
- **Prevention:** Automated: Yes — constrain regex to CSS contexts: `grep -Pn '(color|background).*#(ff|e6|d4|c53)' output/briefs/*.html`
- **Principle violated:** Verification checks must not produce false positives
- **Fix type:** Implementation

## Fixes Needed

### Architectural Fixes
None — all failures are implementation-level issues within the existing architecture.

### Implementation Fixes

1. **Add pre-flight infrastructure validation to startup**
   - What needs to change: Add a startup step that verifies (1) Vercel API routes return 200, (2) GitHub Actions workflows exist at repo root, (3) required secrets are configured
   - Files affected: CLAUDE.md (startup sequence), possibly a scripts/preflight.sh
   - Verification criteria: Running the agent with a broken API endpoint triggers an error message before any search begins

2. **Create manage_state.py dedup subcommand**
   - What needs to change: Add a `dedup` subcommand to manage_state.py that takes verified directories and outputs dedup decisions, eliminating need for inline Python
   - Files affected: scripts/manage_state.py, CLAUDE.md (Step 13)
   - Verification criteria: `python3 scripts/manage_state.py dedup --verified-dir output/verified` produces correct output without inline Python

3. **Fix post-render color regex**
   - What needs to change: Constrain regex to match only within CSS `style=` attributes and `<style>` blocks, not free text
   - Files affected: CLAUDE.md (post-render verification step), or a dedicated scripts/verify_html.py
   - Verification criteria: Running check on briefs HTML with words like "preferred" produces zero false positives

4. **Fix GitHub Actions workflow — create settings.local.json in CI**
   - What needs to change: Add a workflow step that creates `.claude/settings.local.json` with required permissions before the validation step
   - Files affected: .github/workflows/daily-digest.yml
   - Verification criteria: Workflow run passes the settings validation step

5. **Add post-deploy smoke test to CI workflow**
   - What needs to change: After deploy, add a step that curls `/api/jobs` and asserts 200 status
   - Files affected: .github/workflows/daily-digest.yml
   - Verification criteria: Workflow fails fast if API is broken after deploy

6. **Enforce HC4 — agent memory read on startup**
   - What needs to change: Make startup Step 1 explicitly read `.claude/agent-memory/*/MEMORY.md` and log which files were loaded
   - Files affected: CLAUDE.md (startup sequence)
   - Verification criteria: Transcript shows agent-memory files read before any profile check

7. **Remove technical-work suggestions from agent responses**
   - What needs to change: When encountering infrastructure issues, agent must investigate via subagents rather than suggesting user actions like "hard refresh" or "check Vercel dashboard"
   - Files affected: CLAUDE.md (UX rules section)
   - Verification criteria: Agent never outputs instructions like "try Cmd+Shift+R" or "open this URL in your browser"

8. **Enforce Step 22 — scheduled run prompt**
   - What needs to change: After first successful interactive session with email sent, agent must offer to set up scheduled runs
   - Files affected: CLAUDE.md (Step 22 enforcement)
   - Verification criteria: Agent prompts user about scheduled runs at end of first session

## Solutions Extracted
1. **Cross-role deduplication by score comparison**: Detect filename collisions across role-type directories, compare scores, keep highest. Deterministic and correct.
2. **Sentinel-based completion verification**: Each subagent writes `<!-- BRIEF COMPLETE -->` marker; parent greps all expected files before proceeding. Lightweight and reliable.
3. **Explore-then-Task debugging pattern**: Use read-only Explore subagent for diagnosis, then write-capable Task subagent for fix. Preserves parent context while handling complex issues.
4. **Batched dispatch with checkpoints**: Split N subagents into batches of 2, commit between batches. Balances parallelism with rate-limit safety.
5. **Vercel Python API fix**: Migrate from legacy `builds` to `functions` + `rewrites`, add `cleanUrls: true` for extension stripping. Resolves 404s on `/api/endpoint` paths.
6. **State.json fallback for Redis**: When Upstash Redis is unavailable, read action state from state.json. Enables graceful degradation.

## Patterns Identified
1. **Batched Parallel Dispatch with Checkpoint**: Prepare -> dispatch N agents -> wait -> checkpoint -> commit -> next batch. Reusable for any rate-limited multi-query agent.
2. **Cross-Category Deduplication Pipeline**: List -> detect collisions -> compare scores -> keep highest -> log decisions. Reusable for any multi-category search.
3. **Sentinel Check then Quality Gate then Dispatch**: Verify sentinels -> run quality checks -> dispatch next stage. Universal handoff pattern between pipeline stages.
4. **Diagnose-via-Subagent then Fix-via-Subagent**: User reports issue -> Explore subagent diagnoses -> Task subagent fixes -> verify. Used 5 times in this session.
5. **User Selection to Subagent Fan-Out**: Present ranked list -> collect selections -> record state -> fan-out parallel subagents. Reusable for any interactive selection workflow.

## Build Metrics
- Build duration: ~2 days (2026-02-11 to 2026-02-12), exact per-step timing unavailable
- Steps completed: 46/46 across 9 phases
- Verification pass rate: 9/9 phases passed verification
- Regressions (new): 0 during build
- Regressions (repeat): 0 during build
- Review cycles: unavailable
- Note: Timing data unavailable — phased-build step timing not yet enabled

## Handoff Contract
- Architectural fixes: 0
- Implementation fixes: 8 — (1) pre-flight infrastructure validation, (2) manage_state.py dedup subcommand, (3) fix post-render color regex, (4) GH Actions settings.local.json creation, (5) post-deploy smoke test in CI, (6) enforce HC4 agent memory read, (7) remove technical-work suggestions, (8) enforce Step 22 scheduled run prompt
- New constraints: CI workflows must not depend on gitignored files; external service dependencies must have local fallbacks; post-render checks must target CSS contexts only
- Regression tests to include: HC4 startup memory read, HC5 inline Python, CR5 technical work suggestions, Step 22 scheduled run prompt, settings.local.json in CI, API smoke test
- Prevention artifacts written: 3 reviewer prompt additions (data-integrity-guardian, deployment-verifier, code-simplicity-reviewer), 1 regression-checker addition
- Metrics recorded: 1 JSONL entry (V17)

<!-- STAGE COMPLETE: /analyze, 2026-02-16 -->

# Session Analysis: Career Matching Agent (JSA V25)

## Summary
6 wins, 18 failures (2 critical, 7 major, 9 minor), 4 edge cases. Key themes: URL data integrity (generic URLs, false expired claims, aggregator-based verification unreliable), subagent coordination (wrong sentinel paths, JobSpy not run, active_status=None), and recurring constraint violations (agent memory not read, parent inline Python, context budget breaches).

## What Went Well
1. **Parallel search dispatch**: All 5 search channels dispatched in parallel, completing a broad search across 35 company career pages, 10 job boards, niche newsletters, web search discovery, and JobSpy in well-orchestrated manner.
2. **Deep niche source discovery**: After user pushed for thoroughness, agent discovered the Jack & Jill / Jill board (237 roles) as a source and scraped it via Ashby API, yielding 4 new roles.
3. **Honest requirement matching**: Requirement-by-requirement analysis against user's CV produced three-tier verdict (YES/MAYBE/NO) that correctly identified poor fits — Lottie (sales role), Sana (wants McKinsey), ElevenLabs (requires ABM). Changed ranking significantly.
4. **Adaptive re-ranking**: When user clarified AI agent company preference, agent correctly re-prioritized Paraglide AI, Jack & Jill, and Meroka upward.
5. **DOCX brief generation**: Successfully generated application briefs in DOCX format with proper formatting, talking points, and application-specific notes including GitHub repo evidence.
6. **User-prompted iterative improvement**: Agent acknowledged URL errors, audited verified JSONs, and corrected presentations — healthy feedback loops.

## What Failed

### Failure 1: Generic career page URLs presented instead of direct listing URLs
- **What happened:** First presentation used generic company careers page URLs (e.g., `https://elevenlabs.io/careers`) instead of direct job posting URLs. Occurred 3 times across presentations.
- **Root cause:** Parent extracted wrong URL field from verified JSONs. Direct ATS links existed in JSON data but parent used company career page URL when composing presentation tables.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — schema validation that enforces `url` must be a direct ATS link (Greenhouse, Ashby, Lever, Workable pattern).
- **Principle violated:** CR2 (never fabricate data — presenting wrong URL is a form of data integrity failure)
- **Fix type:** Implementation

### Failure 2: .done sentinel files written to wrong directory
- **What happened:** Search-verify subagents wrote `.done` files to `.channels/` at project root instead of `output/.channels/`, causing channel verification gate to fail. Required 3 retries and parent intervention.
- **Root cause:** Subagent instructions don't hardcode the output path for `.done` files.
- **Category:** subagent-coordination
- **Prevention:** Automated: Yes — post-dispatch check: `ls output/.channels/*.done | wc -l` should match dispatched channel count.
- **Principle violated:** V24 regression (sentinel write must be mandatory final step in search-verify agent — 4th occurrence)
- **Fix type:** Implementation

### Failure 3: JobSpy aggregator channel did not run the actual script
- **What happened:** JobSpy channel subagent used WebSearch/WebFetch instead of running `scripts/jobspy_search.py`. User caught this: "also, did you use jobscan?"
- **Root cause:** No hard constraint in JobSpy channel agent mandating script execution.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — regression-checker should verify JobSpy aggregator channel explicitly runs `scripts/jobspy_search.py`.
- **Principle violated:** Channel definition lacks enforcement
- **Fix type:** Implementation

### Failure 4: False expired/removal claims — 7 of 8 recommendations wrong
- **What happened:** Agent recommended removing 8 jobs as expired/stale without visiting URLs. Upon user-requested verification, 7 of 8 were actually still live (Synthesia re-listed, Emma valid April 19, Crush valid May 17, etc.).
- **Root cause:** Agent inferred "stale from prior runs" without URL verification. No verification-before-removal gate exists.
- **Category:** data-integrity
- **Prevention:** Automated: No — requires human judgment. Regression: "Never recommend removing a job without visiting the URL first."
- **Principle violated:** CR1 (never present job without full verification — removal recommendations are a form of presentation)
- **Fix type:** Architectural — add mandatory URL verification step before any removal recommendation

### Failure 5: Expired jobs persisting in ranked lists across multiple presentations
- **What happened:** Synthesia, Letty, Scandit, and others marked expired still appeared in active rankings. Re-verification subagent set `active_status=None` instead of `"expired"`.
- **Root cause:** No schema validation enforces non-null `active_status` after re-verification.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — schema check for null `active_status` after any verification run.
- **Principle violated:** V23 regression (schema inconsistency cascade)
- **Fix type:** Implementation

### Failure 6: Aggregator-based liveness verification unreliable — Linda AI false positive
- **What happened:** Playwright reported Linda AI as "LIVE" (seeing "Apply now" on StudySmarter aggregator page) when listing was actually expired. User caught it immediately.
- **Root cause:** Checking if an aggregator page loads is not equivalent to confirming listing is open at source. No verification strategy distinguishes aggregator from source.
- **Category:** data-integrity
- **Prevention:** Automated: No — aggregator pages can't be reliably distinguished from source pages by static analysis.
- **Principle violated:** No explicit constraint existed — gap in verification design
- **Fix type:** Architectural — redesign liveness verification to always check company's own ATS first

### Failure 7: Agent memory not read on startup (HC4/S2)
- **What happened:** No evidence of reading `.claude/agent-memory/*/MEMORY.md` at startup.
- **Root cause:** Multi-version recurring regression (V14/V17/V19/V24 — 5th occurrence).
- **Category:** configuration
- **Prevention:** Automated: Yes — preflight check for memory read confirmation.
- **Principle violated:** HC4 (read agent memory on startup)
- **Fix type:** Implementation

### Failure 8: Parent executed Python inline (HC5 violation)
- **What happened:** Parent ran `cat output/_delta.json | python3 -c "import json,sys..."` inline and directly read/modified verified JSONs after subagent truncation failures.
- **Root cause:** Subagent returned truncated output; parent resorted to inline Python rather than re-dispatching with larger budget.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — regression-checker should flag any parent-context Python execution.
- **Principle violated:** HC5 (never execute Python in parent except allowed scripts), Context Budget rules
- **Fix type:** Implementation

### Failure 9: Foreground/background contradiction in CLAUDE.md
- **What happened:** Core Rules mandate "All dispatches MUST be foreground-only" while Startup S6 says "All subagents background: true". Agent followed background directive.
- **Root cause:** Contradictory directives added across V23 and V25 builds.
- **Category:** configuration
- **Prevention:** Automated: Yes — grep for contradictory "foreground-only" and "background: true" in CLAUDE.md.
- **Principle violated:** Self-contradictory CLAUDE.md
- **Fix type:** Implementation

### Failure 10: Jack & Jill wrong listing data (wrong Ashby board slug)
- **What happened:** Search found old/incorrect listing via wrong board slug (`jack-and-jill` vs correct `jack-jill-external-ats`). Showed GBP 36-60K salary when actual listing is GBP 100-180K.
- **Root cause:** Multiple Ashby boards exist for same company; search agent used first match without cross-referencing.
- **Category:** data-integrity
- **Prevention:** Automated: No — requires domain knowledge to distinguish company board slugs.
- **Principle violated:** CR2 (never fabricate data)
- **Fix type:** Implementation

### Failure 11: Dedup `--role-types` flag parsing failure
- **What happened:** `manage_state.py dedup` showed "0 input files" when called with `--role-types` flag. Required fallback call without flag.
- **Root cause:** Argument parsing bug in manage_state.py.
- **Category:** configuration
- **Prevention:** Automated: Yes — test dedup with --role-types flag in unit tests.
- **Principle violated:** Testing gap
- **Fix type:** Implementation

### Failure 12: Preflight safety bounds too aggressive for multi-week gaps
- **What happened:** After 17-day gap, safety bound (50% threshold) blocked preflight on 3 of 4 role types. Required `--no-safety-bound` override.
- **Root cause:** Safety bounds calibrated for daily runs; no graceful handling for long gaps.
- **Category:** configuration
- **Prevention:** Automated: Partial — preflight should detect gap duration and auto-adjust threshold.
- **Principle violated:** V24 regression (first-run detection)
- **Fix type:** Implementation

### Failure 13: Write to session-state.md failed on first attempt
- **What happened:** First `Write(output/session-state.md)` returned "Error writing file" — had to retry after Read.
- **Root cause:** File didn't exist yet; Write tool requires Read-before-Write for existing files.
- **Category:** configuration
- **Prevention:** Automated: Yes — ensure session-state.md exists in preflight (touch if missing).
- **Principle violated:** V24 regression (session-state.md write after every search batch)
- **Fix type:** Implementation

### Failure 14: Subagent output truncation forcing parent fallback
- **What happened:** Haiku subagent dispatched to "Get all job URLs and scores" truncated its output, requiring second dispatch and eventually parent inline Python.
- **Root cause:** Haiku token budget insufficient for large verified JSON reads.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — use Sonnet for data-heavy reads, not Haiku.
- **Principle violated:** HC5 (parent fallback violates context budget)
- **Fix type:** Implementation

### Failure 15: SyntaxWarning spam from manage_state.py
- **What happened:** `SyntaxWarning: invalid escape sequence '\d'` on every `manage_state.py` invocation (line 1408), polluting output throughout session.
- **Root cause:** Raw regex string not using r-prefix.
- **Category:** configuration
- **Prevention:** Automated: Yes — `python3 -W error scripts/manage_state.py --help 2>&1 | grep SyntaxWarning`
- **Principle violated:** Code quality
- **Fix type:** Implementation

### Failure 16: Playwright browser crash during batch verification
- **What happened:** Playwright session expired/crashed returning "Failed to launch the browser process" during batch URL verification.
- **Root cause:** Long-running Playwright session exceeded resource limits.
- **Category:** performance
- **Prevention:** Automated: Partial — implement browser restart logic between batches.
- **Principle violated:** Performance budget
- **Fix type:** Implementation

### Failure 17: Jill board roles presented without actual URLs
- **What happened:** nPlan, Godiligent.ai, Marloo roles from Jill board presented with "via Jill board" instead of clickable URLs.
- **Root cause:** Ashby API scrape extracted role data but not direct application URLs.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — schema validation should reject entries without valid URL.
- **Principle violated:** CR2 (presentation without verifiable data)
- **Fix type:** Implementation

### Failure 18: Specter Labs URL garbled/duplicated
- **What happened:** URL appeared with broken prefix (missing `h`) and duplicated inline.
- **Root cause:** String handling error during presentation formatting.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — URL format validation before presentation.
- **Principle violated:** Data integrity
- **Fix type:** Implementation

## Fixes Needed

### Architectural Fixes

#### AF1: Mandatory URL verification before removal recommendations
- **What needs to change:** Add a verification gate that requires visiting the actual URL before any job can be recommended for removal. Current behavior allows "stale from prior runs" inference without checking.
- **Files affected:** CLAUDE.md (new hard constraint), search-verify agent definition, manage_state.py (new `verify-before-archive` subcommand)
- **Verification criteria:** Agent cannot recommend removal without proof of URL returning 404/expired at source ATS

#### AF2: Source-first liveness verification strategy
- **What needs to change:** Replace current "check if page loads" approach with structured verification: (1) find company's actual ATS URL, (2) verify at source, (3) use aggregator only as fallback with "unverified liveness" flag. Current approach trusts aggregator pages that show "Apply" for dead listings.
- **Files affected:** CLAUDE.md (new verification protocol), search-verify agent definition, verified JSON schema (add `source_url` vs `aggregator_url` distinction)
- **Verification criteria:** No aggregator URL accepted as primary verification source; all liveness checks hit company's own ATS first

### Implementation Fixes

#### IF1: Schema validation for URL type and active_status
- **What needs to change:** Add schema validation that (a) `url` must match ATS patterns (greenhouse.io, ashbyhq.com, lever.co, workable.com, rippling.com, or company-specific), not generic career pages, and (b) `active_status` must be non-null after any verification.
- **Files affected:** scripts/manage_state.py (schema validation), tests/
- **Verification criteria:** Schema validation rejects generic career page URLs and null active_status

#### IF2: Hardcode .done sentinel path in subagent dispatch
- **What needs to change:** Subagent dispatch variables must include explicit `.done` file path: `output/.channels/{channel_name}.done`. Not left to subagent inference.
- **Files affected:** CLAUDE.md (dispatch variable checklist), search-verify agent definitions
- **Verification criteria:** Gate-check passes on first attempt after search dispatch

#### IF3: JobSpy channel hard constraint
- **What needs to change:** JobSpy aggregator channel agent must have hard constraint: "MUST run `scripts/jobspy_search.py` — WebSearch/WebFetch fallback is PROHIBITED."
- **Files affected:** CLAUDE.md (channel definitions or references)
- **Verification criteria:** JobSpy channel always runs the script

#### IF4: Resolve foreground/background CLAUDE.md contradiction
- **What needs to change:** Remove contradictory directives. Either enforce foreground-only (safer) or background (faster). Given 8 versions of background permission failures, mandate foreground-only.
- **Files affected:** CLAUDE.md (Core Rules + Startup S6)
- **Verification criteria:** No contradictory foreground/background directives in CLAUDE.md

#### IF5: Agent memory read enforcement
- **What needs to change:** Add memory read as explicit preflight.sh check or as first step in startup sequence with verification. 5th occurrence of this regression.
- **Files affected:** scripts/preflight.sh, CLAUDE.md
- **Verification criteria:** preflight.sh fails if agent memory not read

#### IF6: Parent inline Python prevention
- **What needs to change:** On subagent truncation, re-dispatch with Sonnet tier and explicit token budget rather than falling back to parent inline Python.
- **Files affected:** CLAUDE.md (recovery protocol), dispatch variable template
- **Verification criteria:** Zero parent-context Python execution in session

#### IF7: Fix SyntaxWarning in manage_state.py
- **What needs to change:** Line 1408 of manage_state.py: change `'\d'` to `r'\d'` (raw string prefix).
- **Files affected:** scripts/manage_state.py
- **Verification criteria:** `python3 -W error scripts/manage_state.py --help` produces no SyntaxWarning

#### IF8: Dedup --role-types flag parsing fix
- **What needs to change:** Fix argument parsing in manage_state.py dedup subcommand to correctly handle --role-types flag.
- **Files affected:** scripts/manage_state.py, tests/
- **Verification criteria:** `manage_state.py dedup --role-types founder-s-associate` processes correct files

#### IF9: Safety bound auto-adjustment for long gaps
- **What needs to change:** Preflight should detect gap between last_run_date and today. If gap > 7 days, auto-adjust safety bound threshold from 50% to 90% or skip bounds entirely with logged warning.
- **Files affected:** scripts/preflight.sh or manage_state.py dedup logic
- **Verification criteria:** 17-day gap doesn't trigger safety bound abort

#### IF10: Ensure session-state.md exists in preflight
- **What needs to change:** Preflight should `touch output/session-state.md` if it doesn't exist, preventing Write tool failure on first attempt.
- **Files affected:** scripts/preflight.sh
- **Verification criteria:** First Write to session-state.md succeeds without prior Read

#### IF11: Subagent tier enforcement for data-heavy reads
- **What needs to change:** Data extraction from large JSON sets must use Sonnet tier, not Haiku. Add to dispatch guidelines.
- **Files affected:** CLAUDE.md (dispatch guidelines)
- **Verification criteria:** No Haiku subagents dispatched for multi-file JSON reads

#### IF12: Pre-presentation URL and data validation gate
- **What needs to change:** Before any results presentation, run a validation pass that checks all URLs are direct ATS links, all active_status values are non-null, and all expired jobs are excluded.
- **Files affected:** CLAUDE.md (presentation protocol), manage_state.py (new `validate-presentation` subcommand)
- **Verification criteria:** Zero presentations with generic career page URLs or expired jobs

## Solutions Extracted

### S1: Safety bound override for long gaps
- **Problem:** Preflight dedup hit safety bounds after 17-day gap.
- **Solution:** `python3 scripts/manage_state.py dedup --no-safety-bound` after confirming gap is intentional.
- **Category:** configuration
- **Transferable:** Yes — any agent with safety bounds should document override procedures.

### S2: Gate-check diagnosis via source reading
- **Problem:** Channel verification gate failed due to wrong .done file paths.
- **Solution:** Read `manage_state.py` source to find exact path expectations (`output/.channels/`) rather than delegating troubleshooting to subagents (3 failed retries).
- **Category:** subagent-coordination
- **Transferable:** Yes — when gate-checks fail, read the verification script source for exact path expectations.

### S3: Ashby API for aggregated job boards
- **Problem:** User-discovered job board (Jill board, 237 roles) missed by standard search.
- **Solution:** Recognized Ashby board slug pattern and used `jobs.ashbyhq.com/{slug}` API endpoint to scrape all listings, then filtered for qualifying roles.
- **Category:** configuration
- **Transferable:** Yes — Ashby, Greenhouse, Lever boards have public APIs for scraping.

### S4: Requirement-by-requirement CV matching
- **Problem:** Score-based ranking didn't account for hard requirement mismatches.
- **Solution:** Dispatched Sonnet subagent with CV + job listing for requirement-by-requirement comparison producing YES/MAYBE/NO verdicts. Caught 14 false positives.
- **Category:** data-integrity
- **Transferable:** Yes — requirement matching against actual CV is more valuable than score-based ranking.

### S5: DOCX generation with global npm module
- **Problem:** `docx` npm module not installed for brief generation.
- **Solution:** `npm install -g docx` + `NODE_PATH=$(npm root -g)` avoids local package.json.
- **Category:** deployment
- **Transferable:** Yes — global npm install with NODE_PATH for non-Node projects.

### S6: GitHub repos as application evidence
- **Problem:** User's CV needed differentiation for AI agent roles.
- **Solution:** Include competitor-intel, growth-experiments, career-matching GitHub repos as concrete evidence of "I build AI agents" claim in every brief.
- **Category:** data-integrity
- **Transferable:** Yes — portfolio evidence from GitHub should be standard in application briefs.

### S7: CV-aware prioritization (apply-as-is vs needs-reframing)
- **Problem:** Application priority didn't factor in CV alignment.
- **Solution:** Prioritize roles where CV matches as-is (FA roles for FA CV) over roles requiring reframing (marketing roles), alongside score and deadline.
- **Category:** data-integrity
- **Transferable:** Yes — apply-as-is vs needs-reframing should be a standard ranking factor.

## Patterns Identified

### P1: Startup-Preflight-Initialize
- **Steps:** (1) Check digest status, (2) Git pull, (3) Run preflight.sh, (4) Capture date, (5) Read context, (6) Quick change check, (7) Clear checkpoints, (8) Init session-state.md
- **Appeared in:** Both search runs in transcript
- **Skill candidate:** Yes
- **Generalization:** Any multi-run agent with persistent state needs this 8-step startup sequence.

### P2: Parallel-Dispatch-Then-Gate
- **Steps:** (1) Dispatch N search subagents in parallel, (2) Collect results with progress reporting, (3) Run gate-checks in parallel, (4) Diagnose failures, (5) Re-run failed gates
- **Appeared in:** Both search rounds (5 channels each time)
- **Skill candidate:** Yes
- **Generalization:** Fan-out/fan-in orchestration with structural validation. Applicable to any multi-source data collection agent.

### P3: Present-Audit-Re-verify-Re-present
- **Steps:** (1) Present results, (2) User identifies issue, (3) Dispatch audit subagent, (4) Dispatch remediation, (5) Commit fixes, (6) Re-present
- **Appeared in:** 3 times in single session (wrong URLs, expired jobs, more expired jobs)
- **Skill candidate:** Yes — but should be prevented rather than repeated
- **Generalization:** User-feedback-driven quality loop. Occurred 3 times suggesting initial verification was insufficient.

### P4: Escalating-URL-Verification
- **Steps:** (1) WebFetch check, (2) User reports false positive, (3) Find direct ATS URLs, (4) Playwright verification, (5) User reports another false positive, (6) Source-of-truth verification
- **Appeared in:** Entire URL verification saga spanning 3 escalation rounds
- **Skill candidate:** Yes
- **Generalization:** Any agent verifying external resources needs an escalation ladder from automated to human-in-the-loop to source verification.

### P5: Iterative-Search-Deepening
- **Steps:** (1) Broad search, (2) User requests deeper, (3) Targeted search with refined criteria, (4) User requests more, (5) Specialized searches (JobSpy, ATS-wide), (6) Cross-reference all rounds
- **Appeared in:** 3 search depth levels in this session
- **Skill candidate:** No — requires human judgment on when to deepen
- **Generalization:** Progressive search deepening driven by user feedback.

## Build Metrics
- **Build duration (total):** Unavailable (no timestamps)
- **Phase durations:** Unavailable
- **Steps completed:** 15 / 15 (all steps across 3 phases)
- **Verification pass rate:** 15 / 15 (100% — all passed first attempt)
- **Regression count (new):** 0 (build phase)
- **Regression count (repeat):** 0 (build phase)
- **Review cycle count:** 3 rounds (4/4 reviewers APPROVED on Round 3)

**Session metrics (from transcript analysis):**
- ~25-30 subagent dispatches
- 18 failures identified (2 critical, 7 major, 9 minor)
- 12 constraint violations (HC4, HC5, CR2, CR12, S2, S7, S10, Context Budget ×3, foreground/background contradiction, post-dispatch verification)
- 4 edge cases (17-day gap, aggregator vs source verification, JS-rendered pages, hidden application instructions)

## Handoff Contract
- Architectural fixes: 2 — (AF1) mandatory URL verification before removal, (AF2) source-first liveness verification strategy
- Implementation fixes: 12 — (IF1) schema validation for URL/active_status, (IF2) hardcode .done sentinel path, (IF3) JobSpy hard constraint, (IF4) resolve fg/bg contradiction, (IF5) agent memory read enforcement, (IF6) parent inline Python prevention, (IF7) fix SyntaxWarning, (IF8) dedup --role-types fix, (IF9) safety bound auto-adjustment, (IF10) ensure session-state.md in preflight, (IF11) subagent tier for data reads, (IF12) pre-presentation validation gate
- New constraints: verify-before-removal gate, source-first verification protocol, Ashby API as search source
- Regression tests to include: URL type validation, active_status non-null enforcement, .done file path verification, JobSpy script execution
- Prevention artifacts written: 4 reviewer prompt additions (data-integrity-guardian, regression-checker ×2, architecture-strategist), 0 checks.sh entries (deferred to V2)
- Metrics recorded: 15/15 steps, 100% verification pass rate, 3 review cycles, 18 session failures

<!-- STAGE COMPLETE: /analyze, 2026-03-23 -->

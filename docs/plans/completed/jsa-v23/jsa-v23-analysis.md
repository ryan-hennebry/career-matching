# Session Analysis: JSA V23

## Summary
6 wins, 20 failures (5 critical, 9 major, 6 minor), 3 edge cases. Single root cause (inconsistent verified JSON schema) cascaded into 4 downstream failures. Background subagent permissions remain broken since V20 — 8th version without fix.

## What Went Well
1. **5-channel search architecture dispatched**: All 5 channels (direct career pages, industry job boards, JobSpy, niche newsletters, web search discovery) completed and produced 62 unique new jobs — broadest search coverage to date.
2. **User context update handled cleanly**: When user broadened from "AI agent companies" to "AI companies broadly" and added priority roles (Founder's Associate, Marketing Associate), agent updated all 8 context.md sections (Target, Industries, Sources, JobSpy queries, newsletter queries, web search queries, direct career pages) in one pass.
3. **Dashboard fix deployed in-session**: `/api/jobs` 500 error diagnosed (score schema mismatch), fixed with `_extract_score()`, committed, pushed, redeployed, verified — all within one session.
4. **Email delivery succeeded**: Digest HTML generated and sent via Resend API on first properly-formed attempt.
5. **Self-audit caught 3 stale artifacts**: User-prompted end-of-session audit found stale session-state.md, missing digest `_status.json` fields, and bloated settings.local.json — all fixed.
6. **Model tier escalation worked**: Escalating JobSpy re-verification from Haiku to Sonnet correctly filtered 131 garbage results down to 43 properly scored jobs.

## What Failed

### Failure 1: Background subagent permissions denied (V20 regression — 8th occurrence)
- **What happened:** All background-dispatched agents (gate-check x3, search-verify x5) had Bash/WebFetch/WebSearch denied despite blanket `settings.local.json` permissions. Wasted ~20 min on escalation attempts.
- **Root cause:** Claude Code background dispatch does not inherit `settings.local.json` permissions. This is a platform limitation, not a configuration issue.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — deployment-verifier should enforce foreground-only dispatch until platform fix confirmed.
- **Principle violated:** V18/V20/V21/V22 regressions all documented this. CLAUDE.md says "background: true" but it doesn't work.
- **Fix type:** Architectural — remove background dispatch from CLAUDE.md entirely, mandate foreground-only.

### Failure 2: Inconsistent verified JSON score schemas across channels
- **What happened:** JobSpy used `score` (int), direct-career-pages used `scoring.total_score`, industry-job-boards used `score` (dict with `total`), founders-associate used `score_breakdown.total`. Caused cascading failures in 4 downstream consumers.
- **Root cause:** No JSON Schema validation gate between search-verify output and downstream consumers. Each search agent independently chose its score field structure.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — `find output/verified -name "*.json" -exec python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert isinstance(d.get('score'), (int,float))" {} \;`
- **Principle violated:** No enforced output schema contract for search-verify agents.
- **Fix type:** Architectural — enforce a canonical verified JSON schema with validation gate.

### Failure 3: Haiku cannot apply profile-matching scoring
- **What happened:** JobSpy Haiku agent scored "Pret a Manger barista" and "Experian Data Scientist" at 95-100. Re-verification with Haiku still kept 131/140 with inflated scores. Required Sonnet to properly filter to 43.
- **Root cause:** Haiku lacks the reasoning depth to evaluate role-profile fit against a rubric. It scores literally (keyword match) not semantically (actual relevance).
- **Category:** data-integrity
- **Prevention:** Automated: Partial — data-integrity-guardian should verify model tier assignment for scoring tasks.
- **Principle violated:** HC1 tier assignment — scoring is a judgment task, not mechanical.
- **Fix type:** Implementation — reassign scoring step to Sonnet tier in search-verify agent definition.

### Failure 4: Parent violated context budget rules
- **What happened:** Parent executed WebFetch (4 URLs), WebSearch (2 queries), read verified JSONs directly, and ran inline Python (`python3 -c`) — all violations of context budget constraints.
- **Root cause:** When subagents failed (permissions, newsletter miss), parent used escape hatches instead of re-dispatching with fixes.
- **Category:** subagent-coordination
- **Prevention:** Automated: No — requires human judgment (tradeoff between user experience and architecture rules).
- **Principle violated:** HC5 (no Python in parent), Context Budget rules (no WebFetch/WebSearch in parent, no escape hatch).
- **Fix type:** Implementation — strengthen orchestration.md to include explicit "on subagent failure" recovery protocol that re-dispatches, not escapes.

### Failure 5: Session-state.md never updated after channel completion (9th occurrence)
- **What happened:** Written once at startup, never updated after channels completed. Still showed 4 channels as "pending" after all 5 finished. Only caught when user asked "anything else you missed?"
- **Root cause:** No automated gate enforces session-state.md update after each channel. Relies on agent memory, which consistently fails.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — `grep -c "pending" output/session-state.md` post-channel.
- **Principle violated:** CR10, V14/V16/V18/V19/V21/V22 regressions.
- **Fix type:** Implementation — add mandatory gate-check after each channel that verifies session-state.md reflects completion.

### Failure 6: manage_state.py dedup archived ALL 63 jobs
- **What happened:** `dedup` ran on a fresh run with no prior-run data and archived 100% of verified files. Required `git checkout HEAD -- output/verified/` to restore.
- **Root cause:** Dedup logic has no safety bounds — doesn't check if it's archiving >50% of files (which would indicate a bug, not duplicates).
- **Category:** data-integrity
- **Prevention:** Automated: Yes — `dedup --dry-run` + assert archived < 50% of total.
- **Principle violated:** V22 MEMORY requirement for context-aware dedup.
- **Fix type:** Implementation — add safety bound: if dedup would archive >50%, abort and warn.

### Failure 7: Niche newsletter agent missed relevant roles
- **What happened:** Newsletter agent checked Early & Exec but incorrectly filtered ALL roles as "exec/leadership," missing Mayday FA, Tracebit FA, JigsawStack GTM.
- **Root cause:** Agent's title filtering conflated "Founder's Associate" with executive roles. Too aggressive exclusion.
- **Category:** data-integrity
- **Prevention:** Automated: Partial — regression-checker should verify title exclusion distinguishes FA from exec.
- **Principle violated:** CR1 (never miss valid roles through over-filtering).
- **Fix type:** Implementation — add positive examples to scoring rubric: "Founder's Associate" and "Founding [X]" are mid-level, not executive.

### Failure 8: Digest job key builder missed high-scoring jobs
- **What happened:** ElevenLabs DevRel (94), ElevenLabs B2B Growth (89), Morpho FA (88), Mayday FA (72) missing from digest because builder only checked top-level `score` field, not `scoring.total_score` or `score_breakdown.total`.
- **Root cause:** Same as Failure 2 — inconsistent score schema. Digest builder was a downstream victim.
- **Category:** data-integrity
- **Prevention:** Same as Failure 2 — schema validation gate prevents this cascade.
- **Principle violated:** Same as Failure 2.
- **Fix type:** Implementation — will be fixed by Failure 2's architectural fix (canonical schema).

### Failure 9: manage_state.py sync crashed on KeyError
- **What happened:** `sync` command crashed because some verified JSONs had `scoring.total_score` instead of top-level `score`.
- **Root cause:** Same as Failure 2 — schema inconsistency cascade.
- **Category:** data-integrity
- **Prevention:** Same as Failure 2.
- **Principle violated:** Same as Failure 2.
- **Fix type:** Implementation — `_extract_score()` hotfix applied in-session; canonical schema prevents recurrence.

### Failure 10: Dashboard /api/jobs returned 500
- **What happened:** API endpoint hit same score schema mismatch, returned "server error," frontend showed "No jobs found."
- **Root cause:** Same as Failure 2 — schema inconsistency cascade.
- **Category:** deployment
- **Prevention:** Same as Failure 2.
- **Principle violated:** Same as Failure 2.
- **Fix type:** Implementation — `_extract_score()` hotfix applied in-session.

### Failure 11: Preflight failed on missing permissions
- **What happened:** Preflight script failed because `settings.local.json` only had one Bash command permitted, missing Read/Write/Glob/Grep.
- **Root cause:** Minimal permissions in committed settings template. No comprehensive default.
- **Category:** configuration
- **Prevention:** Automated: Yes — validate minimum permission set in preflight.
- **Principle violated:** V21 regression — settings.local.json must be comprehensive before first session.
- **Fix type:** Implementation — ship comprehensive default permissions in settings.local.json template.

### Failure 12: Preflight failed on missing orchestration checkpoint + agent frontmatter
- **What happened:** Second preflight run found orchestration.md missing checkpoint clear step and gate-check.md missing `background: true`.
- **Root cause:** Build output didn't match preflight's structural checks.
- **Category:** configuration
- **Prevention:** Automated: Yes — preflight already catches this; the build should have been validated.
- **Principle violated:** Build should have run preflight before declaring complete.
- **Fix type:** Implementation — add preflight as final build step.

### Failure 13: Incremental commit+push skipped after search (8th occurrence)
- **What happened:** No commit after search phase; single commit only after full delivery.
- **Root cause:** Agent consistently forgets HC7. No automated gate enforces it.
- **Category:** subagent-coordination
- **Prevention:** Automated: Yes — post-search gate: `git status --porcelain | wc -l` must be 0 (all committed).
- **Principle violated:** HC7, V14/V16/V18/V19/V20/V21/V22 all documented this.
- **Fix type:** Implementation — add mandatory commit gate in orchestration Phase 1 exit.

### Failure 14: HC10 — subagent dispatches missing mandatory variables
- **What happened:** working_dir, output_directory, dashboard_url never passed to any subagent dispatch.
- **Root cause:** Orchestration dispatch templates don't enforce these variables.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — architecture-strategist should check dispatch variable completeness.
- **Principle violated:** HC10.
- **Fix type:** Implementation — add mandatory variable checklist to dispatch template in orchestration.md.

### Failure 15: Auto-retry protocol violated — gate-check dispatched 3 times
- **What happened:** Gate-check attempted 3 times (2 retries) before parent took over. Protocol allows max 1 retry.
- **Root cause:** Permission failures triggered retry instinct rather than strategy change.
- **Category:** subagent-coordination
- **Prevention:** Automated: Partial — regression-checker should verify retry counts.
- **Principle violated:** Auto-retry protocol max 1 retry.
- **Fix type:** Implementation — add retry counter to orchestration dispatch logic.

### Failure 16: Niche newsletter subagent took 3h 16m
- **What happened:** Single subagent for newsletter channel took over 3 hours.
- **Root cause:** Likely excessive research scope or rate limiting. No time budget enforced.
- **Category:** performance
- **Prevention:** Automated: Partial — performance-oracle should enforce time budgets on subagent dispatches.
- **Principle violated:** V20 regression — search-verify must complete in <2 minutes.
- **Fix type:** Implementation — enforce hard time budget in subagent dispatch with checkpoint-and-return.

### Failure 17: send_email.py called with wrong flag
- **What happened:** Used `--html` instead of correct `--body-file` flag.
- **Root cause:** V21 regression documented this exact issue. Agent didn't recall.
- **Category:** configuration
- **Prevention:** Automated: Yes — `python3 scripts/send_email.py --help | grep body-file`.
- **Principle violated:** V21 regression — orchestration references must match actual CLI interface.
- **Fix type:** Implementation — ensure orchestration.md references correct flag.

### Failure 18: list-active-role-types produced full-sentence slugs
- **What happened:** Parsed context.md literally, producing slugs like `any-role-matching-user-s-skills-and-experience-level-no-title-restriction-beyond-exclusions`.
- **Root cause:** manage_state.py parsing logic too literal for free-form bullet text.
- **Category:** data-integrity
- **Prevention:** Automated: Yes — validate slug format: `[a-z0-9-]{3,40}`.
- **Principle violated:** Script should produce clean slugs from structured input.
- **Fix type:** Implementation — improve slug extraction to use short labels, not full sentences.

### Failure 19: settings.local.json bloated to 34+ entries
- **What happened:** Subagent permission requests added 24 domain-specific and command-specific entries including entire JSON blobs.
- **Root cause:** No cleanup/compaction of settings.local.json after subagent dispatches.
- **Category:** configuration
- **Prevention:** Automated: Yes — `python3 -c "import json; d=json.load(open('.claude/settings.local.json')); exit(1) if len(d['permissions']['allow']) > 15 else exit(0)"`.
- **Principle violated:** HC8 — settings modifications should be minimal and clean.
- **Fix type:** Implementation — add post-run settings cleanup step to orchestration.

### Failure 20: UX — two questions asked in one message
- **What happened:** "Two questions before I proceed" — asked about Lead exclusion AND brief selection simultaneously.
- **Root cause:** Agent bundled questions for efficiency, violating CR4.
- **Category:** uncategorized
- **Prevention:** Automated: No — requires human judgment.
- **Principle violated:** CR4 — must ask one question at a time.
- **Fix type:** Implementation — reinforce in orchestration.md UX section.

## Fixes Needed

### Architectural Fixes

#### A1: Remove background dispatch — mandate foreground-only
- **What needs to change:** Remove all `background: true` from agent frontmatter and CLAUDE.md dispatch instructions. Replace with foreground-only dispatch. Remove the "background dispatch" pattern entirely until Claude Code platform fixes permission inheritance.
- **Files affected:** CLAUDE.md, all `.claude/agents/*.md` frontmatter, `references/orchestration.md`
- **Verification criteria:** Zero `background: true` in any agent file. All dispatches use foreground mode. Preflight checks for no background dispatch references.

#### A2: Enforce canonical verified JSON schema with validation gate
- **What needs to change:** Define a single canonical schema for verified JSONs with `score` as a mandatory top-level integer. Add a validation gate (script or preflight check) that runs after every search-verify agent writes output. Reject non-conforming files immediately.
- **Files affected:** `references/scoring-algorithm.md` or new `references/verified-schema.json`, `scripts/manage_state.py` (add `validate-schema` subcommand), `scripts/preflight.sh` (add post-search schema check), all search-verify agent prompts
- **Verification criteria:** All verified JSONs have top-level `score` as int/float. `manage_state.py validate-schema` passes on all files. Dashboard `/api/jobs` returns correct scores without `_extract_score()` fallback chain.

### Implementation Fixes

#### I1: Reassign scoring to Sonnet tier
- **What needs to change:** Search-verify agent scoring step must use Sonnet, not Haiku. Haiku can fetch/extract job data, but profile-matching scoring requires Sonnet-level judgment.
- **Files affected:** `.claude/agents/search-verify.md` (model tier), `references/orchestration.md` (tier documentation)
- **Verification criteria:** search-verify agent frontmatter specifies Sonnet for scoring. No Haiku-scored results with >90 score for clearly irrelevant roles.

#### I2: Add mandatory session-state.md update gate after each channel
- **What needs to change:** After each search channel completes, a gate-check verifies session-state.md has been updated to reflect the channel's completion. Block next channel dispatch until gate passes.
- **Files affected:** `references/orchestration.md` (Phase 1 post-channel gates), `.claude/agents/gate-check.md` (add session-state verification)
- **Verification criteria:** After any channel completes, `grep "pending" output/session-state.md` returns 0 for that channel.

#### I3: Add safety bound to dedup
- **What needs to change:** `manage_state.py dedup` must abort if it would archive >50% of total verified files. Add `--dry-run` flag that reports what would be archived without acting.
- **Files affected:** `scripts/manage_state.py`
- **Verification criteria:** `dedup --dry-run` on a fresh run with no prior data reports 0 archives. Running dedup on 63 unique files does not archive any.

#### I4: Add positive examples to scoring rubric for title filtering
- **What needs to change:** Scoring rubric must explicitly list "Founder's Associate," "Founding [X]," and "Associate" roles as mid-level (included), distinguished from "Head/VP/Chief/Director" (excluded).
- **Files affected:** `references/scoring-algorithm.md`, search-verify agent prompt templates
- **Verification criteria:** Newsletter agent correctly includes "Founder's Associate" roles from Early & Exec. No false-positive exclusion of associate-level roles.

#### I5: Enforce incremental commit+push gate after search phase
- **What needs to change:** Add a mandatory commit gate at orchestration Phase 1 exit. `git status --porcelain` in `output/verified/` must return empty (all committed and pushed) before Phase 2 begins.
- **Files affected:** `references/orchestration.md` (Phase 1 exit gate)
- **Verification criteria:** After search phase, `git status --porcelain output/verified/` returns empty.

#### I6: Ship comprehensive default settings.local.json
- **What needs to change:** The settings.local.json template must include all blanket permissions (Read, Write, Glob, Grep, Bash, WebFetch, WebSearch, Task, Edit) so preflight never fails on permissions.
- **Files affected:** `.claude/settings.local.json` template or documentation
- **Verification criteria:** Fresh session with template settings.local.json passes preflight on first attempt.

#### I7: Add mandatory dispatch variables to orchestration template
- **What needs to change:** Every subagent dispatch in orchestration.md must include `working_dir`, `output_directory`, `dashboard_url` as mandatory variables. Add a dispatch checklist that gate-check verifies.
- **Files affected:** `references/orchestration.md` (dispatch template), `.claude/agents/gate-check.md`
- **Verification criteria:** Grep for dispatch blocks in orchestration.md — all contain the 3 mandatory variables.

#### I8: Fix list-active-role-types slug extraction
- **What needs to change:** `manage_state.py list-active-role-types` must produce clean slugs (3-40 chars, `[a-z0-9-]` only) from context.md, not full-sentence conversions.
- **Files affected:** `scripts/manage_state.py`
- **Verification criteria:** Output contains clean slugs like `ai-engineer`, `founders-associate`, not full sentences.

## Solutions Extracted
1. **Permission escalation cascade** — Attempted specific wildcards → blanket permissions → foreground fallback. The reusable pattern: escalate dispatch strategy on permission failure, don't retry the same strategy.
2. **Model tier escalation for scoring** — Haiku→Sonnet for scoring tasks that require judgment. Haiku is sufficient for data extraction but not for profile-matching evaluation.
3. **Unified `_extract_score()` function** — Polymorphic schema extraction handles 4 different score field locations. Applied to manage_state.py and api/jobs.py. Defensive extraction at consumption point is the right pattern for multi-source pipelines.
4. **`git checkout HEAD --` recovery** — After dedup destroyed all files, immediate git restore from last commit saved the run. Always commit before destructive operations.
5. **End-of-session self-audit** — Checking all output artifacts against documented requirements catches accumulated drift from long sessions.
6. **Context propagation pattern** — When user changed search criteria, systematically updated 8 context.md sections in one pass. Reusable for any multi-section config update.

## Patterns Identified
1. **Permission Escalation Cascade** (7 steps) — specific wildcards → blanket permission → foreground fallback → parent direct execution. Appeared 3 times. Skill candidate: Yes.
2. **Multi-Schema Score Extraction** (5 steps) — discover crash → read samples → build normalizer → apply everywhere → verify. Appeared in 4 downstream systems. Skill candidate: Yes (schema normalizer).
3. **Subagent Quality Verification Loop** (7 steps) — dispatch → inspect → find problems → re-dispatch stricter → inspect → escalate tier → verify. Appeared for JobSpy and newsletter. Skill candidate: Yes (quality gate).
4. **Context Update Before Search Dispatch** (9 steps) — user change → update Target → Industries → Sources → queries → newsletters → web search → career pages → validate consistency. Appeared once but will recur every session. Skill candidate: Yes.
5. **Deploy-Verify-Fix Cycle** (9 steps) — commit → push → deploy → verify endpoint → discover failure → diagnose → fix → redeploy → re-verify. Appeared for dashboard. Skill candidate: No (too deployment-specific, but verification assertions are extractable).

## Build Metrics
- **Build duration (total):** Unavailable (phased-build step timing not yet enabled)
- **Steps completed:** 22 / 22
- **Verification pass rate:** 5 / 5 capability checks passed
- **Regression count (new):** 0 (build introduced no new regressions)
- **Regression count (repeat):** 1 (pre-existing settings.local.json failure, grew to 5 pre-existing by Phase 3)
- **Review cycle count:** 2 (Round 1 + Round 2 before build)
- **Test suite growth:** 132 (Phase 0) → 165+ (Phase 3), 38 new tests added

## Handoff Contract
- Architectural fixes: 2 — (A1) Remove background dispatch, mandate foreground-only; (A2) Enforce canonical verified JSON schema with validation gate
- Implementation fixes: 8 — (I1) Scoring to Sonnet tier; (I2) Session-state.md update gate; (I3) Dedup safety bound; (I4) Title filtering positive examples; (I5) Incremental commit gate; (I6) Comprehensive default settings; (I7) Mandatory dispatch variables; (I8) Fix slug extraction
- New constraints: CR10 enforcement gate, HC7 enforcement gate, schema validation gate, dedup safety bound, scoring tier minimum
- Regression tests to include: Schema validation, dedup safety, session-state update, commit gate, slug format
- Prevention artifacts written: 5 reviewer prompt additions (deployment-verifier, data-integrity-guardian x2, regression-checker, performance-oracle), 0 bash prevention scripts (deferred to V2)
- Metrics recorded: V23 build metrics (22/22 steps, 5/5 verification, 0 new regressions)

<!-- STAGE COMPLETE: /analyze, 2026-02-25 -->

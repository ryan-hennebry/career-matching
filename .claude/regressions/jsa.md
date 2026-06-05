# JSA Regressions

## V14
- [ ] Agent must never attempt PDF generation — briefs are HTML files only (Chromium pagination is fundamentally broken)
- [ ] Agent must read `.claude/agent-memory/` on startup and treat documented failures as hard constraints
- [ ] Digest email must not show blue hyperlinks — must use design system link color
- [ ] Digest email must hide sections with zero items (e.g., "Still Active: 0" must not render)
- [ ] Digest email must only show jobs scoring 70+ (same threshold as CLI presentation)
- [ ] Digest email must not use colored warning text (red, amber, orange)
- [ ] Brief score breakdowns must not use gray background boxes / bordered containers
- [ ] Brief generation must complete in <60s — no hiring manager research, Crunchbase, Glassdoor, funding rounds
- [ ] Parent must verify visual output after digest-email and briefs-html subagents complete (post-render check)
- [ ] session-state.md must be written after every search batch, not just at Step 20
- [ ] Pre-run cleanup must execute and log when last_run_date differs from today
- [ ] After generating output files, agent must state the full absolute file path to the user
- [ ] Job title links in briefs must be visually distinct (not just color — underline or bold)
- [ ] No ad-hoc HTTP servers — use scripts/preview.sh for HTML preview

## V15
- [ ] Selecting jobs for briefs must not reject unselected jobs — use "brief_requested" action, not "accept + reject rest"
- [ ] Never write inline Python (`python3 -c`) that imports manage_state internals — use CLI subcommands only
- [ ] Git pull must execute before any file reads in interactive mode (startup step 2)
- [ ] Email send must check `_status.json` for `sent_at` matching today before sending (idempotency guard)
- [ ] API keys must never appear as CLI arguments — pipe via stdin
- [ ] Agent must proactively offer scheduled run setup after first successful interactive session
- [ ] Every API key request must include the source URL (e.g., console.anthropic.com/settings/keys)

## V16
- [ ] Score threshold is inclusive: present jobs scoring >= 70, not > 70
- [ ] Provide unified numbered list across all role types when asking user to select jobs for briefs
- [ ] Auto-retry must dispatch via Task tool subagent — never retry inline in parent context
- [ ] On subagent partial failure (work done but no _status.json), dispatch recovery subagent — never read verified JSONs in parent
- [ ] preview.sh must keep HTTP server running after script exits — no trap cleanup EXIT that kills the server
- [ ] Do not ask user for email send confirmation — pre-send gate checks are sufficient; send automatically
- [ ] session-state.md must be written after EVERY search batch, not deferred to end of all batches (V14 regression recurrence)
- [ ] Onboarding must ask "What types of roles are you targeting?" explicitly — inferred roles are a suggestion, not final answer
- [ ] Jobs below user's minimum salary must be score-penalized or grouped separately — never rank alongside salary-compliant jobs

## V17
- [ ] GitHub Actions workflow must create `.claude/settings.local.json` during CI setup — file is gitignored and never committed
- [ ] Post-deploy smoke test must verify `/api/jobs` returns 200 before running the agent in CI
- [ ] API endpoints must fall back from Upstash Redis to `state.json` when Redis is unavailable
- [ ] Agent must read `.claude/agent-memory/*/MEMORY.md` on startup (V14 regression recurrence — HC4)
- [ ] Agent must offer scheduled run setup after first successful interactive session (V15 regression recurrence — Step 22)
- [ ] Cross-role dedup must use a CLI subcommand, not inline `python3 -c` — avoid HC5 violation
- [ ] Post-render regex for amber/red colors must match CSS values only, not text substrings like "preferred"
- [ ] [deployment] Vercel API handlers must use Vercel-compatible pattern (not BaseHTTPRequestHandler) — test with live deploy before marking build complete
- [ ] [deployment] vercel.json must use modern `functions` + `rewrites` config, not legacy `builds` key; enable `cleanUrls: true`
- [ ] [deployment] Vercel must auto-deploy from main branch — verify in Vercel project settings
- [ ] [configuration] GitHub Actions workflows must live at repo root `.github/workflows/`, not nested in agent subdirectories
- [ ] [configuration] All required secrets (RESEND_API_KEY, ANTHROPIC_API_KEY) must be validated as configured in GH Actions before enabling scheduled workflows
- [ ] [uncategorized] Agent must never ask user to do technical work (hard refresh, check URLs, inspect dashboards) — delegate to subagents per CR5

## V18
- [ ] [subagent-coordination] Background subagent dispatch must test tool access first — dispatch a trivial test agent before main workflow; on failure, switch to foreground-only mode immediately
- [ ] [subagent-coordination] Parent context must NEVER execute search, filter, dedup, WebFetch, or WebSearch directly — these are always subagent-delegated, even when subagents fail
- [ ] [subagent-coordination] Parent must NEVER read source files (verified JSONs, scripts, algorithms, workflow files) directly — dispatch subagents to read and return summaries
- [ ] [data-integrity] Cross-role dedup must compare on normalized title+company, not filename slugs — filename truncation causes false-negative matches
- [ ] [uncategorized] After presenting results, agent must proactively show dashboard URL ("View and manage all jobs at: {url}") — do not wait for user to ask
- [ ] [configuration] Agent must never fabricate instructions about Claude Code UI features (keyboard shortcuts, permission modes) — state uncertainty and suggest documentation
- [ ] [security] API keys must never appear in bash command arguments (echo, gh secret set) — use stdin redirection or instruct user to set via GitHub UI (V15 regression recurrence)
- [ ] [security] settings.local.json modifications must be additive (merge into existing permissions) — never overwrite the entire file
- [ ] [data-integrity] session-state.md must be written after EVERY search batch, not deferred to end (V14/V16 regression recurrence)

## V19
- [ ] [subagent-coordination] Subagents must write output to the correct version directory (v19, not v18) — pass absolute working directory as explicit variable in dispatch prompt
- [ ] [configuration] GitHub Actions workflow must reference the current agent version directory — never point at a previous version (v18→v19 mismatch found)
- [ ] [data-integrity] Cross-role dedup must normalize on (company.lower(), title.lower()) from JSON content, not filename slugs — same company+title under different role types produces different slugs (V18 regression recurrence)
- [ ] [configuration] Dashboard URL must be stored in context.md ## Delivery and proactively shown to user after presenting results (V18 regression recurrence)
- [ ] [subagent-coordination] Incremental commit+push must execute after each search batch (Step 11b) — not deferred to session end (V14/V16/V18 regression recurrence)
- [ ] [subagent-coordination] Parent must NEVER run `python3 scripts/*` directly — all script execution via subagent dispatch (context budget violation)
- [ ] [configuration] Bash permissions must be pre-configured in `.claude/settings.local.json` for known subagent commands to enable autonomous scheduled runs
- [ ] [subagent-coordination] Never pass `model:` parameter to Task tool — violates HC1
- [ ] [subagent-coordination] CM subagent must write `_summary.md` — on failure, dispatch recovery subagent per recovery protocol (not workaround in parent)
- [ ] [configuration] Pre-run cleanup must use `find -type f -delete` not `rm -f dir/*` — zsh treats unmatched globs as errors
- [ ] [design-system] All role types must use consistent table format in presentation — no mixed table/line formats
- [ ] [data-integrity] Agent memory files must be read on startup (V14/V17 regression recurrence — HC4)
- [ ] [deployment] GitHub Actions workflow must generate CI-only config files (settings.local.json) or use `--dangerously-skip-permissions` — never expect gitignored files to exist in CI
- [ ] [deployment] GitHub Actions timeout must be >=90 minutes for full agent runs — 30 minutes is insufficient
- [ ] [deployment] Scheduled workflow must include preflight checks (secrets set, required files exist, dependencies installed) before the Claude API call
- [ ] [deployment] Scheduled workflow must include retry logic (`nick-fields/retry` or equivalent) for transient failures

## V20
- [ ] [data-integrity] Pre-run cleanup must cross-reference state.json before deleting verified files — preserve files for still-active jobs, not blind delete-all
- [ ] [configuration] Dashboard URL must be mandatory in all code paths — remove all "omit silently" / null fallbacks; fail loudly if missing (V18/V19 regression recurrence)
- [ ] [deployment] GitHub Actions heredoc for settings.local.json must produce valid JSON — add validation step after file creation
- [ ] [configuration] settings.local.json must include Read, Write, Glob, Grep in permissions allowlist for background subagent operation
- [ ] [subagent-coordination] After context compaction, NEVER reconstruct findings from conversation summary — re-dispatch subagents to get actual data
- [ ] [data-integrity] Cross-role dedup must not hard-delete verified JSON files that the dashboard API depends on — preserve at least one copy per unique job
- [ ] [subagent-coordination] Incremental commit+push must execute after EACH search batch (V14/V16/V18/V19 regression recurrence — HC7)
- [ ] [data-integrity] Score threshold (>=70) must be enforced before presentation — no jobs below 70 shown to user
- [ ] [design-system] All role types must use identical table format in presentation (V19 regression recurrence)
- [ ] [data-integrity] Cross-role dedup must normalize on (company.lower(), title.lower()) from JSON content — catch same company+title across role type directories (V18/V19 regression recurrence)
- [ ] [performance] CLAUDE.md must be <=300 lines per Agent Decomposition Pattern — extract to references/ for on-demand loading
- [ ] [data-integrity] Within-role dedup must catch same-URL duplicates (Robinhood appeared twice with different scores)
- [ ] [subagent-coordination] First Write to session-state.md must be preceded by a Read (tool constraint)
- [ ] [performance] Search-verify subagents must complete in <2 minutes — skip hiring manager research, Crunchbase, funding rounds

## V21
- [ ] [performance] Search-verify subagent hit API rate limit after 24 tool uses / 16 min — must have a hard time/tool-use budget with checkpoint-and-return on budget exhaustion
- [ ] [configuration] settings.local.json must be comprehensive BEFORE first live session test — validate minimum required permissions in preflight (Read, Write, Glob, Grep, WebFetch, WebSearch, Bash scripts)
- [ ] [deployment] Vercel dashboard must be re-linked and redeployed on every version transition — `vercel link --project jsa-dashboard --yes && vercel --prod --yes` (V21: stale v18 data for 2 days)
- [ ] [deployment] GitHub Actions workflow must reference current version directory — never point at previous version (V19/V21 regression recurrence)
- [ ] [deployment] `vercel --prod` must always be preceded by `vercel link --project <name> --yes` — running without link creates accidental new project
- [ ] [testing] Preflight CLI flag checks must be validated against actual `--help` output — never hardcode assumed flag names (3 consecutive startup failures)
- [ ] [testing] Preflight structural greps must use partial matches — exact heading matches break when headings are annotated
- [ ] [data-integrity] Archival/cleanup must cross-reference state.json active jobs before moving verified JSONs — blind archive breaks dashboard and brief generation (V20 regression recurrence)
- [ ] [data-integrity] Search queries for domain-specific roles must use targeted terms ("AI agent", "agentic AI") not generic composites ("AI marketing community manager")
- [ ] [subagent-coordination] Incremental commit+push after every search batch — not deferred to session end (V14/V16/V18/V19/V20/V21 regression recurrence — 6th occurrence, needs hard enforcement)
- [ ] [data-integrity] session-state.md must be written after EVERY search batch (V14/V16/V18/V19/V21 regression recurrence — 5th occurrence, needs hard enforcement)
- [ ] [configuration] send_email.py uses `--body-file` not `--html` — orchestration references must match actual CLI interface
- [ ] [configuration] Never `git add` files listed in `.gitignore` (settings.local.json)
- [ ] [uncategorized] Never claim `/export` captures pre-compaction content — state uncertainty per HC6, recommend JSONL conversion script
- [ ] [uncategorized] Never ask user to do technical work (Vercel settings, GH Actions config) — handle via CLI per CR5 (V17/V18 regression recurrence)

## V22
- [ ] [subagent-coordination] Rate limit hit on first dispatch returned stale data — agent must detect stale/missing output from subagent summaries and surface options, never present stale data as fresh
- [ ] [subagent-coordination] Search breadth defaulted to 2 batches (career pages only) — all 5 search channels must dispatch automatically on every run with zero user prompting (V23 memory requirement not enforced)
- [ ] [data-integrity] Dedup archived all new results due to stale prior-run role-type directories in output/verified/ — dedup must be scoped to active role types only (V23 memory requirement not enforced)
- [ ] [configuration] CI preflight required settings.local.json in SCHEDULED_RUN context — preflight must skip this check when SCHEDULED_RUN=true (V20 known issue, not addressed until V22 session)
- [ ] [configuration] Workflow did not pass SCHEDULED_RUN env var to preflight step — all bash steps in CI must receive required env vars, not just the Claude action step
- [ ] [deployment] Vercel dashboard not redeployed after data push — post-push Vercel deploy must be a mandatory orchestration step, not memory-only (V21 regression recurrence)
- [ ] [subagent-coordination] Incremental commit+push after each search batch was skipped — 7th occurrence (V14/V16/V18/V19/V20/V21/V22), needs hard enforcement gate not just constraint
- [ ] [data-integrity] session-state.md not written after each search batch — 6th occurrence (V14/V16/V18/V19/V21/V22), needs hard enforcement gate

## V23
- [ ] [subagent-coordination] Background subagent permissions denied despite blanket settings.local.json — 8th version with this failure (V20 regression). Must remove background dispatch entirely and mandate foreground-only until Claude Code platform fix confirmed.
- [ ] [data-integrity] Inconsistent verified JSON score schemas across channels (score int, scoring.total_score, score_breakdown.total, score dict) — cascaded into 4 downstream failures (digest builder, manage_state sync, api/jobs 500, dedup). Must enforce canonical schema with validation gate.
- [ ] [data-integrity] Haiku cannot apply profile-matching scoring — scored barista/data scientist at 95-100. Scoring must use Sonnet tier minimum, not Haiku. (V22 memory requirement for cost reduction must preserve scoring quality.)
- [ ] [subagent-coordination] Parent violated context budget — executed WebFetch (4 URLs), WebSearch (2 queries), read verified JSONs directly, ran inline Python. Must re-dispatch on failure, not escape-hatch. (HC5, Context Budget rules)
- [ ] [data-integrity] session-state.md not updated after channel completion — 9th occurrence (V14/V16/V18/V19/V21/V22/V23). Requires structural enforcement gate, not constraint.
- [ ] [data-integrity] manage_state.py dedup archived ALL 63 jobs on fresh run — must add safety bound (abort if >50% would be archived) and --dry-run flag.
- [ ] [data-integrity] Niche newsletter agent missed Founder's Associate roles from Early & Exec — conflated "Founder's Associate" with executive roles. Scoring rubric must include positive examples for associate-level titles.
- [ ] [data-integrity] Digest job key builder missed high-scoring jobs from channels using non-standard score fields — downstream of schema inconsistency (see above).
- [ ] [subagent-coordination] Incremental commit+push skipped after search phase — 8th occurrence (V14/V16/V18/V19/V20/V21/V22/V23). Must add structural commit gate at Phase 1 exit.
- [ ] [subagent-coordination] HC10 violated — working_dir, output_directory, dashboard_url never passed to any subagent dispatch. Must add mandatory dispatch variable checklist.
- [ ] [subagent-coordination] Auto-retry protocol violated — gate-check dispatched 3 times (max is 2 total attempts). Must enforce retry counter.
- [ ] [performance] Niche newsletter subagent took 3h 16m — must enforce hard time budget with checkpoint-and-return on exhaustion. (V20 regression: search-verify must complete in <2 min.)
- [ ] [configuration] send_email.py called with --html instead of --body-file (V21 regression recurrence) — orchestration references must match actual CLI interface.
- [ ] [data-integrity] list-active-role-types produced full-sentence slugs instead of clean [a-z0-9-] slugs — parsing too literal for free-form context.md text.
- [ ] [configuration] settings.local.json bloated to 34+ entries from subagent permission requests — must add post-run cleanup or cap entry count.
- [ ] [uncategorized] Two questions asked in one message (CR4 violation) — must ask one question at a time.

## V24
- [ ] [configuration] Preflight.sh exits with error code 1 on first run after build (100% safety bound) — must detect first-run state and skip bound checks when no prior-run data exists
- [ ] [data-integrity] context.md Target section written as compound bullets breaks list-active-role-types — must validate one-role-per-bullet format immediately after writing
- [ ] [subagent-coordination] Search-verify agents did not write .done sentinel files — sentinel write must be a mandatory final step inside the search-verify agent (V14/V16/V18/V24 recurrence — 4th occurrence)
- [ ] [data-integrity] 16/23 verified JSONs failed schema validation (legacy format) — search-verify agents must validate against canonical schema before writing (V23 recurrence)
- [ ] [subagent-coordination] Incremental commit+push skipped after search batch — 9th occurrence (V14/V16/V18/V19/V20/V21/V22/V23/V24). MUST add structural commit gate at Phase 1 exit — constraint alone is insufficient
- [ ] [subagent-coordination] Post-compaction parent read _delta.json and _summary.md files directly — violates P2 rule and context budget. Must dispatch recovery subagent (V20 recurrence)
- [ ] [subagent-coordination] session-state.md not written after search batch — 10th occurrence (V14/V16/V18/V19/V21/V22/V23/V24). MUST add structural write gate — constraint alone is insufficient
- [ ] [subagent-coordination] Agent lost task IDs for background agents after context compaction — must persist task IDs in session-state.md and verify before polling
- [ ] [performance] Rate limit hit mid-session caused both delivery agents to abort — need token budget awareness or graceful pause on rate limit detection
- [ ] [performance] Briefs HTML skipped due to token cost — briefs-html compilation too expensive in same session as 8 brief generators. Must decouple to separate session or pre-compiled
- [ ] [subagent-coordination] HC-10 violated — working_dir, output_directory, dashboard_url not passed to any subagent dispatch (V23 recurrence)
- [ ] [configuration] HC-5 violated — list-active-role-types run in parent context (not in allowed subcommand list)
- [ ] [configuration] Startup git pull not executed explicitly — preflight.sh git pull is implicit, not the required explicit parent git pull with success verification
- [ ] [ux-cli] Full 8-row briefs status table reprinted after every single brief completion (8 reprints) — must print one-liner per completion, full table only at end
- [ ] [ux-cli] No proactive status update during long-running parallel operations — user asked "still going?" 3 times. Must implement timed polling with proactive status messages every 90s
- [ ] [ux-cli] Post-compaction re-entry had no immediate user-visible status — agent silently read files for minutes before producing output. Must print immediate 1-2 sentence summary on re-entry
- [ ] [ux-cli] No visual separators between role type sections in results presentation — sections need clear headers with counts, spacing, and hierarchy for terminal readability
- [ ] [ux-cli] User typed job names from memory instead of using numbered selection — must present unified numbered list including prior-run active jobs for selection
- [ ] [ux-cli] CR-7 violated — relative paths used when citing output files; must state absolute file paths after generating output

## V25
- [ ] [data-integrity] Generic career page URLs presented instead of direct ATS listing URLs — parent extracted wrong URL field from verified JSONs. Must add pre-presentation schema validation enforcing ATS URL patterns (greenhouse.io, ashbyhq.com, lever.co, workable.com, rippling.com).
- [ ] [subagent-coordination] .done sentinel files written to `.channels/` instead of `output/.channels/` — 5th occurrence (V14/V16/V18/V24/V25). Subagent dispatch must hardcode explicit absolute path for sentinel file.
- [ ] [subagent-coordination] JobSpy aggregator channel used WebSearch instead of running `scripts/jobspy_search.py` — must add hard constraint prohibiting WebSearch fallback in JobSpy channel.
- [ ] [data-integrity] Agent recommended removing 7 of 8 jobs as expired without visiting URLs — all 7 were actually still live. Must add mandatory URL verification before any removal recommendation. (ARCHITECTURAL)
- [ ] [data-integrity] Re-verification subagent set `active_status=None` instead of `"expired"` — expired jobs persisted in rankings across multiple presentations. Schema validation must enforce non-null `active_status` after any verification.
- [ ] [data-integrity] Aggregator-based liveness verification unreliable — Playwright confirmed Linda AI as "LIVE" via StudySmarter aggregator when listing was expired. Must verify at company's own ATS first, not aggregator. (ARCHITECTURAL)
- [ ] [configuration] Agent memory not read on startup — 6th occurrence (V14/V17/V19/V22/V24/V25). Must add preflight.sh enforcement check, not just constraint.
- [ ] [subagent-coordination] Parent executed inline Python after subagent truncation — `python3 -c "import json,sys..."` in parent context. Must re-dispatch with Sonnet tier on truncation, not fall back to parent. (V15/V18/V19/V23/V24 recurrence)
- [ ] [configuration] Foreground/background contradiction in CLAUDE.md — Core Rules mandate "foreground-only" while Startup S6 says "background: true". Must resolve to single directive.
- [ ] [data-integrity] Jack & Jill listing used wrong Ashby board slug (`jack-and-jill` vs `jack-jill-external-ats`) showing GBP 36-60K instead of actual GBP 100-180K. Cross-reference company ATS slug when multiple boards exist.
- [ ] [configuration] manage_state.py emits SyntaxWarning for `'\d'` raw string on every invocation (line 1408) — must use r-prefix.
- [ ] [configuration] Dedup `--role-types` flag shows "0 input files" due to argument parsing bug — must fix or test this flag.
- [ ] [configuration] Safety bounds (50%) too aggressive for multi-week gaps between runs — must auto-adjust threshold when gap > 7 days.
- [ ] [subagent-coordination] Haiku subagent truncated output for large JSON reads — must use Sonnet tier for data-heavy extraction tasks.
- [ ] [data-integrity] Expired jobs re-included in ranked lists after being flagged as removed — user caught "you've included roles that are no longer available". Pre-presentation gate must exclude all expired jobs.
- [ ] [data-integrity] Jill board roles presented with "via Jill board" instead of actual URLs — must extract direct application URLs from Ashby API.
- [ ] [data-integrity] Specter Labs URL garbled (missing 'h' prefix, duplicated inline) — must validate URL format before presentation.
- [ ] [configuration] session-state.md Write failed on first attempt (file didn't exist) — preflight must ensure file exists. (V24 recurrence)

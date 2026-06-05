# Research: JSA V18 (Full)

## Current State

The Job Search Agent V18 is a Claude Code orchestrated multi-agent system that aggregates, scores, and delivers job listings for crypto/AI/startup roles. The parent Claude context serves as the orchestrator — there is no single Python entry point. Six named subagents handle specialized tasks (onboarding, source research, search+verify, brief generation, briefs HTML compilation, digest email). A Vercel-hosted dashboard provides an interactive web interface backed by 8 Python serverless API endpoints and Upstash Redis for live user actions.

### Architecture Overview

**Orchestration:** CLAUDE.md defines a 23-step sequential workflow. The parent dispatches subagents via the Task tool, reads status files for completion, and handles email delivery directly. Subagents are defined in `.claude/agents/*.md` with YAML frontmatter and preloaded skills from `.claude/skills/`.

**Data Flow:** `context.md` (user profile) -> source-researcher discovers sources -> search-verify subagents (JobSpy scraping + WebFetch specialty boards, one per role type) -> `output/jobs/` raw results -> `output/verified/{role_type}/` scored JSONs -> `manage_state.py sync` -> `state.json` + `output/_delta.json` -> user presentation -> brief-generator subagents -> `output/briefs/` -> digest-email + briefs-html subagents -> `output/digests/` HTML -> `send_email.py` via Resend API. Dashboard reads committed `output/` + `state.json` via Vercel serverless + Upstash Redis for live actions.

**Execution Modes:**
- **Interactive:** Full 23-step flow with user feedback, brief selection, git pull/push
- **Scheduled (`$SCHEDULED_RUN`):** Skips onboarding, user feedback, git pull, briefs. Auto-accepts all jobs for digest. GitHub Actions commits state to main.

## Code References

### Entry Point & Orchestration
- `CLAUDE.md` — 23-step orchestration workflow, all constraints, agent dispatch logic

### Named Agents (`.claude/agents/`)
- `onboarding.md` — CV parse + profile extraction. Skill: `jsa-onboarding`. Output: `_onboarding_draft.json`
- `source-researcher.md` — Industry source discovery (5 categories). Skill: `jsa-source-researcher`. Output: `_source_research.json`
- `search-verify.md` — Search+verify+score per role type. Skill: `jsa-search-verify`. 14 input variables. Output: `output/verified/{role_type_slug}/`
- `brief-generator.md` — Single application brief (6-section markdown, 300-500 words). Skill: `jsa-brief-generator`. Output: `output/briefs/{slug}-brief.md`
- `briefs-html.md` — Compile briefs into styled HTML. Skills: `jsa-design-system`, `jsa-briefs-html`. Output: `output/briefs/briefs-{date}.html`
- `digest-email.md` — Generate digest email HTML. Skills: `jsa-design-system`, `jsa-digest-email`. Output: `output/digests/{date}-email.html`

### Skills (`.claude/skills/`)
- `jsa-design-system.md` — Unified design system: Newsreader (serif headings 28/22/18px) + DM Sans (sans-serif body 15px), warm stone/ink palette (no blue), score badge tiers (green 90+, stone 80-89, muted 70-79), dashboard interactive tokens, elevation system, spacing scale
- `jsa-briefs-html.md` — Briefs HTML compilation instructions (cover page, TOC, brief-page sections, 800px max-width)
- `jsa-digest-email.md` — Digest email template (new today cards + still active table + summary strip, 600px max-width, 8 template variables)
- `jsa-brief-generator.md` — Single brief generation (6 sections, 300-500 words, no external research)
- `jsa-search-verify.md` — Search+filter+verify+score workflow (14 template variables)
- `jsa-onboarding.md` — CV parsing and profile extraction
- `jsa-source-researcher.md` — Deep industry source discovery (5 categories, WebFetch accessibility verification)

### Scripts (`scripts/`)
- `manage_state.py` — CLI with 3 subcommands: `sync` (update state, expire old jobs, compute delta), `record-action` (write user_action), `dedup` (cross-role dedup by source_domain:company:title, keeps highest score)
- `jobspy_search.py` — python-jobspy wrapper (Indeed/LinkedIn/Glassdoor scraping)
- `filter_jobs.py` — Title exclusion keyword filter
- `summarize_jobs.py` — One-line summaries for context efficiency
- `send_email.py` — Resend API sender (HTML body + optional base64 attachment, loads .env)
- `verify_html.py` — Post-render check for prohibited CSS colors (blue/red/orange/amber)
- `preview.sh` — Local HTTP server on port 8800, PID tracked at `/tmp/jsa-preview.pid`

### API Endpoints (`api/`)
- `jobs.py` — Returns scored job list
- `job.py` — Returns single job detail
- `state.py` — Returns summary counts
- `pipeline.py` — Groups jobs by pipeline stage
- `action.py` — Writes user actions (accept/reject/brief_requested) to Upstash Redis
- `brief.py` — Returns brief HTML
- `context.py` — Returns profile section names from context.md
- `run.py` — Dispatches/polls GitHub Actions workflow via API
- `_files.py` — Shared file reader (scans `output/verified/`)
- `_upstash.py` — Redis client with state.json fallback
- `_response.py` — CORS + JSON response helpers

### Dashboard (`public/`)
- `index.html` — SPA shell
- `js/app.js` — Client-side router
- `js/api.js` — Fetch client for API endpoints
- `js/components.js` — HTML renderers (job cards, pipeline view, etc.)
- `css/dashboard.css` — Dashboard styles (warm stone/ink palette, interactive tokens)

### State Files
- `state.json` — Primary persistent state: `{last_run_date, jobs: {key: JobEntry}, expired_jobs: {key: JobEntry}}`. Atomic writes via tempfile+os.replace. EXPIRY_DAYS=14, PURGE_DAYS=90.
- `context.md` — User profile (skills, experience, industries, target roles, constraints, sources, delivery email)
- `output/_delta.json` — Delta from sync: `{run_date, new_jobs, still_active, expired_count, rejected_count}`
- `output/session-state.md` — Human-readable run log
- `output/verified/{role_type}/_status.json` — Per-role search status (complete/partial/failed)
- `output/digests/_status.json` — Digest email status (includes `sent_at` for idempotency)
- `output/briefs/_status.json` — Briefs HTML compilation status

### Agent Memory (`.claude/agent-memory/`)
- `brief-generator/MEMORY.md`, `briefs-html/MEMORY.md`, `digest-email/MEMORY.md`, `search-verify/MEMORY.md` — Per-agent failure patterns read on startup as hard constraints (currently empty)

### Reference Docs
- `references/algorithms.md` — Scoring rubrics (5-factor: required_skills 40, preferred 20, experience 15, industry 15, location 10 + salary penalty -10), skill normalization table, experience level mapping, location/industry match scoring, dedup rules (source_domain:company:title), CV parsing extraction order, learning system storage format

### CI/CD
- `.github/workflows/daily-digest.yml` — Cron `0 6 * * 1-5` (6am UTC weekdays), workflow_dispatch, Python 3.12, installs Claude Code via npm, creates settings.local.json, preflight checks, runs agent with `--print` + `SCHEDULED_RUN=true`, commits state.json + session-state.md, post-deploy smoke test against Vercel `/api/jobs`
- `vercel.json` — Routes api/*.py as serverless (10s maxDuration), rewrites to public/ for static
- `.vercel/project.json` — Project: jsa-dashboard

### Config
- `requirements.txt` — `upstash-redis>=1.0.0`, `markdown>=3.5` (Vercel serverless deps)
- `.claude/settings.local.json` — Claude agent permissions (gitignored, created by CI setup)

## Patterns Found

### Named Agent Pattern
- YAML frontmatter in `.claude/agents/*.md` with `model: inherit`, `memory: project`
- Skills preloaded via `skills:` field (resolved to `.claude/skills/`)
- Variables passed as compact JSON blobs from parent to subagent prompt
- Status file protocol (`_status.json`) for completion signaling
- Completion sentinels in output files (`<!-- BRIEF COMPLETE -->`)

### State Management Pattern
- All state mutations through `manage_state.py` CLI subcommands — never inline Python
- Atomic writes via tempfile+os.replace
- Job lifecycle: new -> active -> expired (14 days) -> purged (90 days)
- User actions stored in both state.json (durable) and Upstash Redis (live)

### Design System Pattern
- Single source of truth: `jsa-design-system.md` skill
- Preloaded by visual output agents (briefs-html, digest-email)
- Warm stone/ink palette, no blue anywhere
- Score badges with tier-specific colors (green/stone/muted)
- Post-render verification via `verify_html.py`

### Subagent Dispatch Pattern
- Batched dispatch (2-3 at a time for search-verify)
- Status file polling for completion
- Auto-retry once on failure, never inline in parent
- Parent sends email directly (not delegated to subagent)
- Session-state.md written after every batch

### Dashboard Pattern
- Vanilla JS SPA (no framework) with client-side routing
- Vercel serverless Python API reading committed files
- Upstash Redis overlay for live user actions between deploys
- CORS headers for cross-origin access

## External Landscape

### Vercel Python Runtime
- Beta on all plans. Supports FastAPI, Django, Flask. Python version from `pyproject.toml`/`.python-version`/`Pipfile.lock`.
- Bundle size limit: 250 MB unzipped. Environment variables: 64 KB total.
- Filesystem: read-only, writable `/tmp` up to 500 MB. Function duration: 10s Hobby, 60s Pro, 900s Enterprise.
- Cold starts: archived functions add ~1s.

### Upstash Redis
- Python SDK v1.6.0 (Feb 2026). `Redis.from_env()` loads `UPSTASH_REDIS_REST_URL`/`UPSTASH_REDIS_REST_TOKEN`.
- Default retry: 1 attempt, 3s delay. Initialize client outside handler for warm invocation reuse.

### Resend Email
- Python SDK actively maintained. Auth: single `RESEND_API_KEY`. Domain verification required for production.
- No built-in templates (HTML constructed manually). Free tier: 100 emails/day, 3,000/month.

### GitHub Actions
- Cron: standard POSIX 5-field, UTC, minimum 5-minute interval. Default branch only.
- Timing: best-effort, may be delayed during high load. Multiple schedules supported per workflow.

### Claude Code Agent Conventions
- Subagents run in own context windows with custom system prompts and specific tool access.
- Recommended limit: 3-4 subagents max per orchestration to avoid dispatch overhead.
- No job-search-specific community patterns found — this is a custom domain application.

## Related Files

All paths relative to `03_agents/tests/v18/`:

| Category | Files |
|----------|-------|
| Orchestration | `CLAUDE.md` |
| Agents | `.claude/agents/{onboarding,source-researcher,search-verify,brief-generator,briefs-html,digest-email}.md` |
| Skills | `.claude/skills/{jsa-design-system,jsa-briefs-html,jsa-digest-email,jsa-brief-generator,jsa-search-verify,jsa-onboarding,jsa-source-researcher}.md` |
| Scripts | `scripts/{manage_state,jobspy_search,filter_jobs,summarize_jobs,send_email,verify_html}.py`, `scripts/preview.sh` |
| API | `api/{jobs,job,state,pipeline,action,brief,context,run}.py`, `api/_{files,upstash,response}.py` |
| Dashboard | `public/index.html`, `public/js/{app,api,components}.js`, `public/css/dashboard.css` |
| State | `state.json`, `context.md`, `output/_delta.json`, `output/session-state.md` |
| Config | `vercel.json`, `.vercel/project.json`, `requirements.txt`, `.claude/settings.local.json` |
| CI/CD | `.github/workflows/daily-digest.yml` |
| Reference | `references/algorithms.md` |
| Memory | `.claude/agent-memory/{brief-generator,briefs-html,digest-email,search-verify}/MEMORY.md` |
| Tests | `tests/fixtures/verified-job-template.json` |

## Historical Context

### Version Lineage
- **V8-V11:** Early iterations establishing core architecture (search, scoring, state management)
- **V12:** Compact JSON + subagent templates
- **V13:** Named agent pattern (YAML frontmatter, skills preloading, status file protocol)
- **V14:** Design system skill, HTML-only output (no PDF), email digest matching briefs styling
- **V16:** Score threshold inclusive (>=70), unified selection list, auto-retry via Task tool
- **V17:** Vercel dashboard deployment, Upstash Redis, GitHub Actions CI/CD, 46-step build, 11 failures
- **V18:** 3-phase build (infrastructure -> backend -> frontend), 8 implementation fixes from V17 analysis, dashboard visual polish, 21 steps

### Regression Tracking
64 total regression items across V14-V18 in `.claude/regressions/jsa.md`. V18 added 10 new items covering: subagent coordination (foreground fallback, context discipline), data integrity (title+company dedup, per-batch session-state writes), configuration (no fabricated UI guidance), security (API key stdin, additive settings.local.json).

### Decision Log (V18)
5 decisions in `.claude/decision-log/jsa-v18.md`: three-phase sequential build, prototyping skipped, preflight.sh script, CLI dedup subcommand, warm stone/ink dashboard palette.

### Analysis (V18)
8 failures identified, all implementation-level (0 architectural): foreground-fallback guard, context discipline enforcement, dedup title+company matching, dashboard link in results, forbid fabricated UI guidance, API key handling fix, additive settings.local.json writes, session-state.md per-batch writes. 3 are regressions from V14/V15/V16.

## Handoff Contract
- Files to modify: `CLAUDE.md`, `scripts/manage_state.py`, `.claude/agents/search-verify.md`, `.claude/skills/jsa-search-verify.md`, `.github/workflows/daily-digest.yml`, `.claude/settings.local.json` (plus potentially other files depending on fix scope)
- Patterns to preserve: Named agent pattern (YAML frontmatter + skills), state management via CLI subcommands only, design system single source of truth, status file protocol, atomic state writes, post-render HTML verification, parent-sends-email pattern
- Hard constraints discovered: No PDF generation, no inline Python for state, no blue in palette, no fabricated UI guidance, API keys via stdin only, additive settings.local.json writes, session-state.md after every batch, parent never reads source files directly, parent never executes search/filter/dedup/WebFetch/WebSearch
- Open questions: (1) Should V19 remain same architecture or restructure given 64 cumulative regressions? (2) Should agent-memory files be pre-populated from regressions to avoid re-discovery? (3) Is the 10s Vercel Hobby function timeout sufficient for dashboard API endpoints under load?

<!-- STAGE COMPLETE: /research [full], 2026-02-17 -->

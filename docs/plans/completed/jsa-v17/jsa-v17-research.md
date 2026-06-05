# Research: Job Search Agent V17

## Current State

JSA V17 is a multi-subagent job search pipeline with a Vercel-hosted dashboard. The agent lives in `03_agents/tests/v17/` and consists of a 578-line CLAUDE.md orchestrator, 6 named subagents, 7 skills, Python scripts for state/search/email, Vercel serverless API endpoints, and GitHub Actions for scheduled runs.

### Pipeline Flow

1. **Onboarding** (if first run) — parse CV, extract structured profile to `context.md`
2. **Source research** (if sources missing) — discover job sources across 5 categories
3. **Search-verify batches** — 2-3 parallel subagents per batch, each searching a role type via JobSpy + WebFetch, verifying listings, scoring on 100-point scale
4. **Cross-role deduplication** — deterministic dedup by highest score
5. **State sync** — `manage_state.py sync` computes delta (new/active/expired) against `state.json`
6. **Presentation + user feedback** — display ranked results, collect accept/reject/brief_requested
7. **Brief generation** — parallel subagents (one per job), 6-section markdown briefs
8. **Digest email + briefs HTML** — parallel subagents, design-system-governed HTML
9. **Email send** — parent-orchestrated via `send_email.py`, idempotency check
10. **Session state write** — checkpoint to `session-state.md`

### Architecture Pattern

Parent orchestrator dispatches all work via Task tool. Each subagent receives a compact JSON blob of variables and writes a `_status.json` sentinel on completion. Auto-retry once on failure; recovery subagent dispatched if status file missing. All state mutations go through `manage_state.py` CLI — no inline Python.

Incremental git commit+push after each pipeline stage (interactive mode). Vercel auto-deploys in ~30s after push, giving near-real-time dashboard updates.

## Code References

### Core Files
- `03_agents/tests/v17/CLAUDE.md:1-578` — Main orchestrator (pipeline steps, hard constraints, subagent dispatch patterns)
- `03_agents/tests/v17/context.md` — User profile (skills, target roles, sources, constraints, delivery prefs)
- `03_agents/tests/v17/state.json` — Persistent job lifecycle (last_run_date, jobs, expired_jobs)

### Named Subagents
- `03_agents/tests/v17/.claude/agents/search-verify.md` — Search sources, verify active, score jobs (14-var input)
- `03_agents/tests/v17/.claude/agents/brief-generator.md` — Generate 6-section markdown brief (7-var input)
- `03_agents/tests/v17/.claude/agents/digest-email.md` — Generate email HTML (8-var input)
- `03_agents/tests/v17/.claude/agents/briefs-html.md` — Compile briefs to styled HTML (1-var input)
- `03_agents/tests/v17/.claude/agents/source-researcher.md` — Discover job sources (4-var input)
- `03_agents/tests/v17/.claude/agents/onboarding.md` — Parse CV, extract profile (5-var input)

### Skills
- `03_agents/tests/v17/.claude/skills/jsa-design-system.md` — Unified design tokens (fonts, colors, typography, layout, CSS blocks)
- `03_agents/tests/v17/.claude/skills/jsa-digest-email.md` — Email HTML generation template
- `03_agents/tests/v17/.claude/skills/jsa-briefs-html.md` — Briefs HTML compilation template
- `03_agents/tests/v17/.claude/skills/jsa-search-verify.md` — Search + verify + score methodology
- `03_agents/tests/v17/.claude/skills/jsa-brief-generator.md` — Brief generation template
- `03_agents/tests/v17/.claude/skills/jsa-source-researcher.md` — Source discovery methodology
- `03_agents/tests/v17/.claude/skills/jsa-onboarding.md` — CV parsing + profile extraction

### Scripts
- `03_agents/tests/v17/scripts/manage_state.py:1-80` — State mutations: `sync` (compute delta), `record-action` (write user action). Atomic writes via tempfile.
- `03_agents/tests/v17/scripts/jobspy_search.py:1-88` — JobSpy wrapper: query, --location, --remote, --results, --output, --country. Searches Indeed/LinkedIn/Glassdoor.
- `03_agents/tests/v17/scripts/filter_jobs.py` — Title exclusion filtering (Senior, Lead, Head of, etc.)
- `03_agents/tests/v17/scripts/summarize_jobs.py` — Markdown table generation for verified jobs
- `03_agents/tests/v17/scripts/send_email.py` — Resend API: --to, --subject, --body-file, --attachment. Loads RESEND_API_KEY from .env.
- `03_agents/tests/v17/scripts/preview.sh` — Local HTML server on port 8800

### API Endpoints (Vercel Python Functions)
- `api/run.py` — POST: dispatch GitHub Actions workflow; GET: poll run status
- `api/jobs.py` — GET: list all verified jobs with pipeline stage derivation
- `api/job.py` — GET: single job detail (path traversal protected)
- `api/action.py` — POST: write user action to Upstash Redis or state.json
- `api/context.py` — GET: serve context.md
- `api/state.py` — GET: serve state.json
- `api/brief.py` — GET: serve brief HTML/markdown
- `api/pipeline.py` — GET: pipeline stage summary
- `api/_files.py` — Shared file reader
- `api/_response.py` — JSON response + CORS helpers
- `api/_upstash.py` — Redis client factory + fallback to state.json

### Infrastructure
- `vercel.json` — Functions config (api/*.py, 10s max duration), rewrites, cleanUrls enabled
- `.github/workflows/jsa-search.yml` — Manual workflow_dispatch, Python 3.12, JobSpy search per role type, commit+push results

### Output Structure
- `output/jobs/{role_type_slug}-aggregator.json` — Raw JobSpy results
- `output/jobs/{role_type_slug}-filtered.json` — After title exclusion
- `output/verified/{role_type_slug}/{company}-{title}.json` — Scored + verified (with score_breakdown)
- `output/verified/{role_type_slug}/_status.json` — Search completion status
- `output/verified/{role_type_slug}/_summary.md` — Results table
- `output/briefs/{company}-{title}-brief.md` — 6-section markdown brief
- `output/briefs/briefs-{run_date}.html` — Compiled styled HTML
- `output/digests/{run_date}-email.html` — Email digest HTML
- `output/digests/_status.json` — Email send status
- `output/session-state.md` — Run checkpoint
- `output/_delta.json` — Daily diff (new/active/expired)
- `output/_source_research.json` — Source discovery results
- `output/_onboarding_draft.json` — Onboarding profile draft

## Patterns Found

### Design System Governance
Single canonical `jsa-design-system.md` skill preloaded by all visual subagents (digest-email, briefs-html). Warm stone/ink palette — no blue anywhere. Fonts: Newsreader (headings), DM Sans (body). Links use ink color with stone underline (editorial, not blue). Score threshold 70 inclusive. HTML only — no PDF. Border-top separators between briefs. Zero-item sections omitted.

### Named Agent Pattern
6 subagents defined in `.claude/agents/*.md` with YAML frontmatter. Each declares: skills to preload, tools available, model (inherit). Variables passed as compact JSON blobs. Status file protocol (`_status.json`) for completion signaling.

### State Architecture
Split state: Git for job data + pipeline state, Upstash Redis for user actions only. `manage_state.py` CLI enforces all mutations — no inline Python. Atomic writes via tempfile. Dashboard reads both sources and merges.

### Error Handling
Auto-retry once via Task tool subagent. Recovery subagent dispatched on partial failure (work done but no status file). Never retry inline in parent context. Never retry more than once per agent per run.

### Checkpoint Strategy
Incremental commit+push after each pipeline stage. Session-state.md written after every search batch (not deferred). State.json updated after sync.

## External Landscape

### Official Doc Patterns
- **Vercel Python**: No configuration required for FastAPI/Flask. Fluid compute enabled by default for new projects (since April 2025). Pre-built deployments (`--prebuilt`) preferred in CI.
- **Upstash Redis Python**: HTTP-based client recommended for serverless. `Redis.from_env()` for auto-loading credentials. Default retry: 1 retry after 3s. Initialize client outside request handler for hot-function reuse.
- **Resend Python SDK**: `resend.Emails.SendParams` dict pattern. Set API key via env var or `resend.api_key`. Type hinting supported.
- **GitHub Actions + Vercel**: `vercel pull` → `vercel build --prod` → `vercel deploy --prebuilt --prod`. Cache pip dependencies with `setup-python` cache option.

### Version Constraints
- **Vercel Functions**: 250 MB unzipped bundle max, 64 KB env var cap per deployment
- **Upstash Redis Python**: `ValueT` only accepts str/int/float/bool — no arbitrary object serialization. JSON serialization for complex values is standard.
- **JobSpy (python-jobspy)**: Latest v0.31.0 (July 2025). SOCKS5 proxy support added. Docker API wrapper available.
- **Resend Python SDK**: Latest v2.21.0 (Jan 2026). SDK 2.0 introduced typed `SendParams` (breaking change from 1.x).

### Community Conventions
- Vercel Python: FastAPI favored for API routes. Pre-built deployments in CI to avoid source code exposure.
- Upstash Redis: Treated as key-value cache for serverless, not full Redis. Pipeline/batch operations reduce HTTP round-trips.
- JobSpy: Docker/API wrappers common for production. Rate limiting + proxy rotation standard for scraping resilience.
- Resend: HTML templates with inline CSS. Tags for tracking/analytics.
- GitHub Actions + Vercel: Separate preview/production deployment jobs. pip caching standard.

### Gaps
- JobSpy 2026-specific breaking changes between 0.25.x and 0.31.0 are sparsely documented
- No Vercel Python cold start benchmarks for 2026
- No Upstash Redis connection pooling guidance for HTTP-based client

## Related Files

### Agent Core
- `03_agents/tests/v17/CLAUDE.md`
- `03_agents/tests/v17/context.md`
- `03_agents/tests/v17/state.json`

### Subagents (6)
- `03_agents/tests/v17/.claude/agents/search-verify.md`
- `03_agents/tests/v17/.claude/agents/brief-generator.md`
- `03_agents/tests/v17/.claude/agents/digest-email.md`
- `03_agents/tests/v17/.claude/agents/briefs-html.md`
- `03_agents/tests/v17/.claude/agents/source-researcher.md`
- `03_agents/tests/v17/.claude/agents/onboarding.md`

### Skills (7)
- `03_agents/tests/v17/.claude/skills/jsa-design-system.md`
- `03_agents/tests/v17/.claude/skills/jsa-digest-email.md`
- `03_agents/tests/v17/.claude/skills/jsa-briefs-html.md`
- `03_agents/tests/v17/.claude/skills/jsa-search-verify.md`
- `03_agents/tests/v17/.claude/skills/jsa-brief-generator.md`
- `03_agents/tests/v17/.claude/skills/jsa-source-researcher.md`
- `03_agents/tests/v17/.claude/skills/jsa-onboarding.md`

### Scripts (6)
- `03_agents/tests/v17/scripts/manage_state.py`
- `03_agents/tests/v17/scripts/jobspy_search.py`
- `03_agents/tests/v17/scripts/filter_jobs.py`
- `03_agents/tests/v17/scripts/summarize_jobs.py`
- `03_agents/tests/v17/scripts/send_email.py`
- `03_agents/tests/v17/scripts/preview.sh`

### API (11)
- `03_agents/tests/v17/api/run.py`
- `03_agents/tests/v17/api/jobs.py`
- `03_agents/tests/v17/api/job.py`
- `03_agents/tests/v17/api/action.py`
- `03_agents/tests/v17/api/context.py`
- `03_agents/tests/v17/api/state.py`
- `03_agents/tests/v17/api/brief.py`
- `03_agents/tests/v17/api/pipeline.py`
- `03_agents/tests/v17/api/_files.py`
- `03_agents/tests/v17/api/_response.py`
- `03_agents/tests/v17/api/_upstash.py`

### Infrastructure
- `03_agents/tests/v17/vercel.json`
- `.github/workflows/jsa-search.yml`
- `03_agents/tests/v17/requirements.txt`

### Cross-Version Memory
- `.claude/decision-log/jsa-v17.md` — 15 decisions (architecture, salary handling, UX, email, state sync, deployment, etc.)
- `.claude/regressions/jsa.md` — 53 regression checks across V14-V17
- `.claude/solutions/` — 6 promoted solutions from V17 compound phase

## Historical Context

V17 was built as an incremental improvement over V16, applying 9 fixes from the V16 analysis while adding a Vercel dashboard as a read-only layer. Key architectural decisions:
- Dashboard is a viewer (reads Git-committed files + Upstash Redis), does not control the pipeline
- Chat interface deferred to V18
- Split state: Git for job data, Upstash Redis for user actions
- Design system governance via single canonical skill
- Incremental commit+push for near-real-time dashboard updates

The V17 build completed all 46 plan steps with 0 regressions, but the interactive session exposed 11 failures (3 critical, 4 major, 4 minor). The compound phase extracted 15 decisions and 6 solutions.

The analysis identified 8 implementation fixes needed — 0 architectural. All failures were infrastructure/configuration issues (Vercel handler pattern, GH Actions workflow location, Redis fallback) or constraint violations (agent memory read, inline Python, post-render regex).

## Handoff Contract
- Files to modify: CLAUDE.md (hard constraints enforcement), scripts/manage_state.py (dedup subcommand), api/_upstash.py (Redis→state.json fallback), vercel.json (if handler pattern issues persist), .github/workflows/jsa-search.yml (settings.local.json creation, smoke test)
- Patterns to preserve: named agent pattern (6 subagents with YAML frontmatter), design system governance (single canonical skill), state architecture (Git + Upstash split), CLI-only state mutations (manage_state.py), auto-retry protocol (once via Task tool), checkpoint strategy (incremental commit+push)
- Hard constraints discovered: Vercel API handlers must use Vercel-compatible pattern (not BaseHTTPRequestHandler); GH Actions workflows must live at repo root `.github/workflows/`; settings.local.json is gitignored — CI must create it; external service dependencies must have local fallbacks; post-render regex must match CSS contexts only (not text substrings); agent must read agent-memory on startup; no inline Python for state mutations
- Open questions: Should V18 transition the dashboard from viewer to orchestrator? Should JobSpy be updated to v0.31.0 (proxy support)? Should Vercel fluid compute be explicitly enabled? Should deployment include a formal smoke test step?

<!-- STAGE COMPLETE: /research full, 2026-02-16 -->

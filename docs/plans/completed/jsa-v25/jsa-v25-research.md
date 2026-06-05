# Research: Career Matching Agent (JSA V25)

## Current State

The Career Matching Agent is a CLI-based multi-subagent system that searches for, verifies, scores, and delivers job opportunities matching a user's profile. It runs as a Claude Code session with a parent orchestrator (Opus) dispatching named subagents across a 5-phase workflow.

### Architecture

**Entry point:** `CLAUDE.md` (parent orchestrator) — receives startup protocol, reads context.md + state.json, runs preflight.sh, then dispatches subagents through the 5-phase workflow.

**7 named agents** (`.claude/agents/*.md`):
- `search-verify.md` (Sonnet) — 5-channel parallel search with scoring and verification
- `brief-generator.md` (Sonnet) — single-job markdown brief generation
- `digest-email.md` (Sonnet) — HTML email digest from verified jobs
- `briefs-html.md` (Sonnet) — compiles briefs into single styled HTML
- `source-researcher.md` (Haiku) — discovers job sources across 5 categories per industry
- `gate-check.md` (Haiku) — mechanical verification gates (schema, dedup, commit, session-state)
- `onboarding.md` (Sonnet) — CV parsing + profile extraction

**7 skills** (`.claude/skills/*.md`):
- `jsa-search-verify` — search + verify + score workflow
- `jsa-brief-generator` — 6-section markdown brief template
- `jsa-digest-email` — email HTML with "New Today" cards + "Still Active" table
- `jsa-briefs-html` — compiled HTML with TOC and styled sections
- `jsa-design-system` — unified visual identity (Newsreader serif + DM Sans, warm stone palette)
- `jsa-onboarding` — CV extraction to structured JSON
- `jsa-source-researcher` — source discovery across 5 categories

**8 scripts** (`scripts/`):
- `preflight.sh` — startup cleanup + dedup
- `manage_state.py` — state sync, dedup, schema validation, checkpoints, dispatch-counter (parent-callable CLI subcommands only)
- `jobspy_search.py` — JobSpy aggregator search (subagent-only)
- `filter_jobs.py` — title exclusion filtering (subagent-only)
- `summarize_jobs.py` — context-efficient job summaries (subagent-only)
- `send_email.py` — email delivery via Resend API (parent-orchestrated)
- `verify_deploy.sh` — deployment verification
- `preview.sh` — HTML preview server (port 8800)

**5 references** (`references/`):
- `orchestration.md` (~38KB) — 5-phase workflow with detailed steps, gates, state architecture
- `subagent-search-verify.md` — search-verify execution logic
- `subagent-digest-email.md` — email digest generation logic
- `algorithms.md` — job matching and scoring algorithms
- `presentation-rules.md` — display/presentation rules for job tables

### 5-Phase Workflow

1. **Onboarding** — Parent Q&A → onboarding subagent writes `_onboarding_draft.json` → parent confirms → writes `context.md`
2. **Source Research** — source-researcher discovers sources → writes to `context.md ## Search Channels`
3. **Phase 1: Search** — dispatch 5 search-verify subagents in parallel → each searches channel, verifies active, scores against profile → writes to `output/verified/{role_type}/` JSONs
4. **Gates** — per-channel commit gates, channel verification, schema validation, dedup gates MUST pass before proceeding
5. **Phase 5: Deliver** — dispatch brief-generator + digest-email + briefs-html → parent runs send_email.py

### Data Flow

- `context.md` — user profile, target roles/industries, search channels, constraints
- `state.json` — persistent job lifecycle (new, active, expired, user actions) across runs
- `session-state.md` — human-readable run log (dispatch budget, search progress, retry log, dedup status)
- `_delta.json` — computed by manage_state.py sync (new_jobs, still_active, expired_count)
- Verified JSONs → `output/verified/{role_type_slug}/{company_slug}-{title_slug}.json`
- Status files → `output/verified/{role_type_slug}/_status.json`
- Summaries → `output/verified/{role_type_slug}/_summary.md`
- Briefs → `output/briefs/briefs-{run_date}.html`
- Digests → `output/digests/{run_date}-email.html`

### Verified Job JSON Schema (Canonical)

10 required fields + scoring breakdown:
- `title`, `company`, `location`, `job_type`, `work_arrangement`
- `salary_min`, `salary_max`, `currency`
- `job_url` (must be direct ATS link), `source`, `date_posted`
- `active_status` (boolean, non-null after verification)
- `industry`, `requirements_met[]`, `gaps[]`, `preferred_met[]`
- `score` (integer 0-100), `score_breakdown` (required_skills/40, preferred_skills/20, experience/15, industry/15, location/10, salary_penalty/-10)
- `benefits[]`, `notes`, `run_date`, `verified_at`

Scoring: 40 required + 20 preferred + 15 experience + 15 industry + 10 location = /100, optional -10 salary penalty. Threshold: >=70 for presentation.

### External Integrations

1. **Resend** — email delivery via `scripts/send_email.py`, `RESEND_API_KEY` from .env
2. **Upstash Redis** — action tracking (`api/_upstash.py`), keys `action:{job_key}`, fallback to state.json
3. **JobSpy** — aggregator for Indeed/LinkedIn/Glassdoor/ZipRecruiter via `scripts/jobspy_search.py`
4. **Vercel** — dashboard deployment, URL stored in `context.md ## Delivery`
5. **GitHub Actions** — scheduled runs via `claude-code-action@v1`

### Model Tier Enforcement

- Opus: parent orchestrator only
- Sonnet: search-verify, brief-generator, digest-email, briefs-html, onboarding (writing/reasoning)
- Haiku: source-researcher, gate-check (mechanical/discovery tasks)

### Hard Constraints (from CLAUDE.md)

- HC1: Pass `model:` to Task matching agent's tier
- HC4: Read agent memory on startup; treat failures as hard constraints
- HC5: Never execute Python in parent except preflight.sh, manage_state.py CLI, send_email.py
- HC7: Incremental commit+push after every search batch
- HC10: Every subagent dispatch includes `working_dir`, `output_directory`, `dashboard_url`
- DISPATCH_CEILING: 25 max subagent dispatches per session
- Phase 1: ALL 5 search channels MANDATORY
- Gates: schema-validation, channel-verification, dedup gates must pass before proceeding

### Agent Memory

- `search-verify/MEMORY.md` — 1000+ lines documenting source effectiveness, search patterns, company findings, channel success rates, re-verification results
- `brief-generator/MEMORY.md` — brand voice, design system enforcement
- `digest-email/MEMORY.md` — email design patterns, subject lines
- `briefs-html/MEMORY.md` — HTML compilation, CSS, navigation

## Code References

- `CLAUDE.md` — parent orchestrator, startup protocol, hard constraints
- `.claude/agents/*.md` — 7 named agent definitions with YAML frontmatter
- `.claude/skills/*.md` — 7 skill definitions
- `references/orchestration.md` — 5-phase workflow (~38KB)
- `references/subagent-search-verify.md` — search-verify execution logic
- `references/subagent-digest-email.md` — email digest generation logic
- `references/algorithms.md` — scoring algorithms
- `references/presentation-rules.md` — display rules
- `scripts/manage_state.py` — state management CLI
- `scripts/jobspy_search.py` — JobSpy aggregator
- `scripts/send_email.py` — email delivery
- `scripts/preflight.sh` — startup cleanup
- `context.md` — user profile and search channels
- `state.json` — persistent job lifecycle
- `api/_upstash.py` — Redis integration
- `api/state.py` — API state endpoint

## Patterns Found

- Named agent pattern with YAML frontmatter (v13 standard)
- Status file protocol (`_status.json`) for completion signaling
- Gate-check as mandatory blocking prerequisite between phases
- Canonical 10-field JSON schema with normalize-on-write strategy
- Design system skill as CSS source of truth (shared across email + briefs)
- Dedup safety bounds (abort if >50% would be archived)
- Session-state checkpoint after every search batch
- Background dispatch with `background: true` for all subagents
- Agent Decomposition Pattern — CLAUDE.md as compact orchestrator, detailed content in `references/`

## External Landscape

- **Greenhouse Harvest API v1/v2**: deprecated after August 31, 2026 — any validation logic using Harvest endpoints must migrate
- **Ashby API**: errors return HTTP 200 with `success: false` in body — URL validation must check response body, not just status codes
- **Lever**: public API for job retrieval, no auth required. URL pattern: `jobs.lever.co/{company}/{jobId}`
- **python-jobspy**: stable at v1.1.82, no breaking changes detected since Feb 2026
- **Resend**: SDK 2.0 stable, Broadcast API for single-request send, webhooks fully programmable
- **Claude Agent SDK**: Python v0.1.48, TypeScript v0.2.71. Agent Teams experimental (multi-instance coordination)
- **ATS integration trend**: Unified API services (unified.to) emerging for multi-ATS integration vs per-vendor
- **Job search automation 2026**: consensus is quality-over-volume — intelligent filtering over mass-apply

## Related Files

- `03_agents/career-matching/` — agent source (git submodule)
- `03_agents/tests/v25/` — test infrastructure and output data
- `.claude/regressions/jsa.md` — 184 regression items across V14-V25
- `.claude/decision-log/jsa-v17.md` through `jsa-v24.md` — 8 versions of decision logs
- `.claude/research-patterns/job-search.md` — external research patterns
- `.claude/research-patterns/job-search-automation.md` — detailed technology patterns
- `.claude/project-profiles/jsa.md` — project profile (type: cli-agent)
- `docs/plans/completed/jsa-v24/` — V24 artifacts

## Historical Context

V25 was a 31-step, 3-phase build (Infrastructure → Orchestration → UX) with 260 tests. The V25 analysis identified 18 failures (2 critical, 7 major, 9 minor) across three themes:

1. **URL data integrity** — generic URLs presented instead of direct ATS links, false expired claims without visiting URLs, aggregator-based verification unreliable
2. **Subagent coordination** — .done sentinel files written to wrong directory (5th occurrence), JobSpy not run, active_status=None after verification
3. **Recurring constraint violations** — agent memory not read on startup (6th occurrence), parent inline Python (6th occurrence), context budget breaches

The analysis identified 2 architectural fixes (verify-before-removal gate, source-first liveness verification) and 12 implementation fixes.

Key regression patterns across versions:
- Incremental commit+push skipped: 9 consecutive versions (V14-V24)
- Session-state.md not written after search batch: 10 consecutive versions
- Agent memory not read on startup: 6 occurrences
- .done sentinel files written to wrong path: 5 occurrences
- Parent inline Python violations: 6 occurrences

## Handoff Contract
- Files to modify: CLAUDE.md, agents/*.md, skills/*.md, scripts/, references/, tests/
- Patterns to preserve: 5-phase workflow, named agent pattern with YAML frontmatter, status file protocol, canonical 10-field schema, design system skill as CSS source of truth, gate-check blocking semantics, dedup safety bounds, agent memory persistence, Agent Decomposition Pattern
- Hard constraints discovered: 11 absolute constraints in CLAUDE.md, parent context budget (no subagent-only ops), incremental commit+push after search batches, settings.local.json merge protocol, all subagents background:true, model tier enforcement (Sonnet for writing/reasoning, Haiku for mechanical), Greenhouse Harvest API deprecation Aug 2026
- Open questions: (1) Should commit+push and session-state enforcement become structural gates with script-level blocking? (9-10th recurrences), (2) How to implement verify-before-removal gate (AF1 from analysis)?, (3) How to implement source-first liveness verification replacing aggregator-based checks (AF2)?, (4) Should foreground/background dispatch contradiction be resolved to foreground-only given 5+ versions of sentinel-path failures?, (5) How to prevent parent from falling back to inline Python on subagent truncation?

<!-- STAGE COMPLETE: /research full, 2026-03-23 -->

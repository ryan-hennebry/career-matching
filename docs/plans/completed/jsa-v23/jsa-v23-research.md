# Research: Job Search Agent V23

## Current State

V23 is a Claude Code CLI agent that automates job search, verification, scoring, briefing, and digest delivery for startup generalist roles. It operates through a 5-phase orchestration pipeline (Search → Verify → Dedup → Present → Deliver) with 7 named subagents dispatched via the Task tool with explicit model tiering.

### Architecture Overview

The agent uses a three-layer architecture:

1. **Scripts layer** (`scripts/`): 7 Python/bash scripts handle data processing, state management, email sending, HTML verification, and job filtering. The central script `manage_state.py` provides 12 CLI subcommands for state lifecycle, dedup, checkpointing, and gate verification.

2. **Orchestration + Config layer** (`CLAUDE.md` + `references/` + `context.md`): The parent orchestrator (249-line CLAUDE.md) reads configuration from `context.md` (user profile, target roles, industries, constraints, sources) and dispatches subagents per the 5-phase workflow defined in `references/orchestration.md`.

3. **Validation layer** (gate-check agent + `manage_state.py` subcommands): Structural enforcement via checkpoint gating, per-channel commit gates, session-state verification, and channel dispatch confirmation.

### Execution Flow

**Startup:** `preflight.sh` → run date capture → agent memory load (assertion: >0 files) → `state.json` load → `context.md` read → dashboard URL validation.

**Phase 1 (Search):** Checkpoint clear → pre-search cleanup (archive non-active role-type dirs) → source research gate (if channels empty) → dispatch 5 search-verify channels in parallel (direct-career-pages, industry-job-boards, jobspy-aggregator, niche-newsletters, web-search-discovery) → per-channel commit gates → channel verification gate → cross-role dedup.

**Phase 2 (Verify):** Integrated into search-verify subagent: fetch job page → verify active → extract fields → score with 5-factor model (required/preferred/experience/industry/location) → write verified JSON.

**Phase 3 (Dedup):** `manage_state.py dedup --role-types $ACTIVE` → `manage_state.py sync` (compute delta) → checkpoint write.

**Phase 4 (Present):** Display tables per role type (New Today / Still Active subsections) → dashboard URL verification → collect user selections via `record-action` CLI.

**Phase 5 (Deliver):** Idempotency gate (check `_status.json` for today's `sent_at`) → dispatch brief-generator per job → dispatch digest-email + briefs-html in parallel → post-render verification → commit+push → send email via parent → update `_status.json`.

### Model Tiering (V23 Innovation)

- **Opus:** Parent orchestrator only (orchestration decisions, user interaction)
- **Sonnet:** Brief-generator, digest-email, briefs-html, onboarding (writing quality)
- **Haiku:** Search-verify, source-researcher, gate-check (mechanical work)

HC1 enforces: parent MUST pass `model:` parameter to Task tool matching each agent's declared tier.

### Hard Constraints (10 Rules)

1. Pass `model:` to Task tool matching agent tier (ENFORCED)
2. Design system CSS canonical in skill (no inline copies)
3. No PDF output — HTML only
4. Read agent memory MEMORY.md files on startup, treat as hard constraints
5. Never execute Python in parent except: send_email.py, manage_state.py CLI, preflight.sh
6. Never give UI feature instructions unless 100% certain
7. Incremental commit+push after every search batch
8. settings.local.json: merge into existing array, never overwrite
9. API keys: environment variables or stdin only, never CLI args
10. Every subagent dispatch: working_dir, output_directory, dashboard_url explicit

Additional critical rules: read-before-write on session-state.md, post-dispatch directory verification.

## Code References

### CLAUDE.md & Configuration
- `03_agents/tests/v23/CLAUDE.md` — 249 lines. Hard constraints (7-21), model tiers (25-38), context budget (41-66), core rules (70-86), phases (109-203)
- `03_agents/tests/v23/context.md` — User profile, target roles, industries, constraints, search channels, delivery config

### References
- `03_agents/tests/v23/references/orchestration.md` — 5-phase workflow with gates, checkpoints, commit protocol, pre-search cleanup, idempotency rules
- `03_agents/tests/v23/references/algorithms.md` — Skill normalization, experience level mapping, scoring edge cases, dedup rules (80% title similarity)
- `03_agents/tests/v23/references/presentation-rules.md` — Table format, 70+ threshold, subsections, footnote pattern
- `03_agents/tests/v23/references/subagent-search-verify.md` — 15-variable JSON blob, budget enforcement (15min/50 calls), scoring rubric
- `03_agents/tests/v23/references/subagent-digest-email.md` — 9 variables, idempotent gate, zero-section omission, dashboard URL mandatory

### Agents (7)
- `03_agents/tests/v23/.claude/agents/search-verify.md` — Haiku, skill: jsa-search-verify
- `03_agents/tests/v23/.claude/agents/brief-generator.md` — Sonnet, skill: jsa-brief-generator
- `03_agents/tests/v23/.claude/agents/digest-email.md` — Sonnet, skills: jsa-design-system, jsa-digest-email
- `03_agents/tests/v23/.claude/agents/briefs-html.md` — Sonnet, skills: jsa-design-system, jsa-briefs-html
- `03_agents/tests/v23/.claude/agents/onboarding.md` — Sonnet, skill: jsa-onboarding
- `03_agents/tests/v23/.claude/agents/source-researcher.md` — Haiku, skill: jsa-source-researcher
- `03_agents/tests/v23/.claude/agents/gate-check.md` — Haiku, no skills

### Skills (7)
- `03_agents/tests/v23/.claude/skills/jsa-design-system.md` — Unified design system (fonts, colors, spacing)
- `03_agents/tests/v23/.claude/skills/jsa-digest-email.md` — Email digest rendering structure
- `03_agents/tests/v23/.claude/skills/jsa-briefs-html.md` — Briefs HTML compilation (cover page, TOC, separators)
- `03_agents/tests/v23/.claude/skills/jsa-brief-generator.md` — 6-section brief structure, 300-500 words, <60s target
- `03_agents/tests/v23/.claude/skills/jsa-search-verify.md` — 5-step verification, skill normalization, 120s per-job
- `03_agents/tests/v23/.claude/skills/jsa-onboarding.md` — CV parsing, experience level mapping, derived fields
- `03_agents/tests/v23/.claude/skills/jsa-source-researcher.md` — 5-category source discovery

### Scripts (7)
- `03_agents/tests/v23/scripts/manage_state.py` — 12 CLI subcommands: sync, record-action, cleanup, dedup, checkpoint, list-active-role-types, verify-clean-working-tree, verify-channels-dispatched, verify-session-state-updated, check-session-resume, check-model-settings, check-dashboard-url
- `03_agents/tests/v23/scripts/jobspy_search.py` — JobSpy wrapper (Indeed, LinkedIn, Glassdoor), 25 results/site default
- `03_agents/tests/v23/scripts/filter_jobs.py` — Title-based exclusion filtering
- `03_agents/tests/v23/scripts/summarize_jobs.py` — One-line job summaries for context reduction
- `03_agents/tests/v23/scripts/send_email.py` — Resend API email sender (`--to`, `--subject`, `--body-file`, `--attachment`)
- `03_agents/tests/v23/scripts/verify_html.py` — HTML color lint (prohibited: blue, red, orange, amber + 40 hex codes)
- `03_agents/tests/v23/scripts/preflight.sh` — Startup validation (env + structure tiers)

### Tests (11 modules)
- `03_agents/tests/v23/tests/test_manage_state.py` — State lifecycle (expiry, dedup, sync, serialization)
- `03_agents/tests/v23/tests/test_manage_state_dedup.py` — Dedup focus (same-URL, cross-role, role-type filtering)
- `03_agents/tests/v23/tests/test_manage_state_preflight.py` — Preflight startup checks
- `03_agents/tests/v23/tests/test_preflight.py` — Comprehensive preflight (11 tests)
- `03_agents/tests/v23/tests/test_workflow.py` — GitHub Actions workflow structural assertions
- `03_agents/tests/v23/tests/test_filter_jobs.py` — Title filtering logic
- `03_agents/tests/v23/tests/test_salary_penalty.py` — Salary mismatch scoring
- `03_agents/tests/v23/tests/test_dashboard_frontend.py` — Dashboard SPA assertions
- `03_agents/tests/v23/tests/test_verify_html.py` — HTML color linting
- `03_agents/tests/v23/tests/test_summarize_jobs.py` — Summary generation
- `03_agents/tests/v23/tests/test_claude_md.py` — CLAUDE.md constraints validation

### State & Output
- `03_agents/tests/v23/state.json` — Job lifecycle tracking (JobEntry schema, EXPIRY_DAYS=14, PURGE_DAYS=90)
- `03_agents/tests/v23/output/verified/{role_type}/` — Verified job JSONs + _status.json + _summary.md
- `03_agents/tests/v23/output/digests/` — Email HTML + _status.json
- `03_agents/tests/v23/output/briefs/` — Brief markdown + compiled HTML + _status.json
- `03_agents/tests/v23/output/_delta.json` — Run delta (new_jobs, still_active, expired_count)
- `03_agents/tests/v23/output/session-state.md` — Human-readable run log
- `03_agents/tests/v23/output/.checkpoints/` — Phase completion markers

### External Integrations
- **Resend:** Email API via `send_email.py`, auth: RESEND_API_KEY env var, sender: onboarding@resend.dev
- **Vercel:** Dashboard at jsa-dashboard.vercel.app, API handlers in `api/*.py` (8 endpoints: jobs, run, state, context, briefs, action, pipeline, brief/{job_key})
- **Upstash Redis:** User action persistence, auth: UPSTASH_REDIS_REST_URL + TOKEN, fallback to state.json
- **JobSpy:** Job board scraper via `jobspy_search.py`, scrapes Indeed/LinkedIn/Glassdoor
- **GitHub Actions:** `.github/workflows/daily-digest.yml`, scheduled cron trigger

### Dependencies
- Python: `upstash-redis>=1.0.0`, `markdown>=3.5`, `python-jobspy` (pip), `resend` (pip)
- System: bash, python3, git, curl, vercel CLI

## Patterns Found

### Orchestration Patterns
- **Three-layer architecture:** Scripts (data) → Orchestration+Config (flow) → Validation (gates)
- **5-channel mandatory search:** All channels dispatch in parallel every run, content adapts to user context
- **Per-channel commit gates:** Sequential gate-check after each channel completes (prevents lost progress)
- **Checkpoint gating:** Phase N validates Phase N-1 checkpoint before proceeding
- **Idempotency guard:** Email delivery checks `_status.json` `sent_at` field before sending

### Data Patterns
- **Multi-schema score handling:** `_extract_score()` handles 4 JSON schemas (score int, scoring.total_score, score_breakdown.total, score dict) — this is a known failure source
- **Dedup dual-stage:** Cross-role by (company.lower(), title.lower()), then same-URL within role, then score threshold filter
- **State lifecycle:** new → active → expired (14 days) → purged (90 days)
- **Delta computation:** `manage_state.py sync` produces `_delta.json` classifying jobs as new/still-active/expired

### Agent Dispatch Patterns
- **15-variable JSON blob** passed to search-verify subagents (role_type_slug, skills, experience_years, salary_min, location_prefs, country, remote_pref, exclude_titles, sources_for_role, run_date, working_dir, output_directory, dashboard_url, model, role_types)
- **Status file protocol:** Each subagent writes `_status.json` on completion for parent verification
- **Recovery protocol:** On subagent failure, dispatch recovery subagent (never fix in parent)
- **Auto-retry protocol:** Max 2 total attempts per subagent (dispatch + 1 retry)

### Design System
- **Fonts:** Newsreader serif headings, DM Sans body
- **Colors:** Green badges (90+: #15803d on #f0fdf4), stone badges (70-89: #1c1917 on #f8f8f6), dark editorial links (#1c1917)
- **No PDF:** HTML-only output, viewed in browser, border-top separators between briefs

## External Landscape

### python-jobspy
- Stable at v1.1.82 (July 2025). No new releases detected. May be in maintenance mode.
- Python >=3.10, <4.0. Bayt/Naukri boards added since last documented.

### Claude Code CLI (February 2026)
- **Agent Teams (research preview):** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` enables multi-instance coordination with inbox-based messaging. Potential future replacement for current subagent dispatch.
- **Background agent pre-prompting:** Permissions now requested before launch (not mid-execution). Addresses the V20 "background subagents denied" regression.
- **Ctrl+B backgrounding:** Send running task to background mid-execution.
- **Tiered permission system:** Allow/Ask/Deny configurable per-tool in settings.local.json.

### Resend API
- Broadcast API single-request send (Feb 12, 2026).
- Self-hosted webhook storage (Jan 26, 2026).
- Bulk dashboard actions (Jan 15, 2026).
- Email scheduling up to 30 days in advance.
- SDK 2.0 stable, Batch Idempotency Keys, Automatic Plain Text generation.

### Schema Validation (Pydantic v2)
- Pydantic v2.11 with Rust-backed validation (5-50x performance over v1).
- `TypeAdapter` reuse, strict unions with discriminators for polymorphic schemas.
- `model_validate_json()` for direct JSON-to-model (skips dict intermediary).
- `@model_validator` for cross-field invariants, `@field_validator(mode="before")` for normalizing scraper output.
- Recommended for enforcing canonical verified JSON schema across all channels.

### Structural Enforcement
- Pre-execution assertion gates: validate preconditions before each pipeline stage, fail-fast.
- Machine-speed circuit breakers for autonomous agents (cost runaway, empty results, stale data).
- Configurable thresholds: >3 consecutive failures = circuit open, hard time/cost budget stop.
- Runtime invariant monitoring: continuous checks during execution (not just at boundaries).

### Gaps
- No external patterns for Claude Code CLI `--print` scheduled runs.
- No community conventions for tiered model assignment in Claude Code subagent dispatch.
- No established pattern for graceful stale-data detection during rate limits.

## Related Files

### Core
- `03_agents/tests/v23/CLAUDE.md`
- `03_agents/tests/v23/context.md`
- `03_agents/tests/v23/state.json`
- `03_agents/tests/v23/requirements.txt`

### References
- `03_agents/tests/v23/references/orchestration.md`
- `03_agents/tests/v23/references/algorithms.md`
- `03_agents/tests/v23/references/presentation-rules.md`
- `03_agents/tests/v23/references/subagent-search-verify.md`
- `03_agents/tests/v23/references/subagent-digest-email.md`

### Agents
- `03_agents/tests/v23/.claude/agents/search-verify.md`
- `03_agents/tests/v23/.claude/agents/brief-generator.md`
- `03_agents/tests/v23/.claude/agents/digest-email.md`
- `03_agents/tests/v23/.claude/agents/briefs-html.md`
- `03_agents/tests/v23/.claude/agents/onboarding.md`
- `03_agents/tests/v23/.claude/agents/source-researcher.md`
- `03_agents/tests/v23/.claude/agents/gate-check.md`

### Skills
- `03_agents/tests/v23/.claude/skills/jsa-design-system.md`
- `03_agents/tests/v23/.claude/skills/jsa-digest-email.md`
- `03_agents/tests/v23/.claude/skills/jsa-briefs-html.md`
- `03_agents/tests/v23/.claude/skills/jsa-brief-generator.md`
- `03_agents/tests/v23/.claude/skills/jsa-search-verify.md`
- `03_agents/tests/v23/.claude/skills/jsa-onboarding.md`
- `03_agents/tests/v23/.claude/skills/jsa-source-researcher.md`

### Scripts
- `03_agents/tests/v23/scripts/manage_state.py`
- `03_agents/tests/v23/scripts/jobspy_search.py`
- `03_agents/tests/v23/scripts/filter_jobs.py`
- `03_agents/tests/v23/scripts/summarize_jobs.py`
- `03_agents/tests/v23/scripts/send_email.py`
- `03_agents/tests/v23/scripts/verify_html.py`
- `03_agents/tests/v23/scripts/preflight.sh`

### Tests
- `03_agents/tests/v23/tests/test_manage_state.py`
- `03_agents/tests/v23/tests/test_manage_state_dedup.py`
- `03_agents/tests/v23/tests/test_manage_state_preflight.py`
- `03_agents/tests/v23/tests/test_preflight.py`
- `03_agents/tests/v23/tests/test_workflow.py`
- `03_agents/tests/v23/tests/test_filter_jobs.py`
- `03_agents/tests/v23/tests/test_salary_penalty.py`
- `03_agents/tests/v23/tests/test_dashboard_frontend.py`
- `03_agents/tests/v23/tests/test_verify_html.py`
- `03_agents/tests/v23/tests/test_summarize_jobs.py`
- `03_agents/tests/v23/tests/test_claude_md.py`

### API Handlers (Vercel)
- `03_agents/tests/v23/api/jobs.py`
- `03_agents/tests/v23/api/run.py`
- `03_agents/tests/v23/api/state.py`
- `03_agents/tests/v23/api/context.py`
- `03_agents/tests/v23/api/briefs.py`
- `03_agents/tests/v23/api/action.py`
- `03_agents/tests/v23/api/pipeline.py`
- `03_agents/tests/v23/api/brief/[job_key].py`

### State & Output
- `03_agents/tests/v23/output/verified/` — Per-role-type verified jobs
- `03_agents/tests/v23/output/digests/` — Email HTML
- `03_agents/tests/v23/output/briefs/` — Brief markdown + HTML
- `03_agents/tests/v23/output/_delta.json`
- `03_agents/tests/v23/output/session-state.md`
- `03_agents/tests/v23/output/.checkpoints/`

## Historical Context

V23 is the result of 16 prior iterations (V8-V22). Key evolution:

- **V8-V11:** Single-agent → subagent orchestration, CLAUDE.md rewrite
- **V12-V13:** Named agent pattern, compact JSON dispatch, design system skill
- **V14-V17:** Regression tracking, deployment fixes (Vercel, GitHub Actions), context budget enforcement
- **V18-V19:** Background subagent failures discovered, cross-role dedup normalization
- **V20-V21:** Pre-run cleanup, session-state enforcement (5+ recurrences), rate limit recovery
- **V22:** Checkpoint-driven architecture validated (43% failure reduction), but cost ($4.09/run), dedup context-awareness, and search breadth remained unresolved
- **V23:** Three-layer architecture, model tiering (HC1 reversal), 5-channel mandatory search, context-aware dedup, per-channel commit gates, gate-check agent

V23 analysis found 20 failures (5 Critical, 9 Medium, 6 minor). Key recurring issues: background subagent permissions (8th version), session-state checkpoint (9th occurrence), incremental commit+push (8th occurrence), and a new schema inconsistency cascade affecting 4 downstream systems.

143 regression items tracked across V14-V23 in `.claude/regressions/jsa.md`.

## Handoff Contract

- **Files to modify:** CLAUDE.md, references/orchestration.md, references/subagent-search-verify.md, scripts/manage_state.py, .claude/agents/*.md, .claude/skills/jsa-search-verify.md, tests/ (multiple)
- **Patterns to preserve:** Three-layer architecture, 5-channel mandatory search, checkpoint gating, model tiering (Opus/Sonnet/Haiku), status file protocol, design system canonicity
- **Hard constraints discovered:**
  1. HC1: model tier enforcement via `model:` parameter on Task tool
  2. HC2: Design system CSS canonical in skill only
  3. HC3: No PDF — HTML only
  4. HC4: Agent memory read on startup (assertion)
  5. HC5: No Python execution in parent except send_email.py, manage_state.py, preflight.sh
  6. HC7: Incremental commit+push after every search batch
  7. HC8: settings.local.json merge-only (never overwrite)
  8. HC9: API keys via env vars or stdin only
  9. HC10: working_dir, output_directory, dashboard_url explicit on every dispatch
  10. Verified JSON schema inconsistency across channels is the root cause of 4 downstream failures
- **Open questions:**
  1. Should background subagent dispatch be removed entirely (foreground-only mandate) given 8 versions of permission failures?
  2. Should Pydantic v2 be adopted for canonical verified JSON schema enforcement, or is a simpler jsonschema validation sufficient?
  3. Should Claude Code Agent Teams (experimental) be investigated as an alternative to current Task tool dispatch?
  4. Should scoring be moved from Haiku to Sonnet tier (Haiku scored barista/data scientist at 95-100)?
  5. What is the right architecture for scheduled runs — Claude Code Action v1, Agent Teams, or a Python script orchestrator?

<!-- STAGE COMPLETE: /research [full], 2026-02-25 -->

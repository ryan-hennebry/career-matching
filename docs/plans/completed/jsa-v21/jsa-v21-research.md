# Research: JSA V21 Job Search Agent

## Current State

JSA V21 is a Claude Code subagent-based job search automation system at `03_agents/tests/v21/`. It runs a 5-phase pipeline (Search → Verify → Dedup → Present → Deliver) orchestrated by a parent CLAUDE.md file that dispatches named subagents via the Task tool. The system searches specialty job boards (Web3.Career, CryptocurrencyJobs, BeInCrypto, AI Jobs) and mainstream aggregators (via python-jobspy), scores listings against a user profile, generates HTML briefs and digest emails, and delivers via Resend API.

V21 introduced a 3-layer architecture (Code Infrastructure → Constraint Promotion → Validation Harness) with a preflight.sh validation script (244 lines, 101 tests passing). The build completed 22/22 steps. Post-build analysis identified 14 failures (4 critical, 4 medium, 6 minor) and 8 constraint violations.

### Entry Point

`03_agents/tests/v21/CLAUDE.md:73-87` — Startup sequence: run preflight.sh, capture run date, read agent memory, load state.json, read context.md, check profile existence, validate dashboard URL.

### Pipeline Phases

| Phase | Purpose | Agents | Outputs |
|-------|---------|--------|---------|
| 1. Search | Discover jobs from sources | search-verify (batched 2-3), source-researcher (optional) | `output/jobs/{role_type}-aggregator.json`, `output/verified/{role_type}/*.json` |
| 2. Verify | Score and validate listings | search-verify (internal) | `output/verified/{role_type}/_status.json`, `_summary.md` |
| 3. Dedup | Cross-role deduplication | Parent via manage_state.py | Updated `state.json`, `output/_delta.json` |
| 4. Present | Show results, collect feedback | Parent (reads summaries, displays tables) | User selections via `manage_state.py record-action` |
| 5. Deliver | Generate briefs + digest email | brief-generator (parallel), digest-email, briefs-html | `output/briefs/*.md`, `output/briefs/briefs-{date}.html`, `output/digests/{date}-email.html` |

### Named Agents

| Agent | File | Tools | Skills | Purpose |
|-------|------|-------|--------|---------|
| search-verify | `.claude/agents/search-verify.md` | Bash/Read/Write/Glob/Grep/WebFetch/WebSearch | jsa-search-verify | Execute jobspy_search.py, filter, verify, score listings |
| source-researcher | `.claude/agents/source-researcher.md` | Bash/Read/Write/Glob/Grep/WebFetch/WebSearch | jsa-source-researcher | Discover high-quality job sources |
| brief-generator | `.claude/agents/brief-generator.md` | Bash/Read/Write/Glob/Grep | jsa-brief-generator | Generate narrative markdown briefs from verified JSON |
| digest-email | `.claude/agents/digest-email.md` | Bash/Read/Write/Glob/Grep | jsa-design-system, jsa-digest-email | Generate HTML email body with job cards |
| briefs-html | `.claude/agents/briefs-html.md` | Bash/Read/Write/Glob/Grep | jsa-design-system, jsa-briefs-html | Compile briefs into single styled HTML |
| onboarding | `.claude/agents/onboarding.md` | Bash/Read/Write/Glob/Grep/WebFetch/WebSearch | jsa-onboarding | Parse CV, extract user profile |

### Skills Inventory

| Skill | File | Purpose |
|-------|------|---------|
| jsa-design-system | `.claude/skills/jsa-design-system.md` | Shared HTML/CSS tokens — Newsreader + DM Sans fonts, warm neutral palette, score badges, layout rules |
| jsa-digest-email | `.claude/skills/jsa-digest-email.md` | Email HTML template — header, summary strip, job cards, still-active table, footer |
| jsa-briefs-html | `.claude/skills/jsa-briefs-html.md` | Briefs compilation — cover page with TOC, brief sections, anchor navigation |
| jsa-search-verify | `.claude/skills/jsa-search-verify.md` | Search algorithms — jobspy integration, filtering, 5-factor scoring model |
| jsa-source-researcher | `.claude/skills/jsa-source-researcher.md` | Source discovery strategy per industry/role |
| jsa-brief-generator | `.claude/skills/jsa-brief-generator.md` | Brief narrative — requirement matching, fit analysis |
| jsa-onboarding | `.claude/skills/jsa-onboarding.md` | CV parsing, profile extraction schema |

### Design System

- Fonts: Newsreader (serif, headings) + DM Sans (sans-serif, body). Fallbacks: Georgia/Times, Helvetica/Arial.
- Colors: `#ffffff` bg, `#f8f8f6` subtle bg, `#f0efeb` inset, `#1c1917` text-primary, `#57534e` text-secondary, `#a8a29e` text-tertiary, `#e7e5e4` border, `#d6d3d1` border-strong.
- Score badges: Green (`#15803d` on `#f0fdf4`) for 90+, stone (`#1c1917` on `#f8f8f6`) for 70-89.
- Email: 600px max-width, 32px/24px padding. Inline-styled HTML (no external CSS). Gmail override block in `<style>`.
- Briefs: 800px max-width, 48px/56px padding. Border-top separators between briefs (no page breaks).

## Code References

- `03_agents/tests/v21/CLAUDE.md:1-234` — Parent orchestrator (280 lines target, phases, hard constraints, dispatch rules)
- `03_agents/tests/v21/CLAUDE.md:73-87` — Startup sequence (preflight, state load, context read)
- `03_agents/tests/v21/.claude/agents/search-verify.md` — Search-verify agent definition
- `03_agents/tests/v21/.claude/agents/source-researcher.md` — Source researcher agent definition
- `03_agents/tests/v21/.claude/agents/brief-generator.md` — Brief generator agent definition
- `03_agents/tests/v21/.claude/agents/digest-email.md` — Digest email agent definition
- `03_agents/tests/v21/.claude/agents/briefs-html.md` — Briefs HTML agent definition
- `03_agents/tests/v21/.claude/agents/onboarding.md` — Onboarding agent definition
- `03_agents/tests/v21/.claude/skills/jsa-design-system.md` — Design system (620+ lines)
- `03_agents/tests/v21/.claude/skills/jsa-digest-email.md` — Email template skill
- `03_agents/tests/v21/.claude/skills/jsa-briefs-html.md` — Briefs compilation skill
- `03_agents/tests/v21/scripts/preflight.sh` — Validation harness (244 lines, ENV + STRUCTURE tiers)
- `03_agents/tests/v21/scripts/manage_state.py` — State lifecycle (sync, dedup, cleanup, record-action)
- `03_agents/tests/v21/scripts/jobspy_search.py` — JobSpy aggregation wrapper
- `03_agents/tests/v21/scripts/filter_jobs.py` — Title exclusion filter
- `03_agents/tests/v21/scripts/summarize_jobs.py` — Context-efficient job summaries
- `03_agents/tests/v21/scripts/send_email.py` — Resend API email delivery
- `03_agents/tests/v21/scripts/verify_html.py` — HTML validation
- `03_agents/tests/v21/scripts/export_transcript.py` — Session transcript export (new, untracked)
- `03_agents/tests/v21/state.json` — Master job lifecycle (94 jobs, 6 role types)
- `03_agents/tests/v21/context.md` — User profile, constraints, sources, delivery config
- `03_agents/tests/v21/.claude/settings.local.json` — Permissions (86-entry allow list)
- `03_agents/tests/v21/output/_delta.json` — Daily incremental job changes
- `03_agents/tests/v21/output/session-state.md` — Run checkpoint log
- `03_agents/tests/v21/api/*.py` — Vercel serverless functions (run, job, brief, action, jobs, context, pipeline, state)
- `03_agents/tests/v21/vercel.json` — Vercel config (rewrites, maxDuration: 10s)
- `.github/workflows/daily-digest.yml` — Root workflow (hardcoded to v20, stale)

## Patterns Found

### Orchestration
- Parent dispatches subagents via Task tool with compact JSON blobs (15 variables for search-verify, 9 for digest-email)
- Subagents write status files (`_status.json`) + summaries (`_summary.md`) — parent reads ONLY these
- Checkpoint discipline: `output/session-state.md` after every batch, commits+pushes after Phase 1/3/5
- Idempotency gate (Phase 5): checks if email `sent_at` exists for today's run_date
- Auto-retry: first failure retries once as subagent dispatch, second failure logs + continues

### State Management
- `state.json` tracks job lifecycle: new/active/expired/rejected per run_date
- 14-day expiry for jobs, reappearance tracking
- `_delta.json` recomputed by `manage_state.py sync` for daily changes
- User actions recorded via `manage_state.py record-action`

### Validation
- `preflight.sh` runs ENV tier (dashboard URL, settings.local.json permissions, jsa-config.json) + STRUCTURE tier (CLAUDE.md format, phase dispatch table, references)
- 101 tests passing at build completion

### Hard Constraints (from CLAUDE.md)
- No `model:` param to Task (always uses default opus)
- CSS only from design-system skill
- No PDF output
- Read agent memory on startup
- No Python in parent except send_email/manage_state/preflight
- Never execute subagent-only ops in parent (WebFetch, WebSearch)
- Incremental commit+push after search/delivery phases

## External Landscape

### python-jobspy
- v1.1.82 (July 2025). Python >=3.10, <4.0. Python 3.13 supported.
- New boards since last documented: Bayt, Naukri
- Community: JobSpy MCP Server (FastMCP-based) wraps jobspy behind MCP protocol — potential alternative to Python subprocess pattern
- Community: Dockerized JobSpy API (rainmanjam/jobspy-api) — FastAPI with auth/rate-limiting

### resend-python
- SDK 2.0 stable since June 2024, no breaking changes
- Batch Idempotency Keys (June 2025) — prevents duplicate sends on retry
- Automatic Plain Text generation (Aug 2025) — no manual text fallbacks needed
- Broadcast API (Feb 2026) — single-API-call batch sends

### claude-code-action
- v1.0 (Aug 2025) — native GitHub Action (`anthropics/claude-code-action@v1`)
- Replaces `claude --print --dangerously-skip-permissions` for scheduled runs
- Single `prompt` input + `claude_args` for CLI options
- Auto-detects automation mode on schedule triggers
- Auth: ANTHROPIC_API_KEY secret, or Bedrock/Vertex/Foundry
- Breaking from v0.x — migration guide available

### Competitive Landscape
- Consumer SaaS (Sonara, LazyApply, Jobright, LoopCV, AIApply, JobHire.AI) all optimize for auto-apply volume
- None target startup generalist niche or crypto/Web3
- None provide intelligence/briefing layer
- JSA differentiator: curation quality over application volume

### Gaps
- Upstash Redis Python SDK: no new changes found
- Crypto/Web3 job board APIs: still no new APIs or accessible boards
- python-jobspy exact dependency versions: not publicly listed on PyPI

## Related Files

### Agent Definitions
- `03_agents/tests/v21/.claude/agents/search-verify.md`
- `03_agents/tests/v21/.claude/agents/source-researcher.md`
- `03_agents/tests/v21/.claude/agents/brief-generator.md`
- `03_agents/tests/v21/.claude/agents/digest-email.md`
- `03_agents/tests/v21/.claude/agents/briefs-html.md`
- `03_agents/tests/v21/.claude/agents/onboarding.md`

### Skills
- `03_agents/tests/v21/.claude/skills/jsa-design-system.md`
- `03_agents/tests/v21/.claude/skills/jsa-digest-email.md`
- `03_agents/tests/v21/.claude/skills/jsa-briefs-html.md`
- `03_agents/tests/v21/.claude/skills/jsa-search-verify.md`
- `03_agents/tests/v21/.claude/skills/jsa-source-researcher.md`
- `03_agents/tests/v21/.claude/skills/jsa-brief-generator.md`
- `03_agents/tests/v21/.claude/skills/jsa-onboarding.md`

### Scripts
- `03_agents/tests/v21/scripts/preflight.sh`
- `03_agents/tests/v21/scripts/manage_state.py`
- `03_agents/tests/v21/scripts/jobspy_search.py`
- `03_agents/tests/v21/scripts/filter_jobs.py`
- `03_agents/tests/v21/scripts/summarize_jobs.py`
- `03_agents/tests/v21/scripts/send_email.py`
- `03_agents/tests/v21/scripts/verify_html.py`
- `03_agents/tests/v21/scripts/export_transcript.py`

### Configuration
- `03_agents/tests/v21/CLAUDE.md`
- `03_agents/tests/v21/context.md`
- `03_agents/tests/v21/state.json`
- `03_agents/tests/v21/.claude/settings.local.json`
- `03_agents/tests/v21/.github/jsa-config.json`
- `03_agents/tests/v21/vercel.json`

### Output
- `03_agents/tests/v21/output/verified/{role_type}/*.json`
- `03_agents/tests/v21/output/verified/{role_type}/_status.json`
- `03_agents/tests/v21/output/jobs/{role_type}-aggregator.json`
- `03_agents/tests/v21/output/briefs/*.md`
- `03_agents/tests/v21/output/briefs/briefs-{date}.html`
- `03_agents/tests/v21/output/digests/{date}-email.html`
- `03_agents/tests/v21/output/_delta.json`
- `03_agents/tests/v21/output/session-state.md`

### Infrastructure
- `03_agents/tests/v21/api/*.py` (8 serverless functions)
- `.github/workflows/daily-digest.yml` (root — hardcoded to v20)
- `03_agents/tests/v21/.claude/agent-memory/search-verify/MEMORY.md`

### Workflow History
- `docs/plans/active/jsa-v21-analysis.md` — 14 failures (4C/4M/6m), 3 architectural + 11 implementation fixes
- `docs/plans/active/jsa-v21-compound.md` — 6 decisions, 7 solutions, 10 proposals
- `.claude/decision-log/jsa-v21.md` — V21 design decisions
- `.claude/regressions/jsa.md` — Cross-version failure tracking

## Historical Context

JSA has iterated from V7 through V21 (15 versions). Key architectural evolution:

| Version | Architecture |
|---------|-------------|
| V7-V8 | Initial subagent design |
| V11 | CLAUDE.md rewrite, single-agent vs subagent decision |
| V13 | Named agent pattern (YAML frontmatter), design system skill |
| V17 | Full codebase research (6 subagents, 7 skills, 11 API endpoints) |
| V18 | 3-phase infrastructure fixes |
| V19 | Full build, scheduling alternatives researched |
| V20 | Full pipeline, 17 failures analyzed, scheduling broken |
| V21 | 3-layer (Code Infra → Constraint Promotion → Validation Harness), 14 failures |

Cross-version trends from analysis: HC7 (incremental commit enforcement) and CR10 (dispatch variable completeness) are 5th-time recurrences. Failure count declining (V20: 17 → V21: 14, 18% reduction). GitHub Actions scheduled runs broken since V20.

## Handoff Contract

- Files to modify: `03_agents/tests/v21/CLAUDE.md`, `03_agents/tests/v21/scripts/preflight.sh`, `03_agents/tests/v21/.claude/settings.local.json`, `03_agents/tests/v21/.claude/agents/*.md`, `03_agents/tests/v21/.claude/skills/*.md`, `03_agents/tests/v21/context.md`, `.github/workflows/daily-digest.yml`
- Patterns to preserve: named agent dispatch via Task tool, status file protocol, design system skill enforcement, preflight.sh validation harness, state.json lifecycle management, checkpoint discipline, idempotency gate
- Hard constraints discovered: no model: param to Task, CSS from design-system skill only, no PDF, no Python in parent (except send_email/manage_state/preflight), never execute subagent-only ops in parent, incremental commit+push after search/delivery, CLAUDE.md <=280 lines
- Open questions: (1) Should scheduled runs migrate from `claude --print` to `claude-code-action@v1`? (2) Should JobSpy MCP Server replace Python subprocess pattern? (3) Should Resend Batch Idempotency Keys replace current idempotency gate? (4) How to enforce HC7 incremental commits beyond checklist (5th recurrence)?

<!-- STAGE COMPLETE: /research full, 2026-02-19 -->

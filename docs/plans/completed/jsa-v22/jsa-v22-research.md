# Research: JSA V22

## Current State

The Job Search Agent (JSA) lives in `03_agents/tests/v21/` and uses a named-agent orchestration pattern (v13 standard). The parent orchestrator (`CLAUDE.md`, 234 lines) is a lightweight dispatcher that reads only status files and delegates all work to 6 named agents via the Task tool. Detailed phase logic lives in `references/` (5 files) and is loaded on-demand.

### Pipeline

Five phases executed sequentially:

1. **Search** — Parent dispatches `search-verify` subagents (one per role type, batches of 2-3). Each subagent runs `jobspy_search.py` for aggregator results, WebFetches specialty boards, filters by title exclusions, verifies each listing (active check + 5-factor scoring), and writes verified JSONs + `_status.json` + `_summary.md`.
2. **Dedup** — Parent runs `manage_state.py dedup` (cross-role by normalized company+title, within-role by URL, score <70 archived) then `manage_state.py sync` (computes delta, updates `state.json`, writes `_delta.json`).
3. **Present** — Parent formats standardized tables from summaries + delta, presents Unified Selection View with dashboard URL, collects user brief selections via `manage_state.py record-action`.
4. **Deliver** — brief-generator subagents (parallel), then briefs-html + digest-email subagents (parallel). Parent sends email via `send_email.py`, commits + pushes.
5. **Maintenance** — Incremental git commit+push after each search batch, Vercel redeploy if dashboard data changed.

### Configuration

| Config | Location | Purpose |
|--------|----------|---------|
| Agent instructions | `CLAUDE.md` (234 lines) | Parent orchestrator, hard constraints, phase dispatch |
| User profile | `context.md` (112 lines) | Skills, experience, targets, sources, delivery, dashboard URL |
| Machine config | `.github/jsa-config.json` | Model, 4 role types, scoring weights, constraints |
| Permissions | `.claude/settings.local.json` | ~70 allow entries for Bash, WebFetch, Read/Write/Glob/Grep |
| Scoring | `references/algorithms.md` (188 lines) | 5-factor model, salary penalty, dedup rules |
| Secrets | `.env` (gitignored) | RESEND_API_KEY, ANTHROPIC_API_KEY |

### Named Agents (6)

| Agent | Skills | Purpose |
|-------|--------|---------|
| `search-verify` | `jsa-search-verify` | Search + verify + score one role type. 15 input variables. Full web access. |
| `brief-generator` | `jsa-brief-generator` | Generate one application brief. 8 input variables. No web access. |
| `briefs-html` | `jsa-design-system`, `jsa-briefs-html` | Compile brief markdowns into styled HTML. |
| `digest-email` | `jsa-design-system`, `jsa-digest-email` | Generate HTML email digest. 9 input variables. Requires `dashboard_url`. |
| `source-researcher` | `jsa-source-researcher` | Discover job sources across 5 categories. Full web access. |
| `onboarding` | `jsa-onboarding` | Parse CV, extract structured profile. No web access. |

### Skills (7)

| Skill | Lines | Purpose |
|-------|-------|---------|
| `jsa-design-system.md` | 620 | Unified visual design: Newsreader + DM Sans fonts, warm stone palette, no blue, layout tokens |
| `jsa-search-verify.md` | 221 | Search workflow, verification steps, 15 template variables, speed target <120s/job |
| `jsa-digest-email.md` | 205 | Email template, sections, idempotency gate, 8 template variables |
| `jsa-source-researcher.md` | 167 | Source discovery, 5 categories, 15-fetch budget |
| `jsa-onboarding.md` | 139 | CV parsing, profile extraction, role/industry inference |
| `jsa-brief-generator.md` | 114 | Brief template, 6 sections, 300-500 words, no external research |
| `jsa-briefs-html.md` | 89 | HTML compilation, design system enforcement, TOC with anchors |

### Scripts (8)

| Script | Purpose |
|--------|---------|
| `manage_state.py` | CLI: sync, record-action, cleanup, dedup. JobEntry/State dataclasses, 14-day expiry, 90-day purge, atomic writes |
| `jobspy_search.py` | JobSpy wrapper (Indeed, LinkedIn, Glassdoor). Subagent-only. |
| `filter_jobs.py` | Title exclusion filter. Subagent-only. |
| `summarize_jobs.py` | One-line job summaries for context efficiency. Subagent-only. |
| `send_email.py` | Resend API email sender. CLI: `--to --subject --body-file --attachment`. Parent-orchestrated. |
| `preflight.sh` | Two-tier validation (env + structure). Runs cleanup + dedup on startup. |
| `verify_html.py` | CSS color compliance checker (no blue, red, orange, amber). |
| `preview.sh` | Local HTTP preview server (port 8800). |

### References (5)

| File | Lines | Purpose |
|------|-------|---------|
| `orchestration.md` | 391 | Five-phase step-by-step instructions for parent. Single source of truth for workflow. |
| `algorithms.md` | 188 | Scoring rubric (required 40 / preferred 20 / experience 15 / industry 15 / location 10), dedup rules |
| `presentation-rules.md` | 200 | Table format, footnote URLs, Unified Selection View, score threshold >=70 |
| `subagent-search-verify.md` | 286 | Wrapper instructions for search-verify (tools, schema, speed target, prohibitions) |
| `subagent-digest-email.md` | 188 | Wrapper instructions for digest-email (tools, schema, idempotency) |

### State Architecture

| File | Schema | Lifecycle |
|------|--------|-----------|
| `state.json` | `{ last_run_date, jobs: { "role/slug": JobEntry }, expired_jobs }` | Persistent across all runs. Atomic writes. 14-day expiry, 90-day purge. |
| `output/_delta.json` | `{ run_date, new_jobs, still_active, expired_count, rejected_count }` | Computed each run by `manage_state.py sync`. Powers dashboard. |
| `output/session-state.md` | Markdown run log | Written by parent after each search batch. Committed to git. |
| `output/verified/{role}/_status.json` | `{ status, jobs_verified, jobs_failed, total_time }` | Per-role subagent completion signal. |
| `output/verified/{role}/_summary.md` | Markdown table | Parent's exclusive view into verified results. |

### External Integrations

| Service | Purpose | Auth |
|---------|---------|------|
| Resend | Email delivery | RESEND_API_KEY in .env |
| Upstash Redis | Dashboard user actions | UPSTASH_REDIS_REST_URL + TOKEN (Vercel env vars) |
| Vercel | Dashboard hosting | Project `jsa-dashboard`, manual deploy |
| JobSpy | Aggregated search | None (scraper) |
| GitHub Actions | Scheduled runs | Repo secrets |
| Specialty boards | Web3.Career, CryptocurrencyJobs, BeInCrypto, AIJobs | WebFetch (no auth) |

### Dashboard

- URL: `https://jsa-dashboard.vercel.app/#digest`
- Architecture: Static frontend (`public/`) + Python serverless API (`api/`), deployed to Vercel
- API endpoints: `/api/state`, `/api/jobs`, `/api/action` (POST), `/api/job`, `/api/brief`, `/api/pipeline`, `/api/run`, `/api/context`
- User actions stored in Upstash Redis (`action:{job_key}` keys), fallback to `state.json`
- **Manual deploy required** after any `output/verified/` or `_delta.json` changes

### GitHub Actions (Scheduling)

- **Repo-root workflow** (`/.github/workflows/daily-digest.yml`): cron Mon-Fri 06:00 UTC, 90min timeout
- **BROKEN**: still points to `03_agents/tests/v20` (not v21)
- Uses `nick-fields/retry@v3`, 2 attempts, 80-min timeout per attempt
- Claude `--print` mode times out at 80-90 min
- V21 workflow exists at `03_agents/tests/v21/.github/workflows/daily-digest.yml` with fixes (no nick-fields/retry, inline settings.local.json, preflight step, post-deploy smoke test) but is not referenced by the repo-root scheduler

### Output Structure

```
output/
├── _delta.json
├── session-state.md
├── _source_research.json
├── jobs/{role_type}-*.json          (raw, temp — cleaned by preflight)
├── verified/{role_type}/*.json      (committed, served by dashboard)
├── archive/{role_type}/*.json       (deduped/low-score)
├── briefs/{company}-{title}-brief.md
├── briefs/briefs-{date}.html
└── digests/{date}-email.html
```

## Code References

- `03_agents/tests/v21/CLAUDE.md` — Parent orchestrator (234 lines)
- `03_agents/tests/v21/context.md` — User profile + delivery config (112 lines)
- `03_agents/tests/v21/.github/jsa-config.json` — Machine-readable config
- `03_agents/tests/v21/.claude/agents/*.md` — 6 named agents
- `03_agents/tests/v21/.claude/skills/*.md` — 7 skills
- `03_agents/tests/v21/references/*.md` — 5 reference docs
- `03_agents/tests/v21/scripts/*.py` — 6 Python scripts
- `03_agents/tests/v21/scripts/preflight.sh` — Validation harness
- `03_agents/tests/v21/scripts/preview.sh` — Local preview server
- `03_agents/tests/v21/state.json` — Persistent state
- `03_agents/tests/v21/api/*.py` — Vercel API handlers
- `03_agents/tests/v21/public/` — Dashboard frontend
- `.github/workflows/daily-digest.yml` — Repo-root scheduled workflow

## Patterns Found

- **Named agent v13 pattern**: YAML frontmatter with `model: inherit`, `memory: project`, `skills:` field. Parent dispatches via Task tool with compact JSON blob.
- **Status file protocol**: Subagents write `_status.json` + `_summary.md`. Parent reads only these sentinel files, never raw output.
- **Design system skill enforcement**: All HTML-producing subagents load `jsa-design-system` skill. CSS is never duplicated in prompts.
- **Context budget separation**: Parent reads only status files, dispatches all file reading/web access/computation to subagents.
- **Atomic state writes**: `manage_state.py` writes to temp file then `os.replace()`.
- **Two-tier validation**: `preflight.sh` separates critical (exit 1) from warning checks.
- **Idempotency**: Email send checks `_status.json` for `sent_at` matching today before sending.
- **Incremental commits**: Git commit+push required after each search batch (documented constraint, 6x regression).

## External Landscape

### Technology Updates (since Feb 19, 2026)

| Technology | Update | Relevance |
|------------|--------|-----------|
| Claude Agent SDK | `background: true` flag in agent definitions — agents can be declared as always-background, removing per-dispatch `run_in_background=true` | High — directly addresses V20/V21 background subagent permission failures |
| Claude Agent SDK | Task tool returns token count, tool uses, and duration metrics | Medium — enables orchestration cost tracking |
| Resend | Broadcast API single-request send (Feb 12, 2026) | Low — simplifies if moving to broadcast model |
| Resend | Improved log search with status filters + error guidance | Low — better debugging for failed sends |
| Vercel | Python SDK in beta (`pip install vercel`) — Sandbox, Blob, Runtime Cache API | Low — future API layer option |
| python-jobspy | No change — still v1.1.82 | No action needed |
| claude-code-action | No change — still v1.0, pin `@v1` safe | No action needed |

### Unchanged Since Last Research

- python-jobspy v1.1.82, Python >=3.10
- Resend SDK 2.0 stable, Batch Idempotency Keys, CID image embedding
- Upstash Redis HTTP-based, from_env(), JSON/pipeline support
- claude-code-action v1.0, replaces `claude --print`
- Crypto/Web3 boards: Web3.Career accessible, CryptoJobsList/Wellfound blocked

## Related Files

- V21 analysis: `docs/plans/completed/jsa-v21/jsa-v21-analysis.md` — 14 failures, 3 architectural + 11 implementation fixes
- V21 compound: `docs/plans/completed/jsa-v21/jsa-v21-compound.md` — 6 decisions, 7 solutions, 10 proposals
- V21 decision log: `.claude/decision-log/jsa-v21.md` — 6 design decisions
- Regressions: `.claude/regressions/jsa.md` — V14-V21 regression catalog
- Research patterns: `.claude/research-patterns/job-search-automation.md`

## Historical Context

JSA has gone through 15 version cycles (V7-V21). Key architectural milestones:

- **V11**: CLAUDE.md rewrite, single-agent vs subagent design decision
- **V13**: Named agent pattern established (YAML frontmatter, skills preloading, status file protocol)
- **V17**: Vercel dashboard, GitHub Actions scheduling introduced
- **V18**: Agent decomposition pattern (CLAUDE.md <=300 lines, references/ extraction)
- **V19**: Cross-role dedup code enforcement (`manage_state.py`)
- **V20**: Three-phase architecture, preflight.sh validation harness
- **V21**: Three-layer build (Code Infrastructure → Constraint Promotion → Validation Harness), 101 tests passing

### Recurring Regressions (from `.claude/regressions/jsa.md`)

The following failures have recurred across multiple versions:

| Regression | Versions | Occurrences |
|------------|----------|-------------|
| Incremental commit+push after every search batch | V14, V16, V18, V19, V20, V21 | 6x |
| session-state.md after every search batch | V14, V16, V18, V19, V21 | 5x |
| Cross-role dedup on normalized (company, title) | V18, V19, V20 | 3x |
| Dashboard URL mandatory in all code paths | V18, V19, V20 | 3x |
| GitHub Actions points at previous version | V19, V21 | 2x |
| Never ask user to do technical work | V17, V18, V21 | 3x |
| Agent memory read on startup | V14, V17, V19 | 3x |

### V21 Analysis Summary

14 failures identified (4 Critical, 4 Major, 6 Minor):
- **3 Architectural fixes**: (A1) search subagent rate/time budget, (A2) GH Actions scheduled run architecture, (A3) parallel tool call failure isolation
- **11 Implementation fixes**: preflight CLI self-validation, partial heading matches, archival cross-references state.json, Vercel deploy automation, incremental commit+push enforcement, session-state after every batch, send_email flag fix, mandatory dispatch variables, comprehensive settings.local.json, no user technical work, export transcript awareness

### V21 Decision Log Summary

6 design decisions documented:
1. Standalone `manage_state.py` over inline dedup (4 consecutive version failures justified code enforcement)
2. Three-Layer Architecture over Two-Phase or Single Phase
3. CLAUDE.md decomposition to references/ (677→266 lines)
4. GH Actions config file over YAML heredoc (100% scheduled run failure rate from heredoc indentation)
5. Tiered validation in preflight.sh (hard-block vs warn)
6. Parallel execution within Layer 1

---

## Delta: V22 Post-Build (2026-02-24)

### Files Changed
- `.claude/regressions/jsa.md`: 8 new V22 regression items added — rate-limit stale data, search breadth default, context-unaware dedup, CI preflight SCHEDULED_RUN, workflow env var propagation, Vercel redeploy skipped, incremental commit 7th occurrence, session-state 6th occurrence
- `.github/workflows/daily-digest.yml`: Added `SCHEDULED_RUN: "true"` env var to preflight step (line 38). Uses `claude-code-base-action@beta` with 50 max_turns, 60-min job timeout. New Vercel deploy step (`if: always() && steps.claude-run.outcome == 'success'`)
- `03_agents/tests/v22/.claude/agent-memory/search-verify/MEMORY.md`: Rewrote "Source Effectiveness" section — added ElevenLabs, updated Anthropic (35+ roles, /careers/jobs path), added Perplexity/Cognition/Cursor/Replit/Hugging Face/Mistral assessments. Added London presence list and "Lead" title exclusion note
- `03_agents/tests/v22/context.md`: Target narrowed from 4 named role types to "any role matching skills + AI agent companies only". Industries narrowed from 3 (Crypto, AI, Startups) to 1 (AI Agents exclusively). Sources table replaced: 19 mixed-industry sources → 14 direct-careers + 2 ai-job-board + 2 jobspy entries. Removed all crypto/web3 and generic startup boards
- `03_agents/tests/v22/scripts/preflight.sh:60-61`: Added SCHEDULED_RUN guard to skip settings.local.json check in CI
- `03_agents/tests/v22/output/verified/`: 5 new subdirectories (ai-agent-roles-agg, ai-agent-roles-b2, ai-agent-roles-jobspy, ai-agent-roles-niche, ai-agent-roles). 14+ verified job JSONs. 3 old Anthropic JSONs archived
- `docs/plans/active/jsa-v22-analysis.md`: New file — 8 failures (3C/3M/2m), 6 solutions, 4 patterns, build metrics

### Assumptions Invalidated
- **"4 role types (Community Manager, Marketing Manager, Marketing Associate, Founder's Associate)"** → context.md now has NO named role types — uses "any role matching skills" with AI agent companies focus only. All role-type-specific source mappings are obsolete
- **"3 industries (Crypto/Web3, AI/ML, Tech Startups)"** → Now exclusively "AI Agents / AI Startups". All crypto/web3 sources documented in the research are no longer relevant
- **"19 sources including crypto boards"** → Sources table is now 18 entries, all AI-agent focused. Crypto boards removed entirely
- **"~70 allow entries in settings.local.json"** → V22 build brought this to 85 entries
- **"GitHub Actions BROKEN: points to v20, uses nick-fields/retry"** → Fixed — workflow points to `03_agents/tests/v22`, uses `anthropics/claude-code-base-action@beta` with 50 max_turns, 60-min timeout
- **"CLAUDE.md is 234 lines"** → V22 CLAUDE.md is ~270 lines (added checkpoint, background:true dispatch, recovery protocol sections)
- **"Orchestration.md is 391 lines"** → V22 build added PRE-GATE/POST-CHECKPOINT wrappers, SUBAGENT BUDGET, Prerequisites — likely increased

### New Patterns/Utilities
- **Checkpoint infrastructure**: `manage_state.py checkpoint write/validate/status/clear` subcommands. `output/.checkpoints/` directory. Phases 2-5 gated by `checkpoint validate`
- **`background: true` in agent frontmatter**: All 6 agents now have `background: true` in YAML, replacing per-dispatch `run_in_background=true`
- **SCHEDULED_RUN env var as CI-mode toggle**: preflight.sh uses `${SCHEDULED_RUN:-}` to skip settings.local.json validation in CI. Workflow propagates it to both preflight and Claude action steps
- **Vercel deploy as workflow step**: New GH Actions step with `if: always() && steps.claude-run.outcome == 'success'`
- **Recovery Protocol in CLAUDE.md**: Formalized pattern for subagent failures — dispatch recovery subagent rather than reading raw JSONs in parent

### Updated Code References
- `03_agents/tests/v22/CLAUDE.md`: ~270 lines (was 234). New: Recovery Protocol, Auto-Retry Protocol, expanded ON STARTUP (items 4-5 for background dispatch and git pull)
- `03_agents/tests/v22/scripts/preflight.sh:60-61`: SCHEDULED_RUN guard for CI mode
- `03_agents/tests/v22/context.md:51-57`: Narrowed target and industry focus
- `03_agents/tests/v22/context.md:69-92`: Replaced source table (AI-agent-only sources)
- `.github/workflows/daily-digest.yml:21`: working-directory now `03_agents/tests/v22`
- `.github/workflows/daily-digest.yml:42-54`: claude-code-base-action@beta replaces nick-fields/retry
- `.github/workflows/daily-digest.yml:76-89`: New Vercel deploy step
- `.claude/regressions/jsa.md:115-122`: 8 new V22 regressions

### Competitive Intelligence

**Rate-Limit Recovery:**
- Portkey/ResilientLLM: Exponential backoff with jitter (250-750ms initial, ×2 factor), per-attempt timeouts, circuit breakers (trip at N consecutive failures or error rate threshold), token bucket rate limiting
- LangGraph + DynamoDB: Checkpoint-based recovery — state snapshots at each step, resume from exact execution point after transient failures
- PraisonAI/AWS: Multi-tier retry with fallback chains across providers/models
- **Applicable:** Pre-dispatch quota check, circuit breaker per search channel (3x fail → deprioritize for this run), jittered backoff in dispatch loop
- **Gap:** No precedent for graceful stale-data detection during rate limits — most systems fail or retry indefinitely

**Multi-Channel Search Orchestration:**
- MuleSoft Gateway Aggregation: Dispatcher routes to multiple backends in parallel, aggregates results, validates completeness
- AWS Multi-Agent Reference Architecture: Orchestration layer with registry of agent types and mandatory dispatch list; unused channels logged as warnings, not silently skipped
- **Applicable:** Channel registry with health checks (last_check, status, next_retry_time), mandatory dispatch enforcement with loud failure on incomplete channels, per-channel metrics (queries, results, dedup rate)
- **Gap:** No precedent for run-scoped search focus (narrowing channels per user context each run)

**Context-Aware Deduplication:**
- Ocient Data Pipelines: Dedup scope tied to pipeline object; scope changes don't re-query old data
- GitLab Vulnerability Dedup: Scope-offset algorithm with fingerprint from (filename, context, relative position)
- **Applicable:** Run-scoped partition with run_id metadata, pivot-detection on context.md changes (pre-archive old directories), `--role-types` flag for scoped dedup
- **No gap:** Pattern well-established in enterprise data pipelines

**Session Resume Guards:**
- LangGraph Checkpointer: State snapshots at each execution step with thread_id; resume from exact node or restart with message history
- AWS DynamoDB + S3 Hybrid: Checkpoints <350KB in DynamoDB, larger offloaded to S3
- Microsoft Durable Task: Automatic checkpointing of tool calls enables resume after interruptions
- **Applicable:** Checkpoint at phase boundaries, idempotency keys per subagent action, state versioning with schema migration
- **Gap:** LangGraph assumes linear workflow; JSA's parallel multi-channel dispatch needs custom checkpoint merging

### Regression Escalation Summary

| Pattern | Versions | Count | V22 Status |
|---------|----------|-------|------------|
| Incremental commit+push after every search batch | V14, V16, V18, V19, V20, V21, V22 | 7x | Needs hard enforcement gate |
| session-state.md after every search batch | V14, V16, V18, V19, V21, V22 | 6x | Needs hard enforcement gate |
| Cross-role dedup on normalized (company, title) | V18, V19, V20 | 3x | No V22 recurrence |
| Dashboard URL mandatory in all code paths | V18, V19, V20 | 3x | No V22 recurrence |
| GitHub Actions points at previous version | V19, V21 | 2x | Fixed in V22 |
| Never ask user to do technical work | V17, V18, V21 | 3x | No V22 recurrence |
| Agent memory read on startup | V14, V17, V19 | 3x | No V22 recurrence |
| Vercel redeploy on data push | V21, V22 | 2x | Needs mandatory orchestration step |
| Search breadth (all channels) | V22 (new) | 1x | Needs 5-channel mandate |
| Context-unaware dedup | V22 (new) | 1x | Needs --role-types scoping |

## Handoff Contract

- Files to modify: `03_agents/tests/v22/CLAUDE.md` (~270 lines), `03_agents/tests/v22/scripts/manage_state.py` (dedup --role-types), `03_agents/tests/v22/references/orchestration.md` (5-channel mandate + post-batch gate), `03_agents/tests/v22/context.md` (add Search Channels subsection), `03_agents/tests/v22/scripts/preflight.sh` (git pull check, session resume guard), `03_agents/tests/v22/tests/test_manage_state.py` (dedup --role-types tests), `03_agents/tests/v22/tests/test_workflow.py` (post-batch commit verification test), `.github/workflows/daily-digest.yml` (if needed)
- Patterns to preserve: named agent v13 dispatch with `background: true`, status file protocol, design system skill enforcement, preflight.sh two-tier validation, checkpoint write/validate/clear gate, SCHEDULED_RUN CI-mode toggle, atomic state writes, context budget separation, recovery subagent protocol, idempotency gate
- Hard constraints discovered: (1) `manage_state.py dedup` MUST accept `--role-types` to scope to active directories; (2) Post-batch commit is a 7x regression — text constraints insufficient, needs code-enforced gate (e.g., `manage_state.py verify-batch-committed`); (3) Session resume guard needed — check `output/digests/_status.json` for same-day `sent_at` before re-initializing; (4) Preflight must run `git pull` in interactive mode; (5) Model tiering (Opus parent / Sonnet briefs / Haiku search) — HC1 "Never pass model: to Task tool" MUST be reversed for cost reduction; (6) 5-channel search is mandatory infrastructure, not optional
- Open questions: (1) Should the 5-channel search mandate live in orchestration.md Phase 1 or as a new HC in CLAUDE.md? (2) Post-batch commit gate — `manage_state.py` subcommand or bash script check? (3) Model tiering from MEMORY.md (Opus/Sonnet/Haiku) conflicts with HC1 — which wins for V23? (4) context.md has "Fixie AI / Dust: TBD" — remove or resolve? (5) "Lead" title exclusion affects top Anthropic results per search-verify memory — soften for V23?

<!-- STAGE COMPLETE: /research delta, 2026-02-24 -->

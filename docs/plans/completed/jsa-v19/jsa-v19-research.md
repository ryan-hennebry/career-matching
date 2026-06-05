# Research: Job Search Agent V19

## Current State

The JSA V19 is a Claude Code agent that automates job searching for startup generalists targeting crypto/AI/Web3 roles. It operates as a parent-subagent orchestration system where the parent CLAUDE.md (654 lines) dispatches work to 6 named subagents via Claude Code's Task tool.

### Architecture

The agent follows a strict parent-subagent boundary:
- **Parent is a lightweight orchestrator** — dispatches tasks, reads status files, runs git commands, communicates with user. Never reads source files, executes scripts, or performs web research directly.
- **6 named subagents** handle all domain work: onboarding, source-researcher, search-verify, brief-generator, digest-email, briefs-html.
- **Skills preloading** — visual subagents (digest-email, briefs-html) preload `jsa-design-system` skill for unified styling.
- **Status file protocol** — every subagent writes `_status.json` (complete/partial/failed) and often `_summary.md`. Parent reads only these files.

### Execution Flow (23 steps)

1. Read agent memory, detect dispatch mode (foreground/background via trivial test agent)
2. Git pull (interactive), load state.json, pre-run cleanup if new run
3. Read context.md for user profile
4. If no profile: dispatch onboarding subagent, interactive Q&A, derive constraints
5. Source research gate: if no sources, dispatch source-researcher, user approval
6. Prepare 14 template variables per role type from context.md
7. Dispatch search-verify subagents in batches of 2-3, checkpoint session-state.md, incremental git commit+push
8. Cross-role dedup via `manage_state.py dedup`
9. State sync via `manage_state.py sync`, compute delta
10. Present results to user (reference-footnote table format)
11. Collect feedback (which jobs get briefs), optional Upstash rejection sync
12. Dispatch brief-generator subagents for selected jobs
13. Dispatch digest-email + briefs-html subagents in parallel
14. Post-render verification (link colors, score badges, zero-section omission)
15. Parent sends email via `send_email.py` (NOT delegated to subagent)
16. Final session-state checkpoint, offer scheduled run setup

### Hard Constraints (6)

| ID | Rule |
|----|------|
| HC1 | Never pass `model:` to Task tool — agents inherit via `model: inherit` |
| HC2 | CSS is canonical in `jsa-design-system` skill only — never embed CSS copies |
| HC3 | Never generate PDF output — briefs are browser-viewed HTML |
| HC4 | Read agent memory on startup — memory failures are hard constraints |
| HC5 | Never write inline Python for state mutations — use `manage_state.py` CLI |
| HC6 | Never give instructions about Claude Code UI features unless 100% certain |

### Named Agents

| Agent | Skills Preloaded | Web Access | Input Vars |
|-------|-----------------|------------|------------|
| onboarding | jsa-onboarding | Yes | 5 |
| source-researcher | jsa-source-researcher | Yes | 4 |
| search-verify | jsa-search-verify | Yes | 14 |
| brief-generator | jsa-brief-generator | No | 7 |
| digest-email | jsa-design-system, jsa-digest-email | No | 8 |
| briefs-html | jsa-design-system, jsa-briefs-html | No | 1 |

**Note:** All agent definitions reference `03_agents/tests/v18/` as working directory — carried over from v18, indicating v19 is an incremental iteration on v18's codebase.

## Code References

### Agent Definitions
- `03_agents/tests/v19/.claude/agents/onboarding.md` — CV parsing, profile extraction
- `03_agents/tests/v19/.claude/agents/source-researcher.md` — Job source discovery across 5 categories
- `03_agents/tests/v19/.claude/agents/search-verify.md` — Search, filter, verify, score jobs (14 vars)
- `03_agents/tests/v19/.claude/agents/brief-generator.md` — Single brief generation (300-500 words, 6 sections)
- `03_agents/tests/v19/.claude/agents/digest-email.md` — Email-safe HTML digest
- `03_agents/tests/v19/.claude/agents/briefs-html.md` — Compile briefs into styled HTML

### Skills
- `03_agents/tests/v19/.claude/skills/jsa-design-system.md` — Unified design system: Newsreader + DM Sans fonts, warm stone palette, no blue, 800px briefs / 600px email
- `03_agents/tests/v19/.claude/skills/jsa-brief-generator.md` — Brief structure (6 sections), no external research, <60s target
- `03_agents/tests/v19/.claude/skills/jsa-briefs-html.md` — Compile markdown briefs into single HTML with TOC
- `03_agents/tests/v19/.claude/skills/jsa-digest-email.md` — Email digest: New Today cards + Still Active table, score threshold 70+
- `03_agents/tests/v19/.claude/skills/jsa-onboarding.md` — CV parsing, profile JSON extraction
- `03_agents/tests/v19/.claude/skills/jsa-search-verify.md` — Search sources, filter, verify active, score (5-factor rubric)
- `03_agents/tests/v19/.claude/skills/jsa-source-researcher.md` — Deep source discovery, 5 categories, accessibility verification

### Scripts
- `03_agents/tests/v19/scripts/jobspy_search.py` — Python. Wraps python-jobspy, outputs JSON
- `03_agents/tests/v19/scripts/filter_jobs.py` — Python. Title exclusion filter
- `03_agents/tests/v19/scripts/manage_state.py` — Python. Core state engine: sync, record-action, dedup. Atomic writes, 14-day expiry, 90-day purge
- `03_agents/tests/v19/scripts/summarize_jobs.py` — Python. One-line summaries for context efficiency
- `03_agents/tests/v19/scripts/send_email.py` — Python. Resend API, HTML body + optional base64 attachment
- `03_agents/tests/v19/scripts/verify_html.py` — Python. CSS color compliance checker (blocks named colors, specific hex codes)
- `03_agents/tests/v19/scripts/preview.sh` — Bash. HTTP server on port 8800

### API Layer (Vercel Serverless)
- `03_agents/tests/v19/api/jobs.py` — GET /api/jobs — job list with scores and pipeline stages
- `03_agents/tests/v19/api/job.py` — GET /api/job?key= — single job detail with user action
- `03_agents/tests/v19/api/pipeline.py` — GET /api/pipeline — jobs grouped by pipeline stage
- `03_agents/tests/v19/api/action.py` — POST /api/action — accept/reject/brief_requested
- `03_agents/tests/v19/api/brief.py` — GET /api/brief?key= — render brief as HTML
- `03_agents/tests/v19/api/context.py` — GET /api/context — profile section names (PII-protected)
- `03_agents/tests/v19/api/run.py` — POST/GET /api/run — GitHub Actions workflow dispatch + status polling
- `03_agents/tests/v19/api/_files.py` — File I/O helpers
- `03_agents/tests/v19/api/_response.py` — JSON response + CORS helpers
- `03_agents/tests/v19/api/_upstash.py` — Upstash Redis client with state.json fallback

### Configuration
- `03_agents/tests/v19/CLAUDE.md` — 654-line orchestrator (entry point)
- `03_agents/tests/v19/context.md` — User profile, skills, constraints, sources, target roles
- `03_agents/tests/v19/state.json` — Persistent job lifecycle tracking (36 active jobs)
- `03_agents/tests/v19/references/algorithms.md` — Scoring rubric, skill normalization, dedup rules
- `03_agents/tests/v19/.claude/settings.local.json` — Tool permissions (WebFetch domains, Bash commands)
- `03_agents/tests/v19/.env.example` — API key template (RESEND_API_KEY)

### Tests
- `03_agents/tests/v19/tests/` — Test directory with fixtures
- `03_agents/tests/v19/tests/fixtures/verified-job-template.json` — Example verified job JSON (30+ fields)

### Agent Memory
- `03_agents/tests/v19/.claude/agent-memory/search-verify/MEMORY.md` — Source effectiveness, search patterns, scoring notes
- `03_agents/tests/v19/.claude/agent-memory/brief-generator/MEMORY.md` — Empty
- `03_agents/tests/v19/.claude/agent-memory/briefs-html/MEMORY.md` — Empty
- `03_agents/tests/v19/.claude/agent-memory/digest-email/MEMORY.md` — Empty

## Patterns Found

### Orchestration Patterns
- **Compact JSON variable passing** — Parent builds JSON blob with N template variables, passes as Task tool prompt. Each agent validates all variables on startup.
- **Status file protocol** — Every subagent writes `_status.json` (status, counts, run_date). Parent reads only status files, never individual outputs.
- **Foreground-fallback guard** — First dispatch tests background mode; if denied, all subsequent dispatches use foreground.
- **Auto-retry protocol** — One retry per subagent per run via Task tool re-dispatch. Never retry inline in parent.
- **Context budget enforcement** — Explicit allowlist in CLAUDE.md: parent may only dispatch, read status/state files, run git. Everything else is subagent-delegated.

### Design System
- Newsreader (serif headings) + DM Sans (body)
- Warm stone palette: `#1c1917` text, `#f8f8f6` cards, `#e7e5e4` borders, `#57534e` secondary
- Score badges: green `#15803d` (90+), stone (70-89), muted (marginal)
- No blue anywhere. No PDF rendering. 800px briefs, 600px email containers.

### Data Architecture
- **Verified JSON schema** — 30+ fields per job: title, company, location, job_type, work_arrangement, salary_min/max, currency, job_url, source, date_posted, active_status, industry, requirements_met[], gaps[], preferred_met[], score, score_breakdown{}, benefits[], notes, run_date, verified_at.
- **State machine** — `state.json` tracks jobs across runs with lifecycle states: active → expired (14 days), expired → purged (90 days). User actions: null → accepted|rejected|brief_requested.
- **Dual persistence** — User actions stored in both state.json (via manage_state.py) and Upstash Redis (via API). API reads merge with Redis priority.

### Output Pipeline
```
jobspy_search.py → aggregator.json → filter_jobs.py → filtered.json
→ search-verify agent → verified/{role}/{company-title}.json
→ manage_state.py dedup → manage_state.py sync → state.json + _delta.json
→ brief-generator → briefs/*.md → briefs-html → briefs-{date}.html
→ digest-email → digests/{date}-email.html → send_email.py → Resend API
```

## External Landscape

### python-jobspy
- Aggregator library scraping LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter concurrently. Maintained at `speedyapply/JobSpy` on GitHub.
- Requires Python >= 3.10, numpy >= 1.26.0. No dedicated documentation site beyond GitHub README.
- Scrapes HTML — any target site redesign can break it without warning. No formal deprecation policy.
- Does not cover crypto/Web3-specific boards — specialty sources must be scraped directly via WebFetch.

### Resend Python SDK
- Attachment pattern: `{"filename": "file.pdf", "content": list(pdf_bytes), "content_type": "application/pdf"}`. Content must be `list(bytes)`, not raw bytes.
- Tags supported for categorization: `[{"name": "type", "value": "digest"}]`.
- Post-send attachment retrieval available via `Emails.Attachments.list(email_id)`.

### Upstash Redis Python SDK
- HTTP-based (REST API), no persistent TCP connections — ideal for serverless/subagent contexts.
- Init: `Redis.from_env()` reads `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`.
- Pipelines: `redis.pipeline()` for batched non-atomic commands. Transactions: `redis.multi()` for atomic.
- JSON commands: `redis.json.set()`, `redis.json.get()` for complex state objects.

### Claude Code Subagents
- Named agents with YAML frontmatter in `.claude/agents/*.md` is the established pattern.
- Skills preloaded via `skills:` field. Status file protocol for completion signaling is convention.
- Subagents preserve context, enforce tool constraints. No peer-to-peer messaging.

### Job Board Accessibility
| Board | Status | Notes |
|-------|--------|-------|
| Web3.Career | Accessible | Best for crypto/Web3 roles |
| CryptocurrencyJobs.co | Accessible | Good industry match |
| BeInCrypto Jobs | Accessible | Confirmed working |
| AI Jobs | Accessible | Confirmed working |
| CryptoJobsList | Blocked | 403/404 on WebFetch |
| Wellfound | Blocked | 403/404 |
| startup.jobs | Blocked | 403/404 |
| LinkedIn/Indeed/Glassdoor | Via python-jobspy | Mainstream roles, poor crypto/AI match |

## Related Files

### Agent Core
- `03_agents/tests/v19/CLAUDE.md`
- `03_agents/tests/v19/context.md`
- `03_agents/tests/v19/state.json`
- `03_agents/tests/v19/references/algorithms.md`

### Agent Definitions (6)
- `03_agents/tests/v19/.claude/agents/*.md`

### Skills (7)
- `03_agents/tests/v19/.claude/skills/*.md`

### Scripts (7)
- `03_agents/tests/v19/scripts/*.py`
- `03_agents/tests/v19/scripts/preview.sh`

### API Layer (10)
- `03_agents/tests/v19/api/*.py`
- `03_agents/tests/v19/vercel.json`

### Tests
- `03_agents/tests/v19/tests/`

### Agent Memory (4)
- `03_agents/tests/v19/.claude/agent-memory/*/MEMORY.md`

### Configuration
- `03_agents/tests/v19/.claude/settings.local.json`
- `03_agents/tests/v19/.env.example`
- `03_agents/tests/v19/.gitignore`
- `03_agents/tests/v19/.github/`
- `03_agents/tests/v19/requirements.txt`

### Dashboard Frontend
- `03_agents/tests/v19/public/`

## Historical Context

### Version History (V8-V19)
- **V8-V11:** Foundation architecture — CLAUDE.md rewrite, single-agent to subagent transition
- **V12:** Compact JSON variable passing, subagent templates
- **V13:** Named agent pattern (YAML frontmatter, skills preloading, status file protocol)
- **V14:** V13 session analysis — 7 wins, 5 failures. Key regressions: PDF generation, agent memory, blue links, session-state timing
- **V17:** Full build (46/46 steps). 11 failures, 8 implementation fixes. GitHub Actions, Vercel deployment, API fallback patterns
- **V18:** Full build (21/21 steps). 8 failures, 8 fixes. Three failure domains: infrastructure, backend, frontend
- **V19:** 8 constraint fixes + 7 regression tests from V18 analysis. 14/14 steps, 101 tests pass. 12 session failures identified in analysis.

### Decision Log (V19)
- Single phase build (all fixes share constraint enforcement domain)
- Proactive foreground-fallback guard (trivial test agent on startup)
- Context budget via CLAUDE.md text constraints (not code-level enforcement)
- Settings.local.json merge semantics (not overwrite)
- Semantic pattern matching for regression tests (not exact strings)
- Prototyping skipped (no triggers met)

### Regressions File
78 lines across V14-V19. Key recurring patterns:
- Session-state timing: V14/V16/V18/V19 — incremental write deferred to end
- Agent memory startup: V14/V17/V19 — HC4 violations
- Dashboard URL proactive display: V18/V19 — not shown after results
- Content-based dedup: V18/V19 — filename slugs instead of normalized title+company
- Script execution in parent: V15/V19 — HC5 violations

## Handoff Contract

- Files to modify: CLAUDE.md (constraint enforcement), agent definitions (working directory), scripts/manage_state.py (dedup logic), .claude/settings.local.json (permissions), context.md (dashboard URL), tests/ (regression tests), .github/workflows/ (version reference)
- Patterns to preserve: Named agent pattern (YAML frontmatter), compact JSON variable passing, status file protocol, design system (jsa-design-system skill), context budget enforcement, foreground-fallback guard, auto-retry protocol
- Hard constraints discovered: HC1-HC6, all 6 active. V18 working directory reference in agent definitions (`v18` not `v19`). Agent memory files mostly empty (only search-verify has content). 78 regression entries across 6 versions.
- Open questions: Should V20 address the v18 working directory references in agent definitions? Should empty agent memory files be pre-populated with patterns from the regressions file? Should the recurring regression patterns (4 versions of session-state timing) trigger architectural changes rather than constraint text additions?

<!-- STAGE COMPLETE: /research [full], 2026-02-17 -->

# Research: Job Search Agent V20

## Current State

The JSA V20 is a Claude Code agent that automates job searching for startup generalists targeting crypto/AI/Web3 roles. It operates as a parent-subagent orchestration system where the parent CLAUDE.md (677 lines) dispatches work to 6 named subagents via Claude Code's Task tool.

### Architecture

The agent follows a strict parent-subagent boundary:
- **Parent is a lightweight orchestrator** — dispatches tasks, reads status files, runs git commands, communicates with user. Never reads source files directly (except `send_email.py` and `manage_state.py` CLI invocations).
- **6 named subagents** handle all domain work: onboarding, source-researcher, search-verify, brief-generator, digest-email, briefs-html.
- **7 skills** preloaded via agent frontmatter `skills:` field — `jsa-design-system` (canonical CSS), plus one skill per subagent.
- **Status file protocol** — every subagent writes `_status.json` (complete/partial/failed) and `_summary.md`. Parent reads only these files.
- **Agent memory** — 4 memory files in `.claude/agent-memory/*/MEMORY.md`, read on startup with fatal assertion (0 files = STOP).

### Directory Layout

```
03_agents/tests/v20/
  CLAUDE.md                          # Parent orchestrator (677 lines)
  context.md                         # User profile, roles, sources, delivery config
  state.json                         # Persistent job lifecycle state
  vercel.json                        # Dashboard deployment config
  .env.example                       # Required env vars template
  requirements.txt                   # Python dependencies
  references/
    algorithms.md                    # Scoring rubric, dedup rules, CV parsing
  scripts/
    manage_state.py                  # State management CLI (sync, dedup, record-action)
    jobspy_search.py                 # JobSpy aggregator wrapper
    filter_jobs.py                   # Title exclusion filter
    summarize_jobs.py                # Context-efficient summaries
    send_email.py                    # Resend API email sender
    verify_html.py                   # HTML output verification
    preview.sh                       # Local HTML preview server
  .claude/
    agents/                          # 6 named agent definitions (YAML frontmatter)
    skills/                          # 7 skill files (jsa-*.md)
    agent-memory/                    # 4 per-subagent memory files
    settings.local.json              # Tool permissions (60+ allow entries)
  .github/workflows/
    daily-digest.yml                 # GitHub Actions scheduled run
  api/                               # Vercel serverless API (10 route files)
  public/                            # Dashboard frontend (HTML/CSS/JS)
  tests/                             # 11 test files
  output/                            # All generated artifacts
```

### Execution Flow (23 Steps)

1. Read agent memory (`.claude/agent-memory/*/MEMORY.md`) — FATAL if 0 files found
2. Capture run date once (`date +%Y-%m-%d`)
3. Foreground-fallback guard: test background Task dispatch; fall back to foreground if denied
4. Git pull (interactive mode only)
5. Load `state.json`; selective pre-run cleanup if `last_run_date` != today (cross-references state.json — preserves active job files)
6. Read `context.md`; onboarding if profile empty
7. Source research gate: dispatch `source-researcher` if `## Sources` empty
8. Build 15-variable compact JSON blob per role type
9. Dispatch `search-verify` agents in batches of 2-3 (one per role type)
10. After each batch: read `_status.json`, write `session-state.md` checkpoint, commit+push
11. Read `_summary.md` for each completed role type
12. `manage_state.py dedup` — cross-role-type deduplication (CLI subcommand, never inline python)
13. `manage_state.py sync` — update `state.json`, generate `output/_delta.json`
14. Present results (score >= 70 threshold, tables, unified ranked list, dashboard URL mandatory)
15. Collect user brief selections; `manage_state.py record-action` per job
16. Optional Upstash rejection sync
17. Dispatch `brief-generator` agents (parallel if 3+)
18. Dispatch `digest-email` + `briefs-html` in parallel
19. Post-render HTML verification (link colors, badges, zero-count sections)
20. Pre-send gate (idempotency via `_status.json.sent_at`); parent sends email via `send_email.py`
21. Write final session summary to `session-state.md`
22. Offer scheduled run setup (first interactive run only)

### Hard Constraints (HC1-HC9)

- HC1: Never pass `model:` to Task tool — agents use `model: inherit` in frontmatter
- HC2: CSS is canonical in `jsa-design-system` skill — never embed CSS in prompts
- HC3: No PDF output — briefs are HTML files opened in browser
- HC4: Read agent memory on startup — fatal if 0 files found
- HC5: Never execute Python in parent (except `send_email.py` and `manage_state.py` CLI)
- HC6: No Claude Code UI feature instructions unless 100% certain
- HC7: Incremental commit+push after every search batch AND after briefs+digest
- HC8: `settings.local.json` edits must merge (read-append-write), never overwrite
- HC9: API keys must never appear in Bash command arguments — use env vars or stdin

### Named Agents

| Agent | File | Purpose | Skills |
|-------|------|---------|--------|
| search-verify | `.claude/agents/search-verify.md` | Search sources, verify listings, score | jsa-search-verify |
| brief-generator | `.claude/agents/brief-generator.md` | Generate application brief per job | jsa-brief-generator |
| briefs-html | `.claude/agents/briefs-html.md` | Compile all briefs into styled HTML | jsa-design-system, jsa-briefs-html |
| digest-email | `.claude/agents/digest-email.md` | Generate email digest HTML | jsa-design-system, jsa-digest-email |
| onboarding | `.claude/agents/onboarding.md` | Parse CV, extract structured profile | jsa-onboarding |
| source-researcher | `.claude/agents/source-researcher.md` | Discover job sources across 5 categories | jsa-source-researcher |

### Design System

Canonical in `jsa-design-system` skill (619 lines), preloaded into digest-email and briefs-html agents:
- Fonts: Newsreader (headings) + DM Sans (body) via Google Fonts
- Palette: warm stone/ink — `#1c1917` primary, `#f8f8f6` subtle bg, `#e7e5e4` border
- Score badges: green (`#15803d`) for 90+, stone (`#1c1917`) for 70-89. No amber, red, or blue anywhere.
- Layouts: Briefs 800px container; Email 600px table-based with Gmail overrides

## Code References

- `03_agents/tests/v20/CLAUDE.md` — Parent orchestrator (677 lines)
- `03_agents/tests/v20/references/algorithms.md` — Scoring rubric, dedup rules, CV parsing
- `03_agents/tests/v20/scripts/manage_state.py` — State CLI (sync, dedup, record-action)
- `03_agents/tests/v20/scripts/jobspy_search.py` — JobSpy aggregator
- `03_agents/tests/v20/scripts/filter_jobs.py` — Title exclusion filter
- `03_agents/tests/v20/scripts/send_email.py` — Resend email delivery
- `03_agents/tests/v20/scripts/verify_html.py` — HTML verification
- `03_agents/tests/v20/scripts/preview.sh` — Local preview server
- `03_agents/tests/v20/.claude/agents/*.md` — 6 named agent definitions
- `03_agents/tests/v20/.claude/skills/jsa-*.md` — 7 skill files
- `03_agents/tests/v20/.claude/agent-memory/*/MEMORY.md` — 4 agent memory files
- `03_agents/tests/v20/.claude/settings.local.json` — Tool permissions (60+ allow entries)
- `03_agents/tests/v20/.github/workflows/daily-digest.yml` — GH Actions scheduled run
- `03_agents/tests/v20/api/*.py` — 10 Vercel serverless API routes
- `03_agents/tests/v20/public/*` — Dashboard frontend (HTML/CSS/JS)
- `03_agents/tests/v20/tests/` — 11 test files
- `03_agents/tests/v20/state.json` — Persistent job lifecycle state
- `03_agents/tests/v20/context.md` — User profile, roles, sources, delivery

## Patterns Found

### Named Agent Pattern
All 6 agents use YAML frontmatter with `model: inherit`, `memory: project`, and `skills:` field. Variables passed as compact JSON blobs. Status file protocol for completion signaling. No peer-to-peer messaging — results flow back to parent only.

### State Management Pattern
`manage_state.py` provides 3 CLI subcommands (sync, dedup, record-action). Atomic writes via `tempfile + os.replace`. Soft-delete model: rejected jobs kept with `user_action = "rejected"`. 14-day expiry window, 90-day purge from `expired_jobs`. Cross-role dedup by normalized `{source_domain}:{company}:{title}:{location}` key.

### Context Budget Enforcement
Parent has explicit tool restrictions in a Context Budget table. Subagents get full tool access (Bash, Read, Write, etc.) while parent is limited to orchestration. "No escape hatch" — if subagent fails, parent must NOT execute the operation directly.

### Incremental Commit Pattern
`session-state.md` written after every search batch (not deferred). Commit+push after each batch in interactive mode. GH Actions commits only `state.json` + `session-state.md` with allowlist guard.

### Design System Enforcement
CSS canonical in one skill file. Visual subagents preload via frontmatter. Post-render verification (Step 19) checks link colors, badge colors, zero-count sections, gray score boxes.

### Scoring Pattern
100-point scale: Required Skills (40), Preferred Skills (20), Experience Fit (15), Industry Match (15), Location Match (10). Salary penalty: -10 if job max < user min. Threshold: >= 70 for presentation.

## External Landscape

### python-jobspy
- Aggregator scraping LinkedIn/Indeed/Glassdoor/Google/ZipRecruiter concurrently
- Python >= 3.10, numpy >= 1.26.0. No formal docs beyond GitHub README.
- Scrapes HTML — site redesigns break silently. No deprecation policy.
- Does not cover crypto/Web3-specific boards.

### resend-python
- Attachments as `{"filename": "f.pdf", "content": list(pdf_bytes), "content_type": "application/pdf"}`
- Content must be `list(bytes)` (list of integers), not raw bytes
- Tags for categorization: `[{"name": "type", "value": "digest"}]`

### upstash-redis-python
- HTTP-based (REST API), no persistent TCP connections — ideal for serverless
- Init via `Redis.from_env()` reads `UPSTASH_REDIS_REST_URL` + TOKEN
- Pipelines for batched non-atomic; `redis.multi()` for atomic
- `rest_encoding="base64"` default — set to `None` for JSON perf

### claude-code-subagents
- Named agents with YAML frontmatter in `.claude/agents/*.md`
- Skills preloaded via `skills:` field
- Status file protocol for completion signaling
- No peer-to-peer messaging — results only flow back to parent

### crypto-web3-job-boards
- Accessible: Web3.Career (best), CryptocurrencyJobs.co, BeInCrypto Jobs, AI Jobs
- Blocked: CryptoJobsList, Wellfound, startup.jobs, TopStartups.io, Welcome to the Jungle
- Via aggregator: LinkedIn/Indeed/Glassdoor (mainstream, poor crypto/AI match)
- Gap: No crypto/Web3 job board APIs — all are scrape-only

## State & Data

### State Files
- `state.json` — Primary persistent state. Schema: `{last_run_date, jobs: {key: JobEntry}, expired_jobs: {key: JobEntry}}`. JobEntry has 14 fields including `user_action`, `expired_date`, `reappeared`.
- `output/_delta.json` — Computed each run: `{run_date, new_jobs[], still_active[], expired_count, rejected_count}`.
- `output/session-state.md` — Per-batch checkpoints + final summary.
- `output/digests/_status.json` — Send idempotency: `{status, html_generated, run_date, sent_at, to}`.
- `output/verified/{role_type}/_status.json` — Per-role verification: complete/partial/failed.
- `output/verified/{role_type}/_summary.md` — Parent's only view into subagent results.

### External Integrations
- **Resend** — Email delivery via `scripts/send_email.py`. `RESEND_API_KEY` from `.env`.
- **Upstash Redis** — Dashboard action sync. Falls back to `state.json` when unavailable.
- **Vercel** — Dashboard hosting + serverless API. Auto-deploys from git push. URL: `https://jsa-dashboard.vercel.app/#digest`.
- **Anthropic API** — Agent orchestration via Claude Code CLI.
- **GitHub Actions** — Scheduled runs (Mon-Fri 06:00 UTC). Retry via `nick-fields/retry@v3`.

### GitHub Actions Workflow
- File: `03_agents/tests/v20/.github/workflows/daily-digest.yml`
- Trigger: `cron: '0 6 * * 1-5'` + `workflow_dispatch`
- Timeout: 90 minutes
- Key steps: checkout, Python 3.12, pip install, npm install claude-code, create `settings.local.json` (33 permissions via heredoc + validation), preflight checks (CLI + secret), `claude --dangerously-skip-permissions` with `nick-fields/retry@v3` (max 2 attempts), commit allowlist guard, push, Vercel smoke test
- Known issue: root `.github/workflows/daily-digest.yml` still references `v18` working directory

### Output Directory Structure
```
output/
  _delta.json, session-state.md, _source_research.json
  jobs/{role_type}-aggregator.json, {role_type}-filtered.json
  verified/{role_type}/{company}-{title}.json, _status.json, _summary.md
  briefs/{company}-{title}-brief.md, briefs-{date}.html, _status.json
  digests/{date}-email.html, _status.json
```

## V20 Build Changes (vs V19)

### What V20 Added
- Named agent definitions (`.claude/agents/*.md`) with `model: inherit` and `skills:` preloading
- Skill files system (7 skills, ~1,548 lines total)
- Agent memory startup assertion (fatal stop if 0 files found)
- `manage_state.py` CLI `dedup` subcommand for cross-role dedup
- Soft-delete fields on JobEntry (`user_action`, `expired_date`, `reappeared`)
- Selective pre-run cleanup (conditional on `last_run_date` vs today)
- Post-presentation dashboard URL assertion (Step 16 gate)
- `references/algorithms.md` extracted from CLAUDE.md
- GH Actions: preflight checks, settings.local.json CI generation, retry logic, 90min timeout
- Full test suite: 11 test files
- 4 new deployment regression entries

### What V20 Changed from V19
- CLAUDE.md: 653 -> 677 lines; added Context Budget table, HC1/HC8, dashboard URL assertion, dedup CLI mandate, `find -delete` cleanup, foreground-fallback guard
- State model: JobEntry gained 3 fields; soft-delete replaces hard-delete
- GH Actions: working-directory v18->v20, timeout 30->90, retry logic, preflight, CI config generation

### What Remained the Same
- Core 23-step workflow structure and sequence
- Scoring weights (40/20/15/15/10)
- Python script API surface (manage_state.py CLI subcommands)
- Vercel dashboard architecture (copied from V18/V19)
- Upstash Redis integration pattern
- Email delivery via Resend
- Auto-retry and recovery protocols

## Related Files

### Agent Code
- `03_agents/tests/v20/CLAUDE.md`
- `03_agents/tests/v20/context.md`
- `03_agents/tests/v20/state.json`
- `03_agents/tests/v20/references/algorithms.md`
- `03_agents/tests/v20/scripts/*.py` (6 scripts)
- `03_agents/tests/v20/scripts/preview.sh`
- `03_agents/tests/v20/.claude/agents/*.md` (6 agents)
- `03_agents/tests/v20/.claude/skills/jsa-*.md` (7 skills)
- `03_agents/tests/v20/.claude/agent-memory/*/MEMORY.md` (4 files)
- `03_agents/tests/v20/.claude/settings.local.json`
- `03_agents/tests/v20/.github/workflows/daily-digest.yml`
- `03_agents/tests/v20/api/*.py` (10 files)
- `03_agents/tests/v20/public/*` (5 files)
- `03_agents/tests/v20/tests/` (11 files)
- `03_agents/tests/v20/vercel.json`

### Cross-Version Memory
- `.claude/regressions/jsa.md` — 98 regression entries across V14-V20
- `.claude/decision-log/jsa-v20.md` — 4 decisions (single phase, enforcement upgrade, scheduling fix, confidence level)
- `.claude/research-patterns/job-search-automation.md` — 5 technology domains documented

### Workflow Docs
- `docs/plans/active/jsa-v20-analysis.md` — 17 failures, 13 fixes identified
- `docs/plans/active/jsa-v20-compound.md` — 4 decisions, 6 solutions, 10 proposals

## Historical Context

V20 is the 7th iteration of the JSA (V14-V20). Key trajectory:
- **V14**: Initial agent with full workflow. Established regressions file.
- **V15-V16**: Iterative constraint additions. Session-state timing issues began recurring.
- **V17**: Added GitHub Actions, Vercel dashboard, Upstash Redis integration.
- **V18**: Named agent pattern introduced. Background subagent coordination issues discovered.
- **V19**: Full build (14 steps, 101 tests). 13 failures including 4 scheduling failures. All scheduling runs failed (0% success).
- **V20**: 15-step build targeting 13 fixes. Added enforcement upgrades for 4 recurring regressions. Runtime session: 17 failures (6 critical, 5 major, 6 minor), 3 architectural + 10 implementation fixes needed.

Recurring regression patterns (4+ versions):
- Session-state timing (V14/V16/V18/V19/V20)
- Cross-role dedup normalization (V18/V19/V20)
- Dashboard URL mandatory (V18/V19/V20)
- Incremental commit enforcement (V14/V16/V18/V19/V20)
- Agent memory startup (V14/V17/V19)

## Handoff Contract

- Files to modify: CLAUDE.md (constraint enforcement + decomposition), agent definitions (6 files), skills (7 files), scripts/manage_state.py (pre-run cleanup, dedup logic), .github/workflows/daily-digest.yml (working-directory fix), context.md (dashboard URL), .claude/settings.local.json (permissions), tests/ (regression tests), .claude/agent-memory/ (populate empty stubs)
- Patterns to preserve: Named agent pattern (YAML frontmatter + skills preloading), compact JSON variable passing, status file protocol, design system (jsa-design-system skill), context budget enforcement, foreground-fallback guard, auto-retry protocol, soft-delete state model, atomic writes via tempfile+os.replace
- Hard constraints discovered: HC1-HC9 (all 9 active). Root `.github/workflows/daily-digest.yml` still references v18 working directory. 3 agent memory files are empty stubs. 98 regression entries across 7 versions. Text-based enforcement insufficient for 4 recurring regressions — assertion-based enforcement added in V20 but durability risk acknowledged.
- Open questions: Should V21 implement a pre-run validation script for full code enforcement of the 4 recurring regressions? Should empty agent memory files be pre-populated from regressions? Should the root GH Actions workflow be updated to v20? Should CLAUDE.md be further decomposed below 300 lines per Agent Decomposition Pattern (currently 677)?

<!-- STAGE COMPLETE: /research [full], 2026-02-18 -->

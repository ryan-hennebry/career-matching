# Research: Job Search Agent V24

## Current State

The JSA V24 is a CLI agent that discovers job opportunities, verifies listings, scores against a user profile, generates application briefs, and delivers digest emails. It runs as a parent orchestrator dispatching 7 named subagents via Claude Code's Task tool, all in background mode.

### Architecture

The parent orchestrator (`CLAUDE.md`, ~300 lines) manages a 5-phase workflow:
1. **Search** — Pre-search cleanup, source research, parallel search-verify channel dispatch (5 channels per role type), checkpoint after every 3 role types, commit+push
2. **Verify** — Integrated into search-verify subagent (not a separate phase in practice)
3. **Dedup** — `manage_state.py dedup` across all roles, archive duplicates with safety bounds
4. **Present** — Uniform table format (Score/Title/Company/Location), 70+ threshold, new/still-active subsections
5. **Deliver** — Brief generation per selected job, briefs-html compilation, digest-email generation, send via `send_email.py`, commit+push

11 hard constraints enforce: model tier matching on dispatch, CSS canonical in design system skill, no PDF output, agent memory read on startup, Python exec restrictions (parent-only: `send_email.py`, `manage_state.py`, `preflight.sh`), incremental commit+push after search batches, settings.local.json merge protocol, API keys via env vars only, mandatory subagent variable propagation, regression escalation.

Context budget separates parent-allowed operations (dispatch, status reads, git, email send, state management CLI) from subagent-only operations (WebFetch, WebSearch, source file reads, search/filter/dedup logic). No escape hatch — parent never executes subagent-only ops regardless of failure count.

### Agents (7)

| Agent | Model | Purpose |
|-------|-------|---------|
| search-verify | Sonnet | Search job sources, verify active listings, score against profile |
| onboarding | Sonnet | Parse CV, extract profile data |
| source-researcher | Haiku | Research 5 categories per industry for job sources |
| digest-email | Sonnet | Generate HTML digest email from verified jobs |
| briefs-html | Sonnet | Compile briefs into single styled HTML |
| brief-generator | Sonnet | Generate single-job application brief (6-section structure) |
| gate-check | Haiku | Mechanical gate verification (manage_state.py subcommands) |

All agents defined in `.claude/agents/*.md` with YAML frontmatter (model tier, skills, background:true).

### Skills (7)

| Skill | Purpose |
|-------|---------|
| jsa-search-verify | Complete search-verify workflow: JobSpy + filtering + verification + scoring |
| jsa-onboarding | CV parsing, seniority derivation, industry/skill union |
| jsa-source-researcher | 5-category source discovery per industry |
| jsa-design-system | Canonical CSS: Newsreader serif headings, DM Sans body, warm neutral palette |
| jsa-digest-email | Email HTML structure, score tiers, data integrity, zero-section omission |
| jsa-briefs-html | Briefs compilation: cover page, TOC, brief pages, score badges |
| jsa-brief-generator | 6-section brief structure, <60s speed target, no external research |

### Scripts (8)

| Script | Purpose | Called By |
|--------|---------|----------|
| `scripts/preflight.sh` | Startup validation (env + structure), runs cleanup + dedup | Parent on startup |
| `scripts/jobspy_search.py` | JobSpy board aggregation (Indeed/LinkedIn/Glassdoor) | search-verify subagent |
| `scripts/filter_jobs.py` | Title exclusion filter (case-insensitive) | search-verify subagent |
| `scripts/manage_state.py` | State lifecycle (sync, dedup, cleanup, validate-schema, record-action) | Parent + preflight |
| `scripts/summarize_jobs.py` | Context-efficient one-liner job summaries | Parent |
| `scripts/send_email.py` | Resend API email delivery (loads .env via dotenv) | Parent (Phase 5) |
| `scripts/preview.sh` | Local HTTP server (port 8800) for HTML preview | Parent |
| `scripts/verify_html.py` | CSS color checker for design system compliance | briefs-html subagent |

### References (5)

| Reference | Purpose |
|-----------|---------|
| `references/orchestration.md` | 5-phase workflow master plan, state architecture, context budget, Phase 1-5 steps |
| `references/presentation-rules.md` | Uniform table format, score threshold 70+, new/still-active subsections |
| `references/algorithms.md` | Scoring edge cases, skill normalization, experience mapping, dedup rules |
| `references/subagent-search-verify.md` | Detailed search-verify instructions, 15 template variables, speed target <120s |
| `references/subagent-digest-email.md` | Email HTML detailed instructions, card rendering, score tiers |

## Code References

- `CLAUDE.md:1-300` — Parent orchestrator: startup, phase dispatch, constraints, onboarding, UX rules
- `context.md:1-229` — User profile, target roles, sources, search channels, scoring weights
- `state.json` — Job lifecycle tracking (new → active → expired → purged)
- `.claude/agents/search-verify.md` — Sonnet-tier search+verify agent
- `.claude/agents/onboarding.md` — Sonnet-tier CV parser
- `.claude/agents/source-researcher.md` — Haiku-tier source discovery
- `.claude/agents/digest-email.md` — Sonnet-tier email generator
- `.claude/agents/briefs-html.md` — Sonnet-tier brief compiler
- `.claude/agents/brief-generator.md` — Sonnet-tier brief writer
- `.claude/agents/gate-check.md` — Haiku-tier gate validator
- `.claude/skills/jsa-design-system.md` — Canonical CSS (warm neutrals, serif headings)
- `.claude/skills/jsa-search-verify.md` — Search-verify workflow skill
- `.claude/skills/jsa-digest-email.md` — Email rendering skill
- `.claude/skills/jsa-briefs-html.md` — Briefs compilation skill
- `.claude/skills/jsa-brief-generator.md` — Brief writing skill
- `.claude/skills/jsa-onboarding.md` — CV parsing skill
- `.claude/skills/jsa-source-researcher.md` — Source discovery skill
- `scripts/preflight.sh` — Startup validation harness
- `scripts/manage_state.py` — State management CLI (~14K lines)
- `scripts/jobspy_search.py` — JobSpy aggregator
- `scripts/filter_jobs.py` — Title exclusion filter
- `scripts/summarize_jobs.py` — Context-efficient summaries
- `scripts/send_email.py` — Resend email client
- `scripts/preview.sh` — Local HTTP preview server
- `scripts/verify_html.py` — CSS color validator
- `references/orchestration.md` — Phase workflow master plan
- `references/presentation-rules.md` — Result presentation format
- `references/algorithms.md` — Scoring/dedup algorithms
- `references/subagent-search-verify.md` — Search-verify dispatch template
- `references/subagent-digest-email.md` — Digest email dispatch template
- `tests/` — 195 tests across 8 modules

## Patterns Found

### State Management
- Canonical 10-field JSON schema: job_id, title, company, job_url, role_type, score, source_channel, run_date, location, status
- Lifecycle: new (first_seen == run_date) → still_active (last_seen within 14 days) → expired → purged (90 days)
- Delta computed by `manage_state.py sync`: new_jobs, still_active, expired_count, rejected_count → `_delta.json`
- Dedup safety bound: >50% archival rate aborts to prevent data loss
- Auto-scoping: dedup limits to role types from current run_date

### Output Structure
```
output/
  jobs/{role_type_slug}-aggregator.json        # Raw JobSpy output
  verified/{role_type_slug}/
    _status.json                                # Channel completion status
    _summary.md                                 # Parent's ONLY view into results
    {company_slug}-{title_slug}.json           # Canonical verified schema
  briefs/
    {company_slug}-{title_slug}-brief.md       # Individual brief
    briefs-{run_date}.html                     # Compiled HTML
    _status.json                                # Compilation status
  digests/
    {run_date}-email.html                      # Digest email
    _status.json                                # Delivery status
  archive/                                      # Deduped/purged files
  session-state.md                              # Run log
  _delta.json                                   # Daily delta
```

### Test Coverage (195 tests, 8 modules)
| Module | Tests | Focus |
|--------|-------|-------|
| test_preflight.py | 29 | Startup environment + structure validation |
| test_workflow.py | 36 | GitHub Actions workflow structure, gate blocking |
| test_dashboard_frontend.py | 33 | CSS tokens, layout, empty states, design system |
| test_manage_state_dedup.py | 18 | Dedup scoping, safety bounds, cross-role dedup |
| test_manage_state.py | 65+ | State subcommands (cleanup, sync, dedup, validate-schema) |
| test_verify_html.py | 15 | CSS-context-aware color detection |
| test_claude_md.py | 12 | CLAUDE.md structure, UX rules, agent tiers |
| test_salary_penalty.py | 4 | Salary validation penalty rules |
| test_filter_jobs.py | 3 | Title exclusion filtering |
| test_summarize_jobs.py | 3 | Job summary output |

### Gate System
- **Preflight gates** (startup): Dashboard URL, permissions, manage_state.py executable, agent YAML, model tiers
- **Schema validation gate** (Phase 1→2): `manage_state.py validate-schema` — blocking
- **Dedup safety bound** (Phase 3): >50% archival rate → abort
- **Phase 2+ PRE-GATE**: Every phase begins with `checkpoint validate`
- **No skip heuristic**: Tests enforce "Do NOT skip" language

### Agent Memory
4 agents maintain persistent memory (`.claude/agent-memory/*/MEMORY.md`):
- **search-verify**: Source effectiveness per channel, search patterns, AI company findings, scoring notes
- **digest-email**: Directory mapping quirks, score field resolution order, still-active rendering rules, score thresholds
- **brief-generator**: Empty
- **briefs-html**: Empty

### Search Channels (5 mandatory)
1. Direct Career Pages — 33 AI companies with career URLs
2. Industry Job Boards — 11 boards (YC Jobs, Wellfound, AI Jobs, Cord, Otta, etc.)
3. JobSpy Aggregator — 14 keyword queries across LinkedIn/Indeed/Glassdoor
4. Niche Newsletters — Discovery-based (Early & Exec primary)
5. Web Search Discovery — Open-ended queries adapted per run

## External Landscape

### Official Documentation Patterns
- **JobSpy**: Board aggregator via single Python API. numpy >=1.26.0. Primary docs on GitHub (no comprehensive docs site). Two packages share "jobspy" name on PyPI — use Cullen Watson's.
- **Resend SDK**: `resend.Emails.send()` with from/to/subject/html. Domain verification required. Test addresses available. Actively maintained (Feb 2026 release).
- **Claude Code Subagents**: Task tool supports sequential/parallel dispatch. Subagents in isolated contexts, no peer communication. 3-4 max recommended.

### Version Constraints
- JobSpy: numpy >=1.26.0, Python 3.9+
- Resend: No breaking constraints; 401=invalid key, 422=unverified domain
- EU AI Act (Aug 2026): Reasoning logs required for candidate-ranking AI — not directly applicable to job-seeker tooling

### Community Conventions
- Rate limiting: randomized delays (1-5s), exponential backoff on 429, user-agent rotation
- AI job search: multi-step pipeline (scan → filter → score → apply), human-over-AI pattern dominant
- Claude Code orchestration: named agents with YAML frontmatter, status file protocol, background dispatch — consistent with JSA architecture

### Gaps
- JobSpy rate limiting behavior and board-specific quirks undocumented
- Resend batch sending rate limits for free tier undocumented
- Claude Code Task tool `model:` parameter undocumented externally
- No JobSpy changelog/migration guide for 2026 versions

## Related Files

All files within `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v24/`:

**Core:**
- `CLAUDE.md`, `context.md`, `state.json`

**Agents (7):**
- `.claude/agents/search-verify.md`, `.claude/agents/onboarding.md`, `.claude/agents/source-researcher.md`
- `.claude/agents/digest-email.md`, `.claude/agents/briefs-html.md`, `.claude/agents/brief-generator.md`
- `.claude/agents/gate-check.md`

**Skills (7):**
- `.claude/skills/jsa-search-verify.md`, `.claude/skills/jsa-onboarding.md`, `.claude/skills/jsa-source-researcher.md`
- `.claude/skills/jsa-design-system.md`, `.claude/skills/jsa-digest-email.md`, `.claude/skills/jsa-briefs-html.md`
- `.claude/skills/jsa-brief-generator.md`

**Scripts (8):**
- `scripts/preflight.sh`, `scripts/jobspy_search.py`, `scripts/filter_jobs.py`, `scripts/manage_state.py`
- `scripts/summarize_jobs.py`, `scripts/send_email.py`, `scripts/preview.sh`, `scripts/verify_html.py`

**References (5):**
- `references/orchestration.md`, `references/presentation-rules.md`, `references/algorithms.md`
- `references/subagent-search-verify.md`, `references/subagent-digest-email.md`

**Tests (8 modules, 195 tests):**
- `tests/test_preflight.py`, `tests/test_workflow.py`, `tests/test_dashboard_frontend.py`
- `tests/test_manage_state_dedup.py`, `tests/test_manage_state.py`, `tests/test_verify_html.py`
- `tests/test_claude_md.py`, `tests/test_salary_penalty.py`, `tests/test_filter_jobs.py`
- `tests/test_summarize_jobs.py`, `tests/conftest.py`

**Agent Memory (4):**
- `.claude/agent-memory/search-verify/MEMORY.md`, `.claude/agent-memory/digest-email/MEMORY.md`
- `.claude/agent-memory/brief-generator/MEMORY.md`, `.claude/agent-memory/briefs-html/MEMORY.md`

**Config:**
- `.env` (API keys), `requirements.txt` (upstash-redis, markdown)

## Historical Context

V24 implemented "Schema-First Fix" — canonical 10-field JSON schema, normalize-on-write, search-verify promoted to Sonnet, blocking gate-checks, dedup auto-scoping, migration script. Build completed 3 phases, 4 commits, 193/195 tests pass.

V24 analysis found 15 failures (1C/10M/4m): preflight first-run detection, context.md format validation, commit+push enforcement (9th recurrence), session-state write enforcement (10th recurrence), 5 UX/CLI issues (new category). 2 architectural fixes (decouple brief generation from briefs-html, token budget awareness) + 14 implementation fixes.

V24 compound extracted 7 decisions, 7 solutions (6 domains + new ux-cli domain), 6 proposals. Failures dropped 25% vs V23 (20→15).

Prior versions: V23 (20 failures, 6 decisions, 6 solutions), V22 (8 failures, 43% reduction), V21 (14 failures), V20 (17 failures), V19 (13 failures), V18 (8 failures), V17 (11 failures).

## Handoff Contract
- Files to modify: CLAUDE.md, agents/*.md, skills/*.md, scripts/, tests/, references/, context.md (if onboarding changes)
- Patterns to preserve: 5-phase workflow, named agent pattern with YAML frontmatter, status file protocol, canonical 10-field schema, design system skill as CSS source of truth, gate-check blocking semantics, dedup safety bounds, agent memory persistence
- Hard constraints discovered: 11 absolute constraints in CLAUDE.md, parent context budget (no subagent-only ops), incremental commit+push after search batches, settings.local.json merge protocol, all subagents background:true, model tier enforcement (Sonnet for writing/reasoning, Haiku for mechanical work)
- Open questions: (1) Should commit+push enforcement become a structural gate rather than a constraint? (9th recurrence), (2) Should session-state write enforcement become a structural gate? (10th recurrence), (3) Are the 2 failing tests (193/195) from V24 build resolved?, (4) Should brief generation be decoupled from briefs-html compilation (V24 architectural fix proposal)?, (5) How to implement token budget awareness / rate limit detection (V24 architectural fix proposal)?

<!-- STAGE COMPLETE: /research full, 2026-02-27 -->

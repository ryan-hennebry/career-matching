# Research: JSA V16 (Post-Build)

## Current State

JSA V16 is a fully operational job search agent that discovers opportunities across 4 role types, verifies listings, generates application briefs, and delivers a daily email digest. It completed its first interactive run on 2026-02-11, producing 18 verified jobs (16 above threshold), 5 briefs, and a sent email digest.

### Architecture

The system follows a parent-orchestrator + named-subagent pattern:

- **Parent orchestrator** (`CLAUDE.md`) — coordinates a 23-step workflow: onboarding → source research → search-verify → present → briefs → digest → email
- **6 named agents** in `.claude/agents/` — each with YAML frontmatter declaring `model: inherit` and preloaded skills
- **7 skills** in `.claude/skills/` — provide instructions, templates, and the design system
- **1 reference doc** (`references/algorithms.md`) — scoring edge cases, normalization patterns, deduplication rules
- **6 Python scripts** in `scripts/` — JobSpy search, filtering, summarization, state management, email delivery, HTML preview
- **1 GitHub Actions workflow** (`.github/workflows/daily-digest.yml`) — weekday 06:00 UTC scheduled runs

### Data Flow

1. User profile stored in `context.md` (persistent configuration)
2. Parent dispatches `source-researcher` → writes `output/_source_research.json` → parent merges into `context.md` sources table
3. Parent dispatches `search-verify` agents (one per role type, batched 2-3) → each writes verified JSON to `output/verified/{role_type_slug}/` + `_status.json` + `_summary.md`
4. Parent runs `manage_state.py sync` → updates `state.json`, writes `output/_delta.json`
5. Parent presents results, collects feedback, dispatches `brief-generator` agents → write `output/briefs/{slug}-brief.md`
6. Parent dispatches `digest-email` + `briefs-html` in parallel → write HTML + `_status.json`
7. Parent sends email via `scripts/send_email.py` (Resend API)

### Named Agents

| Agent | Skills | Purpose |
|-------|--------|---------|
| `onboarding` | jsa-onboarding | Parse CV, extract profile, discover initial sources |
| `source-researcher` | jsa-source-researcher | Discover job sources across 5 categories per industry |
| `search-verify` | jsa-search-verify | Search boards (JobSpy + WebFetch), verify listings, score |
| `brief-generator` | jsa-brief-generator | Generate application brief from verified JSON (no web) |
| `digest-email` | jsa-design-system, jsa-digest-email | Generate email digest HTML |
| `briefs-html` | jsa-design-system, jsa-briefs-html | Compile briefs into single styled HTML |

### Design System

Unified design system defined in `jsa-design-system` skill:
- Fonts: Newsreader (headings), DM Sans (body)
- Colors: warm stone palette (`#1c1917` text, `#f8f8f6` bg-subtle, `#d6d3d1` borders)
- Score accents: green (`#15803d` on `#f0fdf4`) for 90+, stone for 70-89
- Layout: 800px briefs, 600px email
- Links: dark editorial (`#1c1917`, stone underline, font-weight 500)
- Gmail link override CSS included

### Skills Inventory

| Skill | Purpose |
|-------|---------|
| `jsa-design-system` | CSS tokens, typography, colors, layout specs for all visual output |
| `jsa-digest-email` | 7-variable template for email HTML generation |
| `jsa-briefs-html` | 1-variable template for briefs HTML compilation |
| `jsa-onboarding` | CV parsing rules, source discovery, draft output schema |
| `jsa-brief-generator` | 6-section brief structure, no-web-research rule, completion sentinel |
| `jsa-search-verify` | 14-variable template, search + verify + score workflow |
| `jsa-source-researcher` | 4-variable template, 5 source categories, accessibility checking |

### Scripts Inventory

| Script | Purpose |
|--------|---------|
| `jobspy_search.py` | JobSpy wrapper for LinkedIn/Indeed/Glassdoor with location/remote filters |
| `filter_jobs.py` | Title exclusion filter (case-insensitive partial match) |
| `summarize_jobs.py` | One-line summaries with salary formatting |
| `manage_state.py` | State lifecycle: sync verified jobs, compute delta, record user actions |
| `send_email.py` | Resend API email with optional HTML attachment, dotenv loading |
| `preview.sh` | Serve HTML on localhost:8800, auto-open browser |

### State Management

- `state.json` — persistent across runs. Keys: `last_run_date`, `jobs` (keyed by `{role_type}/{slug}`), `expired_jobs`
- Job entry: `title`, `company`, `score`, `role_type`, `source`, `first_seen`, `last_seen`, `active_status`, `job_url`, `location`, `requirements_met`, `user_action`, `expired_date`, `reappeared`
- Delta: `manage_state.py sync` produces `_delta.json` with `new_jobs`, `still_active`, `expired_count`, `rejected_count`
- Jobs not seen for 14 days → expired. >90 days expired → purged.

### Current Run Output (2026-02-11)

**Verified jobs by role type:**
- `community-manager/`: 2 (1inch DAO Community Manager, Crypto.com IRL Community Manager)
- `marketing-manager/`: 5 (Re7 Capital, Wintermute, Dune, Cryptio, Mercuryo)
- `marketing-associate/`: 4 (1inch Social Media Manager, Aztec, Sui Foundation, Wynd Labs)
- `founders-associate/`: 7 (nannie, MAGIC, VenueScanner, Tracebit, Avant Arte, Kernel, Kingpin)

**Briefs generated:** 5 (nannie, Wynd Labs, VenueScanner, Tracebit, Aztec)
**Digest sent:** Yes, to ryanhennebry@gmail.com
**Scheduled runs:** Configured via GitHub Actions (weekday 06:00 UTC)

### Agent Memory (Documented Failures)

**search-verify:**
- WebFetch parallel calls fail with "Sibling tool call errored" — use sequential or max 2 concurrent
- Blocked sources: CryptoJobsList, Remote3, WorkInStartups (old URLs), Escape the City, TrueUp, Flexa, JobsAI Substack, Startups.gallery
- JobSpy: broad queries without location work better; Glassdoor often fails; "Community Manager" results often misclassified
- Scoring: assign neutral 10/20 for missing preferred skills section

**source-researcher:**
- Known-blocked: CryptoJobsList, Wellfound, startup.jobs, TopStartups.io, Welcome to the Jungle, TrueUp, JobsAI Substack, Startups.gallery, Flexa Careers
- High-quality accessible: Web3.Career, CryptoJobs, CryptocurrencyJobs, BeInCrypto, AIJobs.ai, WorkInStartups, Jumpstart, YC Jobs, Techstars
- Substack newsletters return 403; JS-heavy sites return only CSS; Discord/Slack need manual check

### Verified Job JSON Schema

```json
{
  "title": "string",
  "company": "string",
  "location": "string",
  "job_type": "string",
  "work_arrangement": "string",
  "salary_min": "number|null",
  "salary_max": "number|null",
  "currency": "string|null",
  "job_url": "string",
  "source": "string",
  "date_posted": "string|null",
  "active_status": "confirmed|unverified",
  "industry": "string",
  "requirements_met": ["string"],
  "gaps": ["string"],
  "preferred_met": ["string"],
  "score": "integer",
  "score_breakdown": {
    "required_skills": {"points": "int", "calculation": "string"},
    "preferred_skills": {"points": "int", "calculation": "string"},
    "experience_fit": {"points": "int", "calculation": "string"},
    "industry_match": {"points": "int", "calculation": "string"},
    "location_match": {"points": "int", "calculation": "string"}
  },
  "benefits": "string|null",
  "notes": "string",
  "run_date": "string",
  "verified_at": "string"
}
```

## Code References

- `CLAUDE.md` — 23-step orchestration workflow, core rules, presentation format
- `.claude/agents/search-verify.md` — Search-verify agent definition
- `.claude/agents/brief-generator.md` — Brief generator agent definition
- `.claude/agents/digest-email.md` — Digest email agent definition
- `.claude/agents/briefs-html.md` — Briefs HTML agent definition
- `.claude/agents/onboarding.md` — Onboarding agent definition
- `.claude/agents/source-researcher.md` — Source researcher agent definition
- `.claude/skills/jsa-design-system.md` — Unified design system
- `.claude/skills/jsa-search-verify.md` — Search-verify skill
- `.claude/skills/jsa-brief-generator.md` — Brief generator skill
- `.claude/skills/jsa-digest-email.md` — Digest email skill
- `.claude/skills/jsa-briefs-html.md` — Briefs HTML skill
- `.claude/skills/jsa-onboarding.md` — Onboarding skill
- `.claude/skills/jsa-source-researcher.md` — Source researcher skill
- `references/algorithms.md` — Scoring edge cases, normalization, deduplication
- `scripts/manage_state.py` — State lifecycle management
- `scripts/send_email.py` — Resend API email delivery
- `scripts/jobspy_search.py` — JobSpy aggregator wrapper
- `scripts/filter_jobs.py` — Title exclusion filter
- `scripts/summarize_jobs.py` — Job summary generator
- `scripts/preview.sh` — HTML preview server
- `.github/workflows/daily-digest.yml` — Scheduled run workflow
- `context.md` — User profile and configuration
- `state.json` — Persistent job state

## Patterns Found

1. **Named agent pattern:** Agents defined in `.claude/agents/*.md` with YAML frontmatter (`model: inherit`, `skills:` list). Variables passed as compact JSON blobs. Status files signal completion.
2. **Skill preloading:** Skills referenced in agent frontmatter are auto-loaded. Design system skill shared across visual output agents.
3. **Parent-orchestrated email:** Email sending is always done by parent, never delegated to subagent (documented hard constraint from prior failures).
4. **No PDF:** All visual output is HTML. Briefs use border-top separators instead of page breaks.
5. **State management via CLI:** All state mutations go through `manage_state.py` subcommands. No inline Python for state changes.
6. **Source approval gate:** Sources discovered by subagent are presented to user for approval before searching. User can add/remove via numbered selection.
7. **Threshold inclusive:** Score >= 70 qualifies. Threshold is inclusive.
8. **One question per message:** Onboarding asks one question at a time, waits for response.
9. **Batch dispatch:** Search-verify agents dispatched in batches of 2-3 to avoid rate limiting.
10. **Auto-retry once:** Failed subagents get one retry, then logged and skipped.

## Related Files

All files under `03_agents/tests/v16/`:
- `CLAUDE.md`, `context.md`, `state.json`
- `.claude/agents/` (6 agent definitions)
- `.claude/skills/` (7 skills)
- `.claude/agent-memory/search-verify/MEMORY.md`, `.claude/agent-memory/source-researcher/MEMORY.md`
- `references/algorithms.md`
- `scripts/` (6 scripts)
- `.github/workflows/daily-digest.yml`
- `output/` (verified jobs, briefs, digests, delta, session state)
- `.env` (API keys)

## Historical Context

- V15 analysis identified 7 failures and 7 fixes + 1 architectural change
- V16 design chose Option B: separate source research phase + all 7 implementation fixes
- V16 plan: 38 steps + Step 2b, 7 phases, all findings resolved
- V16 reviews: 3 rounds, final verdict approved (0 Required, 0 Recommended, 6 Informational)
- V16 build: all 7 phases complete
- V16 analysis: 9 failures from first interactive run → 2 architectural + 7 implementation fixes

## User-Directed Changes (V17 Scope)

### Duplicate Source Research Elimination

The V16 agent researches sources twice:
1. **Onboarding subagent** (`jsa-onboarding` skill) — discovers initial sources during CV parsing (lines 43-44 in transcript: "Parse CV and discover sources")
2. **Source-researcher subagent** (Step 8 in orchestration) — performs deep industry source discovery with user approval

The onboarding source discovery is redundant. Only the deep source-researcher search (Step 8) should persist. The onboarding subagent should parse the CV and extract the profile only — no source discovery. This saves tokens and eliminates a slow, unnecessary step.

### V17 Dashboard Integration

The next version must integrate the dashboard design documented in `docs/plans/active/jsa-v17-dashboard-design.md`. This is a major addition:

**What it adds:**
- Vercel-hosted web app (Python serverless functions + vanilla HTML/CSS/JS)
- Daily digest view, job pipeline tracker, inline brief viewer, run controls
- Git-deploy hybrid architecture: static job data bundled in deploy, user actions in Upstash Redis
- GitHub Actions workflow dispatch for "Run Now" from dashboard
- Design system evolution: new interactive tokens (buttons, inputs, focus rings, hover states), elevation system, pipeline status tokens, spacing scale — all extending the existing warm stone editorial palette

**Architecture:**
- `api/*.py` — 8 serverless functions (state, jobs, job detail, actions, briefs, pipeline, context, run controls)
- `public/` — SPA shell with vanilla JS (router, components, API client)
- Upstash Redis — user action storage (the only mutable state)
- GitHub Actions — run controls proxy (keeps PAT server-side)
- Data flow: Claude orchestrator → git commit → Vercel auto-deploy → dashboard reads bundled files + Redis

**Design system extensions:**
- Interactive tokens: `--btn-bg`, `--btn-text`, `--btn-secondary-*`, `--btn-ghost-*`, `--focus-ring`, `--input-*`
- Elevation: borders-only depth (no shadows on cards), dropdown shadow only for floating elements
- Active/selected states: sidebar active border, card selected border
- Pipeline status tokens: new/reviewing/brief/applied/rejected/expired with warm semantic colors
- Spacing scale: 4px–48px
- Transitions: 120ms fast, 200ms base

**Key constraints from dashboard design:**
- No blue anywhere (no `#2563eb`, no blue focus rings)
- No shadows on cards (borders-only editorial depth)
- No rounded pill buttons (sharp 4px radius)
- No sidebar with different background color (border separation only)
- No icons without text labels
- Cost: $0 (Vercel Hobby + Upstash free + GitHub Actions free)

**10 build steps** defined in the dashboard design doc, from Vercel/Upstash/Actions setup through polish.

## Handoff Contract

- **Files to modify:** `CLAUDE.md` (orchestration rules), `.claude/skills/jsa-search-verify.md` (scoring), `.claude/skills/jsa-digest-email.md` (presentation), `.claude/skills/jsa-onboarding.md` (remove source discovery), `.claude/skills/jsa-design-system.md` (extend with dashboard tokens), `references/algorithms.md` (validation rules), `scripts/preview.sh` (server persistence), named agent definitions as needed. **New files:** `api/*.py` (8 serverless functions), `public/` (SPA shell + CSS + JS), `vercel.json`, `requirements.txt`, `.github/workflows/jsa-search.yml`
- **Patterns to preserve:** Named agent pattern with YAML frontmatter, skill preloading, parent-orchestrated email, state management via CLI, design system in shared skill, one-question-per-message onboarding, batch dispatch, no PDF
- **Hard constraints discovered:**
  - Threshold is inclusive (>=70)
  - Auto-retry always via subagent dispatch (never inline)
  - No email confirmation prompt — send after checks pass
  - Ask target roles explicitly even when inferred from CV
  - preview.sh server killed by trap on script exit — needs background process
  - Salary validation must happen in scoring (Re7 Capital scored 92 despite being below salary minimum)
  - Numbered selection view must be used for ALL user-facing lists requiring selection
  - Session-state.md must be written after every search batch, not just at end
  - Onboarding subagent must NOT discover sources (only deep search-researcher persists)
  - Dashboard design system must extend existing tokens, not replace them
  - No blue anywhere in dashboard — warm stone/ink interactive palette
  - Dashboard uses Git-committed static data + Upstash Redis for user actions only
- **Open questions (to resolve in /design):**
  - Should salary-below-minimum be a hard filter (exclude entirely) or a soft flag (include with warning)?
  - Should the unified numbered selection view apply to brief selection only, or also to source approval?
  - How does the dashboard interact with the CLI orchestrator's state.json? Does state.json get replaced by Upstash, or do they coexist?
  - Does the email digest continue alongside the dashboard, or does the dashboard replace it?
  - How do briefs get generated from the dashboard? (Currently requires Claude agent — dashboard "Run Now" only runs JobSpy)
  - Should the V16→V17 migration happen in-place or as a new directory (`03_agents/tests/v17/`)?
- **Base commit (V16 build start):** `9fb0441` (chore: clear agent memory and strip personal data from V16 context)
- **Analysis handoff:** 2 architectural fixes (unified numbered selection view, salary validation in scoring/presentation) + 7 implementation fixes (off-by-one threshold, auto-retry subagent dispatch, recovery subagent protocol, preview.sh fix, no-confirmation email send, session-state checkpoint promotion, explicit target roles question)
- **User-directed additions:** Remove duplicate source research from onboarding, integrate V17 dashboard design (`docs/plans/active/jsa-v17-dashboard-design.md`)

<!-- STAGE COMPLETE: /research full, 2026-02-11 -->

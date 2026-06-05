# Design: JSA V17 — Dashboard + 9 Fixes

## Context

V16 completed a full interactive run: 16 jobs found, 5 briefs generated, email sent. The analysis identified 9 failures (2 architectural, 7 implementation). Additionally, the user wants to integrate a Vercel-hosted dashboard as the primary viewing interface, and remove duplicate source research from onboarding.

**Inputs:**
- `jsa-v16-analysis.md` — 9 failures, 2 architectural + 7 implementation
- `jsa-v17-dashboard-design.md` — Full dashboard design (Vercel + Upstash + GitHub Actions)
- `jsa-v16-research.md` — Post-build research with handoff contract

---

## Options Considered

### Option A: Incremental Fixes + Additive Dashboard
- Apply all 9 V16 fixes to a new `03_agents/tests/v17/` directory (copy V16, modify)
- Build dashboard as a separate layer that reads Git-committed output files
- CLI and dashboard are loosely coupled — Git is the sync mechanism, Upstash for user actions
- Dashboard extends the existing design system (single canonical file)
- **Pros:** Low risk, fixes are well-understood, dashboard is additive, CLI stays functional independently
- **Cons:** Two interfaces to maintain (CLI + dashboard + email), some code duplication
- **Risk level:** Medium (dashboard is new, but built on proven data)
- **Complexity:** Moderate

### Option B: Unified Architecture Redesign
- Redesign the agent around the dashboard as the primary orchestrator
- CLI becomes a headless backend that the dashboard calls
- Tighter coupling — dashboard drives the pipeline, CLI executes
- **Pros:** More cohesive, single interface, no state sync issues
- **Cons:** High risk, requires building an agent runtime in serverless, fundamentally different from V16
- **Risk level:** High
- **Complexity:** Complex

## Chosen Approach

**Option A: Incremental Fixes + Additive Dashboard**

Why: V16's pipeline works. The 9 fixes are well-scoped. The dashboard is a viewer that reads from Git-committed files — it doesn't need to control the pipeline. This preserves the working system while adding a better interface. The chat interface (V18) is when the dashboard becomes the primary orchestrator.

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│  CLI Agent (Claude Code)                                 │
│  ┌─────────┐ ┌──────────┐ ┌───────┐ ┌───────┐ ┌─────┐ │
│  │Onboarding│→│Source Res.│→│Search │→│Briefs │→│Email│ │
│  │(profile) │ │(explicit)│ │+Verify│ │+HTML  │ │+Push│ │
│  └─────────┘ └──────────┘ └───────┘ └───────┘ └─────┘ │
│       ↓ commit+push after each stage                     │
└──────────────────────┬──────────────────────────────────┘
                       │ Git
┌──────────────────────▼──────────────────────────────────┐
│  Vercel Dashboard                                        │
│  ┌─────────┐ ┌──────────┐ ┌───────┐ ┌──────┐ ┌──────┐ │
│  │Summary  │ │Pipeline  │ │Job    │ │Brief │ │Run   │ │
│  │Strip    │ │Sidebar   │ │Detail │ │Viewer│ │Now   │ │
│  └─────────┘ └──────────┘ └───────┘ └──────┘ └──────┘ │
│       ↕ Upstash Redis (user actions: accept/reject)      │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **CLI Agent** | Full pipeline: onboarding, source research, search+verify, briefs, email, Git push |
| **Dashboard (Vercel)** | Read-only view of Git-committed data + user actions via Upstash |
| **Upstash Redis** | User actions only (accept/reject/brief_requested). Read by dashboard AND optionally by CLI |
| **GitHub Actions** | "Run Now" triggers JobSpy search only. Commits results + pushes → Vercel redeploys |
| **Git** | Sync mechanism between CLI and dashboard. Source of truth for job data |

### Data Flow

**Write path (CLI → Dashboard):**
1. CLI agent runs pipeline locally
2. After each stage: `git add output/ && git commit && git push`
3. Vercel auto-deploys in ~30s
4. Dashboard reads fresh data from bundled files

**Read path (Dashboard):**
1. Serverless functions read bundled output files (verified JSONs, briefs, delta, context)
2. Merge with Upstash user actions (accept/reject/brief_requested)
3. Derive pipeline stage from user actions + first_seen date
4. Render views

**User action path (Dashboard → Upstash):**
1. User clicks Accept/Reject/Request Brief on dashboard
2. `POST /api/action` → writes to Upstash Redis
3. Optimistic UI update
4. CLI optionally reads Upstash rejections before brief generation

**Run Now path (Dashboard → GitHub Actions):**
1. User clicks "Run Now", selects role types
2. `POST /api/run` → proxies to GitHub Actions workflow dispatch
3. GitHub Actions runs `jobspy_search.py`
4. Workflow commits results + pushes → Vercel redeploys
5. Dashboard polls `GET /api/run/status` for progress

### Pipeline Stage Derivation

```
user_action == null  + first_seen == last_run_date  → "new"
user_action == null  + first_seen <  last_run_date  → "reviewing"
user_action == "brief_requested"                    → "brief_requested"
user_action == "accepted"                           → "applied"
user_action == "rejected"                           → "rejected"
In expired_jobs dict                                → "expired"
```

### State Management

| Data | Source of Truth | Access |
|------|----------------|--------|
| Job data (verified JSONs) | Git (output/verified/) | CLI writes, dashboard reads |
| Briefs (markdown) | Git (output/briefs/) | CLI writes, dashboard reads |
| Delta (new/active) | Git (output/_delta.json) | CLI writes, dashboard reads |
| User profile | Git (context.md) | CLI writes, dashboard reads |
| User actions | Upstash Redis | Dashboard writes, both read |
| Pipeline progress | Git (output/ file existence) | CLI writes, dashboard infers |
| Run state | state.json (Git-committed) | CLI writes, dashboard reads |

---

## V16 Fixes (applied to V17 codebase)

### Architectural Fix 1: Unified Numbered Selection View
- After per-role-type tables, show a single ranked-by-score table with row numbers 1-N
- Apply to ALL user-facing selections: sources, jobs, role types
- Pattern: present grouped tables for context, then unified numbered list for selection

### Architectural Fix 2: Salary Validation
- -10pt score penalty for jobs clearly below user's salary minimum (£40K)
- Penalty applied in scoring algorithm (references/algorithms.md)
- Job still visible but demoted — can't outrank salary-compliant jobs of similar quality
- Visual: tagged with "Below Salary Minimum" in presentation

### Implementation Fixes 3-9
3. **Threshold inclusivity:** "score >= 70" (not > 70)
4. **Auto-retry via subagent:** "Retry as a subagent dispatch via Task tool — never inline in parent"
5. **Recovery subagent:** On partial failure, dispatch recovery subagent to read outputs and write summary
6. **preview.sh persistence:** Background server with nohup, write PID to file, no trap cleanup
7. **No email confirmation:** Send immediately after pre-send gate checks pass
8. **Session-state per-batch:** Promote to CORE RULE — write after every search batch
9. **Explicit target roles:** Ask "What types of roles are you targeting?" even when inferred

### Additional Fix: Remove Duplicate Source Research
- Onboarding extracts profile only (CV, roles, constraints, delivery). No source discovery.
- Source research is a separate explicit step after onboarding completes
- Only the deep source-researcher agent persists

---

## Dashboard Architecture

### File Structure

```
03_agents/tests/v17/
├── api/                           # Vercel Python serverless functions
│   ├── state.py                   # GET /api/state — summary counts
│   ├── jobs.py                    # GET /api/jobs — job list + scores + pipeline stage
│   ├── job.py                     # GET /api/job?key=... — single job detail
│   ├── action.py                  # POST /api/action — write user action to Upstash
│   ├── brief.py                   # GET /api/brief?key=... — render individual markdown brief
│   ├── pipeline.py                # GET /api/pipeline — jobs grouped by stage
│   ├── context.py                 # GET /api/context — profile summary
│   └── run.py                     # POST /api/run — trigger GitHub Actions (JobSpy)
│                                  # GET /api/run/status — poll workflow status
├── public/
│   ├── index.html                 # SPA shell
│   ├── css/
│   │   └── dashboard.css          # Full design system (base + dashboard extensions)
│   └── js/
│       ├── api.js                 # API client
│       ├── components.js          # UI renderers
│       └── app.js                 # Router + views
├── .github/workflows/
│   └── jsa-search.yml             # GitHub Actions — JobSpy search workflow
├── vercel.json                    # Routing + function config
└── requirements.txt               # upstash-redis, markdown
```

### Dashboard Views

1. **Daily Digest (default):** Summary strip + "New Today" + "Still Active" sections
2. **Pipeline:** Sidebar stages + filtered job list
3. **Job Detail:** Full score breakdown, requirements, gaps, action buttons
4. **Brief Viewer:** Individual markdown brief rendered with design system styling
5. **Sources:** Profile sources list (read from context.md)
6. **Pipeline Progress:** "Run in progress" indicator when partial data detected

### Design System Extensions

Single canonical `jsa-design-system.md` with new "Dashboard Extensions" section:
- Interactive tokens (buttons: ink on stone, focus rings: stone not blue, inputs: inset bg)
- Elevation (borders-only depth, shadow only for floating elements)
- Active/selected states (sidebar accent, card selected border)
- Pipeline status tokens (semantic warm variants)
- Spacing scale (4px base, 4-48px range)
- Transitions (120ms fast, 200ms base)

**Hard rule:** No blue anywhere. All interactive elements use warm stone/ink palette.

### Email Evolution

- Full rich digest continues (same as V16 quality)
- Each job card gains a "View on Dashboard" link
- Briefs HTML attached as before
- Design system shared between email, briefs HTML, and dashboard

---

## Implementation Phases

### Phase 1: Foundation
- Create v17/ directory (copy V16)
- Apply all 9 fixes to CLAUDE.md, skills, agents, scripts
- Remove source discovery from onboarding skill
- Add salary penalty to scoring algorithm
- Add unified numbered selection view to presentation workflow

### Phase 2: Design System Extension
- Extend jsa-design-system.md with dashboard tokens
- Interactive states, spacing scale, status tokens, transitions

### Phase 3: Infrastructure
- vercel.json, requirements.txt
- .github/workflows/jsa-search.yml
- Upstash integration helper (shared between API functions)

### Phase 4: Backend (Serverless Functions)
- 8 API endpoints (state, jobs, job, action, brief, pipeline, context, run)
- Git-committed file reading + Upstash merging

### Phase 5: Frontend Shell + CSS
- index.html SPA shell
- dashboard.css (full design system)
- Summary strip, sidebar, layout grid

### Phase 6: Frontend Views + Interactivity
- Daily digest view, pipeline view, job detail, brief viewer
- API client, components, router
- User actions (Upstash writes)
- Run controls (GitHub Actions dispatch)
- Pipeline progress indicator

### Phase 7: Email Evolution
- Add "View on Dashboard" links to digest email template
- CLI incremental commit+push after each pipeline stage

### Phase 8: CLI-Upstash Integration
- Optional Upstash read in CLI for rejection filtering
- Graceful degradation when credentials absent

---

## Success Criteria

1. All 9 V16 failures fixed and verifiable
2. Dashboard deployed on Vercel with warm stone/ink aesthetic
3. Dashboard shows real V16 output data (verified jobs, briefs, pipeline)
4. User actions (accept/reject) persist in Upstash across page refreshes
5. "Run Now" triggers GitHub Actions JobSpy search
6. Email digest includes "View on Dashboard" links
7. CLI incremental pushes trigger Vercel redeployments
8. Design system is unified — email, briefs HTML, and dashboard share tokens
9. No blue anywhere in dashboard
10. Score badges match existing pattern (green 90+, default 80-89, muted 70-79)

---

## Risks

| Risk | Mitigation |
|------|-----------|
| V17 scope is large (~8 phases) | Phase 1 (fixes) is independent of dashboard — can ship fixes first |
| Vercel Python serverless cold starts | Free tier has ~250ms cold starts. Acceptable for personal tool |
| Upstash free tier limits (10K commands/day) | Dashboard + CLI combined won't approach this for a personal tool |
| GitHub Actions PAT management | Fine-grained PAT with minimal scope (actions:write only). GITHUB_TOKEN for commits |
| Design system divergence between email/dashboard | Single canonical skill file prevents drift |
| Incremental pushes during CLI run could show partial data | Pipeline progress indicator in dashboard handles this |

---

## Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Salary below minimum | -10pt soft penalty | Visible but demoted. User decides, not the system |
| Email digest | Keep full digest + dashboard links | Push notification AND pull interface |
| Numbered selection | All user-facing selections | Consistent UX pattern |
| Run Now scope | JobSpy only (V17), full pipeline (V18) | Scope control |
| Chat interface | Deferred to V18 | Massive additional complexity |
| Directory | New v17/ | Clean separation from V16 |
| Source research | Separate from onboarding | Faster onboarding, no duplication |
| Design tokens | Single canonical file | One source of truth |
| Push timing | After each stage | Dashboard shows incremental progress |
| Rejection sync | CLI reads Upstash (optional) | Graceful degradation without credentials |
| Brief rendering | Individual markdown via /api/brief | Simpler routing, better detail views |
| PAT scope | GITHUB_TOKEN + separate PAT | Minimal scope per token |
| API cost | Doesn't matter | Personal tool |
| State sync | Git + Upstash split | Different purposes, no sync problem |
| Device | Desktop primary | Basic 768px responsive breakpoint |
| Domain | Default vercel.app | Zero DNS work |
| Build scope | Don't exclude non-dashboard files | Vercel only serves api/ + public/ |

---

## Handoff Contract

- **Approach:** Option A — Incremental V16 fixes + additive Vercel dashboard
- **Components:**
  - CLI Agent (9 fixes applied to copied V16 code)
  - Dashboard (8 serverless functions + vanilla SPA)
  - Design System (extended with dashboard tokens)
  - GitHub Actions (JobSpy workflow dispatch)
  - Email (full digest + dashboard links)
- **Success criteria:**
  - All 9 V16 failures fixed
  - Dashboard deployed on Vercel showing real data
  - User actions persist in Upstash
  - "Run Now" triggers GitHub Actions
  - Design system unified across all outputs
  - No blue in dashboard
- **Risks requiring mitigation:**
  - Scope (8 phases) — fixes are independent, can ship first
  - Partial data during incremental pushes — progress indicator
  - Design system divergence — single canonical file

<!-- STAGE COMPLETE: /design, 2026-02-11 -->

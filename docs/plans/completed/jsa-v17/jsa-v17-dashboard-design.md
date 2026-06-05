# JSA V17 — Dashboard Design (Pre-Design Input)

> **Status:** Draft — to be incorporated during V17 `/design` phase
> **Origin:** Interface design exploration session (2026-02-11)
> **Workflow note:** After running `/analyze` on the V16 transcript, this document should be included as input during the `/design` phase before moving to `/plan`. The design system evolution section is the critical addition — it must be resolved during `/design`, not deferred to `/plan`.

---

## What We're Building

A Vercel-hosted web app (Python serverless functions + vanilla HTML/CSS/JS) that replaces the CLI interaction for the Job Search Agent. This is an editorial strategy desk — warm, focused, unhurried.

**Features:** Daily digest view, job pipeline tracker, inline brief viewer, run controls.

Run controls trigger GitHub Actions workflows for job searches.

**Location:** Root of `03_agents/tests/v17/` (Vercel convention)

**Hosting:** Vercel Hobby (free) + Upstash Redis (free tier) + GitHub Actions (free tier). Total cost: $0.

---

## Design System Evolution

The existing design system (`jsa-design-system.md`) was built for documents — email HTML and briefs HTML. Single-column, read-only, scroll-down formats. It's genuinely strong: Newsreader + DM Sans is a distinctive pairing, the warm stone palette feels editorial, the score badge pattern works.

But a dashboard is interactive. The current system has **zero** interactive tokens — no buttons, no hover states, no focus rings, no inputs, no elevation, no active states, no semantic status colors, no spacing scale. These gaps must be filled without breaking the editorial identity.

### What stays exactly the same
- Newsreader + DM Sans font pairing (all sizes/weights)
- Warm stone color world: `--bg` (#fff), `--bg-subtle` (#f8f8f6), `--bg-inset` (#f0efeb), all text hierarchy, all border hierarchy
- Score badge pattern (green/default/muted)
- Card surface treatment (bg-subtle + border + 4px radius)
- Table styling (uppercase tracked headers, inset background)
- Link styling (dark editorial, stone underline)

### What gets added (dashboard-specific extensions)

**Interactive tokens (new):**
```css
/* Buttons — ink on stone, not blue on white */
--btn-bg: #1c1917;              /* Primary: warm black */
--btn-text: #ffffff;
--btn-bg-hover: #292524;
--btn-secondary-bg: transparent;
--btn-secondary-border: #d6d3d1;
--btn-secondary-hover-bg: #f8f8f6;
--btn-ghost-hover-bg: #f0efeb;

/* Focus ring — visible but not jarring */
--focus-ring: #78716c;          /* Stone, not blue */
--focus-ring-offset: 2px;

/* Inputs */
--input-bg: #f8f8f6;           /* Slightly inset, not white */
--input-border: #d6d3d1;
--input-border-focus: #1c1917;
```

**Elevation system (new):**
```css
/* Borders-only depth — matches the editorial flatness */
--shadow-sm: none;              /* Cards use borders, not shadows */
--shadow-dropdown: 0 4px 12px rgba(28,25,23,0.08);  /* Only for floating elements */
--overlay-bg: rgba(28,25,23,0.3);  /* Modal/drawer backdrop */
```

**Active/selected states (new):**
```css
--sidebar-active-border: #1c1917;   /* Left border accent */
--sidebar-active-bg: #f8f8f6;
--sidebar-hover-bg: #f0efeb;
--card-selected-border: #1c1917;    /* Stronger border when selected */
```

**Pipeline status tokens (new):**
```css
/* Semantic — warm variants, not neon */
--status-new: #1c1917;          /* Ink — strong, demands attention */
--status-new-bg: #f0efeb;
--status-reviewing: #57534e;    /* Secondary — passive */
--status-brief: #15803d;        /* Reuse score green — action taken */
--status-brief-bg: #f0fdf4;
--status-applied: #15803d;
--status-applied-bg: #f0fdf4;
--status-rejected: #a8a29e;     /* Tertiary — dimmed */
--status-expired: #a8a29e;
```

**Spacing scale (new):**
```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
```

**Transitions (new):**
```css
--transition-fast: 120ms ease;
--transition-base: 200ms ease;
```

### Design signature

The signature element is the **summary strip** — the `--bg-inset` bar with uppercase tracked stats. In the email it's a single line. In the dashboard it becomes a persistent top bar: run date, pipeline counts, last-run status. It's the editorial masthead — always visible, grounding the whole interface.

### What will NOT be done
- No shadows on cards (borders-only depth — editorial, not SaaS)
- No blue anywhere (no `#2563eb`, no blue focus rings)
- No rounded pill buttons (sharp 4px radius everywhere, matching cards)
- No sidebar with a different background color (same as canvas, border separation only)
- No icons without text labels (the user isn't a power user)

---

## Architecture: Git-Deploy Hybrid + GitHub Actions

### Data Storage

**Static data (bundled with each Git deploy):**
- `output/verified/{role_type}/*.json` — job details (~76KB total)
- `output/briefs/*.md` — brief markdown files
- `output/_delta.json` — new/active classification
- `context.md` — user profile

**Dynamic data (Upstash Redis):**
- User actions (accept/reject/brief_requested) — the ONLY mutable state

### Write Path (orchestrator → dashboard)
1. Claude orchestrator runs locally (unchanged)
2. Outputs written to `output/` (unchanged)
3. Orchestrator commits + pushes to Git
4. Vercel auto-deploys in ~30s

### Read Path (dashboard)
- Serverless functions read bundled files from deploy + merge user actions from Upstash

### Run Controls (GitHub Actions Workflow Dispatch)

**How it works:**
1. User clicks "Run Now" on dashboard, selects role types
2. Dashboard JS calls `POST /api/run` → serverless function proxies to GitHub REST API: `POST /repos/{owner}/{repo}/actions/workflows/jsa-search.yml/dispatches`
3. GitHub spins up a runner, runs `jobspy_search.py` for selected role types
4. Workflow commits results to repo + pushes → triggers Vercel redeploy
5. Dashboard polls `GET /api/run/status` for workflow status (pending → in_progress → completed)
6. On completion, dashboard refreshes to show new jobs

**Requirements:**
- `.github/workflows/jsa-search.yml` workflow file
- GitHub fine-grained PAT with `actions:write` scope → stored as Vercel env var `GITHUB_PAT`
- Dashboard JS needs GitHub API client for dispatch + status polling (via `/api/run` proxy)

**UX:**
- "Run Now" → role type checkboxes → "Searching... (running on GitHub Actions)" → status updates → "Complete — X new results. Vercel redeploying..." → auto-refresh
- ~3-5 min total from button click to results visible
- Future upgrade: add Anthropic API key as GitHub secret → run full Claude verification from Actions too

---

## File Structure

```
03_agents/tests/v17/
├── .github/
│   └── workflows/
│       └── jsa-search.yml    # GitHub Actions — JobSpy search workflow
├── api/
│   ├── state.py              # GET /api/state — summary counts
│   ├── jobs.py               # GET /api/jobs — job list with scores
│   ├── job.py                # GET /api/job?key=... — single job detail
│   ├── action.py             # POST /api/action — write user action to Upstash
│   ├── brief.py              # GET /api/brief?key=... — render markdown brief
│   ├── pipeline.py           # GET /api/pipeline — jobs grouped by stage
│   ├── context.py            # GET /api/context — profile summary
│   └── run.py                # POST /api/run — trigger GitHub Actions search
│                             # GET /api/run/status — poll workflow status
├── public/
│   ├── index.html            # SPA shell
│   ├── css/
│   │   └── dashboard.css     # Design system + layout
│   └── js/
│       ├── api.js            # API client (incl. GitHub Actions dispatch)
│       ├── components.js     # UI renderers
│       └── app.js            # Router + views
├── scripts/                  # Orchestrator-only (not deployed by Vercel)
│   ├── manage_state.py
│   ├── jobspy_search.py
│   └── send_email.py
├── output/                   # Committed after each run
├── context.md
├── vercel.json
└── requirements.txt          # upstash-redis, markdown
```

No build step, no framework.

---

## Build Steps (10 steps)

### Step 0: Vercel + Upstash + GitHub Actions setup

- Connect GitHub repo to Vercel
- Install Upstash Redis integration (auto-injects `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` env vars)
- Create GitHub fine-grained PAT with `actions:write` scope
- Add `GITHUB_PAT` as Vercel env var
- Create `vercel.json` (rewrites for `api/` functions, `public/` static serving)
- Create `requirements.txt` (`upstash-redis`, `markdown`)
- Create `.github/workflows/jsa-search.yml` (workflow dispatch with `role_types` input, runs `jobspy_search.py`, commits + pushes results)

**Verify:** `vercel dev` starts locally. Upstash Redis connection succeeds. GitHub Actions workflow file is valid YAML.

### Step 1: Backend — serverless functions

Create `api/*.py` serverless functions. Each exports a handler compatible with Vercel's Python runtime.

- `api/state.py` — `GET /api/state`: read bundled `output/_delta.json` + merge Upstash user actions, return summary counts
- `api/jobs.py` — `GET /api/jobs`: read bundled verified JSONs, derive pipeline stage from Upstash `user_action` + `first_seen`, sort by score descending
- `api/job.py` — `GET /api/job?key=...`: read full verified JSON from bundled `output/verified/{role_type}/{slug}.json`
- `api/action.py` — `POST /api/action`: body `{"key": "...", "action": "brief_requested"|"accepted"|"rejected"}`. Write to Upstash Redis.
- `api/brief.py` — `GET /api/brief?key=...`: read brief markdown from bundled `output/briefs/`, render to HTML via `markdown` library
- `api/pipeline.py` — `GET /api/pipeline`: group jobs by derived stage, return `{stage: {count, jobs}}`
- `api/context.py` — `GET /api/context`: parse bundled `context.md` for profile summary, sources, target roles
- `api/run.py` — `POST /api/run`: body `{"role_types": [...]}`. Proxy to GitHub REST API workflow dispatch (keeps PAT server-side). `GET /api/run/status`: poll GitHub API for workflow run status.

**Pipeline stage derivation:**
```
user_action == null  + first_seen == last_run_date  → "new"
user_action == null  + first_seen <  last_run_date  → "reviewing"
user_action == "brief_requested"                    → "brief_requested"
user_action == "accepted"                           → "applied"
user_action == "rejected"                           → "rejected"
In expired_jobs dict                                → "expired"
```

**Verify:** `vercel dev` → `curl localhost:3000/api/state` returns JSON. `curl localhost:3000/api/jobs` returns job list.

### Step 2: HTML shell + CSS foundation

Create `public/index.html`:
- Single-page shell with `<head>` (Google Fonts link, `css/dashboard.css`)
- Top bar: summary strip (run date, pipeline counts, "Run Now" button)
- Left sidebar: pipeline stage list with counts
- Main content: `<div id="content">` swapped by JS
- Script tags: `js/api.js`, `js/components.js`, `js/app.js`

Create `public/css/dashboard.css`:
- All CSS custom properties (existing design system tokens + new dashboard extensions)
- Layout: CSS Grid — `240px` sidebar + fluid main (max-width `800px`, centered)
- Typography: exact sizes from design system
- Component patterns: job card, score badge, summary strip, buttons (primary/secondary/ghost), sidebar items
- Responsive: below 768px sidebar collapses to horizontal scrolling tab bar at top

**Verify:** Open Vercel preview URL — correct fonts load, layout renders, warm stone palette visible.

### Step 3: Daily Digest view (default)

`public/js/api.js`: API client wrappers for all endpoints (incl. GitHub Actions dispatch via `/api/run`).

`public/js/components.js`:
- `renderScoreBadge(score)` → green/default/muted badge
- `renderJobCard(job, options)` → card with score, title, company, location, source, action buttons
- `renderSummaryStrip(stats)` → top bar content
- `renderJobList(jobs, heading)` → section with heading + cards
- `renderEmptyState(message)` → helpful empty message

`public/js/app.js`:
- Client-side router: `navigate(view, params)`
- Views: `digest`, `pipeline`, `detail`, `brief`, `sources`
- On load: fetch state + jobs, render summary strip, render "New Today" + "Still Active" sections

**Verify:** Dashboard shows real jobs, sorted by score, correct badge colors.

### Step 4: Job detail view

Click a job card → main area shows full detail:
- Score badge (large), title, company, location
- Score breakdown table (5 factors with points and calculation)
- Requirements met (checkmark list), gaps, preferred met
- Benefits, notes, salary info
- Action buttons row (contextual based on current `user_action`)

**Verify:** Click any job → see full score breakdown, all fields rendered. Back link works.

### Step 5: Pipeline sidebar

Wire sidebar to show stages from `GET /api/pipeline`. Active stage gets left border accent. Rejected/Expired dimmed. Clicking filters main content.

**Verify:** Sidebar counts match job distribution. Clicking filters correctly.

### Step 6: User actions (Upstash Redis)

Wire action buttons to `POST /api/action`. Serverless function writes to Upstash Redis. Optimistic UI update. Re-fetch pipeline counts after action.

**Verify:** Actions persist on refresh. Upstash Redis reflects changes (not local `state.json`).

### Step 7: Brief viewer

"View Brief" on jobs with briefs. `api/brief.py` renders markdown → HTML. Full-width view with design system styling.

**Verify:** Rendered brief displays correctly. Back navigation works.

### Step 8: Run controls (GitHub Actions)

- "Run Now" button opens run panel with role type checkboxes
- `POST /api/run` proxies to GitHub Actions workflow dispatch (keeps PAT server-side)
- `GET /api/run/status` polls GitHub API for workflow run status
- Dashboard shows progress: "Triggered → Running → Complete → Redeploying..."
- On completion, prompt user to refresh (or auto-refresh after Vercel deploy webhook)
- Clear note: "Full verification requires Claude agent — this runs JobSpy search only"

**Verify:** "Run Now" → triggers GitHub Actions workflow (visible in GitHub Actions tab). Poll status shows progress. On completion, Vercel redeploys with new data. New jobs visible on refresh.

### Step 9: Polish + empty states

Empty states, error handling, sources view, past digest links.

---

## Key Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Backend | Vercel Python serverless functions | No server management, auto-scales |
| Frontend | Vanilla JS | No build step, matches project simplicity |
| State storage | Upstash Redis (user actions only) | Free, serverless-native |
| Job data | Git-committed files bundled in deploy | Immutable between runs, <100KB |
| Brief rendering | Python `markdown` lib in serverless fn | Server-side, consistent with design system |
| Run controls | GitHub Actions Workflow Dispatch | No time limits, full Python env, can expand to verification |
| Run progress | Poll GitHub API via `/api/run/status` | Simple, reliable |
| Deployment | Git push → Vercel auto-deploy | Zero-config CD |
| Depth strategy | Borders-only | Matches editorial flatness, floating elements only get shadow |
| Sidebar bg | Same as canvas | Border separation, not color separation |
| Cost | $0 (Hobby + Upstash + GitHub Actions free tiers) | Personal tool |

---

## Critical Files

| File | Role |
|------|------|
| `api/*.py` | Serverless functions (state, jobs, actions, briefs, run controls) |
| `api/run.py` | GitHub Actions dispatch proxy + status polling |
| `.github/workflows/jsa-search.yml` | GitHub Actions workflow for JobSpy search |
| `vercel.json` | Vercel routing + function config |
| `.claude/skills/jsa-design-system.md` | Canonical design tokens (to be extended) |
| `output/verified/{role_type}/*.json` | Full job detail (score_breakdown, gaps, benefits) |
| `output/briefs/*.md` | Brief content for inline viewer |
| `context.md` | Profile, sources, target roles |
| `output/_delta.json` | New/still-active classification |
| `scripts/jobspy_search.py` | Run by GitHub Actions workflow |

---

## Verification

After all steps (using Vercel preview/production URL):
1. Vercel deployment URL — styled layout with warm stone palette, Newsreader headings, DM Sans body
2. Summary strip shows run date and pipeline counts
3. Job cards render with correct score badge colors (green 90+, default 80-89, muted 70-79)
4. Click a job → full detail with 5-factor score breakdown table
5. "Request Brief" → action written to Upstash, job moves to Brief Requested stage, persists on refresh
6. Sidebar counts update correctly when filtering by stage
7. "View Brief" → rendered markdown brief in design system styling
8. "Run Now" → triggers GitHub Actions workflow (visible in GitHub Actions tab)
9. Poll status shows progress in dashboard (Triggered → Running → Complete)
10. On completion, Vercel redeploys with new data — new jobs visible on refresh
11. Empty states are helpful, not broken
12. No blue anywhere — all interactive elements use warm stone/ink palette
13. Focus rings visible for keyboard navigation
14. Responsive: sidebar collapses to horizontal tabs below 768px

# Design: Job Search Agent V18

## Context

V17 build completed all 46 steps across 9 phases with 0 regressions, but the interactive session exposed 11 failures (3 critical, 4 major, 4 minor). All failures are implementation-level — no architectural changes needed. The V17 analysis identified 8 specific fixes. Separately, a dashboard visual polish design was drafted (jsa-v18-dashboard-design.md) covering 10 CSS/JS/HTML enhancements to the Vercel dashboard.

V18 combines both workstreams: fix the 8 implementation issues from V17 analysis + apply the dashboard visual polish.

**From V17 research handoff:**
- Files to modify: CLAUDE.md, scripts/manage_state.py, api/_upstash.py, .github/workflows/, public/ (CSS/JS/HTML)
- Patterns to preserve: named agent pattern (6 subagents), design system governance, state architecture (Git + Upstash), CLI-only state mutations, auto-retry protocol, checkpoint strategy
- Hard constraints: Vercel handlers must be Vercel-compatible; GH Actions at repo root; settings.local.json gitignored — CI must create it; external deps need local fallbacks; post-render regex CSS-only; agent reads memory on startup; no inline Python for state

## Options Considered

### Option 1: Three-Phase Sequential (Infrastructure → Backend → Frontend)

Phase 1 handles infrastructure (GH Actions, pre-flight validation, CLAUDE.md constraints). Phase 2 handles backend/state logic (manage_state.py dedup subcommand, color regex fix, Redis fallback hardening). Phase 3 handles dashboard visual polish (CSS tokens, component rendering, HTML structure, app logic).

- Pros: Clean separation of concerns; each phase independently testable and deployable; infrastructure fixes land first so CI works before backend/frontend changes; easy to bisect failures
- Cons: Three phases means three test cycles and three commit checkpoints; some CLAUDE.md edits span Phase 1 and Phase 2
- Failure mode: Phase 1 GH Actions changes may need iteration if workflow YAML syntax is wrong — but this is caught by GH Actions validation, not at deploy time
- **Chosen**

### Option 2: Two-Phase (All Fixes → Visual Polish)

All 8 implementation fixes in Phase 1, then dashboard visual polish in Phase 2.

- Pros: Simpler phase structure; fewer test cycles; all "fix" work grouped together
- Cons: Phase 1 mixes infrastructure (GH Actions, pre-flight) with state logic (manage_state.py dedup, regex) and CLAUDE.md constraints — different failure modes entangled; harder to bisect if Phase 1 has issues
- Failure mode: A manage_state.py bug could block testing GH Actions fixes because both are in the same phase
- **Rejected:** Mixes infrastructure and state logic with different failure modes, making debugging harder if Phase 1 issues arise

### Option 3: Single Unified Phase

All 8 fixes + all 10 dashboard changes in one build phase.

- Pros: Fastest to execute; single test cycle; minimal overhead
- Cons: Largest blast radius; 15+ files modified simultaneously; impossible to bisect failures; CSS changes could mask backend state issues; high cognitive load for a single build phase
- Failure mode: A CSS change that breaks card rendering could be confused with a manage_state.py dedup bug if both land together
- **Rejected:** Blast radius too large — 15+ files across infrastructure, backend, and frontend with no isolation between failure domains

## Prototyping Results

Prototyping skipped — no triggers met. All changes use existing technologies (Python CLI, Vercel serverless, vanilla CSS/JS) already proven in V17. No new libraries, no concurrent state across 3+ components, no unverifiable external APIs.

## Chosen Approach

**Three-Phase Sequential (Infrastructure → Backend → Frontend)**

This provides clean separation between three distinct failure domains:
1. Infrastructure issues (YAML syntax, file paths, permissions) are caught by CI runners
2. Backend/state issues (Python logic, JSON manipulation) are caught by unit-testable scripts
3. Frontend issues (CSS rendering, JS component logic) are caught by visual inspection + Playwright

Phases are ordered by dependency: infrastructure must work before backend logic is testable in CI, and backend state must be correct before the dashboard can display it properly.

## Architecture

### Phase 1: Infrastructure Fixes (4 items)

**Components:**
- `CLAUDE.md` — Add HC4 enforcement to startup sequence (agent memory read), add CR5 to UX rules (no technical work suggestions), enforce Step 22 scheduled run prompt
- `.github/workflows/daily-digest.yml` — Add settings.local.json creation step, add post-deploy smoke test step
- `scripts/preflight.sh` (new) — Verify Vercel API health, GH Actions workflow existence at repo root, required secrets presence

**Data flow:**
1. Agent starts → reads CLAUDE.md → startup sequence now includes memory read check + preflight validation
2. Preflight script curls Vercel API, checks `.github/workflows/` directory, verifies env vars
3. GH Actions workflow creates settings.local.json before validation step, runs smoke test after deploy

**Interfaces:**
- preflight.sh is called from CLAUDE.md startup sequence as a bash command
- GH Actions workflow calls preflight.sh as a step

### Phase 2: Backend/State Fixes (3 items)

**Components:**
- `scripts/manage_state.py` — Add `dedup` subcommand for cross-role deduplication
- `CLAUDE.md` — Update Step 13 to reference `manage_state.py dedup` instead of inline Python
- Post-render verification — Fix color regex to match CSS contexts only (either in CLAUDE.md or a new `scripts/verify_html.py`)

**Data flow:**
1. Search-verify subagents write verified JSONs to `output/verified/{role_type}/`
2. `manage_state.py dedup --verified-dir output/verified` reads all verified dirs, detects filename collisions, compares scores, outputs dedup decisions
3. Parent orchestrator calls `manage_state.py dedup` instead of inline Python
4. Post-render verification uses CSS-context-aware regex

**Interfaces:**
- `manage_state.py dedup` CLI: `--verified-dir <path>` → stdout JSON of dedup decisions
- verify_html regex: constrained to `style=` attributes and `<style>` blocks

### Phase 3: Dashboard Visual Polish (10 items)

**Components:**
- `public/css/dashboard.css` — Score-tier tokens, card hover, header/stats bar, section headings, sidebar polish, layout width, empty/loading states, detail view, micro-interactions, dark mode token mapping (commented)
- `public/js/components.js` — Tier class application, stacked stats, count badges, score bars, tag variants, empty state CTA
- `public/index.html` — Summary date element, summary divider, sidebar label
- `public/js/app.js` — Date display logic, section dividers, enhanced empty states, loading spinner

**Data flow:**
1. API returns job data + run metadata → app.js populates date, stats, and job lists
2. components.js applies tier classes based on score thresholds (90+, 80-89, 70-79)
3. CSS renders visual hierarchy via left-edge color bars, stacked KPI stats, count badges
4. Empty states show card container with "Run Search" CTA wired to run controls

**Interfaces:**
- Score tier thresholds: 90+ = green, 80-89 = default, 70-79 = muted
- Layout: 960px max-width (up from 800px), 40px horizontal padding
- All new classes use existing design token naming conventions

**Design signature:** The left-edge score bar — a color accent on each job card that communicates quality at a glance before reading the digit.

## Design Approval Questions

1. **Hardest decision:** Phase granularity — whether to separate infrastructure and backend/state into distinct phases. Chose separation because infrastructure failures (YAML, file paths) and state logic failures (Python, JSON) have completely different debugging workflows. Rejected two-phase approach where both are combined because a manage_state.py bug could block testing GH Actions fixes.

2. **Rejected alternatives:** Two-phase (mixes infrastructure and state logic failure modes, harder to bisect). Single-phase (15+ files, impossible to isolate which domain caused a regression). Both rejected because they sacrifice debuggability for speed — and V17 analysis showed debugging was already a pain point.

3. **Least confident aspect:** The pre-flight validation script (preflight.sh). Checking "Vercel API health" requires knowing the deployment URL, which varies between preview and production. Checking "required secrets are configured" in GH Actions is not easily scriptable from local. This may need to be a partial check (local validations only) with CI-specific checks in the workflow itself. Would change approach if preflight.sh becomes too brittle — in that case, fold checks directly into CLAUDE.md startup as individual bash commands rather than a monolithic script.

## Success Criteria

1. `manage_state.py dedup --verified-dir output/verified` produces correct JSON output for cross-role dedup (no inline Python needed)
2. GH Actions workflow creates settings.local.json and passes validation step
3. Post-deploy smoke test in CI curls `/api/jobs` and gets 200
4. Post-render HTML color check produces 0 false positives on text containing "preferred", "credible", "prepared"
5. CLAUDE.md startup sequence includes explicit agent-memory read step with log output
6. CLAUDE.md UX rules prohibit directing user to do technical work
7. Dashboard cards show tier-specific left border colors (green 4px for 90+, default 3px for 80-89, muted 2px for 70-79)
8. Stats are stacked value/label format (20px number, 11px uppercase label)
9. Content area is 960px wide with 40px horizontal padding
10. All new dashboard elements work below 768px
11. No blue anywhere — warm stone/ink palette only
12. No shadows on cards — borders-only depth
13. Dark mode token mapping present as commented CSS

## Risks

1. **preflight.sh brittleness** — Vercel deployment URL varies between environments; secrets can't be checked locally. Mitigation: Split checks into local-only (file existence, syntax) and CI-only (API health, secrets).
2. **manage_state.py dedup edge cases** — Cross-role dedup assumes filename-based collision detection. If two different jobs at different companies have the same slug, false dedup occurs. Mitigation: Include source URL in collision key, not just filename.
3. **CSS specificity conflicts** — New V18 tokens could conflict with existing V17 styles if selectors overlap. Mitigation: All new classes use unique prefixes (`.tier-*`, `.summary-stat-*`, `.sidebar-label`).
4. **Responsive breakpoint gaps** — Stacked stats and count badges may not work well at 768px breakpoint. Mitigation: Explicit responsive testing as final step.

## Known Risks Passed to /plan

1. **preflight.sh scope** — Plan must decide: monolithic script vs inline bash commands in CLAUDE.md. Need to specify exactly which checks are local-only vs CI-only.
2. **dedup collision key** — Plan must define the exact collision key format (filename only? filename + source domain? job URL hash?).
3. **CSS regression testing** — Plan must include a visual verification step after Phase 3 to catch specificity conflicts.
4. **CLAUDE.md multi-phase edits** — CLAUDE.md is modified in both Phase 1 and Phase 2. Plan must define the edit order to avoid merge conflicts.

## Handoff Contract

- Approach: Three-Phase Sequential (Infrastructure → Backend → Frontend)
- Components:
  - Phase 1: CLAUDE.md (startup/UX rules), .github/workflows/daily-digest.yml, scripts/preflight.sh
  - Phase 2: scripts/manage_state.py (dedup), CLAUDE.md (Step 13), post-render regex fix
  - Phase 3: public/css/dashboard.css, public/js/components.js, public/index.html, public/js/app.js
- Success criteria: 13 measurable items (see Success Criteria section)
- Risks requiring mitigation: preflight.sh brittleness, dedup collision key ambiguity, CSS specificity conflicts, responsive breakpoints
- Known risks for /plan: preflight.sh scope decision, dedup collision key format, CSS regression testing step, CLAUDE.md multi-phase edit ordering

<!-- STAGE COMPLETE: /design, 2026-02-16 -->

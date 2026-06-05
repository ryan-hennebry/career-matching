# JSA V18 — Dashboard Design (Pre-Design Input)

> **Status:** Draft — to be incorporated during V18 `/design` phase
> **Origin:** Interface design exploration session (2026-02-12)

---

## What We're Building

A visual polish pass on the V17 Vercel dashboard. CSS + `components.js` + `index.html` + `app.js` only — no backend changes, no new API endpoints, no new infrastructure. The V17 architecture (Vercel serverless + Upstash Redis + GitHub Actions) is unchanged.

**Scope:** Score-tier visual hierarchy, card enhancements, header restructure, section headings, sidebar polish, layout width increase, empty/loading states, detail view improvements, micro-interactions, and dark mode token mapping (documented, not active).

---

## Design System Evolution

The V17 design system established interactive tokens (buttons, focus rings, inputs), elevation, pipeline status tokens, and spacing. V18 builds on top of that foundation with visual refinements — no new architectural concepts, just craft.

### What stays exactly the same

- Architecture: Vercel serverless + Upstash Redis + GitHub Actions
- Backend: all `api/*.py` serverless functions unchanged
- API surface: all endpoints, request/response shapes unchanged
- Routing: `vercel.json` unchanged
- Data model: verified JSONs, `_delta.json`, briefs, `context.md` unchanged
- Design system foundations: Newsreader + DM Sans, warm stone palette, all existing tokens
- Interactive tokens: buttons, focus rings, inputs, elevation, pipeline status, spacing scale

### What gets added (V18 visual extensions)

**1. Score-tier visual hierarchy (new tokens):**
```css
/* Left-edge color bar — the V18 signature element */
--tier-green-border: 4px;        /* 90+ score: strong accent */
--tier-default-border: 3px;      /* 80-89 score: standard */
--tier-muted-border: 2px;        /* 70-79 score: thinner */

/* Modifier classes applied to .job-card */
.tier-green {
  border-left: var(--tier-green-border) solid var(--score-green);
  background: linear-gradient(90deg, rgba(22,163,74,0.03) 0%, transparent 40%);
}

.tier-default {
  border-left: var(--tier-default-border) solid var(--text-secondary);
}

.tier-muted {
  border-left: var(--tier-muted-border) solid var(--border);
  opacity: 0.85;
}
```
Rationale: Communicates job quality at a glance before reading the score digit. Left-edge color bars provide visual hierarchy without introducing shadows.

**2. Card enhancements:**
```css
/* Hover lift — subtle depth without shadows */
.job-card:hover {
  transform: translateY(-1px);
  border-color: var(--text-tertiary);
  transition: transform var(--transition-fast), border-color var(--transition-fast);
}

/* Action buttons separated from card content */
.job-card-actions {
  border-top: 1px solid var(--border-light);
  padding-top: var(--space-3);
  margin-top: var(--space-3);
}

/* Company one-liner from notes field */
.job-card-note {
  font-size: 13px;
  color: var(--text-tertiary);
  font-style: italic;
  margin-top: var(--space-1);
}

/* Wider header gap */
.job-card-header {
  gap: 16px; /* was 12px */
}
```

**3. Header/stats bar restructure:**
```css
/* Stacked value/label cells — Linear/Vercel KPI pattern */
--summary-height: 72px;          /* was 56px */

.summary-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.summary-stat-value {
  font-family: 'DM Sans', sans-serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.summary-stat-label {
  font-family: 'DM Sans', sans-serif;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-tertiary);
}

/* Run date display */
.summary-date {
  font-size: 13px;
  color: var(--text-secondary);
}

/* Vertical separator between title and stats */
.summary-divider {
  width: 1px;
  height: 32px;
  background: var(--border);
  margin: 0 var(--space-6);
}
```

**4. Section headings:**
```css
/* Newsreader serif headings — matches editorial identity */
.job-list-heading {
  font-family: 'Newsreader', serif;
  font-size: 16px;                /* was DM Sans 12px uppercase */
  font-weight: 500;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-light);
  padding-bottom: var(--space-2);
  margin-bottom: var(--space-4);
}

/* Count badge pill */
.job-list-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: var(--bg-inset);
  font-family: 'DM Sans', sans-serif;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-left: var(--space-2);
}
```

**5. Sidebar polish:**
```css
.sidebar {
  padding: var(--space-5);       /* larger padding */
}

/* Pipeline label above filters */
.sidebar-label {
  font-family: 'DM Sans', sans-serif;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  margin-bottom: var(--space-3);
}

/* Count badges */
.sidebar-count {
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--text-secondary);
}

/* Hover text darkening */
.sidebar-item:hover .sidebar-item-label {
  color: var(--text-primary);
}

/* Zero-count dimming */
.sidebar-item[data-count="0"] {
  opacity: 0.5;
}
```

**6. Layout width:**
```css
--content-max-width: 960px;      /* was 800px */

.main-content {
  max-width: var(--content-max-width);
  padding: 0 40px;              /* was 32px */
}
```
Rationale: 960px fills 1440px monitors comfortably without stretching text lines too wide. The extra horizontal padding gives cards room to breathe.

**7. Empty & loading states:**
```css
/* Card-like container for empty states */
.empty-state {
  background: var(--bg-subtle);
  border: 1px solid var(--border-light);
  border-radius: 4px;
  padding: var(--space-8) var(--space-6);
  text-align: center;
}

.empty-state-message {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}

/* Optional CTA */
.empty-state-cta {
  /* Uses existing --btn-bg / --btn-text tokens */
}

/* CSS spinner — stone palette */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-light);
  border-top-color: var(--text-secondary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: var(--space-8) auto;
}
```

**8. Detail view:**
```css
/* Score breakdown visual bars */
.score-factor-bar {
  width: 60px;
  height: 6px;
  background: var(--bg-inset);
  border-radius: 3px;
  overflow: hidden;
}

.score-factor-fill {
  height: 100%;
  background: var(--text-secondary);
  border-radius: 3px;
}

.score-factor-fill.high {
  background: var(--score-green);
}

/* Tag variants */
.tag-met {
  background: rgba(22,163,74,0.08);
  color: #15803d;
  border: 1px solid rgba(22,163,74,0.15);
}

.tag-gap {
  background: transparent;
  color: var(--text-tertiary);
  border: 1px dashed var(--border);
}

/* Detail header */
.detail-header {
  border-bottom: 1px solid var(--border-light);
  padding-bottom: var(--space-4);
  margin-bottom: var(--space-5);
}
```

**9. Micro-interactions:**
```css
/* Button press */
button:active {
  transform: scale(0.98);
}

/* Score badge lift on card hover */
.job-card:hover .score-badge {
  transform: scale(1.05);
  transition: transform var(--transition-fast);
}

/* Focus-within card highlight */
.job-card:focus-within {
  border-color: var(--text-tertiary);
}

/* Explicit transition targets (no transition: all) */
.job-card {
  transition: transform var(--transition-fast), border-color var(--transition-fast);
}

.score-badge {
  transition: transform var(--transition-fast);
}

button {
  transition: background-color var(--transition-fast), transform var(--transition-fast);
}
```

**10. Dark mode token mapping (documented, not active):**
```css
/* Architecture readiness — NOT enabled */
/* @media (prefers-color-scheme: dark) { */
/*   :root {                                          */
/*     --bg: #1c1917;                                 */
/*     --bg-subtle: #292524;                          */
/*     --bg-inset: #1a1918;                           */
/*     --text-primary: #fafaf9;                       */
/*     --text-secondary: #a8a29e;                     */
/*     --text-tertiary: #78716c;                      */
/*     --border: #44403c;                             */
/*     --border-light: #292524;                       */
/*     --btn-bg: #fafaf9;                             */
/*     --btn-text: #1c1917;                           */
/*     --btn-bg-hover: #e7e5e4;                       */
/*     --btn-secondary-border: #44403c;               */
/*     --btn-secondary-hover-bg: #292524;             */
/*     --input-bg: #292524;                           */
/*     --input-border: #44403c;                       */
/*     --input-border-focus: #fafaf9;                 */
/*     --focus-ring: #a8a29e;                         */
/*     --score-green: #22c55e;                        */
/*     --score-green-bg: rgba(34,197,94,0.1);         */
/*   }                                                */
/* }                                                  */
```
Rationale: Full warm-stone-on-dark inversion mapped out. Not enabled — serves as an architectural checklist for a future iteration. No dark mode toggle in UI.

### Design signature

The **score bar** — a left-edge color accent on each job card that communicates quality at a glance before you read a digit. V17's signature was the summary strip masthead. V18's signature is the score bar.

### What will NOT be done

- No backend changes (all `api/*.py` unchanged)
- No new API endpoints
- No framework introduction (still vanilla JS)
- No shadows on cards (borders-only depth continues)
- No blue anywhere (no `#2563eb`, no blue focus rings)
- No dark mode toggle (mapping documented, not implemented)

---

## File Structure

No structural changes from V17. The same file tree applies. Four files are modified:

| File | Change Type |
|------|-------------|
| `public/css/dashboard.css` | New tokens, new classes, layout width, animations |
| `public/js/components.js` | Tier classes, stacked stats, count badges, score bars, tag variants, empty state CTA |
| `public/index.html` | Summary date element, sidebar "Pipeline" label, summary divider |
| `public/js/app.js` | Date display logic, section dividers, enhanced empty states |

---

## Build Steps (5 steps)

### Step 1: CSS token additions + new classes

Add all new custom properties and utility classes to `dashboard.css`:
- Score-tier tokens (`--tier-green-border`, etc.) and `.tier-green` / `.tier-default` / `.tier-muted` modifier classes
- Card hover styles (translateY, border-color transition)
- Header/stats bar tokens (`--summary-height: 72px`, stacked stat layout)
- Section heading styles (Newsreader 16px, `.job-list-count` badge)
- Sidebar polish (padding, `.sidebar-label`, `.sidebar-count`, hover/zero-count states)
- Layout width (`--content-max-width: 960px`, 40px padding)
- Empty/loading state containers and spinner animation
- Detail view score bars and tag variants
- Micro-interactions (button active, score badge hover, focus-within)
- Dark mode token mapping (commented out)

**Verify:** CSS parses without errors. No visual regressions on existing elements.

### Step 2: components.js rendering changes

Update render functions to use new classes and patterns:
- `renderJobCard()` — apply `.tier-green` / `.tier-default` / `.tier-muted` based on score, add `.job-card-note` for notes, add `.job-card-actions` wrapper
- `renderSummaryStrip()` — stacked `.summary-stat` cells (value + label), run date display, vertical divider
- `renderJobList()` — Newsreader heading with `.job-list-count` badge
- `renderScoreBreakdown()` — visual bars (60px track) per factor, `.tag-met` and `.tag-gap` variants
- `renderEmptyState()` — card container with message and optional "Run Search" CTA button
- Sidebar rendering — `.sidebar-label` "Pipeline" header, `.sidebar-count` badges, `data-count` attributes

**Verify:** Cards show tier-appropriate left borders. Stats are stacked. Count badges appear.

### Step 3: index.html structural additions

- Add `.summary-date` element in header for run date display
- Add `.summary-divider` between title area and stats
- Add `.sidebar-label` element ("Pipeline") above sidebar filter list
- Update `--summary-height` reference if hardcoded in markup

**Verify:** HTML structure supports new layout. No broken references.

### Step 4: app.js logic changes

- Populate run date from API state response into `.summary-date`
- Wire section dividers between job list groups
- Enhanced empty state rendering with "Run Search" CTA that triggers run controls
- Loading spinner display during data fetches

**Verify:** Date displays correctly. Empty states show CTA. Loading spinner appears during fetches.

### Step 5: Responsive breakpoint updates + verification

- Ensure all new elements (stacked stats, count badges, score bars, sidebar label) work below 768px
- Summary stats may need horizontal scroll or wrap at narrow widths
- Score factor bars in detail view should be full-width on mobile
- Test sidebar "Pipeline" label and count badges in collapsed horizontal tab bar

**Verify:** Full verification checklist (see Section 7) passes at both desktop and mobile widths.

---

## Key Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Score hierarchy | Left-edge color bar | Visual without adding shadows |
| Content width | 960px | Fills 1440px monitors, doesn't stretch text |
| Stats layout | Stacked value/label | Linear/Vercel KPI pattern |
| Section headings | Newsreader serif | Matches editorial identity |
| Empty states | Card container + CTA | Maintains page structure |
| Dark mode | Token mapping only | Architecture readiness without scope creep |
| Hover depth | translateY(-1px) | Subtle lift without shadows |
| Transition targets | Explicit properties | No `transition: all` — predictable, performant |
| Tag variants | Green tint vs dashed border | Met/gap distinction without color overload |
| Score bars | 60px inline tracks | Compact visual in detail table rows |

---

## Critical Files

| File | Role |
|------|------|
| `public/css/dashboard.css` | All new tokens, classes, animations, dark mode mapping |
| `public/js/components.js` | Tier rendering, stacked stats, count badges, score bars, tag variants, empty states |
| `public/index.html` | Summary date, sidebar label, summary divider structural elements |
| `public/js/app.js` | Date display, section dividers, enhanced empty states, loading spinner |

---

## Verification

After all steps (using Vercel preview/production URL):

1. Cards show tier-specific left border colors (green 4px for 90+, default 3px for 80-89, muted 2px for 70-79)
2. Stats are stacked value/label format (20px number, 11px uppercase label)
3. Section headings use Newsreader 16px with count badges
4. Empty state has card container with "Run Search" button
5. Content area is 960px wide with 40px horizontal padding
6. Sidebar has "Pipeline" label and larger count badges (13px bold, tabular-nums)
7. Card hover shows translateY(-1px) lift with border-color transition
8. Score breakdown has visual bars (60px track) in detail view
9. Requirements met are green-tinted (`.tag-met`), gaps are dashed (`.tag-gap`)
10. Loading state shows stone-palette spinner
11. Run date visible in header stats bar
12. No blue anywhere — all interactive elements use warm stone/ink palette
13. No shadows on cards — borders-only depth
14. Responsive: all new elements work below 768px (stacked stats, count badges, score bars, sidebar label)

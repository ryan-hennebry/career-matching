---
name: jsa-design-system
description: Unified design system for all JSA visual outputs (email HTML, briefs HTML)
---

## Design System — Job Search Agent

All visual subagents (digest-email, briefs-html) MUST follow these specifications exactly. No alternative fonts, colors, or rendering methods. Every visual output must feel like it came from the same editorial system.

---

### Font Imports

**Google Fonts URL (both email and briefs HTML):**
```
https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&family=DM+Sans:wght@400;500;600;700&display=swap
```

**HTML import (place in `<head>`):**
```html
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Fallback stack:**
- Heading fallback: `'Newsreader', 'Georgia', 'Times New Roman', serif`
- Body fallback: `'DM Sans', 'Helvetica Neue', 'Arial', sans-serif`

---

### Typography Scale

| Element | Font | Size | Weight | Line-height | Letter-spacing |
|---------|------|------|--------|-------------|----------------|
| H1 (page title) | Newsreader | 28px | 600 | 1.25 | -0.01em |
| H2 (section header) | Newsreader | 22px | 600 | 1.3 | 0 |
| H3 (card title) | Newsreader | 18px | 500 | 1.35 | 0 |
| Body | DM Sans | 15px | 400 | 1.6 | 0.01em |
| Body emphasis | DM Sans | 15px | 500 | 1.6 | 0.01em |
| Small / meta | DM Sans | 13px | 400 | 1.5 | 0.02em |
| Table cell | DM Sans | 14px | 400 | 1.5 | 0.01em |
| Table header | DM Sans | 12px | 600 | 1.5 | 0.06em |
| Score badge | DM Sans | 14px | 700 | 1 | 0 |

**Table headers:** Always uppercase, tracked out (`letter-spacing: 0.06em`). Uses `text-transform: uppercase`.

**Italic usage:** Newsreader italic for pull-quotes, notes, or editorial asides only. Never italic on body text.

---

### Color Palette

**Core:**
| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#ffffff` | Page/email background |
| `--bg-subtle` | `#f8f8f6` | Card backgrounds, section fills (warm off-white) |
| `--bg-inset` | `#f0efeb` | Table header rows, inset panels |
| `--text-primary` | `#1c1917` | Headings, primary body text (warm black) |
| `--text-secondary` | `#57534e` | Secondary text, descriptions |
| `--text-tertiary` | `#a8a29e` | Metadata, timestamps, light labels |
| `--border` | `#e7e5e4` | Table borders, card borders, dividers |
| `--border-strong` | `#d6d3d1` | Section dividers, prominent separators |
| `--accent` | `#1c1917` | Links (dark, editorial — same as text-primary) |
| `--accent-underline` | `#d6d3d1` | Link underline color (stone gray, subtle) |

**Score Accents:**
| Range | Hex | Background | Usage |
|-------|-----|------------|-------|
| 90+ (strong) | `#15803d` | `#f0fdf4` | Score badge green |
| 80-89 (good) | `#1c1917` | `#f8f8f6` | Default, no accent color |
| 70-79 (marginal) | `#78716c` | `#f8f8f6` | Score badge muted stone |

**Score badge pattern:**
```css
.score-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 3px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 700;
  /* color and background-color set per range */
}
```

---

### Layout Specifications

**Briefs HTML (800px):**
- Container max-width: `800px`
- Container padding: `48px 56px`
- Section spacing: `36px` between major sections
- Card spacing: `24px` between cards

**Email (600px):**
- Container max-width: `600px`
- Container padding: `32px 24px`
- Section spacing: `28px` between major sections
- Card spacing: `20px` between cards

**Common:**
- Single column layout
- Generous whitespace — never crowd elements
- Content aligned left (no center-aligned body text)
- Headings aligned left

---

### Component Patterns

**Section Divider (between major sections):**
```css
.section-divider {
  border: none;
  border-top: 2px solid #d6d3d1; /* --border-strong */
  margin: 36px 0;
}
```

**Job Card (Briefs HTML):**
```css
.job-card {
  background: #f8f8f6; /* --bg-subtle */
  border: 1px solid #e7e5e4; /* --border */
  border-radius: 4px;
  padding: 24px 28px;
  margin-bottom: 24px;
}
.job-card h3 {
  font-family: 'Newsreader', Georgia, serif;
  font-size: 18px;
  font-weight: 500;
  color: #1c1917;
  margin: 0 0 8px 0;
}
.job-card .meta {
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  color: #57534e;
  margin-bottom: 16px;
}
```

**Job Card (Email — table-based):**
```html
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f8f6;border:1px solid #e7e5e4;border-radius:4px;margin-bottom:20px;">
  <tr>
    <td style="padding:24px 24px;">
      <!-- Card content with inline styles -->
    </td>
  </tr>
</table>
```

**Data Table:**
```css
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
}
.data-table th {
  background: #f0efeb; /* --bg-inset */
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #57534e;
  padding: 10px 14px;
  text-align: left;
  border-bottom: 2px solid #d6d3d1;
}
.data-table td {
  padding: 12px 14px;
  border-bottom: 1px solid #e7e5e4;
  color: #1c1917;
  vertical-align: top;
}
.data-table tr:last-child td {
  border-bottom: none;
}
```

---

### Link Styling

Links use dark text-primary color with a subtle stone-gray underline. This creates an editorial feel (not a web app). `font-weight:500` provides a secondary differentiation signal for clients that strip underline styling.

**Briefs HTML links:**
```css
a {
  color: #1c1917; /* --text-primary */
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
  text-decoration-color: #d6d3d1; /* --border-strong, subtle stone gray */
  font-weight: 500;
  transition: text-decoration-color 0.15s;
}
a:hover {
  text-decoration-color: #1c1917;
}
```

**Email links (inline):**
```html
<a href="..." style="color:#1c1917;text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px;text-decoration-color:#d6d3d1;font-weight:500;">...</a>
```

**Gmail link color override (MUST include in email `<style>` block):**
```html
<style>
  u + #body a { color: inherit !important; text-decoration: inherit !important; font-weight: inherit !important; }
  #MessageViewBody a { color: inherit !important; text-decoration: inherit !important; }
</style>
```
Add `id="body"` to the `<body>` tag. This prevents Gmail from overriding link colors with its default blue.

---

### Email CSS Block (Complete)

All email HTML must use inline styles. This block is the reference for all email styling:

```css
/* REFERENCE ONLY — convert to inline styles for email HTML */
/* Container */
body { margin: 0; padding: 0; background: #ffffff; }
.email-container { max-width: 600px; margin: 0 auto; padding: 32px 24px; font-family: 'DM Sans', 'Helvetica Neue', Arial, sans-serif; font-size: 15px; line-height: 1.6; color: #1c1917; }

/* Header */
.email-header h1 { font-family: 'Newsreader', Georgia, serif; font-size: 28px; font-weight: 600; line-height: 1.25; letter-spacing: -0.01em; color: #1c1917; margin: 0 0 8px 0; }
.email-header .subtitle { font-family: 'DM Sans', sans-serif; font-size: 13px; color: #a8a29e; letter-spacing: 0.02em; margin: 0; }

/* Summary strip */
.summary-strip { background: #f0efeb; padding: 16px 20px; border-radius: 4px; margin: 24px 0; }
.summary-strip .stat { font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 600; color: #57534e; text-transform: uppercase; letter-spacing: 0.06em; }

/* Section headers */
.section-header { font-family: 'Newsreader', Georgia, serif; font-size: 22px; font-weight: 600; line-height: 1.3; color: #1c1917; margin: 28px 0 16px 0; padding-bottom: 8px; border-bottom: 2px solid #d6d3d1; }

/* Job cards in email */
.email-card { background: #f8f8f6; border: 1px solid #e7e5e4; border-radius: 4px; padding: 24px; margin-bottom: 20px; }
.email-card-title { font-family: 'Newsreader', Georgia, serif; font-size: 18px; font-weight: 500; color: #1c1917; margin: 0 0 6px 0; }
.email-card-meta { font-family: 'DM Sans', sans-serif; font-size: 13px; color: #57534e; }
.email-card-body { font-family: 'DM Sans', sans-serif; font-size: 14px; color: #1c1917; line-height: 1.5; }

/* Footer */
.email-footer { margin-top: 28px; padding-top: 20px; border-top: 1px solid #e7e5e4; font-size: 13px; color: #a8a29e; }
```

**Email structure (table layout):**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600;6..72,700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:#ffffff;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;padding:32px 24px;font-family:'DM Sans','Helvetica Neue',Arial,sans-serif;font-size:15px;line-height:1.6;color:#1c1917;">
          <!-- Content rows here -->
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

**Mobile responsive (email):**
```html
<style>
  @media only screen and (max-width: 620px) {
    .email-container { padding: 20px 16px !important; }
    .email-card { padding: 16px !important; }
    .email-header h1 { font-size: 24px !important; }
    .section-header { font-size: 20px !important; }
    /* Stack columns if using multi-column layout */
    .responsive-col { display: block !important; width: 100% !important; }
  }
</style>
```

---

### Briefs HTML CSS Block (Complete)

```css
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&family=DM+Sans:wght@400;500;600;700&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'DM Sans', 'Helvetica Neue', Arial, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: #1c1917;
  background: #ffffff;
  -webkit-font-smoothing: antialiased;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 48px 56px;
}

/* Typography */
h1 {
  font-family: 'Newsreader', Georgia, serif;
  font-size: 28px;
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: -0.01em;
  color: #1c1917;
  margin-bottom: 8px;
}

h2 {
  font-family: 'Newsreader', Georgia, serif;
  font-size: 22px;
  font-weight: 600;
  line-height: 1.3;
  color: #1c1917;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #d6d3d1;
}

h3 {
  font-family: 'Newsreader', Georgia, serif;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.35;
  color: #1c1917;
  margin-bottom: 8px;
}

p { margin-bottom: 12px; }
strong { font-weight: 600; }
em { font-family: 'Newsreader', Georgia, serif; font-style: italic; }

/* Links — dark editorial style, not blue */
a {
  color: #1c1917;
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
  text-decoration-color: #d6d3d1;
  font-weight: 500;
}
a:hover {
  text-decoration-color: #1c1917;
}

/* Section spacing */
.section { margin-bottom: 36px; }
.section-divider {
  border: none;
  border-top: 2px solid #d6d3d1;
  margin: 36px 0;
}

/* Cards */
.job-card {
  background: #f8f8f6;
  border: 1px solid #e7e5e4;
  border-radius: 4px;
  padding: 24px 28px;
  margin-bottom: 24px;
}

/* Score badges */
.score-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 3px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 700;
}
.score-green { color: #15803d; background: #f0fdf4; }
.score-default { color: #1c1917; background: #f8f8f6; }
.score-muted { color: #78716c; background: #f8f8f6; }

/* Tables */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  margin-bottom: 16px;
}
th {
  background: #f0efeb;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #57534e;
  padding: 10px 14px;
  text-align: left;
  border-bottom: 2px solid #d6d3d1;
}
td {
  padding: 12px 14px;
  border-bottom: 1px solid #e7e5e4;
  vertical-align: top;
}
tr:last-child td { border-bottom: none; }

/* Metadata */
.meta {
  font-size: 13px;
  color: #57534e;
  letter-spacing: 0.02em;
}
.meta-light {
  font-size: 13px;
  color: #a8a29e;
}

/* Tags / chips */
.tag {
  display: inline-block;
  background: #f0efeb;
  color: #57534e;
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 3px;
  margin-right: 6px;
  margin-bottom: 4px;
}

/* Brief separator — bold border between briefs (HTML viewed in browser) */
.brief-page {
  border-top: 4px solid #1c1917;
  margin-top: 48px;
  padding-top: 40px;
}
.brief-page:first-child {
  border-top: none;
  margin-top: 0;
  padding-top: 0;
}
```

---

### Rendering Rules

**Briefs: HTML only.** No PDF rendering. The briefs HTML file is opened directly in the user's browser. No Playwright PDF conversion — Chromium's PDF pagination causes dead whitespace issues that cannot be resolved with CSS break rules.

**Warning/caveat display in HTML and emails:**
- Never use colored text (red, amber/orange) for warnings, salary caveats, or skill gaps. Colored text is visually jarring and breaks the editorial aesthetic.
- Instead use **bold text** (`font-weight:600`) for emphasis, or structurally separate warnings into their own line/element.
- Salary caveats: render as a separate line in `--text-secondary` color with bold label: `<strong>Note:</strong> Salary £36-60K — lower end below your £40K minimum`
- Skill gaps: render as a separate line in `--text-secondary` color with bold label: `<strong>Gaps:</strong> Partnership negotiation, financial modeling`

---

### Aesthetic

Internal strategy document — clean, professional, editorial. The Newsreader serif headings provide editorial gravity. DM Sans body text provides modern clarity. Warm neutral palette (stone tones instead of cool greys) creates a distinguished, approachable feel.

**NOT:** a marketing site, dashboard, SaaS newsletter, or startup landing page.

---

### Dashboard Extensions

The following tokens extend the design system for interactive dashboard use. These are additive — all existing tokens remain unchanged.

**Interactive Tokens:**
```css
/* Buttons — ink on stone, not blue on white */
--btn-bg: #1c1917;
--btn-text: #ffffff;
--btn-bg-hover: #292524;
--btn-secondary-bg: transparent;
--btn-secondary-border: #d6d3d1;
--btn-secondary-hover-bg: #f8f8f6;
--btn-ghost-hover-bg: #f0efeb;

/* Focus ring — visible but not jarring */
--focus-ring: #78716c;
--focus-ring-offset: 2px;

/* Inputs */
--input-bg: #f8f8f6;
--input-border: #d6d3d1;
--input-border-focus: #1c1917;
```

**Elevation System:**
```css
--shadow-sm: none;
--shadow-dropdown: 0 4px 12px rgba(28,25,23,0.08);
--overlay-bg: rgba(28,25,23,0.3);
```

**Active/Selected States:**
```css
--sidebar-active-border: #1c1917;
--sidebar-active-bg: #f8f8f6;
--sidebar-hover-bg: #f0efeb;
--card-selected-border: #1c1917;
```

**Pipeline Status Tokens:**
```css
--status-new: #1c1917;
--status-new-bg: #f0efeb;
--status-reviewing: #57534e;
--status-brief: #15803d;
--status-brief-bg: #f0fdf4;
--status-applied: #15803d;
--status-applied-bg: #f0fdf4;
--status-rejected: #a8a29e;
--status-expired: #a8a29e;
```

**Spacing Scale:**
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

**Transitions:**
```css
--transition-fast: 120ms ease;
--transition-base: 200ms ease;
```

**Button Patterns:**
```css
.btn {
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: var(--transition-fast);
  border: none;
}
.btn:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: var(--focus-ring-offset);
}
.btn-primary {
  background: var(--btn-bg);
  color: var(--btn-text);
}
.btn-primary:hover { background: var(--btn-bg-hover); }
.btn-secondary {
  background: var(--btn-secondary-bg);
  color: var(--text-primary);
  border: 1px solid var(--btn-secondary-border);
}
.btn-secondary:hover { background: var(--btn-secondary-hover-bg); }
.btn-ghost {
  background: transparent;
  color: var(--text-primary);
  border: none;
}
.btn-ghost:hover { background: var(--btn-ghost-hover-bg); }
```

**Sidebar Item Pattern:**
```css
.sidebar-item {
  padding: 8px 16px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: var(--text-secondary);
  border-left: 3px solid transparent;
  cursor: pointer;
  transition: var(--transition-fast);
}
.sidebar-item:hover { background: var(--sidebar-hover-bg); }
.sidebar-item.active {
  color: var(--text-primary);
  font-weight: 600;
  background: var(--sidebar-active-bg);
  border-left-color: var(--sidebar-active-border);
}
```

**Status Badge Pattern:**
```css
.status-badge {
  display: inline-block;
  font-family: 'DM Sans', sans-serif;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
```

**Hard Rule:** No blue anywhere. All interactive elements use warm stone/ink palette. Focus rings use `#78716c` (stone), not browser default blue.

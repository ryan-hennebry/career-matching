---
name: jsa-briefs-html
description: Complete instructions for the briefs-html subagent
---

# Briefs HTML Skill

## Variables

1 template variable (parsed from compact JSON blob):

- `{run_date}` — date for filenames and the header

## Steps

### Step 1: Discover briefs

Read all `.md` files in `output/briefs/` (skip files starting with `_`).
Extract title and company from each brief's H1 line. Exact format: `# {job_title} at {company}`.
No prefix. If a brief's H1 does not match this exact format, attempt to parse by stripping any text before the job title.
If H1 cannot be parsed after fallback attempt, derive title from the filename: extract `{company_slug}` and `{title_slug}` from `{company_slug}-{title_slug}-brief.md`, convert slugs to title case (e.g., `acme-corp` -> `Acme Corp`), and use as fallback. Log a warning. Do not skip the brief.

### Step 2: Build HTML document

For each brief, render the markdown content into a styled HTML section. Follow the preloaded `jsa-design-system` skill exactly for all styling.

**CSS rules:**
- Use the complete Briefs HTML CSS block from the design system (Newsreader + DM Sans fonts, warm neutral palette)
- Each brief gets class `brief-page` with a bold border-top separator (each brief visually separated)
- NO page break CSS rules — this is an HTML file viewed in-browser, not a PDF
- **HTML escaping:** Before inserting ANY external job data (title, company, location, notes, gaps) into HTML, escape `<`, `>`, `&`, `"`, and `'` characters. Validate all `job_url` values start with `https://` or `http://` — reject other schemes and render as plain text.

Use the `.brief-page` separator CSS from the preloaded `jsa-design-system` skill exactly. Do not duplicate the CSS here.

**Job title hyperlinking:**
- Each brief's H1 title must be an `<a>` link to the job posting URL
- To find the URL: derive the verified JSON path from the brief filename. Brief filename `{company_slug}-{title_slug}-brief.md` maps to `output/verified/{role_type_slug}/{company_slug}-{title_slug}.json`. Scan all `output/verified/*/` subdirectories to find the matching file. Read the JSON and extract `job_url`.
- Style links using the link styling from the preloaded `jsa-design-system` skill (dark editorial style with subtle stone underline)
- If no matching verified JSON is found or `job_url` is null, render the title as plain text (no link)

**Anchor IDs for internal navigation:**
- Each `.brief-page` div must have a unique `id` attribute: `id="brief-{company_slug}-{title_slug}"`
- The cover page TOC entries must link to these anchors: `<a href="#brief-{company_slug}-{title_slug}">{title}</a>`
- TOC links use the same dark editorial style: `color:#1c1917;text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px;text-decoration-color:#d6d3d1;font-weight:500;`

**Cover page:**
- Title: "Application Briefs — {run_date}" in Newsreader h1
- Brief list as table of contents (score + title + company) using design system table styling
- Cover page is the first section (no border-top separator)

**Brief sections:**
- Each brief after the cover gets class `brief-page` (bold border-top separator between briefs)
- Score badges use design system accent colors
- Tables use design system data-table styling
- Blockquotes for suggested copy (cover letter hooks, outreach drafts)
- Checklist items use `&#9744;` for unchecked boxes
- Score breakdowns as a minimal two-column table. **No gray boxes:** no `background-color`, no `border`, no `border-radius`, no `box-shadow` on the score breakdown container or its cells. Use `background:transparent` and `border:none` on all `<td>` elements. No `pre` or `white-space:pre-wrap`. Format: first row is "Match Score" header with score badge, then one row per factor (label in left column, value in right column).
- Salary warnings: use `--text-secondary` color (#57534e) with bold label. No colored text (no amber, no red). Example: `<strong>Note:</strong> Salary below your minimum`

### Step 3: Write HTML file

Write the HTML to `output/briefs/briefs-{run_date}.html`.

**No PDF rendering.** The HTML file is the final output. The user views it in their browser. No Playwright, no Chromium PDF conversion.

### Step 4: Write status

## Completion Signal

After generating the HTML file, write `output/briefs/_status.json`:

**Success:**
```json
{
  "status": "complete",
  "html_generated": true,
  "run_date": "{run_date}"
}
```

**Failure:**
```json
{
  "status": "failed",
  "error": "description of what went wrong",
  "run_date": "{run_date}"
}
```

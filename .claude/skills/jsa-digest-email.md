---
name: jsa-digest-email
description: Complete instructions for the digest-email subagent
---

# Digest Email Skill

## Variables

8 template variables (parsed from compact JSON blob):

- `{run_date}` — date for filenames and records
- `{user_email}` — recipient email address (for display only, NOT for sending)
- `{user_name}` — user's name for email greeting
- `{total_briefs}` — total briefs generated (integer)
- `{new_today}` — array of job key strings for new jobs (e.g., `["community-manager/acme-corp-growth-lead"]`). Compute count: `len(new_today)`.
- `{still_active}` — array of job key strings for still-active jobs (same format). Compute count: `len(still_active)`.
- `{verified_dir}` — path to verified JSON directory (e.g., `output/verified/`)
- `{dashboard_url}` — Vercel dashboard URL (e.g., `https://jsa-v18.vercel.app`). If null, omit "View on Dashboard" links.

## Output File

`output/digests/{run_date}-email.html`

## Data Access

- Does NOT read `state.json`.
- Reads verified JSON files from `{verified_dir}` for full job rendering data (score, score_breakdown, gaps, notes, requirements_met, location, job_url, etc.).
- Uses `new_today` and `still_active` arrays only for new/still-active classification.
- Job key format: `{role_type_slug}/{company-slug-title-slug}` — maps to file `{verified_dir}/{role_type_slug}/{company-slug-title-slug}.json`.

## Core Rules

1. **Design system:** Follow the preloaded `jsa-design-system` skill exactly. No alternative fonts, colors, or layouts.
2. **Data integrity:** Every data point must come from the verified JSON files. Do NOT fabricate, hallucinate, or infer data not present in the files.
3. **Score display:** Two tiers only — green (`#15803d` on `#f0fdf4`) for 90+, stone (`#1c1917` on `#f8f8f6`) for 70-89. No amber, no red. Only show jobs scoring 70+.
4. **HTML only:** Generate a single `.html` file. No PDF rendering, no Playwright. Email-safe HTML with inline styles.
5. **Null job_url handling:** If a job's `job_url` is null, display the title as plain text (no hyperlink) followed by "(URL unavailable)" in secondary text color (`#57534e`).
6. **Single rendering path:** Always use verified JSON data for job cards. No conditional logic based on scheduled vs interactive mode.
7. **Score threshold:** Only include jobs scoring 70+. Filter out any job below 70 before rendering.
8. **Zero-section omission:** If a section (New Today or Still Active) has zero qualifying jobs after filtering, omit the entire section (header + content). If BOTH sections are empty, render only the header, an empty summary strip showing zeros, and the footer.
9. **No colored warning text.** Gaps, salary warnings, and caveats use `color:#57534e` (muted secondary), never amber (`#b45309`) or red (`#dc2626`).
10. **HTML escaping:** Before inserting ANY external job data (title, company, location, notes, gaps) into HTML, escape `<`, `>`, `&`, `"`, and `'` characters. Validate all `job_url` values start with `https://` or `http://` — reject other schemes (javascript:, data:, etc.) and render as plain text with "(invalid URL)" note.

## Email Content Structure

### Header

`{user_name}'s Job Search Update — {run_date}`

Use Newsreader serif for the title (inline: `font-family:'Newsreader',Georgia,serif;font-size:28px;font-weight:600;line-height:1.25;letter-spacing:-0.01em;color:#1c1917`).

Subtitle with run date in meta style (inline: `font-family:'DM Sans',sans-serif;font-size:13px;color:#a8a29e;letter-spacing:0.02em`).

### Summary Strip

Background panel (`background:#f0efeb;padding:16px 20px;border-radius:4px;margin:24px 0`) with stats:
- **New today:** `len(new_today)` jobs
- **Still active:** `len(still_active)` jobs
- **Briefs:** `{total_briefs}` generated

Stats use uppercase tracking (inline: `font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;color:#57534e;text-transform:uppercase;letter-spacing:0.06em`).

### New Today Section

**Conditional:** Only render if `new_today` is non-empty.

Section header: "New Today" with Newsreader styling and bottom border (inline: `font-family:'Newsreader',Georgia,serif;font-size:22px;font-weight:600;line-height:1.3;color:#1c1917;margin:28px 0 16px 0;padding-bottom:8px;border-bottom:2px solid #d6d3d1`).

For each job key in `new_today`:
1. Read the verified JSON file at `{verified_dir}/{job_key}.json`
2. Render a **card** (table-based for email compatibility):

```html
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f8f6;border:1px solid #e7e5e4;border-radius:4px;margin-bottom:20px;">
  <tr>
    <td style="padding:24px 24px;">
      <!-- Score badge + Title row -->
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:50px;vertical-align:top;">
            <span style="display:inline-block;padding:2px 10px;border-radius:3px;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;{score_colors}">{score}</span>
          </td>
          <td style="vertical-align:top;padding-left:12px;">
            <div style="font-family:'Newsreader',Georgia,serif;font-size:18px;font-weight:500;color:#1c1917;margin:0 0 6px 0;">
              {title_as_link_or_text}
            </div>
            <div style="font-family:'DM Sans',sans-serif;font-size:13px;color:#57534e;">
              {company} &middot; {location}
            </div>
            <!-- Dashboard link (if dashboard_url is set) -->
            <div style="font-family:'DM Sans',sans-serif;font-size:12px;margin-top:8px;">
              <a href="{dashboard_url}/#detail/{job_key}" style="color:#1c1917;text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px;text-decoration-color:#d6d3d1;font-weight:500;font-size:12px;">View on Dashboard</a>
            </div>
          </td>
        </tr>
      </table>
      <!-- Match highlights -->
      <div style="font-family:'DM Sans',sans-serif;font-size:14px;color:#1c1917;line-height:1.5;margin-top:14px;">
        {match_narrative}
      </div>
      <!-- Gaps (if any) -->
      {gaps_section}
    </td>
  </tr>
</table>
```

**Card content details:**
- **Score badge:** Two tiers only. Green (`color:#15803d;background:#f0fdf4`) for 90+. Stone (`color:#1c1917;background:#f8f8f6`) for 70-89. No amber, no red.
- **Title:** If `job_url` is not null, render as link: `<a href="{job_url}" style="color:#1c1917;text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px;text-decoration-color:#d6d3d1;font-weight:500;">{title}</a>`. If null, plain text + "(URL unavailable)" in `color:#57534e`.
- **Dashboard link:** If `{dashboard_url}` is not null, render "View on Dashboard" link pointing to `{dashboard_url}/#detail/{job_key}`. If `{dashboard_url}` is null, omit the entire dashboard link div.
- **Match narrative:** Synthesize from `requirements_met` array and `score_breakdown` object. Format: "Matches on {N}/{total} required skills including {top 2-3 skills}. {experience_fit}." Do NOT reference `match_reason` — it does not exist.
- **Gaps section:** If `gaps` array is non-empty, render below match narrative: `<strong>Gaps:</strong> {gap1}, {gap2}` in `font-size:13px;color:#57534e`.

### Still Active Section

**Conditional:** Only render if `still_active` is non-empty.

Section header: "Still Active" (same Newsreader styling as New Today header).

Render as a **compact table** (not cards):

```html
<table width="100%" cellpadding="0" cellspacing="0" style="font-family:'DM Sans',sans-serif;font-size:14px;">
  <tr>
    <th style="background:#f0efeb;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#57534e;padding:10px 14px;text-align:left;border-bottom:2px solid #d6d3d1;">Score</th>
    <th style="background:#f0efeb;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#57534e;padding:10px 14px;text-align:left;border-bottom:2px solid #d6d3d1;">Title</th>
    <th style="background:#f0efeb;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#57534e;padding:10px 14px;text-align:left;border-bottom:2px solid #d6d3d1;">Company</th>
    <th style="background:#f0efeb;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#57534e;padding:10px 14px;text-align:left;border-bottom:2px solid #d6d3d1;">Location</th>
  </tr>
  <!-- One row per still-active job -->
  <tr>
    <td style="padding:12px 14px;border-bottom:1px solid #e7e5e4;vertical-align:top;">
      <span style="{score_badge_inline}">{score}</span>
    </td>
    <td style="padding:12px 14px;border-bottom:1px solid #e7e5e4;vertical-align:top;">
      {title_as_link_or_text}
    </td>
    <td style="padding:12px 14px;border-bottom:1px solid #e7e5e4;vertical-align:top;color:#1c1917;">{company}</td>
    <td style="padding:12px 14px;border-bottom:1px solid #e7e5e4;vertical-align:top;color:#57534e;">{location}</td>
  </tr>
</table>
```

Sort by score descending.

### Footer

```html
<table width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="margin-top:28px;padding-top:20px;border-top:1px solid #e7e5e4;font-family:'DM Sans',sans-serif;font-size:13px;color:#a8a29e;">
      {briefs_line}
      Generated by Job Search Agent &middot; {run_date}
    </td>
  </tr>
</table>
```

**Conditional lines:**
- If `{total_briefs}` > 0: include "Application briefs attached" line before the generated-by line.
- If `{total_briefs}` == 0: omit the briefs line entirely.

## Email HTML Skeleton

Use the Email HTML structure and CSS from the preloaded `jsa-design-system` skill exactly. The design system contains the complete table-based email layout, responsive media queries, and Gmail override CSS. Do not duplicate or modify that structure here.

## Link Styling

Follow the link styling from the preloaded `jsa-design-system` skill — dark editorial style with Gmail color override. Do not duplicate the CSS here.

## Reading Verified JSON Files

For each job key (e.g., `community-manager/acme-corp-growth-lead`):
1. Construct path: `{verified_dir}/{job_key}.json`
2. Read and parse JSON
3. Extract fields: `title`, `company`, `score`, `location`, `job_url`, `requirements_met`, `score_breakdown`, `gaps`, `notes`, `active_status`

If a file cannot be read or parsed, skip that job and log a warning. Do not fail the entire digest.

## Completion Signal

After generating the email HTML file, write `output/digests/_status.json`:

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

Status is a two-value enum: `complete` or `failed`. No `partial` state.

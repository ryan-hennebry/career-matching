# Presentation Rules

How job results are formatted, displayed, and presented to the user. These rules enforce uniform table format across all role types — a multi-version regression (V14, V16, V18, V19, V20).

---

## Score Threshold

**Minimum score: 70 (inclusive).** Only present jobs scoring >= 70. A score of exactly 70 IS shown. Below 70 = not shown, logged in session-state.md. Threshold comparison: `score >= 70`, not `score > 70`. (V16 regression — previously used `> 70`, excluding 70-score jobs.)

**Empty results fallback:** If a role type has zero jobs above 70, present top 3 regardless of score with a note: "No strong matches found. Here are the closest."

---

## Pre-Presentation Requirements

Before presenting ANY role type's results:

1. All jobs for that role type are verified
2. Cross-role-type deduplication completed (Step 13)
3. Jobs ranked by score, highest first

---

## Uniform Table Format (I6 Standardization)

**ALL role types MUST use the identical table format below.** No role type may use bullet lists, numbered lists, or prose paragraphs instead of tables. This is a multi-version regression (V19/V20): no mixed table/line formats. Every role type renders in the same columns and style.

### Two Subsections Per Role Type

Every role type with results MUST show two subsections:

- **New Today** -- jobs appearing for the first time in this run (from delta `new_jobs` list)
- **Still Active** -- jobs seen in previous runs that are still active (from delta `still_active` list)

If a role type has both new and still-active jobs, show both subsections. If only one category has results, show only that subsection.

### Column Definitions

Tables use exactly four columns in this order:

| Column   | Content                                           |
|----------|---------------------------------------------------|
| Score    | Integer overall score (e.g., 92)                  |
| Title    | Exact job title with `[N]` reference footnote     |
| Company  | Company name (with salary penalty tag if applicable) |
| Location | Location string from verified JSON                |

### Standard Table Format -- Reference Footnote Pattern

```
**New Today: {Role Type}** ({N} new)

| Score | Title                      | Company       | Location         |
|-------|----------------------------|---------------|------------------|
| 92    | Founder Associate [1]      | Duku AI       | London (Remote)  |
| 87    | Growth Lead [2]            | MAGIC AI      | London           |
| 95    | Associate PMM * [3]        | Triptease     | London (Hybrid)  |

[1] https://linkedin.com/jobs/view/4344764433
[2] https://web3.career/jobs/magic-ai-growth-lead
[3] https://linkedin.com/jobs/view/4355891722

* Triptease salary below minimum
Duku AI — AI autonomous testing platform, Series A, London
MAGIC AI — AI-powered gaming infrastructure, Seed, Remote
Triptease — Hotel direct booking platform, Series B, London
```

```
**Still Active: {Role Type}** ({N} still active)

| Score | Title                      | Company       | Location         |
|-------|----------------------------|---------------|------------------|
| 88    | DevRel Lead [4]            | Acme Corp     | Remote           |

[4] https://linkedin.com/jobs/view/4355891723

Acme Corp — Developer tooling startup, Series A, Remote
```

---

## Sort Order

Jobs are sorted within each table by score, highest first.

**Salary-penalized jobs** appear at the bottom of their score tier (after all jobs of equal or higher unpunished score).

**Stale jobs:** If `date_posted` is available and >30 days ago, present last with a note: "Posted >30 days ago — may still be active." Do not skip entirely.

---

## Score Display Format

- **Table view (all jobs):** Integer score in the Score column (e.g., 92).
- **Score breakdown (briefs only):** Full 5-factor breakdown shown ONLY for jobs getting briefs (90+). All other jobs show only the integer score in the table.

---

## Link Formatting

**URLs as reference footnotes.** Each title gets a `[N]` suffix in the table. Full clickable URLs are listed below the table, never inline in table cells. (V14 regression — job title links must be visually distinct, not just color. The footnote pattern with `[N]` after the title ensures visibility.)

**No hyperlinks in table.** URLs are reference footnotes below, not markdown links inside cells.

---

## Annotation Markers

| Marker | Meaning | Footnote Text |
|--------|---------|---------------|
| `*`    | Salary or other concern | Specific concern described below URL list (e.g., "Triptease salary below minimum") |
| `[N]`  | URL reference | Full URL listed below table |

**Salary penalty tag:** Jobs with `salary_penalty` applied display "Below Salary Minimum" after the company name in the table. These jobs appear at the bottom of their score tier.

**Unverified listings:** Mark with dagger after title. Footnote: "Listing could not be directly verified -- found via cross-reference search." Applied when `active_status == "unverified"`.

---

## Quick Notes

One-line company summary as a footnote below the URL list for every company. Source from `notes` field in verified JSON. Extract first sentence, truncate to max 15 words if needed.

Format: `{Company} — {one-line summary}`

---

## Empty-State Messaging

If a role type has zero jobs above the 70-point threshold:

> "No strong matches found. Here are the closest."

Then show top 3 jobs regardless of score using the same standard table format.

---

## Unified Selection View

**MANDATORY before collecting user feedback (Step 17).**

After presenting all per-role-type tables (New Today + Still Active), show a single ranked list across all role types for selection. This is a unified numbered list -- not per-role-type numbering. (V16 regression -- previously each role type had its own numbered list, causing confusion.)

```
Here are all jobs ranked by score:

 #  | Score | Title                      | Company       | Type              |
----|-------|----------------------------|---------------|-------------------|
 1  | 95    | Associate PMM              | Triptease     | Marketing Assoc.  |
 2  | 92    | Founder Associate          | Duku AI       | Founder's Assoc.  |
 3  | 88    | DevRel Lead                | Acme Corp     | Community Manager |
 4  | 87    | Growth Lead                | MAGIC AI      | Marketing Manager |

Which jobs would you like briefs for? (e.g., "1, 3, 4")
```

### Unified Selection Columns

| Column  | Content                                    |
|---------|--------------------------------------------|
| #       | Sequential number across all role types     |
| Score   | Integer overall score                       |
| Title   | Job title (no footnote markers needed here) |
| Company | Company name                                |
| Type    | Role type (abbreviated if needed)           |

Apply this unified numbered list pattern to ALL user-facing selections: sources, jobs, role types. Present grouped tables for context, then a unified numbered list for selection.

---

## Dashboard URL Display

**MANDATORY after presenting the unified selection view.** (V18/V19 regression -- previously omitted.)

After displaying the unified ranked list, output on a separate line:

> View and manage all jobs at: {dashboard_url}

Where `{dashboard_url}` is read from `context.md` `## Delivery` section (same value passed to `digest-email` subagent in Step 19).

If no dashboard URL is stored in context.md, omit this line silently -- do not fabricate a URL.

### Post-Presentation Verification (Step 16b)

After presenting results, verify the dashboard URL was included:

- If `context.md` `## Delivery` contains a `Dashboard:` line, the presentation MUST include the `> View and manage all jobs at:` line with the URL.
- If it was omitted, STOP and re-present the unified selection view with the URL included.
- Do NOT proceed to Step 17 until the URL is verified present (or confirmed absent from context.md).

---

## UX Rules (Presentation-Related)

- One question per message, always. Never bundle.
- Report progress with specifics: "Searched 4 of 7 role types" not "making progress."
- Use the user's language level -- no jargon, no technical terms unless they use them first.
- Never direct the user to perform technical work (hard refresh, check URLs, inspect dashboards, run commands).

---
name: jsa-search-verify
description: Complete instructions for the search-verify subagent
---

# Search & Verify: {role_type}

## Your Task

Search for {role_type} jobs and verify all promising candidates. Write verified results to `output/verified/{role_type_slug}/`.

Do NOT interact with the user. Do NOT present results. Write files and exit.

**Working directory:** All paths in this template are relative to `03_agents/tests/v18/`.

**First action:** `cd 03_agents/tests/v18/`

## Filename Slugification

In all filenames, apply these rules to derive slugs:
- **title_slug:** Derive from job title — lowercase, spaces to hyphens, strip special characters, truncate to 50 chars (e.g., "Senior Product Manager" → "senior-product-manager")
- **company slug:** Slugify company name using the same rules (e.g., "Acme Corp" → "acme-corp")

## Run Date

{run_date} — use this date for ALL filenames and records. Do not call `date` again.

## User Profile

- **Skills:** {skills}
- **Experience:** {experience_years} years, {seniority} level
- **Industries:** {target_industries}
- **Salary minimum:** {salary_min}
- **Location:** {location_prefs}
- **Country:** {country}
- **Remote:** {remote_pref}

## Sources

{sources_for_role}

## Core Rules

1. **NEVER present a job without full verification.** Every job written to output must have confirmed active status, exact title, requirement comparison, and score.
2. **NEVER fabricate data.** Copy titles character-for-character. Extract URLs from pages. Never construct URLs by pattern.
3. **MUST verify ALL promising candidates** (estimated score 60%+). Do not cherry-pick.

## Search Workflow

1. Run `python3 scripts/jobspy_search.py "{role_type} {industry_qualifiers}" --location "{location_prefs}" --country "{country}" --output output/jobs/{role_type_slug}-aggregator.json` for aggregator results. If remote preference is remote-only, add `--remote` to the command. Do NOT pass `--exclude-titles` here — filtering happens exclusively via `filter_jobs.py` in step 4. Default is 25 results per job board site (~75 total). **Shell escaping:** If `{role_type}` contains special characters (e.g., apostrophes in "Founder's Associate"), the double quotes handle it. Never use single quotes around the role type. **Industry qualifiers** (e.g., "crypto AI startup") prevent off-industry results from polluting aggregator output.
2. **If step 1 returns zero results:** Wait 30 seconds, retry once with a broader query (e.g., drop location specifics, keep country). If still zero, log in `_status.json` and proceed to specialty sources.
3. WebFetch each specialty source listed in Sources above. **Note:** Specialty source results are processed in-context (not via filter/summarize scripts). Apply title exclusion logic manually to these results. Proceed directly to verification for promising candidates from specialty sources.
4. Run `python3 scripts/filter_jobs.py output/jobs/{role_type_slug}-aggregator.json --output output/jobs/{role_type_slug}-filtered.json --exclude-titles {exclude_titles}` to apply title exclusion constraints. Note: `filter_jobs.py` uses space-separated `--exclude-titles` (e.g., `--exclude-titles senior lead head`). This differs from `jobspy_search.py` which uses comma-separated format — but we only use `filter_jobs.py` for filtering, so no conflict.
5. Run `python3 scripts/summarize_jobs.py output/jobs/{role_type_slug}-filtered.json` to get one-line summaries. Note: output goes to stdout (no `--output` flag) — read summaries from command output.
6. Review summaries and identify promising candidates (likely 60%+ match based on title/company/location)

## Verification Workflow

For EACH promising candidate, complete ALL 5 steps:

### Step 1: CONFIRM ACTIVE

WebFetch the company career page or job listing URL.

- If WebFetch succeeds → proceed with fetched data
- If WebFetch fails (JS-rendered page):
  - If aggregator data includes full job description → proceed with aggregator data
  - If aggregator data is incomplete AND estimated score >= 85% → use agent-browser as fallback
  - Otherwise → mark active status as `"unverified"` and proceed with available data

**Job freshness (during verification):**
- Record `date_posted` from listing or aggregator data if available
- If `date_posted` is unavailable, leave field as null — do not fabricate
- Freshness does NOT affect verification — verify all promising candidates regardless of age
- Parent orchestrator handles deprioritization at presentation time

### Step 1b: CROSS-REFERENCE (LinkedIn/unverifiable listings)

If Step 1 could not confirm active status via WebFetch:
1. WebSearch: `"{company}" "{exact job title}" site:careers OR site:lever.co OR site:greenhouse.io`
2. If found on company careers page or ATS: confirm active, use that URL
3. If found on another board: confirm active via that board
4. If no cross-reference: mark `"active_status": "unverified"`

### Step 2: READ FULL DESCRIPTION

Use the aggregator description OR the fetched career page. Copy the exact title character-for-character from the listing. Do not paraphrase, shorten, or modify it.

### Step 3: CHECK REQUIREMENTS

Compare EACH requirement against user skills. Use skill normalization from `references/algorithms.md` (Skill Normalization table).

**Required skills:**
- List each required skill from the job description
- For each: Does user have it? YES / NO

**Preferred skills:**
- List each preferred/nice-to-have skill
- For each: Does user have it? YES / NO

### Step 4: SCORE

Apply the scoring rubric from `references/algorithms.md`. Show ALL math.

| Factor | Calculation | Points |
|--------|-------------|--------|
| Required skills | 40 × (matched / total required) | /40 |
| Preferred skills | 20 × (matched / total preferred) | /20 |
| Experience fit | See algorithms.md Experience Fit Scoring | /15 |
| Industry match | See algorithms.md Industry Match Scoring | /15 |
| Location | See algorithms.md Location Match Scoring | /10 |
| **BASE TOTAL** | | **/100** |
| Salary penalty | See algorithms.md Salary Validation Penalty | -10 or 0 |
| **FINAL SCORE** | | **BASE - penalty** |

### Step 5: WRITE

**Salary field mapping:** Aggregator data (from JobSpy/pandas) uses `min_amount`/`max_amount` — map these to `salary_min`/`salary_max` in the verified JSON below.

Save to `output/verified/{role_type_slug}/{company_slug}-{title_slug}.json` with this schema:

```json
{
  "title": "exact title from listing",
  "company": "exact name from website",
  "location": "from listing",
  "job_type": "Full-time",
  "work_arrangement": "Remote / Hybrid / In-person",
  "salary_min": null,
  "salary_max": null,
  "currency": null,
  "job_url": "extracted from page",
  "source": "source name",
  "date_posted": "2026-01-20 or null if unavailable",
  "active_status": "confirmed / unverified",
  "industry": "job industry",
  "requirements_met": ["requirement: evidence from user profile"],
  "gaps": ["gap description"],
  "preferred_met": ["preferred skill or qualification met"],
  "score": 85,
  "score_breakdown": {
    "required_skills": {
      "matched": 4,
      "total": 5,
      "points": 32,
      "calculation": "40 * (4/5) = 32"
    },
    "preferred_skills": {
      "matched": 2,
      "total": 3,
      "points": 13,
      "calculation": "20 * (2/3) = 13.3"
    },
    "experience_fit": {
      "points": 15,
      "calculation": "description of fit"
    },
    "industry_match": {
      "points": 15,
      "calculation": "description of match"
    },
    "location_match": {
      "points": 10,
      "calculation": "description of match"
    },
    "salary_penalty": {
      "applied": false,
      "points": 0,
      "reason": "Salary range overlaps minimum"
    },
    "total": 85
  },
  "benefits": [],
  "notes": "optional — additional context about this job, omit if none",
  "run_date": "{run_date}",
  "verified_at": "{run_date}"
}
```

## Summary Output

After writing `_status.json`, also write `output/verified/{role_type_slug}/_summary.md`:

```markdown
| Score | Title | Company | Location | Status |
|-------|-------|---------|----------|--------|
| 92 | Founder Associate | Duku AI | London (Remote) | confirmed |
| 87 | Growth Lead | MAGIC AI | London | confirmed |
| 72 | Community Lead | CryptoDAO | Remote | unverified |
...

**Searched:** N | **Verified:** N | **Above 70:** N
```

## Completion Signal

After processing ALL candidates, write `output/verified/{role_type_slug}/_status.json`:

```json
{
  "role_type": "{role_type}",
  "status": "complete",
  "total_searched": 15,
  "total_verified": 8,
  "zero_result_retry": false,
  "run_date": "{run_date}"
}
```

Set `"status"` to:
- `"complete"` — all promising candidates verified
- `"partial"` — some candidates could not be verified (e.g., all WebFetch failed)
- `"failed"` — search returned no results after retry

## Deduplication

**Note:** For deduplication, use the rules in this template, NOT `references/algorithms.md`.

Before writing a verified job file, check existing files in `output/verified/{role_type_slug}/`:
- **Company + Title + Location** must be unique (exact match)
- **Same job from multiple sources:** Keep first found, note additional source

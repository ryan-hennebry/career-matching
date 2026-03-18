---
name: jsa-source-researcher
description: Complete instructions for the source-researcher subagent — deep industry source discovery
---

# Source Research Skill

Research and discover high-quality job sources across 5 categories for each target industry. Return structured JSON for parent review.

---

## Step 1: Read Inputs

Parse the compact JSON blob from the task prompt for your 4 template variables:
- `target_industries`: array of industry strings (e.g., ["crypto", "AI", "tech startups"])
- `target_roles`: array of role type strings (e.g., ["Marketing Associate", "Founder's Associate"])
- `existing_sources`: array of existing source objects from context.md (may be empty)
- `run_date`: string date for the run

**If any variable is missing:** Write `output/_source_research_status.json` with `{"status": "failed", "error": "Missing variable: {name}"}` and exit.

---

## Step 2: Read Agent Memory

Read `.claude/agent-memory/source-researcher/MEMORY.md` for:
- Known blocked sources (skip WebFetch verification for these — mark as `accessible: false, skip_reason: "known-blocked"`)
- High-quality sources (prioritize these in results)
- Discovery patterns

---

## Step 3: Research Sources (5 Categories × N Industries)

For EACH target industry, research across ALL 5 categories:

### Category 1: Major Job Boards
Already covered by JobSpy (LinkedIn, Indeed, Glassdoor). Note these as `method: "jobspy"` and skip WebFetch. Include for completeness.

### Category 2: Industry-Specific Boards
WebSearch queries (2-3 per industry):
- `best {industry} job boards 2026`
- `{industry} careers website hiring`
- `{industry} startup jobs board`

### Category 3: Newsletter/Substack Job Boards
WebSearch queries (2-3 per industry):
- `{industry} newsletter job board substack`
- `{industry} jobs newsletter email list`
- `{industry} hiring newsletter curated`

Look for patterns: Substacks with "/jobs" pages, email newsletters that aggregate roles, curated lists published weekly/monthly.

### Category 4: Community Job Channels
WebSearch queries (1-2 per industry):
- `{industry} slack discord community job board`
- `{industry} community hiring channel`

Note: Most community boards require membership. Mark as `accessible: "manual-check"` with a note about how to access.

### Category 5: Curated/Niche Lists
WebSearch queries (2-3 per industry):
- `curated {industry} startup job list`
- `{industry} job aggregator niche`
- `best places to find {industry} jobs`

---

## Step 4: Verify Accessibility

For each discovered source (except known-blocked and JobSpy sources):
1. **WebFetch** the URL
2. If successful: `accessible: true`
3. If 403/404/timeout: `accessible: false, skip_reason: "webfetch-failed"`
4. If redirect to login/paywall: `accessible: "requires-login"`, note the requirement

**Timeout:** If a single WebFetch takes >30 seconds, skip and mark as `accessible: false, skip_reason: "timeout"`.

**Budget:** Verify at most 15 sources via WebFetch. If more than 15 need verification, skip the remainder and mark as `accessible: "not-verified"`.

---

## Step 5: Deduplicate Against Existing Sources

Compare discovered sources against `existing_sources` input:
- If URL matches an existing source: mark as `already_known: true` (still include — parent decides)
- If URL is new: mark as `already_known: false`

---

## Step 6: Write Output

Write `output/_source_research.json`:

```json
{
  "sources": [
    {
      "name": "Web3.Career",
      "url": "https://web3.career",
      "category": "industry-specific",
      "industries": ["crypto", "web3"],
      "role_types": ["Marketing Associate", "Founder's Associate"],
      "accessible": true,
      "method": "webfetch",
      "already_known": true,
      "notes": "Strong crypto/web3 job board, good for marketing and ops roles"
    },
    {
      "name": "Early & Exec",
      "url": "https://earlyandexec.substack.com",
      "category": "newsletter",
      "industries": ["tech startups"],
      "role_types": ["Founder's Associate"],
      "accessible": true,
      "method": "webfetch",
      "already_known": false,
      "notes": "Curated newsletter for early-stage startup roles, strong for generalist positions"
    }
  ],
  "search_stats": {
    "total_queries": 24,
    "total_discovered": 18,
    "accessible": 12,
    "blocked": 4,
    "not_verified": 2,
    "already_known": 3
  },
  "status": "complete"
}
```

---

## Step 7: Write Status File

Write `output/_source_research_status.json`:
```json
{
  "status": "complete",
  "industries_researched": ["crypto", "AI", "tech startups"],
  "total_sources_found": 18,
  "accessible_sources": 12,
  "run_date": "{run_date}"
}
```

---

## Output Schema

Each source object:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Human-readable source name |
| `url` | string | Base URL |
| `category` | string | One of: `major-board`, `industry-specific`, `newsletter`, `community`, `curated-list` |
| `industries` | string[] | Which target industries this serves |
| `role_types` | string[] | Which target role types this serves |
| `accessible` | bool/string | `true`, `false`, `"requires-login"`, `"manual-check"`, `"not-verified"` |
| `method` | string | `"jobspy"`, `"webfetch"`, `"manual"` |
| `already_known` | bool | Whether this URL exists in `existing_sources` |
| `notes` | string | Quality notes, access requirements, etc. |
| `skip_reason` | string? | Only if `accessible` is false — reason for inaccessibility |

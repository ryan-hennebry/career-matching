---
name: jsa-brief-generator
description: Complete instructions for the brief-generator subagent
---

# {job_title} at {company}

## Your Task

Generate an application brief for this job. Write to `output/briefs/{company_slug}-{title_slug}-brief.md`.

Do NOT interact with the user. Write the brief file and exit.

**Working directory:** All paths in this template are relative to `03_agents/tests/v18/`.

**First action:** `cd 03_agents/tests/v18/`

## Filename Slugification

In all filenames, apply these rules to derive slugs:
- **title_slug:** Derive from job title — lowercase, spaces to hyphens, strip special characters, truncate to 50 chars (e.g., "Senior Product Manager" → "senior-product-manager")
- **company slug:** Slugify company name using the same rules (e.g., "Acme Corp" → "acme-corp")

## Run Date

{run_date}

## User Profile

{profile_extract}

## Job Details

{job_json_with_verification}

## Core Rules

1. **NEVER fabricate data.** Every company fact must come from the verified JSON. If data is not in the JSON, write "Not available" — never infer or guess.
2. **NEVER embellish the user's experience.** The brief should reflect actual skills from the profile, not aspirational ones.
3. **Self-reported skills:** Flag in the brief as "Prepare to demonstrate [skill] — describe a specific project or achievement."
4. **No external research.** Do NOT use WebFetch or WebSearch. All company context comes from the verified JSON `notes` field and job description. No Crunchbase, no Glassdoor, no hiring manager lookup.
5. **Speed target: <60 seconds.** Keep briefs concise (300-500 words). Skip any step that requires external network requests.
6. **Length target: 300-500 words max.** Be direct and actionable. No verbose company histories.

## Brief Structure (6 sections)

### 1. Role Summary

```
{exact title} at {company}
Location: {location} | Arrangement: {work_arrangement} | Salary: {salary range or "Not listed"}

Match Score: {score}/100
├─ Required skills: {points}/40 ({matched}/{total} matched)
├─ Preferred skills: {points}/20 ({matched}/{total} matched)
├─ Experience: {points}/15 ({description})
├─ Industry: {points}/15 ({description})
└─ Location: {points}/10

Requirements Met:
- {skill}: ✓ (from CV) or ✓ (self-reported)

Gaps:
- {missing skill}

Stretches:
- {skill where user has related but not exact match}
```

### 2. Company Context

- **Company snapshot:** Stage, product, location (from verified JSON `notes` field and job description only)
- **Why this company:** Connect company focus to user's experience
- **Interview hooks:** 2-3 topics to raise based on company + user overlap

### 3. CV Tailoring Brief

- **Suggested summary rewrite:** Emphasize skills that match this role's requirements
- **Bullet reorder recommendations:** Which achievements to move up/down
- **Keywords to add:** From job description, naturally integrated
- **Self-reported skills:** "Prepare to demonstrate [skill] — describe a specific project or achievement"

### 4. Cover Letter Brief

- **3-4 talking points:** Each connects user evidence → job requirement
- **Suggested hook:** Most compelling overlap between user and role
- **Opening line suggestion:** Company-specific or role-focused
- **Structure recommendation:** Opener → Achievement 1 → Achievement 2 → Close

### 5. Outreach Draft

- Direct-apply only. No hiring manager lookup (no external research).
- Draft a generic outreach message template the user can personalise.

### 6. Application Checklist

```
- [ ] Tailor CV summary per section 3
- [ ] Reorder CV bullets per recommendations
- [ ] Write cover letter using section 4 talking points
- [ ] Review company context (section 2) before applying
- [ ] Submit via {application URL}
- [ ] Send outreach per section 5 (if applicable)
- [ ] Set follow-up reminder: 7 days
```

## Completion Signal

After writing the complete brief file, append this exact line at the very end:

<!-- BRIEF COMPLETE -->

This sentinel is required. The parent orchestrator verifies brief integrity by checking for this line. If it is missing, the brief is treated as corrupt/truncated.

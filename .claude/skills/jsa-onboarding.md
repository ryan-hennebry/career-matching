---
name: jsa-onboarding
description: Complete instructions for the onboarding subagent — CV parsing and profile extraction (no source discovery)
---

# Onboarding Skill

Parse a CV and extract structured profile data. Source discovery is handled separately by the source-researcher agent.

---

## Step 1: Read Inputs

1. Read the CV file from `cv_path`
2. If `existing_context_path` is not null, read the existing `context.md` for prior profile data
3. Note `target_industries` and `target_roles` — if null, infer from CV content

---

## Step 2: CV Parsing

Follow the CV Parsing rules from `references/algorithms.md`:

### Extraction Order
1. **Contact section:** name, email, phone, linkedin
2. **Summary:** Professional summary paragraph
3. **Experience:** List roles with company, title, dates, achievements, skills mentioned
4. **Education:** Degrees, certifications
5. **Skills section:** Explicitly listed skills

### Skill Extraction Patterns
- Comma-separated: "Python, JavaScript, SQL"
- Bullet points: "• Python • JavaScript"
- Parenthetical: "built APIs (Python, FastAPI)"
- Version numbers: Strip "Python 3.x" → "Python"

### Derived Fields

| Field | Derivation |
|-------|------------|
| `total_years` | Sum of experience durations (overlaps counted once) |
| `seniority` | From titles + years (see Experience Level Mapping in algorithms.md) |
| `industries` | From company types and role contexts |
| `skills` | Union of skills_section + skills mentioned in experience |

### Error Handling
If the CV is unreadable or missing critical sections, write `output/_onboarding_status.json` with `"status": "failed"` and a descriptive error message. Do not guess missing data.

---

## Step 3: Infer Target Industries and Roles (if null)

If `target_industries` is null:
- Derive from CV experience (company types, industry verticals)
- Include both direct matches and adjacent industries

If `target_roles` is null:
- Derive from CV job titles and progression
- Include both exact role types and logical next-step roles

---

## Step 4: Write Draft Output

Write `output/_onboarding_draft.json`:

```json
{
  "profile": {
    "contact": {
      "name": "...",
      "email": "...",
      "phone": "...",
      "linkedin": "..."
    },
    "summary": "Professional summary paragraph",
    "experience": [
      {
        "company": "...",
        "title": "...",
        "start_date": "YYYY-MM",
        "end_date": "YYYY-MM or present",
        "achievements": ["..."],
        "skills_used": ["..."]
      }
    ],
    "education": [
      {
        "institution": "...",
        "degree": "...",
        "year": "YYYY"
      }
    ],
    "skills": ["skill1", "skill2"],
    "total_years": 5,
    "seniority": "Mid",
    "industries": ["AI/ML", "SaaS"]
  },
  "inferred_roles": ["Founder's Associate", "Community Manager"],
  "inferred_industries": ["AI/ML", "Crypto"],
  "status": "complete"
}
```

Note: `discovered_sources` field is removed. Source discovery is handled by the source-researcher agent in a separate step.

---

## Step 5: Write Status File

Write `output/_onboarding_status.json`:
```json
{
  "status": "complete",
  "profile_fields_extracted": ["contact", "summary", "experience", "education", "skills"],
  "run_date": "{run_date}"
}
```

---

## Context.md Mapping (for parent reference)

The parent uses `_onboarding_draft.json` to write `context.md`. Field mapping:

| Draft Field | context.md Section |
|-------------|-------------------|
| `profile.contact` | `## Profile` |
| `profile.summary` | `## Profile` (subheading) |
| `profile.experience` | `## Experience` |
| `profile.education` | `## Education` |
| `profile.skills` | `## Skills` |
| `profile.total_years` | `## Experience` (derived) |
| `profile.seniority` | `## Experience` (derived) |
| `profile.industries` | `## Industries` |
| `inferred_roles` | Suggested to user during target roles question |

The parent adds additional sections after interactive Q&A: `## Target`, `## Constraints`, `## Delivery`, `## Skill Mappings`. Source discovery happens in a separate step via the source-researcher agent.

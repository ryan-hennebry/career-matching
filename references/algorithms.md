# Algorithms Reference

Edge cases and normalization patterns for scoring, CV parsing, deduplication, and learning.

---

## Scoring Edge Cases

### Skill Normalization

When matching skills, normalize related terms:

| Canonical | Also Matches |
|-----------|--------------|
| sql | postgresql, mysql, database queries, sqlite, mariadb |
| python | python3, py |
| javascript | js, es6, node.js, nodejs |
| product management | pm, product manager, product owner |
| machine learning | ml, deep learning, ai/ml |
| data analysis | data analytics, business intelligence, bi |
| agile | scrum, kanban, sprint planning |
| aws | amazon web services, ec2, s3, lambda |
| react | reactjs, react.js |

Store approved mappings in context.md under `## Skill Mappings`.

### Experience Level Mapping

| Level | Years | Title Signals |
|-------|-------|---------------|
| Junior | 0-2 | "junior", "associate", "entry" |
| Mid | 2-5 | Standard titles without prefix |
| Senior | 5-8 | "senior", "sr.", "staff" |
| Lead | 8-12 | "lead", "principal", "architect" |
| Director+ | 12+ | "director", "vp", "head of" |

### Experience Fit Scoring

| Job Level vs User Level | Score |
|-------------------------|-------|
| Exact match | 15 |
| One level stretch | 10 |
| Two+ levels under | 5 |
| Overqualified (user > job) | 10 |

### Location Match Scoring

| Scenario | Score |
|----------|-------|
| Remote job + user prefers remote | 10 |
| Hybrid job + user open to hybrid | 10 |
| Hybrid job + user remote only | 5 |
| Location in user's list | 10 |
| No match | 0 |

### Salary Validation Penalty

After computing the base score (sum of 5 factors = /100), apply a salary penalty if applicable:

| Condition | Penalty |
|-----------|---------|
| Job salary_max < user salary_min | -10 points |
| Job salary_min < user salary_min AND salary_max >= user salary_min | No penalty (range overlaps) |
| No salary listed | No penalty |
| Currency mismatch (unable to compare) | No penalty |

**Rules:**
- Penalty applied AFTER base scoring (final score can go below 70 but job is still presented if base score was 70+)
- A penalized job can never outrank a salary-compliant job of equal base score
- Tag penalized jobs with "Below Salary Minimum" in presentation
- The penalty is visible in `score_breakdown` as a new `salary_penalty` field

### Industry Match Scoring

| Match Type | Score |
|------------|-------|
| Direct match | 15 |
| Related industry | 10 |
| No match (neutral) | 5 |

Related industries: B2B SaaS ↔ Enterprise Software, AI/ML ↔ Tech, Fintech ↔ Finance

---

## Deduplication Rules

Before adding a job, check for duplicates:

1. **Company + Title + Location** must be unique
2. **Title similarity threshold:** 80% (Jaccard on word sets)
3. **Same job from multiple sources:** Keep first, add source to `sources` array

Title normalization: Remove stopwords (the, a, an, and, or, -, |) before comparison.

---

## CV Parsing

### Extraction Order

1. **Contact section:** name, email, phone, linkedin
2. **Summary:** Professional summary paragraph
3. **Experience:** List roles with dates, achievements, skills mentioned
4. **Education:** Degrees, certifications
5. **Skills section:** Explicitly listed skills

### Derived Fields

| Field | Derivation |
|-------|------------|
| total_years | Sum of experience durations (overlaps counted once) |
| seniority_level | From titles + years (see Experience Level Mapping) |
| industries | From company types and role contexts |
| all_skills | Union of skills_section + skills from experience |

### Skill Extraction Patterns

- Comma-separated: "Python, JavaScript, SQL"
- Bullet points: "• Python • JavaScript"
- Parenthetical: "built APIs (Python, FastAPI)"
- Version numbers: Strip "Python 3.x" → "Python"

### Error Handling

| Error | Action |
|-------|--------|
| Unreadable PDF | Ask user to paste text or upload DOCX |
| Missing sections | Ask user to confirm missing data |
| Ambiguous dates | Ask user to clarify |
| No skills found | Ask user to list top 10 skills |

---

## Learning System

### Storage Format (in context.md)

```yaml
### Pass Reasons (accumulated)
salary_too_low: 4
not_interested_company: 3
role_mismatch: 2

### Source Effectiveness
linkedin: discovered=45, matched=12, applied=5, interviewed=2, interview_rate=40%
lever: discovered=20, matched=15, applied=8, interviewed=4, interview_rate=50%

### Interview Outcomes
90-100: applied=5, interviewed=4, conversion=80%
80-89: applied=10, interviewed=5, conversion=50%
60-79: applied=8, interviewed=2, conversion=25%

### Preference Evolution
2026-01-29: salary_minimum 175000 → 180000 (user request)
```

### Pattern Detection Threshold

**3+ signals** in same direction triggers a suggestion. Never auto-apply changes—always confirm with user.

### Auto-Adjustments (No Confirmation)

These ranking changes happen automatically:
- Source priority by interview rate
- Skill weights from successful applications
- Company type ranking from application patterns

---

## Job Requirements Extraction

When parsing job descriptions, look for:

**Required sections:** "requirements", "qualifications", "must have", "you have"
**Preferred sections:** "nice to have", "preferred", "bonus", "plus"

**Skill indicators:**
- "X years of experience with Y" → required skill Y
- "Proficiency in X" → required skill X
- "Experience with X a plus" → preferred skill X
- "Familiarity with X" → preferred skill X

**Seniority signals:**
- "5+ years" → senior
- "10+ years" → lead/director
- "2-3 years" → mid
- "entry level" → junior

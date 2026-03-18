# Job Search Agent - Context

## Profile

- **Name:** [Your Name]
- **Location:** [City, Country]
- **Summary:** [Brief professional summary — 2-3 sentences covering your experience level, key domains, and standout achievements]

## Skills

- [Skill 1]
- [Skill 2]
- [Skill 3]
<!-- Add all relevant skills. Include both hard skills and domain expertise. -->
<!-- Mark self-reported skills with (self-reported) if not evidenced in CV -->

## Experience

- **[Title]** — [Company], [Location] ([Start] - [End], [Duration])
  - [Key achievement with metrics]
  - [Key achievement with metrics]
<!-- List all roles reverse-chronologically. Include metrics where possible. -->

**Total experience:** [X] years
**Seniority:** [Junior / Mid-level / Senior]
**Education:** [Degree, Institution (Grade, Year)]

## Target

- [Target Role 1]
- [Target Role 2]
- [Target Role 3]

**Focus:** [Industry or company type focus]
**Agentic AI flag:** If a company works on AI agents / agentic AI, flag prominently — this is the user's preference

## Industries

- [Industry 1]
- [Industry 2]

## Constraints

- **Location:** [Remote / Hybrid / In-person — City or Region]
- **Country:** [Country]
- **Remote preference:** [remote, hybrid, in-person]
- **Minimum salary:** [Amount with currency symbol]
- **Title exclusions:** [Titles to exclude, e.g. Senior, Lead, Director]
- **AI flag:** Highlight jobs mentioning AI agents, context engineering, prompt engineering, or Claude Code

## Sources

Strategy: [Describe your search strategy — what career pages and job boards to prioritise based on your target industries and roles]

| Source | URL | Method | Category |
|--------|-----|--------|----------|
| [Company] Careers | [URL] | webfetch | direct-careers |
| [Job Board] | [URL] | webfetch | [category] |
| LinkedIn (via JobSpy) | https://linkedin.com/jobs | jobspy | major-board |
| Indeed (via JobSpy) | https://indeed.com/jobs | jobspy | major-board |

## Delivery

- **Email:** [your@email.com]
- **Dashboard:** [Dashboard URL if deployed]

## Search Progress

## Search Channels

5 mandatory channels dispatched every run. Content adapts to Industries and Target above.

### Direct Career Pages

Companies with known career pages in the user's target industries. Populated from Industries and Target above.

| Company | Career URL |
|---------|-----------|
| [Company 1] | [URL] |
| [Company 2] | [URL] |

### Industry Job Boards

Industry-specific job boards matching the user's target industries.

| Board | URL | Industries |
|-------|-----|-----------|
| [Board 1] | [URL] | [Industry] |
| [Board 2] | [URL] | [Industry] |

### JobSpy Aggregator

Keyword queries for `scripts/jobspy_search.py` across LinkedIn/Indeed/Glassdoor. 8+ queries with different keyword angles.

| Query | Sites | Notes |
|-------|-------|-------|
| "[industry]" [role type] | linkedin,indeed,glassdoor | [Notes] |

### Niche Newsletters

Discovery-based channel. No static list — each run uses WebSearch to find the latest issues of relevant newsletters.

**Known newsletters (always check latest issue):**
- [Newsletter Name]: [URL]

**Example discovery queries:**
- "[industry] jobs newsletter {current month year}"
- "who is hiring {month} {year}"

### Web Search Discovery

Open-ended queries adapted to Industries + Target each run. Designed to find roles not listed on standard boards.

**Example queries:**
- "[industry] company hiring [role type] {year}"
- "new [industry] companies hiring {year}"

## Scoring & Algorithms

See `references/algorithms.md` for: scoring rubric (100-point scale), skill normalization, experience level mapping, deduplication rules, CV parsing patterns.

### Scoring Weights
- Required skills: 40
- Preferred skills: 20
- Experience: 15
- Industry: 15
- Location: 10

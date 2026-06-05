# V11 Spec: Job Search Agent — Enforcement Rules + Subagent Orchestration

## Summary

V11 rewrites CLAUDE.md with MUST/NEVER enforcement rules (fixing V10's 12 behavioural failures) and adds a subagent orchestration model (fixing context exhaustion). Three agent types: parent orchestrator, role-type search+verify subagents, and brief-generation subagents.

## Decisions Made (Interview)

| Decision | Choice |
|----------|--------|
| Verification when WebFetch fails | Aggregator data first, agent-browser fallback at 85%+ |
| Batch presentation strategy | Subagent orchestration (one subagent per role type) |
| Subagent coordination | CLAUDE.md + separate template files |
| Subagent scope | Single role-type subagent (search + verify per role type) |
| Profile passing to subagents | Parent extracts + injects into template variables |
| Verification Log | Subagent output files ARE the log (no merging to context.md) |
| Self-reported skills | Scored equally, brief-differentiated (flag as self-reported) |
| User feedback on rejections | Record signal + one follow-up question |
| Rate limiting | Sequential subagent batches of 2-3 |
| State resume | Session checkpoint file (session-state.md) |
| Score integrity | Anti-gaming rules + one worked example in template |
| Return sessions | Quick change check (3-line summary + one question) |
| Verified output format | Existing job JSON + verification object |
| Brief company research | 4-step company research checklist |
| Scheduled (unattended) runs | Conservative defaults + note in digest |
| Template size | Comprehensive (full rules, ~3K tokens per subagent) |
| Template file location | Separate files: subagent-search-verify.md, subagent-brief.md |
| Dream companies | Removed entirely (onboarding, context.md, workflows) |
| Date handling | Capture once at start of subagent run |
| Onboarding pace | Strict one question at a time |
| Release strategy | Single V11 release |
| Spec scope | Test environment only (03_agents/tests/v11/) |

---

## File Structure

```
03_agents/tests/v11/
├── CLAUDE.md                              # REWRITTEN (~180 lines) — parent orchestrator instructions
├── context.md                             # Blank template + Search Progress section (no Verification Log here)
├── .claude/settings.local.json            # From V10 (unchanged)
├── references/
│   ├── algorithms.md                      # From production (unchanged)
│   ├── sources.md                         # From production (unchanged)
│   ├── templates.md                       # From production (unchanged)
│   ├── subagent-search-verify.md          # NEW: role-type subagent template (~3K tokens)
│   └── subagent-brief.md                  # NEW: brief generation subagent template (~2K tokens)
├── scripts/
│   ├── jobspy_search.py                   # From V10 (unchanged)
│   ├── filter_jobs.py                     # From V10 (unchanged)
│   ├── summarize_jobs.py                  # From V10 (unchanged)
│   ├── send_email.py                      # From V10 (unchanged)
│   └── create_briefs_pdf.py               # From V10 (unchanged)
├── tests/
│   ├── test_filter_jobs.py                # From V10 (unchanged)
│   └── test_summarize_jobs.py             # From V10 (unchanged)
└── output/
    ├── jobs/                              # Raw search results (JSON)
    ├── verified/                          # NEW: subagent verified results
    │   └── {role_type}/                   # One directory per role type
    │       └── {company}-{title-slug}.json  # Job JSON + verification object
    ├── briefs/                            # Generated briefs (MD/PDF)
    ├── digests/                           # Daily digests
    └── session-state.md                   # NEW: checkpoint file for resume
```

---

## Files to Create/Modify

### 1. `CLAUDE.md` — Parent Orchestrator Instructions (~180 lines)

**Section Structure:**

| Section | Lines | Purpose |
|---------|-------|---------|
| Header | ~3 | Agent identity |
| Core Rules | ~24 | 6 MUST/NEVER rules |
| Onboarding | ~18 | 7-step flow (dream companies removed), includes "skills beyond CV" |
| Constraint Derivation | ~12 | + store ALL role types explicitly |
| Source Discovery | ~8 | + map sources to role types |
| Orchestration Workflow | ~20 | NEW: subagent dispatch, batching, coordination |
| Presentation Workflow | ~12 | Present per role type as subagents complete |
| UX Rules | ~8 | One question at a time, progress reporting, no tech work |
| Scheduled Runs | ~10 | Conservative defaults, Decisions Made section in digest |
| Session Management | ~10 | Checkpoint file, resume flow, progressive offloading |
| Security | ~4 | Agent handles .env silently |
| Capabilities | ~3 | Reference |
| Outputs | ~4 | + date rule |
| File Structure | ~8 | Updated with verified/ and session-state.md |

**Core Rules (6 MUST/NEVER):**

1. NEVER present a job without full verification (fixes V10 failures 1, 3, 5, 8)
2. NEVER fabricate data — copy exactly from source (fixes 6, 9, 12)
3. MUST search ALL target role types before ranking (fixes 2)
4. MUST ask one question at a time (fixes 7)
5. NEVER ask user to do technical work (fixes 4)
6. MUST batch work within context limits (fixes 5, 11)

**Onboarding (7 steps — strict one-at-a-time):**

1. Read context.md + scan output/
2. If profile exists → quick change check: 3-line summary + "Anything changed since [date]?"
3. Ask for CV
4. Parse CV → write to context.md
5. Present extracted profile for correction
6. Ask: "Skills you have that aren't on your CV?" → flag as `source: self-reported` in context.md. Scored equally in matching. Briefs differentiate: "Prepare to demonstrate [skill] — consider [project/example]"
7. Target questions (one per message): roles, industries, location, salary, email
8. Derive constraints → confirm with user

**Orchestration Workflow:**

1. Read ALL role types from `## Target` in context.md
2. Read `references/subagent-search-verify.md` as template
3. For each role type, prepare template variables:
   - `{role_type}` — the target role
   - `{skills}` — user's skills list (including self-reported)
   - `{experience_years}` — total years
   - `{seniority}` — seniority level
   - `{target_industries}` — industry list
   - `{salary_min}` — minimum salary
   - `{location_prefs}` — location preferences
   - `{remote_pref}` — remote preference
   - `{sources_for_role}` — sources mapped to this role type
   - `{run_date}` — captured once via `date +%Y-%m-%d`
4. Launch subagents in batches of 2-3 (to avoid rate limiting)
5. Wait for each batch to complete before launching next
6. Update `## Search Progress` in context.md after each batch
7. As each subagent completes, read `output/verified/{role_type}/` and present results
8. Collect user feedback per role type (if rejected: record signal + one follow-up question)
9. For accepted jobs (user wants briefs): launch brief subagents using `references/subagent-brief.md`
10. Write session-state.md progressively. After presenting a role type, offload details to file.

**Presentation Workflow:**

Preconditions before presenting a role type's results:
1. All jobs for that role type verified (check output/verified/{role_type}/)
2. Every job has: exact title, working URL, active status, scored
3. Jobs ranked by score, highest first
4. Show math breakdown for each score

**Session Management:**

- Progressive offloading: after presenting + receiving feedback for a role type, write summary to session-state.md and drop details from working memory
- Brief generation always dispatched to subagent (never in parent context)
- If context running low: save full checkpoint to session-state.md, instruct user "say continue"
- session-state.md schema:
  ```
  ## Session State
  Phase: [onboarding|searching|presenting|briefing]
  Run Date: {date}
  Batch: {N} of {M}

  ## Completed Role Types
  - {role_type}: {N} verified, {N} presented (user: accepted/rejected — reason)

  ## Pending Role Types
  - {role_type}: [not started|searching|verified]

  ## User Feedback
  - "{direct quote or summary}"

  ## Pending Brief Generation
  - {job_id}: {company} - {title}
  ```

**Security:**

Agent creates/updates .env silently. Never ask user to edit config files. Never expose API keys in conversation.

---

### 2. `context.md` — Template (V11)

Same structure as production context.md with these changes:

**Removed:**
- `dream_companies` from `## Target`
- Dream company references from `## Delivery`

**Modified:**
- Skills section: support `source: self-reported` flag
  ```
  skills:
    - product management
    - sql
    - prompt engineering (self-reported)
  ```

**Added:**
```
## Search Progress

| Role Type | Status | Source(s) | Jobs Found | Verified | Date |
|-----------|--------|-----------|------------|----------|------|
```

**Employed Mode updated:** Remove dream company bypass.

---

### 3. `references/subagent-search-verify.md` — Role-Type Subagent Template (~3K tokens)

Comprehensive template containing ALL rules. Variable slots filled by parent.

**Template Structure:**

```markdown
# Search & Verify: {role_type}

## Your Task
Search for {role_type} jobs and verify all promising candidates. Write verified results to output/verified/{role_type}/.

## Run Date
{run_date} — use this date for ALL filenames. Do not call `date` again.

## User Profile
- Skills: {skills}
- Experience: {experience_years} years, {seniority} level
- Industries: {target_industries}
- Salary minimum: {salary_min}
- Location: {location_prefs}
- Remote: {remote_pref}

## Sources
{sources_for_role}

## Core Rules
1. NEVER present a job without full verification
2. NEVER fabricate data — copy exactly from source
3. MUST verify ALL promising candidates (score 60%+)

## Search Workflow
1. Run `python3 scripts/jobspy_search.py --query "{role_type}" --location "{location}" --remote {remote_flag}`
2. WebFetch each specialty source listed above
3. Run `python3 scripts/filter_jobs.py` to apply constraints
4. Run `python3 scripts/summarize_jobs.py` to get one-line summaries
5. Identify promising candidates (likely 60%+ match)

## Verification Workflow (per job)
1. CONFIRM ACTIVE — WebFetch company career page. If WebFetch fails (JS-rendered):
   - If aggregator data includes full description → proceed with aggregator data
   - If aggregator data is incomplete AND estimated score >= 85% → use agent-browser
   - Otherwise → mark active status as "unverified" and proceed with available data
2. READ FULL DESCRIPTION — Use aggregator description OR fetched career page. Copy exact title character-for-character.
3. CHECK REQUIREMENTS — Compare each requirement against user skills:
   - List each required skill: matched (Y/N)
   - List each preferred skill: matched (Y/N)
4. SCORE — Apply rubric, show math:
   - Required skills: 40pts × (matched / total required)
   - Preferred skills: 20pts × (matched / total preferred)
   - Experience fit: 15pts (exact=15, one stretch=10, 2+ under=5, overqualified=10)
   - Industry match: 15pts (direct=15, related=10, none=5)
   - Location: 10pts (match=10, partial=5, none=0)
5. WRITE — Save to output/verified/{role_type}/{company}-{title-slug}.json

## Anti-Gaming Rules
- Missing required skill = 0 points for that skill. Not partial.
- If a job doesn't specify a requirement clearly, score 0 for that category. Unknown ≠ assumed match.
- Show the math: list each skill, matched/not, points awarded.

## Worked Example
Job: "Senior Product Manager" at TechCo
Required: Python (user has? NO → 0), SQL (YES → score), Kubernetes (NO → 0)
3 required skills, 1 matched = 33% → 40 × 0.33 = 13pts
Despite good title match, this job scores LOW because requirements don't align.

## Accuracy Rules
- Titles: copy character-for-character from listing
- URLs: extract from page, never construct by pattern
- Companies: use name as written on their website
- If URL returns 404, mark as "URL broken" — never guess a replacement

## Output Schema
Standard job JSON with added verification object:
{
  "id": "...",
  "title": "exact title from listing",
  "company": "exact name from website",
  "url": "extracted from page",
  "location": "...",
  "remote": true/false,
  "salary_min": N,
  "salary_max": N,
  "discovered_at": "{run_date}",
  "source": "...",
  "description": "full description text",
  "verification": {
    "active": true/false/"unverified",
    "score": N,
    "score_breakdown": {
      "required_skills": {"matched": [...], "missing": [...], "points": N},
      "preferred_skills": {"matched": [...], "missing": [...], "points": N},
      "experience_fit": {"job_level": "...", "user_level": "...", "points": N},
      "industry_match": {"job_industry": "...", "match_type": "...", "points": N},
      "location": {"job_location": "...", "match_type": "...", "points": N}
    },
    "requirements_met": [...],
    "gaps": [...],
    "verified_date": "{run_date}"
  }
}

## Deduplication
Company + Title + Location must be unique. Title similarity threshold: 80% (Jaccard on word sets).

## Skill Normalization
[Include full skill normalization table from algorithms.md]
```

---

### 4. `references/subagent-brief.md` — Brief Generation Subagent Template (~2K tokens)

```markdown
# Brief Generation: {job_title} at {company}

## Your Task
Generate an application brief for this job. Write to output/briefs/{job_id}-brief.md.

## Run Date
{run_date}

## User Profile
{profile_extract}

## Job Details
{job_json_with_verification}

## Core Rules
1. NEVER fabricate data — every claim must come from a WebFetch result
2. If data not found, write "Not found" — never infer

## Company Research Checklist
1. WebFetch {company} website → extract: founded year, employee count, stage/funding, product description
2. WebFetch "{company} funding OR launch OR news" → extract: last funding round, recent events, notable partnerships
3. WebFetch Glassdoor for {company} → extract: rating, notable review themes (if available)
4. For ANY field where WebFetch returns nothing: write "Research unavailable"

## Brief Structure (6 sections)

### 1. Role Summary
- Exact title (from verification)
- Location / remote status
- Salary range (if available)
- Match score: {score}/100
- Score breakdown table (from verification)
- Requirements met: [list]
- Gaps: [list]
- Stretches: [list where user has related but not exact skill]

### 2. Company Context
- Company snapshot (from research checklist)
- Recent signals (from news search)
- Why this company (connect company focus to user's experience)
- Interview hooks (topics to raise based on company + user overlap)

### 3. CV Tailoring Brief
- Suggested summary rewrite (emphasize matching skills)
- Bullet reorder recommendations
- Keywords to add (from job description)
- For self-reported skills: "Prepare to demonstrate [skill] — describe a specific project or achievement"

### 4. Cover Letter Brief
- 3-4 talking points (each: user evidence → job requirement)
- Suggested hook (most compelling overlap)
- Opening line suggestion
- Structure recommendation

### 5. Outreach Draft
- WebFetch LinkedIn/company page for hiring manager name
- If found: draft outreach message
- If not found: write "Hiring manager not identified"

### 6. Application Checklist
- [ ] Tailor CV per section 3
- [ ] Write cover letter per section 4
- [ ] Submit via [application URL]
- [ ] Send outreach per section 5 (if applicable)
- [ ] Set follow-up reminder: 7 days

## Accuracy Rules
- Every company fact must have a source (WebFetch URL)
- Titles: character-for-character from listing
- Don't embellish the user's experience — brief should reflect actual skills
```

---

## V10 Failure-to-Fix Mapping

| # | V10 Failure | V11 Fix |
|---|-------------|---------|
| 1 | Title matching without requirements | Core Rule 1 + Verification Workflow step 3 (requirement comparison) |
| 2 | Incomplete search coverage | Core Rule 3 + Orchestration (one subagent per role type) + Search Progress |
| 3 | Stale jobs presented as active | Core Rule 1 + Verification Workflow step 1 (confirm active) |
| 4 | Asked user to do technical work | Core Rule 5 + Security section (agent handles .env) |
| 5 | Cherry-picking verification | Core Rule 1 + Core Rule 6 + subagent model (each subagent verifies ALL its candidates) |
| 6 | Wrong job titles | Core Rule 2 + Accuracy Rules (character-for-character) |
| 7 | Multiple questions at once | Core Rule 4 + UX Rules (strict one-at-a-time) |
| 8 | Presenting before full verification | Presentation Workflow preconditions + subagent model (results only after subagent completes) |
| 9 | Aggregator URLs assumed valid | Core Rule 2 + Accuracy Rules (extract from page, never construct) |
| 10 | Missing skills not on CV | Onboarding step 6 ("Skills beyond CV?") + self-reported skill handling |
| 11 | Context exhaustion | Subagent model (each gets own 200K) + progressive offloading + checkpoint |
| 12 | Inconsistent dates | Accuracy Rules + date capture once at subagent start |

---

## Success Criteria

V11 succeeds when a live session shows:

1. Agent verifies ALL promising jobs before presenting any role type's results
2. All job titles in output match source listings exactly
3. All URLs in output resolve (no 404s from fabrication)
4. All role types from `## Target` appear in `## Search Progress` as "searched"
5. Every presented job has a verified JSON file in output/verified/
6. Dates use correct year throughout (captured once per subagent)
7. Agent asks one question at a time during onboarding
8. Agent asks about skills not on CV
9. Agent handles .env setup silently
10. Agent saves state before context exhaustion (session-state.md written)
11. Subagents launch in batches of 2-3 (not all at once)
12. Brief generation runs as separate subagent (not in parent context)
13. Score math is shown for every presented job with anti-gaming rules applied
14. Company research in briefs uses the 4-step checklist (no fabricated facts)

---

## Risks

| Risk | Mitigation |
|------|------------|
| Subagent orchestration adds complexity beyond original "CLAUDE.md only" scope | Template files contain full rules — enforcement is structural, not aspirational |
| Rate limiting from parallel subagents | Sequential batches of 2-3 reduce concurrent requests |
| Parent context still exhausts with 7 role types | Brief subagents + progressive offloading + checkpoint failsafe |
| Subagent ignores comprehensive template rules | Same risk as single-agent; mitigated by full rules + anti-gaming + worked example |
| Template variable injection fails | Template defines exactly 9 variable slots. Parent fills from context.md. Missing field → template has fallback instructions |
| Output directory conflicts between subagents | Each subagent writes to its own output/verified/{role_type}/ directory — no shared state |

---

## Implementation Steps

1. **Copy V10 environment** → `03_agents/tests/v11/`
2. **Remove dream company references** from context.md template, CLAUDE.md, and all sections
3. **Write CLAUDE.md** (~180 lines) — parent orchestrator with all sections above
4. **Write context.md** — blank template with Search Progress table, self-reported skill format, no dream companies
5. **Write references/subagent-search-verify.md** — comprehensive role-type template (~3K tokens)
6. **Write references/subagent-brief.md** — brief generation template (~2K tokens)
7. **Create output/verified/ directory** structure
8. **Verify** — run a live session: onboard → search (subagents) → verify → present → generate briefs (subagents) → validate all 14 success criteria

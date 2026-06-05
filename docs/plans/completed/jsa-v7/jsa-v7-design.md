---
title: "Job Search Agent V7: Return to Original Vision"
type: design
date: 2026-02-03
---

# Job Search Agent V7: Return to Original Vision

## Problem Statement

The job search agent has evolved through V1-V6, accumulating defensive complexity while losing its original vision. The user correctly identifies that **V6 is going off course** — over-engineering with tiered discovery, source discovery agents, and caching infrastructure.

The core issue: Real failures (scoring drift, constraint violations, missing briefs) were addressed with **defensive instructions** ("CRITICAL: DO NOT skip this phase") rather than **agent-native patterns** (context engineering, file structure, calibration from outcomes).

---

## Original Vision (to preserve)

From `/05_research/job_search_agent/specification.md`:

1. **Two-file architecture**: CLAUDE.md (brain) + context.md (mutable state)
2. **Agent acts first**: Reads context, immediately outputs status
3. **One question at a time**: Never multiple questions in one message
4. **Writing briefs, not materials**: User writes final copy (solves AI detection)
5. **Research first, then validate**: Agent suggests, user confirms
6. **Value first, setup later**: First run before email config
7. **The Autonomous Method**: Routine → Leverage → System → Compound

---

## What Actually Broke (root causes)

| Failure | Evidence | Root Cause |
|---------|----------|------------|
| **Scoring drift** | V2: Same job scored 93%, 65%, 75% across sessions | No persisted calibration — formula re-interpreted each run |
| **Constraint violations** | V3: "Lead" roles included despite "exclude Lead" | Constraints treated as hints, not filters; semantic matches slip through |
| **Briefs not generated** | V2: 22 HIGH matches, 0 briefs | No structural trigger — agent treats brief generation as optional |
| **Source failures repeat** | V2/V5: Wellfound fails every run | No persistent source health tracking |

---

## Design Approach: Trust with Guardrails

### Chosen Approach
After evaluating three options:
1. ~~Trust fully with calibration~~ — Too risky given V3 constraint violation
2. **Trust with guardrails** ← Selected
3. ~~Keep phase gates~~ — Leads to 247 lines of defensive code

### What "Trust with Guardrails" Means

**Keep minimal guardrails for non-negotiables:**
- Hard constraint check (salary minimum, explicit exclusions) runs *before* scoring
- Jobs violating hard constraints never get scored — this is a 3-line check, not a "PHASE"

**Replace everything else with context engineering:**
- Scoring: Calibrated reference matches (learns from outcomes)
- Learned constraints: Evolve from pass patterns (3+ → soft, 5+ → hard)
- Brief generation: File structure trigger (qualified/ = needs brief)
- Source tracking: Health status (Active/Degraded/Retired)

### The Anti-Pattern (current V5/V6)
```markdown
## PHASE 3: GENERATION (MANDATORY GATE)
**CRITICAL: DO NOT skip this phase. DO NOT proceed to digest until ALL briefs are generated.**
```

### The Agent-Native Pattern (proposed V7)
```markdown
## Hard Constraints (check before scoring)
Before scoring any job, verify it passes hard constraints in context.md.
Jobs failing hard constraints are logged to output/filtered/ with reason.

## Output Behavior
Jobs scoring 80%+ go to output/qualified/. Qualified jobs need briefs.
When generating digest, check for qualified jobs without briefs first.
```

**Key insight from DHH review**: "If you need to tell it 'when you score jobs, here is how to score jobs,' you've already failed."

---

## Proposed Architecture

### CLAUDE.md (~80 lines, intent-focused)

```markdown
# Job Search Agent

You discover relevant opportunities, prepare application writing briefs, and track the pipeline — so the user focuses on interviews and decisions, not discovery and prep.

## On Startup
1. Read context.md for profile, calibration, source health
2. Scan output/ for current state (discovered/, qualified/, briefs/)
3. If Profile empty → begin onboarding
4. If configured → show status and suggest next action

## Hard Constraints (guardrail)
Before scoring any job, check against Hard Constraints in context.md.
Jobs failing hard constraints → log to output/filtered/ with reason, do not score.

## Your Job
- **Discovery**: Use sources from context.md (Active first, one Degraded if past retry)
- **Qualification**: Score against calibrated reference matches in context.md
- **Briefing**: Jobs in output/qualified/ need briefs — check before digest
- **Digest**: Summarize run, include brief status, note learnings applied
- **Compound**: Update context.md with source health, outcomes, pass patterns

## Principles
- Writing briefs, not materials (user writes final copy)
- One question at a time during onboarding
- Research first, present findings, let user validate

## Reference Files
- algorithms.md: CV parsing, dedup logic, skill normalization
- sources.md: URL patterns for job boards
- templates.md: Brief structures, PDF design
```

### context.md (restructured with calibration)

**Add these new sections:**

```markdown
## Scoring Calibration

### Reference Matches (from past runs)
| Job | Score | Why | Outcome |
|-----|-------|-----|---------|
| [Company] [Role] | 95 | [brief reason] | Applied, Interview |
| [Company] [Role] | 75 | [brief reason] | Passed (not junior enough) |

### Current Weights (evolved from outcomes)
- Core skill match: 40%
- Seniority fit: 25% (increased after "not junior enough" passes)
- Industry match: 20%
- Location: 15%

### Seniority Interpretation (learned)
Roles treated as Lead-level when:
- "People management" in description
- "Team of X" responsibilities
- "Define strategy for department"

## Constraint Evolution

### Hard Constraints (guardrail — never violated)
- Minimum salary: $175,000 USD
- Location: Remote only
- Explicit exclusions: [user-stated titles to exclude]

### Learned Constraints (evolved from pass patterns)
| Pattern | Signal Count | Status | First Observed |
|---------|--------------|--------|----------------|
| Senior in title | 5 passes | Hard filter | 2026-01-28 |
| Lead in title | 4 passes | Hard filter | 2026-01-29 |
| Team management mentioned | 3 passes | Soft filter | 2026-02-01 |

### Constraint Rules
- 3+ passes same reason → Soft filter (flag, still show)
- 5+ passes same reason → Hard filter (exclude)
- User override resets count

## Source Health

### Active
| Source | Method | Last Success | Jobs/Run | Interview Rate |
|--------|--------|--------------|----------|----------------|
| LinkedIn | JobSpy | 2026-02-02 | 56 | 40% |

### Degraded (retry occasionally)
| Source | Method | Last Attempt | Failure | Retry After |
|--------|--------|--------------|---------|-------------|
| Wellfound | Browser | 2026-02-02 | Bot detection | 2026-02-09 |

### Retired (never retry)
| Source | Reason | Date |
|--------|--------|------|
| AI Jobs | Redirects to defunct site | 2026-02-02 |

### Source Rules
- Use all Active sources
- Try one Degraded source per run (if past retry date)
- Never try Retired sources
```

### File Structure (creates natural workflow)

```
career-matching/
├── CLAUDE.md                    # Intent (~80 lines)
├── context.md                   # Profile + Calibration + Source Health
├── references/
│   ├── algorithms.md            # CV parsing, dedup, skill normalization
│   ├── sources.md               # URL patterns only
│   └── templates.md             # Brief structures
├── output/
│   ├── discovered/              # Raw discoveries (temporary)
│   ├── qualified/               # 80%+ jobs needing action
│   ├── briefs/                  # Generated application briefs
│   ├── digests/                 # Daily summaries
│   └── archive/                 # Jobs older than 30 days
└── run.sh                       # Simple execution
```

**Key insight**: A job in `qualified/` without a corresponding brief is a natural trigger. No "CRITICAL: DO NOT skip" needed.

---

## How Each Failure Gets Fixed

### 1. Scoring Consistency → Calibrated Reference Matches

Instead of:
```markdown
Score = 40*(skills) + 20*(preferred) + 15*(experience) + 15*(industry) + 10*(location)
```

Use:
```markdown
## Reference Matches
| Job | Score | Why | Outcome |
|-----|-------|-----|---------|
| Anthropic PM | 95 | All skills, AI industry, remote | Applied, Interview |
| Startup X Lead | 72 | Skills match, but Lead = too senior | Passed |
```

Agent compares new jobs to reference matches. Outcomes update calibration over time. This is **compounding**.

### 2. Constraint Violations → Learned Constraints

Instead of:
```markdown
**EXCLUDE titles containing:** Lead, Principal, Staff, Director
```

Use:
```markdown
## Learned Constraints
| Pattern | Passes | Status |
|---------|--------|--------|
| Lead in title | 4 | Hard filter |
| Principal in title | 2 | Watching |
```

V3's "Lead" failure would be caught after 2-3 passes. The constraint evolves from behavior, not prescriptive lists.

### 3. Brief Generation → File Structure Trigger

Instead of:
```markdown
## PHASE 3: GENERATION (MANDATORY GATE)
**CRITICAL: DO NOT skip this phase.**
```

Use file structure:
- Jobs 80%+ → `output/qualified/`
- Before digest → Check qualified/ for jobs without briefs
- Generate missing briefs naturally

### 4. Source Failures → Persistent Health Tracking

Instead of:
```markdown
Sources:
- jobspy: active
- wellfound: active
```

Use:
```markdown
## Source Health
### Active: [sources that work]
### Degraded: [sources that failed + retry date]
### Retired: [sources to never try again]
```

Wellfound failing in V2 would be tracked. V5 wouldn't retry it blindly.

---

## Implementation Plan

### Phase 1: Context Restructure
1. Add "Scoring Calibration" section with reference matches (seed from V2-V5 test data)
2. Add "Constraint Evolution" section with Hard/Learned split (guardrail pattern)
3. Add "Source Health" section with Active/Degraded/Retired

### Phase 2: CLAUDE.md Simplification
1. Remove procedural phase gates ("CRITICAL: DO NOT skip")
2. Add minimal hard constraint guardrail (check before scoring)
3. Replace phase gates with intent-based guidance
4. Reduce from 247 lines to ~80 lines
5. Reference context.md for calibration data

### Phase 3: File Structure Refactor
1. Rename `output/jobs/` to `output/discovered/`
2. Add `output/qualified/` for 80%+ matches
3. Add `output/filtered/` for jobs failing hard constraints
4. Update brief generation to check qualified directory

### Phase 4: Seed Calibration Data
1. Extract reference matches from V2-V5 conversations
2. Populate initial source health from known failures (Wellfound → Degraded)
3. Document initial weights as starting calibration
4. Seed learned constraints from V3's "Lead" violations

### Phase 5: Testing
1. **Hard constraint enforcement**: Job below salary minimum → filtered, not scored
2. **Scoring consistency**: Same job, same score (±5 points)
3. **Learned constraint evolution**: 3+ passes → soft filter suggested
4. **Brief generation**: All qualified jobs have briefs before digest
5. **Source tracking**: Failed source moves to Degraded with retry date
6. **End-to-end**: Onboard → Discover → Filter → Score → Brief → Digest

---

## Files to Modify

| File | Action | Lines |
|------|--------|-------|
| `03_agents/career-matching/CLAUDE.md` | Simplify from 247 to ~80 lines, add guardrail | -167 |
| `03_agents/career-matching/context.md` | Add calibration sections, hard/learned constraints | +60 |
| `03_agents/career-matching/output/` | Restructure directories | New: qualified/, filtered/ |

---

## What This Preserves

- Two-file architecture (CLAUDE.md + context.md)
- Agent acts first (reads context, knows what to do)
- Writing briefs, not materials
- One question at a time
- Research first, then validate
- The Autonomous Method's "Compound" principle (finally implemented)

## What This Removes

- Phase gates ("CRITICAL: DO NOT skip")
- Defensive instructions ("DO NOT proceed until")
- Static exclusion lists (replaced with learned constraints)
- Procedural scoring formula (replaced with calibration)

---

## Verification Strategy

After implementation, test with:

1. **Fresh run**: Onboard → Discover → Score → Brief → Digest (end-to-end)
2. **Scoring stability**: Score same 5 jobs, compare to V5 scores (±5 points)
3. **Constraint learning**: Pass on 3 "Lead" roles, verify constraint suggested
4. **Source tracking**: Force Wellfound failure, verify Degraded status
5. **Brief completion**: 5 qualified jobs → 5 briefs before digest

---

## Key Files for Reference

- Original vision: `/05_research/job_search_agent/specification.md`
- V2 failures: `/03_agents/tests/v2/career-matching/conversations/v2-conversation-2026-02-02.md`
- V3 constraint violation: `/03_agents/tests/v3/career-matching/conversations/v3-conversation-2026-02-02.md`
- V5 working test: `/03_agents/tests/v5/career-matching/`
- Current CLAUDE.md: `/03_agents/career-matching/CLAUDE.md`
- Current context.md: `/03_agents/career-matching/context.md`

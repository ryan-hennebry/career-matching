---
title: "Job Search Agent V7 Superpowers Implementation Plan"
type: plan
date: 2026-02-03
---

# Job Search Agent V7 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Simplify career-matching from 247 lines of defensive CLAUDE.md to ~80 lines of intent-focused instructions, while adding calibration and learned constraints to context.md.

**Architecture:** Replace procedural phase gates ("CRITICAL: DO NOT skip") with context engineering (calibrated reference matches, learned constraints, source health tracking). Trust the agent with minimal guardrails (hard constraint check before scoring).

**Tech Stack:** Markdown files (CLAUDE.md, context.md), file-based workflow triggers (output directories)

---

## Critical Files

| File | Action | Current | Target |
|------|--------|---------|--------|
| `03_agents/career-matching/CLAUDE.md` | Simplify | 247 lines | ~80 lines |
| `03_agents/career-matching/context.md` | Add sections | 164 lines | ~224 lines |
| `03_agents/career-matching/output/jobs/` | Rename | exists | `discovered/` |
| `03_agents/career-matching/output/qualified/` | Create | - | new |
| `03_agents/career-matching/output/filtered/` | Create | - | new |

---

## Phase 1: Context Restructure

Add calibration sections to context.md (~60 lines).

### Task 1.1: Add Scoring Calibration Section

**Files:**
- Modify: `03_agents/career-matching/context.md` (after line 145, before Session History)

**Step 1: Add the Scoring Calibration section**

Insert after `## Skill Mappings` section (line 158):

```markdown
## Scoring Calibration

### Reference Matches (seed from V5 test run 2026-02-02)
| Job | Score | Why | Outcome |
|-----|-------|-----|---------|
| 1inch Social Media Manager | 100 | Web3 + community (100K members) + social | Pending |
| watchTowr Digital Marketing Manager | 95 | Cybersecurity startup + marketing role | Pending |
| watchTowr Social & Content Manager | 95 | Same company, content expertise match | Pending |
| Evervault Events & Community Manager | 95 | Community management direct skill match | Pending |
| Tessl Events Marketing Manager | 90 | AI startup + marketing role | Pending |

### Current Weights (initial calibration)
- Industry match: 25%
- Role match: 25%
- Company stage: 25%
- Work style: 25%

### Seniority Interpretation (learned patterns)
Roles treated as too senior when:
- "Senior" in title (hard filter - 5+ passes)
- "Lead" in title (hard filter - 4+ passes)
- "Head of" / "Director" / "VP" in title (user-stated exclusion)
- "People management" or "team of X" in description
```

**Step 2: Verify insertion**

Run: `grep -c "Scoring Calibration" 03_agents/career-matching/context.md`
Expected: `1`

**Step 3: Commit**

```bash
git add 03_agents/career-matching/context.md
git commit -m "feat(career-matching): add scoring calibration section to context.md"
```

---

### Task 1.2: Add Constraint Evolution Section

**Files:**
- Modify: `03_agents/career-matching/context.md` (after Scoring Calibration)

**Step 1: Add the Constraint Evolution section**

Insert after Scoring Calibration section:

```markdown
## Constraint Evolution

### Hard Constraints (guardrail - never violated)
- Minimum salary: $175,000 USD
- Location: Remote only
- Explicit exclusions: Senior, Lead, Head of, Director, VP, Chief, Principal, Staff

### Learned Constraints (evolved from pass patterns)
| Pattern | Signal Count | Status | First Observed |
|---------|--------------|--------|----------------|
| Senior in title | 5 | Hard filter | 2026-02-02 |
| Lead in title | 4 | Hard filter | 2026-02-02 |

### Constraint Rules
- 3+ passes same reason -> Soft filter (flag, still show)
- 5+ passes same reason -> Hard filter (exclude)
- User override resets count
```

**Step 2: Verify insertion**

Run: `grep -c "Constraint Evolution" 03_agents/career-matching/context.md`
Expected: `1`

**Step 3: Commit**

```bash
git add 03_agents/career-matching/context.md
git commit -m "feat(career-matching): add constraint evolution section to context.md"
```

---

### Task 1.3: Add Source Health Section

**Files:**
- Modify: `03_agents/career-matching/context.md` (replace existing `## Sources` section at lines 72-75)

**Step 1: Replace Sources section with Source Health**

Replace:
```markdown
## Sources
# Status: active | paused
- jobspy: active
# Industry-specific sources added during onboarding
```

With:
```markdown
## Source Health

### Active
| Source | Method | Last Success | Jobs/Run | Interview Rate |
|--------|--------|--------------|----------|----------------|
| LinkedIn | JobSpy | 2026-02-02 | 56 | - |

### Degraded (retry occasionally)
| Source | Method | Last Attempt | Failure | Retry After |
|--------|--------|--------------|---------|-------------|
| Wellfound | Browser | 2026-02-02 | Bot detection | 2026-02-09 |
| WorkInStartups | WebFetch | 2026-02-02 | 403 Forbidden | 2026-02-09 |

### Retired (never retry)
| Source | Reason | Date |
|--------|--------|------|
| (none yet) | | |

### Source Rules
- Use all Active sources first
- Try one Degraded source per run (if past retry date)
- Never try Retired sources
- Update this table after each run
```

**Step 2: Verify replacement**

Run: `grep -c "Source Health" 03_agents/career-matching/context.md`
Expected: `1`

**Step 3: Commit**

```bash
git add 03_agents/career-matching/context.md
git commit -m "feat(career-matching): add source health tracking to context.md"
```

---

## Phase 2: CLAUDE.md Simplification

Reduce from 247 lines to ~80 lines of intent-focused instructions.

### Task 2.1: Write New CLAUDE.md

**Files:**
- Replace: `03_agents/career-matching/CLAUDE.md` (entire file)

**Step 1: Write new CLAUDE.md content**

```markdown
# Job Search Agent

Discover opportunities, prepare application briefs, track pipeline. User focuses on interviews and decisions.

## On Startup

1. Read context.md for profile, calibration, source health
2. Scan output/ for state (discovered/, qualified/, filtered/, briefs/)
3. If Profile empty -> begin onboarding
4. If configured -> show status, suggest next action

Always start: "I'm your job search agent. I find relevant opportunities, prepare briefs, and track your pipeline."

## Hard Constraints (guardrail)

Before scoring any job, check against Hard Constraints in context.md:
1. Salary >= minimum? If no -> log to output/filtered/ with reason, skip scoring
2. Location matches? If no -> log to output/filtered/, skip scoring
3. Title contains exclusion? If yes -> log to output/filtered/, skip scoring

Jobs failing hard constraints are never scored or shown in digest.

## Workflow

### Discovery
Use sources from context.md Source Health section:
- All Active sources
- One Degraded source if past retry date
- Never Retired sources

Save raw discoveries to output/discovered/. Deduplicate by company + title + location.

### Qualification
Score jobs against calibrated reference matches in context.md:
- Compare new job to reference matches with similar characteristics
- Use current weights for scoring factors
- Apply seniority interpretation patterns

Jobs scoring 80%+ -> move to output/qualified/

### Briefing
Jobs in output/qualified/ need briefs. Before generating digest:
1. List qualified jobs without briefs in output/briefs/
2. Generate missing briefs
3. Briefs go to output/briefs/{company}-{role}.md

### Digest
After all briefs generated:
1. Generate daily digest to output/digests/{date}-digest.md
2. Include brief status and count
3. Note any learnings applied

### Compound
After each run, update context.md:
- Source health (Active/Degraded/Retired)
- Pass reasons (track for constraint evolution)
- Reference matches (if user provides outcome feedback)

## Onboarding

One question at a time. Wait for response before continuing.
Research first, present findings, let user validate.

Steps:
1. CV Upload -> Parse, extract profile, present for validation
2. Target Roles -> Suggest 3-5 based on CV
3. Industries -> Suggest matching industries
4. Location -> Remote preference
5. Salary -> Minimum acceptable
6. First Run -> Execute discovery, show matches, then offer email setup

CV parsing details -> references/algorithms.md

## Principles

- Writing briefs, not materials (user writes final copy)
- One question at a time during onboarding
- Research first, present findings, let user validate
- Value first, setup later (first run before email config)

## Reference Files

- references/algorithms.md - CV parsing, dedup logic, skill normalization
- references/sources.md - URL patterns for job boards
- references/templates.md - Brief structures, PDF design

## File Structure

career-matching/
  CLAUDE.md              # Intent (~80 lines)
  context.md             # Profile + Calibration + Source Health
  references/            # algorithms.md, sources.md, templates.md
  output/
    discovered/          # Raw discoveries
    qualified/           # 80%+ jobs needing briefs
    filtered/            # Jobs failing hard constraints
    briefs/              # Application briefs
    digests/             # Daily summaries
    archive/             # Jobs older than 30 days
  run.sh                 # Execution script
```

**Step 2: Verify line count**

Run: `wc -l 03_agents/career-matching/CLAUDE.md`
Expected: ~85 lines (target was ~80)

**Step 3: Commit**

```bash
git add 03_agents/career-matching/CLAUDE.md
git commit -m "refactor(career-matching): simplify CLAUDE.md from 247 to ~80 lines (V7)"
```

---

## Phase 3: File Structure Refactor

Update output directories to create natural workflow triggers.

### Task 3.1: Rename output/jobs/ to output/discovered/

**Step 1: Rename directory**

```bash
cd 03_agents/career-matching/output && git mv jobs discovered
```

**Step 2: Verify rename**

Run: `ls 03_agents/career-matching/output/ | grep discovered`
Expected: `discovered`

---

### Task 3.2: Create output/qualified/ directory

**Step 1: Create directory with .gitkeep**

```bash
mkdir -p 03_agents/career-matching/output/qualified
touch 03_agents/career-matching/output/qualified/.gitkeep
```

**Step 2: Verify creation**

Run: `ls 03_agents/career-matching/output/ | grep qualified`
Expected: `qualified`

---

### Task 3.3: Create output/filtered/ directory

**Step 1: Create directory with .gitkeep**

```bash
mkdir -p 03_agents/career-matching/output/filtered
touch 03_agents/career-matching/output/filtered/.gitkeep
```

**Step 2: Verify creation**

Run: `ls 03_agents/career-matching/output/ | grep filtered`
Expected: `filtered`

**Step 3: Commit all directory changes**

```bash
git add 03_agents/career-matching/output/
git commit -m "refactor(career-matching): update file structure for V7 workflow"
```

---

### Task 3.4: Update run.sh for new directories

**Files:**
- Modify: `03_agents/career-matching/run.sh`

**Step 1: Update references from jobs/ to discovered/**

Search for `jobs/` and replace with `discovered/` where appropriate.

**Step 2: Verify no broken references**

Run: `grep "jobs/" 03_agents/career-matching/run.sh`
Expected: No matches (or only comments)

**Step 3: Commit**

```bash
git add 03_agents/career-matching/run.sh
git commit -m "fix(career-matching): update run.sh for new directory structure"
```

---

## Phase 4: Seed Calibration Data

Already done in Phase 1 (reference matches and source health seeded from V5 test data).

---

## Phase 5: End-to-End Testing

### Task 5.1: Test Hard Constraint Enforcement

**Test:** Verify jobs below salary minimum go to filtered/, not qualified/

**Verification steps:**
1. Create test job file with salary $150,000 (below $175,000 minimum)
2. Run agent discovery workflow
3. Check: `ls 03_agents/career-matching/output/filtered/` contains the job
4. Check: `ls 03_agents/career-matching/output/qualified/` does NOT contain the job

---

### Task 5.2: Test Scoring Consistency

**Test:** Score same job twice, verify scores within +/-5 points

**Verification steps:**
1. Present 1inch Social Media Manager job to agent
2. Record score
3. Clear conversation context, present same job
4. Record second score
5. Verify: scores within +/-5 points of each other

---

### Task 5.3: Test Brief Generation Trigger

**Test:** Jobs in qualified/ get briefs before digest

**Verification steps:**
1. Place test job in `output/qualified/`
2. Ask agent to generate digest
3. Verify: Agent checks for briefs first
4. Verify: Brief exists in `output/briefs/`
5. Verify: Digest mentions brief count

---

### Task 5.4: Test Source Health Tracking

**Test:** Failed source moves to Degraded status

**Verification steps:**
1. Run discovery with Wellfound in Active
2. Observe 403 failure
3. Verify: context.md shows Wellfound in Degraded section
4. Verify: Retry date is set 7 days out

---

### Task 5.5: Full End-to-End Test

**Test:** Complete flow from onboarding to digest

**Verification steps:**
1. Clear context.md profile section
2. Run agent, complete onboarding flow
3. Verify: Discovery runs against Active sources only
4. Verify: Hard constraints filter jobs to filtered/
5. Verify: 80%+ jobs go to qualified/
6. Verify: All qualified jobs get briefs
7. Verify: Digest generated with accurate brief count
8. Verify: context.md updated with source health changes

**Final commit:**

```bash
git add .
git commit -m "test(career-matching): verify V7 end-to-end workflow"
```

---

## Summary

| Phase | Tasks | Commits |
|-------|-------|---------|
| 1. Context Restructure | 3 tasks | 3 commits |
| 2. CLAUDE.md Simplification | 1 task | 1 commit |
| 3. File Structure | 4 tasks | 2 commits |
| 4. Seed Data | (included in Phase 1) | - |
| 5. Testing | 5 tasks | 1 commit |

**Total: 13 tasks, 7 commits**

## Key Design Decisions

1. **Trust with Guardrails**: Hard constraint check (3 lines) runs before scoring. Everything else is context-driven.

2. **Calibration over Formula**: Reference matches with outcomes replace static scoring formula. Agent compares new jobs to known-good matches.

3. **File Structure as Workflow**: `qualified/` directory = natural trigger for brief generation. No "CRITICAL: DO NOT skip" needed.

4. **Learned Constraints**: Pass patterns accumulate. 3+ passes = soft filter, 5+ passes = hard filter. System improves over time.

5. **Source Health**: Active/Degraded/Retired tracking prevents repeated failures (Wellfound blocked every V1-V5 run).

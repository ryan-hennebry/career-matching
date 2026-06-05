# Design: Job Search Agent V8

## Context

V7 plan was rejected in review. Three reviewers agreed: it moved complexity rather than removing it. Adding Scoring Calibration, Constraint Evolution, and Source Health sections to context.md is YAGNI - we don't have interview outcome data yet.

Current state:
- CLAUDE.md: 247 lines of defensive guardrails ("CRITICAL: DO NOT skip")
- context.md: 164 lines (profile, preferences, empty tracking sections)
- output/: 7 directories (jobs/, applications/, briefs/, cv_variants/, digests/, reports/, archive/)

Review constraints:
1. Target ~40 lines of intent in CLAUDE.md, not 80
2. Don't add sections to context.md for data that doesn't exist yet
3. Three output directories max (jobs, briefs, digests)
4. Single source of truth for hard constraints
5. Trust the agent - delete defensive instructions entirely
6. No calibration/evolution/health tracking until proven needed

## Options Considered

### Option 1: Trust the Agent Entirely
- Delete scoring rubrics, source tiers, templates, learning systems
- Agent uses judgment based on profile
- ~30 line CLAUDE.md
- Pros: Maximum simplicity, follows reviewer guidance
- Cons: No consistency mechanism across sessions

### Option 2: Keep Scoring Rubric Only
- Delete everything except the 5-factor scoring rubric (~15 lines)
- Rubric provides consistency anchor
- Pros: Explicit scoring ensures reproducibility
- Cons: Reviewers called this "configuration theater" - telling agent HOW to think

### Option 3: Keep Pass Reasons Counter
- Delete scoring/learning but keep simple pass reason tracking
- Agent asks why on pass, stores count
- Pros: Low overhead, informs preferences
- Cons: Still YAGNI - counter is empty, rules engine for unproven problem

### Option 4: Hard Constraints Only
- No scoring rubric, no learning system
- Binary pass/fail on constraints (salary, location, industries)
- Agent uses judgment for ranking within constraints
- Pros: Simplest possible, profile is the consistency mechanism
- Cons: Loses explicit scoring

## Chosen Approach

**Option 4: Hard Constraints Only** (with Option 1's simplicity)

Reviewers unanimously recommended trusting the agent. The consistency mechanism is the stable profile in context.md, not scoring rubrics. Session 47 reads the same profile as session 1.

Pass tracking deleted entirely - agent can ask "why are you passing?" in-session without persisting counters.

## Architecture

### CLAUDE.md (~30 lines)

```markdown
# Job Search Agent

You find relevant opportunities and prepare application briefs so the user focuses on interviews and decisions, not discovery and prep.

## On Startup

1. Read context.md for profile and constraints
2. Scan output/jobs/ for current state
3. If no profile → begin onboarding
4. Otherwise → show status, suggest next action

## Constraints

Hard constraints live in context.md. Jobs that fail these don't surface:
- Salary minimum
- Location/remote requirements
- Target industries

## Outputs

- Jobs: `output/jobs/{id}.json`
- Briefs: `output/briefs/{id}-brief.md`
- Digests: `output/digests/{date}.md`

## Briefs

Write application briefs, not full materials. The user writes final copy.

## When User Passes

Ask why. Use judgment to inform future suggestions.
```

### context.md (structure only)

```markdown
# Job Search Agent - Context

## Profile
name:
email:
linkedin_url:

## Skills
# populated from CV during onboarding

## Experience
# populated from CV during onboarding

## Target
roles:

## Constraints
salary_minimum:
remote_preference:
industries:

## Dream Companies
```

### Output Directories (3 total)

- `output/jobs/`
- `output/briefs/`
- `output/digests/`

### Deleted

**From CLAUDE.md:**
- Scoring rubrics (40 points for skills, etc.)
- Source tiers table
- Decision boundaries table
- Material generation templates (6-section brief structure)
- Daily digest section structure
- Learning system section
- Employed mode section
- Scheduled runs section
- LinkedIn audit section
- Interview brief section
- File structure diagram

**From context.md:**
- Learnings section (Pass Reasons, Pass Statistics)
- Source Effectiveness tracking
- Interview Outcomes tracking
- Preference Evolution tracking
- Pending Suggestions
- Auto-Adjustments Applied
- Skill Mappings
- Session History
- Last Run section
- Delivery section
- Preferences section (stretch_tolerance, research_depth)

**Directories:**
- `output/applications/`
- `output/cv_variants/`
- `output/reports/`
- `output/archive/`
- `references/` folder (algorithms.md, sources.md, templates.md)

## Success Criteria

1. CLAUDE.md is under 40 lines
2. context.md contains only profile and constraints (no empty tracking sections)
3. Three output directories only
4. Agent successfully discovers jobs, creates briefs, generates digests
5. No regression in core functionality (onboarding, discovery, brief generation)

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Loss of scoring consistency | Medium | Profile is stable; agent judgment is sufficient |
| Missing features users need | Low | Can add back if proven needed |
| Onboarding incomplete without templates | Low | Agent knows how to onboard without explicit steps |
| No employed mode | Low | Add back when user gets a job |

---

## Handoff

Design complete. Run `/plan` to break into executable steps.

# Review: Job Search Agent V7 Implementation Plan

## Plan Summary

The plan simplifies career-matching from 247 lines of defensive CLAUDE.md to ~80 lines of intent-focused instructions, adding calibration and learned constraints to context.md. It replaces procedural guardrails ("CRITICAL: DO NOT skip") with context engineering (reference matches, constraint evolution, source health tracking).

---

## Review Feedback

### DHH Rails Reviewer

**Verdict: Direction is right, but still over-engineered**

**The Good:**
- Simplification is the correct direction
- "File structure as workflow" is elegant (convention over configuration)
- Removing defensive "CRITICAL: DO NOT skip" instructions is correct

**Issues Identified:**

1. **Scoring Calibration is too clever:**
   - Percentage weights (25% each) are premature optimization
   - The agent has judgment - let it use it
   - Reference matches good; explicit weights are "configuration theater"

2. **Constraint Evolution builds a state machine you don't need:**
   - "3+ passes = soft filter, 5+ = hard filter" is a rules engine before you know you need one
   - YAGNI - start with hard constraints only
   - Add learned constraints when you have proof you need it

3. **Source Health is over-complicated:**
   - Three states (Active/Degraded/Retired) with retry dates for ONE working source
   - "Interview Rate" column will never be filled
   - Simpler: "Working: LinkedIn. Broken: Wellfound, WorkInStartups"

4. **Too many directories:**
   - Six directories for a three-state pipeline
   - `filtered/` should be a log file, not a directory
   - Jobs in `active/` with brief files = "briefed" (convention over configuration)

5. **Split context should be unified:**
   - Why two files (CLAUDE.md + context.md)?
   - Consider: CLAUDE.md (instructions) + profile.yml (structured data)
   - Session History and learnings sections are "aspirational cruft"

**DHH's Simpler Version:** ~40 line CLAUDE.md + profile.yml. Delete everything else.

---

### Kieran Rails Reviewer

**Verdict: Right direction, needs refinement before implementation**

**Issues Identified:**

1. **CRITICAL - Hard Constraints duplication:**
   - Defined in CLAUDE.md AND context.md
   - Two sources of truth = confusion
   - **Fix:** Single source of truth in context.md only

2. **Missing directory transitions:**
   - Plan renames `jobs/` to `discovered/`
   - Ignores: `applications/`, `cv_variants/`, `reports/`
   - **Regression risk** - plan should address ALL existing directories

3. **Testing strategy incomplete:**
   - No edge case tests (empty qualified/, all sources Degraded, corrupted context.md)
   - No regression tests for existing features (email, LinkedIn audit, interview briefs)
   - No rollback strategy
   - Test 5.2 (scoring consistency) is flaky - tests LLM variance, not system

4. **Calibration approach unclear:**
   - Weights defined but never referenced in CLAUDE.md
   - How does agent score? Weights? Reference similarity? Both?
   - **Fix:** Add explicit scoring instructions

5. **Onboarding regression:**
   - Current: 7 steps including Sources
   - Proposed: 6 steps, Sources removed
   - Who populates Source Health during onboarding?

6. **Constraint Evolution unclear:**
   - "Soft filter (flag, still show)" - show WHERE?
   - **Fix:** Specify output location for soft-filtered jobs

7. **Missing error handling:**
   - What happens when JobSpy returns 0 results?
   - What happens when brief generation fails mid-run?

8. **File formats unspecified:**
   - What format for each directory? JSON? Markdown?

---

### Code Simplicity Reviewer

**Verdict: Complexity moved, not removed. YAGNI violations throughout.**

**Core Finding:**
- Current: 247 + 164 = 411 lines total
- Proposed: 80 + 224 = 304 lines total
- **Only 26% reduction**, not the dramatic simplification implied

**YAGNI Violations:**

| Feature | Problem |
|---------|---------|
| Reference Matches with Outcomes | No interview data exists yet |
| Constraint Evolution auto-promotion | Automation for unvalidated problem |
| Source Health Interview Rate | Will be empty for months |
| Retry After dates | Calendar logic for sources that might never work |
| Archive directory | Mentioned once, never explained |
| Six output directories | Current has 5, proposed has 6 - not simplification |

**File Structure as Workflow is NOT simpler:**
- Moving files between directories = file operations
- Reading directory contents = workflow state detection
- Race conditions if multiple runs happen
- **Simpler:** Status field in job file, not directory location

**Recommended Simplification:**
- CLAUDE.md: ~30 lines of intent
- context.md: Current structure unchanged (don't add new sections)
- output/: 3 directories (jobs, briefs, digests)
- No calibration until you have 10+ interview outcomes
- No constraint evolution until pattern emerges organically

**Core insight:** "The solution isn't to move complexity to context.md with state machines. The solution is to trust the agent and delete the complexity entirely."

---

## Identified Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Regression from missing directory mapping | High | Document ALL existing directory transitions |
| Dual source of truth for constraints | High | Remove inline constraints from CLAUDE.md |
| Onboarding step removed without explanation | Medium | Document Sources step removal or restore it |
| Scoring instructions ambiguous | Medium | Add explicit scoring method to CLAUDE.md |
| No rollback strategy | Medium | Archive current CLAUDE.md before replacing |
| Edge cases untested | Medium | Add tests for empty states, failures, corruption |
| Complexity moved not removed | Low | Consider deferring calibration sections entirely |

---

## Required Changes

### Critical (must fix before implementation)

- [ ] Remove Hard Constraints duplication - single source of truth in context.md
- [ ] Document ALL directory transitions (applications/, cv_variants/, reports/)
- [ ] Add rollback strategy (archive current CLAUDE.md)
- [ ] Fix Test 5.2 - replace flaky LLM consistency test with deterministic checks

### Important (should fix)

- [ ] Add explicit scoring instructions to CLAUDE.md (how to use weights + references)
- [ ] Specify file formats for each output directory
- [ ] Document or restore Sources onboarding step
- [ ] Clarify soft filter output location
- [ ] Add error handling section

### Consider (recommended by reviewers)

- [ ] Defer Scoring Calibration section until interview data exists
- [ ] Defer Constraint Evolution section until pattern emerges
- [ ] Simplify Source Health to 3 lines (working/broken list)
- [ ] Reduce to 3 output directories (jobs, briefs, digests)
- [ ] Consider profile.yml for structured data instead of prose in context.md

---

## Approval Status

**NEEDS CHANGES**

The plan has the right architectural direction (trust the agent, use context over guardrails), but adds speculative complexity that violates YAGNI. All three reviewers identified the same core issue: the plan moves complexity rather than removing it.

**Minimum viable changes before proceeding:**
1. Fix Hard Constraints duplication
2. Document all directory transitions
3. Add rollback strategy
4. Fix Test 5.2

**Recommended approach:** Simplify the simplification. Ship ~40 line CLAUDE.md with hard constraints only. Add calibration/evolution sections when you have real data demanding them.

---

## Next Steps

1. Update plan to address Critical items
2. Consider deferring calibration sections (reviewers unanimous on YAGNI)
3. Re-run `/review` after updates
4. When approved, run `/build` to implement

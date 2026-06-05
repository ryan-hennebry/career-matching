# Design: Job Search Agent V10

## Context

V9 was a clean test environment that successfully completed the core workflow (onboarding → search → digest → briefs → email) while exposing **7 failure modes**. V10 is a **refinement release** that fixes these failures without architectural redesign.

### Core Principle: Dynamic Constraint Derivation

V10 introduces a key architectural shift: **the agent derives all constraints from conversation, not templates**.

Instead of predefined exclusion lists or fixed scoring weights, the agent:
1. Learns user intent through conversation
2. Analyzes what that means (e.g., "junior/mid level" → which titles to exclude)
3. Derives scoring weights based on what user emphasizes
4. Stores all derived constraints in context.md for reproducibility

This means V10 starts with a **blank context.md** (headers only) and the agent populates everything through intelligent analysis of the onboarding conversation.

### V9 Failures to Fix

| # | Failure | Root Cause | Fix Type |
|---|---------|------------|----------|
| 1 | "Lead" title not excluded | WebFetch bypassed title filter | New script |
| 2 | Scoring not deterministic | Rubric only in agent reasoning | Dynamic derivation + storage |
| 3 | Digest/briefs out of sync | Generated from different data | Workflow |
| 4 | Context burn from raw JSON | No summarization layer | New script |
| 5 | WebFetch sources not filtered | No universal filter | New script |
| 6 | Newsletter added without validation | No content check | CLAUDE.md |
| 7 | API key exposed | No credential guidance | CLAUDE.md |

## Chosen Approach

**Separate V10 environment** — Copy `03_agents/tests/v9/` to `v10/`, then apply fixes from the V9 analysis.

Why separate:
- Preserves V9 as baseline for A/B comparison
- Lower risk with incremental changes
- Clear diff shows exactly what changed

## Architecture

### New Scripts

#### 1. `scripts/filter_jobs.py`
Universal title filtering for any source (JobSpy, WebFetch, manual).

```
Input: jobs.json + --exclude-titles (agent provides derived values)
Output: filtered_jobs.json
```

The agent determines what to exclude based on onboarding conversation, then passes those values to the script.

Addresses: Failures #1, #5

#### 2. `scripts/summarize_jobs.py`
One-line summaries to prevent context burn.

```
Input: output/jobs/*.json
Output: Title | Company | Location | Salary (20 jobs max)
```

Addresses: Failure #4

### CLAUDE.md Updates

1. **Constraint Derivation** — New section after "On Startup":
   ```markdown
   ## Constraint Derivation

   During onboarding, derive all constraints from user conversation:

   1. **Title exclusions** — Based on seniority preference, determine which title
      keywords indicate misfit. Example: "junior/mid level" → exclude titles
      containing senior, lead, head, director, vp, principal, chief, staff, manager

   2. **Scoring weights** — Based on what user emphasizes in conversation, assign
      weights to criteria. If user mentions salary multiple times, weight it higher.
      If location flexibility is mentioned, weight it lower.

   3. **Store immediately** — Write all derived constraints to context.md right
      after derivation. This ensures reproducibility on future runs.

   The key insight: constraints emerge from understanding user intent, not templates.
   ```

2. **Context Management** — Add line: "Never read raw JSON files into context — use scripts/summarize_jobs.py"

3. **Source Discovery** — Step 2 changes from "Verify accessible" to "Verify accessible AND content matches constraints"

4. **Digest Workflow** — New section enforcing single-pass generation:
   - Collect all jobs → filter ALL → score → ranked list → digest → briefs from same list

5. **Security** — Add credential handling guidance: "API keys must be stored in .env, never inline"

### context.md Template

**Blank template with headers only** — no predefined values, no examples:

```markdown
# Job Search Agent - Context

## Profile

## Skills

## Experience

## Target

## Constraints

## Industries

## Sources

## Scoring Rubric

## Dream Companies

## Delivery
```

The agent populates all sections through onboarding conversation analysis.

## Implementation Phases

### Phase 1: Environment Setup
- Copy v9/ → v10/
- Replace context.md with blank template
- Update any hardcoded paths

### Phase 2: New Scripts
- Add `filter_jobs.py` with tests
- Add `summarize_jobs.py` with tests

### Phase 3: CLAUDE.md Updates
- Add Constraint Derivation section
- Add Context Management guidance
- Update Source Discovery
- Add Digest Workflow section
- Add Security guidance

### Phase 4: Verification
- Unit tests for scripts
- Live session testing each failure mode

## Success Criteria

V10 succeeds when:

1. **Filtering works universally** — Jobs from WebFetch sources are filtered by agent-derived title exclusions
2. **Scoring is deterministic** — Agent derives rubric from conversation, stores in context.md, same input → same ranking
3. **Digest/briefs stay in sync** — Generated from single ranked list
4. **Context stays under 40%** — Summaries read instead of raw JSON
5. **Sources validated for content** — Newsletter editions checked for seniority match
6. **No credentials in output** — .env pattern enforced
7. **No predefined constraints** — All constraints derived from onboarding conversation

## Verification Plan

### Unit Tests
- `test_filter_jobs.py` — Verify title exclusion logic
- `test_summarize_jobs.py` — Verify output format, 20-job limit

### Live Session Tests
Specific scenarios to test each failure mode:

| Test | Expected Result |
|------|-----------------|
| Add job with "Lead" in title from WebFetch | Excluded (using agent-derived exclusions) |
| Check scoring rubric after onboarding | Stored in context.md with agent-derived weights |
| Generate digest then briefs | Same jobs, same order |
| Search 60+ jobs | Context under 40% |
| Add exec-focused newsletter | Agent flags seniority mismatch |
| Provide API key inline | Agent requests .env storage |
| Check context.md before onboarding | Headers only, no data |
| Check context.md after onboarding | All sections populated from conversation |

## Risks

| Risk | Mitigation |
|------|------------|
| Filter script misses edge cases | Comprehensive test cases (case sensitivity, partial matches) |
| Agent derives wrong constraints | Review derived constraints with user before proceeding |
| Live session reveals new failures | Document and queue for V11 |

## File Structure

```
03_agents/tests/v10/
├── CLAUDE.md                    # Updated with 5 sections
├── context.md                   # Blank template (headers only)
├── .claude/settings.local.json  # Same as V9
├── scripts/
│   ├── jobspy_search.py         # From V9 (unchanged)
│   ├── send_email.py            # From V9 (unchanged)
│   ├── filter_jobs.py           # NEW: Universal title filter
│   └── summarize_jobs.py        # NEW: Context-efficient summaries
├── tests/
│   ├── test_filter_jobs.py      # NEW
│   └── test_summarize_jobs.py   # NEW
└── output/
    ├── jobs/
    ├── briefs/
    └── digests/
```

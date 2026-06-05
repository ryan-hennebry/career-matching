# Design: Job Search Agent V9

## Context

V8 completed its core mission (5 matches, 5 briefs) but had 6 documented failures:
1. Context burn from unfiltered job descriptions
2. Initial search returned wrong seniority levels
3. Single source assumption (only JobSpy)
4. `python` vs `python3` command
5. No context management strategy
6. Agent listed options instead of recommending

V9 is a clean test environment to validate fixes. No prior context, empty profile, full onboarding test.

## Options Considered

### Option A: Incremental Patches
Apply fixes directly to V8 files (~25 lines).

- Pros: Fast, minimal changes
- Cons: No clean before/after, session context pollution

### Option B: V9 Fresh Start (Chosen)
Create new `v9/` directory with fixes applied and empty state.

- Pros: Clean comparison, fresh context test, proper versioning
- Cons: More setup work

### Option C: Split PRs
Separate script fixes from CLAUDE.md guidance.

- Pros: Isolated review
- Cons: Delays full fix, failures are interconnected

## Chosen Approach

**Option B: V9 Fresh Start** with:
- Completely empty context.md (template only)
- Empty output directories
- All 6 fixes applied to CLAUDE.md and jobspy_search.py
- Configurable `--country` flag instead of hardcoded value
- **Source discovery during onboarding** — agent researches best 5-10 sources per industry (niche boards, newsletters, career aggregators) and stores curated list in context.md

## Architecture

### Directory Structure

```
03_agents/tests/v9/
├── CLAUDE.md                    # Fixed agent instructions (~50 lines)
├── context.md                   # Empty template (structure only)
├── scripts/
│   └── jobspy_search.py         # Fixed script with --exclude-titles, --country
├── .claude/
│   └── settings.local.json      # Permitted domains (copy from v8)
└── output/
    ├── jobs/
    │   └── .gitkeep
    ├── briefs/
    │   └── .gitkeep
    └── digests/
        └── .gitkeep
```

### CLAUDE.md Changes

Add **Principles** section (~4 lines):
```markdown
## Principles

1. **Verify fit before presenting** - Check seniority/requirements match before showing results
2. **Source breadth and variety** - Use niche boards, newsletters, and aggregators — not just major sites
3. **Conserve context** - Filter server-side, store in files, read summaries first
4. **Recommend, don't list** - Suggest single highest-leverage next action
```

Add **Source Discovery** section (~6 lines):
```markdown
## Source Discovery

During onboarding, after learning target industries:
1. Research the best job sources for each industry (WebSearch)
2. Include variety: niche job boards, newsletters, aggregators
3. Curate 5-10 high-quality sources per industry
4. Store in context.md ## Sources for reuse
```

Add **Context Management** section (~4 lines):
```markdown
## Context Management

1. Store raw search results in output/jobs/*.json, not in context
2. Read one-line summaries (title/company/location) first
3. Only fetch full descriptions for confirmed-interest jobs
4. Use Task tool for brief generation if context is tight
```

Fix **Capabilities** line:
```markdown
- Job search: `python3 scripts/jobspy_search.py` for major boards, WebFetch for specialty sources (per context.md)
```

### context.md Template

Completely empty — just section headers with placeholder comments. Agent populates during onboarding.

```markdown
# Job Search Agent - Context

## Profile
# name, email, linkedin_url, location

## Skills
# populated after CV review

## Experience
# populated after CV review

## Target
# roles to search for

## Constraints
# salary_minimum, remote_preference, locations, seniority, exclude_titles

## Industries
# target industries

## Sources
# specialty boards for target industries (populated during onboarding)

## Dream Companies
# companies to always surface

## Delivery
# email for notifications
```

### jobspy_search.py Changes

Add arguments:
```python
parser.add_argument("--exclude-titles", help="Comma-separated title keywords to exclude")
parser.add_argument("--country", default="UK", help="Country for Indeed (default: UK)")
```

Add post-filter logic:
```python
if args.exclude_titles:
    exclude = [x.strip().lower() for x in args.exclude_titles.split(",")]
    results = [j for j in results if not any(ex in j.get("title", "").lower() for ex in exclude)]
```

Update scrape_jobs call:
```python
country_indeed=args.country,
```

## Success Criteria

1. **CLAUDE.md stays under 70 lines** (adding Source Discovery section increases target)
2. **Fresh onboarding works** - Agent extracts profile from CV without prior context
3. **Source discovery happens** - Agent researches and curates 5-10 sources per industry during onboarding
4. **Source variety achieved** - Mix of niche boards, newsletters, aggregators (not just LinkedIn/Indeed)
5. **Seniority filtering happens automatically** - No user correction needed for senior roles
6. **Context stays under 30%** - Two-pass strategy keeps context efficient
7. **Agent recommends, doesn't list** - Single high-leverage suggestion after tasks

## Risks

| Risk | Mitigation |
|------|------------|
| Principles too vague | Keep them action-oriented, not philosophical |
| Context Management ignored | Make it a numbered checklist, not prose |
| Source research burns context | Do research early in session, store results immediately |
| Sources section grows unbounded | Curate 5-10 per industry, prioritize quality over quantity |
| --exclude-titles filter too aggressive | Log filtered count in script output |

## Test Plan

1. Start fresh Claude Code session in `03_agents/tests/v9/`
2. Upload CV, trigger onboarding
3. Observe: Does agent ask good constraints questions?
4. **Observe: Does agent research sources for your industries?**
5. **Check context.md: Are 5-10 varied sources stored per industry?**
6. Run job search, observe: Does it use variety of sources (not just JobSpy)?
7. Check context usage: Under 30% after first search?
8. Request briefs, observe: Does agent recommend next action?

## Files to Create/Modify

| File | Action | Lines |
|------|--------|-------|
| `v9/CLAUDE.md` | Create (based on v8 + fixes) | ~55 |
| `v9/context.md` | Create (empty template) | ~50 |
| `v9/scripts/jobspy_search.py` | Create (based on v8 + flags) | ~75 |
| `v9/.claude/settings.local.json` | Copy from v8 | ~20 |
| `v9/output/jobs/.gitkeep` | Create | 0 |
| `v9/output/briefs/.gitkeep` | Create | 0 |
| `v9/output/digests/.gitkeep` | Create | 0 |

---

## Handoff

Design complete. Run `/plan` to break into executable TDD steps.

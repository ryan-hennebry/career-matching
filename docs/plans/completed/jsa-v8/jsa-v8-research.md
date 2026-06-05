# Research: Job Search Agent V8 Failures

## Current State

The V8 session completed its core mission (5 strong matches, 5 application briefs) but consumed 40%+ context inefficiently and required 3 user corrections. The analysis identified 6 failures, most of which are implementation issues addressable through CLAUDE.md guidance and script enhancements.

---

## Code References

### Agent Instructions
- `03_agents/tests/v8/CLAUDE.md:1-46` — Current 46-line agent instruction file
- `03_agents/tests/v8/CLAUDE.md:14` — Job search capability line: `scripts/jobspy_search.py` without `python3` prefix
- `03_agents/tests/v8/CLAUDE.md:38-45` — Scheduled runs section (no context management)

### User Context
- `03_agents/tests/v8/context.md:40-55` — Constraints section with seniority and exclude_titles
- `03_agents/tests/v8/context.md:56-60` — Industries section (Crypto, AI, Tech, Startups)
- `03_agents/tests/v8/context.md:62-63` — Empty Dream Companies section

### JobSpy Script
- `03_agents/tests/v8/scripts/jobspy_search.py:19-26` — Argument parser (no `--exclude-titles` flag)
- `03_agents/tests/v8/scripts/jobspy_search.py:29-36` — `scrape_jobs()` call with hardcoded sites
- `03_agents/tests/v8/scripts/jobspy_search.py:35` — Hardcoded `country_indeed="USA"` (wrong for UK user)

### Session Outputs
- `03_agents/tests/v8/output/digests/2026-02-03.md:3-6` — Session summary (375+ raw → 5 filtered)
- `03_agents/tests/v8/output/digests/2026-02-03.md:44-49` — Sources that failed (Wellfound 403, WorkInStartups 404)
- `03_agents/tests/v8/output/digests/2026-02-03.md:56-59` — Agent's own "Search Improvements" suggestions

### Design Documents
- `docs/plans/active/jsa-v8-design.md:48-54` — Chosen approach: "Hard Constraints Only"
- `docs/plans/active/jsa-v8-design.md:162-168` — Success criteria (under 40 lines, no regression)
- `docs/plans/active/jsa-v8-analysis.md:122-208` — Proposed CLAUDE.md diff with fixes

---

## Failures Mapped to Code

### Failure 1: Context burn from unfiltered job descriptions

**What happened:** Agent pulled 2500+ char descriptions for 10+ jobs before filtering

**Current code gap:**
- `CLAUDE.md` has no context management guidance
- `jobspy_search.py` returns all results to stdout, agent reads into context
- No `--exclude-titles` server-side filtering

**Relevant files:**
- `CLAUDE.md:38-45` — Scheduled runs with no context strategy
- `jobspy_search.py:38-56` — Results dumped to stdout/file with no pre-filter

---

### Failure 2: Initial search returned wrong seniority levels

**What happened:** First search returned Marketing Manager roles at £70K+ (senior), user had to say "exclude all senior roles"

**Current code gap:**
- `context.md:47` says `seniority: junior/mid-level` but this is informational only
- `context.md:48-54` has `exclude_titles` list but agent didn't use it proactively
- `CLAUDE.md` doesn't instruct agent to filter by exclude_titles before showing results

**Relevant files:**
- `CLAUDE.md:14` — Capability line doesn't mention passing exclude filters
- `context.md:48-54` — exclude_titles list (Senior, Lead, Head of, etc.)

---

### Failure 3: Single source assumption

**What happened:** Agent only used JobSpy (LinkedIn/Indeed/Glassdoor), user asked "why only jobsearch?"

**Current code gap:**
- `CLAUDE.md:14` mentions WebFetch but doesn't list industry-specific boards
- No sources configuration in `context.md`
- Agent didn't proactively check crypto job boards despite Industries: Crypto

**Relevant files:**
- `CLAUDE.md:14` — "WebFetch for company career pages" (too vague)
- `context.md:56-60` — Industries listed but no linked sources
- `.claude/settings.local.json` — Has crypto boards permitted but agent didn't know to use them

---

### Failure 4: python vs python3 command

**What happened:** `python scripts/jobspy_search.py` failed with "command not found"

**Current code gap:**
- `jobspy_search.py:1` has `#!/usr/bin/env python3` shebang
- `CLAUDE.md:14` says `scripts/jobspy_search.py` without specifying `python3`

**Relevant file:**
- `CLAUDE.md:14` — Missing `python3` prefix

---

### Failure 5: No context management strategy

**What happened:** User observed "40% context used, out of smart zone"

**Current code gap:**
- `CLAUDE.md` has no "Context Management" section
- No guidance to store results in files vs context
- No two-pass strategy (summaries first, full descriptions on demand)

**Relevant file:**
- `CLAUDE.md` — Missing section entirely

---

### Failure 6: Agent listed options instead of recommending

**What happened:** After briefs, agent asked "what else can you do?" with 15+ options

**Current code gap:**
- `CLAUDE.md` has no guidance on proactive recommendations
- No "Principles" section about recommending vs listing

**Relevant file:**
- `CLAUDE.md` — Missing principles/behavior guidance

---

## Patterns Found

### 1. V8 Design Philosophy
The design explicitly chose "trust the agent" over configuration-heavy approaches. The profile in `context.md` is the consistency mechanism, not scoring rubrics.

### 2. Minimal CLAUDE.md Target
Design targeted ~30-40 lines. Current file is 46 lines. Adding new sections must be minimal.

### 3. Implicit vs Explicit Constraints
`context.md` has `exclude_titles` and `seniority` but agent didn't use them proactively. The connection between constraint data and search behavior is unclear.

### 4. Sources Gap
`.claude/settings.local.json` permits 15+ job boards but `CLAUDE.md` doesn't tell agent which to use when. User had to prompt multi-source search.

### 5. Script Limitations
`jobspy_search.py` is UK-focused user but has `country_indeed="USA"` hardcoded. No exclude filter. No remote flag usage in context.

---

## Related Files

### V8 Test Session
```
03_agents/tests/v8/
├── CLAUDE.md                         # Agent instructions (46 lines)
├── context.md                        # User profile & constraints
├── scripts/jobspy_search.py          # JobSpy wrapper (65 lines)
├── .claude/settings.local.json       # Permitted domains
└── output/
    ├── jobs/.gitkeep                 # Empty (jobs kept in context)
    ├── briefs/*.md                   # 5 application briefs
    └── digests/2026-02-03.md         # Session digest
```

### Planning Documents
```
docs/plans/active/
├── jsa-v8-design.md                  # Architecture decisions
├── jsa-v8-plan.md                    # Implementation steps
├── jsa-v8-reviews.md                 # Review rounds
└── jsa-v8-analysis.md                # Session analysis (failures source)
```

---

## Historical Context

### V8 Design Decisions (from jsa-v8-design.md)
- **Rejected approaches:** Scoring rubrics (Option 2), pass reason tracking (Option 3)
- **Chosen approach:** Hard constraints only + trust agent judgment (Option 4)
- **Deleted:** 200+ lines of CLAUDE.md, learning systems, 4 output directories
- **Kept:** Profile-based consistency, 3 output dirs, brief generation

### Reviewer Feedback (from jsa-v8-reviews.md referenced in design)
- "Trust the agent" was unanimous
- "Configuration theater" criticism of explicit scoring
- "YAGNI" for data that doesn't exist yet
- Target ~40 lines of intent, not 80

---

## Summary of What Needs to Change

| File | Change Type | Lines Affected |
|------|-------------|----------------|
| CLAUDE.md | Add Principles section | +8 lines |
| CLAUDE.md | Add Context Management section | +6 lines |
| CLAUDE.md | Fix python3 command | 1 line |
| context.md | Add Sources section | +10 lines |
| jobspy_search.py | Add --exclude-titles flag | +5 lines |
| jobspy_search.py | Fix country_indeed for UK | 1 line |

**Total estimated changes:** ~30 lines of additions/modifications

---

## Handoff

Research complete. Run `/design` to explore options and define architecture for the fixes.

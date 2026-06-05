**NOTE: This design document has been SUPERSEDED by the implementation plan (`jsa-v14-plan.md`) on all divergent points. Key differences: 5 agents (not 7), no schema_version, no run_history, no ExpiredJob subclass, 8 phases (not 9), push to main (not job-search-state branch), {role_type_slug}/{filename} key format, single sync CLI command. The plan is the canonical reference for implementation.**

# Design: Job Search Agent V14

## Context

V13 delivered the first end-to-end named subagent pipeline (search, verify, brief, digest, PDF, email). 10 wins, 5 failures, 2 edge cases. Architecture is stable. V14 focuses on: output quality (design system upgrade), daily automation (GitHub Actions + state management), context efficiency (3 new subagents), resilience (auto-retry), and mobile-responsive email.

---

## Decisions (from interview)

| Decision | Choice |
|----------|--------|
| Daily runs: brief generation | Digest-only (briefs on-demand interactively) |
| Scheduler | GitHub Actions (free, full CLI support) |
| Design system approach | Pre-bake via frontend-design skill into jsa-design-system.md |
| LinkedIn verification | Cross-reference company careers page + other boards |
| New subagents | All 3: onboarding, source-discovery, results-presenter |
| Subagent resilience | Auto-retry once on failure |
| Subagent instructions | Skills (not reference templates) — all agents use skill pattern |
| Skill enforcement | Inline CSS in skills (COPY VERBATIM) |
| Digest link styling | Subtle underline + accent color |
| Mobile email layout | Card layout on mobile, tables on desktop |
| Daily delta display | Section split: "New Today" + "Still Active" |
| Job expiry | 14-day rolling window |
| State storage | Git-committed state.json on dedicated branch |

---

## Architecture

### 7 Named Subagents (up from 4)

**Architectural change from V13:** All subagent instructions are now delivered via skills instead of reference template files. In V13, agents had a startup step ("Read your full instructions from `references/subagent-*.md`") which cost a tool call and created two instruction delivery mechanisms. In V14, every agent declares its instruction skill in frontmatter — the framework preloads it automatically. The `references/` folder is eliminated (except `algorithms.md` and `context.md` which are reference data, not agent instructions).

| Agent | Purpose | Tools | Skills | Variables |
|-------|---------|-------|--------|-----------|
| `onboarding` | CV parsing + profile extraction (non-interactive parts) | Bash, Read, Write, Glob, Grep, WebFetch, WebSearch | jsa-onboarding | 3 |
| `source-discovery` | Research job sources per industry | Bash, Read, Write, Glob, Grep, WebFetch, WebSearch | jsa-source-discovery | 3 |
| `search-verify` | Search + verify + score jobs | Bash, Read, Write, Glob, Grep, WebFetch, WebSearch | jsa-search-verify | 14 (+1) |
| `results-presenter` | Read verified JSONs, generate formatted CLI output | Bash, Read, Write, Glob, Grep | jsa-results-presenter | 2 |
| `brief-generator` | Company research + 6-section brief | Bash, Read, Write, Glob, Grep, WebFetch, WebSearch | jsa-brief-generator | 7 |
| `digest-email` | HTML email with daily delta sections | Bash, Read, Write, Glob, Grep | jsa-design-system, jsa-digest-email | 6 (+2) |
| `briefs-pdf` | Compile briefs into continuous-page PDF | Bash, Read, Write, Glob, Grep | jsa-design-system, jsa-briefs-pdf | 1 |

### Orchestrator Workflow (19 steps)

1. Load `state.json` (create if missing)
2. Capture run date
3. Pre-run cleanup (check state.json last_run_date)
4. Read context.md (role types, constraints, sources)
5. If onboarding needed: dispatch onboarding agent (CV parse), then interactive Q&A in parent, then source-discovery agent
6. Prepare 14 template variables per role type (added `industry_qualifiers`)
7. Dispatch search-verify agents in batches of 2-3. **Auto-retry once on failure.**
8. After each batch: read `_summary.md`. Update state.json via `manage_state.py update`.
9. Cross-role-type deduplication
10. Compute daily delta via `manage_state.py delta`
11. Dispatch results-presenter agent (pass delta JSON)
12. Present results to user (read ONE file: `output/presentation-{date}.md`)
13. Collect user feedback (rejection signals + follow-up)
14. Dispatch brief agents for accepted jobs. **Auto-retry once on failure.**
15. Checkpoint after every 3 role types
16. Dispatch digest-email + briefs-pdf in parallel. **Auto-retry once on failure.**
17. Send email (parent-orchestrated, same gate logic as V13)
18. Update state.json (record user actions)
19. Write final session-state.md

### Scheduled Mode (GitHub Actions)

Skips steps 5, 12-13, 14-15 (no onboarding, no user interaction, no briefs). Runs search-verify, computes delta, generates digest-only email, sends, commits state.json.

- Cron: `0 7 * * 1-5` (8am UK time)
- Branch: `job-search-state` (long-lived, diverges only in state.json)
- Secrets: `ANTHROPIC_API_KEY`, `RESEND_API_KEY`
- Model: claude-opus-4-6
- Timeout: 30 minutes

---

## V13 Failure Fix Mapping

| V13 Issue | V14 Fix | Phase |
|-----------|---------|-------|
| F1: Generic design system | frontend-design skill baked into jsa-design-system.md, CSS embedded in agent skills | 1 |
| F2: Marketing Associate thin results | Industry-qualified search queries (`"Marketing Associate crypto"`) | 3 |
| F3: Unverified LinkedIn listings | Cross-reference company careers page + other boards; `†` marker | 3 |
| F4: Source research wrong model | source-discovery is now a named agent; HARD CONSTRAINT: never pass `model:` | 2, 7 |
| F5: Inconsistent CLI presentation | results-presenter enforces identical format; CLAUDE.md hard constraints | 2, 7 |
| EC1: Multi-page A4 briefs PDF | Per-brief continuous pages, CSS `break-before: page` between briefs | 6 |
| EC2: LinkedIn unverifiable | Cross-reference verification step in jsa-search-verify skill | 3 |

---

## Implementation Phases

### Phase 1: Copy V13 to V14 + Design System Upgrade + Templates→Skills Migration

**Files created/modified:**
- Copy `03_agents/tests/v13/` to `03_agents/tests/v14/`
- Update all v13 path references to v14 (8+ files with hardcoded paths)
- Invoke `frontend-design` skill -> rewrite `.claude/skills/jsa-design-system.md` with distinctive fonts, color palette, typographic scale
- **Migrate reference templates to skills:** Convert each `references/subagent-*.md` to `.claude/skills/jsa-*.md`. Content stays the same — file moves from `references/` to `.claude/skills/` and gets skill frontmatter (`name`, `description`).
- **Update agent definitions:** Replace "Read your full instructions from `references/subagent-*.md`" startup logic with `skills:` frontmatter declaration. Remove `disallowedTools: Skill` from agents that had it.
- **Delete `references/subagent-*.md` files** after migration. Keep `references/algorithms.md` and `references/context.md` (reference data, not agent instructions).
- Embed complete CSS blocks in `.claude/skills/jsa-digest-email.md` and `.claude/skills/jsa-briefs-pdf.md` with "COPY VERBATIM" instruction

**Success criteria:** `grep -r "v13" 03_agents/tests/v14/` returns nothing. Design system has font imports (not system fonts). CSS blocks in skills match design system exactly. No `references/subagent-*.md` files exist. All 7 agent definitions use `skills:` frontmatter. No agent has "Read your full instructions from" in its body.

### Phase 2: New Subagents

**New files (9):**
- `.claude/agents/onboarding.md`, `source-discovery.md`, `results-presenter.md`
- `.claude/skills/jsa-onboarding.md`, `jsa-source-discovery.md`, `jsa-results-presenter.md`
- `.claude/agent-memory/onboarding/MEMORY.md`, `source-discovery/MEMORY.md` (seeded with V13 learnings), `results-presenter/MEMORY.md`

**Success criteria:** 7 agent definitions, 8 skills (design system + 7 agent skills), 7 memory directories. All agents have `model: inherit`. All agents declare skills in frontmatter.

### Phase 3: Fix V13 Failures

**Modified files:**
- `.claude/skills/jsa-search-verify.md` -- cross-reference verification step, industry-qualified queries, `_summary.md` output
- `.claude/agent-memory/search-verify/MEMORY.md` -- updated learnings

**Key changes:**
- New Step 1b in verification: WebSearch company careers page + aggregator mirrors for LinkedIn-only listings
- Template variable count: 13 -> 14 (add `industry_qualifiers`)
- After completion: write `_summary.md` alongside `_status.json`

**Success criteria:** jsa-search-verify skill has cross-reference step. `_summary.md` format documented. 14 variables documented.

### Phase 4: Daily Delta + State Management

**New files (3):**
- `state.json` -- schema with jobs, expired_jobs, run_history
- `scripts/manage_state.py` -- load/save/delta/update/expire functions + CLI
- `tests/test_manage_state.py` -- 6 tests (empty state, returning jobs, 14-day expiry, new identification, user action preserved, score update)

**State schema:**
```json
{
  "schema_version": 1,
  "last_run_date": "2026-02-09",
  "jobs": {
    "company-slug-title-slug": {
      "title": "...", "company": "...", "score": 85,
      "role_type": "...", "first_seen": "2026-02-08",
      "last_seen": "2026-02-09", "active_status": "confirmed",
      "job_url": "...", "location": "...", "user_action": null
    }
  },
  "expired_jobs": [],
  "run_history": [{"date": "...", "new_jobs": 3, "still_active": 12, "expired": 1}]
}
```

**Success criteria:** All 6 tests pass. `manage_state.py update` and `delta` commands work. 14-day expiry logic correct.

### Phase 5: Digest Email Rewrite

**Modified files:**
- `.claude/skills/jsa-digest-email.md` -- complete rewrite
- `.claude/agents/digest-email.md` -- 6 template variables (up from 4)
- `.claude/agent-memory/digest-email/MEMORY.md` -- updated

**Key changes:**
- Variables: add `new_today_count`, `still_active_count`
- Sections: Header -> Summary strip -> **New Today (N)** (full detail) -> **Still Active (M)** (compact) -> Footer
- REMOVED: Statistics section, score distribution
- Links: subtle underline + accent color on job titles
- Mobile: `@media` queries for card layout on narrow screens, table fallback for clients that strip CSS
- CSS: complete block from jsa-design-system.md embedded with COPY VERBATIM

**Success criteria:** No "Statistics" in skill. "New Today" and "Still Active" sections defined. Mobile media queries present. Link styling uses underline.

### Phase 6: Briefs PDF Continuous-Page Rendering

**Modified files:**
- `.claude/skills/jsa-briefs-pdf.md` -- rendering approach rewrite
- `.claude/agent-memory/briefs-pdf/MEMORY.md` -- updated

**Key changes:**
- Remove `format: 'A4'` -> use `width: '800px'` with `prefer_css_page_size: True`
- CSS: `break-before: page` on `.brief-page`, `break-after: page` on `.cover-page`
- No `@page { size: A4 }`, no `page-break-*` deprecated rules
- Each brief is one continuous page of variable height
- Page breaks only between title page and first brief, and between each brief

**Success criteria:** No A4 format in skill. CSS uses `break-before: page`. Python Playwright code in skill.

### Phase 7: CLAUDE.md Orchestrator Rewrite

**Modified files:**
- `CLAUDE.md` -- major rewrite
- `.claude/settings.local.json` -- `WebFetch(*)` blanket + broader Bash patterns

**Key additions:**
- HARD CONSTRAINTS section (5 rules: no model override, identical tables, quick notes, `†` marker, CSS canonical)
- Auto-retry protocol (one retry on failure, continue on second failure)
- 19-step workflow (up from 15)
- SCHEDULED RUNS section (automated vs interactive mode)
- State management integration (steps 1, 8, 10, 18)
- Results-presenter integration (steps 11-12)

**Success criteria:** HARD CONSTRAINTS present. Auto-retry documented. 19 steps. `WebFetch(*)` in settings.

### Phase 8: GitHub Actions Scheduler

**New files (1):**
- `.github/workflows/daily-digest.yml`

**Workflow:** Checkout `job-search-state` branch -> install Python deps + Playwright Chromium -> run Claude Code in scheduled mode -> commit state.json -> push

**Success criteria:** Cron `0 7 * * 1-5`. Installs deps. Uses `claude-opus-4-6`. Commits state after run.

### Phase 9: End-to-End Verification

**13 cross-file consistency checks** (grep-based)
**12 tests** (6 existing + 6 new state management)
**7 manual smoke test items**

---

## File Summary

### New Files (14)
| File | Phase |
|------|-------|
| `.claude/agents/onboarding.md` | 2 |
| `.claude/agents/source-discovery.md` | 2 |
| `.claude/agents/results-presenter.md` | 2 |
| `.claude/skills/jsa-onboarding.md` | 2 |
| `.claude/skills/jsa-source-discovery.md` | 2 |
| `.claude/skills/jsa-results-presenter.md` | 2 |
| `.claude/agent-memory/onboarding/MEMORY.md` | 2 |
| `.claude/agent-memory/source-discovery/MEMORY.md` | 2 |
| `.claude/agent-memory/results-presenter/MEMORY.md` | 2 |
| `state.json` | 4 |
| `scripts/manage_state.py` | 4 |
| `tests/test_manage_state.py` | 4 |
| `.github/workflows/daily-digest.yml` | 8 |
| `output/presentation-{date}.md` | Runtime |

### Modified Files (12)
| File | Phase | Change |
|------|-------|--------|
| `.claude/skills/jsa-design-system.md` | 1 | Complete rewrite (frontend-design skill output) |
| `.claude/skills/jsa-search-verify.md` | 1, 3 | Migrated from references/, cross-ref verification, industry queries, _summary.md |
| `.claude/skills/jsa-brief-generator.md` | 1 | Migrated from references/, paths updated |
| `.claude/skills/jsa-digest-email.md` | 1, 5 | Migrated from references/, complete rewrite (mobile, delta sections, no stats, CSS embed) |
| `.claude/skills/jsa-briefs-pdf.md` | 1, 6 | Migrated from references/, continuous-page rendering, CSS embed |
| `.claude/agents/search-verify.md` | 1 | Paths, skills frontmatter, remove startup Read logic |
| `.claude/agents/brief-generator.md` | 1 | Paths, skills frontmatter, remove startup Read logic |
| `.claude/agents/digest-email.md` | 1, 5 | Paths, dual skills frontmatter, 6 template variables |
| `.claude/agents/briefs-pdf.md` | 1, 6 | Paths, dual skills frontmatter |
| `.claude/settings.local.json` | 7 | WebFetch(*), broader Bash patterns |
| `.claude/agent-memory/search-verify/MEMORY.md` | 3 | Cross-reference, industry queries |
| `.claude/agent-memory/digest-email/MEMORY.md` | 5 | No stats, mobile, delta sections |
| `.claude/agent-memory/briefs-pdf/MEMORY.md` | 6 | Continuous page, no A4 |
| `CLAUDE.md` | 7 | Major rewrite (hard constraints, resilience, 19 steps, state, scheduled) |

### Deleted Files (4)
| File | Phase | Reason |
|------|-------|--------|
| `references/subagent-search-verify.md` | 1 | Migrated to `.claude/skills/jsa-search-verify.md` |
| `references/subagent-brief-generator.md` | 1 | Migrated to `.claude/skills/jsa-brief-generator.md` |
| `references/subagent-digest-email.md` | 1 | Migrated to `.claude/skills/jsa-digest-email.md` |
| `references/subagent-briefs-pdf.md` | 1 | Migrated to `.claude/skills/jsa-briefs-pdf.md` |

### Unchanged Files (7)
`scripts/jobspy_search.py`, `scripts/filter_jobs.py`, `scripts/summarize_jobs.py`, `scripts/send_email.py`, `references/algorithms.md` (reference data, not agent instructions), `tests/test_filter_jobs.py`, `tests/test_summarize_jobs.py`

---

## Risks

| Risk | Mitigation |
|------|-----------|
| frontend-design skill produces inconsistent output | Invoke ONCE, bake permanently, embed CSS in agent skills |
| Skill list pollution (8 jsa-* skills visible in non-agent sessions) | All prefixed `jsa-` for easy identification; cosmetic only |
| WebFetch(*) too permissive | Agent only visits job boards -- no sensitive data risk |
| GitHub Actions minute limits | 30-min timeout; daily digest-only runs are fast |
| state.json merge conflicts | Single writer (GitHub Actions); manual runs don't commit state |
| Auto-retry doubles API cost | One retry max; second failure continues pipeline |
| Email clients strip @media queries | Progressive enhancement: table layout works without CSS |

---

## Verification

### Automated
```bash
# No v13 paths
grep -r "v13" 03_agents/tests/v14/ --include="*.md" --include="*.py" --include="*.json" | grep -v ".git"

# All 7 agents inherit model
grep -c "model: inherit" 03_agents/tests/v14/.claude/agents/*.md  # expect: 7

# All 7 agents declare skills in frontmatter
grep -c "skills:" 03_agents/tests/v14/.claude/agents/*.md  # expect: 7

# No reference template files remain (subagent-* only — algorithms.md and context.md stay)
ls 03_agents/tests/v14/references/subagent-*.md 2>/dev/null  # expect: no such file

# 8 skill files exist (design system + 7 agent skills)
ls 03_agents/tests/v14/.claude/skills/jsa-*.md | wc -l  # expect: 8

# No "Read your full instructions from" in agent definitions
grep -r "Read your full instructions" 03_agents/tests/v14/.claude/agents/  # expect: nothing

# No A4 in briefs PDF skill
grep -i "format.*A4" 03_agents/tests/v14/.claude/skills/jsa-briefs-pdf.md  # expect: nothing

# No Statistics in digest skill
grep -i "statistics" 03_agents/tests/v14/.claude/skills/jsa-digest-email.md  # expect: nothing

# Design system has font imports
grep -i "import\|google.*font" 03_agents/tests/v14/.claude/skills/jsa-design-system.md  # expect: match

# CSS embedded in skills
grep -c "COPY VERBATIM" 03_agents/tests/v14/.claude/skills/jsa-digest-email.md  # expect: >= 1
grep -c "COPY VERBATIM" 03_agents/tests/v14/.claude/skills/jsa-briefs-pdf.md  # expect: >= 1

# WebFetch blanket
grep "WebFetch" 03_agents/tests/v14/.claude/settings.local.json  # expect: WebFetch(*)

# Tests pass
cd 03_agents/tests/v14 && python3 -m pytest tests/ -v
```

### Manual Smoke Test
- [ ] Interactive run: onboarding CV parse dispatches to subagent
- [ ] search-verify writes `_summary.md`
- [ ] results-presenter produces identical table format for all role types
- [ ] digest-email has no Statistics section, has mobile CSS
- [ ] briefs-pdf uses continuous pages, no A4
- [ ] state.json updated after run
- [ ] GitHub Actions workflow triggers on `workflow_dispatch`

# Design: JSA V16

## Context

V15 post-build analysis identified 7 implementation failures + 1 user-identified architectural issue. The 7 implementation fixes are prescribed (accept/reject semantics, state API misuse, git pull enforcement, email idempotency, API key stdin piping, post-run scheduled prompt, API key URLs). The architectural change — source discovery workflow — is the design question.

**Current source discovery:** During onboarding, the onboarding subagent runs 2 WebSearches per industry, WebFetches candidates for accessibility, writes sources to `context.md`. Sources are static from that point — no re-discovery on subsequent runs. The V15 session produced only 6 sources (3 JobSpy aggregators + 3 specialty), all obvious/generic. User feedback: "not niche enough to give the candidate an edge."

**User's desired behavior:**
1. Agent researches best job boards for user's specific target industries — including niche sources (Substack newsletters, Slack communities, curated lists)
2. Presents discovered sources to user for approval/additions before searching
3. User can add specific sources the agent didn't find

## Options Considered

### Option A: Enhance Onboarding Source Discovery

Expand the existing onboarding subagent's Step 4 (source discovery) with deeper research:
- More WebSearch queries (5-8 per industry instead of 2)
- Explicit niche source categories: newsletters, Slack/Discord communities, curated lists, aggregator Substacks
- WebFetch to verify each candidate
- Present sources to user for approval within the onboarding Q&A flow

**Pros:**
- Minimal structural change — enhances existing step
- Sources set once, used on every subsequent run
- No new agents or skills needed
- User sees sources during natural onboarding Q&A

**Cons:**
- Onboarding already runs long (~3-5 min). Adding deep source research could push to 8-10 min
- Sources become stale — no mechanism to refresh on subsequent runs
- Onboarding subagent is already at capacity (CV parsing, profile Q&A, industry inference, source discovery)
- Mixing deep research with interactive Q&A creates awkward flow (long pause mid-conversation)

**Risk:** Medium — could bloat onboarding duration
**Complexity:** Simple

### Option B: Separate Source Research Phase (New Step Before Search)

Insert a new phase between onboarding and search. On every run (or first run + on-demand), a dedicated source-research step:
1. Reads user profile from `context.md` (industries, roles, preferences)
2. Runs deep research: WebSearch across multiple query patterns, checks niche categories
3. Compares discovered sources against existing `context.md` sources
4. Presents delta (new sources found) to user for approval
5. User approves/rejects/adds sources → updates `context.md`
6. Search proceeds with approved sources

**Pros:**
- Deep research without blocking onboarding flow
- Can refresh sources on subsequent runs (discover new boards that launched)
- Clean separation of concerns — onboarding does profile, source-research does sources
- User approval gate before any searching happens
- Can be skipped on subsequent runs if user is happy with existing sources

**Cons:**
- Adds a new phase to the 20-step workflow (now 22+ steps)
- First interactive run gets longer overall (onboarding + source research + search)
- New subagent/skill to maintain
- Need to handle "skip if sources already approved" logic for repeat runs

**Risk:** Medium — workflow complexity increase
**Complexity:** Moderate

### Option C: Source Research as Part of Search-Verify Subagent

Extend the search-verify subagent to include a source research preamble:
1. Before searching, research niche sources for this specific role type
2. Return discovered sources + search results together
3. Parent orchestrator collates sources from all search-verify subagents
4. Present to user, get approval, re-search if needed

**Pros:**
- No new agents — extends existing search-verify
- Role-type-specific source discovery (marketing vs engineering might have different niche boards)

**Cons:**
- Breaks clean separation — search-verify now does research AND search
- User approval gate happens AFTER search already started (too late)
- Subagent already at capacity (JobSpy + WebFetch + verify)
- Can't present sources to user before searching — defeats the purpose

**Risk:** High — user approval gate comes too late
**Complexity:** Moderate

## Chosen Approach

**Option B: Separate Source Research Phase** — with optimizations to keep it fast.

Rationale:
- Option A bloats onboarding. Option C defeats the purpose (approval comes after search).
- Option B gives clean separation: onboarding handles profile, source-research handles sources, search handles jobs.
- The user's core ask is: "research first, present to me, then search." This is inherently a sequential gate — it needs its own phase.

**Confirmed decisions:**
- **Refresh strategy: "Only when I ask."** On subsequent runs, source research is SKIPPED entirely. The orchestrator checks `context.md` for existing `## Sources` section — if sources exist, skip to search. User can explicitly say "refresh sources" to re-run source research.
- **Research depth: "Deep" (8-10 queries per industry).** One-time cost on first run (~3-5 min). Covers all 5 source categories. Finds newsletters, communities, and curated lists that shallow research misses.

## Architecture

### New Phase: Source Research (Steps 7-8, shifting current 7+ down by 2)

**Step 7: Source Research Gate**

Check `context.md` for existing `## Sources` section:
- If sources exist → skip to Step 9 (search). User can say "refresh sources" to force Step 8.
- If no sources → run Step 8 (first run)

**Step 8: Source Research + Approval**

Dispatch a `source-researcher` subagent (new agent) that:
1. Reads user profile from context.md (industries, roles, seniority, location)
2. Researches sources across 5 categories per industry:
   - Major job boards (LinkedIn, Indeed — already in JobSpy)
   - Industry-specific boards (Web3.Career, CryptocurrencyJobs, etc.)
   - Newsletter/Substack job boards (e.g., Early & Exec, relevant industry newsletters)
   - Community job channels (relevant Slack/Discord communities with job boards)
   - Curated/niche lists (angel.co successors, startup-specific boards, sector-specific aggregators)
3. WebFetch each candidate to verify accessibility (skip known-blocked from regressions)
4. Returns structured JSON: array of `{name, url, category, role_types, accessible, notes}`

Parent orchestrator:
1. Reads subagent output
2. Merges with existing sources in `context.md` (preserving user's manual additions)
3. Presents to user: table of all sources (existing + new), categorized
4. User approves, removes, or adds sources
5. Writes updated `context.md` with `sources_approved: YYYY-MM-DD`

### New Files

| File | Purpose |
|------|---------|
| `.claude/agents/source-researcher.md` | Subagent definition — deep source research |
| `.claude/skills/jsa-source-researcher.md` | Skill template — research queries, categories, output format |
| `.claude/memory/source-researcher.md` | Memory — known blocked sources, quality notes |

### Modified Workflow (CLAUDE.md)

Current steps 7-20 become steps 9-22. New steps:
- **Step 7:** Source research gate (check `sources_approved` in context.md)
- **Step 8:** Source research dispatch + user approval

### Integration with 7 Implementation Fixes

All 7 fixes apply to their originally identified files. Step numbers shift by +2 for anything after the new source research phase:
1. `brief_requested` action → `manage_state.py` + CLAUDE.md (step 17 → step 19)
2. No ad-hoc Python → CLAUDE.md constraint section (no step change)
3. Git pull at startup → CLAUDE.md step 2 (no step change — before source research)
4. Email idempotency → CLAUDE.md step 21 → step 23
5. API key stdin → CLAUDE.md scheduled run section (no step change)
6. Post-run scheduled prompt → CLAUDE.md step 22 → step 24
7. API key URLs → CLAUDE.md delivery section (no step change)

## Success Criteria

1. First interactive run includes source research phase with user approval before search
2. Source research discovers at least 3 niche/non-obvious sources per industry (newsletters, communities, curated lists)
3. User can approve, remove, or add sources before search proceeds
4. Subsequent runs skip source research (user can explicitly request refresh)
5. All 7 implementation fixes verified (per V15 analysis criteria)
6. All existing tests pass + new tests for `brief_requested` action type
7. No regressions from V15 success criteria (design system, parallel search, scoring, state recovery)

## Risks

1. **Source research subagent takes too long** — Mitigated by: 8-10 WebSearch queries per industry across 5 categories + known-blocked skip list + 3-minute timeout
2. **WebFetch blocked by many niche sources** — Mitigated by: memory file of known-blocked sites, graceful degradation (report as "unverified" rather than failing)
3. **Step renumbering breaks existing references** — Mitigated by: single pass through CLAUDE.md to update all step numbers
4. **Source research returns low-quality results** — Mitigated by: structured query patterns in skill template, category-based approach ensures breadth

## Handoff Contract

- **Approach:** Separate source research phase (new Step 7-8) + 7 implementation fixes
- **Components:**
  - `source-researcher` agent + skill + memory (new — deep industry source research)
  - CLAUDE.md orchestrator (modified — new steps 7-8, step renumbering, 7 fixes)
  - `manage_state.py` (modified — `brief_requested` action)
  - `context.md` schema (modified — `sources_approved` metadata field)
- **Success criteria:** 7 measurable checks (see above)
- **Risks requiring mitigation:** Subagent duration (3-min timeout + skip list), step renumbering (single pass), WebFetch blocks (graceful degradation)
- **Refresh model:** Manual only — user says "refresh sources" to re-run. No auto-expiry.
- **Research depth:** Deep — 8-10 queries/industry across 5 categories (boards, newsletters, communities, curated lists, niche aggregators)

<!-- STAGE COMPLETE: /design, 2026-02-11 -->

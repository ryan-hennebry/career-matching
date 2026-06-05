# Plan: JSA V16 — Source Research Phase + 7 Implementation Fixes

## Overview

From the V16 design Handoff Contract:
- **Approach:** Separate source research phase (new Steps 7-8) + 7 implementation fixes from V15 analysis
- **Components:** `source-researcher` agent + skill + memory (new), CLAUDE.md orchestrator (modified), `manage_state.py` (modified), `context.md` schema (modified)
- **Research depth:** Deep — 8-10 queries/industry across 5 categories (boards, newsletters, communities, curated lists, niche aggregators)
- **Refresh model:** Manual only — user says "refresh sources" to re-run

V15 directory (`03_agents/tests/v15/`) is copied to V16 (`03_agents/tests/v16/`) as the starting point. All file paths below are relative to `03_agents/tests/v16/`.

## Files to Modify
- `CLAUDE.md` — Orchestrator rewrite: new steps 7-8, renumber 7→9 through 20→21, plus 7 fixes (23 steps total)
- `scripts/manage_state.py` — Add `brief_requested` to VALID_ACTIONS
- `tests/test_manage_state.py` — Add test for `brief_requested` action
- `tests/conftest.py` — No changes needed (fixtures are generic)

## Files to Create
- `03_agents/tests/v16/` — Full V16 directory (copy from v15)
- `.claude/agents/source-researcher.md` — New subagent definition
- `.claude/skills/jsa-source-researcher.md` — Research queries, categories, output format
- `.claude/agent-memory/source-researcher/MEMORY.md` — Known blocked sources, quality notes

## Implementation Steps

### Phase 1: Scaffold V16 Directory

#### Step 1: Copy V15 to V16
**Action:** Create V16 directory from V15 base

```bash
cp -r 03_agents/tests/v15 03_agents/tests/v16
```

**Verify:**
```bash
ls 03_agents/tests/v16/CLAUDE.md && echo "V16 directory created"
```

**Verify existing test count:**
```bash
cd 03_agents/tests/v16 && python3 -m pytest tests/ -v 2>&1 | grep -c "PASSED"
# Record this count — expected 14, but verify before proceeding
```

#### Step 2: Update internal version references
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Modify — update header from "Job Search Agent" to include V16 context. All `v15` path references in agent/skill files become `v16`.

Target files for find-and-replace (`03_agents/tests/v15/` → `03_agents/tests/v16/`):
- `.claude/agents/search-verify.md`
- `.claude/agents/brief-generator.md`
- `.claude/agents/digest-email.md`
- `.claude/agents/briefs-html.md`
- `.claude/agents/onboarding.md`
- `.claude/skills/jsa-search-verify.md`
- `.claude/skills/jsa-brief-generator.md`
- `.claude/skills/jsa-onboarding.md`
- `scripts/manage_state.py` (docstring: `JSA V15` → `JSA V16`)
- `.github/workflows/daily-digest.yml`

Note: The exact files may vary — the point is to enumerate them rather than using a wildcard.

Also update `tests/conftest.py`, `tests/test_manage_state.py`:
- No path references to change (they use relative imports)

**Verify:**
```bash
grep -r "v15" 03_agents/tests/v16/ --include="*.md" --include="*.py" --include="*.yml" | grep -v __pycache__ | wc -l
# Expected: 0 (all v15 references updated to v16)
```

#### Step 2b: Verify `sources_for_role` is consumed by search-verify agent
**Action:** Pre-build verification — confirm V15's search-verify agent already references `sources_for_role`.

```bash
grep "sources_for_role" 03_agents/tests/v16/.claude/agents/search-verify.md 03_agents/tests/v16/.claude/skills/jsa-search-verify.md
```

- If found in both files: proceed — no changes needed.
- If missing from either file: add a step in Phase 4 to update the search-verify agent/skill to consume the `sources_for_role` template variable.

**This check prevents a build-time surprise in Step 9 where `sources_for_role` is passed but potentially ignored.**

---

### Phase 2: Add `brief_requested` Action Type (Fix #1 + Fix #2)

#### Step 3: Write failing test for `brief_requested`
**File:** `03_agents/tests/v16/tests/test_manage_state.py`
**Action:** Append new test class after `TestPurgeExpired`

```python
class TestBriefRequested:
    """Tests for brief_requested action type."""

    def test_brief_requested_is_valid_action(self, empty_state, verified_dir):
        """brief_requested is accepted by record_action without error."""
        from manage_state import record_action, update_state

        job = make_verified_json(title="Growth Lead", company="Acme Corp", score=85)
        (verified_dir / "community-manager" / "acme-corp-growth-lead.json").write_text(
            json.dumps(job), encoding="utf-8"
        )
        state = update_state(empty_state, verified_dir, "2026-02-09", ["community-manager"])

        state = record_action(state, "community-manager/acme-corp-growth-lead", "brief_requested")
        assert state.jobs["community-manager/acme-corp-growth-lead"].user_action == "brief_requested"

    def test_brief_requested_appears_in_still_active(self, empty_state, verified_dir):
        """Jobs with brief_requested action appear in still_active (not excluded like rejected)."""
        from manage_state import compute_delta, record_action, update_state

        job = make_verified_json(title="Growth Lead", company="Acme Corp", score=85)
        (verified_dir / "community-manager" / "acme-corp-growth-lead.json").write_text(
            json.dumps(job), encoding="utf-8"
        )

        state = update_state(empty_state, verified_dir, "2026-02-08", ["community-manager"])
        state = record_action(state, "community-manager/acme-corp-growth-lead", "brief_requested")

        # Run 2 so it becomes still_active not new
        state = update_state(state, verified_dir, "2026-02-09", ["community-manager"])
        delta = compute_delta(state, "2026-02-09")

        assert "community-manager/acme-corp-growth-lead" in delta["still_active"]

    def test_unselected_jobs_remain_neutral(self, empty_state, verified_dir):
        """Jobs not selected for briefs keep user_action as None (not rejected)."""
        from manage_state import record_action, update_state

        for name in ("alpha-lead", "beta-mgr"):
            job = make_verified_json(title=name, company="Co", score=80)
            (verified_dir / "community-manager" / f"co-{name}.json").write_text(
                json.dumps(job), encoding="utf-8"
            )

        state = update_state(empty_state, verified_dir, "2026-02-09", ["community-manager"])

        # Only brief_requested on alpha, beta left untouched
        state = record_action(state, "community-manager/co-alpha-lead", "brief_requested")

        assert state.jobs["community-manager/co-alpha-lead"].user_action == "brief_requested"
        assert state.jobs["community-manager/co-beta-mgr"].user_action is None
```

**Verify:**
```bash
cd 03_agents/tests/v16 && python3 -m pytest tests/test_manage_state.py::TestBriefRequested -v 2>&1 | tail -10
# Expected: 3 FAILED (brief_requested not in VALID_ACTIONS)
```

#### Step 4: Implement `brief_requested` action
**File:** `03_agents/tests/v16/scripts/manage_state.py`
**Action:** Modify line 19

Change:
```python
VALID_ACTIONS = {"accepted", "rejected"}
```
To:
```python
VALID_ACTIONS = {"accepted", "rejected", "brief_requested"}
```

**Verify:**
```bash
cd 03_agents/tests/v16 && python3 -m pytest tests/test_manage_state.py::TestBriefRequested -v 2>&1 | tail -10
# Expected: 3 PASSED
```

#### Step 5: Run full test suite
**Verify:**
```bash
cd 03_agents/tests/v16 && python3 -m pytest tests/ -v 2>&1 | tail -20
# Expected: all 17 tests PASSED (14 existing + 3 new)
```

#### Step 6: Commit Phase 2
```bash
git add 03_agents/tests/v16/scripts/manage_state.py 03_agents/tests/v16/tests/test_manage_state.py
git commit -m "feat(jsa): add brief_requested action type to manage_state.py"
```

---

### Phase 3: Create Source Researcher Agent

#### Step 7: Create agent memory file
**File:** `03_agents/tests/v16/.claude/agent-memory/source-researcher/MEMORY.md`
**Action:** Create

```markdown
# Source Researcher Agent Memory

## Known Blocked Sources (403/404/timeout)
- CryptoJobsList (cryptojobslist.com) — 403
- Wellfound (wellfound.com) — 403/redirect
- startup.jobs — 404
- TopStartups.io (topstartups.io) — 403
- Welcome to the Jungle (wttj.co) — 403

## High-Quality Sources (verified accessible)
- Web3.Career (web3.career) — crypto/web3 jobs, good API-free access
- CryptocurrencyJobs (cryptocurrencyjobs.co) — crypto-specific, accessible
- BeInCrypto Jobs (beincrypto.com/jobs) — crypto news + jobs
- AI Jobs (aijobs.net) — AI-specific aggregator

## Source Discovery Patterns
- WebSearch more reliable than WebFetch for initial discovery in subagent context
- Always WebFetch candidate URLs to verify accessibility before recommending
- Newsletter/Substack boards often have job sections that are accessible
- Community boards (Discord/Slack) can't be WebFetched — note as "manual check required"
```

**Verify:**
```bash
test -f 03_agents/tests/v16/.claude/agent-memory/source-researcher/MEMORY.md && echo "Memory file created"
```

#### Step 8: Create source researcher skill
**File:** `03_agents/tests/v16/.claude/skills/jsa-source-researcher.md`
**Action:** Create

```markdown
---
name: jsa-source-researcher
description: Complete instructions for the source-researcher subagent — deep industry source discovery
---

# Source Research Skill

Research and discover high-quality job sources across 5 categories for each target industry. Return structured JSON for parent review.

---

## Step 1: Read Inputs

Parse the compact JSON blob from the task prompt for your 4 template variables:
- `target_industries`: array of industry strings (e.g., ["crypto", "AI", "tech startups"])
- `target_roles`: array of role type strings (e.g., ["Marketing Associate", "Founder's Associate"])
- `existing_sources`: array of existing source objects from context.md (may be empty)
- `run_date`: string date for the run

**If any variable is missing:** Write `output/_source_research_status.json` with `{"status": "failed", "error": "Missing variable: {name}"}` and exit.

---

## Step 2: Read Agent Memory

Read `.claude/agent-memory/source-researcher/MEMORY.md` for:
- Known blocked sources (skip WebFetch verification for these — mark as `accessible: false, skip_reason: "known-blocked"`)
- High-quality sources (prioritize these in results)
- Discovery patterns

---

## Step 3: Research Sources (5 Categories × N Industries)

For EACH target industry, research across ALL 5 categories:

### Category 1: Major Job Boards
Already covered by JobSpy (LinkedIn, Indeed, Glassdoor). Note these as `method: "jobspy"` and skip WebFetch. Include for completeness.

### Category 2: Industry-Specific Boards
WebSearch queries (2-3 per industry):
- `best {industry} job boards 2026`
- `{industry} careers website hiring`
- `{industry} startup jobs board`

### Category 3: Newsletter/Substack Job Boards
WebSearch queries (2-3 per industry):
- `{industry} newsletter job board substack`
- `{industry} jobs newsletter email list`
- `{industry} hiring newsletter curated`

Look for patterns: Substacks with "/jobs" pages, email newsletters that aggregate roles, curated lists published weekly/monthly.

### Category 4: Community Job Channels
WebSearch queries (1-2 per industry):
- `{industry} slack discord community job board`
- `{industry} community hiring channel`

Note: Most community boards require membership. Mark as `accessible: "manual-check"` with a note about how to access.

### Category 5: Curated/Niche Lists
WebSearch queries (2-3 per industry):
- `curated {industry} startup job list`
- `{industry} job aggregator niche`
- `best places to find {industry} jobs`

---

## Step 4: Verify Accessibility

For each discovered source (except known-blocked and JobSpy sources):
1. **WebFetch** the URL
2. If successful: `accessible: true`
3. If 403/404/timeout: `accessible: false, skip_reason: "webfetch-failed"`
4. If redirect to login/paywall: `accessible: "requires-login"`, note the requirement

**Timeout:** If a single WebFetch takes >30 seconds, skip and mark as `accessible: false, skip_reason: "timeout"`.

**Budget:** Verify at most 15 sources via WebFetch. If more than 15 need verification, skip the remainder and mark as `accessible: "not-verified"`.

---

## Step 5: Deduplicate Against Existing Sources

Compare discovered sources against `existing_sources` input:
- If URL matches an existing source: mark as `already_known: true` (still include — parent decides)
- If URL is new: mark as `already_known: false`

---

## Step 6: Write Output

Write `output/_source_research.json`:

```json
{
  "sources": [
    {
      "name": "Web3.Career",
      "url": "https://web3.career",
      "category": "industry-specific",
      "industries": ["crypto", "web3"],
      "role_types": ["Marketing Associate", "Founder's Associate"],
      "accessible": true,
      "method": "webfetch",
      "already_known": true,
      "notes": "Strong crypto/web3 job board, good for marketing and ops roles"
    },
    {
      "name": "Early & Exec",
      "url": "https://earlyandexec.substack.com",
      "category": "newsletter",
      "industries": ["tech startups"],
      "role_types": ["Founder's Associate"],
      "accessible": true,
      "method": "webfetch",
      "already_known": false,
      "notes": "Curated newsletter for early-stage startup roles, strong for generalist positions"
    }
  ],
  "search_stats": {
    "total_queries": 24,
    "total_discovered": 18,
    "accessible": 12,
    "blocked": 4,
    "not_verified": 2,
    "already_known": 3
  },
  "status": "complete"
}
```

---

## Step 7: Write Status File

Write `output/_source_research_status.json`:
```json
{
  "status": "complete",
  "industries_researched": ["crypto", "AI", "tech startups"],
  "total_sources_found": 18,
  "accessible_sources": 12,
  "run_date": "{run_date}"
}
```

---

## Output Schema

Each source object:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Human-readable source name |
| `url` | string | Base URL |
| `category` | string | One of: `major-board`, `industry-specific`, `newsletter`, `community`, `curated-list` |
| `industries` | string[] | Which target industries this serves |
| `role_types` | string[] | Which target role types this serves |
| `accessible` | bool/string | `true`, `false`, `"requires-login"`, `"manual-check"`, `"not-verified"` |
| `method` | string | `"jobspy"`, `"webfetch"`, `"manual"` |
| `already_known` | bool | Whether this URL exists in `existing_sources` |
| `notes` | string | Quality notes, access requirements, etc. |
| `skip_reason` | string? | Only if `accessible` is false — reason for inaccessibility |

**Verify:**
```bash
test -f 03_agents/tests/v16/.claude/skills/jsa-source-researcher.md && echo "Skill file created"
```

#### Step 9: Create source researcher agent definition
**File:** `03_agents/tests/v16/.claude/agents/source-researcher.md`
**Action:** Create

```markdown
---
name: source-researcher
description: Research and discover high-quality job sources across 5 categories per industry
tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
disallowedTools: NotebookEdit
skills: jsa-source-researcher
memory: project
model: inherit
---

You are a source-researcher subagent for the Job Search Agent.

Your job is to research and discover high-quality job sources for the user's target industries and roles. You return structured JSON — the parent handles user interaction and approval.

Parse the compact JSON blob provided in the task prompt for your 4 template variables (`target_industries`, `target_roles`, `existing_sources`, `run_date`). Confirm all 4 are present before proceeding.

**If any variable is missing:** Write `output/_source_research_status.json` with `{"status": "failed", "error": "Missing variable: {name}"}` and exit immediately.

**Working directory:** All paths are relative to `03_agents/tests/v16/`.

**First action:** `cd 03_agents/tests/v16/`
```

**Verify:**
```bash
test -f 03_agents/tests/v16/.claude/agents/source-researcher.md && echo "Agent file created"
```

#### Step 10: Commit Phase 3
```bash
git add 03_agents/tests/v16/.claude/agents/source-researcher.md \
       03_agents/tests/v16/.claude/skills/jsa-source-researcher.md \
       03_agents/tests/v16/.claude/agent-memory/source-researcher/MEMORY.md
git commit -m "feat(jsa): add source-researcher agent, skill, and memory"
```

---

### Phase 4: Rewrite CLAUDE.md Orchestrator

This is the largest phase. The CLAUDE.md file must be rewritten to:
1. Insert new Steps 7-8 (source research gate + dispatch)
2. Renumber Steps 7-20 → Steps 9-22
3. Apply all 7 implementation fixes
4. Add post-run step (Step 22: scheduled run prompt)

#### Step 11: Rewrite CLAUDE.md — HARD CONSTRAINTS section
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Modify — add constraint #5

After constraint #4, add:
```markdown
5. **Never write inline Python for state mutations.** All state changes must go through `scripts/manage_state.py` CLI subcommands. No `python3 -c` calls that import manage_state internals.
```

**Verify:**
```bash
grep -c "Never write inline Python" 03_agents/tests/v16/CLAUDE.md
# Expected: 1
```

#### Step 12: Rewrite CLAUDE.md — CORE RULES section
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Modify — update rule 8 to reflect new step count

Change:
```
8. **Use `scripts/preview.sh` for HTML preview.** Never start ad-hoc HTTP servers. Always use the preview script for serving HTML files locally.
```
To:
```
8. **Use `scripts/preview.sh` for HTML preview.** Never start ad-hoc HTTP servers. Always use the preview script for serving HTML files locally.
9. **Always provide source URLs for API key requests.** When requesting any API key, include the exact URL where the user can create/find it. Resend: resend.com/api-keys. Anthropic: console.anthropic.com/settings/keys.
```

**Verify:**
```bash
grep "Always provide source URLs" 03_agents/tests/v16/CLAUDE.md
# Expected: 1 match
```

**Verify rule numbering:**
```bash
grep -c "^[0-9]\+\." 03_agents/tests/v16/CLAUDE.md | head -1
# Count numbered rules in CORE RULES section to confirm no collision
```

#### Step 13: Rewrite CLAUDE.md — ON STARTUP section
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Modify step 3 to be more emphatic about git pull

Change:
```
3. **Git pull (interactive mode only):** If `$SCHEDULED_RUN` is NOT set, run `git pull` to ensure `state.json` is current. Scheduled runs may have committed updates since the last interactive session. Git pull MUST happen before state load.
```
To:
```
3. **Git pull (interactive mode only — MANDATORY):** If `$SCHEDULED_RUN` is NOT set, execute `git pull` and verify it succeeds BEFORE any file reads. This ensures `state.json` and `context.md` are current. If git pull fails (merge conflict, network error), inform user and stop — do not proceed with stale data.
```

**Verify:**
```bash
grep "MANDATORY" 03_agents/tests/v16/CLAUDE.md | head -5
# Expected: includes git pull line
```

#### Step 14: Rewrite CLAUDE.md — ON STARTUP steps 7-8
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Modify — replace steps 7-8 in ON STARTUP with source-aware routing

Change:
```
7. **If Profile section is empty → begin Onboarding**
8. **If profile exists → quick change check:**
   - Show 3-line summary of stored profile
   - Ask: "Anything changed since [last run date]?"
   - If changes → update context.md
   - If no changes → proceed to search
```
To:
```
7. **If Profile section is empty → begin Onboarding**
8. **If profile exists → quick change check:**
   - Show 3-line summary of stored profile
   - Ask: "Anything changed since [last run date]?"
   - If changes → update context.md
   - If no changes → proceed to source research gate (see ORCHESTRATION WORKFLOW, Step 7)
```

**Verify:**
```bash
grep "source research gate" 03_agents/tests/v16/CLAUDE.md
# Expected: 1 match
```

#### Step 15: Rewrite CLAUDE.md — ORCHESTRATION WORKFLOW (full rewrite)
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Replace the entire ORCHESTRATION WORKFLOW section (from `## ORCHESTRATION WORKFLOW` to just before `## PRESENTATION WORKFLOW`)

**Builder note:** The content below between the outer code fence markers is the LITERAL content to paste into CLAUDE.md. The inner code fences (for bash commands, JSON examples, and the session-state.md template) are part of the CLAUDE.md content itself, not plan formatting.

The new section has 23 steps (was 20):
- Steps 1-6: unchanged
- Steps 7-8: NEW (source research gate + dispatch)
- Steps 9-23: renumbered from old 7-20, with fixes applied

New content:

```markdown
## ORCHESTRATION WORKFLOW

This is the core search-verify-present loop. All search and verification work is dispatched to subagents.

**23 steps:**

**Step 1: Capture run date.** Execute `date +%Y-%m-%d` once. Use this date for ALL filenames and records.

**Step 2: Git pull (interactive mode only).** See ON STARTUP step 3.

**Step 3: Load state.** Read `state.json` via `python3 scripts/manage_state.py` or directly.

**Step 4: Pre-run cleanup.** If `last_run_date` differs from today's run date, clean stale output (see ON STARTUP step 5).

**Step 5: Read context.md** for profile, skills, constraints, sources, target role types.

**Step 6: If onboarding needed,** dispatch onboarding subagent (see ONBOARDING section).

**Step 7: Source research gate.**
Check `context.md` for existing `## Sources` section with entries:
- If `## Sources` has entries AND user did NOT say "refresh sources" → skip to Step 9.
- If `## Sources` is empty or missing → run Step 8 (first run).
- If user explicitly said "refresh sources" → run Step 8 (manual refresh).

**Step 8: Source research + approval.**

8a. Dispatch source-researcher subagent:

Task tool call:
  prompt: '{"target_industries": [...], "target_roles": [...], "existing_sources": [...], "run_date": "..."}'
  description: "Research job sources"
  subagent_type: "source-researcher"

- `target_industries`: from context.md `## Industries`
- `target_roles`: from context.md `## Target`
- `existing_sources`: current entries from context.md `## Sources` table (may be empty array on first run)
- `run_date`: session run date

8b. Read `output/_source_research.json` from subagent output.

8c. Merge results: combine subagent's discovered sources with any existing sources in context.md. Deduplicate by URL.

8d. Present to user: categorized table of ALL sources (existing + newly discovered).

Format:
```
Here are the job sources I've found for your target industries:

**Industry-Specific Boards**
| Source | URL | Industries | Accessible |
|--------|-----|-----------|------------|
| Web3.Career | web3.career | Crypto | Yes |
| CryptocurrencyJobs | cryptocurrencyjobs.co | Crypto | Yes |

**Newsletter Job Boards**
| Source | URL | Industries | Accessible |
|--------|-----|-----------|------------|
| Early & Exec | earlyandexec.substack.com | Tech startups | Yes |

**Community Channels**
| Source | URL | Industries | Accessible |
|--------|-----|-----------|------------|
| CryptoDevHub Discord | discord.gg/xxx | Crypto | Manual check |

**Major Boards (via JobSpy)**
| Source | Industries |
|--------|-----------|
| LinkedIn | All |
| Indeed | All |
| Glassdoor | All |

Would you like to add, remove, or change any sources before I start searching?
```

8e. Wait for user response:
- If user approves → proceed
- If user adds sources → add to list
- If user removes sources → remove from list

8f. Write updated `## Sources` table to context.md with ALL approved sources. Use format:

```markdown
## Sources

| Source | URL | Method | Role Types | Category |
|--------|-----|--------|------------|----------|
| LinkedIn (via JobSpy) | https://linkedin.com/jobs | jobspy | Marketing Associate, Founder's Associate | major-board |
| Web3.Career | https://web3.career | webfetch | Marketing Associate, Founder's Associate | industry-specific |
| Early & Exec | https://earlyandexec.substack.com | webfetch | Founder's Associate | newsletter |
```

Note: The `Category` column is new in V16. Existing V15 sources that lack a category should be assigned one during migration.

**Step 9: Prepare 14 template variables per role type.**
For each role type, build the compact JSON blob:
```json
{"role_type": "...", "role_type_slug": "...", "skills": "...", "experience_years": "...",
 "seniority": "...", "target_industries": "...", "salary_min": "...", "location_prefs": "...",
 "country": "...", "remote_pref": "...", "sources_for_role": "...", "run_date": "...",
 "exclude_titles": "...", "industry_qualifiers": "..."}
```
- `industry_qualifiers` = keywords from `## Industries` (e.g., "crypto AI startup") — prevents off-industry results.
- `sources_for_role` = filtered from `## Sources` table — only sources whose `Role Types` column includes this role type.
  Note: The `sources_for_role` variable is passed to the search-verify agent template. Ensure the search-verify agent definition (`.claude/agents/search-verify.md`) and skill already reference this variable — if not, add a step to update them. (Pre-verified in Step 2b. If Step 2b found it missing, an additional step was added in Phase 4.)
- If remote preference is remote-only, add `--remote` to the `jobspy_search.py` command in the subagent template.

**Step 10: Dispatch search-verify agents in batches of 2-3.**

Task tool call:
  prompt: "{compact JSON blob with 14 variables}"
  description: "Search {role_type} jobs"
  subagent_type: "search-verify"

Launch subagents in sequential batches of 2-3 (to avoid rate limiting). Wait for each batch to complete before launching next. On failure, apply AUTO-RETRY PROTOCOL.

**Step 11: After each batch:** Read each subagent's `_status.json`. Collect role types with "complete" or "partial" status into `searched_role_types` list. **MANDATORY: Write `output/session-state.md` after every search batch completes.** Do not defer checkpointing to the end of all batches.

Map `_status.json` values:
- `"complete"` → verified
- `"partial"` → verified (add note: "incomplete verification")
- `"failed"` → not started (log for retry or note failure)
- Missing `_status.json` → failed (log the failure)

**Step 12: Read `_summary.md`** for each completed role type.

**Step 13: Cross-role-type deduplication (MANDATORY before presentation).**
- Scan all `output/verified/*/` directories (skip files starting with `_`)
- If same company+title filename exists in multiple role types, read ONLY those duplicate files to compare scores
- Keep highest-scoring copy, delete duplicates
- Log dedup actions in session-state.md

**Step 14: Update state** via `manage_state.py sync`:
```bash
python3 scripts/manage_state.py sync \
  --verified-dir output/verified \
  --run-date {run_date} \
  --searched-role-types {comma_separated_role_types} \
  --state state.json \
  --output output/_delta.json
```

**Step 15: Compute delta.** The `sync` command in step 14 returns the delta. Read `output/_delta.json` for `new_jobs`, `still_active`, `expired_count`, `rejected_count`.

**Step 16: Present results to user** — use PRESENTATION WORKFLOW (see below). Show "New Today" and "Still Active" subsections.

**Step 17: Collect user feedback.** Present jobs and ask which ones the user wants briefs for. Record `brief_requested` for selected jobs. Do NOT reject unselected jobs — leave their `user_action` as null.

If user explicitly says "reject" for specific jobs, record `rejected` for those only.

```bash
python3 scripts/manage_state.py record-action \
  --state state.json \
  --job-key "{key}" \
  --action "brief_requested"
```

Note: State is already persisted by `record-action` in Step 17 (each call invokes `save_state()` internally). No separate save step needed. Step 17 uses CLI subcommands only. Never write inline Python (`python3 -c`) that imports manage_state internals.

**Step 18: Dispatch brief agents in parallel** for `brief_requested` jobs, auto-retry once on failure.

If 3+ briefs are needed, dispatch all brief agents in a single message with multiple Task tool calls (parallel dispatch). If 1-2 briefs, sequential dispatch is fine.

Task tool call:
  prompt: '{"job_title": "...", "company": "...", "company_slug": "...", "title_slug": "...", "run_date": "...", "profile_extract": "...", "job_json_with_verification": "..."}'
  description: "Generate brief for {job_title} at {company}"
  subagent_type: "brief-generator"

After each brief subagent completes, verify `output/briefs/{company_slug}-{title_slug}-brief.md`:
- File must exist
- File's last non-whitespace line must be exactly `<!-- BRIEF COMPLETE -->`
- If sentinel is missing, treat as corrupt/truncated. Log failure, notify user.

**Step 19: Dispatch digest-email + briefs-html in parallel.**

digest-email (7 variables):
  prompt: '{"run_date": "...", "user_email": "...", "user_name": "...", "total_briefs": N, "new_today": [...], "still_active": [...], "verified_dir": "output/verified/"}'
  description: "Generate digest email HTML"
  subagent_type: "digest-email"

briefs-html (1 variable, only if briefs exist):
  prompt: '{"run_date": "..."}'
  description: "Compile briefs into HTML"
  subagent_type: "briefs-html"

Verify completion via `_status.json` files. If status file exists but cannot be parsed as valid JSON, treat as failed.

**Step 19b: Post-render verification (PARENT-ORCHESTRATED).**
After digest-email and briefs-html complete, parent reads generated HTML and checks:
1. Link colors are `#1c1917`, not `#2563eb`
2. Score badges use only green/stone, no amber/red
3. Zero-count sections are omitted
4. Brief score breakdowns have no gray boxes (no `background-color` on score tables)
If non-compliant: patch HTML directly or re-dispatch the failing subagent.

**Step 20: Send email (PARENT-ORCHESTRATED).**

Pre-send gate:
a. Check idempotency: Read `output/digests/_status.json`. If `sent_at` field exists AND `run_date` matches current session's `run_date`, SKIP — email already sent. Inform user: "Email already sent for today's run — skipping to avoid duplicate."
b. Three-way briefs-html check:
   - Step 19 succeeded: include attachment.
   - Step 19 failed: notify user and ask how to proceed.
   - Step 19 was never dispatched (zero briefs): proceed without attachment.
c. If digest failed → do NOT send.

```bash
python3 scripts/send_email.py \
  --to "{user_email}" \
  --subject "Job Search Update — {run_date}" \
  --body-file output/digests/{run_date}-email.html \
  --attachment output/briefs/briefs-{run_date}.html
```

If no briefs HTML: omit `--attachment` flag.
If RESEND_API_KEY not set: ask user for key with source URL: "I need a Resend API key to send your digest. Get one at resend.com/api-keys. What's your key?" Write to .env silently.

AFTER successful send: Update `output/digests/_status.json` with `sent_at` and `to` fields.

**CRITICAL:** The parent orchestrator sends email, NOT a subagent.

**Step 21: Final checkpoint — write complete run summary to `output/session-state.md`.**
```markdown
# Session State — {run_date}
## Run Summary
- Date: {run_date}
- Mode: interactive | scheduled
- Role types searched: {list}
- Sources used: {count} ({count} new from source research)
## Results
- New jobs found: {N}
- Still active: {N}
- Expired: {N}
- Rejected: {N}
- Briefs requested: {N}
## Actions Taken
- Briefs generated: {N}
- Email sent: yes/no
- Errors: {list or "none"}
```

**Step 22: Post-run scheduled run prompt (interactive mode only, first run only).**
If ALL of the following are true:
- `$SCHEDULED_RUN` is NOT set (interactive mode)
- `state.json` had no `last_run_date` before this session (first interactive run)
- Email was successfully sent in Step 20

Then ask: "Would you like to set up a daily scheduled run? I can configure GitHub Actions to run this automatically on weekday mornings."

If user says yes → proceed with scheduled run setup (see SCHEDULED RUNS section).
If user says no → end session.

**Step 23: API key piping for scheduled runs.**
When setting GitHub secrets for scheduled runs, pipe keys via stdin — never as CLI arguments:

```bash
echo "$RESEND_API_KEY" | gh secret set RESEND_API_KEY
echo "$ANTHROPIC_API_KEY" | gh secret set ANTHROPIC_API_KEY
```

Never use `gh secret set NAME --body "value"` — this exposes the key in command history and output.
```

**Verify:**
```bash
grep -c "^\\*\\*Step " 03_agents/tests/v16/CLAUDE.md
# Expected: 23 (or 24 counting Step 19b)
```

**Mid-phase structural check:**
```bash
# Verify CLAUDE.md section headings are intact after large rewrite
for section in "HARD CONSTRAINTS" "CORE RULES" "ON STARTUP" "ORCHESTRATION WORKFLOW" "PRESENTATION WORKFLOW"; do
  grep -q "## $section" 03_agents/tests/v16/CLAUDE.md && echo "OK: $section" || echo "MISSING: $section"
done
```

#### Step 16: Update CLAUDE.md — ONBOARDING section
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Modify step 11 in onboarding to remove source merging (now handled by source research phase)

Change:
```
11. Merge discovered sources from `_onboarding_draft.json` with user feedback → store in `## Sources`
```
To:
```
11. Store any sources discovered during CV parsing as initial entries in `## Sources`. Full source research happens in the source research phase (Step 8) after onboarding.
```

**Verify:**
```bash
grep "Full source research happens" 03_agents/tests/v16/CLAUDE.md
# Expected: 1 match
```

#### Step 17: Update CLAUDE.md — AUTO-RETRY PROTOCOL
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Add source-researcher to the agent types list

Change:
```
This applies to all subagent types: search-verify, brief-generator, digest-email, briefs-html, onboarding.
```
To:
```
This applies to all subagent types: source-researcher, search-verify, brief-generator, digest-email, briefs-html, onboarding.
```

**Verify:**
```bash
grep "source-researcher, search-verify" 03_agents/tests/v16/CLAUDE.md
# Expected: 1 match
```

#### Step 18: Update CLAUDE.md — SCHEDULED RUNS section
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Update step numbers and add source research skip

Change:
```
4. **Proceed directly:** Steps 1, 3-4, 5, 7-13, 18 (digest-email only, no briefs-html), 19, 20.
```
To:
```
4. **Proceed directly:** Steps 1, 3-5, 7 (gate check — skip Step 8), 9-15, 19 (digest-email only, no briefs-html), 20, 21.
(Scheduled runs skip Steps 6, 8, 16-18 because: no onboarding needed, source research already done, no user present for presentation/feedback.)
```

**Verify:**
```bash
grep "gate check" 03_agents/tests/v16/CLAUDE.md
# Expected: 1 match
```

#### Step 19: Update CLAUDE.md — SECURITY section
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Update API key onboarding to include source URLs

Change:
```
- **API key onboarding:** On first run, .env will NOT contain RESEND_API_KEY. When email is needed, check if set. If not, ask user: "I need a Resend API key to send your digest. Get one at resend.com/api-keys. What's your key?" Write to .env silently.
```
To:
```
- **API key onboarding:** On first run, .env will NOT contain RESEND_API_KEY. When email is needed, check if set. If not, ask user: "I need a Resend API key to send your digest. Get one at resend.com/api-keys — click 'Create API Key', name it anything, and paste the key here." Write to .env silently. For Anthropic API key: "Get one at console.anthropic.com/settings/keys." Always include the source URL in the same message as the request.
```

**Verify:**
```bash
grep "console.anthropic.com" 03_agents/tests/v16/CLAUDE.md
# Expected: 1 match
```

#### Step 20: Update CLAUDE.md — CAPABILITIES section
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Add source research capability

After line `- Digest generation: named digest-email agent (design system enforced)`, add:
```
- Source research: named `source-researcher` agent (deep industry source discovery with user approval)
```

**Verify:**
```bash
grep "source-researcher" 03_agents/tests/v16/CLAUDE.md
# Expected: at least 2 matches (capabilities + auto-retry)
```

#### Step 21: Update CLAUDE.md — OUTPUTS section
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Add source research output files

After `- Onboarding draft:` line, add:
```
- Source research: `output/_source_research.json` (discovered sources from source-researcher subagent)
- Source research status: `output/_source_research_status.json`
```

**Verify:**
```bash
grep "_source_research" 03_agents/tests/v16/CLAUDE.md
# Expected: 2 matches
```

#### Step 22: Verify inline Python removal (no implementation needed)
**File:** `03_agents/tests/v16/CLAUDE.md`
**Action:** Verify only — the inline Python block for recording actions was already removed in the Step 15 orchestration rewrite. No additional changes needed.

**Verify:**
```bash
grep "python3 -c" 03_agents/tests/v16/CLAUDE.md
# Expected: 0 matches (no inline Python for state mutations)
```

#### Step 23: Commit Phase 4
```bash
git add 03_agents/tests/v16/CLAUDE.md
git commit -m "feat(jsa): rewrite V16 orchestrator — source research phase + 7 fixes"
```

---

### Phase 5: Add CLI Subcommand to manage_state.py (Fix #2 continuation — CLI-only state mutations)

The CLAUDE.md now references `manage_state.py record-action` CLI subcommand that doesn't exist yet in V15. We need to add it.

#### Step 24: Write failing test for `record-action` CLI
**File:** `03_agents/tests/v16/tests/test_manage_state.py`
**Action:** Append new test class

```python
class TestRecordActionCLI:
    """Tests for record-action CLI subcommand."""

    def test_record_action_cli(self, empty_state, verified_dir, tmp_path):
        """CLI record-action writes updated state with action recorded."""
        import subprocess

        from manage_state import save_state, update_state

        job = make_verified_json(title="Growth Lead", company="Acme Corp", score=85)
        (verified_dir / "community-manager" / "acme-corp-growth-lead.json").write_text(
            json.dumps(job), encoding="utf-8"
        )
        state = update_state(empty_state, verified_dir, "2026-02-09", ["community-manager"])
        state_path = tmp_path / "state.json"
        save_state(state, state_path)

        scripts_dir = Path(__file__).resolve().parent.parent / "scripts"

        result = subprocess.run(
            [
                sys.executable, str(scripts_dir / "manage_state.py"),
                "record-action",
                "--state", str(state_path),
                "--job-key", "community-manager/acme-corp-growth-lead",
                "--action", "brief_requested",
            ],
            capture_output=True, text=True,
            cwd=scripts_dir.parent,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        with open(state_path, encoding="utf-8") as f:
            updated = json.load(f)
        assert updated["jobs"]["community-manager/acme-corp-growth-lead"]["user_action"] == "brief_requested"
```

**Verify:**
```bash
cd 03_agents/tests/v16 && python3 -m pytest tests/test_manage_state.py::TestRecordActionCLI -v 2>&1 | tail -10
# Expected: 1 FAILED (record-action subcommand doesn't exist)
```

#### Step 25: Implement `record-action` CLI subcommand
**File:** `03_agents/tests/v16/scripts/manage_state.py`
**Action:** Add `_cli_record_action` function and register subcommand

Add after `_cli_sync` function (before `main()`):

```python
def _cli_record_action(args: argparse.Namespace) -> None:
    """CLI record-action subcommand: record a user action on a job."""
    state_path = Path(args.state)
    state = load_state(state_path)
    # record_action() validates args.action against VALID_ACTIONS internally —
    # raises ValueError for invalid actions, so no CLI-level validation needed.
    state = record_action(state, args.job_key, args.action)
    save_state(state, state_path)
```

In `main()`, after the `sync_parser` block, add:

```python
    action_parser = subparsers.add_parser("record-action", help="Record user action on a job")
    action_parser.add_argument("--state", default="state.json")
    action_parser.add_argument("--job-key", required=True, dest="job_key")
    action_parser.add_argument("--action", required=True)
    action_parser.set_defaults(func=_cli_record_action)
```

**Verify:**
```bash
cd 03_agents/tests/v16 && python3 -m pytest tests/test_manage_state.py::TestRecordActionCLI -v 2>&1 | tail -10
# Expected: 1 PASSED
```

#### Step 26: Run full test suite
**Verify:**
```bash
cd 03_agents/tests/v16 && python3 -m pytest tests/ -v 2>&1 | tail -20
# Expected: all 18 tests PASSED (14 existing + 3 brief_requested + 1 CLI)
```

#### Step 27: Commit Phase 5
```bash
git add 03_agents/tests/v16/scripts/manage_state.py 03_agents/tests/v16/tests/test_manage_state.py
git commit -m "feat(jsa): add record-action CLI subcommand to manage_state.py"
```

---

### Phase 6: Update context.md Schema + Remaining Files

#### Step 28: Add Category column to context.md Sources table
**File:** `03_agents/tests/v16/context.md`
**Action:** Modify — add `Category` column to Sources table

Change:
```markdown
## Sources

| Source | URL | Method | Role Types |
|--------|-----|--------|------------|
| LinkedIn (via JobSpy) | https://linkedin.com/jobs | jobspy | Marketing Associate, Founder's Associate |
| Indeed (via JobSpy) | https://indeed.com | jobspy | Marketing Associate, Founder's Associate |
| Glassdoor (via JobSpy) | https://glassdoor.com | jobspy | Marketing Associate, Founder's Associate |
| Web3.Career | https://web3.career | webfetch | Marketing Associate, Founder's Associate |
| CryptocurrencyJobs | https://cryptocurrencyjobs.co | webfetch | Marketing Associate, Founder's Associate |
| Nodesk | https://nodesk.co/remote-jobs/marketing/ | webfetch | Marketing Associate, Founder's Associate |
```
To:
```markdown
## Sources

| Source | URL | Method | Role Types | Category |
|--------|-----|--------|------------|----------|
| LinkedIn (via JobSpy) | https://linkedin.com/jobs | jobspy | Marketing Associate, Founder's Associate | major-board |
| Indeed (via JobSpy) | https://indeed.com | jobspy | Marketing Associate, Founder's Associate | major-board |
| Glassdoor (via JobSpy) | https://glassdoor.com | jobspy | Marketing Associate, Founder's Associate | major-board |
| Web3.Career | https://web3.career | webfetch | Marketing Associate, Founder's Associate | industry-specific |
| CryptocurrencyJobs | https://cryptocurrencyjobs.co | webfetch | Marketing Associate, Founder's Associate | industry-specific |
| Nodesk | https://nodesk.co/remote-jobs/marketing/ | webfetch | Marketing Associate, Founder's Associate | industry-specific |
```

**Verify:**
```bash
grep "Category" 03_agents/tests/v16/context.md
# Expected: 1 match (table header)
```

#### Step 29: Create output directory for source research
**Action:** Ensure .gitkeep exists for source research output

The source research outputs go to `output/_source_research.json` and `output/_source_research_status.json` — these are in the existing `output/` directory, so no new directory needed. The existing `.gitignore` should handle these.

**Verify:**
```bash
cat 03_agents/tests/v16/.gitignore | grep -c "output/"
# Expected: references to output directory in gitignore
```

#### Step 30: Update .github/workflows/daily-digest.yml
**File:** `03_agents/tests/v16/.github/workflows/daily-digest.yml`
**Action:** No changes needed — the scheduled run skips source research (Step 7 gate check), and the workflow file paths don't reference step numbers. The `working-directory` references `03_agents/tests/v15` and needs updating.

Change:
```yaml
        working-directory: 03_agents/tests/v15
```
To (all 4 occurrences):
```yaml
        working-directory: 03_agents/tests/v16
```

Also update the allowlist check path if it references v15:
```yaml
          python3 -c "import json; c=json.load(open('.claude/settings.local.json')); perms=c.get('permissions',{}).get('allow',[]); assert len(perms) >= 10, f'Expected >=10 permissions, got {len(perms)}'"
```
No change needed — relative path.

**Verify:**
```bash
grep -c "v15" 03_agents/tests/v16/.github/workflows/daily-digest.yml
# Expected: 0
grep -c "v16" 03_agents/tests/v16/.github/workflows/daily-digest.yml
# Expected: 4 (one per working-directory)
```

#### Step 31: Clean output files from V15 copy
**Action:** Remove V15-specific output data that shouldn't carry over

```bash
rm -f 03_agents/tests/v16/output/jobs/*
rm -f 03_agents/tests/v16/output/verified/*/*
rm -f 03_agents/tests/v16/output/briefs/*
rm -f 03_agents/tests/v16/output/digests/*
rm -f 03_agents/tests/v16/output/_delta.json
rm -f 03_agents/tests/v16/output/_onboarding_draft.json
rm -f 03_agents/tests/v16/output/session-state.md
rm -f 03_agents/tests/v16/state.json
```

Preserve `.gitkeep` files in output subdirectories.

**Verify:**
```bash
find 03_agents/tests/v16/output -type f ! -name ".gitkeep" | head -5
# Expected: 0 files (only .gitkeep remains)
```

#### Step 32: Reset Search Progress in context.md
**File:** `03_agents/tests/v16/context.md`
**Action:** Search Progress table should already show "not started" (it does in V15). No change needed.

**Verify:**
```bash
grep "not started" 03_agents/tests/v16/context.md
# Expected: 2 matches (one per role type)
```

#### Step 33: Commit Phase 6
```bash
git add 03_agents/tests/v16/context.md \
       03_agents/tests/v16/.github/workflows/daily-digest.yml \
       03_agents/tests/v16/output/
git commit -m "feat(jsa): update context.md schema, workflow paths, clean output for V16"
```

---

### Phase 7: Final Verification

#### Step 34: Run full test suite
```bash
cd 03_agents/tests/v16 && python3 -m pytest tests/ -v
```
**Expected:** All 18 tests pass.

#### Step 35: Verify no V15 references remain in V16
```bash
grep -r "v15" 03_agents/tests/v16/ --include="*.md" --include="*.py" --include="*.yml" --include="*.json" | grep -v __pycache__ | grep -v ".pytest_cache" | grep -v "node_modules"
```
**Expected:** 0 matches (all references updated to v16).

#### Step 36: Verify CLAUDE.md structural integrity
```bash
# Check all required sections exist
for section in "HARD CONSTRAINTS" "CORE RULES" "ON STARTUP" "ONBOARDING" "CONSTRAINT DERIVATION" "AUTO-RETRY PROTOCOL" "ORCHESTRATION WORKFLOW" "PRESENTATION WORKFLOW" "UX RULES" "SESSION MANAGEMENT" "SCHEDULED RUNS" "SECURITY" "CAPABILITIES" "OUTPUTS"; do
  grep -q "## $section" 03_agents/tests/v16/CLAUDE.md && echo "OK: $section" || echo "MISSING: $section"
done
```
**Expected:** All sections OK.

#### Step 37: Verify all 7 fixes are present
```bash
# Fix 1: brief_requested action
grep "brief_requested" 03_agents/tests/v16/scripts/manage_state.py && echo "Fix 1: OK"

# Fix 2: No inline Python constraint
grep "Never write inline Python" 03_agents/tests/v16/CLAUDE.md && echo "Fix 2: OK"

# Fix 3: Git pull enforcement
grep "MANDATORY" 03_agents/tests/v16/CLAUDE.md | grep -i "git pull" && echo "Fix 3: OK"

# Fix 4: Email idempotency
grep "idempotency" 03_agents/tests/v16/CLAUDE.md && echo "Fix 4: OK"

# Fix 5: API key stdin
grep "stdin" 03_agents/tests/v16/CLAUDE.md || grep "echo.*gh secret set" 03_agents/tests/v16/CLAUDE.md && echo "Fix 5: OK"

# Fix 6: Post-run scheduled prompt
grep "scheduled run prompt" 03_agents/tests/v16/CLAUDE.md && echo "Fix 6: OK"

# Fix 7: API key source URLs
grep "console.anthropic.com" 03_agents/tests/v16/CLAUDE.md && echo "Fix 7: OK"
```
**Expected:** All 7 fixes OK.

#### Step 38: Commit final verification (if any fixes needed)
Only if Steps 34-37 revealed issues that were fixed.

```bash
git add 03_agents/tests/v16/
git commit -m "fix(jsa): V16 final verification fixes"
```

---

## Handoff Contract
- Total steps: 38, Total phases: 7
- Files created:
  - `03_agents/tests/v16/` (full directory, copied from v15)
  - `03_agents/tests/v16/.claude/agents/source-researcher.md`
  - `03_agents/tests/v16/.claude/skills/jsa-source-researcher.md`
  - `03_agents/tests/v16/.claude/agent-memory/source-researcher/MEMORY.md`
- Files modified:
  - `03_agents/tests/v16/CLAUDE.md` (orchestrator rewrite)
  - `03_agents/tests/v16/scripts/manage_state.py` (brief_requested + record-action CLI)
  - `03_agents/tests/v16/tests/test_manage_state.py` (4 new tests)
  - `03_agents/tests/v16/context.md` (Category column)
  - `03_agents/tests/v16/.github/workflows/daily-digest.yml` (v15→v16 paths)
  - `03_agents/tests/v16/.claude/agents/*.md` (v15→v16 path references)
  - `03_agents/tests/v16/.claude/skills/*.md` (v15→v16 path references)
- Verification sequence:
  1. `python3 -m pytest tests/ -v` — all 18 tests pass
  2. `grep -r "v15" ... | wc -l` — 0 stale references
  3. Section headings check — all 14 CLAUDE.md sections present
  4. 7-fix check — all fixes verified by grep

<!-- STAGE COMPLETE: /plan, 2026-02-11 -->
<!-- STAGE COMPLETE: /revise after round 1, 2026-02-11 -->
<!-- STAGE COMPLETE: /revise after round 2, 2026-02-11 -->

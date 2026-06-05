# JSA V14 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade JSA from V13 to V14 — distinctive design system, skills-based architecture (replacing reference templates), 1 new subagent (onboarding), daily delta state management, mobile-responsive email, continuous-page PDF, orchestrator hardening, and GitHub Actions scheduling.

**Architecture:** 5 named subagents (up from 4) with all instructions via skills instead of reference templates. State persists across runs via `state.json`. Scheduled daily runs via GitHub Actions at 8am UK weekdays.

**Tech Stack:** Python 3, Playwright + Chromium, Resend API, Claude Code named agents + skills

**Prerequisites:**
- Task 1.4 (Design System Upgrade) is a **HUMAN STEP** — requires manual invocation of the `frontend-design` skill. All subsequent phases depend on it.

---

## PHASE 1: Baseline Setup (Copy V13, Design System, Skills Migration)

### Task 1.1: Copy V13 directory to V14

```bash
cp -r 03_agents/tests/v13 03_agents/tests/v14
```

### Task 1.2: Update all v13 path references to v14

**Files to modify (replace all `v13` → `v14`):**
- `03_agents/tests/v14/.claude/agents/search-verify.md`
- `03_agents/tests/v14/.claude/agents/brief-generator.md`
- `03_agents/tests/v14/.claude/agents/digest-email.md`
- `03_agents/tests/v14/.claude/agents/briefs-pdf.md`

Note: `CLAUDE.md` paths are updated in Phase 6 (Task 6.1), not here — CLAUDE.md gets a major rewrite in that phase.

Note: `references/subagent-*.md` files are deleted in Task 1.7 — do not update paths in files that will be removed.

**Verify:**
```bash
grep -r "v13" 03_agents/tests/v14/ --include="*.md" --include="*.py" --include="*.json" | grep -v ".git" | grep -v "output/" | grep -v "CLAUDE.md"
# Expected: zero matches (CLAUDE.md excluded — updated in Phase 6)
```

### Task 1.3: Clean output directory

```bash
find 03_agents/tests/v14/output -mindepth 1 -not -name '.gitkeep' -delete
rm -f 03_agents/tests/v14/*.png
rm -rf 03_agents/tests/v14/.playwright-mcp
mkdir -p 03_agents/tests/v14/output/{jobs,verified,briefs,digests}
touch 03_agents/tests/v14/output/{jobs,verified,briefs,digests}/.gitkeep
```

**Commit:** `chore(jsa-v14): copy v13 baseline and update paths`

### Task 1.4: Invoke frontend-design skill → rewrite jsa-design-system.md

**HUMAN STEP.** Invoke the `frontend-design` skill with this brief:
- **Context:** Job search agent producing email digests and PDF briefs
- **Aesthetic:** Internal strategy document — clean, professional, cohesive. NOT marketing/dashboard/newsletter.
- **Outputs:** Email HTML (600px, inline styles, table layout) + PDF HTML (800px, Playwright rendering)
- **Constraints:** Google Fonts (NOT system fonts). Score accents (green 90+, default 80-89, amber 70-79, red below salary min). Complete CSS blocks for both email and PDF.

**File:** `03_agents/tests/v14/.claude/skills/jsa-design-system.md`

Keep YAML frontmatter:
```yaml
---
name: jsa-design-system
description: Unified design system for all JSA visual outputs (email HTML, PDF HTML)
---
```

Body must include: font import URLs, typography scale, full color palette, score accents, layout specs, email CSS block, PDF CSS block, rendering rule (Playwright + Chromium ONLY).

**Verify:**
```bash
grep -i "import\|google.*font\|fonts.googleapis" 03_agents/tests/v14/.claude/skills/jsa-design-system.md
# Expected: at least one match
```

**Commit:** `feat(jsa-v14): upgrade design system with distinctive fonts and palette`

**GATE:** Task 1.4 (design system) must be complete before proceeding. Verify `jsa-design-system.md` contains font imports and complete CSS blocks.

**Convention:** All JSA skills use the `jsa-` prefix to namespace them from other project skills.

### Task 1.5: Migrate reference templates to skills

For `search-verify` and `brief-generator`, copy content from reference template and prepend YAML frontmatter:

| Source | Destination | Skill Name |
|--------|-------------|------------|
| `references/subagent-search-verify.md` | `.claude/skills/jsa-search-verify.md` | `jsa-search-verify` |
| `references/subagent-brief-generator.md` | `.claude/skills/jsa-brief-generator.md` | `jsa-brief-generator` |

For `digest-email` and `briefs-pdf`, create placeholder skills (frontmatter only) — these are completely rewritten in Phase 5 (Tasks 5.1, 5.4). Creating full copies from V13 references only to overwrite them is wasted work.

| Destination | Skill Name | Content |
|-------------|------------|---------|
| `.claude/skills/jsa-digest-email.md` | `jsa-digest-email` | Placeholder — complete rewrite in Phase 5, Task 5.1 |
| `.claude/skills/jsa-briefs-pdf.md` | `jsa-briefs-pdf` | Placeholder — complete rewrite in Phase 5, Task 5.4 |

Each skill file gets this frontmatter:
```yaml
---
name: jsa-{name}
description: Complete instructions for the {name} subagent
---
```

### Task 1.6: Update all 4 agent definitions

For each agent, apply these changes:

**search-verify.md:**
```yaml
---
name: search-verify
description: Search job sources, verify active listings, score against user profile
tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
disallowedTools: NotebookEdit
skills: jsa-search-verify
memory: project
model: inherit
---

You are a search-verify subagent for the Job Search Agent.

Parse the compact JSON blob provided in the task prompt for your 13 template variables. Confirm all 13 are present before proceeding.

**If any variable is missing or null:** Write `output/verified/{role_type_slug}/_status.json` with `"status": "failed", "error": "Missing variable: {name}"` and exit immediately.

**Working directory:** All paths are relative to `03_agents/tests/v14/`.

**First action:** `cd 03_agents/tests/v14/`
```

**brief-generator.md:**
```yaml
---
name: brief-generator
description: Generate application brief for a single job match
tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
disallowedTools: NotebookEdit
skills: jsa-brief-generator
memory: project
model: inherit
---

You are a brief-generator subagent for the Job Search Agent.

Parse the compact JSON blob provided in the task prompt for your 7 template variables. Confirm all 7 are present before proceeding.

**If any variable is missing or null:** Do NOT write any output files. Exit immediately.

**Working directory:** All paths are relative to `03_agents/tests/v14/`.

**First action:** `cd 03_agents/tests/v14/`
```

**digest-email.md:**
```yaml
---
name: digest-email
description: Generate email digest HTML from verified job data
tools: Bash, Read, Write, Glob, Grep
disallowedTools: WebFetch, WebSearch, NotebookEdit
skills: jsa-design-system, jsa-digest-email
memory: project
model: inherit
---

You are a digest-email subagent for the Job Search Agent.

**CRITICAL:** You have `jsa-design-system` and `jsa-digest-email` skills preloaded. Follow the design system exactly. Do not modify or improvise styling.

Parse the compact JSON blob provided in the task prompt for your 7 template variables. Confirm all 7 are present before proceeding.

**If any variable is missing or null:** Write `output/digests/_status.json` with `"status": "failed", "error": "Missing variable: {name}"` and exit immediately.

**Data access:** Does NOT read `state.json`. Reads verified JSON files from `output/verified/` for full job rendering data (score_breakdown, gaps, notes, etc.). Uses delta-classified lists (`new_today`, `still_active`) only for new/still-active classification.

**Note:** This agent definition is written with 7 variables from the start. The jsa-digest-email skill is a placeholder until Phase 5 (Task 5.1) — digest-email is non-functional until Phase 5 is complete.

**Working directory:** All paths are relative to `03_agents/tests/v14/`.

**First action:** `cd 03_agents/tests/v14/`
```

**briefs-pdf.md:**
```yaml
---
name: briefs-pdf
description: Compile application briefs into a single styled PDF
tools: Bash, Read, Write, Glob, Grep
disallowedTools: WebFetch, WebSearch, NotebookEdit
skills: jsa-design-system, jsa-briefs-pdf
memory: project
model: inherit
---

You are a briefs-pdf subagent for the Job Search Agent.

**CRITICAL:** You have `jsa-design-system` and `jsa-briefs-pdf` skills preloaded. Follow the design system exactly. Do not modify or improvise styling.

Parse the compact JSON blob provided in the task prompt for your 1 template variable. Confirm it is present before proceeding.

**If the variable is missing or null:** Write `output/briefs/_status.json` with `"status": "failed", "error": "Missing variable: run_date"` and exit immediately.

**Working directory:** All paths are relative to `03_agents/tests/v14/`.

**First action:** `cd 03_agents/tests/v14/`
```

Key changes across all 4:
1. Remove `Skill` from `disallowedTools` (was on search-verify and brief-generator)
2. Add `skills:` frontmatter with appropriate skill names
3. Remove "Read your full instructions from `references/...`" body text
4. Paths updated from v13 to v14

Note: `digest-email` and `briefs-pdf` produce visual output and therefore need both the design system skill (`jsa-design-system`) and their instruction skill. The design system CSS is accessed via the preloaded skill, not embedded as a copy.

**Verify:**
```bash
grep -c "skills:" 03_agents/tests/v14/.claude/agents/*.md
# Expected: 4 lines, each showing 1

grep "disallowedTools:.*Skill" 03_agents/tests/v14/.claude/agents/*.md
# Expected: zero matches

grep "Read your full instructions" 03_agents/tests/v14/.claude/agents/*.md
# Expected: zero matches
```

### Task 1.7: Delete reference template files

```bash
rm 03_agents/tests/v14/references/subagent-*.md
```

Keep `references/algorithms.md` (reference data, not agent instructions).

**`context.md` location:** V13 stores `context.md` at the project root (`03_agents/tests/v13/context.md`). V14 keeps this convention — `context.md` remains at the project root (`03_agents/tests/v14/context.md`). The onboarding agent (Task 2.1) writes to `context.md` (root), not `references/context.md`. The `references/` directory is for static reference data only (`algorithms.md`).

**Verify:**
```bash
ls 03_agents/tests/v14/references/subagent-*.md 2>/dev/null  # no such file
ls 03_agents/tests/v14/references/algorithms.md              # exists
```

**Commit:** `refactor(jsa-v14): migrate reference templates to skills, update agent definitions`

---

## PHASE 2: Onboarding Subagent

### Task 2.1: Create onboarding agent + skill + memory

**Note:** The onboarding subagent exists for context window management — CV text is large and should not pollute the parent orchestrator's context.

**Create:** `03_agents/tests/v14/.claude/agents/onboarding.md`
```yaml
---
name: onboarding
description: Parse CV, extract user profile data, and discover job sources for target industries
tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
disallowedTools: NotebookEdit
skills: jsa-onboarding
memory: project
model: inherit
---

You are an onboarding subagent for the Job Search Agent.

Your job is to parse a CV, extract structured profile data, and discover relevant job sources. You do NOT conduct the interactive Q&A — the parent handles that. Writes draft output to `output/_onboarding_draft.json` (structured profile data + discovered sources). The parent reads this draft, presents to user for correction, and writes the final `context.md`.

**`_onboarding_draft.json` schema:**
```json
{"profile": {"contact": {...}, "summary": "...", "experience": [...], "education": [...], "skills": [...], "total_years": N, "seniority": "...", "industries": [...]}, "discovered_sources": [{"name": "...", "url": "...", "role_types": [...], "accessible": true}], "status": "complete"}
```

Parse the compact JSON blob provided in the task prompt for your 5 template variables (`cv_path`, `existing_context_path`, `run_date`, `target_industries`, `target_roles`). Confirm all 5 are present before proceeding.

**Note:** On first run, `target_industries` and `target_roles` are `null` — the onboarding agent infers them from the CV. On re-onboarding, the parent passes known values from `context.md`. `cv_path` is the path to the CV file — the onboarding agent reads the file itself. This avoids JSON escaping issues with large free-form text (same pattern as `existing_context_path`). `existing_context_path` is the path to `context.md` (e.g., `context.md`) if it exists, or `null` on first run. The onboarding agent reads this file itself — passing file paths instead of inline text avoids JSON escaping issues with large free-form markdown.

**If any variable is missing (not provided at all):** Write `output/_onboarding_status.json` with `"status": "failed", "error": "Missing variable: {name}"` and exit immediately. Note: `null` is a valid value for `target_industries` and `target_roles` (see above).

**Working directory:** All paths are relative to `03_agents/tests/v14/`.

**First action:** `cd 03_agents/tests/v14/`
```

**Create:** `03_agents/tests/v14/.claude/skills/jsa-onboarding.md`

Skill contains: CV parsing workflow, extraction steps (contact, summary, experience, education, skills), derived fields (total_years, seniority, industries), source discovery workflow (identify candidates via WebSearch, verify accessibility via WebFetch, map to role types), context.md writing format, status file spec. References `algorithms.md` for CV Parsing rules, Skill Extraction Patterns, Experience Level Mapping. Known source reliability from V13 learnings. Skill must define the mapping from `_onboarding_draft.json` fields to `context.md` sections (e.g., `profile.skills` -> `## Skills`, `profile.experience` -> `## Experience`, `discovered_sources` -> `## Sources`).

**Create:** `03_agents/tests/v14/.claude/agent-memory/onboarding/MEMORY.md`
```markdown
# Onboarding Agent Memory

## Key Patterns
- CV formats vary widely; LinkedIn exports have a specific structure
- Use algorithms.md CV Parsing rules for extraction
- Skill Extraction Patterns: comma-separated, bullet points, parenthetical, version numbers
- Many specialty boards block WebFetch (403/404): CryptoJobsList, Wellfound, startup.jobs
- Best results from: Web3.Career, CryptocurrencyJobs, BeInCrypto Jobs, AI Jobs
- WebSearch more reliable than WebFetch in subagent context
```

**All agents follow the same failure pattern:** write `_status.json` (or `{subdir}/_status.json`) with `{"status": "failed", "error": "..."}`. The orchestrator checks these files for failure detection and auto-retry.

**Pattern:** All agent definitions follow this structure: YAML frontmatter (name, description, tools, disallowedTools, skills, memory, model) -> role description -> JSON parsing instruction -> failure handling -> working directory -> first action.

**Verify:**
```bash
ls 03_agents/tests/v14/.claude/agents/*.md | wc -l        # Expected: 5
ls 03_agents/tests/v14/.claude/skills/jsa-*.md | wc -l     # Expected: 6
ls 03_agents/tests/v14/.claude/agent-memory/*/MEMORY.md | wc -l  # Expected: 5
```

**Commit:** `feat(jsa-v14): add onboarding subagent with CV parsing and source discovery`

---

## PHASE 3: Fix V13 Failures (search-verify upgrades)

### Task 3.1: Add cross-reference verification, industry qualifiers, _summary.md to search-verify skill

**Modify:** `03_agents/tests/v14/.claude/skills/jsa-search-verify.md`

Three additions:

**1. Industry-qualified queries:** Modify search command to include `{industry_qualifiers}`:
```
python3 scripts/jobspy_search.py "{role_type} {industry_qualifiers}" --location ...
```
Add note: industry qualifiers (e.g., "crypto AI startup") prevent off-industry results.

**2. Cross-reference verification (new Step 1b):**
```markdown
### Step 1b: CROSS-REFERENCE (LinkedIn/unverifiable listings)

If Step 1 could not confirm active status via WebFetch:
1. WebSearch: `"{company}" "{exact job title}" site:careers OR site:lever.co OR site:greenhouse.io`
2. If found on company careers page or ATS: confirm active, use that URL
3. If found on another board: confirm active via that board
4. If no cross-reference: mark `"active_status": "unverified"`
```

**3. Summary output (new section):**
```markdown
## Summary Output

After writing `_status.json`, also write `output/verified/{role_type_slug}/_summary.md`:

| Score | Title | Company | Location | Status |
|-------|-------|---------|----------|--------|
...

**Searched:** N | **Verified:** N | **Above 70:** N
```

### Task 3.2: Update search-verify agent definition for 14 variables

**Modify:** `03_agents/tests/v14/.claude/agents/search-verify.md`

Change `13 template variables` → `14 template variables`.

### Task 3.3: Update search-verify agent memory

**Modify:** `03_agents/tests/v14/.claude/agent-memory/search-verify/MEMORY.md`

Normalize heading to `# Search-Verify Agent Memory` with `## Key Patterns` section. Add cross-reference verification patterns, industry-qualified query benefits, `_summary.md` format.

**Verify:**
```bash
grep "industry_qualifiers" 03_agents/tests/v14/.claude/skills/jsa-search-verify.md  # match
grep "CROSS-REFERENCE" 03_agents/tests/v14/.claude/skills/jsa-search-verify.md      # match
grep "_summary.md" 03_agents/tests/v14/.claude/skills/jsa-search-verify.md           # match
grep "14 template" 03_agents/tests/v14/.claude/agents/search-verify.md               # match
```

**Commit:** `fix(jsa-v14): add cross-reference verification, industry qualifiers, summary output`

---

## PHASE 4: Daily Delta + State Management (TDD)

### Task 4.1: Write failing tests

**Create:** `03_agents/tests/v14/tests/test_manage_state.py`

14 tests:
1. `test_empty_state_initialization` — empty State gets populated on first update_state() call
2. `test_returning_jobs_identified` — jobs seen in both runs have updated `last_seen`
3. `test_14_day_expiry` — jobs not seen for 14+ days move to `expired_jobs` dict
4. `test_new_job_identification` — new jobs appear in compute_delta() `new_jobs` array
5. `test_user_action_preserved` — `user_action` string survives update_state() calls
6. `test_score_update_on_rescan` — score updates when returning job has different score
7. `test_key_derived_from_filename` — given verified JSON at `verified_dir/community-manager/acme-corp-growth-lead.json`, the resulting key should be `community-manager/acme-corp-growth-lead` (note: diverges from design doc's flat key format; plan's namespaced format is canonical). Key uniqueness is guaranteed by the directory structure — one file per company-title per role type, namespaced by `{role_type_slug}/`.
8. `test_expiry_scoped_to_searched_role_types` — given jobs in two role types (`community-manager` and `devrel`), when only `community-manager` is in `searched_role_types` with "complete" status, only `community-manager`'s old jobs expire; `devrel` jobs remain untouched
9. `test_expired_job_reappears` — expired job reappears: moved back to jobs, first_seen preserved, last_seen updated, `user_action` set to `None`, `reappeared` field set to `True`, delta includes reappeared flag. (5 assertions)
10. `test_reappeared_flag_resets_on_next_run` — call `update_state` with a job that was reappeared on a previous run (already in `state.jobs` with `reappeared=True`), verify `reappeared` is reset to `False`. (2 assertions)
11. `test_compute_delta_excludes_rejected` — verify that `compute_delta`'s `still_active` list excludes jobs where `user_action == "rejected"`. Set up state with 3 jobs: one accepted, one rejected, one with no action. Verify `still_active` contains only the accepted and no-action jobs.
12. `test_record_action_invalid_value` — record_action with invalid action string (not "accepted"/"rejected") raises ValueError
13. `test_record_action_invalid_key` — record_action with a job_key not present in state.jobs raises KeyError
14. `test_load_state_missing_file` — load_state on a non-existent path returns empty `State(last_run_date=None, jobs={}, expired_jobs={})` without raising an error

**Create:** `03_agents/tests/v14/tests/fixtures/verified-job-template.json` — a static copy of a real V13 verified JSON file (e.g., `03_agents/tests/v13/output/verified/founders-associate/duku-ai-founder-associate.json`). This isolates test fixtures from V13 output files — if V13 output is cleaned, tests are unaffected.

**Create:** `03_agents/tests/v14/tests/conftest.py` with factory functions:
- `make_verified_json(title, company, score, role_type, ...)` — represents what `search-verify` writes to disk (V13 shape — does NOT include `reappeared` or `expired_date`, which are added by `manage_state.py`). Loads `tests/fixtures/verified-job-template.json` as the template for default values. The factory copies this fixture and overrides only the fields specified by the caller. This ensures the test fixture matches the actual verified JSON schema without maintaining a separate field list. Used for writing fixture files to `verified_dir` in tests. Tests write these fixtures to disk via `make_verified_json`, then let `update_state` extract `JobEntry` fields naturally — no separate `make_verified_job` factory needed.
- `verified_dir` fixture using `tmp_path` — creates `tmp_path / "community-manager"` and `tmp_path / "devrel"` as default subdirectories, matching the role types used in tests 7, 8, and 9. Does NOT include `_status.json` files — `manage_state.py` does not read `_status.json` (caller's responsibility to filter `searched_role_types`).
- `empty_state` fixture returning fresh `State()` instance

**Note:** `tests/__init__.py` should exist from the V13 copy (Task 1.1). Create it idempotently (`touch tests/__init__.py`) before writing tests — simpler than checking existence.

**Import path:** `scripts/` is not a Python package (no `__init__.py`). In `conftest.py`, add `sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))` to enable `import manage_state` in tests. **Working directory requirement:** `conftest.py` uses `Path(__file__).resolve()` for the sys.path insert, so pytest can be invoked from any directory — but the canonical invocation is `cd 03_agents/tests/v14 && python3 -m pytest tests/ -v`.

**Verify:**
```bash
cd 03_agents/tests/v14 && python3 -m pytest tests/test_manage_state.py -v 2>&1 | head -5
# Expected: ERRORS (script doesn't exist yet, 14 tests)
```

### Task 4.2: Implement manage_state.py

**Create:** `03_agents/tests/v14/scripts/manage_state.py`

**Architecture:** Python library with typed dataclasses and a thin CLI wrapper.

**Dataclasses:**
- `JobEntry`: title, company, score (int), role_type, source, first_seen, last_seen, active_status, job_url, location, requirements_met (list[str]), user_action (str | None -- "accepted", "rejected", or None), expired_date (str | None = None), reappeared (bool = False)
- `State`: last_run_date (str | None), jobs (dict[str, JobEntry]), expired_jobs (dict[str, JobEntry])

**Note:** `manage_state.py` extracts only the fields listed above from verified JSONs. Fields like `score_breakdown`, `gaps`, and `notes` remain in the verified JSON files and are read directly by email/PDF generation agents — they are not stored in state.

**Library functions (public API):**
- `load_state(path: Path) -> State` -- If the state file does not exist, returns an empty `State(last_run_date=None, jobs={}, expired_jobs={})` for silent first-run initialization.
- `save_state(state: State, path: Path) -> None` -- atomic write using `tempfile.NamedTemporaryFile(dir=path.parent, delete=False, mode='w', suffix='.json', encoding='utf-8')`, serialize with `json.dump(data, f, indent=2)`, then `os.replace(tmp.name, path)` (use `os.replace` instead of `os.rename` for cross-platform atomicity — `os.rename` can fail on Windows if target exists)
- `update_state(state: State, verified_dir: Path, run_date: str, searched_role_types: list[str]) -> State` -- scan verified JSONs, update state, expire old. Job keys derived from `{role_type_slug}/{filename_without_json}`. Expiry only for searched role types. The `searched_role_types` parameter is a list of role type slugs (e.g., `["community-manager", "founders-associate"]`). The caller (orchestrator) is responsible for filtering this list based on `_status.json` — only role types with `"complete"` or `"partial"` status should be included. `manage_state.py` trusts this input and does not read `_status.json`. **Empty list behavior:** If `searched_role_types` is empty, no jobs are expired (no role types were searched, so no absence signal exists). State is still updated with any new jobs found in `verified_dir`. Expired job resurrection: restore from expired_jobs, preserve first_seen, update last_seen, set `user_action` to `None`, set `reappeared = True`. **Post-processing:** After all updates (new jobs added, expirations applied, resurrections completed), reset `reappeared = False` for all jobs in `state.jobs` that were seen in the current scan but were NOT newly resurrected this run. "Seen in the current scan" means a verified JSON file for this job key exists in `verified_dir` during this run. Jobs in `state.jobs` whose role type was not searched are untouched (including their `reappeared` flag). The `reappeared` flag is only `True` during the specific run where a job is restored from `expired_jobs`.
- `compute_delta(state: State, run_date: str) -> dict` -- returns `{"run_date": "...", "new_jobs": ["community-manager/acme-corp-growth-lead", ...], "still_active": ["devrel/some-company-dev-advocate", ...], "expired_count": N, "rejected_count": N}`. The delta carries only classification data — job key lists (strings) indicating which jobs are new vs still-active. Full rendering data (score, score_breakdown, gaps, notes, requirements_met) is read directly from verified JSON files by the consuming agents. `still_active` excludes jobs where `user_action == "rejected"`. **Known limitation:** `still_active` list grows unboundedly in scheduled mode — without user interaction to reject jobs, active jobs accumulate. Acceptable for V14; revisit if list exceeds 50 jobs.
- `record_action(state: State, job_key: str, action: str) -> State` -- validates job_key exists (raises KeyError if not). Validates action is in `VALID_ACTIONS` (raises ValueError if not). Sets user_action to the given action. V14 tracks two states only (accepted/rejected). Richer lifecycle tracking (e.g., "applied", "briefed", "interviewing") deferred to future versions.

**Thin CLI wrapper:** argparse with a single `sync` subcommand that calls update_state + compute_delta in one pass. Tests exercise library functions directly; the CLI wrapper is thin enough to validate via smoke test. `record_action()` remains as a library function only (no CLI subcommand).

- `sync --verified-dir DIR --run-date DATE --searched-role-types type1,type2,... --state PATH --output FILE`
  - `--state PATH`: path to state.json (default: `state.json` in working directory)
  - `--output FILE`: writes the delta JSON (output of `compute_delta`)
  - `--searched-role-types` parsing: split on comma (`args.searched_role_types.split(',')`) to convert to `list[str]`. If the argument is empty string, pass an empty list to `update_state`.

**Constants:** `EXPIRY_DAYS = 14` and `VALID_ACTIONS = {"accepted", "rejected"}` at module level.

**Verify:**
```bash
cd 03_agents/tests/v14 && python3 -m pytest tests/test_manage_state.py -v
# Expected: 14 passed
```

### Task 4.3: Create initial state.json

**Create:** `03_agents/tests/v14/state.json`
```json
{
  "last_run_date": null,
  "jobs": {},
  "expired_jobs": {}
}
```

State.json schema -- each job entry in `jobs` must include: `title`, `company`, `score`, `role_type`, `source`, `first_seen`, `last_seen`, `active_status`, `job_url`, `location`, `requirements_met`, `user_action` (null | "accepted" | "rejected"), `expired_date` (null | date string), `reappeared` (bool, default false). The `expired_jobs` dict is keyed by job key (same format as `jobs`), storing the same `JobEntry` objects (with `expired_date` populated).

**Note:** The design document shows `expired_jobs` as an array `[]`. This plan intentionally uses `dict` (`{}`) instead — dict provides O(1) lookups by job key, which is required for resurrection checks. The plan's dict format is canonical; the design doc is superseded on this point.

**Decision:** Intentional clean start. V13 verified data is not migrated. All jobs on V14's first run will appear as 'new'.

**Commit:** `feat(jsa-v14): add state management with daily delta tracking (TDD, 14 tests)`

---

## PHASE 5: Visual Output (Digest Email + Briefs PDF)

### Task 5.1: Rewrite jsa-digest-email skill

**Modify:** `03_agents/tests/v14/.claude/skills/jsa-digest-email.md`

Complete rewrite with:
- **7 variables:** `run_date`, `user_email`, `user_name`, `total_briefs` (int), `new_today` (array of job key strings, e.g., `["community-manager/acme-corp-growth-lead", "devrel/some-company-dev-advocate"]`), `still_active` (array of job key strings, same format), `verified_dir` (path to verified JSON directory, e.g., `output/verified/`). Agent computes counts from array lengths (`len(new_today)`, `len(still_active)`) — no separate count variables needed.
- **Sections:** Header → Summary strip → **New Today** (full detail, card layout) → **Still Active** (compact table) → Footer
- **REMOVED:** Statistics section, score distribution
- **Links:** subtle underline + accent color (`text-underline-offset: 3px`)
- **Mobile:** `@media` queries for card layout on narrow screens, table fallback for clients that strip CSS
- **CSS:** Reference the preloaded `jsa-design-system` skill. Do not embed a copy.
- **New/Still Active determination:** The orchestrator passes delta-classified lists (`new_today`, `still_active`) as template variables — these contain job keys and the new/still-active classification. The digest email agent does NOT read `state.json`. Reads verified JSON files from `output/verified/` for full job rendering data (score_breakdown, gaps, notes, etc.). Uses delta-classified lists only for new/still-active classification.
- **Job cards:** Always use verified JSON data from verified JSON files for job cards (score, score_breakdown, location, requirements_met, gaps, notes). Single rendering path — no conditional logic based on scheduled vs interactive mode.
- **Conditional Sections:**
  - When `total_briefs == 0`: omit "Application briefs attached as PDF" footer line
  - When `new_today` is empty: omit "New Today" section header, show only "Still Active"
  - When `still_active` is empty: omit "Still Active" section header, show only "New Today"
- **send_email.py compatibility:** V13 `send_email.py` already handles `args.attachment` being `None` (no attachment). Verify this path works for scheduled runs where no PDF is generated. Add a verification step in Phase 8 to confirm no-attachment email sends succeed.
- **Data flow summary:** Orchestrator computes delta via `manage_state.py` -> passes job key lists (`new_today`, `still_active`) + `verified_dir` path as template variables -> digest email agent reads verified JSON files from `verified_dir` for full rendering data (score_breakdown, gaps, notes) -> renders cards using design system CSS.

### Task 5.2: Verify digest-email agent definition has 7 variables

Agent definition was written with 7 variables in Task 1.6. Verify: `grep "7 template" 03_agents/tests/v14/.claude/agents/digest-email.md` — should match.

### Task 5.3: Update digest-email agent memory

Normalize heading to `# Digest-Email Agent Memory` with `## Key Patterns` section. Add: 7 variables (including new_today and still_active job key lists from orchestrator delta, verified_dir path for reading full job data from verified JSONs — counts computed from array lengths), removed Statistics, mobile CSS, link styling, delta determination. Agent reads verified JSON files directly from `output/verified/` for rendering data — does NOT read `state.json`.

**Verify:**
```bash
grep -i "statistics" 03_agents/tests/v14/.claude/skills/jsa-digest-email.md   # zero matches
grep "New Today" 03_agents/tests/v14/.claude/skills/jsa-digest-email.md        # match
grep "Still Active" 03_agents/tests/v14/.claude/skills/jsa-digest-email.md     # match
grep "@media" 03_agents/tests/v14/.claude/skills/jsa-digest-email.md           # match
grep "jsa-design-system" 03_agents/tests/v14/.claude/skills/jsa-digest-email.md  # references design system
grep "underline" 03_agents/tests/v14/.claude/skills/jsa-digest-email.md        # match
grep "7 template" 03_agents/tests/v14/.claude/agents/digest-email.md           # match
```

**Commit:** `feat(jsa-v14): rewrite digest email with daily delta, mobile CSS, styled links`

### Task 5.4: Rewrite jsa-briefs-pdf skill

**Modify:** `03_agents/tests/v14/.claude/skills/jsa-briefs-pdf.md`

Key changes:
- `width: "800px"` + `prefer_css_page_size: True` (NOT `format: "A4"`)
- CSS: `break-before: page` on `.brief-page` (single break rule; do not use both `break-before` and `break-after` as dual rules create ambiguity)
- NO `@page { size: A4 }`, NO deprecated `page-break-*` properties
- Each brief is one continuous page of variable height
- Reference the preloaded `jsa-design-system` skill for all CSS.
- Playwright render call: `page.pdf(path=output_path, width='800px', prefer_css_page_size=True)` — no `format` parameter, no `height` parameter (height determined by content). Same script pattern as V13 but with new PDF options.

### Task 5.5: Update briefs-pdf agent memory

Normalize heading to `# Briefs-PDF Agent Memory` with `## Key Patterns` section. Add: continuous-page rendering, no A4, `prefer_css_page_size`, `break-before: page` only (single break rule).

**Verify:**
```bash
grep -i "format.*A4" 03_agents/tests/v14/.claude/skills/jsa-briefs-pdf.md        # zero matches
grep "break-before: page" 03_agents/tests/v14/.claude/skills/jsa-briefs-pdf.md    # match
grep "width.*800" 03_agents/tests/v14/.claude/skills/jsa-briefs-pdf.md            # match
grep "prefer_css_page_size" 03_agents/tests/v14/.claude/skills/jsa-briefs-pdf.md  # match
grep "jsa-design-system" 03_agents/tests/v14/.claude/skills/jsa-briefs-pdf.md  # references design system
```

**Commit:** `feat(jsa-v14): continuous-page PDF rendering, remove A4 format`

---

## PHASE 6: CLAUDE.md Orchestrator Rewrite

### Task 6.1: Rewrite CLAUDE.md

**Modify:** `03_agents/tests/v14/CLAUDE.md`

**Base:** V13 CLAUDE.md. Apply these changes:

**Add sections:**
- HARD CONSTRAINTS: "Never pass `model:` to Task tool" + "CSS canonical (reference design system skill)"
- AUTO-RETRY PROTOCOL: retry once on failure, continue on second failure
- SCHEDULED RUNS: GitHub Actions mode, skip onboarding/interactive steps, state committed to main (pushes directly to main). **Non-overlap constraint:** Interactive runs do not commit state, so no conflict with scheduled runs. Known limitation: if a user runs interactively and a scheduled run fires before the interactive session ends, the scheduled run's state update will not include the interactive session's actions. Mitigation: the interactive session does not save state until user feedback (step 16), so the conflict window is limited. The scheduled run's state is authoritative (committed to main); the interactive session's state.json becomes stale on next `git pull`.

**Modify sections:**
- ON STARTUP: capture run date, then `git pull` (interactive mode only) to ensure `state.json` is current, then load `state.json` and use `last_run_date`. Git pull MUST happen before state load — scheduled runs may have committed updates since the last interactive session.
- ONBOARDING: dispatch `onboarding` subagent for CV parse + source discovery (writes _onboarding_draft.json with profile data and discovered sources), parent merges to context.md
- SESSION MANAGEMENT: V14 replaces V13's mid-session resume via `session-state.md` with persistent state tracking via `state.json`. The `state.json` file tracks job lifecycle across runs (new, active, expired, user actions). `output/session-state.md` is repurposed as a human-readable run log (final summary), not a checkpoint for resume. Mid-session interruptions are handled by re-running — `state.json` preserves job data, and search-verify overwrites verified JSONs idempotently.
- ORCHESTRATION WORKFLOW: 20 steps — the full step list:
  1. Capture run date
  2. Git pull (interactive mode only)
  3. Load state.json
  4. Pre-run cleanup (check last_run_date)
  5. Read context.md
  6. If onboarding needed: dispatch onboarding subagent
  7. Prepare 14 template variables per role type (including `industry_qualifiers`)
  8. Dispatch search-verify agents in batches of 2-3, auto-retry once on failure
  9. After each batch: read `_status.json`, collect role types with "complete"/"partial" status into `searched_role_types` list (collection only — state update happens in step 12). Checkpoint: write session-state.md progress after every 3 role types.
  10. Read `_summary.md` for each completed role type
  11. Cross-role-type deduplication
  12. Update state via `manage_state.py sync` (passes `searched_role_types`)
  13. Compute delta via `manage_state.py` (returns job key lists)
  14. Present results to user (New Today + Still Active subsections)
  15. Collect user feedback, record_action in loop
  16. Save state after user feedback (call save_state)
  17. Dispatch brief agents for accepted jobs, auto-retry once
  18. Dispatch digest-email (7 variables including verified_dir) + briefs-pdf in parallel
  19. Send email (parent-orchestrated)
  20. Write output/session-state.md
  After user reviews and accepts/rejects jobs (step 15), call `record_action(state, job_key, action)` in a loop for each user decision — e.g., `for key, action in decisions: record_action(state, key, action)` — then save state. Final step: write `output/session-state.md` — a human-readable run log with these sections:
  ```markdown
  # Session State — {run_date}
  ## Run Summary
  - Date: {run_date}
  - Mode: interactive | scheduled
  - Role types searched: {list}
  ## Results
  - New jobs found: {N}
  - Still active: {N}
  - Expired: {N}
  - Rejected: {N}
  ## Actions Taken
  - Briefs generated: {N}
  - Email sent: yes/no
  - Errors: {list or "none"}
  ```
- PRESENTATION WORKFLOW: Modify existing V13 PRESENTATION WORKFLOW section. Keep existing table format. Add only these deltas: (1) "New Today" and "Still Active" subsections, (2) `†` dagger marker for unverified listings with footnote, (3) quick notes — a one-line company summary appended as a footnote below the URL list for every company (e.g., `Duku AI — AI autonomous testing platform, Series A, London`). Sourced from the `notes` field in verified JSON. The orchestrator extracts the first sentence of the `notes` field and truncates to max 15 words if needed. Output: formatted directly by the orchestrator (console output during interactive mode, passed to email agent for digest). No intermediate file.
- All paths: v13 -> v14

**Keep unchanged:** CORE RULES, CONSTRAINT DERIVATION, UX RULES, SECURITY, CAPABILITIES, OUTPUTS

### Task 6.2: Update settings.local.json

**Modify:** `03_agents/tests/v14/.claude/settings.local.json`

Replace 52 individual `WebFetch(domain:...)` with single `"WebFetch(*)"`. Add broader Bash patterns.

```json
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(pip3 install:*)",
      "Bash(rm:*)",
      "Bash(mkdir:*)",
      "Bash(date:*)",
      "Bash(ls:*)",
      "Bash(wc:*)",
      "Bash(tail:*)",
      "Bash(head:*)",
      "Bash(grep:*)",
      "Bash(cat:*)",
      "Bash(curl:*)",
      "Bash(done)",
      "Bash(pdfinfo:*)",
      "Bash(pandoc:*)",
      "WebFetch(*)",
      "WebSearch",
      "mcp__plugin_compound-engineering_pw__browser_navigate",
      "mcp__plugin_compound-engineering_pw__browser_take_screenshot",
      "mcp__plugin_compound-engineering_pw__browser_press_key"
    ]
  }
}
```

**Note:** `WebFetch(*)` is intentionally broad. WebFetch is read-only and agent behavior is bounded by instructions, not URL allowlists.

**Verify:**
```bash
grep "HARD CONSTRAINTS" 03_agents/tests/v14/CLAUDE.md      # match
grep "AUTO-RETRY" 03_agents/tests/v14/CLAUDE.md             # match
grep "SCHEDULED RUNS" 03_agents/tests/v14/CLAUDE.md         # match
grep "industry_qualifiers" 03_agents/tests/v14/CLAUDE.md    # match
grep "manage_state.py" 03_agents/tests/v14/CLAUDE.md        # match
grep "PRESENTATION WORKFLOW" 03_agents/tests/v14/CLAUDE.md  # match
grep 'WebFetch(\*)' 03_agents/tests/v14/.claude/settings.local.json  # match
```

**Commit:** `feat(jsa-v14): rewrite orchestrator — hard constraints, auto-retry, 20 steps, scheduled mode`

---

## PHASE 7: GitHub Actions Scheduler

### Task 7.1: Create GitHub Actions workflow

**NOTE:** This workflow file is a template. GitHub Actions only reads from the repository root `.github/workflows/`. Before enabling scheduled runs, copy this file to the repo root `.github/workflows/daily-digest.yml`. All `run:` steps already include `working-directory: 03_agents/tests/v14` — no modification needed when copying.

**Create:** `03_agents/tests/v14/.github/workflows/daily-digest.yml`

```yaml
name: Daily Job Search Digest

on:
  schedule:
    - cron: '0 7 * * 1-5'  # 07:00 UTC = 7am GMT (winter) / 8am BST (summer). Accept seasonal 1hr drift.
  workflow_dispatch: {}

concurrency:
  group: jsa-daily-digest
  cancel-in-progress: false  # Trade-off: manual workflow_dispatch during scheduled run will queue (not cancel). Queued run may use stale data. Acceptable — manual triggers are rare.

permissions:
  contents: write

jobs:
  daily-digest:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        working-directory: 03_agents/tests/v14
        run: |
          pip install python-jobspy resend playwright
          python -m playwright install chromium
      - name: Install Claude Code
        working-directory: 03_agents/tests/v14
        run: |
          npm install -g @anthropic-ai/claude-code
          claude --version
      - name: Verify settings.local.json permissions
        working-directory: 03_agents/tests/v14
        run: |
          python3 -c "import json; c=json.load(open('.claude/settings.local.json')); perms=c.get('permissions',{}).get('allow',[]); assert len(perms) >= 10, f'Expected >=10 permissions, got {len(perms)}'"
      - name: Run scheduled digest
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          SCHEDULED_RUN: 'true'
        working-directory: 03_agents/tests/v14
        run: |
          claude --model claude-opus-4-6 --print "Run scheduled daily digest. SCHEDULED_RUN=true."
      - name: Commit state
        working-directory: 03_agents/tests/v14
        run: |
          git config user.name "Job Search Agent"
          git config user.email "agent@autonomous.bot"
          git add state.json output/session-state.md
          git diff --staged --quiet || git commit -m "chore(jsa): daily digest $(date +%Y-%m-%d)"
          git push origin main
```

**State commit policy:** State is committed regardless of email delivery success. If search-verify succeeded but email failed, the state still has valid new jobs that should be persisted. Email delivery status is tracked separately in `output/digests/_status.json` (no `sent_at` field if send failed). The `git diff --staged --quiet` check ensures no commit is created if nothing changed (e.g., total failure before state update).

**Verify:**
```bash
grep "cron:" 03_agents/tests/v14/.github/workflows/daily-digest.yml     # '0 7 * * 1-5'
grep "claude-opus-4-6" 03_agents/tests/v14/.github/workflows/daily-digest.yml  # match
```

**Commit:** `feat(jsa-v14): add GitHub Actions daily digest scheduler`

---

## PHASE 8: End-to-End Verification

### Task 8.1: Cross-file consistency checks (7 cross-cutting checks)

```bash
# 1. No v13 paths anywhere
grep -r "v13" 03_agents/tests/v14/ --include="*.md" --include="*.py" --include="*.json" --include="*.yml" | grep -v ".git" | grep -v "output/"
# Expected: zero

# 2. All 5 agents have skills + model:inherit, no reference template loading
grep -c "model: inherit" 03_agents/tests/v14/.claude/agents/*.md  # 5
grep -l "skills:" 03_agents/tests/v14/.claude/agents/*.md | wc -l  # 5
grep -r "Read your full instructions" 03_agents/tests/v14/.claude/agents/  # zero

# 3. No reference templates remain (subagent-* files deleted)
ls 03_agents/tests/v14/references/subagent-*.md 2>/dev/null  # no such file

# 4. state.json is valid JSON with correct schema
python3 -c "
import json, sys
s=json.load(open('03_agents/tests/v14/state.json'))
errors = []
if 'jobs' not in s: errors.append('Missing jobs key')
if 'expired_jobs' not in s: errors.append('Missing expired_jobs key')
if 'schema_version' in s: errors.append('state.json must not contain schema_version')
if 'run_history' in s: errors.append('state.json must not contain run_history')
if errors: print('\n'.join(errors), file=sys.stderr); sys.exit(1)
"

# 5. GitHub Actions workflow exists
ls 03_agents/tests/v14/.github/workflows/daily-digest.yml  # exists

# 6. Both visual output skills reference jsa-design-system
grep -l 'jsa-design-system' 03_agents/tests/v14/.claude/skills/jsa-{digest-email,briefs-pdf}.md | wc -l  # 2

# 7. Presentation workflow rules present in CLAUDE.md
grep "dagger\|†" 03_agents/tests/v14/CLAUDE.md       # match (unverified marker)
grep "footnote" 03_agents/tests/v14/CLAUDE.md          # match (reference URLs)
```

Note: "All tests pass" check removed from 8.1 — covered by Task 8.2.

Note: Per-phase verification steps remain in their respective phases (Phase 1 font check, Phase 3 cross-ref check, Phase 5 no-statistics check, Phase 5 no-A4 check, etc.)

### Task 8.2: Run all tests

```bash
# First, validate V13 tests still pass after copy (catch breakage before adding V14 tests)
cd 03_agents/tests/v14 && python3 -m pytest tests/test_filter_jobs.py tests/test_summarize_jobs.py -v
# Expected: 6 passed (3 filter + 3 summarize)

# Then, run all tests including V14 state management
cd 03_agents/tests/v14 && python3 -m pytest tests/ -v
# Expected: 20 passed (3 filter + 3 summarize + 14 state management)
# Note: Test fixtures should use the full verified JSON schema (all fields from V13 output, including score_breakdown, requirements_met, gaps, notes) to ensure manage_state.py handles real data shapes.
```

### Task 8.3: Manual smoke test checklist

- [ ] Onboarding CV parse + source discovery dispatches to subagent -- `output/_onboarding_draft.json` created with profile fields and discovered sources
- [ ] search-verify writes `_summary.md` -- `output/verified/{slug}/_summary.md` contains table with Score/Title/Company columns
- [ ] Orchestrator PRESENTATION WORKFLOW produces identical tables for all role types
- [ ] digest-email has no Statistics, has mobile CSS, has New Today / Still Active
- [ ] briefs-pdf uses continuous pages, no A4
- [ ] state.json updated after run
- [ ] GitHub Actions triggers on `workflow_dispatch`
- [ ] Scheduled run produces valid email with zero briefs, no PDF attachment line (local test: `SCHEDULED_RUN=true claude --model claude-opus-4-6 --print "Run scheduled daily digest."`)

**Rollback:** Each phase has its own commit. To revert a specific phase, use `git revert <commit-hash>`. Phases are independent enough for selective revert.

---

## Summary

| Phase | Tasks | Description | Files | Commit |
|-------|-------|-------------|-------|--------|
| 1 | 7 | Baseline setup (copy, design system, skills migration) | 1 dir copied, 4 skills created, 4 agents modified, 4 refs deleted | 3 commits (below) |
| 2 | 1 | Onboarding subagent | 3 created (agent, skill, memory) | 1 commit |
| 3 | 3 | V13 failure fixes | 3 modified | 1 commit |
| 4 | 3 | State management (TDD) | 5 created (tests, conftest, fixtures, manage_state.py, state.json) | 1 commit |
| 5 | 5 | Visual output (digest email + briefs PDF) | 5 modified | 2 commits |
| 6 | 2 | CLAUDE.md rewrite | 2 modified | 1 commit |
| 7 | 1 | GitHub Actions | 1 created | 1 commit |
| 8 | 3 | Verification | 0 | 0 commits |

**All 10 commit messages:**
1. `chore(jsa-v14): copy v13 baseline and update paths`
2. `feat(jsa-v14): upgrade design system with distinctive fonts and palette`
3. `refactor(jsa-v14): migrate reference templates to skills, update agent definitions`
4. `feat(jsa-v14): add onboarding subagent with CV parsing and source discovery`
5. `fix(jsa-v14): add cross-reference verification, industry qualifiers, summary output`
6. `feat(jsa-v14): add state management with daily delta tracking (TDD, 14 tests)`
7. `feat(jsa-v14): rewrite digest email with daily delta, mobile CSS, styled links`
8. `feat(jsa-v14): continuous-page PDF rendering, remove A4 format`
9. `feat(jsa-v14): rewrite orchestrator — hard constraints, auto-retry, 20 steps, scheduled mode`
10. `feat(jsa-v14): add GitHub Actions daily digest scheduler`

**Total: 8 phases, 25 tasks, 10 commits**

---

## Critical Files

| File | Why Critical |
|------|-------------|
| `.claude/skills/jsa-design-system.md` | Foundation for all visual output quality |
| `.claude/skills/jsa-search-verify.md` | Largest skill; cross-ref, industry queries, summary |
| `.claude/skills/jsa-digest-email.md` | Complete rewrite with delta, mobile, links |
| `scripts/manage_state.py` | Only TDD-tested code; daily delta engine |
| `CLAUDE.md` | Core orchestrator; 20-step workflow |

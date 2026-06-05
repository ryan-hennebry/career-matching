# Plan: JSA V21 — Code Infrastructure + Structural Decomposition + Validation Harness

## Overview

V21 evolves the V20 job search agent through three layers: (1) code infrastructure — manage_state.py cleanup/dedup CLI, CLAUDE.md decomposition to ~211 lines with reference file extraction, GH Actions config file replacing heredoc; (2) constraint promotion — 4 parent proposals to CLAUDE.md, 6 subagent proposals to reference files, 10 implementation constraints; (3) validation harness — preflight.sh with tiered checks, GH Actions integration.

Base: copy `03_agents/tests/v20/` to `03_agents/tests/v21/`, then modify in place.

## Files to Modify

### New Files
- `03_agents/tests/v21/scripts/manage_state.py` — Rewrite: cleanup + dedup CLI (no pre-run alias)
- `03_agents/tests/v21/scripts/preflight.sh` — New: tiered pre-session validation
- `03_agents/tests/v21/.github/jsa-config.json` — New: standalone JSON config
- `03_agents/tests/v21/references/orchestration.md` — New: extracted orchestration workflow (5 phases)
- `03_agents/tests/v21/references/presentation-rules.md` — New: extracted presentation rules
- `03_agents/tests/v21/tests/test_manage_state.py` — New: combined cleanup + dedup tests (single file, shared fixtures)
- `03_agents/tests/v21/tests/test_preflight.py` — New: preflight.sh tests
<!-- test_claude_md_structure.py removed: structure checks moved to preflight.sh "CLAUDE.md structure" tier -->

### Modified Files
- `03_agents/tests/v21/CLAUDE.md` — Decompose from 676 to ~211 lines
- `03_agents/tests/v21/.github/workflows/daily-digest.yml` — Replace heredoc with config file read + add preflight step
- `03_agents/tests/v21/.claude/settings.local.json` — Add directory-level wildcard permissions
- `03_agents/tests/v21/context.md` — Add Dashboard URL to `## Delivery` section
- `03_agents/tests/v21/references/subagent-search-verify.md` — Speed optimization (drop external lookups)
- `03_agents/tests/v21/references/subagent-digest-email.md` — Add idempotent email gate (P4)
- `03_agents/tests/v21/references/algorithms.md` — No changes (preserved as-is)

## Implementation Steps

---

### Phase 1: Foundation — Copy V20 + manage_state.py (Layer 1a)

**Dependency:** None (start of plan)

#### Step 1: Copy V20 directory to V21
**File:** `03_agents/tests/v21/` (entire directory)
**Action:** Create (copy from V20)

Copy the V20 directory wholesale to create the V21 base. This preserves all existing files, tests, configs, and agents.

```bash
cp -r 03_agents/tests/v20 03_agents/tests/v21
```

**Verify:**
- Bash: `diff <(ls -R 03_agents/tests/v20) <(ls -R 03_agents/tests/v21)` — identical structure
- Bash: `wc -l 03_agents/tests/v21/CLAUDE.md` — should be 676

#### Step 2: Write failing tests for manage_state.py (cleanup subcommand)
**File:** `03_agents/tests/v21/tests/test_manage_state.py`
**Action:** Create

Single test file for all manage_state.py tests (cleanup + dedup share fixture setup).

Tests for the cleanup subcommand (class `TestCleanup`):
- `test_cleanup_removes_raw_directory` — Creates temp files in `output/raw/`, runs cleanup, asserts directory removed
- `test_cleanup_removes_search_results` — Creates temp files in `output/search-results/`, runs cleanup, asserts removed
- `test_cleanup_removes_unverified` — Creates temp files in `output/unverified/`, runs cleanup, asserts removed
- `test_cleanup_preserves_verified` — Creates files in `output/verified/`, runs cleanup, asserts ALL files remain
- `test_cleanup_preserves_jobs` — Creates files in `output/jobs/`, runs cleanup, asserts ALL files remain
- `test_cleanup_handles_missing_directories` — Runs cleanup when temp dirs don't exist, asserts no error
- `test_cleanup_dry_run` — Runs cleanup with --dry-run, asserts temp dirs still exist
- `test_cleanup_never_touches_verified_with_active_jobs` — Verified files with active jobs in state.json remain untouched after cleanup

**Verify:**
- Test: `cd 03_agents/tests/v21 && python -m pytest tests/test_manage_state.py::TestCleanup -v` — all tests FAIL (no implementation yet)
- Lint: `ruff check 03_agents/tests/v21/tests/test_manage_state.py`

#### Step 3: Write failing tests for manage_state.py (dedup subcommand)
**File:** `03_agents/tests/v21/tests/test_manage_state.py`
**Action:** Append to file created in Step 2

Tests for the dedup subcommand (class `TestDedup`):
- `test_dedup_detects_cross_role_duplicates` — Two verified JSONs in different role dirs with same (company, title) normalized. Asserts lower-scoring copy moved to `output/archive/`
- `test_dedup_normalization_case_insensitive` — "Acme Corp" vs "acme corp" detected as same
- `test_dedup_normalization_strips_whitespace` — " Acme Corp " vs "Acme Corp" detected as same
- `test_dedup_archives_below_threshold` — Job with score <70 moved to `output/archive/`
- `test_dedup_preserves_above_threshold` — Job with score >=70 preserved in verified/
- `test_dedup_keeps_highest_score` — Of two duplicates (scores 85 and 72), keeps 85 in verified/, archives 72
- `test_dedup_handles_unicode_company_names` — "Zürich AG" and "zürich ag" detected as same
- `test_dedup_handles_empty_directories` — Runs dedup when verified/ has no subdirs, no error
- `test_dedup_dry_run_preserves_all` — Runs with --dry-run, asserts no files moved
- `test_dedup_scans_filesystem_for_roles` — Roles are derived from `output/verified/*/` directory names, not a hardcoded list
- `test_dedup_same_url_within_role` — Two verified JSONs in the same role dir with the same URL but different (company, title). Asserts lower-scoring copy archived (V20 regression: within-role same-URL dedup)
- `test_dedup_preserves_at_least_one_copy` — Cross-role dedup of N duplicates always preserves exactly one copy in verified/ (V20 dashboard API dependency)

**Verify:**
- Test: `cd 03_agents/tests/v21 && python -m pytest tests/test_manage_state.py::TestDedup -v` — all tests FAIL
- Lint: `ruff check 03_agents/tests/v21/tests/test_manage_state.py`

#### Step 4: Implement manage_state.py
**File:** `03_agents/tests/v21/scripts/manage_state.py`
**Action:** Rewrite

Complete rewrite of manage_state.py as a CLI with subcommands:
- `cleanup` — removes `output/raw/`, `output/search-results/`, `output/unverified/`. NEVER touches `output/verified/` or `output/jobs/`. Uses `shutil.rmtree` with `ignore_errors=True`.
- `dedup` — scans `output/verified/*/` directories (filesystem-driven role discovery). For each JSON file, extracts `(company, title)` normalized via `.lower().strip()`. Cross-role dedup: if same key appears in multiple roles, keep highest-scoring copy, archive others to `output/archive/`. Within-role same-URL dedup: if two JSONs in the same role dir share the same URL (normalized), keep highest-scoring copy, archive the other (V20 regression). Score threshold: archive jobs with `overall_score < 70`. Cross-role dedup must always preserve at least one copy per unique job in verified/ (V20 dashboard API dependency).
  - **Dedup strategy separation:** Extract matching logic into separate functions: `_find_cross_role_duplicates()` and `_find_same_url_duplicates()` — each returns a list of `(keep, archive)` pairs. A single `_apply_archive()` function processes these pairs (move to archive directory, create subdirs). This separates the two distinct dedup dimensions (cross-role company+title vs within-role same-URL) from the shared archive-or-keep flow.
  - **Archive directory contract:** Archived files go to `output/archive/{role}/{filename}` (mirroring verified/ structure). Each archived file retains its original JSON content unchanged. Dashboard API must exclude `output/archive/` — only `output/verified/` is served. Use `os.makedirs(exist_ok=True)` when creating archive subdirectories to avoid `FileNotFoundError`.
- `--dry-run` flag on all subcommands (prints actions, doesn't execute).
- **No `pre-run` subcommand.** ON STARTUP calls `python3 scripts/manage_state.py cleanup && python3 scripts/manage_state.py dedup` — two explicit commands are clearer than an alias with zero logic.
- Uses argparse, standard library only (os, json, glob, shutil, pathlib).

**Verify:**
- Test: `cd 03_agents/tests/v21 && python -m pytest tests/test_manage_state.py -v` — all tests PASS
- Lint: `ruff check 03_agents/tests/v21/scripts/manage_state.py`

#### Step 5: Commit Phase 1
```bash
cd 03_agents/tests/v21 && git add -A && git commit -m "feat(jsa-v21): Layer 1a — manage_state.py cleanup/dedup CLI with tests"
```

**Verify:**
- Bash: `git log --oneline -1` — confirms commit

---

### Phase 2: CLAUDE.md Decomposition (Layer 1b)

**Dependency:** Phase 1 complete

#### Step 6: Add "CLAUDE.md structure" tier to preflight.sh spec
**File:** (no file change yet — this defines requirements for Step 20's preflight.sh implementation)
**Action:** Define requirements

The CLAUDE.md structural checks that were planned for a separate `test_claude_md_structure.py` are instead integrated into `preflight.sh` as a "CLAUDE.md structure" tier. This avoids over-engineering 14 Python tests for what is a linting concern. The following checks will be added to preflight.sh (Step 20):

**Critical CLAUDE.md structure checks (exit 1 on failure):**
- CLAUDE.md <=280 lines
- `## Hard Constraints` section exists
- `## Context Budget` section exists
- `## Core Rules` section exists
- `## ON STARTUP` section exists
- Phase dispatch table exists with 5 phases (Search, Verify, Dedup, Present, Deliver)
- Each dispatch row references a `references/*.md` file
- ON STARTUP references `preflight.sh`
- ON STARTUP references `manage_state.py`

**Critical reference file structure checks (exit 1 on failure):**
- `references/orchestration.md` exists and contains sections for all 5 phases
- `references/presentation-rules.md` exists and contains table formatting rules

No separate test file is created. These checks run as part of `bash scripts/preflight.sh`.

**Verify:**
- No verification needed at this step (requirements only; implementation in Step 20)

#### Step 7: Create references/orchestration.md
**File:** `03_agents/tests/v21/references/orchestration.md`
**Action:** Create

Extract the orchestration workflow from CLAUDE.md into this file. Organize by 5 phases:
- `## Phase 1: Search` — Source discovery, JobSpy aggregation, specialty board scraping
- `## Phase 2: Verify` — Listing verification, fit scoring, company context (moderate trim: keep listing analysis, drop external lookups)
- `## Phase 3: Dedup` — Run manage_state.py dedup, cross-role dedup, score threshold enforcement. Must include exact CLI invocations with correct flags (e.g., `python3 scripts/manage_state.py dedup --verified-dir output/verified --archive-dir output/archive`). Pin flag names here as the single source of truth — argparse flags in manage_state.py must match these exactly.
- `## Phase 4: Present` — Format tables, standardized table format, user feedback loop
- `## Phase 5: Deliver` — Briefs generation, digest email with dashboard URL, git commit. **Entry criteria must include:** check `output/digests/_status.json` for `email_sent: true` for today's date — if already sent, skip email dispatch entirely (authoritative idempotency gate at orchestration layer; subagent retains defensive check)

Each phase section includes:
- Entry criteria (what must be true before starting)
- Numbered step-by-step instructions (the actual workflow)
- Exit criteria (what must be true when done)
- Subagent dispatch patterns where applicable

**Note:** No checkpoint JSON protocol. Continue using `session-state.md` for state tracking. Checkpointing can be added in a future version if a specific failure mode justifies it.

Also includes a `## State Architecture` section with one-liner comments per state file (kept minimal to avoid documentation drift):
- `_status.json` — owned by digest-email subagent, tracks email-sent status
- `session-state.md` — owned by parent orchestrator, tracks session progress
- `state.json` — owned by parent orchestrator, maps active jobs

Also includes P6 (selective cleanup via manage_state.py) in Phase 3 instructions.
Also includes P9 (zsh safe directory cleanup) in relevant cleanup sections.
Also includes I8 (incremental commit enforcement) per-phase. **Copy spec for commit instruction in orchestration.md Phase 1:** The exact text must be: "After each search batch: `git add output/ && git commit -m 'batch N complete' && git push`" — this prescribes the exact instruction that must appear in orchestration.md to enforce per-batch incremental commits (V14/V16/V18/V19/V20 5-version recurrence).

**Additional verification:** Ensure no `model:` parameter appears in dispatch blocks within CLAUDE.md, orchestration.md, or any subagent reference file. Verify: `grep -rn "model:" CLAUDE.md references/orchestration.md references/subagent-*.md` should return no matches in dispatch/Task-tool blocks (V19 HC1 regression).

**Verify:**
- Bash: `test -f 03_agents/tests/v21/references/orchestration.md && echo "exists"` — exists
- Bash: `grep -q "commit.*push\|incremental commit\|per-batch commit" 03_agents/tests/v21/references/orchestration.md && echo "PASS: per-batch commit+push documented" || echo "FAIL: missing incremental commit+push enforcement"` — PASS

#### Step 8: Create references/presentation-rules.md
**File:** `03_agents/tests/v21/references/presentation-rules.md`
**Action:** Create

Extract presentation rules from CLAUDE.md:
- Table formatting rules (I6 standardization)
- Column definitions, sort order, display rules
- Score display format
- Empty-state messaging
- All UX rules related to presentation

**Verify:**
- Bash: `test -f 03_agents/tests/v21/references/presentation-rules.md && echo "exists"` — exists
- Bash: `grep -q "identical.*table\|same.*format\|uniform.*table" 03_agents/tests/v21/references/presentation-rules.md && echo "PASS: uniform table format enforced" || echo "FAIL: missing identical table format enforcement"` — PASS (V19/V20 recurrence: all role types must use identical table format)

#### Step 9: Decompose CLAUDE.md
**File:** `03_agents/tests/v21/CLAUDE.md`
**Action:** Modify (major reduction)

Rewrite CLAUDE.md as a compact orchestrator (~266 lines):
- **Retain:** Hard Constraints, Context Budget, Core Rules, ON STARTUP, Onboarding (inline), Constraint Derivation, Auto-Retry Protocol, Recovery Protocol, UX Rules, Session Management, Scheduled Runs, Security, Capabilities, Outputs
- **Context Budget section must explicitly list:**
  - **Parent-allowed tools:** dispatch subagents, read status files, present results to user, collect feedback, git operations, send email (via subagent dispatch)
  - **Subagent-only tools (parent MUST NOT call directly):** WebFetch, WebSearch, file reading of source/verified JSONs, search, filter, dedup logic, Python script execution (except ON STARTUP preflight)
- **Remove:** Full orchestration workflow (~325 lines) → now in `references/orchestration.md`
- **Remove:** Presentation rules (~86 lines) → now in `references/presentation-rules.md`
- **Add:** Phase dispatch table (~15 lines):
  | Phase | Entry Criteria | Exit Criteria | Load Reference |
  |-------|---------------|---------------|----------------|
  | Search | Session started, context.md loaded | Raw jobs in output/jobs/ | `references/orchestration.md` (Phase 1) |
  | Verify | Raw jobs exist | Verified JSONs in output/verified/ | `references/orchestration.md` (Phase 2) |
  | Dedup | Verified JSONs exist | Duplicates archived, <70 archived | `references/orchestration.md` (Phase 3) |
  | Present | Dedup complete | Tables shown, user feedback collected | `references/presentation-rules.md` |
  | Deliver | User approved selections | Briefs + digest email sent | `references/orchestration.md` (Phase 5) |
- **Update ON STARTUP:** Add `bash scripts/preflight.sh`, `python3 scripts/manage_state.py cleanup && python3 scripts/manage_state.py dedup`, validate Dashboard URL in context.md, read `.claude/agent-memory/*/MEMORY.md` files (V14/V17/V19 recurrence — HC4). Note: the `python3 scripts/manage_state.py` calls in ON STARTUP are executed by `preflight.sh` (not by the parent orchestrator directly). CLAUDE.md must not contain direct `python3 scripts/*` calls outside of the ON STARTUP block. Add verification: `grep -n "python3 scripts/" CLAUDE.md` results must only appear within the ON STARTUP section.
- **Add I9:** Read-before-Write on session-state to Core Rules
- **Add P2:** Post-compaction redispatch to Context Budget
- **Add P3:** Mandatory variable propagation to Hard Constraints
- **Add P8:** Regression enforcement escalation to Hard Constraints
- **Add P10:** Post-dispatch directory verification to Core Rules

**Verify:**
- Bash: `wc -l 03_agents/tests/v21/CLAUDE.md` — <=280
- Bash: `grep -q "## Hard Constraints" 03_agents/tests/v21/CLAUDE.md && grep -q "## Context Budget" 03_agents/tests/v21/CLAUDE.md && grep -q "## ON STARTUP" 03_agents/tests/v21/CLAUDE.md && echo "PASS" || echo "FAIL"` — PASS
- Bash: `grep -q "WebFetch" 03_agents/tests/v21/CLAUDE.md && echo "PASS: Context Budget lists subagent-only tools" || echo "FAIL: Context Budget missing subagent-only tool enumeration"` — PASS

#### Step 10: Commit Phase 2
```bash
cd 03_agents/tests/v21 && git add CLAUDE.md references/orchestration.md references/presentation-rules.md && git commit -m "feat(jsa-v21): Layer 1b — CLAUDE.md decomposition (676→~266 lines)"
```

**Verify:**
- Bash: `git log --oneline -1` — confirms commit

---

### Phase 3: GH Actions Config + Permissions (Layer 1c + I1-I3)

**Dependency:** Phase 1 complete (Phase 2 can run in parallel but we sequence for clean commits)

#### Step 11: Create .github/jsa-config.json
**File:** `03_agents/tests/v21/.github/jsa-config.json`
**Action:** Create

Standalone JSON config file extracted from the daily-digest.yml heredoc. Contains:
- All role definitions, search parameters, scoring weights
- Dashboard URL
- All configuration that was previously embedded in the YAML heredoc

**Expected top-level keys:** `agent` (version, model), `roles` (array of role objects), `scoring` (weights, thresholds), `dashboard` (url), `delivery` (email settings). Add schema validation to preflight.sh: verify these top-level keys exist and are non-empty.

**Verify:**
- Bash: `python3 -c "import json; json.load(open('03_agents/tests/v21/.github/jsa-config.json'))"` — valid JSON (schema validation deferred to preflight.sh as single config validation authority)

#### Step 12: Update daily-digest.yml
**File:** `03_agents/tests/v21/.github/workflows/daily-digest.yml`
**Action:** Modify

- Remove the heredoc JSON block
- Add: `config=$(cat .github/jsa-config.json)` to read config from file
- Add: step to create `settings.local.json` during CI setup (since it is gitignored and won't exist in CI) — copy from a template or generate with required permissions (V17/V19 regression)
- Add: `bash scripts/preflight.sh` step BEFORE the agent launch step
- Update the agent launch step to pass `$config` as the JSON payload

**Note:** This workflow file at `03_agents/tests/v21/.github/workflows/daily-digest.yml` is the development copy for V21 iteration. For production deployment, this workflow must be copied to the repo root `.github/workflows/` since GH Actions only recognizes workflows at that location (V17 regression). The nested path is used during development to avoid interfering with any existing production workflows.

**Verify:**
- Bash: `python3 -c "import yaml; yaml.safe_load(open('03_agents/tests/v21/.github/workflows/daily-digest.yml'))"` — valid YAML

#### Step 13: Update context.md with Dashboard URL
**File:** `03_agents/tests/v21/context.md`
**Action:** Modify

Add Dashboard URL to `## Delivery` section:
```
Dashboard: https://jsa-dashboard.vercel.app/#digest
```

**Copy spec:**
- Section heading: "## Delivery"
- Dashboard label: "Dashboard: https://jsa-dashboard.vercel.app/#digest"

**Verify:**
- Bash: `grep -q "Dashboard:" 03_agents/tests/v21/context.md && echo "present"` — present

#### Step 14: Update settings.local.json with permissions (additive merge)
**File:** `03_agents/tests/v21/.claude/settings.local.json`
**Action:** Modify

Read existing `settings.local.json`, merge new permissions into existing `allow` array, write back. Do NOT overwrite the file. New entries to add to the `allow` array:
- `python3 scripts/*` — allow execution of any script in scripts/
- `bash scripts/*` — allow bash execution of scripts

Additionally, add Claude Code tool permissions for background subagent operation (V20 regression: background subagents need explicit tool access):
- `Read` — file reading tool
- `Write` — file writing tool
- `Glob` — file pattern matching tool
- `Grep` — content search tool

**Merge strategy:** Read existing JSON, parse the `allow` array, append new permission entries, write back. Verify that the resulting `allow` array length >= pre-modification length (existing permissions must not be removed).

**Verify:**
- Bash: `python3 -c "import json; d=json.load(open('03_agents/tests/v21/.claude/settings.local.json')); a=d.get('permissions',{}).get('allow',[])+d.get('allowedTools',[]); print('ok' if any('scripts/*' in str(v) for v in a) else 'missing')"` — ok
- Bash: `python3 -c "import json; d=json.load(open('03_agents/tests/v21/.claude/settings.local.json')); a=d.get('permissions',{}).get('allow',[])+d.get('allowedTools',[]); print(f'permissions count: {len(a)}')"` — count must be >= pre-existing count

#### Step 15: Commit Phase 3
```bash
cd 03_agents/tests/v21 && git add .github/jsa-config.json .github/workflows/daily-digest.yml context.md .claude/settings.local.json && git commit -m "feat(jsa-v21): Layer 1c — GH Actions config file + permissions + dashboard URL"
```

**Verify:**
- Bash: `git log --oneline -1` — confirms commit

---

### Phase 4: Subagent Proposal Promotion (Layer 2b)

**Dependency:** Phase 2 complete (CLAUDE.md decomposed, reference files exist)

#### Step 16: Update references/subagent-search-verify.md with speed optimization
**File:** `03_agents/tests/v21/references/subagent-search-verify.md`
**Action:** Modify (if exists; create from `.claude/skills/jsa-search-verify.md` content otherwise)

Apply I10 speed optimization:
- Keep full listing analysis for fit scoring
- Drop external company lookups (Crunchbase, hiring manager, funding rounds)
- Move deep company research to brief phase for top-scoring jobs only
- Target <120s per job verification

Apply P1 (Foreground Fallback Guard):
- If foreground dispatch fails, retry once. If retry fails, log the failure and continue (don't block the pipeline).

**Verify:**
- Bash: `grep -q "Crunchbase" 03_agents/tests/v21/references/subagent-search-verify.md && echo "FAIL: still has Crunchbase" || echo "PASS"` — PASS (Crunchbase removed)

#### Step 17: Create/update references/subagent-digest-email.md with idempotent gate
**File:** `03_agents/tests/v21/references/subagent-digest-email.md`
**Action:** Modify (if exists; create otherwise)

Apply P4 (Idempotent Email Gate):
- Before sending, check if `output/digests/_status.json` has `email_sent: true` for today's date
- If already sent, skip sending and log "Email already sent for [date]"
- After successful send, write `email_sent: true` with timestamp to `_status.json`

**Copy spec:**
- Skip message: "Email already sent for {date}. Skipping."
- Success message: "Digest email sent successfully for {date}."

**Verify:**
- Bash: `grep -qi "idempotent\|already sent\|email_sent" 03_agents/tests/v21/references/subagent-digest-email.md && echo "present"` — present

#### Step 18: Commit Phase 4
```bash
cd 03_agents/tests/v21 && git add references/ && git commit -m "feat(jsa-v21): Layer 2b — subagent proposal promotion (P1, P4, I10)"
```

**Verify:**
- Bash: `git log --oneline -1` — confirms commit

---

### Phase 5: Validation Harness (Layer 3)

**Dependency:** Phase 2, Phase 3, Phase 4 complete

#### Step 19: Write failing tests for preflight.sh
**File:** `03_agents/tests/v21/tests/test_preflight.py`
**Action:** Create

Tests that invoke preflight.sh via subprocess and check exit codes/output:
- `test_preflight_passes_when_all_present` — All required files present, exits 0
- `test_preflight_fails_missing_dashboard_url` — context.md missing Dashboard URL, exits 1 with error message
- `test_preflight_fails_missing_permissions` — settings.local.json missing required permissions, exits 1
- `test_preflight_fails_invalid_config_json` — .github/jsa-config.json is invalid JSON, exits 1
- `test_preflight_fails_missing_manage_state` — scripts/manage_state.py doesn't exist, exits 1
- `test_preflight_warns_empty_agent_memory` — agent-memory files empty, exits 0 with warning
- `test_preflight_warns_missing_reference_files` — references/ missing expected files, exits 0 with warning
- `test_preflight_idempotent` — Running twice produces same result
- `test_preflight_runs_manage_state_cleanup_and_dedup` — After critical checks pass, preflight.sh invokes `python3 scripts/manage_state.py cleanup` and `python3 scripts/manage_state.py dedup`
- `test_preflight_env_only_skips_structure_checks` — `preflight.sh --env` runs environment/runtime checks but does NOT run CLAUDE.md structure checks (verify structure failure does not cause exit 1 when only `--env` is passed)
- `test_preflight_structure_only_skips_env_checks` — `preflight.sh --structure` runs CLAUDE.md/reference structural checks but does NOT run environment checks (verify env failure does not cause exit 1 when only `--structure` is passed)

**Copy spec:**
- Critical failure messages:
  - "CRITICAL: Dashboard URL missing from context.md"
  - "CRITICAL: Required permissions missing from settings.local.json"
  - "CRITICAL: .github/jsa-config.json is invalid JSON"
  - "CRITICAL: scripts/manage_state.py not found or not executable"
- Warning messages:
  - "WARNING: Agent memory files are empty"
  - "WARNING: Missing reference files: {list}"

**Verify:**
- Test: `cd 03_agents/tests/v21 && python -m pytest tests/test_preflight.py -v` — all tests FAIL
- Lint: `ruff check 03_agents/tests/v21/tests/test_preflight.py`

#### Step 20: Implement preflight.sh
**File:** `03_agents/tests/v21/scripts/preflight.sh`
**Action:** Create

Bash script with flag-based dispatch: `preflight.sh --env` runs only environment/runtime checks, `preflight.sh --structure` runs only CLAUDE.md/reference structural checks, `preflight.sh` (no flag) runs all tiers. This separates build-time structural linting from runtime prerequisites.

Tiers:
- **Critical checks (exit 1 on failure):**
  1. Dashboard URL present in context.md (`grep -q "Dashboard:" context.md`)
  2. settings.local.json has required permissions
  3. .github/jsa-config.json exists and is valid JSON (`python3 -c "import json; json.load(open('.github/jsa-config.json'))"`)
  4. scripts/manage_state.py exists and is executable
- **ON STARTUP state management (run after critical checks pass):**
  1. `python3 scripts/manage_state.py cleanup` — remove stale temp directories
  2. `python3 scripts/manage_state.py dedup` — deduplicate verified jobs
- **Critical CLAUDE.md structure checks (exit 1 on failure):**
  1. CLAUDE.md <=280 lines
  2. Required sections exist: `## Hard Constraints`, `## Context Budget`, `## Core Rules`, `## ON STARTUP`
  3. Phase dispatch table has 5 phases (Search, Verify, Dedup, Present, Deliver)
  4. Each dispatch row references a `references/*.md` file
  5. ON STARTUP references `preflight.sh` and `manage_state.py`
- **Critical reference file content checks (exit 1 on failure):**
  1. `references/orchestration.md` contains phase headings for all 5 phases
  2. `references/presentation-rules.md` contains table format section
- **CLI flag validation (exit 1 on failure):**
  1. `python3 scripts/manage_state.py dedup --dry-run --verified-dir output/verified --archive-dir output/archive` exits 0 — validates flags actually work via direct invocation rather than parsing help text (help text is not a stable interface)
- **Non-critical checks (warn but continue):**
  1. .claude/agent-memory/ files are non-empty
  2. references/ files exist for all phases (orchestration.md, presentation-rules.md, subagent-*.md)
  3. No stale version references in GH Actions workflow

Script uses the copy spec messages exactly. Exits 0 if all critical checks pass (warnings don't affect exit code).

**Verify:**
- Test: `cd 03_agents/tests/v21 && python -m pytest tests/test_preflight.py -v` — all tests PASS
- Bash: `bash 03_agents/tests/v21/scripts/preflight.sh` — runs without error (from v21 dir)

#### Step 21: Run full test suite
**Action:** Verify (no file changes)

Run ALL tests across V21 to ensure nothing is broken:

**Verify:**
- Test: `cd 03_agents/tests/v21 && python -m pytest tests/ -v` — all tests PASS
- Lint: `ruff check 03_agents/tests/v21/scripts/ 03_agents/tests/v21/tests/`

#### Step 22: Commit Phase 5
```bash
cd 03_agents/tests/v21 && git add scripts/preflight.sh tests/test_preflight.py && git commit -m "feat(jsa-v21): Layer 3 — preflight.sh validation harness with tests"
```

**Verify:**
- Bash: `git log --oneline -1` — confirms commit

---

## Deployment Verification

### Pre-Deploy Checks

Preflight.sh handles all structural and content validation. Pre-deploy runs preflight + tests + lint:

```bash
cd 03_agents/tests/v21

# Preflight validates structure, content, config, permissions
bash scripts/preflight.sh

# Lint all Python files
ruff check scripts/ tests/

# Run full test suite
python3 -m pytest tests/ -v
```

### Post-Deploy Smoke Test

```bash
cd 03_agents/tests/v21

# Run preflight (same as agent ON STARTUP)
bash scripts/preflight.sh

# Validate manage_state.py CLI responds
python3 scripts/manage_state.py cleanup --dry-run
python3 scripts/manage_state.py dedup --verified-dir output/verified --archive-dir output/archive --dry-run
```

### Rollback Plan

```bash
cd /Users/ryanhennebry/Projects/autonomous1

# Option 1: Revert all V21 commits (if V21 was multi-commit)
git log --oneline --all | grep "jsa-v21" | head -5  # identify commits
git revert --no-commit <oldest-v21-commit>..HEAD
git commit -m "revert(jsa-v21): rollback V21 changes"

# Option 2: Delete V21 directory entirely (V20 is untouched)
rm -rf 03_agents/tests/v21
git add -A && git commit -m "revert(jsa-v21): remove V21 directory"

# Verify rollback
test ! -d 03_agents/tests/v21 && echo "V21 removed"
# OR if keeping V21 but reverting:
wc -l 03_agents/tests/v21/CLAUDE.md  # Should return to 676
```

---

## Handoff Contract
- Total steps: 22, Total phases: 5
- Files created: `scripts/manage_state.py` (rewrite), `scripts/preflight.sh`, `.github/jsa-config.json`, `references/orchestration.md`, `references/presentation-rules.md`, `tests/test_manage_state.py` (merged cleanup+dedup), `tests/test_preflight.py`
- Files modified: `CLAUDE.md`, `.github/workflows/daily-digest.yml`, `.claude/settings.local.json`, `context.md`, `references/subagent-search-verify.md`, `references/subagent-digest-email.md`
- Verification sequence: Phase 1 (manage_state tests) → Phase 2 (structure tests) → Phase 3 (config + permissions) → Phase 4 (subagent refs) → Phase 5 (preflight tests + full suite)
- Deployment verification: pre-deploy, post-deploy, rollback — all present
- Layer mapping: Phase 1 = Layer 1a, Phase 2 = Layer 1b, Phase 3 = Layer 1c + I1-I3, Phase 4 = Layer 2b, Phase 5 = Layer 3
- Note: Layer 2a proposals (P2, P3, P8, P10) are integrated into Step 9 (CLAUDE.md decomposition) since they target the parent CLAUDE.md. Layer 2c implementation constraints are distributed across Steps 9 (I4, I9), 4 (I5, I7), 7-8 (I6, I8), 16 (I10), and 14 (I3). I2 is resolved by Step 11-12 (config file). P5 checkpoint JSON protocol dropped per review (session-state.md used instead). test_claude_md_structure.py removed — structure checks merged into preflight.sh. test_manage_state_cleanup.py and test_manage_state_dedup.py merged into single test_manage_state.py. pre-run subcommand removed — ON STARTUP uses explicit cleanup && dedup.

<!-- STAGE COMPLETE: /plan, 2026-02-19 -->

<!-- STAGE COMPLETE: /revise after round 1, 2026-02-19 -->

<!-- STAGE COMPLETE: /revise after round 2, 2026-02-19 -->

<!-- STAGE COMPLETE: /revise after round 3, 2026-02-19 -->

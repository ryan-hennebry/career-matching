# Plan: JSA V23 — Enforcement Gates + Cost Reduction

## Overview

V23 implements 6 fixes from V22 analysis using a Three-Layer architecture (Scripts → Orchestration+Config → Validation). The build step will first copy V22 → V23, then apply changes to the V23 directory.

**Key changes:**
- Context-aware dedup (`--role-types` flag) to prevent false archives
- Commit gate (`verify-clean-working-tree`) to block uncommitted changes between batches (per-channel enforcement)
- Session-state gate (`verify-session-state-updated`) to enforce session-state.md writes after each batch
- 5-channel search mandate with verification (`verify-channels-dispatched`)
- Model tiering (Haiku/Sonnet) to cut run cost from $4+ to <$1
- Preflight validation: shell-native checks in preflight.sh (git pull, agent-memory read) + Python-backed checks called by orchestrator/gate-check subagent directly (session resume guard, model setting check, dashboard URL)

**Base directory:** `03_agents/tests/v23/` (copied from V22 at build start)

## Files to Modify

### Layer 1: Script Enforcement
- `scripts/manage_state.py` — Add 5 new subcommands: `dedup --role-types`, `list-active-role-types` (parses context.md `## Target` to extract active role-type slugs), `verify-clean-working-tree` (checks no uncommitted changes in output/verified/), `verify-channels-dispatched`, `verify-session-state-updated`. Group verify-* subcommands under a `verify` subparser and check-* subcommands under a `check` subparser for discoverability (e.g., `manage_state.py verify clean-working-tree`, `manage_state.py check session-resume`).
- `tests/test_manage_state_dedup.py` — New tests for scoped dedup
- `tests/test_manage_state.py` — New tests for list-active-role-types, verify-clean-working-tree, verify-channels-dispatched, and verify-session-state-updated

### Layer 2: Orchestration + Configuration
- `CLAUDE.md` — Reverse Hard Constraint 1 (model: inherit → explicit model tiering)
- `.claude/agents/search-verify.md` — Add `model: haiku`
- `.claude/agents/source-researcher.md` — Add `model: haiku`
- `.claude/agents/brief-generator.md` — Add `model: sonnet`
- `.claude/agents/digest-email.md` — Add `model: sonnet`
- `.claude/agents/briefs-html.md` — Add `model: sonnet`
- `.claude/agents/onboarding.md` — Add `model: sonnet`
- `.claude/agents/gate-check.md` — New agent file with `model: haiku` for mechanical gate verification work
- `references/orchestration.md` — Add Context Budget section + rewrite Phase 1 with 5-channel mandate + commit/channel/session-state gates
- `context.md` — Add `## Search Channels` section

### Layer 3: Validation + Preflight
- `scripts/manage_state.py` — Add 3 preflight subcommands under `check` subparser: check-session-resume, check-model-settings, check-dashboard-url
- `tests/test_manage_state_preflight.py` — New test file for preflight subcommands (10 tests — single test layer per check, no duplicate coverage in test_preflight.py)
- `scripts/preflight.sh` — Add 2 shell-native checks: git pull, agent-memory startup read. (3 Python-backed checks — session resume, model settings, dashboard URL — are called by orchestrator/gate-check subagent via `manage_state.py check-*` subcommands directly, not wrapped by preflight.sh)
- `tests/test_preflight.py` — Existing test file, add 4 new tests for the 2 shell-native checks

### Layer 4: Deployment
- `.github/workflows/daily-digest.yml` — Update to V23 paths + SCHEDULED_RUN + settings.local.json
- `scripts/verify_deploy.sh` — Consolidated deployment verification script

## Implementation Steps

### Phase 0: Setup

#### Step 0.1: Copy V22 → V23
**File:** `03_agents/tests/v23/` (entire directory)
**Action:** Create
**Description:** Copy entire V22 directory to V23. Remove output data (jobs, verified, briefs, digests, archive) — only code/config carries forward.
**Verify:**
- Lint: N/A (copy operation)
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/ -v` (all 132 existing tests pass on copied codebase)

---

### Phase 1: Layer 1 — Script Enforcement (manage_state.py + tests)

#### Step 1.1: Write failing test for `dedup --role-types`
**File:** `tests/test_manage_state_dedup.py`
**Action:** Modify (add new test cases)
**Description:** Add 9 test cases in class `TestDedupRoleTypes`:
1. `test_role_types_filters_to_specified_dirs` — low-score job in included role archived, excluded role untouched
2. `test_role_types_multiple_slugs` — comma-separated slugs all processed
3. `test_role_types_omitted_processes_all` — backward compatibility, all dirs processed
4. `test_role_types_cross_role_dedup_scoped` — cross-role dedup limited to included roles only
5. `test_role_types_cross_role_dedup_both_included` — when both roles included, normal cross-role dedup applies
6. `test_role_types_empty_string_processes_none` — empty string = no processing
7. `test_role_types_summary_reflects_scoped_counts` — JSON output `total_input` counts only scoped roles
8. `test_pre_search_archival_preserves_state_json_referenced_dirs` — a directory whose role-type slug is NOT in the active list but IS referenced by an active state.json entry is preserved (not archived). Verifies the cross-reference path between archival logic and state.json.
9. `test_within_role_url_dedup` — two jobs with identical URLs but different scores in the same role directory are deduplicated (only higher-scored entry retained). Validates V20 within-role URL-based dedup survives the V22 copy.

Tests invoke `manage_state.py dedup --role-types <slugs>` via subprocess, using `tmp_path` with mock verified directories containing test JSON files.
**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state_dedup.py::TestDedupRoleTypes -v` (new tests FAIL — feature not implemented)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check tests/test_manage_state_dedup.py`

#### Step 1.2: Implement `dedup --role-types` in manage_state.py
**File:** `scripts/manage_state.py`
**Action:** Modify
**Description:** Three changes to manage_state.py:
1. Modify `_load_verified_jobs()` to accept optional `role_types: list[str] | None` parameter. When provided, only scan subdirectories whose names appear in the list. When `None`, scan all (backward compatible).
2. Modify `_cli_dedup()` to parse `args.role_types` (comma-separated string) into a list and pass to `_load_verified_jobs()`. Empty string = process nothing.
3. Add `--role-types` argument to the dedup subparser: `dedup_parser.add_argument("--role-types", type=str, default=None, help="Comma-separated role type slugs to process")`
**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state_dedup.py -v` (all 9 new + existing tests PASS)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check scripts/manage_state.py`

#### Step 1.2a: Write failing test for `list-active-role-types`
**File:** `tests/test_manage_state.py`
**Action:** Modify (add new test class at end of file)
**Description:** Add class `TestListActiveRoleTypes` with 4 tests:
1. `test_extracts_role_types_from_target_section` — context.md with `## Target` containing role types returns newline-separated slugs, exit 0
2. `test_returns_empty_when_no_target_section` — context.md without `## Target` section returns empty output, exit 0
3. `test_handles_multiple_role_types` — context.md with multiple role types listed returns all of them
4. `test_exits_one_when_context_file_missing` — nonexistent context path, exit 1 with error message

Tests use `tmp_path` with mock context.md files. Invokes `manage_state.py list-active-role-types --context-path <path>` via subprocess.
**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state.py::TestListActiveRoleTypes -v` (new tests FAIL — feature not implemented)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check tests/test_manage_state.py`

#### Step 1.2b: Implement `list-active-role-types` in manage_state.py
**File:** `scripts/manage_state.py`
**Action:** Modify
**Description:** Add `_cli_list_active_role_types(args)` function that:
1. Reads the file at `args.context_path`
2. Parses the `## Target` section to extract active role-type slugs (the slug for each role type, e.g., `ai-agent-engineer`, `crypto-defi-ops`)
3. Prints each slug on a separate line to stdout
4. Exits 0 on success, exits 1 if context file not found

Add CLI subparser `list-active-role-types` with `--context-path` argument (default: `context.md`).

This is the single authoritative extraction mechanism referenced by Step 2.4 item 10. Both pre-search archival and `dedup --role-types` MUST consume the same list from this subcommand.
**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state.py::TestListActiveRoleTypes -v` (PASS)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check scripts/manage_state.py`

#### Step 1.3: Write failing test for `verify-clean-working-tree`
**File:** `tests/test_manage_state.py`
**Action:** Modify (add new test class at end of file)
**Description:** Add class `TestVerifyCleanWorkingTree` with 4 tests:
1. `test_clean_repo_exits_zero` — all files committed in a git repo, exit 0
2. `test_uncommitted_files_exit_one` — untracked files in output/verified/, exit 1
3. `test_modified_file_exit_one` — modified committed file, exit 1
4. `test_empty_verified_dir_exits_zero` — no verified dir, exit 0

Tests use `tmp_path`, initialize a git repo with `git init && git add . && git commit`, then invoke `manage_state.py verify-clean-working-tree --verified-path <path>` via subprocess.

**Enforcement note:** `verify-clean-working-tree` is invoked per-channel (after each search-verify subagent returns), not just end-of-phase. This enforces incremental commit+push after each channel completes, preventing the 7-version recurring regression (V14-V22) of uncommitted changes accumulating across batches.

**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state.py::TestVerifyCleanWorkingTree -v` (new tests FAIL)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check tests/test_manage_state.py`

#### Step 1.4: Implement `verify-clean-working-tree` in manage_state.py
**File:** `scripts/manage_state.py`
**Action:** Modify
**Description:** Add `import subprocess` to imports. Add `_cli_verify_batch_committed(args)` function that runs `subprocess.run(["git", "status", "--porcelain", args.verified_path], capture_output=True, text=True)`. If stdout is non-empty, print the uncommitted files and `sys.exit(1)`. Otherwise exit 0. Add CLI subparser `verify-clean-working-tree` with `--verified-path` argument (default: `output/verified`).

**Blocking enforcement:** This gate is called by a subagent (not the parent directly — see Context Budget in Step 2.3). The parent dispatches a gate-check subagent after each channel's search-verify subagent returns. The gate subagent runs `manage_state.py verify-clean-working-tree` and reports pass/fail. If fail, the parent halts dispatch of subsequent channels until the commit is landed. This is a code-level blocking mechanism, not documentation-only.

**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state.py::TestVerifyCleanWorkingTree -v` (PASS)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check scripts/manage_state.py`

#### Step 1.5: Write failing test for `verify-channels-dispatched`
**File:** `tests/test_manage_state.py`
**Action:** Modify (add new test class at end of file)
**Description:** Add class `TestVerifyChannelsDispatched` with 4 tests:
1. `test_all_channels_present_exits_zero` — all 5 `.done` files with today's mtime, exit 0
2. `test_missing_channel_exits_one` — 4 of 5 `.done` files present, exit 1 naming missing channel
3. `test_stale_mtime_exits_one` — one `.done` file with yesterday's mtime, exit 1
4. `test_no_channels_dir_exits_one` — no `.channels/` directory, exit 1 with all 5 named

Each search subagent writes a `.done` file to `.channels/{channel-name}.done` on completion. The verify command checks that all 5 `.done` files exist with today's mtime. No JSON parsing required.

Expected channel names: `direct-career-pages`, `industry-job-boards`, `jobspy-aggregator`, `niche-newsletters`, `web-search-discovery`. Invokes `manage_state.py verify-channels-dispatched --output-dir <path> --run-date <YYYY-MM-DD>`.
**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state.py::TestVerifyChannelsDispatched -v` (FAIL)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check tests/test_manage_state.py`

#### Step 1.6: Implement `verify-channels-dispatched` in manage_state.py
**File:** `scripts/manage_state.py`
**Action:** Modify
**Description:** Add `_cli_verify_channels_dispatched(args)` function. Required channel names: `["direct-career-pages", "industry-job-boards", "jobspy-aggregator", "niche-newsletters", "web-search-discovery"]`. For each:
1. Check `{args.output_dir}/.channels/{channel}.done` exists
2. Check file mtime date matches `args.run_date`
3. If any channel `.done` file missing or stale mtime → collect errors and exit 1 with details
4. If all valid → exit 0

No JSON parsing — each search subagent writes a simple `.done` file on completion, and the verify command checks existence + today's mtime.

Add CLI subparser `verify-channels-dispatched` with `--output-dir` (default: `output`) and `--run-date` (default: today's date) arguments.
**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state.py::TestVerifyChannelsDispatched -v` (PASS)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check scripts/manage_state.py`

#### Step 1.7: Write failing test for `verify-session-state-updated`
**File:** `tests/test_manage_state.py`
**Action:** Modify (add new test class at end of file)
**Description:** Add class `TestVerifySessionStateUpdated` with 3 tests:
1. `test_session_state_modified_today_exits_zero` — `session-state.md` mtime is today, exit 0
2. `test_session_state_stale_exits_one` — `session-state.md` mtime is yesterday, exit 1
3. `test_session_state_missing_exits_one` — no `session-state.md` file, exit 1

Tests use `tmp_path` with mock session-state.md. Invokes `manage_state.py verify-session-state-updated --session-state-path <path> --run-date <YYYY-MM-DD>`.
**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state.py::TestVerifySessionStateUpdated -v` (FAIL)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check tests/test_manage_state.py`

#### Step 1.8: Implement `verify-session-state-updated` in manage_state.py
**File:** `scripts/manage_state.py`
**Action:** Modify
**Description:** Add `_cli_verify_session_state_updated(args)` function that checks `session-state.md` at `args.session_state_path` exists and has an mtime date matching `args.run_date`. If missing or stale, print error and `sys.exit(1)`. Otherwise exit 0. Add CLI subparser `verify-session-state-updated` with `--session-state-path` (default: `session-state.md`) and `--run-date` (default: today's date) arguments.

**Enforcement note:** This gate is invoked after each search batch (same timing as `verify-clean-working-tree`) to enforce session-state.md writes. 6-version recurrence (V14/V16/V18/V19/V21/V22) demands structural enforcement, not documentation.

**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state.py::TestVerifySessionStateUpdated -v` (PASS)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check scripts/manage_state.py`

#### Step 1.9: Run full test suite — confirm no regressions
**Description:** Run all existing + new tests to confirm nothing is broken.
**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/ -v`
- Lint: `cd 03_agents/tests/v23 && python -m ruff check scripts/ tests/`

#### Step 1.10: Commit Layer 1
**Description:** Stage and commit all Layer 1 changes.
```bash
git add 03_agents/tests/v23/scripts/manage_state.py 03_agents/tests/v23/tests/test_manage_state.py 03_agents/tests/v23/tests/test_manage_state_dedup.py
git commit -m "feat(jsa): V23 Layer 1 — dedup --role-types, verify-clean-working-tree, verify-channels-dispatched, verify-session-state-updated"
```

---

### Phase 2: Layer 2 — Orchestration + Configuration

#### Step 2.1: Reverse HC1 in CLAUDE.md
**File:** `CLAUDE.md`
**Action:** Modify (two edits)

**V19 regression supersession note:** V19 regression item forbids passing `model:` to the Task tool. This is intentionally superseded by V23's model-tiering design decision (MEMORY.md "V23 Required Improvement: Cost Reduction"). The regression file (`.claude/regressions/jsa.md`) must be updated after build to mark the V19 HC1 item as superseded by V23, with rationale: "Cost reduction requires explicit model tiering; Opus for all subagents costs $4+/run."

**Edit 1 — Replace HC1 text:**
Find: `1. **Never pass \`model:\` to Task tool.** Named agents inherit model from parent via \`model: inherit\` in their frontmatter. Never include \`model:\` as a key in the JSON or as a Task tool parameter.`
Replace with: `1. **Pass \`model:\` to Task tool matching the agent's designated tier.** Each subagent has an assigned model tier in its frontmatter. When dispatching via Task tool, pass the matching \`model:\` value. See **Agent Model Tiers** below.`

**Note on settings.local.json:** Model tiering is implemented via agent frontmatter and Task tool `model:` parameter, NOT via settings.local.json changes. No settings.local.json modifications are needed for this feature (V18 regression: settings changes must be additive).

**Edit 2 — Insert Agent Model Tiers section:**
Find the `---` separator before `## Context Budget` and insert the following section between them:

```markdown
## Agent Model Tiers

Cost-tiered model assignment. Parent orchestrator runs on Opus (inherited from CLI session). Subagents use the cheapest model that can do the job.

| Tier | Model Value | Agents | Rationale |
|------|-------------|--------|-----------|
| Opus | _(parent only)_ | Parent orchestrator | Orchestration decisions, user interaction, context management |
| Sonnet | `sonnet` | brief-generator, digest-email, briefs-html, onboarding | Good writing quality, template-following — does not need Opus-level reasoning |
| Haiku | `haiku` | search-verify, source-researcher, gate-check | Mechanical work: fetch pages, filter, score against rubric, extract structured data, run verification gates |

**Enforcement:** If a subagent dispatch omits `model:`, the default (Opus) runs — wasting budget. Every Task tool dispatch MUST include the `model:` key matching the agent's tier from the table above.

**Source of truth:** Agent frontmatter `model:` field is the source of truth for tier assignment. This table is a summary — if it drifts, agent frontmatter wins.
```

**Verify:**
- Test: `grep "Pass.*model.*to Task tool" 03_agents/tests/v23/CLAUDE.md` (should match)
- Test: `grep "Agent Model Tiers" 03_agents/tests/v23/CLAUDE.md` (should match)
- Lint: N/A (markdown)

#### Step 2.2: Add model tiers to agent frontmatter + create gate-check agent
**Files:** `.claude/agents/search-verify.md`, `.claude/agents/source-researcher.md`, `.claude/agents/brief-generator.md`, `.claude/agents/digest-email.md`, `.claude/agents/briefs-html.md`, `.claude/agents/onboarding.md`, `.claude/agents/gate-check.md`
**Action:** Modify (6 files) + Create (1 file)
**Description:** In each existing agent's YAML frontmatter, find the line `model: inherit` and replace with the designated tier. All 6 files currently have `model: inherit` in their frontmatter. Additionally, create a new `gate-check.md` agent file for mechanical gate verification work.

| File | Find | Replace |
|------|------|---------|
| `.claude/agents/search-verify.md` | `model: inherit` | `model: haiku` |
| `.claude/agents/source-researcher.md` | `model: inherit` | `model: haiku` |
| `.claude/agents/brief-generator.md` | `model: inherit` | `model: sonnet` |
| `.claude/agents/digest-email.md` | `model: inherit` | `model: sonnet` |
| `.claude/agents/briefs-html.md` | `model: inherit` | `model: sonnet` |
| `.claude/agents/onboarding.md` | `model: inherit` | `model: sonnet` |
| `.claude/agents/gate-check.md` | _(new file)_ | `model: haiku` |

**gate-check.md:** Create with YAML frontmatter containing `model: haiku`. Purpose: executes mechanical gate checks (`verify-clean-working-tree`, `verify-channels-dispatched`, `verify-session-state-updated`, `check-session-resume`, `check-model-settings`, `check-dashboard-url`) on behalf of the parent orchestrator. Purely mechanical work — runs manage_state.py subcommands and reports pass/fail.

**Verify:**
- Test: `cd 03_agents/tests/v23 && grep -l "model: inherit" .claude/agents/*.md | wc -l` (should return 0 — no agents with inherit)
- Test: `cd 03_agents/tests/v23 && grep "model: " .claude/agents/{search-verify,source-researcher,brief-generator,digest-email,briefs-html,onboarding,gate-check}.md | wc -l` (should return 7)
- Lint: N/A (markdown frontmatter)

#### Step 2.3: Add Context Budget section to orchestration.md
**File:** `references/orchestration.md`
**Action:** Modify (add Context Budget section at top of file, before Phase 1)
**Description:** Add a `## Context Budget` section explicitly listing parent-callable tools vs subagent-only:

```markdown
## Context Budget

**Parent-callable tools (direct):**
- Task (dispatch subagents)
- Read (status files, session-state.md, _dashboard.md ONLY)
- git add, git commit, git push (via Bash)

**Subagent-only tools (NEVER called by parent):**
- All `manage_state.py` subcommands (dedup, verify-clean-working-tree, verify-channels-dispatched, verify-session-state-updated)
- WebFetch, WebSearch
- All script execution (python3 scripts/*)
- Write (source files, output files)

**Gate execution:** All verification gates (`verify-clean-working-tree`, `verify-channels-dispatched`, `verify-session-state-updated`) are invoked by a gate-check subagent dispatched by the parent. The parent reads the subagent's pass/fail result from its status output. The parent NEVER runs `python scripts/manage_state.py` directly.
```

**Verify:**
- `grep "Context Budget" 03_agents/tests/v23/references/orchestration.md` (should match)

#### Step 2.4: Rewrite orchestration.md Phase 1 with 5-channel mandate
**File:** `references/orchestration.md`
**Action:** Modify (replace entire `## Phase 1: Search` section)
**Description:** Replace the existing Phase 1 section (from `## Phase 1: Search` up to but not including `## Phase 2`) with the 5-channel mandate version. Key structural changes:

1. **Section heading**: `## Phase 1: Search` with subtitle "5-channel parallel search with enforcement gates. Every run dispatches ALL 5 channels — no channel is optional."
2. **Pre-search cleanup step**: Before dispatching channels, archive any role-type directories in `output/verified/` that are NOT in the active `--role-types` list. Defense in depth: prevents V22 stale-directory failure even if `--role-types` flag is accidentally omitted from dedup later. Archival runs ONLY before search begins, never mid-phase. **Note:** If state.json consistency with archived directories matters, handle it in a separate dedicated step after archival (do not compound this conditional with the archival logic).
3. **5 Search Channels table**: Fixed infrastructure — Direct Career Pages, Industry Job Boards, JobSpy Aggregator, Niche Newsletters, Web Search Discovery. All use `search-verify` subagent with `model: haiku`.
4. **Source research gate**: Check `## Search Channels` in context.md (renamed from `## Sources`).
5. **Channel-specific JSON blobs**: Common variables include `working_dir: /absolute/path/to/v23/`, `output_directory`, and `dashboard_url` (HC10 mandatory). Channel-specific additions: sources list for ch1-2, queries for ch3-5. Each search subagent writes a `.done` file to `.channels/{channel-name}.done` on completion.
6. **Parallel dispatch**: All 5 channels dispatched in a SINGLE message (parallel execution). No sequential batching of channels.
7. **Per-channel Batch Commit Gate** (MANDATORY): After EACH channel's search-verify subagent returns, the parent dispatches a gate-check subagent that runs `git add && git commit && git push`, then `manage_state.py verify-clean-working-tree`. Gate fails → parent halts until resolved. This enforces incremental commits per-channel (not just end-of-phase).
8. **Per-channel Session-State Gate** (MANDATORY): Same timing as commit gate — a gate-check subagent confirms `session-state.md` was updated after each channel completes, via `manage_state.py verify-session-state-updated`.
9. **Channel Verification Gate** (MANDATORY): After all 5 return, a gate-check subagent runs `manage_state.py verify-channels-dispatched`. Gate fails if any channel has no `.done` file — re-dispatch that channel (max 1 retry).
10. **Active role-types source of truth**: The single authoritative source for the active role-type slugs is `context.md ## Target` (the role types the user is currently searching for). The extraction mechanism is `manage_state.py list-active-role-types --context-path context.md`, which parses the Target section and returns the slug list. Both pre-search archival (item 2) and `dedup --role-types` (Step 1.2) MUST consume the same list from this single source.
11. **Updated exit criteria**: All 5 channels dispatched and reported, all per-channel commit+session-state gates passed, channel verification gate passed, batch commit landed.

**Copy spec:**
- Channel dispatch section heading: "5 Search Channels (ALL MANDATORY)"
- Gate after each channel: "Per-Channel Commit Gate (MANDATORY)" and "Per-Channel Session-State Gate (MANDATORY)"
- Gate after all channels: "Channel Verification Gate (MANDATORY)"
- Channel names (exact): "Direct Career Pages", "Industry Job Boards", "JobSpy Aggregator", "Niche Newsletters", "Web Search Discovery"
- Channel dispatch summary table headings: "Channel", "Status", "Jobs Found"
- Mandatory dispatch JSON fields: `working_dir`, `output_directory`, `dashboard_url`, `model`

**Verify:**
- `grep "5 Search Channels" 03_agents/tests/v23/references/orchestration.md` (should match)
- `grep "verify-channels-dispatched" 03_agents/tests/v23/references/orchestration.md` (should match)
- `grep "verify-clean-working-tree" 03_agents/tests/v23/references/orchestration.md` (should match)
- `grep "verify-session-state-updated" 03_agents/tests/v23/references/orchestration.md` (should match)
- `grep "Context Budget" 03_agents/tests/v23/references/orchestration.md` (should match)
- `grep -c "Direct Career Pages\|Industry Job Boards\|JobSpy Aggregator\|Niche Newsletters\|Web Search Discovery" 03_agents/tests/v23/references/orchestration.md` (should be >= 5)
- `grep "output_directory\|dashboard_url\|working_dir" 03_agents/tests/v23/references/orchestration.md` (should match all 3)

#### Step 2.5: Add Search Channels section to context.md
**File:** `context.md`
**Action:** Modify (insert before `## Scoring & Algorithms`)
**Description:** Insert a `## Search Channels` section immediately before the existing `## Scoring & Algorithms` section. Content:

**`### Direct Career Pages`** — Table of companies with career URLs. Populate from current context.md `## Industries` and `## Target` at build time — do not hardcode company names in the plan.

**`### Industry Job Boards`** — Table of industry-relevant boards. Populate from current context.md `## Industries` at build time — boards should match the user's target industries.

**`### JobSpy Aggregator`** — Table of keyword queries. Populate from current context.md `## Target` role types and `## Industries` at build time — queries should be tailored to the user's current focus.

**`### Niche Newsletters`** — Discovery-based (no static list). Example queries for WebSearch discovery.

**`### Web Search Discovery`** — Open-ended queries adapted to Industries + Target each run. Example queries listed.

**Copy spec:**
- Section heading: "Search Channels"
- Subtitle: "5 mandatory channels dispatched every run. Content adapts to Industries and Target above."
- Subsection headings: "Direct Career Pages", "Industry Job Boards", "JobSpy Aggregator", "Niche Newsletters", "Web Search Discovery"

**Verify:**
- `grep "## Search Channels" 03_agents/tests/v23/context.md` (should match)
- `grep -c "###" 03_agents/tests/v23/context.md` (should increase by 5)

#### Step 2.6: Commit Layer 2
**Description:** Stage and commit all Layer 2 changes.
```bash
git add 03_agents/tests/v23/CLAUDE.md 03_agents/tests/v23/.claude/agents/*.md 03_agents/tests/v23/references/orchestration.md 03_agents/tests/v23/context.md
git commit -m "feat(jsa): V23 Layer 2 — HC1 reversal, model tiering, 5-channel mandate, search channels"
```

---

### Phase 3: Layer 3 — Validation + Preflight

#### Step 3.1: Write failing tests for 2 shell-native preflight checks
**File:** `tests/test_preflight.py`
**Action:** Modify (add 4 tests to existing file)
**Description:** Add 4 new tests for the 2 shell-native checks only. The 3 Python-backed checks (session-resume, model-settings, dashboard-url) are tested at the `manage_state.py` layer in Step 3.2 — no duplicate coverage at the preflight.sh layer. Tests use `subprocess.run` to invoke `preflight.sh` with `tmp_path` for isolation.

**Class `TestPreflightGitPull` (2 tests):**
1. `test_git_pull_runs_in_interactive_mode` — no `SCHEDULED_RUN` env var, verifies preflight does NOT print "Skipping git pull (scheduled run)"
2. `test_git_pull_skipped_in_scheduled_mode` — `SCHEDULED_RUN=true`, verifies preflight prints "Skipping git pull (scheduled run)"

**Class `TestPreflightAgentMemory` (2 tests):**
3. `test_passes_when_claude_md_has_agent_memory_ref` — CLAUDE.md contains `.claude/agent-memory`, exit 0
4. `test_warns_when_claude_md_missing_agent_memory_ref` — CLAUDE.md without agent-memory reference, FAILED=1 with "CLAUDE.md missing agent-memory startup read (HC4)"

**Compatibility note:** The existing `_setup_passing_tree` helper must create test agents with `model: haiku` (not `model: inherit`) so existing tests continue passing after model validation is added.

**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_preflight.py -v` (4 new tests FAIL — features not implemented)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check tests/test_preflight.py`

#### Step 3.2: Implement 3 preflight subcommands in manage_state.py
**File:** `scripts/manage_state.py`
**Action:** Modify (add 3 subcommands: check-session-resume, check-model-settings, check-dashboard-url)
**Description:** Add 3 new subcommands that preflight.sh will call (Step 3.3 depends on these existing):

1. **`check-session-resume`** — Reads `output/digests/_status.json`, extracts `sent_at` field, compares date portion to today. If match: prints "A digest was already sent today ({date})" and exits 1. If no file or different date: exits 0. Args: `--status-path` (default: `output/digests/_status.json`), `--run-date` (default: today).

2. **`check-model-settings`** — Iterates over `.claude/agents/*.md`, parses YAML frontmatter, extracts `model:` value. Valid values: `haiku`, `sonnet`. Everything else (including `inherit`, `opus`, missing): prints "Agent model misconfigured: {filename} has model: {value} (expected haiku or sonnet)" and exits 1. If all valid: prints "All agent model settings validated" and exits 0. Args: `--agents-dir` (default: `.claude/agents`), `--exclude` (optional comma-separated list of agent filenames to skip validation — allows new agents to be added without immediately updating this check; document that any excluded agent must use `haiku` or `sonnet` before the exclusion is removed).

3. **`check-dashboard-url`** — Reads `context.md`, looks for `Dashboard:` value in the `## Delivery` section. If empty or missing: prints "Dashboard URL missing or empty in context.md" and exits 1. If present: prints the URL and exits 0. Args: `--context-path` (default: `context.md`).

Add CLI subparsers for all 3 subcommands with their respective arguments.

**Tests file:** `tests/test_manage_state_preflight.py`
**Tests action:** Create (new test file)
**Tests description:** Create test file with 3 test classes:

**Class `TestCheckSessionResume` (3 tests):**
1. `test_exits_one_when_digest_sent_today` — `_status.json` with today's `sent_at`, exit 1
2. `test_exits_zero_when_digest_sent_different_day` — old date in `sent_at`, exit 0
3. `test_exits_zero_when_no_status_file` — no file, exit 0

**Class `TestCheckModelSettings` (4 tests):**
4. `test_passes_with_valid_models` — agents with `model: haiku`/`model: sonnet`, exit 0
5. `test_fails_with_model_inherit` — agent with `model: inherit`, exit 1
6. `test_fails_with_missing_model` — agent with no `model:` line, exit 1
7. `test_fails_with_model_opus` — agent with `model: opus`, exit 1

**Class `TestCheckDashboardUrl` (3 tests):**
8. `test_exits_zero_with_valid_url` — context.md with `Dashboard: https://...`, exit 0
9. `test_exits_one_with_empty_url` — context.md with `Dashboard:` (empty), exit 1
10. `test_exits_one_when_missing` — context.md without Dashboard line, exit 1

**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_manage_state_preflight.py -v` (10 tests PASS)
- Lint: `cd 03_agents/tests/v23 && python -m ruff check scripts/manage_state.py tests/test_manage_state_preflight.py`
- Smoke: `cd 03_agents/tests/v23 && python scripts/manage_state.py check-session-resume --help` (should show usage)
- Smoke: `cd 03_agents/tests/v23 && python scripts/manage_state.py check-model-settings --help` (should show usage)
- Smoke: `cd 03_agents/tests/v23 && python scripts/manage_state.py check-dashboard-url --help` (should show usage)

#### Step 3.3: Implement 2 shell-native preflight checks in preflight.sh
**File:** `scripts/preflight.sh`
**Action:** Modify (add 2 shell-native checks + upgrade flag parser)
**Description:** `preflight.sh` focuses on the 2 shell-native checks only. The 3 Python-backed checks (session-resume, model-settings, dashboard-url) are called by the orchestrator (or gate-check subagent) via `manage_state.py check-*` subcommands directly — not wrapped by preflight.sh.

**Flag parser upgrade:** Replace positional-only parsing with loop-based parser supporting `--env` and `--structure` flags. No `--force` flag — users can delete `output/digests/_status.json` to re-run instead (eliminates a second code path).

**2 shell-native checks:**

**ENV tier (before existing checks):**

1. **Git pull** — At top of ENV tier: if `SCHEDULED_RUN` is set, print "Skipping git pull (scheduled run)". Otherwise, check if inside git work tree and run `git pull --ff-only`, gracefully handling failures (no remote, conflicts).

**STRUCTURE tier (after `background: true` check):**

2. **Agent-memory startup read** — Verify CLAUDE.md contains the agent-memory startup read step (`grep ".claude/agent-memory" CLAUDE.md`). If missing, print warning "CLAUDE.md missing agent-memory startup read (HC4)" and set FAILED=1. (V14/V17/V19 three-time recurrence.)

**Orchestrator-direct checks (NOT in preflight.sh):** The 3 Python-backed checks are invoked by the orchestrator (or gate-check subagent) calling `manage_state.py` subcommands directly:
- `manage_state.py check-session-resume` — session resume guard
- `manage_state.py check-model-settings` — model setting validation
- `manage_state.py check-dashboard-url` — dashboard URL check

**Copy spec:**
- Git pull skip: "Skipping git pull (scheduled run)"

**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/test_preflight.py -v` (ALL 17 tests PASS — 13 existing + 4 new)
- Lint: `cd 03_agents/tests/v23 && bash -n scripts/preflight.sh` (syntax check)

#### Step 3.4: Run full test suite — confirm no regressions
**Description:** Run all tests (existing + Layer 1 + Layer 3) to confirm nothing is broken.
**Verify:**
- Test: `cd 03_agents/tests/v23 && python -m pytest tests/ -v`
- Lint: `cd 03_agents/tests/v23 && python -m ruff check scripts/ tests/`

#### Step 3.5: Commit Layer 3
**Description:** Stage and commit all Layer 3 changes.
```bash
git add 03_agents/tests/v23/scripts/preflight.sh 03_agents/tests/v23/tests/test_preflight.py 03_agents/tests/v23/scripts/manage_state.py 03_agents/tests/v23/tests/test_manage_state_preflight.py
git commit -m "feat(jsa): V23 Layer 3 — preflight subcommands, preflight.sh checks, session guard, model validation"
```

---

### Phase 4: Deployment Steps

#### Step 4.1: Update GitHub Actions workflow
**File:** `.github/workflows/daily-digest.yml` (repo root)
**Action:** Modify
**Description:** Update the repo-root GitHub Actions workflow to reference V23 instead of V22/V20. Change all paths referencing `03_agents/tests/v2X/` to `03_agents/tests/v23/`. Also ensure:
1. `SCHEDULED_RUN=true` env var is set in the workflow environment
2. A step creates `settings.local.json` in the V23 directory before Claude CLI runs (V17/V19/V20/V22 recurrence — workflow fails at validation if this file doesn't exist)
**Verify:**
- `grep "v23" .github/workflows/daily-digest.yml` (should match)
- `grep "SCHEDULED_RUN" .github/workflows/daily-digest.yml` (should match)

#### Step 4.2: Vercel dashboard redeployment
**Description:** Redeploy the Vercel dashboard from the V23 directory. This is mandatory after every version transition (V21/V22 regression).
```bash
cd 03_agents/tests/v23 && vercel link --project jsa-dashboard --yes && vercel --prod --yes
```
**Verify:**
- `curl -s https://jsa-dashboard.vercel.app/api/state` (should return valid JSON with current `run_date`)

#### Step 4.3: Create deployment verification script
**File:** `scripts/verify_deploy.sh`
**Action:** Create
**Description:** Create a consolidated deployment verification script that runs all pre-deploy and post-deploy checks: lint (`ruff check`), test count (`pytest --co -q | tail -1`), file existence (spot-check key files), HC1 reversal confirmation (no `model: inherit` in agents), model tier settings (grep agent frontmatter), orchestration references (5-channel, gates), email CLI flag verification (grep confirming `--body-file` appears and `--html` does NOT appear in orchestration references to `send_email.py` — V21 regression), and dashboard health (`curl` Vercel endpoint). Script exits non-zero on any failure.
**Verify:**
- `bash 03_agents/tests/v23/scripts/verify_deploy.sh` (should exit 0 if all checks pass)

#### Step 4.4: Final commit
**Description:** Commit deployment-related changes (workflow update + verification script).
```bash
git add .github/workflows/daily-digest.yml 03_agents/tests/v23/scripts/verify_deploy.sh
git commit -m "chore(jsa): V23 update GitHub Actions workflow + Vercel redeploy + deploy verification"
```

---

## Deployment Verification

All pre-deploy and post-deploy checks are consolidated into a single script created during Step 4.3. The `scripts/verify_deploy.sh` script runs all verification checks (lint, test count, file existence, HC1 reversal, model settings, orchestration references, dashboard health). The script exits non-zero on any failure. No manual bash snippets — one script, one command: `bash scripts/verify_deploy.sh`.

## Handoff Contract

- Total steps: 28, Total phases: 5 (Setup + 3 Layers + Deployment)
- New tests: 38 (9 dedup role-types + 4 list-active-role-types + 4 verify-clean-working-tree + 4 verify-channels-dispatched + 3 verify-session-state-updated + 10 preflight subcommands + 4 preflight shell) — dedup tests increased by 2 (state.json cross-ref + URL dedup), preflight shell tests reduced to 4 (2 shell-native checks only; 3 Python-backed checks tested at manage_state.py layer)
- Expected total test count: 170+ (132 existing + 38 new)
- Files created: `03_agents/tests/v23/` (copied from V22), `tests/test_manage_state_dedup.py` (test file, modified), `tests/test_manage_state_preflight.py` (new test file for preflight subcommands), `tests/test_preflight.py` (existing test file with 4 tests added to existing 13), `.claude/agents/gate-check.md` (new agent, model: haiku), `scripts/verify_deploy.sh` (consolidated deployment checks)
- Files modified: `scripts/manage_state.py` (1 utility subcommand `list-active-role-types` + 4 verification subcommands + 3 preflight subcommands, grouped under `verify`/`check` subparsers), `tests/test_manage_state.py` (4 new test classes), `CLAUDE.md` (HC1 reversal + Agent Model Tiers), `.claude/agents/*.md` (6 files: model tier assignment + 1 new gate-check agent), `references/orchestration.md` (Phase 1 rewrite: 5-channel mandate + Context Budget), `context.md` (Search Channels section), `scripts/preflight.sh` (2 shell-native checks + flag parser upgrade), `.github/workflows/daily-digest.yml` (V23 path + SCHEDULED_RUN + settings.local.json)
- Verification sequence: pytest (per step) → ruff lint (per step) → full suite (per layer)
- Deployment verification: single `scripts/verify_deploy.sh` script
- V19 regression note: HC1 ("Never pass model: to Task tool") is intentionally superseded by V23 model-tiering; regression file update required after build

<!-- STAGE COMPLETE: /plan, 2026-02-24 -->
<!-- STAGE COMPLETE: /revise after round 1, 2026-02-24 -->
<!-- STAGE COMPLETE: /revise after round 2, 2026-02-24 -->

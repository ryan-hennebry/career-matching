# Plan: JSA V20 — Single Phase, 13 Fixes + Enforcement Upgrade

## Overview

V20 implements 13 fixes across 7 components in a single phase. The key innovation is upgrading enforcement from text constraints to code/assertion enforcement for 4 recurring regressions (dedup, dashboard URL, incremental commit, agent memory). All changes are constraint edits, one script enhancement, one workflow rewrite, and agent definition updates.

**From Design Handoff:**
- Approach: Single Phase — All 13 Fixes
- Components: Scheduling infrastructure (daily-digest.yml), CLAUDE.md constraint fixes (9 fixes), regression prevention layer (4 assertion-based enforcement upgrades), script fix (manage_state.py content-based dedup), agent definition updates (6 agents), settings allowlist, regression tests
- Success criteria: Manual workflow_dispatch completes, 5 consecutive scheduled runs without failure, 0 regression recurrences, content-based dedup catches test duplicates, all 12 implementation fixes verified

## Files to Modify

- `.github/workflows/daily-digest.yml` — Scheduling infrastructure (timeout, retry, permissions, preflight, inline settings, version path)
- `03_agents/tests/v20/CLAUDE.md` — 9 constraint fixes + 3 regression prevention assertions
- `03_agents/tests/v20/scripts/manage_state.py` — Add location to content-based dedup collision key
- `03_agents/tests/v20/tests/test_dedup.py` — New: location-based dedup tests
- `03_agents/tests/v20/.claude/agents/search-verify.md` — working_dir variable, version path fix
- `03_agents/tests/v20/.claude/agents/brief-generator.md` — working_dir variable, version path fix
- `03_agents/tests/v20/.claude/agents/digest-email.md` — working_dir variable, dashboard_url requirement, version path fix
- `03_agents/tests/v20/.claude/agents/onboarding.md` — working_dir variable, version path fix
- `03_agents/tests/v20/.claude/agents/briefs-html.md` — working_dir variable, version path fix
- `03_agents/tests/v20/.claude/agents/source-researcher.md` — working_dir variable, version path fix
- `03_agents/tests/v20/.claude/settings.local.json` — Add git log/diff permissions (additive only, no removals)

## Implementation Steps

---

### Phase 1: V20 Directory Scaffold + manage_state.py Dedup Enhancement

---

### Step 1: Copy v19 directory to v20

**Action:** Create directory
**Command:**
```bash
cp -R 03_agents/tests/v19 03_agents/tests/v20
```

**Verify:**
```bash
ls 03_agents/tests/v20/CLAUDE.md
# Expected: file exists
```

---

### Step 2: Update manage_state.py collision key to include location

**File:** `03_agents/tests/v20/scripts/manage_state.py`
**Action:** Modify

In the `_compute_dedup` function, update the docstring and collision key:

**Edit 1 — Update docstring:**
```
old_string: Collision key: {source_domain}:{company}:{title}.
new_string: Collision key: {source_domain}:{company}:{title}:{location}.
```

**Edit 2 — Add location extraction and update key format:**
```python
# old_string:
        title = job.get("title", "unknown").lower().strip()
        key = f"{domain}:{company}:{title}"

# new_string:
        title = job.get("title", "unknown").lower().strip()
        location = job.get("location", "unknown").lower().strip()
        key = f"{domain}:{company}:{title}:{location}"
```

**Verify:**
```bash
grep -n "location" 03_agents/tests/v20/scripts/manage_state.py | head -5
# Expected: location extraction line + key format line visible
python3 -c "import ast; ast.parse(open('03_agents/tests/v20/scripts/manage_state.py').read()); print('Syntax OK')"
```

---

### Step 3: Write location-based dedup tests

**File:** `03_agents/tests/v20/tests/test_dedup.py`
**Action:** Create

```python
"""Tests for content-based dedup with location in collision key."""

import json
import os
import tempfile
import pytest

# Add parent dir to path so we can import manage_state
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from manage_state import _compute_dedup


def _write_verified_json(tmpdir, role_type, filename, job_data):
    """Helper: write a verified JSON file in the expected directory structure."""
    role_dir = os.path.join(tmpdir, role_type)
    os.makedirs(role_dir, exist_ok=True)
    filepath = os.path.join(role_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(job_data, f)
    return filepath


def _make_job(company="Acme Corp", title="Engineer", location="London, UK",
              source_url="https://example.com/job/1", score=75):
    """Helper: create a minimal verified job dict."""
    return {
        "company": company,
        "title": title,
        "location": location,
        "source_url": source_url,
        "score": score,
        "active_status": "verified",
        "requirements_met": ["python"],
    }


class TestLocationDedup:
    """Test that location is part of the dedup collision key."""

    def test_same_job_different_locations_not_deduped(self, tmp_path):
        """Two jobs with same company+title but different locations should NOT collide."""
        _write_verified_json(str(tmp_path), "engineer", "acme-engineer-london.json",
                             _make_job(location="London, UK"))
        _write_verified_json(str(tmp_path), "engineer", "acme-engineer-nyc.json",
                             _make_job(location="New York, NY"))

        result = _compute_dedup(str(tmp_path))
        assert result["total_output"] == 2, f"Expected 2 kept, got {result['total_output']}"
        assert len(result["removed"]) == 0

    def test_same_job_same_location_is_deduped(self, tmp_path):
        """Two jobs with same company+title+location should collide — highest score kept."""
        _write_verified_json(str(tmp_path), "engineer", "acme-engineer-a.json",
                             _make_job(location="London, UK", score=80))
        _write_verified_json(str(tmp_path), "engineer", "acme-engineer-b.json",
                             _make_job(location="London, UK", score=60))

        result = _compute_dedup(str(tmp_path))
        assert result["total_output"] == 1, f"Expected 1 kept, got {result['total_output']}"
        assert len(result["removed"]) == 1
        # The higher-scored one (80) should be kept
        assert result["kept"][0]["score"] == 80


class TestLocationNormalization:
    """Test that location normalization handles edge cases."""

    def test_case_insensitive_location_match(self, tmp_path):
        """'London' vs 'LONDON' should collide."""
        _write_verified_json(str(tmp_path), "engineer", "acme-a.json",
                             _make_job(location="London", score=90))
        _write_verified_json(str(tmp_path), "engineer", "acme-b.json",
                             _make_job(location="LONDON", score=70))

        result = _compute_dedup(str(tmp_path))
        assert result["total_output"] == 1

    def test_whitespace_stripped_location_match(self, tmp_path):
        """'  London  ' vs 'London' should collide."""
        _write_verified_json(str(tmp_path), "engineer", "acme-a.json",
                             _make_job(location="  London  ", score=85))
        _write_verified_json(str(tmp_path), "engineer", "acme-b.json",
                             _make_job(location="London", score=65))

        result = _compute_dedup(str(tmp_path))
        assert result["total_output"] == 1

    def test_missing_location_defaults_to_unknown(self, tmp_path):
        """Two jobs with missing location both default to 'unknown' — should collide."""
        job_a = _make_job(score=80)
        del job_a["location"]
        job_b = _make_job(score=60)
        del job_b["location"]

        _write_verified_json(str(tmp_path), "engineer", "acme-a.json", job_a)
        _write_verified_json(str(tmp_path), "engineer", "acme-b.json", job_b)

        result = _compute_dedup(str(tmp_path))
        assert result["total_output"] == 1

    def test_missing_vs_explicit_location_not_deduped(self, tmp_path):
        """Missing location (='unknown') vs 'London' should NOT collide."""
        job_no_loc = _make_job(score=80)
        del job_no_loc["location"]

        _write_verified_json(str(tmp_path), "engineer", "acme-noloc.json", job_no_loc)
        _write_verified_json(str(tmp_path), "engineer", "acme-london.json",
                             _make_job(location="London", score=70))

        result = _compute_dedup(str(tmp_path))
        assert result["total_output"] == 2
```

**Verify:**
```bash
cd 03_agents/tests/v20 && python3 -m pytest tests/test_dedup.py -v
# Expected: 6 tests pass
```

---

### Phase 2: CLAUDE.md Constraint Fixes + Regression Prevention Layer

---

### Step 4: Add working_dir variable to all dispatch templates (Failure 1)

**File:** `03_agents/tests/v20/CLAUDE.md`
**Action:** Modify (6 edits across 5 CLAUDE.md internal steps + 1 recovery protocol)

**Pattern (Rec10):** Every subagent dispatch JSON blob must include `"working_dir": "03_agents/tests/v20"` as the first key. The builder applies this pattern to each location listed below.

**`working_dir` is MANDATORY in every subagent dispatch.** All subagent file operations use paths relative to `working_dir`. Never omit it — omission causes subagents to write output to the wrong directory.

| Edit | CLAUDE.md Location | Change |
|---|---|---|
| 4a | Step 9 (variable prep) | Variable count 14 → 15. Add `"working_dir": "03_agents/tests/v20"` as first key in JSON blob template. |
| 4b | Step 8a (source-researcher dispatch) | Add `"working_dir"` as first key in prompt JSON. |
| 4c | Step 10 (search-verify dispatch) | Update "14 variables" → "15 variables (must include working_dir)" in prompt description. |
| 4d | Step 18 (brief-generator dispatch) | Add `"working_dir"` as first key in prompt JSON. |
| 4e | Step 19 (digest-email + briefs-html dispatch) | Add `"working_dir"` as first key in both prompt JSONs. Update variable counts: digest-email 8 → 9, briefs-html 1 → 2. |
| 4f | Recovery protocol | Replace hardcoded `03_agents/tests/v18/` with `03_agents/tests/v20/` in recovery subagent prompt. |

**Post-render verification (Rec2):** After Edit 4e dispatches (digest-email + briefs-html), verify output HTML files exist and contain expected content markers:
- `output/digests/*.html` — must exist, file size > 0, contains `<html` tag
- `output/briefs/*.html` (if briefs were generated) — must exist, file size > 0, contains `<html` tag
If either file is missing or empty, re-dispatch the failed subagent before proceeding to email send.

**Verify:**
```bash
grep -c "working_dir" 03_agents/tests/v20/CLAUDE.md
# Expected: >= 6 occurrences
grep "v18" 03_agents/tests/v20/CLAUDE.md
# Expected: 0 occurrences (all v18 references replaced)
```

---

### Step 5: Add dashboard URL storage + post-presentation verification (Failure 4)

**File:** `03_agents/tests/v20/CLAUDE.md`
**Action:** Modify (2 edits)

**Cross-references (Rec4):** Dashboard URL touches 3 locations in CLAUDE.md — onboarding (Step 9b below), presentation verification (Step 16b below), and digest-email dispatch (Edit 4e in plan Step 4 + digest-email.md in plan Step 13). The builder must ensure all three are consistent.

**Edit 5a — Add dashboard URL to onboarding:**
```
old_string:
9. Ask: "Email for digests?" → Store in `## Delivery`
10. Derive constraints (title exclusions, scoring weights) → present for confirmation

new_string:
9. Ask: "Email for digests?" → Store in `## Delivery`
9b. Ask: "Do you have a dashboard URL for tracking jobs? (e.g., a Vercel deployment)" → If yes, store in `## Delivery` as `Dashboard: {url}`. If no, omit silently.
10. Derive constraints (title exclusions, scoring weights) → present for confirmation
```

**Edit 5b — Add POST-PRESENTATION VERIFICATION after Step 16:**
```
old_string:
**Step 17: Collect user feedback.** Present jobs and ask which ones the user wants briefs for.

new_string:
**Step 16b: POST-PRESENTATION VERIFICATION (MANDATORY).**
After presenting results (Step 16), verify the dashboard URL was included:
```bash
# Assert dashboard URL was shown (if one exists in context.md)
# If context.md ## Delivery contains a Dashboard entry but the presentation output did NOT include it, STOP and re-present with the URL.
```
If `context.md` `## Delivery` contains a `Dashboard:` line, the presentation MUST include the `> View and manage all jobs at:` line with the URL. If it was omitted, STOP and re-present the unified selection view with the URL included. Do NOT proceed to Step 17 until the URL is verified present (or confirmed absent from context.md).

**Step 17: Collect user feedback.** Present jobs and ask which ones the user wants briefs for.
```

**Verify:**
```bash
grep -n "POST-PRESENTATION VERIFICATION" 03_agents/tests/v20/CLAUDE.md
# Expected: 1 match
grep -n "Dashboard:" 03_agents/tests/v20/CLAUDE.md
# Expected: >= 1 match
```

---

### Step 6: Elevate incremental commit to hard constraint + post-batch verification (Failure 5)

**File:** `03_agents/tests/v20/CLAUDE.md`
**Action:** Modify (3 edits)

**Edit 6a — Add HC7, HC8, HC9:**
```
old_string:
6. **Never give instructions about Claude Code UI features** (buttons, menus, settings panels, keyboard shortcuts, sidebar options) unless 100% certain the feature exists. If unsure, respond: "I'm not sure about that UI element — please check Claude Code documentation at docs.anthropic.com/claude-code."

new_string:
6. **Never give instructions about Claude Code UI features** (buttons, menus, settings panels, keyboard shortcuts, sidebar options) unless 100% certain the feature exists. If unsure, respond: "I'm not sure about that UI element — please check Claude Code documentation at docs.anthropic.com/claude-code."
7. **Incremental commit+push after every search batch (interactive mode).** After each search batch completes (Step 11b) and after briefs+digest (Step 19c), MUST commit and push. This is not optional — skipping it breaks dashboard incremental progress.
8. **settings.local.json edits in interactive mode must merge into existing permissions array — never overwrite the file.** Read existing JSON, append new entries, write back. This prevents accidental removal of permissions granted during previous sessions.
9. **API keys (ANTHROPIC_API_KEY, RESEND_API_KEY) must never appear in Bash command arguments** — use environment variables or stdin redirection exclusively. Passing keys as CLI args exposes them in process listings and shell history.
```

**Edit 6b — Add POST-BATCH COMMIT VERIFICATION to Step 11b:**
```
old_string:
**Step 11b: Incremental commit+push (interactive mode only).** After each search batch AND after dedup (Step 13), write session-state.md and commit+push output:
1. **Write session-state.md** — Update `output/session-state.md` with current run progress (batches completed, jobs found, timestamp).
2. **Commit and push:**
```bash
git add output/ state.json output/session-state.md
git commit -m "chore(jsa): search batch {N} — {run_date}"
git push origin main
```
This triggers Vercel redeployment so the dashboard shows incremental progress. Skip in scheduled mode (GitHub Actions handles its own commits).

new_string:
**Step 11b: Incremental commit+push (interactive mode only).** After each search batch AND after dedup (Step 13), write session-state.md and commit+push output:
1. **Write session-state.md** — Update `output/session-state.md` with current run progress (batches completed, jobs found, timestamp).
2. **Commit and push:**
```bash
git add output/ state.json output/session-state.md
git commit -m "chore(jsa): search batch {N} — {run_date}"
git push origin main
```
This triggers Vercel redeployment so the dashboard shows incremental progress. Skip in scheduled mode (GitHub Actions handles its own commits).

**POST-BATCH COMMIT VERIFICATION (MANDATORY in interactive mode):**
After each commit+push, verify the commit landed:
```bash
git log --oneline -1
```
The output MUST contain the expected commit message substring (e.g., "search batch" or "briefs + digest"). If the commit did not happen (git log shows a different commit), retry the commit (max 2 retries). If commit still fails after 2 retries, write a warning to session-state.md ("WARN: commit failed for batch {N}") and continue to the next batch. Do NOT loop indefinitely.

> **Future improvement (Rec7):** Consider extracting POST-BATCH and POST-PRESENTATION verifications to dedicated scripts (e.g., `scripts/verify_commit.sh`, `scripts/verify_presentation.sh`) that return non-zero on failure, replacing prose-based enforcement.
```

**Edit 6c — Add Context Budget section to CLAUDE.md:**

Add a new `## Context Budget` section after the Hard Constraints section in CLAUDE.md:

```
## Context Budget

| Tool / Action | Parent | Subagent |
|---|---|---|
| git (status, add, commit, push, log, diff) | YES | NO |
| Task dispatch | YES | NO |
| Bash for commit/push | YES | NO |
| `python3 scripts/send_email.py` | YES | NO |
| `python3 scripts/manage_state.py` CLI | YES | NO |
| WebFetch | NO | YES |
| WebSearch | NO | YES |
| python3 for data processing | NO | YES |
| File reads of source/verified JSONs | NO | YES |
| File reads of agent-memory, context.md | YES (startup only) | YES |

**Enforcement:** If the parent context attempts a subagent-only tool (WebFetch, WebSearch, python3 for processing, reading verified JSONs), STOP and dispatch a subagent instead. This keeps the parent lightweight for orchestration decisions.
```

**Verify:**
```bash
grep -n "POST-BATCH COMMIT VERIFICATION" 03_agents/tests/v20/CLAUDE.md
# Expected: 1 match
grep -n "HC.*7\|7\.\s.*Incremental" 03_agents/tests/v20/CLAUDE.md
# Expected: HC7 line visible
grep -n "Context Budget" 03_agents/tests/v20/CLAUDE.md
# Expected: 1 match
```

---

### Step 7: Strengthen HC5 — no python3 in parent (Failure 6)

**File:** `03_agents/tests/v20/CLAUDE.md`
**Action:** Modify

```
old_string:
5. **Never write inline Python for state mutations.** All state changes must go through `scripts/manage_state.py` CLI subcommands. No `python3 -c` calls that import manage_state internals.

new_string:
5. **Never execute Python in parent context.** No `python3 scripts/*`, no `python3 -c`, no inline Python. All script execution MUST be dispatched to subagents. The only exception: `python3 scripts/send_email.py` in Step 20 (parent-orchestrated email send) and `python3 scripts/manage_state.py` CLI subcommands dispatched via Bash in parent for state sync (Steps 13-14).
```

**Verify:**
```bash
grep -n "Never execute Python" 03_agents/tests/v20/CLAUDE.md
# Expected: 1 match
```

---

### Step 8: Reinforce HC1 — no model param in dispatch (Failure 8)

**File:** `03_agents/tests/v20/CLAUDE.md`
**Action:** Modify

```
old_string:
1. **Never pass `model:` to Task tool.** Named agents inherit model from parent via `model: inherit` in their frontmatter. Passing `model:` from parent overrides this and causes billing/routing issues.

new_string:
1. **Never pass `model:` to Task tool.** Named agents inherit model from parent via `model: inherit` in their frontmatter. Passing `model:` from parent overrides this and causes billing/routing issues. This applies to ALL dispatch calls: Steps 8a, 10, 18, 19. The Task tool `prompt` field contains only the JSON variables blob — never include `model:` as a key in the JSON or as a Task tool parameter.
```

**Verify:**
```bash
grep -n "ALL dispatch calls" 03_agents/tests/v20/CLAUDE.md
# Expected: 1 match
```

---

### Step 9: Add _summary.md mandatory requirement + recovery preamble (Failure 9)

**File:** `03_agents/tests/v20/CLAUDE.md`
**Action:** Modify

```
old_string:
When a subagent completes work (files exist in output directory) but fails to write `_status.json` or `_summary.md`:

1. **Do NOT read individual verified JSONs in parent context.** This bloats the context window.
2. **Dispatch a recovery subagent** via Task tool:

new_string:
**All search-verify subagents MUST write `_summary.md`** in addition to `_status.json`. The `_summary.md` is the parent's ONLY view into subagent results — without it, the parent has no data for that role type. If a subagent completes verification files but omits `_summary.md`, it is treated as a partial failure requiring recovery.

When a subagent completes work (files exist in output directory) but fails to write `_status.json` or `_summary.md`:

1. **Do NOT read individual verified JSONs in parent context.** This bloats the context window.
2. **Dispatch a recovery subagent** via Task tool:
```

**Verify:**
```bash
grep -n "MUST write.*_summary.md" 03_agents/tests/v20/CLAUDE.md
# Expected: 1 match
```

---

### Step 10: Replace rm -f with find -delete in cleanup (Failure 10)

**File:** `03_agents/tests/v20/CLAUDE.md`
**Action:** Modify

```
old_string:
5. **Pre-run cleanup:** If `state.json`'s `last_run_date` differs from today's run date, this is a new run — clean stale output:
   ```
   rm -f output/jobs/*
   rm -f output/verified/*/*
   rm -f output/briefs/*
   rm -f output/digests/*
   ```

new_string:
5. **Pre-run cleanup:** If `state.json`'s `last_run_date` differs from today's run date, this is a new run — clean stale output:
   ```
   find output/jobs -type f -delete 2>/dev/null || true
   find output/verified -type f -delete 2>/dev/null || true
   find output/briefs -type f -delete 2>/dev/null || true
   find output/digests -type f -delete 2>/dev/null || true
   ```
   **Never use `rm -f dir/*` for cleanup** — glob expansion fails silently when too many files match, leaving stale data. `find -delete` handles any file count reliably.
```

**Verify:**
```bash
grep -n "rm -f" 03_agents/tests/v20/CLAUDE.md
# Expected: 0 matches
grep -n "find.*-delete" 03_agents/tests/v20/CLAUDE.md
# Expected: >= 4 matches
```

---

### Step 11: Enforce table format for all role types (Failure 11)

**File:** `03_agents/tests/v20/CLAUDE.md`
**Action:** Modify

```
old_string:
**Two subsections:**

**New Today** — jobs appearing for the first time in this run (from delta `new_jobs` list).

**Still Active** — jobs seen in previous runs that are still active (from delta `still_active` list).

new_string:
**Two subsections (MANDATORY for every role type with results):**

Every role type with results MUST be presented using the standard table format below. No role type may use bullet lists, numbered lists, or prose paragraphs instead of tables. If a role type has both new and still-active jobs, show both subsections. If only one category has results, show only that subsection.

**New Today** — jobs appearing for the first time in this run (from delta `new_jobs` list).

**Still Active** — jobs seen in previous runs that are still active (from delta `still_active` list).
```

**Verify:**
```bash
grep -n "MANDATORY for every role type" 03_agents/tests/v20/CLAUDE.md
# Expected: 1 match
```

---

### Step 12: Fix agent memory glob pattern + startup assertion (Failure 12)

**File:** `03_agents/tests/v20/CLAUDE.md`
**Action:** Modify

```
old_string:
2. **Read agent memory:** Read all `.claude/agent-memory/*/MEMORY.md` files. Log count read: "Agent memory: read {N} MEMORY.md files." Carry documented failure patterns as active constraints for the session.

new_string:
2. **Read agent memory:** Glob for `.claude/agent-memory/*/MEMORY.md` and also `.claude/agent-memory/*.md` (both patterns — some memories may be at the root level). Log count read: "Agent memory: read {N} memory files."
   **STARTUP ASSERTION (MANDATORY):** If the glob matches 0 files, STOP with error: "FATAL: 0 agent memory files found — check .claude/agent-memory/ paths." Do NOT continue — agent memory contains critical regression guards.
   Carry documented failure patterns as active constraints for the session.
```

**Verify:**
```bash
grep -n "STARTUP ASSERTION" 03_agents/tests/v20/CLAUDE.md
# Expected: 1 match
grep -n "FATAL.*0 agent memory" 03_agents/tests/v20/CLAUDE.md
# Expected: 1 match
```

---

### Phase 3: Agent Definition Updates + Settings Allowlist

---

### Step 13: Update all 6 agent definitions — working_dir variable + version path fix

**Files:** All agent definitions in `03_agents/tests/v20/.claude/agents/`
**Action:** Modify

**Pattern:** Each agent file requires these changes:
1. Replace hardcoded `03_agents/tests/v18/` with `{working_dir}` in both the "Working directory" line and "First action" line
2. Update the variable count where applicable (agents that parse a JSON blob)
3. For `digest-email.md` only: add `dashboard_url` requirement

**Note:** Each agent should include a startup assertion: `test -d {working_dir} || exit 1` before file operations. (See Rec1.)

Apply per-file edits as follows:

| Agent File | Variable Count Change | Additional Changes |
|---|---|---|
| `search-verify.md` | 14 → 15 (add `working_dir`) | Update variable parse instruction |
| `brief-generator.md` | 7 → 8 (add `working_dir`) | Update variable parse instruction |
| `digest-email.md` | 7 → 9 (add `working_dir` + `dashboard_url`) | Add dashboard_url non-empty check; write status failed if missing |
| `onboarding.md` | N/A (no JSON blob parse) | Working directory + first action only |
| `briefs-html.md` | N/A (no JSON blob parse) | Working directory + first action only |
| `source-researcher.md` | N/A (no JSON blob parse) | Working directory + first action only |

**Detailed edits for each file:**

**search-verify.md (3 edits):**
- Variable count: `old: "14 template variables. Confirm all 14"` → `new: "15 template variables (the 14 search variables + working_dir). Confirm all 15"`
- Working directory: `old: "03_agents/tests/v18/"` → `new: "{working_dir}"`
- First action: `old: "cd 03_agents/tests/v18/"` → `new: "cd {working_dir}"`

**brief-generator.md (3 edits):**
- Variable count: `old: "7 template variables. Confirm all 7"` → `new: "8 template variables (the 7 brief variables + working_dir). Confirm all 8"`
- Working directory: `old: "03_agents/tests/v18/"` → `new: "{working_dir}"`
- First action: `old: "cd 03_agents/tests/v18/"` → `new: "cd {working_dir}"`

**digest-email.md (4 edits):**
- Variable count: `old: "7 template variables. Confirm all 7"` → `new: "9 template variables (the 7 digest variables + working_dir + dashboard_url). Confirm all 9"`
- Add after the missing-variable check: `**Dashboard URL:** Verify dashboard_url is non-empty. Include it in the digest HTML output (e.g., a "View Dashboard" link). If dashboard_url is empty or missing, write status failed with error "Missing variable: dashboard_url" and exit.`
- Working directory: `old: "03_agents/tests/v18/"` → `new: "{working_dir}"`
- First action: `old: "cd 03_agents/tests/v18/"` → `new: "cd {working_dir}"`

**onboarding.md, briefs-html.md, source-researcher.md (2 edits each):**
- Working directory: `old: "03_agents/tests/v18/"` → `new: "{working_dir}"`
- First action: `old: "cd 03_agents/tests/v18/"` → `new: "cd {working_dir}"`

**Verify:**
```bash
grep -r "v18" 03_agents/tests/v20/.claude/agents/
# Expected: 0 matches across all agent files
grep -r "working_dir" 03_agents/tests/v20/.claude/agents/
# Expected: >= 12 matches (2 per file minimum)
grep "dashboard_url" 03_agents/tests/v20/.claude/agents/digest-email.md
# Expected: >= 2 matches
```

---

### Step 14: Update settings.local.json — add git log/diff permissions (additive only)

**File:** `03_agents/tests/v20/.claude/settings.local.json`
**Action:** Modify (ADDITIVE — do NOT remove existing entries)

**Edit — Append git log/diff to existing permissions array:**

Read the existing `settings.local.json`, parse the JSON `permissions.allow` array, append these two entries if not already present:
```
"Bash(git log:*)",
"Bash(git diff:*)"
```
Write the updated JSON back. **Do NOT remove any existing entries** — stale entries (e.g., v18 bash loop patterns) are harmless, but removing them risks violating the additive-only regression guard.

**Important:** This is a merge operation. Read existing JSON → append new entries → write back. Never overwrite the file from scratch.

**Verify:**
```bash
python3 -c "import json; d=json.load(open('03_agents/tests/v20/.claude/settings.local.json')); perms=d['permissions']['allow']; print(len(perms), 'permissions'); assert 'Bash(git log:*)' in perms; assert 'Bash(git diff:*)' in perms; print('OK: git log/diff present')"
# Expected: permission count + assertions pass
```

**Sync note (R6):** The GH Actions inline permissions list (Step 15) is authoritative for CI. The local `settings.local.json` is authoritative for interactive mode. To verify they don't drift, run:
```bash
# Compare local vs CI permission counts
python3 -c "import json; local=json.load(open('03_agents/tests/v20/.claude/settings.local.json'))['permissions']['allow']; print(f'Local: {len(local)} permissions')"
# Manually compare against the inline list in daily-digest.yml Step 15
```

---

### Phase 4: Scheduling Infrastructure

---

### Step 15: Rewrite daily-digest.yml

**File:** `.github/workflows/daily-digest.yml`
**Action:** Modify (full rewrite — changes are too interleaved for individual edits)

Replace entire file content with:

```yaml
name: Daily Job Search Digest

on:
  schedule:
    - cron: '0 6 * * 1-5'  # 06:00 UTC = 7am BST. During GMT (winter) this runs at 6am local.
  workflow_dispatch: {}

concurrency:
  group: jsa-daily-digest
  cancel-in-progress: false  # Manual workflow_dispatch during scheduled run will queue (not cancel).

permissions:
  contents: write

jobs:
  daily-digest:
    runs-on: ubuntu-latest
    timeout-minutes: 90
    defaults:
      run:
        working-directory: 03_agents/tests/v20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install python-jobspy resend playwright
          python -m playwright install chromium
      - name: Install Claude Code
        run: |
          npm install -g @anthropic-ai/claude-code
          claude --version
      - name: Preflight checks
        run: |
          which claude || { echo "ERROR: claude CLI not found on PATH"; exit 1; }
          if [ -z "$ANTHROPIC_API_KEY" ]; then
            echo "ERROR: ANTHROPIC_API_KEY is not set"
            exit 1
          fi
          echo "Preflight OK: claude CLI found, ANTHROPIC_API_KEY is set"
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Create settings.local.json
        run: |
          mkdir -p .claude
          cat > .claude/settings.local.json << 'SETTINGS_EOF'
          {
            "permissions": {
              "allow": [
                "Bash(find:*)",
                "Bash(python3:*)",
                "Bash(ls:*)",
                "Bash(git status:*)",
                "Bash(git add:*)",
                "Bash(git commit:*)",
                "Bash(git push:*)",
                "Bash(git log:*)",
                "Bash(git diff:*)",
                "WebFetch(domain:web3.career)",
                "WebFetch(domain:cryptocurrencyjobs.co)",
                "WebFetch(domain:www.remote3.co)",
                "WebFetch(domain:beincrypto.com)",
                "WebFetch(domain:laborx.com)",
                "WebFetch(domain:aijobs.app)",
                "WebFetch(domain:theaijobboard.com)",
                "WebFetch(domain:workinstartups.com)",
                "WebFetch(domain:www.ukstartupjobs.com)",
                "WebFetch(domain:aijobs.ai)",
                "WebFetch(domain:www.ycombinator.com)",
                "WebFetch(domain:www.jumpstart-uk.com)",
                "WebFetch(domain:jobs.techstars.com)",
                "WebFetch(domain:www.escapethecity.org)",
                "WebFetch(domain:builtinlondon.uk)",
                "WebSearch",
                "WebFetch(domain:cryptojobslist.com)",
                "WebFetch(domain:www.crypto.jobs)",
                "WebFetch(domain:uk.indeed.com)",
                "WebFetch(domain:careers.robinhood.com)",
                "WebFetch(domain:tether.recruitee.com)",
                "WebFetch(domain:jobs.ashbyhq.com)",
                "WebFetch(domain:mercuryo.bamboohr.com)",
                "WebFetch(domain:startup.jobs)",
                "WebFetch(domain:www.linkedin.com)",
                "WebFetch(domain:quidax.factorialhr.com)",
                "WebFetch(domain:seal.run)",
                "WebFetch(domain:nexo.breezy.hr)",
                "WebFetch(domain:jobs.lever.co)"
              ]
            }
          }
          SETTINGS_EOF
          echo "settings.local.json created with $(python3 -c "import json; print(len(json.load(open('.claude/settings.local.json'))['permissions']['allow']))" ) permissions"
          # NOTE: Heredoc indentation risk — the JSON content above is indented within
          # the YAML `run: |` scalar, which means leading whitespace is included in the
          # heredoc output. If the shell preserves this indentation, the resulting file
          # will contain leading spaces on each line, producing invalid JSON. The
          # `python3 -c "import json; print(len(json.load(...))"` validation on the line
          # above intentionally catches this at deploy time — if the JSON is malformed
          # due to indentation, the python3 command will fail with a JSONDecodeError and
          # the step will exit non-zero before proceeding.
      - name: Run scheduled digest
        uses: nick-fields/retry@v3
        with:
          timeout_minutes: 80
          max_attempts: 2
          retry_wait_seconds: 30
          command: |
            cd 03_agents/tests/v20  # Explicit cd required: nick-fields/retry@v3 command may not inherit job-level working-directory defaults
            claude --model claude-opus-4-6 --dangerously-skip-permissions --print "Run scheduled daily digest. SCHEDULED_RUN=true."
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          SCHEDULED_RUN: 'true'
      - name: Commit state
        run: |
          git config user.name "Job Search Agent"
          git config user.email "agent@autonomous.bot"
          git add state.json output/session-state.md
          STAGED=$(git diff --staged --name-only)
          for f in $STAGED; do
            case "$f" in
              03_agents/tests/v20/state.json|03_agents/tests/v20/output/session-state.md) ;;
              *) echo "ERROR: unexpected staged file: $f" && exit 1 ;;
            esac
          done
          git diff --staged --quiet || git commit -m "chore(jsa): daily digest $(date +%Y-%m-%d)"
          git push origin main
```

**Changes from current version:**
1. Version path: v18 → v20 (in working-directory, cd command, commit safeguard)
2. Timeout: 30 → 90 minutes
3. Added `--dangerously-skip-permissions` to Claude CLI invocation
4. Added preflight checks step (claude CLI + API key)
5. Added inline settings.local.json creation (replaces validation step)
6. Added retry logic via `nick-fields/retry@v3` (2 attempts, 80min timeout, 30s wait)
7. Added `git log:*` and `git diff:*` to inline settings permissions

**Dual-source permissions note (R6):** This inline permissions list is authoritative for CI (scheduled mode). The local `settings.local.json` (Step 14) is authoritative for interactive mode. When adding new permissions, update BOTH sources. The Pre-Deploy Checks section includes a comparison command to detect drift.

**Verify:**
```bash
python3 -c "import yaml; y=yaml.safe_load(open('.github/workflows/daily-digest.yml')); print('timeout:', y['jobs']['daily-digest']['timeout-minutes']); assert y['jobs']['daily-digest']['timeout-minutes'] == 90"
# Expected: timeout: 90
grep "dangerously-skip-permissions" .github/workflows/daily-digest.yml
# Expected: 1 match
grep "nick-fields/retry" .github/workflows/daily-digest.yml
# Expected: 1 match
grep "v18" .github/workflows/daily-digest.yml
# Expected: 0 matches
```

---

## Deployment Verification

### Pre-Deploy Checks

```bash
# Syntax check manage_state.py
python3 -c "import ast; ast.parse(open('03_agents/tests/v20/scripts/manage_state.py').read()); print('manage_state.py: syntax OK')"

# Run dedup tests
cd 03_agents/tests/v20 && python3 -m pytest tests/test_dedup.py -v

# Run full test suite (if other tests exist)
cd 03_agents/tests/v20 && python3 -m pytest tests/ -v --tb=short 2>/dev/null || true

# Validate YAML workflow syntax
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily-digest.yml')); print('daily-digest.yml: syntax OK')"

# Validate settings.local.json
python3 -c "import json; d=json.load(open('03_agents/tests/v20/.claude/settings.local.json')); print(f'settings: {len(d[\"permissions\"][\"allow\"])} permissions')"

# Verify no v18 references remain
grep -r "v18" 03_agents/tests/v20/.claude/agents/ 03_agents/tests/v20/CLAUDE.md .github/workflows/daily-digest.yml && echo "FAIL: v18 references found" && exit 1 || echo "OK: no v18 references"

# Verify working_dir in all agent definitions
for f in 03_agents/tests/v20/.claude/agents/*.md; do
  grep -q "working_dir" "$f" && echo "OK: $f has working_dir" || echo "WARN: $f missing working_dir"
done

# Audit Bash permissions coverage (Rec8)
# Verify settings.local.json covers all known subagent Bash commands
python3 -c "
import json
perms = json.load(open('03_agents/tests/v20/.claude/settings.local.json'))['permissions']['allow']
bash_perms = [p for p in perms if p.startswith('Bash(')]
required = ['find', 'python3', 'ls', 'git status', 'git add', 'git commit', 'git push', 'git log', 'git diff']
for r in required:
    matches = [p for p in bash_perms if r in p]
    status = 'OK' if matches else 'MISSING'
    print(f'  {status}: Bash({r}:*)')
"
```

### Post-Deploy Checks

```bash
# Manual workflow_dispatch test
gh workflow run daily-digest.yml
# Wait ~2 minutes, then check status:
gh run list --workflow=daily-digest.yml --limit=1

# Verify the run used v20 path
gh run view $(gh run list --workflow=daily-digest.yml --limit=1 --json databaseId -q '.[0].databaseId') --log | grep "v20" | head -3

# Check for preflight success
gh run view $(gh run list --workflow=daily-digest.yml --limit=1 --json databaseId -q '.[0].databaseId') --log | grep "Preflight OK"

# Verify dashboard /api/jobs returns 200 (Rec5)
# Replace DASHBOARD_URL with the actual dashboard URL from context.md
curl -sf "${DASHBOARD_URL}/api/jobs" > /dev/null && echo "OK: /api/jobs returns 200" || echo "WARN: /api/jobs health check failed"
```

### Rollback Plan

```bash
# If post-deploy checks fail, revert the workflow to v19
git log --oneline -5  # Find the commit hash before v20 changes

# Option A: Revert the specific commit
git revert <commit-hash> --no-edit
git push origin main

# Option B: Point workflow back to v19
# Edit .github/workflows/daily-digest.yml: change v20 → v19 in working-directory and cd commands
# This leaves the v20 directory in place but stops using it

# Verify rollback
gh workflow run daily-digest.yml
gh run list --workflow=daily-digest.yml --limit=1
```

## Handoff Contract

- Total steps: 15, Total phases: 4
- Files created: `03_agents/tests/v20/` (directory, copied from v19), `03_agents/tests/v20/tests/test_dedup.py`
- Files modified: `03_agents/tests/v20/scripts/manage_state.py`, `03_agents/tests/v20/CLAUDE.md`, `03_agents/tests/v20/.claude/agents/search-verify.md`, `03_agents/tests/v20/.claude/agents/brief-generator.md`, `03_agents/tests/v20/.claude/agents/digest-email.md`, `03_agents/tests/v20/.claude/agents/onboarding.md`, `03_agents/tests/v20/.claude/agents/briefs-html.md`, `03_agents/tests/v20/.claude/agents/source-researcher.md`, `03_agents/tests/v20/.claude/settings.local.json`, `.github/workflows/daily-digest.yml`
- Verification sequence: Phase 1 (dedup tests) → Phase 2 (grep assertions) → Phase 3 (grep assertions) → Phase 4 (YAML syntax + workflow_dispatch)
- Deployment verification: pre-deploy (syntax, tests, grep checks), post-deploy (manual workflow_dispatch), rollback (git revert or v19 fallback)

<!-- STAGE COMPLETE: /plan, 2026-02-18 -->
<!-- STAGE COMPLETE: /revise after round 1, 2026-02-18 -->

<\!-- STAGE COMPLETE: /revise after round 2, 2026-02-18 -->

# JSA V15 Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply 11 fixes (1 critical, 3 high, 7 medium) across 17 files — path corrections, security hardening, dead code removal, CSS dedup, expired job purging, and infrastructure improvements.

**Architecture:** No structural changes. Modifications only to existing files in the three-layer architecture (orchestrator -> agents -> skills). All changes are find-replace, code additions, or block removals.

**Tech Stack:** Python 3.12, Bash, Markdown (agent/skill definitions), YAML (GitHub Actions), JSON (settings)

**Base directory:** `03_agents/tests/v15/`

---

## Files to Modify

- Modify: `.claude/agents/brief-generator.md` (C1, M4)
- Modify: `.claude/agents/search-verify.md` (C1)
- Modify: `.claude/agents/briefs-html.md` (C1)
- Modify: `.claude/agents/digest-email.md` (C1, H3)
- Modify: `.claude/agents/onboarding.md` (C1)
- Modify: `.claude/skills/jsa-search-verify.md` (C1)
- Modify: `.claude/skills/jsa-brief-generator.md` (C1)
- Modify: `.claude/skills/jsa-digest-email.md` (H1, M3)
- Modify: `.claude/skills/jsa-briefs-html.md` (H1, M3)
- Modify: `.github/workflows/daily-digest.yml` (C1, M6)
- Modify: `CLAUDE.md` (C1, M2)
- Modify: `scripts/manage_state.py` (C1, M1)
- Modify: `scripts/preview.sh` (H2)
- Modify: `scripts/jobspy_search.py` (M5)
- Modify: `tests/test_manage_state.py` (M1)
- Modify: `tests/conftest.py` (C1)
- Modify: `.claude/settings.local.json` (M7)

---

## Implementation Steps

### Phase 1: Path Fix (C1) — MUST be first

#### Step 1.1: Replace `v14` → `v15` in all 9 agent/skill files

**Files (all paths relative to `03_agents/tests/v15/`):**

**`.claude/agents/brief-generator.md`** — Lines 17, 19:
- `03_agents/tests/v14/` → `03_agents/tests/v15/` (2 occurrences)

**`.claude/agents/search-verify.md`** — Lines 17, 19:
- `03_agents/tests/v14/` → `03_agents/tests/v15/` (2 occurrences)

**`.claude/agents/briefs-html.md`** — Lines 19, 21:
- `03_agents/tests/v14/` → `03_agents/tests/v15/` (2 occurrences)

**`.claude/agents/digest-email.md`** — Lines 23, 25:
- `03_agents/tests/v14/` → `03_agents/tests/v15/` (2 occurrences)

**`.claude/agents/onboarding.md`** — Lines 26, 28:
- `03_agents/tests/v14/` → `03_agents/tests/v15/` (2 occurrences)

**`.claude/skills/jsa-search-verify.md`** — Lines 14, 16:
- `03_agents/tests/v14/` → `03_agents/tests/v15/` (2 occurrences)

**`.claude/skills/jsa-brief-generator.md`** — Lines 14, 16:
- `03_agents/tests/v14/` → `03_agents/tests/v15/` (2 occurrences)

**Action:** For each file, use `replace_all` to replace `03_agents/tests/v14/` with `03_agents/tests/v15/`.

#### Step 1.2: Replace `v14` → `v15` in GitHub Actions workflow

**File:** `.github/workflows/daily-digest.yml`

Replace all 5 occurrences:
- Line 25: `working-directory: 03_agents/tests/v14` → `working-directory: 03_agents/tests/v15`
- Line 30: same
- Line 35: same
- Line 43: same
- Line 47: same

**Action:** Use `replace_all` to replace `03_agents/tests/v14` with `03_agents/tests/v15`.

#### Step 1.3: Replace `V14` references in Python files

**File:** `scripts/manage_state.py`
- Line 1: `"""State management for JSA V14` → `"""State management for JSA V15`
- Line 251: `description="JSA V14 State Management"` → `description="JSA V15 State Management"`

**File:** `tests/conftest.py`
- Line 1: `"""Shared fixtures for JSA V14 tests."""` → `"""Shared fixtures for JSA V15 tests."""`

#### Step 1.4: Replace `V14` reference in CLAUDE.md

**File:** `CLAUDE.md`
- Line 346: `V14 uses persistent state tracking` → `V15 uses persistent state tracking`

#### Step 1.5: Verify zero v14/V14 references remain

**Run:**
```bash
cd 03_agents/tests/v15 && grep -ri "v14" --include="*.md" --include="*.py" --include="*.yml" --include="*.json" --include="*.sh" . | grep -v ".git/"
```

**Expected:** No output (zero matches).

#### Step 1.6: Commit Phase 1

```bash
cd /Users/ryanhennebry/Projects/autonomous1 && git add 03_agents/tests/v15/.claude/agents/brief-generator.md 03_agents/tests/v15/.claude/agents/search-verify.md 03_agents/tests/v15/.claude/agents/briefs-html.md 03_agents/tests/v15/.claude/agents/digest-email.md 03_agents/tests/v15/.claude/agents/onboarding.md 03_agents/tests/v15/.claude/skills/jsa-search-verify.md 03_agents/tests/v15/.claude/skills/jsa-brief-generator.md 03_agents/tests/v15/.github/workflows/daily-digest.yml 03_agents/tests/v15/scripts/manage_state.py 03_agents/tests/v15/tests/conftest.py 03_agents/tests/v15/CLAUDE.md && git commit -m "fix(jsa-v15): replace all v14 path references with v15 (C1)"
```

---

### Phase 2: Security (H1, H2)

#### Step 2.1: Add HTML-escape instruction to `jsa-digest-email.md`

**File:** `.claude/skills/jsa-digest-email.md`

After line 8 (the `## Core Rules` heading is at line 31), insert a new rule after rule 9. Add as rule 10:

```
10. **HTML escaping:** Before inserting ANY external job data (title, company, location, notes, gaps) into HTML, escape `<`, `>`, `&`, `"`, and `'` characters. Validate all `job_url` values start with `https://` or `http://` — reject other schemes (javascript:, data:, etc.) and render as plain text with "(invalid URL)" note.
```

**Action:** Edit `.claude/skills/jsa-digest-email.md` — after line `9. **No colored warning text.**...` (the last core rule), add a blank line and rule 10.

#### Step 2.2: Add HTML-escape instruction to `jsa-briefs-html.md`

**File:** `.claude/skills/jsa-briefs-html.md`

After the existing "CSS rules:" section in Step 2 (around line 27), add a new bullet:

```
- **HTML escaping:** Before inserting ANY external job data (title, company, location, notes, gaps) into HTML, escape `<`, `>`, `&`, `"`, and `'` characters. Validate all `job_url` values start with `https://` or `http://` — reject other schemes and render as plain text.
```

**Action:** Edit `.claude/skills/jsa-briefs-html.md` — after the line `- NO page break CSS rules — this is an HTML file viewed in-browser, not a PDF` (line 30), add the HTML escaping bullet.

#### Step 2.3: Harden `scripts/preview.sh` (H2)

**File:** `scripts/preview.sh`

Two changes:

1. Line 27: Add `--bind 127.0.0.1` to the Python HTTP server command:
   - Old: `python3 -m http.server $PORT &>/dev/null &`
   - New: `python3 -m http.server $PORT --bind 127.0.0.1 &>/dev/null &`

2. Add a cleanup trap after `set -e` (line 5). Insert after line 5:
```bash
cleanup() { kill $SERVER_PID 2>/dev/null || true; }
```
And after `SERVER_PID=$!` (line 28), add:
```bash
trap cleanup EXIT
```

**Full replacement for lines 5-28:**

Old (line 5):
```
set -e
```
New (line 5-7):
```
set -e
SERVER_PID=""
cleanup() { kill "$SERVER_PID" 2>/dev/null || true; }
```

Old (line 27-28):
```
python3 -m http.server $PORT &>/dev/null &
SERVER_PID=$!
```
New:
```
python3 -m http.server $PORT --bind 127.0.0.1 &>/dev/null &
SERVER_PID=$!
trap cleanup EXIT
```

#### Step 2.4: Commit Phase 2

```bash
cd /Users/ryanhennebry/Projects/autonomous1 && git add 03_agents/tests/v15/.claude/skills/jsa-digest-email.md 03_agents/tests/v15/.claude/skills/jsa-briefs-html.md 03_agents/tests/v15/scripts/preview.sh && git commit -m "fix(jsa-v15): add HTML escaping rules and harden preview server (H1, H2)"
```

---

### Phase 3: Housekeeping (H3, M2, M5)

#### Step 3.1: Remove stale Phase 5 note from `digest-email.md` (H3)

**File:** `.claude/agents/digest-email.md`

Delete line 21:
```
**Note:** This agent definition is written with 7 variables from the start. The jsa-digest-email skill is a placeholder until Phase 5 (Task 5.1) — digest-email is non-functional until Phase 5 is complete.
```

Replace with empty string (remove the line entirely).

#### Step 3.2: Add parallel dispatch instruction to CLAUDE.md Step 17 (M2)

**File:** `CLAUDE.md`

Find the existing Step 17 text (around line 197):
```
**Step 17: Dispatch brief agents** for accepted jobs, auto-retry once on failure.
```

Replace with:
```
**Step 17: Dispatch brief agents in parallel** for accepted jobs, auto-retry once on failure.

If 3+ briefs are needed, dispatch all brief agents in a single message with multiple Task tool calls (parallel dispatch). If 1-2 briefs, sequential dispatch is fine.
```

#### Step 3.3: Remove dead code from `scripts/jobspy_search.py` (M5)

**File:** `scripts/jobspy_search.py`

Five deletions (apply from highest line numbers first to preserve line stability):

1. **Remove `--exclude-titles` argument** (line 32):
   Delete: `    parser.add_argument("--exclude-titles", help="Comma-separated title keywords to exclude")`

2. **Remove `filter_jobs_by_title()` function** (lines 37-53):
   Delete the entire function:
   ```python
   def filter_jobs_by_title(jobs: list[dict[str, Any]], exclude_titles: str) -> tuple[list[dict[str, Any]], int]:
       """
       Filter jobs by excluding titles containing specified keywords.
       Returns (filtered_jobs, excluded_count).
       """
       # Parse exclusions, filtering out empty strings
       exclusions = [x.strip().lower() for x in exclude_titles.split(",") if x.strip()]

       if not exclusions:
           return jobs, 0

       filtered = []
       excluded_count = 0

       for job in jobs:
           title = job.get("title", "").lower()
           if any(ex in title for ex in exclusions):
               excluded_count += 1
           else:
               filtered.append(job)

       return filtered, excluded_count
   ```

3. **Remove the conditional call in `main()`** (lines 100-102):
   Delete:
   ```python
           # Apply title exclusion filter
           excluded_count = 0
           if args.exclude_titles:
               results, excluded_count = filter_jobs_by_title(results, args.exclude_titles)
   ```

   And update `build_output` call (line 105) — remove `excluded_count` parameter:
   Old:
   ```python
           # Build output
           output = build_output(
               query=args.query,
               location=args.location,
               remote=args.remote,
               jobs=results,
               excluded_count=excluded_count,
           )
   ```
   New:
   ```python
           # Build output
           output = build_output(
               query=args.query,
               location=args.location,
               remote=args.remote,
               jobs=results,
           )
   ```

4. **Remove `excluded_count` reference in output message** (lines 114-116 in `main()`):
   Old:
   ```python
            msg = f"Wrote {len(results)} jobs to {args.output}"
            if excluded_count:
                msg += f" (excluded {excluded_count} by title)"
   ```
   New:
   ```python
            msg = f"Wrote {len(results)} jobs to {args.output}"
   ```

5. **Remove `excluded_count` parameter and conditional from `build_output()`** (lines 55-72):
   Old:
   ```python
   def build_output(
       query: str,
       location: str,
       remote: bool,
       jobs: list[dict[str, Any]],
       excluded_count: int = 0,
   ) -> dict[str, Any]:
       """Build the output dictionary with metadata."""
       output: dict[str, Any] = {
           "query": query,
           "location": location,
           "remote": remote,
           "searched_at": datetime.now().isoformat(),
           "count": len(jobs),
           "jobs": jobs,
       }

       if excluded_count > 0:
           output["excluded_by_title"] = excluded_count

       return output
   ```
   New:
   ```python
   def build_output(
       query: str,
       location: str,
       remote: bool,
       jobs: list[dict[str, Any]],
   ) -> dict[str, Any]:
       """Build the output dictionary with metadata."""
       return {
           "query": query,
           "location": location,
           "remote": remote,
           "searched_at": datetime.now().isoformat(),
           "count": len(jobs),
           "jobs": jobs,
       }
   ```

#### Step 3.4: Verify no `--exclude-titles` remains

**Run:**
```bash
cd 03_agents/tests/v15 && grep -r "exclude.titles\|filter_jobs_by_title" --include="*.py" .
```

**Expected:** No output.

#### Step 3.5: Commit Phase 3

```bash
cd /Users/ryanhennebry/Projects/autonomous1 && git add 03_agents/tests/v15/.claude/agents/digest-email.md 03_agents/tests/v15/CLAUDE.md 03_agents/tests/v15/scripts/jobspy_search.py && git commit -m "fix(jsa-v15): remove stale note, add parallel briefs, remove dead filter code (H3, M2, M5)"
```

---

### Phase 4: CSS Dedup (M3)

> **Note:** Line numbers below reference the file state BEFORE Phases 2-3 modifications. After Phase 2 inserts new content into both `jsa-digest-email.md` and `jsa-briefs-html.md`, all subsequent line numbers shift. Use section headers (e.g., `## Email HTML Skeleton`, `## Link Styling`) as content anchors for find-replace rather than relying on exact line numbers.

#### Step 4.1: Remove duplicated CSS from `jsa-digest-email.md`

**File:** `.claude/skills/jsa-digest-email.md`

**Remove the "Email HTML Skeleton" section** (lines 158-197). This is a full HTML template that duplicates what's already in `jsa-design-system.md` (the "Email structure (table layout)" section at lines 255-276 and the "Email CSS Block (Complete)" at lines 224-253).

Replace lines 158-197 with:
```
## Email HTML Skeleton

Use the Email HTML structure and CSS from the preloaded `jsa-design-system` skill exactly. The design system contains the complete table-based email layout, responsive media queries, and Gmail override CSS. Do not duplicate or modify that structure here.
```

**Remove the "Link Styling (Email)" section** (lines 199-213). This is an exact duplicate of the Link Styling section in `jsa-design-system.md` (lines 188-220).

Replace lines 199-213 with:
```
## Link Styling

Follow the link styling from the preloaded `jsa-design-system` skill — dark editorial style with Gmail color override. Do not duplicate the CSS here.
```

#### Step 4.2: Remove duplicated CSS from `jsa-briefs-html.md`

**File:** `.claude/skills/jsa-briefs-html.md`

**Remove the brief separator CSS block** (lines 32-44). This is an exact copy of the `.brief-page` CSS in `jsa-design-system.md` (lines 443-453).

Replace lines 32-44 with:
```
Use the `.brief-page` separator CSS from the preloaded `jsa-design-system` skill exactly. Do not duplicate the CSS here.
```

**Remove the `h1 a` link style** (line 50). This duplicates the link styling in `jsa-design-system.md`.

Replace line 50:
```
- Style the link with a **visible** subtle underline: `color:#1c1917;text-decoration:underline;text-underline-offset:4px;text-decoration-thickness:1px;text-decoration-color:#d6d3d1;`
- Add style in the `<style>` block: `h1 a { color: #1c1917; text-decoration: underline; text-underline-offset: 4px; text-decoration-thickness: 1px; text-decoration-color: #d6d3d1; }`
```
with:
```
- Style links using the link styling from the preloaded `jsa-design-system` skill (dark editorial style with subtle stone underline)
```

#### Step 4.3: Verify no large duplicated CSS blocks remain

**Run:**
```bash
cd 03_agents/tests/v15 && grep -c "border-radius:3px\|font-family:'DM Sans'" .claude/skills/jsa-digest-email.md .claude/skills/jsa-briefs-html.md
```

Inline style examples in card/table templates are expected (subagents need them for email rendering). What should NOT remain are standalone CSS blocks that duplicate the design system.

#### Step 4.4: Commit Phase 4

```bash
cd /Users/ryanhennebry/Projects/autonomous1 && git add 03_agents/tests/v15/.claude/skills/jsa-digest-email.md 03_agents/tests/v15/.claude/skills/jsa-briefs-html.md && git commit -m "fix(jsa-v15): deduplicate CSS — reference design system skill instead (M3)"
```

---

### Phase 5: Python + Agent (M1, M4)

#### Step 5.1: Write failing tests for `purge_expired()` (M1 — TDD)

**File:** `tests/test_manage_state.py`

Add a new test class at the end of the file:

```python
class TestPurgeExpired:
    """Tests for purge_expired() — remove old expired jobs."""

    def test_purge_removes_jobs_older_than_90_days(self, empty_state, verified_dir):
        """Expired jobs older than 90 days are removed from expired_jobs."""
        from manage_state import update_state, purge_expired

        job = make_verified_json(title="Old Role", company="Gone Corp", score=75)
        job_path = verified_dir / "community-manager" / "gone-corp-old-role.json"
        job_path.write_text(json.dumps(job), encoding="utf-8")

        # Run 1: job appears
        state = update_state(empty_state, verified_dir, "2025-01-01", ["community-manager"])

        # Remove file and expire after 15 days
        job_path.unlink()
        state = update_state(state, verified_dir, "2025-01-16", ["community-manager"])
        assert "community-manager/gone-corp-old-role" in state.expired_jobs

        # Purge: 91 days after expiry date (2025-01-16 + 91 = 2025-04-17)
        state = purge_expired(state, "2025-04-17")
        assert "community-manager/gone-corp-old-role" not in state.expired_jobs

    def test_purge_keeps_recently_expired_jobs(self, empty_state, verified_dir):
        """Expired jobs less than 90 days old are kept."""
        from manage_state import update_state, purge_expired

        job = make_verified_json(title="Recent Role", company="Fresh Corp", score=80)
        job_path = verified_dir / "community-manager" / "fresh-corp-recent-role.json"
        job_path.write_text(json.dumps(job), encoding="utf-8")

        # Run 1: job appears
        state = update_state(empty_state, verified_dir, "2025-06-01", ["community-manager"])

        # Remove file and expire after 15 days
        job_path.unlink()
        state = update_state(state, verified_dir, "2025-06-16", ["community-manager"])
        assert "community-manager/fresh-corp-recent-role" in state.expired_jobs

        # Purge: only 30 days after expiry (2025-06-16 + 30 = 2025-07-16)
        state = purge_expired(state, "2025-07-16")
        assert "community-manager/fresh-corp-recent-role" in state.expired_jobs
```

#### Step 5.2: Run tests to verify they fail

**Run:**
```bash
cd 03_agents/tests/v15 && python3 -m pytest tests/test_manage_state.py::TestPurgeExpired -v
```

**Expected:** 2 ERRORS — `ImportError: cannot import name 'purge_expired' from 'manage_state'` (collection errors, not test failures)

#### Step 5.3: Implement `purge_expired()` in `manage_state.py` (M1)

**File:** `scripts/manage_state.py`

Add the function after the existing `compute_delta()` function (around line 191, before `record_action()`):

```python
PURGE_DAYS = 90


def purge_expired(state: State, run_date: str) -> State:
    """Remove expired jobs older than PURGE_DAYS from state.expired_jobs."""
    run_dt = datetime.strptime(run_date, "%Y-%m-%d")
    purge_threshold = run_dt - timedelta(days=PURGE_DAYS)

    keys_to_purge = []
    for key, entry in state.expired_jobs.items():
        if entry.expired_date:
            try:
                expired_dt = datetime.strptime(entry.expired_date, "%Y-%m-%d")
            except ValueError:
                continue  # Skip entries with malformed dates
            if expired_dt <= purge_threshold:
                keys_to_purge.append(key)

    for key in keys_to_purge:
        del state.expired_jobs[key]

    return state
```

#### Step 5.4: Call `purge_expired()` in `_cli_sync()`

**File:** `scripts/manage_state.py`

In the `_cli_sync()` function, add the purge call after `update_state()` and before `save_state()`:

Old (lines 232-234):
```python
    state = load_state(state_path)
    state = update_state(state, verified_dir, args.run_date, searched)
    save_state(state, state_path)
```

New:
```python
    state = load_state(state_path)
    state = update_state(state, verified_dir, args.run_date, searched)
    state = purge_expired(state, args.run_date)
    save_state(state, state_path)
```

#### Step 5.5: Run tests to verify they pass

**Run:**
```bash
cd 03_agents/tests/v15 && python3 -m pytest tests/test_manage_state.py -v
```

**Expected:** 16 passed (14 existing + 2 new purge tests).

#### Step 5.6: Fix `brief-generator.md` failure behavior (M4)

**File:** `.claude/agents/brief-generator.md`

The current behavior (line 15):
```
**If any variable is missing or null:** Do NOT write any output files. Exit immediately.
```

This silently exits without writing a status file. All other 4 agents write a `_status.json` on failure. Fix:

Replace line 15 with:
```
**If any variable is missing or null:** Write `output/briefs/_brief_generator_status.json` with `{"status": "failed", "error": "Missing variable: {name}"}` and exit immediately. Do NOT write any brief output files.
```

> **Note:** This uses `_brief_generator_status.json` (not `_status.json`) because `output/briefs/_status.json` is already used by the `briefs-html` subagent. The parent orchestrator checks brief completion via the `<!-- BRIEF COMPLETE -->` sentinel in brief files (CLAUDE.md Step 17), not via this status file. This status file is for failure diagnostics only.

#### Step 5.7: Commit Phase 5

```bash
cd /Users/ryanhennebry/Projects/autonomous1 && git add 03_agents/tests/v15/scripts/manage_state.py 03_agents/tests/v15/tests/test_manage_state.py 03_agents/tests/v15/.claude/agents/brief-generator.md && git commit -m "fix(jsa-v15): add purge_expired() with tests, fix brief-generator status (M1, M4)"
```

---

### Phase 6: Infrastructure (M6, M7)

#### Step 6.1: Add staged-file verification to CI workflow (M6)

**File:** `.github/workflows/daily-digest.yml`

In the "Commit state" step, add verification that only expected files are staged. Replace the existing commit step:

Old:
```yaml
      - name: Commit state
        working-directory: 03_agents/tests/v15
        run: |
          git config user.name "Job Search Agent"
          git config user.email "agent@autonomous.bot"
          git add state.json output/session-state.md
          git diff --staged --quiet || git commit -m "chore(jsa): daily digest $(date +%Y-%m-%d)"
          git push origin main
```

New:
```yaml
      - name: Commit state
        working-directory: 03_agents/tests/v15
        run: |
          git config user.name "Job Search Agent"
          git config user.email "agent@autonomous.bot"
          git add state.json output/session-state.md
          STAGED=$(git diff --staged --name-only)
          for f in $STAGED; do
            case "$f" in
              state.json|output/session-state.md) ;;
              *) echo "ERROR: unexpected staged file: $f" && exit 1 ;;
            esac
          done
          git diff --staged --quiet || git commit -m "chore(jsa): daily digest $(date +%Y-%m-%d)"
          git push origin main
```

#### Step 6.2: Narrow permissions in `settings.local.json` (M7)

**File:** `.claude/settings.local.json`

Replace the overly broad `rm` and `curl` permissions:

Old:
```json
      "Bash(rm:*)",
```
New:
```json
      "Bash(rm:output/*)",
```

Old:
```json
      "Bash(curl:*)",
```
New:
```json
      "Bash(curl:http://localhost:*)",
```

#### Step 6.3: Commit Phase 6

```bash
cd /Users/ryanhennebry/Projects/autonomous1 && git add 03_agents/tests/v15/.github/workflows/daily-digest.yml 03_agents/tests/v15/.claude/settings.local.json && git commit -m "fix(jsa-v15): add staged-file verification, narrow permissions (M6, M7)"
```

---

### Final Verification

#### Step 7.1: Run all tests

```bash
cd 03_agents/tests/v15 && python3 -m pytest tests/ -v
```

**Expected:** 16 passed (14 existing + 2 new purge tests).

#### Step 7.2: Verify all 8 success criteria

| # | Criterion | Verification command |
|---|-----------|---------------------|
| 1 | Zero v14/V14 references | `grep -ri "v14" --include="*.md" --include="*.py" --include="*.yml" --include="*.json" --include="*.sh" . \| grep -v ".git/"` → empty |
| 2 | 16 tests pass | `python3 -m pytest tests/ -v` → 16 passed |
| 3 | No --exclude-titles | `grep -r "exclude.titles" --include="*.py" .` → empty |
| 4 | No duplicated CSS blocks in skills | Manual check: `jsa-digest-email.md` and `jsa-briefs-html.md` reference design system, no standalone CSS blocks |
| 5 | All 5 agents write _status.json on failure | Grep agent failure handlers: `grep -A1 "missing or null" .claude/agents/*.md` → all write status JSON |
| 6 | Preview binds localhost | `grep "bind 127.0.0.1" scripts/preview.sh` → match |
| 7 | CI verifies staged files | `grep "unexpected staged file" .github/workflows/daily-digest.yml` → match |
| 8 | Permissions scoped | `grep "rm:output" .claude/settings.local.json && grep "localhost" .claude/settings.local.json` → both match |

---

## Handoff Contract

- Total steps: 22 (across 7 phases including verification)
- Total phases: 7 (6 implementation + 1 verification)
- Files created: 0
- Files modified: 17
- Verification sequence: Phase 1 verify (grep v14) → Phase 3 verify (grep exclude-titles) → Phase 5 tests (pytest) → Phase 7 full verification (all 8 criteria)

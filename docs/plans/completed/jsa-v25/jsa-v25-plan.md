# Plan: JSA V25 — Full Fix with Three-Layer Approach

## Overview

Three-Layer implementation (Infrastructure → Orchestration → UX) addressing V24's 15 failures. Layer 1 fixes scripts to provide structural enforcement. Layer 2 wires gates and implements architectural changes (tiered delivery, dispatch counter, post-compaction recovery). Layer 3 adds UX protocol rules for progress, status, and selection formatting.

Success criteria: <=10 failures, zero chronic regression recurrence, delivery always completes, all gates fire.

## Files to Modify

### New version directory (copy v24 → v25)
- `03_agents/tests/v25/` — Full copy of v24, then apply fixes

### Layer 1: Scripts
- `scripts/preflight.sh` — First-run detection
- `scripts/manage_state.py` — New `verify-and-commit`, `verify-session-state-written`, `increment-dispatch-counter`, `check-dispatch-budget` subcommands
- `.claude/agents/search-verify.md` — Sentinel enforcement + schema validation

### Layer 2: Orchestration + Config
- `references/orchestration.md` — Structural gates, tiered delivery, dispatch counter, post-compaction recovery, constraint compliance, context.md validation, task ID persistence
- `CLAUDE.md` — Dispatch counter ceiling, HC-5 fix, startup git pull, post-compaction rule

### Layer 3: UX
- `references/orchestration.md` — UX Protocol section (7 rules with exact format strings)

### Tests
- `tests/test_preflight.py` — First-run detection tests (3 new)
- `tests/test_manage_state.py` — verify-and-commit (3 new) + verify-session-state-written (4 new) tests
- `tests/test_schema_validation.py` — New: sentinel (2) + schema validation (4) tests
- `tests/test_dispatch_counter.py` — New: dispatch counter budget tests (7)
- `tests/test_orchestration.py` — New: gate, delivery, compaction, constraint, UX tests (25+)

## Implementation Steps

### Phase 1: Infrastructure (Layer 1 — Script Fixes)

#### Step 1: Copy v24 to v25
**File:** `03_agents/tests/v25/`
**Action:** Create (copy directory)
**Description:** Copy entire v24 directory to v25 as starting point.

```bash
cp -r 03_agents/tests/v24 03_agents/tests/v25
```

**Verify:**
- Test: `ls 03_agents/tests/v25/scripts/manage_state.py && echo "OK"`

---

#### Step 2: Write failing test for preflight first-run detection
**File:** `03_agents/tests/v25/tests/test_preflight.py`
**Action:** Modify

Add `import shutil` to the existing imports at the top of the file (after `import textwrap`).

Append new test class at end of file (after `TestPreflightSchemaValidation`):

```python
class TestPreflightFirstRun:
    """Tests for first-run detection: empty output/verified/ skips safety bounds."""

    def test_first_run_empty_verified_exits_zero(self, tmp_path: Path) -> None:
        """Empty output/verified/ (first run) should exit 0 even with --env."""
        _setup_passing_tree(tmp_path)
        # Ensure output/verified/ exists but is empty (no role subdirs with jobs)
        verified_dir = tmp_path / "output" / "verified"
        verified_dir.mkdir(parents=True, exist_ok=True)
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 0, (
            f"First run (empty verified/) should exit 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_first_run_missing_verified_exits_zero(self, tmp_path: Path) -> None:
        """Missing output/verified/ (first run) should exit 0 even with --env."""
        _setup_passing_tree(tmp_path)
        # Remove output/verified/ entirely if it exists
        verified_dir = tmp_path / "output" / "verified"
        if verified_dir.exists():
            shutil.rmtree(verified_dir)
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 0, (
            f"First run (missing verified/) should exit 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_existing_output_uses_normal_bounds(self, tmp_path: Path) -> None:
        """Existing output/verified/ with data uses normal safety bounds."""
        _setup_passing_tree(tmp_path)
        # Create a verified dir with actual job files
        verified_dir = tmp_path / "output" / "verified" / "ai-engineer"
        verified_dir.mkdir(parents=True, exist_ok=True)
        (verified_dir / "acme-job.json").write_text(
            json.dumps({
                "job_id": "acme-001", "title": "Engineer", "company": "Acme",
                "job_url": "https://example.com", "role_type": "ai-engineer",
                "score": 85, "source_channel": "direct-career-pages",
                "run_date": "2026-02-27", "location": "Remote", "status": "verified",
            }),
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 0, (
            f"Existing output should pass normal bounds.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_preflight.py -v -k first_run` (expect FAIL)

---

#### Step 3: Implement preflight first-run detection
**File:** `03_agents/tests/v25/scripts/preflight.sh`
**Action:** Modify

Replace the entire SCHEMA TIER block (lines 310-332) with a guarded version that detects first run:

```bash
# ===================================================================
# SCHEMA TIER -- verified JSON schema validation checks
# ===================================================================
if [[ "$RUN_ENV" == "true" ]]; then

    # --- First-run detection ---
    # If output/verified/ is empty or missing, skip schema/model checks (nothing to validate).
    FIRST_RUN=false
    if [[ ! -d "output/verified" ]]; then
        FIRST_RUN=true
    else
        # Check if verified/ has any non-underscore JSON files in subdirs
        VERIFIED_COUNT=$(find "output/verified" -mindepth 2 -name "*.json" ! -name "_*" 2>/dev/null | head -1 | wc -l | tr -d ' ')
        if [[ "$VERIFIED_COUNT" -eq 0 ]]; then
            FIRST_RUN=true
        fi
    fi

    if [[ "$FIRST_RUN" == "true" ]]; then
        echo "First run detected (empty output/verified/) -- skipping schema validation"
    else
        # 1. Validate all verified JSONs conform to canonical schema
        if python3 scripts/manage_state.py validate-schema 2>/dev/null; then
            : # schema validation passed
        else
            fail "[PREFLIGHT FAIL] Schema validation failed -- run migrate-schema first"
        fi
    fi

    # 2. Verify search-verify agent is on Sonnet tier
    if [[ -f ".claude/agents/search-verify.md" ]]; then
        if ! grep -q "^model: sonnet$" ".claude/agents/search-verify.md"; then
            fail "[PREFLIGHT FAIL] search-verify agent not on Sonnet tier"
        fi
    else
        fail "[PREFLIGHT FAIL] search-verify agent not on Sonnet tier"
    fi

    if [[ "$FAILED" -ne 0 ]]; then
        exit 1
    fi
fi
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_preflight.py -v -k first_run` (expect PASS)
- Lint: `cd 03_agents/tests/v25 && shellcheck scripts/preflight.sh`

---

#### Step 4: Write failing test for verify-and-commit subcommand
**File:** `03_agents/tests/v25/tests/test_manage_state.py`
**Action:** Modify

Append new test class at end of file (after `TestMigrateSchema`):

```python
# ---------------------------------------------------------------------------
# Tests for verify-and-commit subcommand
# ---------------------------------------------------------------------------


class TestVerifyAndCommit:
    """Tests for the verify-and-commit subcommand of manage_state.py."""

    def test_dirty_output_stages_commits_exits_zero(self, tmp_path: Path) -> None:
        """Dirty output/ directory: stages, commits, exits 0."""
        repo = tmp_path / "repo"
        _init_git_repo(repo)

        # Create initial commit
        (repo / "README.md").write_text("placeholder")
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "initial")

        # Create dirty output directory with a new file
        output_dir = repo / "output"
        verified_dir = output_dir / "verified" / "ai-engineer"
        verified_dir.mkdir(parents=True)
        (verified_dir / "job.json").write_text('{"title": "test"}')

        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-and-commit",
                "--output-dir",
                str(output_dir),
                "--phase-label",
                "search",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo),
        )
        assert result.returncode == 0, (
            f"dirty output should stage+commit and exit 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        # Verify the file is now committed
        status = _git(repo, "status", "--porcelain", str(output_dir))
        assert status.stdout.strip() == "", (
            f"output should be clean after commit: {status.stdout}"
        )

    def test_clean_output_exits_zero(self, tmp_path: Path) -> None:
        """Clean output/ directory (nothing to commit): exits 0."""
        repo = tmp_path / "repo"
        _init_git_repo(repo)

        # Create initial commit with output dir
        output_dir = repo / "output"
        verified_dir = output_dir / "verified" / "ai-engineer"
        verified_dir.mkdir(parents=True)
        (verified_dir / "job.json").write_text('{"title": "test"}')
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "initial")

        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-and-commit",
                "--output-dir",
                str(output_dir),
                "--phase-label",
                "search",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo),
        )
        assert result.returncode == 0, (
            f"clean output should exit 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_commit_message_contains_phase_label(self, tmp_path: Path) -> None:
        """Commit message includes the phase label."""
        repo = tmp_path / "repo"
        _init_git_repo(repo)

        (repo / "README.md").write_text("placeholder")
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "initial")

        output_dir = repo / "output"
        verified_dir = output_dir / "verified" / "ai-engineer"
        verified_dir.mkdir(parents=True)
        (verified_dir / "job.json").write_text('{"title": "test"}')

        subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-and-commit",
                "--output-dir",
                str(output_dir),
                "--phase-label",
                "search",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo),
        )
        log = _git(repo, "log", "--oneline", "-1")
        assert "search" in log.stdout.lower(), (
            f"commit message should contain phase label 'search': {log.stdout}"
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_manage_state.py -v -k verify_and_commit` (expect FAIL)

---

#### Step 5: Implement verify-and-commit subcommand
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify

Add implementation function before `main()` (around line 1178):

```python
# ---------------------------------------------------------------------------
# verify-and-commit subcommand
# ---------------------------------------------------------------------------


def _cli_verify_and_commit(args: argparse.Namespace) -> None:
    """Stage and commit all changes under output/, then optionally push.

    Commit and push are separate operations so network failure does not
    block the local commit (the critical operation).

    Exit codes:
      0 — success (committed, pushed if --push)
      0 — nothing to commit (clean)
      1 — commit failure or push failure (transient)
      2 — merge conflict (unrecoverable)
    """
    output_dir = Path(args.output_dir)
    phase_label = args.phase_label
    do_push = getattr(args, "push", True)

    # Check if output/ has any uncommitted changes
    status_result = subprocess.run(
        ["git", "status", "--porcelain", str(output_dir)],
        capture_output=True,
        text=True,
    )
    if not status_result.stdout.strip():
        print("Nothing to commit (output/ is clean)")
        return  # exit 0

    # Stage all changes under output/
    add_result = subprocess.run(
        ["git", "add", str(output_dir)],
        capture_output=True,
        text=True,
    )
    if add_result.returncode != 0:
        print(f"ERROR: git add failed: {add_result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Commit with phase label
    commit_msg = f"chore(jsa): {phase_label} — auto-commit verified output"
    commit_result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        capture_output=True,
        text=True,
    )
    if commit_result.returncode != 0:
        print(f"ERROR: git commit failed: {commit_result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"Committed output/ changes ({phase_label})")

    # Push (optional, separate from commit)
    if not do_push:
        return  # exit 0 — committed but not pushed

    push_result = subprocess.run(
        ["git", "push"],
        capture_output=True,
        text=True,
    )
    if push_result.returncode != 0:
        stderr = push_result.stderr.lower()
        if "conflict" in stderr or "merge" in stderr:
            print(f"ERROR: merge conflict during push: {push_result.stderr}", file=sys.stderr)
            sys.exit(2)
        # Non-fast-forward rejection: attempt pull --ff-only before retry
        if "non-fast-forward" in stderr or "fetch first" in stderr:
            print("Non-fast-forward rejection — attempting git pull --ff-only before retry", file=sys.stderr)
            pull_result = subprocess.run(
                ["git", "pull", "--ff-only"],
                capture_output=True,
                text=True,
            )
            if pull_result.returncode != 0:
                print(f"ERROR: git pull --ff-only failed: {pull_result.stderr}", file=sys.stderr)
                sys.exit(2)
            # Retry push after successful pull
            retry_result = subprocess.run(
                ["git", "push"],
                capture_output=True,
                text=True,
            )
            if retry_result.returncode != 0:
                print(f"ERROR: git push failed after pull: {retry_result.stderr}", file=sys.stderr)
                sys.exit(1)
            print(f"Pushed output/ changes ({phase_label}) after pull --ff-only")
            return
        print(f"WARNING: git push failed (commit succeeded locally): {push_result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"Pushed output/ changes ({phase_label})")
```

Add CLI parser inside `main()` after the `check-dashboard-url` parser block:

```python
    # --- verify-and-commit ---
    vac_parser = subparsers.add_parser(
        "verify-and-commit",
        help="Stage, commit, and push all changes under output/",
    )
    vac_parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default="output",
        help="Path to output directory (default: output)",
    )
    vac_parser.add_argument(
        "--phase-label",
        dest="phase_label",
        default="search",
        help="Phase label for commit message (default: search)",
    )
    vac_parser.add_argument(
        "--no-push",
        dest="push",
        action="store_false",
        default=True,
        help="Commit only, do not push (useful when network is unavailable)",
    )
    vac_parser.set_defaults(func=_cli_verify_and_commit)
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_manage_state.py -v -k verify_and_commit` (expect PASS)
- Lint: `cd 03_agents/tests/v25 && ruff check scripts/manage_state.py`
- Type check: `cd 03_agents/tests/v25 && mypy scripts/manage_state.py --ignore-missing-imports`

---

#### Step 6: Write failing test for verify-session-state-written subcommand
**File:** `03_agents/tests/v25/tests/test_manage_state.py`
**Action:** Modify

Append new test class at end of file:

```python
# ---------------------------------------------------------------------------
# Tests for verify-session-state-written subcommand
# ---------------------------------------------------------------------------


class TestVerifySessionStateWritten:
    """Tests for the verify-session-state-written subcommand."""

    def test_has_today_date_exits_zero(self, tmp_path: Path) -> None:
        """session-state.md contains today's date entry, exits 0."""
        session_state = tmp_path / "session-state.md"
        session_state.write_text(
            "# Session State\n\n## 2026-02-27\n\nSearch batch 1 complete.\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-session-state-written",
                "--session-state-path",
                str(session_state),
                "--run-date",
                "2026-02-27",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            f"session-state.md with today's date should exit 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_missing_today_date_exits_one(self, tmp_path: Path) -> None:
        """session-state.md without today's date entry, exits 1."""
        session_state = tmp_path / "session-state.md"
        session_state.write_text(
            "# Session State\n\n## 2026-02-25\n\nOld batch data.\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-session-state-written",
                "--session-state-path",
                str(session_state),
                "--run-date",
                "2026-02-27",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 1, (
            f"session-state.md without today's date should exit 1.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_missing_file_exits_one(self, tmp_path: Path) -> None:
        """Missing session-state.md file, exits 1."""
        nonexistent = str(tmp_path / "nonexistent" / "session-state.md")
        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-session-state-written",
                "--session-state-path",
                nonexistent,
                "--run-date",
                "2026-02-27",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 1, (
            f"missing session-state.md should exit 1.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_date_in_content_not_heading_exits_zero(self, tmp_path: Path) -> None:
        """Date appears in body text (not just heading), exits 0."""
        session_state = tmp_path / "session-state.md"
        session_state.write_text(
            "# Session State\n\nRun date: 2026-02-27. Batch complete.\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(MANAGE_STATE),
                "verify-session-state-written",
                "--session-state-path",
                str(session_state),
                "--run-date",
                "2026-02-27",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            f"date in body text should still count.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_manage_state.py -v -k verify_session_state` (expect FAIL)

---

#### Step 7: Implement verify-session-state-written subcommand
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify

Add implementation function (after `_cli_verify_and_commit`):

```python
# ---------------------------------------------------------------------------
# verify-session-state-written subcommand
# ---------------------------------------------------------------------------


def _cli_verify_session_state_written(args: argparse.Namespace) -> None:
    """Verify session-state.md contains an entry for the given run date.

    Two-tier check (simplified per code-simplicity-reviewer):
    1. Check for `## {date}` heading
    2. Fall back to plain string match anywhere in file

    Exits 0 if found, exits 1 if missing or file does not exist.
    """
    session_state_path = Path(args.session_state_path)
    run_date = args.run_date

    if not session_state_path.exists():
        print(
            f"ERROR: session-state.md not found: {session_state_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    content = session_state_path.read_text(encoding="utf-8")

    # Tier 1: heading match
    if f"## {run_date}" in content:
        print(f"OK: session-state.md contains entry for {run_date}")
        return

    # Tier 2: plain string match anywhere
    if run_date in content:
        print(f"OK: session-state.md contains entry for {run_date}")
        return

    print(
        f"ERROR: session-state.md does not contain entry for {run_date}",
        file=sys.stderr,
    )
    sys.exit(1)
```

Add CLI parser inside `main()` after the `verify-and-commit` parser block:

```python
    # --- verify-session-state-written ---
    vssw_parser = subparsers.add_parser(
        "verify-session-state-written",
        help="Verify session-state.md contains an entry for the run date",
    )
    vssw_parser.add_argument(
        "--session-state-path",
        dest="session_state_path",
        default="output/session-state.md",
        help="Path to session-state.md (default: output/session-state.md)",
    )
    vssw_parser.add_argument(
        "--run-date",
        dest="run_date",
        required=True,
        help="Expected run date YYYY-MM-DD",
    )
    vssw_parser.set_defaults(func=_cli_verify_session_state_written)
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_manage_state.py -v -k verify_session_state` (expect PASS)
- Lint: `cd 03_agents/tests/v25 && ruff check scripts/manage_state.py`

---

#### Step 8: Sentinel enforcement — test + implementation (merged from old Steps 8-9)
**Files:** `03_agents/tests/v25/tests/test_schema_validation.py` (Create), `03_agents/tests/v25/.claude/agents/search-verify.md` (Modify)
**Action:** Create test file with sentinel tests, then implement sentinel enforcement

Create `tests/test_schema_validation.py`:

```python
"""Tests for schema validation and sentinel enforcement in search-verify agent.

Covers:
- Agent definition contains .done sentinel write instruction
- Canonical 10-field schema validation
- Agent definition contains schema validation instruction
"""

from __future__ import annotations

from pathlib import Path

# Path to the search-verify agent definition
SEARCH_VERIFY_AGENT = (
    Path(__file__).resolve().parent.parent / ".claude" / "agents" / "search-verify.md"
)


class TestSentinelEnforcement:
    """Tests that search-verify agent writes .done sentinel on completion."""

    def test_agent_contains_done_sentinel_instruction(self) -> None:
        """search-verify.md must contain instruction to write .done sentinel file."""
        content = SEARCH_VERIFY_AGENT.read_text(encoding="utf-8")
        assert ".done" in content, (
            "search-verify agent definition must contain '.done' sentinel write instruction"
        )

    def test_agent_sentinel_is_mandatory_final_step(self) -> None:
        """search-verify.md must mark sentinel write as mandatory/final."""
        content = SEARCH_VERIFY_AGENT.read_text(encoding="utf-8").lower()
        has_mandatory = "mandatory" in content or "must" in content or "required" in content
        has_final = "final" in content or "last" in content or "completion" in content
        assert has_mandatory and has_final, (
            "search-verify agent must describe .done sentinel as a mandatory final step.\n"
            f"Has mandatory language: {has_mandatory}, has final language: {has_final}"
        )

    def test_agent_specifies_sonnet_tier(self) -> None:
        """search-verify.md must specify Sonnet model tier (V23 Haiku scoring regression)."""
        content = SEARCH_VERIFY_AGENT.read_text(encoding="utf-8")
        assert "model: sonnet" in content or "model:sonnet" in content, (
            "search-verify agent must specify 'model: sonnet' tier to avoid Haiku scoring regression"
        )
```

Then append the following block at the end of `search-verify.md`:

```markdown

## Completion Protocol

**Mandatory final step — sentinel write:**

After writing all verified job JSON files to `output/verified/{role_type_slug}/`, you MUST write a `.done` sentinel file as the required last action before returning:

```bash
touch output/verified/{role_type_slug}/.done
```

This `.done` file signals completion to the gate-check agent. If this file is missing, the gate-check will block pipeline progression. Never skip this step — it is mandatory for every search-verify dispatch, even if zero jobs were found.
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_schema_validation.py -v -k sentinel` (expect PASS)

---

#### Step 9: Schema validation — test + implementation (merged from old Steps 10-11)
**Files:** `03_agents/tests/v25/tests/test_schema_validation.py` (Modify), `03_agents/tests/v25/.claude/agents/search-verify.md` (Modify)
**Action:** Append schema tests to test file, then implement schema validation instruction in agent

Append to `tests/test_schema_validation.py`:

```python
import json
import subprocess
import sys

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _make_valid_job(**overrides) -> dict:
    """Create a valid 10-field job entry."""
    defaults = {
        "job_id": "test-001", "title": "Engineer", "company": "TestCo",
        "job_url": "https://example.com/job", "role_type": "ai-engineer",
        "score": 85, "source_channel": "direct-career-pages",
        "run_date": "2026-02-27", "location": "Remote", "status": "verified",
    }
    defaults.update(overrides)
    return defaults


def _run_validate_schema(output_dir: str) -> subprocess.CompletedProcess:
    """Run validate-schema subcommand."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "validate-schema",
        "--output-dir",
        output_dir,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestSchemaValidation:
    """Tests for schema validation of verified job JSONs."""

    def test_valid_10_field_job_passes(self, tmp_path: Path) -> None:
        """Valid job with all 10 canonical fields passes validation."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True)
        (role_dir / "valid-job.json").write_text(
            json.dumps(_make_valid_job()), encoding="utf-8",
        )
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0, (
            f"valid 10-field job should pass.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_missing_fields_fails(self, tmp_path: Path) -> None:
        """Job missing required fields fails validation."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True)
        incomplete_job = {"title": "Engineer", "company": "TestCo"}
        (role_dir / "bad-job.json").write_text(
            json.dumps(incomplete_job), encoding="utf-8",
        )
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1, (
            f"job missing fields should fail.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_extra_fields_tolerated(self, tmp_path: Path) -> None:
        """Job with extra fields beyond the 10 canonical still passes."""
        output_dir = tmp_path / "output"
        role_dir = output_dir / "verified" / "ai-engineer"
        role_dir.mkdir(parents=True)
        job = _make_valid_job(salary="$120k", description="Great role")
        (role_dir / "extra-fields.json").write_text(
            json.dumps(job), encoding="utf-8",
        )
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0, (
            f"extra fields should be tolerated.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_agent_contains_schema_validation_instruction(self) -> None:
        """search-verify.md must contain schema validation instruction."""
        content = SEARCH_VERIFY_AGENT.read_text(encoding="utf-8")
        has_validate = "validate-schema" in content or "validate schema" in content.lower()
        assert has_validate, (
            "search-verify agent must contain schema validation instruction "
            "(reference to validate-schema)"
        )
```

Then in `search-verify.md`, insert the following blocks before the `## Completion Protocol` section.

First, add title inclusion guidance (V23 regression — associate-level titles incorrectly filtered as executive):

```markdown

## Title Scoring Guidance

**Associate-level titles are INCLUDED.** The following titles and similar are valid matches — do NOT filter them as executive-only:
- Associate Product Manager, Associate Engineer, Associate Data Scientist
- Junior/Mid-level variants of target role types
- "Staff" and "Principal" titles (these are senior IC, not executive)

**Executive-level titles are EXCLUDED** (CEO, CTO, CFO, VP, SVP, EVP, Director-level and above). When in doubt, INCLUDE the title — false negatives are worse than false positives for the user's job search.
```

Then add schema validation:

```markdown

## Pre-Write Schema Validation

Before writing any verified job JSON file, validate it against the canonical 10-field schema by running:

```bash
python3 scripts/manage_state.py validate-schema --output-dir output
```

If validation fails, do not proceed — fix the data or exit with an error status. The canonical fields are: job_id, title, company, job_url, role_type, score (int), source_channel, run_date, location, status. All fields are required. Extra fields are tolerated but the 10 canonical fields must be present with correct types.
```

**Note:** The `validate-schema` subcommand already exists in `manage_state.py` from V24. No changes needed to `manage_state.py` for this step.

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_schema_validation.py -v` (expect PASS for both sentinel and schema)
- Lint: `cd 03_agents/tests/v25 && ruff check scripts/manage_state.py`

---

#### Step 11b: Add `--active-only`, `--dry-run`, and safety bound to dedup subcommand
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify

Add `--active-only`, `--dry-run`, and safety abort threshold flags to the existing `dedup` subcommand parser. When `--active-only` is set, dedup only processes role-type directories that match the active role types from `context.md ## Target`. The `--dry-run` flag previews what would be archived without modifying files. The safety bound aborts if >50% of entries would be archived.

In the dedup CLI parser, add:

```python
    dedup_parser.add_argument(
        "--active-only",
        action="store_true",
        default=False,
        help="Only dedup role-type directories matching active role types from context.md",
    )
    dedup_parser.add_argument(
        "--context-path",
        dest="context_path",
        default="context.md",
        help="Path to context.md for --active-only filtering (default: context.md)",
    )
    dedup_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview dedup actions without modifying files",
    )
```

In the dedup implementation function, add early filtering and safety bound. Note: use an internal helper function `_get_active_role_types(context_path)` instead of shelling out to self via subprocess (avoids spawning a child Python process from within a Python process):

```python
def _get_active_role_types(context_path: str) -> set[str]:
    """Read active role-type slugs from context.md ## Target section.

    Factored out as internal helper so dedup --active-only can call directly
    without subprocess self-invocation.
    """
    ctx = Path(context_path)
    if not ctx.exists():
        return set()
    content = ctx.read_text(encoding="utf-8")
    target_start = content.find("## Target")
    if target_start == -1:
        return set()
    target_section = content[target_start:]
    next_heading = target_section.find("\n## ", 1)
    if next_heading != -1:
        target_section = target_section[:next_heading]
    slugs = set()
    for line in target_section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            slug = stripped[2:].strip().lower().replace(" ", "-")
            if slug:
                slugs.add(slug)
    return slugs
```

Also refactor the existing `_cli_list_active_role_types` handler to delegate to `_get_active_role_types()` instead of duplicating parsing logic. This keeps a single code path for slug extraction.

Then in the dedup function body:

```python
    if args.active_only:
        # Read active role types via internal helper (no subprocess self-call)
        active_slugs = _get_active_role_types(args.context_path)
        if active_slugs:
            role_dirs = [d for d in role_dirs if d.name in active_slugs]

    # Safety bound: abort if >50% of entries would be archived
    if total_entries > 0 and archive_count > total_entries * 0.5:
        print(f"SAFETY ABORT: {archive_count}/{total_entries} entries ({archive_count*100//total_entries}%) "
              f"would be archived — exceeds 50% threshold. Use --force to override.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"DRY RUN: would archive {archive_count} duplicates out of {total_entries} entries")
        return
```

Add test to `tests/test_manage_state.py`:

```python
class TestDedupSafety:
    """Tests for --active-only, --dry-run, and safety bound on dedup subcommand."""

    def test_active_only_flag_accepted(self, tmp_path: Path) -> None:
        """dedup subcommand must accept --active-only flag."""
        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "dedup", "--help"],
            capture_output=True, text=True,
        )
        assert "--active-only" in result.stdout, (
            "dedup subcommand must accept --active-only flag"
        )

    def test_dry_run_flag_accepted(self, tmp_path: Path) -> None:
        """dedup subcommand must accept --dry-run flag."""
        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "dedup", "--help"],
            capture_output=True, text=True,
        )
        assert "--dry-run" in result.stdout, (
            "dedup subcommand must accept --dry-run flag"
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_manage_state.py -v -k "TestDedupSafety"` (expect PASS after implementation)

---

#### Step 12: Verify + Commit Layer 1 (merged from old Steps 12-13)
**Description:** Run full Layer 1 test suite and commit.

**Pre-commit verification:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_preflight.py tests/test_manage_state.py tests/test_schema_validation.py -v`
- Lint: `cd 03_agents/tests/v25 && ruff check scripts/`
- Type check: `cd 03_agents/tests/v25 && mypy scripts/manage_state.py --ignore-missing-imports`

**Commit (only if all verifications pass):**

```bash
git add 03_agents/tests/v25/
git commit -m "build(jsa): V25 Layer 1 — infrastructure/script fixes

- First-run detection in preflight.sh (empty verified/ skips schema checks)
- verify-and-commit subcommand in manage_state.py (with --no-push, single-responsibility)
- verify-session-state-written subcommand in manage_state.py
- Sentinel enforcement in search-verify agent (.done file)
- Schema validation instruction in search-verify agent
- Dedup --active-only, --dry-run, and safety bound"
```

**Verify:**
- `git status` shows clean after commit

---

### Phase 2: Orchestration + Config (Layer 2)

#### Step 14: Write failing test for structural commit gate
**File:** `03_agents/tests/v25/tests/test_orchestration.py`
**Action:** Create

```python
"""Tests for orchestration.md structural assertions — V25 Layer 2 + Layer 3.

Grep-based tests that verify orchestration.md contains specific patterns
for gates, tiered delivery, dispatch counter, compaction recovery,
constraint compliance, context validation, and task ID persistence.

Consolidated into 4 test classes:
- TestPhase1Gates: channel dispatch + commit gate + session-state gate
- TestPhase5Delivery: tiered delivery + task ID persistence
- TestArchitecturalCompliance: constraint compliance + context validation + compaction + settings.local.json
- TestUxProtocol: all 6 UX format rules
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORCHESTRATION_MD = PROJECT_ROOT / "references" / "orchestration.md"
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


def _read_orch() -> str:
    return ORCHESTRATION_MD.read_text(encoding="utf-8")


def _read_claude() -> str:
    return CLAUDE_MD.read_text(encoding="utf-8")


def _phase1_text() -> str:
    content = _read_orch()
    start = content.find("## Phase 1")
    end = content.find("## Phase 2")
    assert start != -1 and end != -1
    return content[start:end]


def _phase5_text() -> str:
    content = _read_orch()
    start = content.find("## Phase 5")
    assert start != -1
    return content[start:]


def _extract_section(content: str, heading: str) -> str:
    """Extract a section from markdown content by heading."""
    start = content.find(heading)
    if start == -1:
        return ""
    # Find the next same-level heading
    level = heading.split(" ")[0]  # e.g., "##"
    rest = content[start + len(heading):]
    next_heading = rest.find(f"\n{level} ")
    if next_heading == -1:
        return content[start:]
    return content[start:start + len(heading) + next_heading]


# ---- Phase 1 Gates (channel dispatch + commit gate + session-state gate) ----

class TestPhase1Gates:
    # -- Channel dispatch --
    def test_phase1_enumerates_all_5_channels(self) -> None:
        """Phase 1 must enumerate all 5 search channels as mandatory dispatches."""
        text = _phase1_text()
        for channel in ("direct-career-pages", "linkedin", "indeed", "builtin", "google-jobs"):
            assert channel in text, f"Phase 1 must enumerate channel '{channel}'"

    def test_channel_dispatch_is_unconditional(self) -> None:
        """Channel dispatch must use unconditional/mandatory language."""
        text = _phase1_text().lower()
        assert "must be dispatched" in text or "mandatory" in text or "unconditional" in text, (
            "Channel dispatch must use mandatory/unconditional language"
        )

    # -- Commit gate --
    def test_phase1_contains_verify_and_commit(self) -> None:
        """Phase 1 must reference verify-and-commit gate-check dispatch."""
        text = _phase1_text()
        assert "verify-and-commit" in text, (
            "Phase 1 must contain 'verify-and-commit' gate-check dispatch"
        )

    def test_verify_and_commit_is_blocking(self) -> None:
        """verify-and-commit must use blocking language."""
        text = _phase1_text()
        idx = text.find("verify-and-commit")
        assert idx != -1
        surrounding = text[max(0, idx - 200):idx + 400]
        assert "MUST pass" in surrounding or "BLOCKING" in surrounding or "blocks progression" in surrounding.lower(), (
            "verify-and-commit gate must use blocking language (MUST pass, BLOCKING, or blocks progression)"
        )

    def test_verify_and_commit_exit_codes(self) -> None:
        """verify-and-commit section must document exit code 1 = retry, exit code 2 = STOP."""
        text = _phase1_text()
        idx = text.find("verify-and-commit")
        assert idx != -1
        surrounding = text[idx:idx + 600]
        assert "exit code 1" in surrounding.lower() or "exit 1" in surrounding.lower(), (
            "verify-and-commit must document exit code 1 = retry"
        )
        assert "exit code 2" in surrounding.lower() or "exit 2" in surrounding.lower(), (
            "verify-and-commit must document exit code 2 = STOP"
        )

    # -- Session-state gate --
    def test_phase1_contains_verify_session_state_written(self) -> None:
        """Phase 1 must reference verify-session-state-written gate-check."""
        text = _phase1_text()
        assert "verify-session-state-written" in text, (
            "Phase 1 must contain 'verify-session-state-written' gate-check dispatch"
        )

    def test_session_state_gate_is_blocking(self) -> None:
        """verify-session-state-written must use blocking language."""
        text = _phase1_text()
        idx = text.find("verify-session-state-written")
        assert idx != -1
        surrounding = text[max(0, idx - 200):idx + 400]
        assert "MUST pass" in surrounding or "BLOCKING" in surrounding or "blocks progression" in surrounding.lower(), (
            "verify-session-state-written gate must use blocking language"
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_orchestration.py -v -k "TestPhase1Gates"` (expect FAIL)

---

#### Step 15: Implement structural commit gate + session-state gate + channel dispatch in orchestration.md
**File:** `03_agents/tests/v25/references/orchestration.md`
**Action:** Modify

Add a mandatory Channel Dispatch rule at the start of Phase 1, then replace the existing "Per-Channel Commit Gate" section with:

```markdown
### Channel Dispatch (MANDATORY — 5-channel unconditional parallel)

All 5 search channels MUST be dispatched on every run. No channel may be skipped, deferred, or conditionally excluded. Dispatch all 5 in a single message (parallel):

1. **direct-career-pages** — search-verify subagent
2. **linkedin** — search-verify subagent
3. **indeed** — search-verify subagent
4. **builtin** — search-verify subagent
5. **google-jobs** — search-verify subagent

Each dispatch includes HC-10 mandatory variables: `working_dir` (absolute, resolving to `03_agents/tests/v25/`), `output_directory`, `dashboard_url`.

Failure to dispatch all 5 channels is a pipeline violation. If a channel returns zero results, that is acceptable — the channel was still dispatched.
```

Then replace the existing "Per-Channel Commit Gate" section with:

```markdown
### Per-Channel Commit Gate (MANDATORY)

After EACH channel's search-verify subagent returns, parent dispatches a gate-check subagent via Task tool (note: do NOT include `model:` as a Task tool parameter — model selection is handled by the agent definition, not dispatch):

```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "command": "python3 scripts/manage_state.py verify-and-commit --phase-label search --output-dir output", "gate_name": "commit-gate-{channel-name}"}'
description: "Gate-check: verify-and-commit for {channel-name}"
```

**Gate: `manage_state.py verify-and-commit`** — MUST pass before proceeding. Blocks progression. No skip option.
- Exit code 0 = clean or committed successfully. Proceed.
- Exit code 1 = push failure (transient). Retry gate-check. Do NOT skip.
- Exit code 2 = merge conflict or unrecoverable. STOP and alert user.

If gate-check fails: re-dispatch gate-check (max 1 retry, tracked in session-state.md `## Retry Log` as `{gate-name}: attempt {N}`). After 2 total attempts (1 original + 1 retry), STOP and alert user. Do NOT skip. This enforces incremental commits per-channel (6-version recurrence: V14/V16/V18/V19/V20/V21).

**Stderr reformatting (MANDATORY):** When a gate-check returns exit code 1 or 2, the parent MUST reformat the raw stderr output into the UX Protocol gate failure alert format before displaying to the user: `[GATE FAILED] {gate-name} — {reason}. Action: {next}.` Do NOT surface raw stderr directly — always apply the prescribed format.

**Post-dispatch directory verification (CR-12):** After the gate-check subagent returns, verify that the committed files exist in the expected output directories. State absolute file paths in the verification log.
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_orchestration.py -v -k "TestPhase1Gates"` (expect PASS)

---

Step 15 also includes the session-state gate implementation. Add to `references/orchestration.md` after the Per-Channel Commit Gate:

```markdown
### Per-Channel Session-State Gate (MANDATORY)

Same timing as the commit gate. The gate-check subagent also confirms `session-state.md` was written for this channel:

```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "command": "python3 scripts/manage_state.py verify-session-state-written --session-state-path output/session-state.md --run-date {run_date}", "gate_name": "session-state-gate"}'
description: "Gate-check: verify-session-state-written for {run_date}"
```

**Gate: `manage_state.py verify-session-state-written`** — MUST pass before proceeding. Blocks progression. No skip option.
- Exit code 0 = session-state.md contains today's date entry. Proceed.
- Exit code 1 = missing or stale. Re-dispatch gate-check. Do NOT skip.

(5-version recurrence: V14/V16/V18/V19/V21). State absolute file paths when reporting gate results (CR-7).
```

---

#### Step 16: Write failing test for tiered delivery
**File:** `03_agents/tests/v25/tests/test_orchestration.py`
**Action:** Modify

Append to test file:

```python
# ---- Phase 5 Delivery (tiered delivery + task ID persistence) ----

class TestPhase5Delivery:
    # -- Tiered delivery --
    def test_phase5_has_brief_generator(self) -> None:
        assert "brief-generator" in _phase5_text()

    def test_phase5_has_digest_email(self) -> None:
        assert "digest-email" in _phase5_text()

    def test_phase5_has_send_email(self) -> None:
        assert "send_email.py" in _phase5_text()

    def test_phase5_has_budget_check(self) -> None:
        text = _phase5_text()
        assert "check-dispatch-budget" in text or "budget" in text.lower(), (
            "Phase 5 must include dispatch budget check"
        )

    def test_phase5_has_briefs_html_conditional(self) -> None:
        text = _phase5_text()
        assert "briefs-html" in text
        assert "budget" in text.lower() or "conditional" in text.lower() or "if budget" in text.lower()

    def test_phase5_has_deferred_logging_with_user_message(self) -> None:
        text = _phase5_text().lower()
        assert "deferred" in text or "skip" in text
        assert "user" in text or "briefs html deferred" in text, (
            "Phase 5 must include user-facing notification when Tier 2 is skipped"
        )

    def test_tiered_delivery_order(self) -> None:
        """Phase 5 tiered delivery steps must appear in correct order."""
        text = _phase5_text()
        pos_brief_gen = text.find("brief-generator")
        pos_digest = text.find("digest-email")
        pos_send = text.find("send_email.py")
        pos_budget = text.lower().find("check-dispatch-budget")
        if pos_budget == -1:
            pos_budget = text.lower().find("budget check")
        pos_briefs_html = text.find("briefs-html")

        assert pos_brief_gen < pos_digest, "brief-generator must come before digest-email"
        assert pos_digest < pos_send, "digest-email must come before send_email.py"
        assert pos_send < pos_budget, "send_email.py must come before budget check"
        assert pos_budget < pos_briefs_html, "budget check must come before briefs-html"

    # -- Task ID persistence --
    def test_orchestration_has_task_id_persistence(self) -> None:
        content = _read_orch().lower()
        assert "task id" in content or "task_id" in content
        assert "active tasks" in content

    # -- body-file enforcement --
    def test_send_email_uses_body_file_not_html(self) -> None:
        """orchestration.md must use --body-file and NOT --html for send_email.py."""
        content = _read_orch()
        assert "--body-file" in content, "send_email.py must use --body-file"
        # Ensure --html flag is not used (V21/V23 recurrence)
        import re
        html_flags = re.findall(r"--html\b", content)
        assert len(html_flags) == 0, "send_email.py must NOT use --html flag (use --body-file instead)"
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_orchestration.py -v -k "TestPhase5Delivery"` (expect FAIL)

---

#### Step 19: Implement tiered delivery in orchestration.md
**File:** `03_agents/tests/v25/references/orchestration.md`
**Action:** Modify

Replace the entire Phase 5 `### Steps` subsection with the tiered delivery sequence:

```markdown
### Steps (Tiered Delivery)

**Tier 1 — Mandatory (always executes):**

1. **Generate briefs (brief-generator x N).** For each `brief_requested` job, dispatch a brief-generator subagent. If 3+ briefs needed, dispatch all in a single message (parallel). After each brief completes, verify `output/briefs/{company_slug}-{title_slug}-brief.md` exists and last non-whitespace line is `<!-- BRIEF COMPLETE -->`. If sentinel missing, treat as corrupt.

   Task tool call per brief:
   ```
   prompt: '{"working_dir": "<abs_path>", "output_directory": "output/briefs/", "dashboard_url": "<url>", "job_title": "...", "company": "...", "company_slug": "...", "title_slug": "...", "run_date": "...", "profile_extract": "...", "job_json_with_verification": "..."}'
   description: "Generate brief for {job_title} at {company}"
   subagent_type: "brief-generator"
   ```

   After dispatching, append task ID to session-state.md `## Active Tasks`. State absolute file paths for all generated briefs (CR-7).

2. **Dispatch digest-email.** Dispatch digest-email subagent (mandatory, first delivery artifact):

   ```
   prompt: '{"working_dir": "<abs_path>", "output_directory": "output/digests/", "dashboard_url": "<url>", "run_date": "...", "user_email": "...", "user_name": "...", "total_briefs": N, "new_today": [...], "still_active": [...], "verified_dir": "output/verified/"}'
   description: "Generate digest email HTML"
   subagent_type: "digest-email"
   ```

   After dispatching, append task ID to session-state.md `## Active Tasks`. Verify completion via `output/digests/_status.json`.

   **Post-render file verification (MANDATORY):** `output/digests/{run_date}-email.html` must exist and be >0 bytes. If missing or empty, re-dispatch (max 1 retry).

   **Post-render style verification:** Parent reads generated HTML and checks: link colors are `#1c1917` (not `#2563eb`), score badges use only green/stone (no amber/red), zero-count sections omitted.

3. **Send email via send_email.py.** Parent-orchestrated. Do NOT ask user for send confirmation.

   ```bash
   python3 scripts/send_email.py \
     --to "{user_email}" \
     --subject "Job Search Update — {run_date}" \
     --body-file output/digests/{run_date}-email.html
   ```

   After successful send: update `output/digests/_status.json` with `sent_at` and `to` fields.

**Tier 2 — Budget-Gated (executes only if dispatch budget allows):**

4. **Budget check.** Read dispatch counter from session-state.md `## Budget` section:

   ```bash
   python3 scripts/manage_state.py check-dispatch-budget --session-state-path output/session-state.md
   ```

   - Exit code 0: under ceiling. Proceed to briefs-html.
   - Exit code 1: at or over ceiling. Skip to step 6.

5. **Dispatch briefs-html (conditional).** Only if budget check passed AND briefs were generated:

   ```bash
   python3 scripts/manage_state.py increment-dispatch-counter --session-state-path output/session-state.md
   ```

   ```
   prompt: '{"working_dir": "<abs_path>", "output_directory": "output/briefs/", "dashboard_url": "<url>", "run_date": "..."}'
   description: "Compile briefs into HTML"
   subagent_type: "briefs-html"
   ```

   After dispatching, append task ID to session-state.md `## Active Tasks`.

6. **Deferred logging + user notification.** If budget check failed (step 4 exit code 1) or zero briefs requested:
   - Log in session-state.md: "briefs-html deferred to next session — dispatch budget exhausted"
   - Emit user-facing message: "Briefs HTML deferred — dispatch budget reached. Will generate next session."
   - Skip briefs-html dispatch entirely
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_orchestration.py -v -k "TestPhase5Delivery"` (expect PASS)

---

#### Step 20: Write failing test for dispatch counter
**File:** `03_agents/tests/v25/tests/test_dispatch_counter.py`
**Action:** Create

```python
"""Tests for dispatch counter subcommands in manage_state.py.

Tests increment-dispatch-counter, check-dispatch-budget, and CLAUDE.md ceiling."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANAGE_STATE = PROJECT_ROOT / "scripts" / "manage_state.py"
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


def _run_manage_state(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MANAGE_STATE)] + args,
        capture_output=True, text=True, cwd=str(cwd),
    )


class TestIncrementDispatchCounter:
    def test_increment_creates_budget_section(self, tmp_path: Path) -> None:
        """increment-dispatch-counter creates ## Budget section if missing."""
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Search Progress\n- channel 1 done\n", encoding="utf-8")
        result = _run_manage_state(
            ["increment-dispatch-counter", "--session-state-path", str(ss)],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        content = ss.read_text(encoding="utf-8")
        assert "## Budget" in content
        assert "dispatch_count: 1" in content

    def test_increment_bumps_existing_counter(self, tmp_path: Path) -> None:
        """increment-dispatch-counter increments existing count."""
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Budget\ndispatch_count: 5\n", encoding="utf-8")
        result = _run_manage_state(
            ["increment-dispatch-counter", "--session-state-path", str(ss)],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        content = ss.read_text(encoding="utf-8")
        assert "dispatch_count: 6" in content


class TestCheckDispatchBudget:
    def test_under_ceiling_exits_0(self, tmp_path: Path) -> None:
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Budget\ndispatch_count: 10\n", encoding="utf-8")
        result = _run_manage_state(
            ["check-dispatch-budget", "--session-state-path", str(ss), "--ceiling", "25"],
            cwd=tmp_path,
        )
        assert result.returncode == 0

    def test_at_ceiling_exits_1(self, tmp_path: Path) -> None:
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Budget\ndispatch_count: 25\n", encoding="utf-8")
        result = _run_manage_state(
            ["check-dispatch-budget", "--session-state-path", str(ss), "--ceiling", "25"],
            cwd=tmp_path,
        )
        assert result.returncode == 1

    def test_over_ceiling_exits_1(self, tmp_path: Path) -> None:
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Budget\ndispatch_count: 30\n", encoding="utf-8")
        result = _run_manage_state(
            ["check-dispatch-budget", "--session-state-path", str(ss), "--ceiling", "25"],
            cwd=tmp_path,
        )
        assert result.returncode == 1

    def test_missing_budget_section_exits_0(self, tmp_path: Path) -> None:
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Search Progress\n- done\n", encoding="utf-8")
        result = _run_manage_state(
            ["check-dispatch-budget", "--session-state-path", str(ss), "--ceiling", "25"],
            cwd=tmp_path,
        )
        assert result.returncode == 0


class TestClaudeMdDispatchCeiling:
    def test_claude_md_has_dispatch_ceiling(self) -> None:
        content = CLAUDE_MD.read_text(encoding="utf-8")
        assert "DISPATCH_CEILING" in content
        assert "25" in content
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_dispatch_counter.py -v` (expect FAIL)

---

#### Step 21: Implement dispatch counter in manage_state.py + CLAUDE.md
**Files:** `03_agents/tests/v25/scripts/manage_state.py`, `03_agents/tests/v25/CLAUDE.md`
**Action:** Modify both

In `manage_state.py`, add `import re` to the module-level imports (at top of file, alongside existing imports). Then add the following functions before `main()`:

```python
# ---------------------------------------------------------------------------
# increment-dispatch-counter subcommand
# ---------------------------------------------------------------------------


def _read_dispatch_count(session_state_path: Path) -> int:
    """Read dispatch_count from session-state.md. Returns 0 if not found.

    Uses regex matching consistent with _write_dispatch_count (symmetric approach).
    """
    if not session_state_path.exists():
        return 0
    content = session_state_path.read_text(encoding="utf-8")
    m = re.search(r"dispatch_count:\s*(\d+)", content)
    return int(m.group(1)) if m else 0


def _write_dispatch_count(session_state_path: Path, count: int) -> None:
    """Write dispatch_count into ## Budget section of session-state.md.

    Uses regex-replace approach: if `dispatch_count: \d+` exists, replace in-place.
    If ## Budget section exists but no count line, append. If no section, append both.
    """
    if not session_state_path.exists():
        session_state_path.write_text(
            f"# Session State\n\n## Budget\ndispatch_count: {count}\n",
            encoding="utf-8",
        )
        return

    content = session_state_path.read_text(encoding="utf-8")

    # Try regex replace first
    new_content, n = re.subn(r"dispatch_count: \d+", f"dispatch_count: {count}", content)
    if n > 0:
        session_state_path.write_text(new_content, encoding="utf-8")
        return

    # No existing count line — append to ## Budget section or create it
    if "## Budget" in content:
        new_content = content.replace("## Budget", f"## Budget\ndispatch_count: {count}", 1)
    else:
        new_content = content.rstrip() + f"\n\n## Budget\ndispatch_count: {count}\n"

    session_state_path.write_text(new_content, encoding="utf-8")


def _cli_increment_dispatch_counter(args: argparse.Namespace) -> None:
    """Increment the dispatch counter in session-state.md ## Budget section."""
    session_state_path = Path(args.session_state_path)
    current = _read_dispatch_count(session_state_path)
    new_count = current + 1
    _write_dispatch_count(session_state_path, new_count)
    print(f"Dispatch count: {current} -> {new_count}")


# ---------------------------------------------------------------------------
# check-dispatch-budget subcommand
# ---------------------------------------------------------------------------


def _cli_check_dispatch_budget(args: argparse.Namespace) -> None:
    """Check if dispatch count is under the ceiling.

    Exits 0 if under ceiling (budget available).
    Exits 1 if at or over ceiling (budget exhausted).
    """
    session_state_path = Path(args.session_state_path)
    ceiling = int(args.ceiling)
    current = _read_dispatch_count(session_state_path)

    if current >= ceiling:
        print(f"Budget exhausted: {current}/{ceiling} dispatches")
        sys.exit(1)

    print(f"Budget available: {current}/{ceiling} dispatches")
```

Add CLI parsers inside `main()`:

```python
    # --- increment-dispatch-counter ---
    idc_parser = subparsers.add_parser(
        "increment-dispatch-counter",
        help="Increment the dispatch counter in session-state.md ## Budget section",
    )
    idc_parser.add_argument(
        "--session-state-path",
        dest="session_state_path",
        default="output/session-state.md",
    )
    idc_parser.set_defaults(func=_cli_increment_dispatch_counter)

    # --- check-dispatch-budget ---
    cdb_parser = subparsers.add_parser(
        "check-dispatch-budget",
        help="Check if dispatch count is under the ceiling",
    )
    cdb_parser.add_argument(
        "--session-state-path",
        dest="session_state_path",
        default="output/session-state.md",
    )
    cdb_parser.add_argument(
        "--ceiling",
        type=int,
        default=25,
    )
    cdb_parser.set_defaults(func=_cli_check_dispatch_budget)
```

In `CLAUDE.md`, replace the parent-allowed operations list:

Find:
```
- `python3 scripts/manage_state.py` CLI subcommands (sync, dedup, cleanup, record-action)
```

Replace with:
```
- `python3 scripts/manage_state.py` CLI subcommands (sync, dedup, cleanup, record-action, list-active-role-types, increment-dispatch-counter, check-dispatch-budget, verify-and-commit, verify-session-state-written) — these are explicitly parent-allowed exceptions per Context Budget rules.
- `python3 scripts/send_email.py` — parent-orchestrated email send (Phase 5 Tier 1 Step 3). Explicitly parent-allowed per Context Budget rules.
- Parent MUST NOT run any other `python3 scripts/*` directly (V19 regression).

**DISPATCH_CEILING: 25** — Maximum subagent dispatches per session. Before optional work (briefs-html), check via `manage_state.py check-dispatch-budget`. Configurable: change the ceiling value here to adjust.
```

Also add a new `## Context Budget` section to `CLAUDE.md` (after the ON STARTUP section):

```markdown
## Context Budget

**Parent-allowed tools (orchestrator runs directly):**
- `bash scripts/preflight.sh`
- `python3 scripts/manage_state.py` subcommands: sync, dedup, cleanup, record-action, list-active-role-types, increment-dispatch-counter, check-dispatch-budget, verify-and-commit, verify-session-state-written
- `python3 scripts/send_email.py` — parent-orchestrated email send (Phase 5 Tier 1 Step 3)
- `git add`, `git commit`, `git push`, `git pull`, `git status`

**Subagent-only tools (NEVER run by parent — dispatch via Task tool):**
- WebFetch, WebSearch
- Search-verify operations (job searching, scoring, filtering)
- Dedup analysis (reading/comparing individual job files)
- Source file reads (reading individual JSON job files, brief content)
- Brief generation, digest-email generation, briefs-html compilation

Parent MUST NOT run `python3 scripts/*` directly for any script OTHER than `manage_state.py`, `preflight.sh`, and `send_email.py`. All other script execution is subagent-only. (V19 regression compliance.)
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_dispatch_counter.py -v` (expect PASS)
- Lint: `cd 03_agents/tests/v25 && ruff check scripts/manage_state.py`

---

#### Step 22: Implement post-compaction recovery protocol
**Files:** `03_agents/tests/v25/references/orchestration.md`, `03_agents/tests/v25/CLAUDE.md`
**Action:** Modify both

Append to `references/orchestration.md` (after Phase 5):

```markdown
---

## Post-Compaction Recovery Protocol

When context compaction occurs mid-session, follow this recovery sequence:

### Immediate Status (MANDATORY)

First user-visible output after compaction MUST be a 1-2 sentence summary of completed/pending work. Example:
> "Search complete for 5/5 channels. Proceeding to dedup and presentation."

No silent file reads before status. The user must see progress immediately.

### Task ID Recovery

All dispatched task IDs are persisted in session-state.md `## Active Tasks`. After compaction:

1. Read `session-state.md ## Active Tasks` to recover in-flight task IDs.
2. Check each task's status (completed, running, failed).
3. For completed tasks: read their output status files (`_status.json`, `_summary.md`).
4. For running tasks: wait for completion, then read outputs.
5. For failed tasks: re-dispatch (max 1 retry per subagent).

### Resume Logic

After recovery:
- Read `session-state.md ## Search Progress` to determine which phase to resume.
- Read `output/.checkpoints/` to determine last completed phase gate.
- Resume from the next uncompleted phase gate.
- NEVER reconstruct findings from conversation summary — re-dispatch subagents to get actual data (P2).

### State Absolute File Paths

When reporting recovery status, always state absolute file paths for:
- session-state.md location
- output directory location
- Any artifacts referenced in the recovery summary
```

In `CLAUDE.md`, add post-compaction rule to Core Rules. Find rule 12 and add rule 13 after it:

```
13. **Post-compaction recovery (P2).** After context compaction, first print a 1-2 sentence status summary. Then read session-state.md `## Active Tasks` for in-flight task IDs. Resume from structured state — NEVER reconstruct from conversation summary.
```

Add these tests to `test_orchestration.py`:

```python
# ---- Architectural Compliance (compaction + constraints + context + settings.local.json) ----

class TestArchitecturalCompliance:
    # -- Post-compaction recovery --
    def test_orchestration_has_compaction_recovery(self) -> None:
        content = _read_orch()
        assert "compaction" in content.lower()

    def test_compaction_references_session_state(self) -> None:
        content = _read_orch().lower()
        idx = content.find("compaction")
        assert idx != -1
        surrounding = content[idx:idx + 800]
        assert "session-state" in surrounding

    def test_compaction_has_immediate_status(self) -> None:
        content = _read_orch().lower()
        idx = content.find("compaction")
        assert idx != -1
        surrounding = content[idx:idx + 800]
        assert "immediate" in surrounding or "1-2 sentence" in surrounding

    def test_claude_md_has_compaction_rule(self) -> None:
        content = _read_claude().lower()
        assert "compaction" in content

    # -- Constraint compliance (HC-5, HC-10, CR-7, CR-12, git pull) --
    def test_hc5_list_active_role_types_in_parent_allowed(self) -> None:
        content = _read_claude()
        budget_start = content.find("## Context Budget")
        if budget_start == -1:
            budget_start = content.find("Parent-allowed")
        assert budget_start != -1
        section = content[budget_start:budget_start + 1000]
        assert "list-active-role-types" in section

    def test_hc10_dispatch_templates_have_mandatory_vars(self) -> None:
        content = _read_orch()
        for var in ("working_dir", "output_directory", "dashboard_url"):
            assert var in content, f"orchestration.md must include '{var}' (HC-10)"

    def test_cr7_absolute_file_paths_reminder(self) -> None:
        content = _read_orch().lower()
        assert "absolute" in content and ("file path" in content or "absolute path" in content)

    def test_cr12_post_dispatch_directory_verification(self) -> None:
        content = _read_orch().lower()
        assert "post-dispatch" in content or ("verify" in content and "directory" in content)

    def test_startup_git_pull_before_preflight(self) -> None:
        content = _read_claude()
        startup_start = content.find("## ON STARTUP")
        assert startup_start != -1
        startup_section = content[startup_start:startup_start + 800]
        assert "git pull" in startup_section

    def test_settings_local_json_merge_rule(self) -> None:
        """orchestration.md must contain settings.local.json additive merge rule."""
        content = _read_orch().lower()
        assert "settings.local.json" in content
        assert "merge" in content or "additive" in content

    # -- Context.md target format validation --
    def test_orchestration_validates_target_format(self) -> None:
        content = _read_orch()
        assert "list-active-role-types" in content
        lower = content.lower()
        assert "verify" in lower and ("slug" in lower or "role type" in lower)

    # -- Foreground-only dispatch rule (V23) --
    def test_foreground_only_dispatch_rule(self) -> None:
        """orchestration.md or CLAUDE.md must prohibit background subagent dispatches."""
        orch = _read_orch().lower()
        claude = _read_claude().lower()
        combined = orch + claude
        assert "foreground" in combined or "background" in combined, (
            "Must contain explicit foreground-only or background-prohibition rule"
        )
```

---

#### Step 23a: Implement constraint compliance fixes — CLAUDE.md startup + core rules
**File:** `03_agents/tests/v25/CLAUDE.md`
**Action:** Modify

In `CLAUDE.md` ON STARTUP section, replace:

```
1. **Run preflight:** `bash scripts/preflight.sh` — executes cleanup + dedup automatically.
```

With:

```
1. **Session resume guard:** Read `output/digests/_status.json`. If `sent_at` matches today's date, prompt user using UX Protocol Rule 7 format: `"A digest was already sent today ({sent_at}). Resume this session or abort? (resume/abort)"` Do NOT re-initialize if user chooses abort.
2. **Agent memory read:** Read `.claude/agent-memory/*/MEMORY.md` and treat documented failures as hard constraints. (HC4 compliance — 3-version recurrence V14/V17/V19.)
3. **Git pull (interactive mode only):** If `$SCHEDULED_RUN` NOT set, run `git pull --ff-only` and verify success BEFORE any file reads or preflight. Fail = stop.
4. **Run preflight:** `bash scripts/preflight.sh` — executes cleanup + dedup automatically.
```

And renumber remaining items (old 2→5, 3→6, etc.). Remove the old standalone `git pull` step (old item 5).

Add foreground-only dispatch rule to `CLAUDE.md` (Core Rules section):

```markdown
**All subagent dispatches MUST be foreground-only.** Do NOT use background Task dispatches (`run_in_background: true`). Every subagent dispatch must block until completion so gate-checks can run immediately after. Background dispatches bypass gate enforcement and cause untracked state. (V23 regression.)
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_orchestration.py -v -k "test_startup_git_pull or test_foreground"` (expect PASS after Step 23b)

---

#### Step 23b: Implement constraint compliance fixes — orchestration.md additions
**File:** `03_agents/tests/v25/references/orchestration.md`
**Action:** Modify

In `references/orchestration.md`, add to POST-CHECKPOINT sections:

```
State absolute file paths for all output artifacts before committing (CR-7).

Post-dispatch directory verification (CR-12): After checkpoint write, verify output files exist in expected directories.
```

Add HC-10 mandatory variables to dispatch templates:

```
working_dir, output_directory, dashboard_url
```

Add working directory validation rule to dispatch templates section:

```markdown
**Working Directory Validation (V19 compliance):** All dispatch prompts MUST set `working_dir` to the absolute path resolving to `03_agents/tests/v25/` (e.g., `/Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v25/`). NEVER use relative paths or previous version paths. Subagent dispatch prompts that contain `v24`, `v23`, or relative `./` paths are invalid — stop and fix before dispatching.
```

**HC-10 audit — concrete templates for ALL dispatch types.** Every Task tool dispatch in orchestration.md MUST include `working_dir`, `output_directory`, and `dashboard_url` in the prompt JSON. The following templates are authoritative:

**Gate-check dispatch (commit gate):**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "command": "python3 scripts/manage_state.py verify-and-commit --phase {phase} --channel {channel}", "gate_name": "commit-gate-{channel}"}'
```

**Gate-check dispatch (session-state gate):**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "command": "python3 scripts/manage_state.py verify-session-state-written --session-state-path output/session-state.md --run-date {run_date}", "gate_name": "session-state-gate"}'
```

**Recovery dispatch (post-compaction re-dispatch):**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "recovery_context": "post-compaction", "failed_task_id": "{task_id}", "resume_phase": "{phase}"}'
description: "Recovery: re-dispatch {subagent_type} after compaction"
```

Search-verify, brief-generator, digest-email, and briefs-html templates already include HC-10 variables in Steps 15 and 19.

Add settings.local.json additive merge rule to `references/orchestration.md` (in the configuration section):

```markdown
### settings.local.json Additive Merge (V18 compliance)

When modifying `settings.local.json`, ALWAYS:
1. Read the existing file first (`json.load`)
2. Merge new entries into existing dict (additive, not overwrite)
3. Preserve all existing permissions and entries
4. Write back the merged result

NEVER overwrite `settings.local.json` with a fresh dict. This preserves user-configured permissions across runs.

**Bloat cap (V23):** If `settings.local.json` exceeds 50 entries after merge, log a warning and remove the oldest entries (by alphabetical key sort) to stay under 50. This prevents unbounded growth across runs.
```

Add mandatory post-push Vercel deploy step to `references/orchestration.md` (after the commit gate section or as a post-Phase 5 step):

```markdown
### Vercel Dashboard Deploy (MANDATORY — once per session)

After the FINAL channel commit gate push in Phase 1 (i.e., after all 5 channels have been committed and pushed), dispatch a single subagent to redeploy the Vercel dashboard. Do NOT deploy after every individual channel push — this avoids triggering up to 5 redundant deploys. If Phase 5 send also pushes data, deploy once more after Phase 5 send completes.

```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "command": "vercel link --project jsa-dashboard --yes && vercel --prod --yes"}'
description: "Deploy Vercel dashboard after data push"
```

This is mandatory because the dashboard reads from the pushed data. Without redeployment, the dashboard shows stale results. (V21/V22 recurrence.)
```

Add a corresponding test to `TestArchitecturalCompliance` in `tests/test_orchestration.py`:

```python
    def test_vercel_deploy_after_push(self) -> None:
        """orchestration.md must contain mandatory Vercel deploy step after push."""
        content = _read_orch().lower()
        assert "vercel" in content, "orchestration.md must reference Vercel deploy"
        assert "vercel --prod" in content or "vercel deploy" in content, (
            "orchestration.md must contain vercel --prod deploy command"
        )
```

**Note:** Constraint compliance, context validation, and task ID persistence tests are consolidated into the `TestArchitecturalCompliance` class created in Step 22 (post-compaction recovery). No separate test classes needed here.

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_orchestration.py -v -k "TestArchitecturalCompliance"` (expect PASS)

---

#### Step 24: Implement context.md target format validation
**File:** `03_agents/tests/v25/references/orchestration.md`
**Action:** Modify

Add after the "Active Role Types" subsection text about consuming the list:

```markdown
**Target Format Validation:** After writing or modifying `context.md ## Target`, run:

```bash
python3 scripts/manage_state.py list-active-role-types --context-path context.md
```

Verify the output contains the expected number of clean slug entries (one per role type). Each slug must match `^[a-z0-9-]+$` (lowercase alphanumeric with hyphens only). If slug count does not match the number of bullet items in `## Target`, or any slug fails the format regex, STOP and fix the Target section formatting before proceeding.
```

Add a slug format test to `tests/test_manage_state.py` (or `tests/test_orchestration.py`):

```python
class TestSlugFormat:
    """Test that list-active-role-types produces valid slug format."""

    def test_slug_format_regex(self, tmp_path: Path) -> None:
        """Each slug line from list-active-role-types must match ^[a-z0-9-]+$."""
        import re
        context = tmp_path / "context.md"
        context.write_text(
            "# Context\n\n## Target\n- AI Engineer\n- Product Manager\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "list-active-role-types",
             "--context-path", str(context)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        slug_pattern = re.compile(r"^[a-z0-9-]+$")
        for line in result.stdout.strip().splitlines():
            assert slug_pattern.match(line.strip()), (
                f"Slug '{line.strip()}' does not match ^[a-z0-9-]+$ format"
            )
```

---

#### Step 25: Implement task ID persistence
**File:** `03_agents/tests/v25/references/orchestration.md`
**Action:** Modify

Add to the Channel Dispatch section (after the `.done` sentinel mention):

```markdown
**Task ID Persistence:** After dispatching each search-verify subagent, append the task ID to `session-state.md ## Active Tasks`. Format: `- {task_id}: search-verify {channel-name} (dispatched {timestamp})`. This enables post-compaction recovery.
```

Note: Task ID persistence for Phase 5 delivery dispatches is already included in the tiered delivery rewrite (Step 19).

---

#### Step 26: Verify + Commit Layer 2 (merged from old Steps 26-27)
**Description:** Run full Layer 2 test suite and commit.

**Pre-commit verification:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_orchestration.py tests/test_dispatch_counter.py -v`
- Lint: `cd 03_agents/tests/v25 && ruff check scripts/`

**Commit (only if all verifications pass):**

```bash
git add 03_agents/tests/v25/
git commit -m "build(jsa): V25 Layer 2 — orchestration + config fixes

- Mandatory 5-channel parallel dispatch rule
- Structural commit gate (verify-and-commit) with exit codes + --no-push
- Session-state write gate (verify-session-state-written, structured date check)
- Tiered delivery (mandatory email + budget-gated briefs-html)
- Dispatch counter (increment + check-budget, ceiling 25, regex approach)
- Post-compaction recovery protocol
- Constraint compliance (HC-5, HC-10, CR-7, CR-12, git pull, foreground-only)
- Context Budget section in CLAUDE.md
- Context.md target format validation
- Task ID persistence in session-state.md
- settings.local.json additive merge rule
- Mandatory Vercel deploy after data push
- Non-fast-forward push handling (pull --ff-only before retry)
- HC-10 concrete templates for gate-check and recovery dispatches
- Slug format validation (^[a-z0-9-]+$)"
```

**Verify:**
- `git status` shows clean after commit

---

### Phase 3: UX Protocol (Layer 3)

#### Step 28: Write failing tests for UX format strings
**File:** `03_agents/tests/v25/tests/test_orchestration.py`
**Action:** Modify

Append 6 UX tests to test file:

**Copy spec:**
- Brief progress format: `Brief {N}/{total} done — {company name}`
- Timed status format: `Still running: {N}/{total} complete`
- Post-compaction status: "First user-visible output after compaction MUST be a 1-2 sentence summary of completed/pending work."
- Selection format: single numbered list across all role types
- Section header format: `## {Role Type} ({N} new, {M} active)`

```python
# ---------------------------------------------------------------------------
# Layer 3 — UX Protocol (all 5 format rules in single class)
# ---------------------------------------------------------------------------


class TestUxProtocol:
    def test_ux_brief_progress_format(self) -> None:
        """orchestration.md UX Protocol must contain one-liner brief progress format."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "Brief {N}/{total} done" in section, (
            "UX Protocol must contain brief progress format: "
            "'Brief {N}/{total} done — {company name}'"
        )
        assert "{company name}" in section or "{company}" in section

    def test_ux_timed_status_format(self) -> None:
        """orchestration.md UX Protocol must contain proactive timed status format."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "Still running: {N}/{total} complete" in section

    def test_ux_post_compaction_immediate_status(self) -> None:
        """orchestration.md UX Protocol must require immediate status after compaction."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        lower = section.lower()
        assert "compaction" in lower
        assert "1-2 sentence summary" in lower

    def test_ux_unified_numbered_selection(self) -> None:
        """orchestration.md UX Protocol must require single numbered list across role types."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        lower = section.lower()
        assert "single numbered list" in lower or "unified numbered" in lower

    def test_ux_section_headers_with_counts(self) -> None:
        """orchestration.md UX Protocol must contain section header format with counts."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "{Role Type} ({N} new, {M} active)" in section

    def test_ux_one_question_at_a_time(self) -> None:
        """orchestration.md UX Protocol must contain one-question-at-a-time rule (CR-4)."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        lower = section.lower()
        assert "one question" in lower, (
            "UX Protocol must contain one-question-at-a-time rule (CR-4)"
        )

    def test_ux_gate_failure_alert_format(self) -> None:
        """orchestration.md UX Protocol must contain gate failure alert format."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "[GATE FAILED]" in section, (
            "UX Protocol must contain gate failure alert format: "
            "'[GATE FAILED] {gate-name} — {reason}. Action: {what happens next}.'"
        )

    def test_ux_session_resume_prompt_format(self) -> None:
        """orchestration.md UX Protocol must contain session resume prompt format."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "resume" in section.lower() and "abort" in section.lower(), (
            "UX Protocol must contain session resume prompt format with resume/abort options"
        )

    def test_ux_end_of_session_completion_summary(self) -> None:
        """orchestration.md UX Protocol must contain end-of-session completion summary format."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "Session complete" in section or "session complete" in section.lower(), (
            "UX Protocol must contain end-of-session completion summary format"
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_orchestration.py -v -k "TestUxProtocol"` (expect FAIL)

---

#### Step 29: Implement UX Protocol section in orchestration.md
**File:** `03_agents/tests/v25/references/orchestration.md`
**Action:** Modify

Append the following section at the end of the file:

```markdown
---

## UX Protocol

Seven mandatory format rules for all user-facing output during orchestration.

### 1. Brief Progress (one-liner after each brief completes)

Format: `Brief {N}/{total} done — {company name}`

Emit this line immediately after each brief-generator subagent returns. Keeps the user informed without flooding the conversation. Full status table only once at end.

### 2. Proactive Timed Status (long-running phases)

Format: `Still running: {N}/{total} complete`

If a phase (search or brief generation) exceeds 90 seconds without user-visible output, emit this status line. Reset the timer after each emission.

**Implementation note:** Claude Code has no timer primitive. Parent counts tool-call round-trips as proxy. After ~3 consecutive subagent dispatches or gate-checks with no user-visible output, emit the timed status line.

### 3. Post-Compaction Immediate Status

First user-visible output after compaction MUST be a 1-2 sentence summary of completed/pending work. Never resume with a bare action or tool call — always orient the user first.

### 4. Unified Numbered Selection

When presenting jobs for user selection, use a single numbered list across all role types. Do not restart numbering per role type. The user picks by number; duplicate or reset numbering causes selection errors.

### 5. Section Headers with Counts

Format: `## {Role Type} ({N} new, {M} active)`

Every role-type section header in the presentation phase must include new and active counts. This gives the user an instant read on volume before scanning the table.

### 6. One Question at a Time (CR-4)

Ask one question per message. Never combine multiple questions in a single user-facing message. If you need answers to multiple things, ask the most important one first, wait for the response, then ask the next. This prevents user confusion and ensures clear signal per response.

### 7. Session Resume Prompt

When a digest was already sent today (detected during ON STARTUP), use this exact format:

`"A digest was already sent today ({sent_at}). Resume this session or abort? (resume/abort)"`

Do not rephrase or combine with other questions. Present this as a standalone decision prompt before any other action.

### End-of-Session Completion Summary

When the session completes successfully (all phases done, digest sent), emit:

`"Session complete: {N} new jobs found, {M} briefs generated, digest sent to {email}."`

This provides closure and confirms the session's output. Emit once, after Phase 5 send succeeds.

### Gate Failure Alert Format

When a gate-check fails, surface the failure to the user in this format:

`[GATE FAILED] {gate-name} — {reason}. Action: {what happens next}.`

Examples:
- `[GATE FAILED] commit-gate-linkedin — git push failed (transient). Action: retrying (attempt 2/2).`
- `[GATE FAILED] session-state-gate — session-state.md missing 2026-03-02 entry. Action: re-dispatching gate-check.`
- `[GATE FAILED] commit-gate-indeed — merge conflict (unrecoverable). Action: stopping pipeline, alerting user.`
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_orchestration.py -v -k "TestUxProtocol"` (expect PASS)

---

#### Step 30: Verify + Commit Layer 3 (merged from old Steps 30-31)
**Description:** Run full test suite (all layers) and commit Layer 3.

**Pre-commit verification:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/ -v`
- Lint: `cd 03_agents/tests/v25 && ruff check scripts/`
- Type check: `cd 03_agents/tests/v25 && mypy scripts/manage_state.py --ignore-missing-imports`

**Commit (only if all verifications pass):**

```bash
git add 03_agents/tests/v25/
git commit -m "build(jsa): V25 Layer 3 — UX protocol format strings

- Brief progress one-liner: Brief {N}/{total} done — {company name}
- Proactive timed status: Still running: {N}/{total} complete (with round-trip proxy)
- Post-compaction immediate status requirement
- Unified numbered selection across role types
- Section headers with counts: ## {Role Type} ({N} new, {M} active)
- One question at a time (CR-4)
- Session resume prompt format (UX Protocol Rule 7)
- Gate failure alert format: [GATE FAILED] {gate-name} — {reason}. Action: {next}.
- End-of-session completion summary format"
```

**Verify:**
- `git status` shows clean after commit

---

## Deployment Verification

### Pre-Deploy Checks

```bash
cd 03_agents/tests/v25

# Full test suite
python -m pytest tests/ -v

# Lint
ruff check scripts/
shellcheck scripts/preflight.sh

# Type check
mypy scripts/manage_state.py --ignore-missing-imports

# Verify critical files exist
test -f references/orchestration.md && echo "orchestration.md OK"
test -f CLAUDE.md && echo "CLAUDE.md OK"
test -f .claude/agents/search-verify.md && echo "search-verify.md OK"

# Verify no placeholder code
grep -rn "TODO\|TBD\|implement later" scripts/ references/ .claude/agents/ && echo "FAIL: placeholders found" || echo "No placeholders"
```

### Post-Deploy Checks

```bash
cd 03_agents/tests/v25

# Smoke test: preflight first-run detection
mkdir -p /tmp/v25-smoke/output/verified
bash scripts/preflight.sh --working-dir /tmp/v25-smoke 2>&1 | grep -i "first run" && echo "First-run OK"

# Smoke test: manage_state.py subcommands exist
python scripts/manage_state.py verify-and-commit --help >/dev/null 2>&1 && echo "verify-and-commit OK"
python scripts/manage_state.py verify-session-state-written --help >/dev/null 2>&1 && echo "verify-session-state-written OK"
python scripts/manage_state.py increment-dispatch-counter --help >/dev/null 2>&1 && echo "increment-dispatch-counter OK"
python scripts/manage_state.py check-dispatch-budget --help >/dev/null 2>&1 && echo "check-dispatch-budget OK"

# Verify orchestration.md has all V25 sections
grep -c "verify-and-commit\|verify-session-state-written\|Tiered Delivery\|UX Protocol\|Post-Compaction" references/orchestration.md

# Verify CLAUDE.md has V25 additions
grep -c "DISPATCH_CEILING\|compaction\|git pull" CLAUDE.md
```

### Rollback Plan

```bash
cd /Users/ryanhennebry/Projects/autonomous1

# Option 1: Remove v25 entirely (if no good commits)
rm -rf 03_agents/tests/v25

# Option 2: Revert specific commits (if partially deployed)
git log --oneline -5  # identify V25 commits
git revert <commit-hash> --no-edit  # revert each V25 commit

# Verify rollback
ls 03_agents/tests/v25 2>/dev/null && echo "v25 still exists" || echo "v25 removed"
cd 03_agents/tests/v24 && python -m pytest tests/ -v  # v24 still works
```

---

## Handoff Contract
- Total steps: ~28 (Step 23 split into 23a/23b per R3 code-simplicity-reviewer), Total phases: 3
- Files created: `03_agents/tests/v25/` (copy of v24), `tests/test_schema_validation.py`, `tests/test_dispatch_counter.py`, `tests/test_orchestration.py`
- Files modified: `scripts/preflight.sh`, `scripts/manage_state.py`, `.claude/agents/search-verify.md`, `references/orchestration.md`, `CLAUDE.md`, `tests/test_preflight.py`, `tests/test_manage_state.py`
- Test classes in test_orchestration.py: 4 consolidated classes (TestPhase1Gates, TestPhase5Delivery, TestArchitecturalCompliance, TestUxProtocol)
- UX Protocol rules: 7 (up from 6) + gate failure alert format + end-of-session completion summary
- Verification sequence: Layer 1 verify+commit → Layer 2 verify+commit → Layer 3 verify+commit (test runs folded into commit steps)
- Deployment verification: pre-deploy, post-deploy, rollback — all present
- Round 2 revisions: 11 findings applied (HC-10 templates, Vercel deploy, non-ff push handling, verify-session-state 2-tier simplification, --check-session-state removal, timed status proxy, CR-4 rule, dedup internal helper, gate failure format, slug regex, tier-skip notification)
- Round 3 revisions: 7 findings applied (send_email.py HC-5 Context Budget, session resume prompt format, _read_dispatch_count regex symmetry, Vercel deploy once-per-session scoping, gate failure stderr reformatting, Step 23 split into 23a/23b, end-of-session completion summary)

<!-- STAGE COMPLETE: /plan, 2026-02-27 -->
<!-- STAGE COMPLETE: /revise after round 1, 2026-03-02 -->
<!-- STAGE COMPLETE: /revise after round 2, 2026-03-02 -->
<!-- STAGE COMPLETE: /revise after round 3, 2026-03-02 -->

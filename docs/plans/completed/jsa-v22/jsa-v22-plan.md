# Plan: JSA V22 — Checkpoint-Driven Architecture

## Overview

Extend the Job Search Agent with checkpoint-driven phase enforcement. Three implementation layers:

1. **Checkpoint Infrastructure** — extend `manage_state.py` with `checkpoint write/validate/status/clear` subcommands + unit tests + benchmark
2. **Orchestration Integration** — update `orchestration.md` with pre-gate/post-checkpoint wrappers, add `background: true` to all agents, remove foreground-fallback guard, update `preflight.sh`, simplify `settings.local.json`
3. **Scheduling & Deployment** — migrate `daily-digest.yml` to `anthropics/claude-code-base-action@beta`, add Vercel deploy step

**Success criteria:** 0 HC7 regressions, 0 session-state regressions, scheduled run < 60min, `background: true` works, 101+ tests pass.

**Prerequisite:** Copy `03_agents/tests/v21/` to `03_agents/tests/v22/` before starting. Update version references in CLAUDE.md, preflight.sh headers.

## Context Budget

| Operation | Parent-Allowed | Subagent-Only |
|---|---|---|
| `checkpoint write/validate/status/clear` | Yes (lightweight state CLI) | Also allowed |
| `git add && git commit && git push` | Yes (state commits) | Also allowed |
| Search (WebFetch, WebSearch, JobSpy) | No | Yes |
| Filter / Verify / Dedup logic | No | Yes |
| Brief generation | No | Yes |
| Email sending | No | Yes |
| `python3 scripts/manage_state.py` (non-checkpoint) | No | Yes |

Note: Checkpoint CLI calls are parent-allowed because they are lightweight state operations (read/write JSON). All substantive pipeline work (search, filter, dedup, WebFetch, WebSearch) remains subagent-only.

## Files to Modify

- `03_agents/tests/v22/scripts/manage_state.py` — checkpoint subcommands (write, validate, status, clear)
- `03_agents/tests/v22/tests/test_manage_state.py` — 12 new checkpoint tests + 1 benchmark
- `03_agents/tests/v22/tests/test_workflow.py` — workflow & agent config tests
- `03_agents/tests/v22/tests/test_claude_md.py` — foreground-fallback removal test
- `03_agents/tests/v22/tests/test_preflight.py` — checkpoint validation tests
- `03_agents/tests/v22/references/orchestration.md` — pre-gate/post-checkpoint wrappers
- `03_agents/tests/v22/.claude/agents/*.md` — add `background: true` to all 6 agents
- `03_agents/tests/v22/CLAUDE.md` — remove foreground-fallback guard
- `03_agents/tests/v22/scripts/preflight.sh` — checkpoint & background validation
- `03_agents/tests/v22/.claude/settings.local.json` — simplify permissions
- `03_agents/tests/v22/output/.checkpoints/.gitkeep` — new directory structure
- `03_agents/tests/v22/output/.checkpoints/.gitignore` — ignore runtime checkpoint JSONs
- `.github/workflows/daily-digest.yml` — migrate to claude-code-base-action@beta

## Implementation Steps

---

### Layer 1: Checkpoint Infrastructure

---

### Step 1: Create checkpoint directory structure

**File:** `v22/output/.checkpoints/.gitkeep`
**Action:** Create (empty file)

**File:** `v22/output/.checkpoints/.gitignore`
**Action:** Create

```gitignore
# Checkpoint JSON files are runtime artifacts — never commit
*.json

# Keep structure files
!.gitkeep
!.gitignore
```

**Verify:**
- Test: `test -d 03_agents/tests/v22/output/.checkpoints && echo OK`
- Lint: N/A (non-code files)

---

### Step 2: Checkpoint write — tests + implementation

**File:** `v22/tests/test_manage_state.py`
**Action:** Modify — append after end of file (after `TestDedup` class)

```python
# ---------------------------------------------------------------------------
# Helpers for checkpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def cp_output_dir(tmp_path: Path) -> Path:
    """Create and return a tmp_path/output/.checkpoints structure for checkpoint tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    (output_dir / ".checkpoints").mkdir()
    return output_dir


def _run_checkpoint(
    args: list[str], output_dir: str
) -> subprocess.CompletedProcess:
    """Run checkpoint subcommand against a given output directory."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "checkpoint",
    ] + args + [
        "--output-dir",
        output_dir,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


class TestCheckpointWrite:
    """Tests for the checkpoint write subcommand."""

    def test_checkpoint_write_creates_file(self, cp_output_dir: Path) -> None:
        """Run checkpoint write search --count 5, verify file exists."""
        result = _run_checkpoint(
            ["write", "search", "--count", "5"],
            str(cp_output_dir),
        )
        assert result.returncode == 0, f"checkpoint write failed: {result.stderr}"

        cp_file = cp_output_dir / ".checkpoints" / "search.json"
        assert cp_file.exists(), "checkpoint file search.json should exist after write"

    def test_checkpoint_write_content(self, cp_output_dir: Path) -> None:
        """Verify JSON keys: phase, count, committed, timestamp."""
        result = _run_checkpoint(
            ["write", "search", "--count", "5"],
            str(cp_output_dir),
        )
        assert result.returncode == 0, f"checkpoint write failed: {result.stderr}"

        cp_file = cp_output_dir / ".checkpoints" / "search.json"
        data = json.loads(cp_file.read_text(encoding="utf-8"))

        assert data["phase"] == "search"
        assert data["count"] == 5
        assert data["committed"] is True
        assert "timestamp" in data

    def test_checkpoint_write_unknown_phase_fails(self, cp_output_dir: Path) -> None:
        """Exit code != 0 for invalid phase name."""
        result = _run_checkpoint(
            ["write", "bogus-phase", "--count", "1"],
            str(cp_output_dir),
        )
        assert result.returncode != 0, "unknown phase should fail"

    def test_checkpoint_write_requires_count(self, cp_output_dir: Path) -> None:
        """Missing --count flag causes failure."""
        result = _run_checkpoint(
            ["write", "search"],
            str(cp_output_dir),
        )
        assert result.returncode != 0, "missing --count should fail"
```

**File:** `v22/scripts/manage_state.py`
**Action:** Modify

**2a.** Insert after `VALID_ACTIONS = ...` constant (line ~22):

```python
VALID_CHECKPOINT_PHASES = ["search", "verify", "dedup", "present", "deliver"]
```

Note: `VALID_CHECKPOINT_PHASES` is the single source of truth for phase names. Tests should import and reference this constant from `manage_state.py` rather than duplicating the list. Orchestration.md phase headings must match these names.

**2b.** First, update the existing import `from datetime import datetime, timedelta` to `from datetime import datetime, timedelta, timezone`. Then insert after the `_cli_dedup` function (after line ~437), before the `main()` function:

```python
# ---------------------------------------------------------------------------
# Checkpoint subcommands
# ---------------------------------------------------------------------------


def _cli_checkpoint_write(args: argparse.Namespace) -> None:
    """Write a checkpoint file for the given phase."""
    output_dir = Path(args.output_dir)
    checkpoints_dir = output_dir / ".checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "phase": args.phase,
        "count": args.count,
        "committed": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    cp_path = checkpoints_dir / f"{args.phase}.json"
    with open(cp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
```

**2c.** Insert inside `main()`, after the `dedup_parser.set_defaults(func=_cli_dedup)` line (before `args = parser.parse_args()`):

```python
    # --- checkpoint ---
    cp_parser = subparsers.add_parser("checkpoint", help="Checkpoint operations")
    cp_subparsers = cp_parser.add_subparsers(dest="cp_command", required=True)

    # Add --output-dir to parent cp_parser (propagates to all subparsers)
    cp_parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=str(Path(__file__).resolve().parent.parent / "output"),
        help="Base output directory",
    )

    # checkpoint write
    cp_write = cp_subparsers.add_parser("write", help="Write a phase checkpoint")
    cp_write.add_argument(
        "phase",
        choices=VALID_CHECKPOINT_PHASES,
        help="Pipeline phase name",
    )
    cp_write.add_argument("--count", type=int, required=True, help="Item count")
    cp_write.set_defaults(func=_cli_checkpoint_write)
```

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_manage_state.py::TestCheckpointWrite -v` (expect 4 PASS)
- Lint: `cd 03_agents/tests/v22 && ruff check scripts/manage_state.py tests/test_manage_state.py`

---

### Step 3: Checkpoint validate — tests + implementation

**File:** `v22/tests/test_manage_state.py`
**Action:** Modify — append after `TestCheckpointWrite`

```python
class TestCheckpointValidate:
    """Tests for the checkpoint validate subcommand."""

    def test_validate_existing_checkpoint_passes(self, cp_output_dir: Path) -> None:
        """Write then validate — exit 0."""
        write_result = _run_checkpoint(
            ["write", "search", "--count", "5"],
            str(cp_output_dir),
        )
        assert write_result.returncode == 0, f"write failed: {write_result.stderr}"

        val_result = _run_checkpoint(
            ["validate", "search"],
            str(cp_output_dir),
        )
        assert val_result.returncode == 0, f"validate should pass: {val_result.stderr}"

    def test_validate_missing_checkpoint_fails(self, cp_output_dir: Path) -> None:
        """Validate without write — exit 1."""
        val_result = _run_checkpoint(
            ["validate", "verify"],
            str(cp_output_dir),
        )
        assert val_result.returncode == 1, "validate on missing checkpoint should exit 1"
```

**File:** `v22/scripts/manage_state.py`
**Action:** Modify

**3a.** Insert handler after `_cli_checkpoint_write`:

```python
def _cli_checkpoint_validate(args: argparse.Namespace) -> None:
    """Validate that a checkpoint exists and is committed."""
    output_dir = Path(args.output_dir)
    cp_path = output_dir / ".checkpoints" / f"{args.phase}.json"

    if not cp_path.exists():
        print(f"FAIL: no checkpoint for phase '{args.phase}'", file=sys.stderr)
        sys.exit(1)

    with open(cp_path, encoding="utf-8") as f:
        data = json.load(f)

    # Minimal schema validation
    required_keys = {"phase", "count", "timestamp"}
    missing = required_keys - set(data.keys())
    if missing:
        print(f"FAIL: checkpoint '{args.phase}' missing required keys: {missing}", file=sys.stderr)
        sys.exit(1)

    if not data.get("committed", False):
        print(f"FAIL: checkpoint '{args.phase}' exists but not committed", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {args.phase} — count={data.get('count', '?')}")
```

**3b.** Insert subparser in `main()` after `cp_write.set_defaults(...)`:

```python
    # checkpoint validate
    cp_validate = cp_subparsers.add_parser("validate", help="Validate a phase checkpoint")
    cp_validate.add_argument(
        "phase",
        choices=VALID_CHECKPOINT_PHASES,
        help="Pipeline phase name",
    )
    cp_validate.set_defaults(func=_cli_checkpoint_validate)
```

Note: `--output-dir` is inherited from the parent `cp_parser` (added in Step 2c). No per-subparser duplication needed.

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_manage_state.py::TestCheckpointValidate -v` (expect 2 PASS)
- Lint: `cd 03_agents/tests/v22 && ruff check scripts/manage_state.py tests/test_manage_state.py`

---

### Step 4: Checkpoint status + clear — tests + implementation

**File:** `v22/tests/test_manage_state.py`
**Action:** Modify — append after `TestCheckpointValidate`

```python
class TestCheckpointStatus:
    """Tests for the checkpoint status subcommand."""

    def test_status_shows_all_phases(self, cp_output_dir: Path) -> None:
        """Write 2 checkpoints, output lists all 5 phases with complete/pending."""
        _run_checkpoint(["write", "search", "--count", "5"], str(cp_output_dir))
        _run_checkpoint(["write", "verify", "--count", "3"], str(cp_output_dir))

        result = _run_checkpoint(["status"], str(cp_output_dir))
        assert result.returncode == 0, f"status failed: {result.stderr}"

        out = result.stdout
        assert "search" in out
        assert "verify" in out
        assert "dedup" in out
        assert "present" in out
        assert "deliver" in out

        lines = out.strip().splitlines()
        phase_lines = {l.split()[0]: l for l in lines if any(p in l for p in ["search", "verify", "dedup", "present", "deliver"])}
        assert "complete" in phase_lines.get("search", "").lower() or "5" in phase_lines.get("search", "")
        assert "pending" in phase_lines.get("dedup", "").lower()

    def test_status_empty(self, cp_output_dir: Path) -> None:
        """All phases show pending when no checkpoints written."""
        result = _run_checkpoint(["status"], str(cp_output_dir))
        assert result.returncode == 0, f"status failed: {result.stderr}"

        out = result.stdout.lower()
        assert out.count("pending") == 5, f"expected 5 pending phases, got: {result.stdout}"


class TestCheckpointClear:
    """Tests for the checkpoint clear subcommand."""

    def test_clear_removes_all(self, cp_output_dir: Path) -> None:
        """Write checkpoints, clear, verify removed."""
        cp_dir = cp_output_dir / ".checkpoints"

        _run_checkpoint(["write", "search", "--count", "5"], str(cp_output_dir))
        _run_checkpoint(["write", "verify", "--count", "3"], str(cp_output_dir))

        assert (cp_dir / "search.json").exists()
        assert (cp_dir / "verify.json").exists()

        result = _run_checkpoint(["clear"], str(cp_output_dir))
        assert result.returncode == 0, f"clear failed: {result.stderr}"

        assert not (cp_dir / "search.json").exists(), "search.json should be removed after clear"
        assert not (cp_dir / "verify.json").exists(), "verify.json should be removed after clear"

    def test_clear_idempotent(self, cp_output_dir: Path) -> None:
        """Clear when empty produces no error."""
        result = _run_checkpoint(["clear"], str(cp_output_dir))
        assert result.returncode == 0, f"clear on empty should succeed: {result.stderr}"

```

Note: `checkpoint clear` is intentionally destructive -- it deletes all `.json` in `.checkpoints/` with no recovery path. This is by design: it runs only at Phase 1 pipeline start to reset stale state from prior runs. The `test_clear_only_runs_in_phase1_context` test in Step 12 (test_workflow.py) enforces this constraint.

**File:** `v22/scripts/manage_state.py`
**Action:** Modify

**4a.** Insert handlers after `_cli_checkpoint_validate`:

```python
def _cli_checkpoint_status(args: argparse.Namespace) -> None:
    """Print status table of all checkpoint phases."""
    output_dir = Path(args.output_dir)
    checkpoints_dir = output_dir / ".checkpoints"
    pad = max(len(p) for p in VALID_CHECKPOINT_PHASES) + 2

    for phase in VALID_CHECKPOINT_PHASES:
        cp_path = checkpoints_dir / f"{phase}.json"
        if cp_path.exists():
            with open(cp_path, encoding="utf-8") as f:
                data = json.load(f)
            committed = "yes" if data.get("committed", False) else "no"
            count = data.get("count", "?")
            ts = data.get("timestamp", "?")
            print(f"{phase:<{pad}} COMPLETE  count={count}  committed={committed}  ts={ts}")
        else:
            print(f"{phase:<{pad}} PENDING")


def _cli_checkpoint_clear(args: argparse.Namespace) -> None:
    """Delete all checkpoint JSON files."""
    output_dir = Path(args.output_dir)
    checkpoints_dir = output_dir / ".checkpoints"

    if not checkpoints_dir.exists():
        return

    for json_file in checkpoints_dir.glob("*.json"):
        json_file.unlink()

    print(f"Cleared all checkpoints in {checkpoints_dir}")
```

**4b.** Insert subparsers in `main()` after `cp_validate.set_defaults(...)`:

```python
    # checkpoint status
    cp_status = cp_subparsers.add_parser("status", help="Show status of all phases")
    cp_status.set_defaults(func=_cli_checkpoint_status)

    # checkpoint clear
    cp_clear = cp_subparsers.add_parser("clear", help="Clear all checkpoints")
    cp_clear.set_defaults(func=_cli_checkpoint_clear)
```

Note: `--output-dir` is inherited from the parent `cp_parser` (added in Step 2c). No per-subparser duplication needed.

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_manage_state.py::TestCheckpointStatus tests/test_manage_state.py::TestCheckpointClear -v` (expect 5 PASS)
- Lint: `cd 03_agents/tests/v22 && ruff check scripts/manage_state.py tests/test_manage_state.py`

---

### Step 5: Checkpoint performance benchmark test

**File:** `v22/tests/test_manage_state.py`
**Action:** Modify — append after `TestCheckpointClear`

```python
class TestCheckpointPerformance:
    """Performance benchmarks for checkpoint operations."""

    def test_direct_call_under_500ms(self, cp_output_dir: Path) -> None:
        """100 direct-call write+validate cycles complete in under 500ms.

        Tests checkpoint logic directly via Python function import,
        bypassing subprocess overhead."""
        import time
        import argparse as _argparse

        # Import checkpoint functions directly
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        import manage_state

        start = time.monotonic()

        for i in range(100):
            # Direct write
            write_args = _argparse.Namespace(
                phase="search",
                count=i,
                output_dir=str(cp_output_dir),
            )
            manage_state._cli_checkpoint_write(write_args)

            # Direct validate
            validate_args = _argparse.Namespace(
                phase="search",
                output_dir=str(cp_output_dir),
            )
            manage_state._cli_checkpoint_validate(validate_args)

        elapsed = time.monotonic() - start
        assert elapsed < 0.5, (
            f"100 direct write+validate cycles took {elapsed:.2f}s, expected < 0.5s"
        )

    @pytest.mark.slow
    def test_subprocess_under_2_seconds(self, cp_output_dir: Path) -> None:
        """10 subprocess write+validate cycles complete in under 2 seconds.

        Tests CLI integration (subprocess overhead) with reduced cycle count."""
        import time

        start = time.monotonic()

        for i in range(10):
            w = _run_checkpoint(
                ["write", "search", "--count", str(i)],
                str(cp_output_dir),
            )
            assert w.returncode == 0, f"write cycle {i} failed: {w.stderr}"

            v = _run_checkpoint(
                ["validate", "search"],
                str(cp_output_dir),
            )
            assert v.returncode == 0, f"validate cycle {i} failed: {v.stderr}"

        elapsed = time.monotonic() - start
        assert elapsed < 2.0, (
            f"10 subprocess write+validate cycles took {elapsed:.2f}s, expected < 2.0s"
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_manage_state.py::TestCheckpointPerformance -v` (expect PASS)
- Lint: `cd 03_agents/tests/v22 && ruff check tests/test_manage_state.py`

**Layer 1 commit:**
```bash
cd 03_agents/tests/v22 && pytest tests/test_manage_state.py -v && \
git add scripts/manage_state.py tests/test_manage_state.py output/.checkpoints/ && \
git commit -m "feat(jsa): add checkpoint write/validate/status/clear to manage_state.py"
```

---

### Layer 2: Orchestration Integration

---

### Step 6: Add pre-gate/post-checkpoint wrappers to orchestration.md with test

**File:** `v22/tests/test_workflow.py`
**Action:** Modify — append after existing tests

```python
def test_orchestration_has_pregate_for_all_phases() -> None:
    """Every phase except Phase 1 must have a PRE-GATE section with checkpoint validate."""
    from pathlib import Path
    ORCHESTRATION_MD = Path(__file__).resolve().parent.parent / "references" / "orchestration.md"
    content = ORCHESTRATION_MD.read_text(encoding="utf-8")

    # Phase 1 should NOT have checkpoint validate (it runs checkpoint clear)
    phase1_start = content.find("## Phase 1")
    phase2_start = content.find("## Phase 2")
    assert phase1_start != -1 and phase2_start != -1
    phase1_text = content[phase1_start:phase2_start]
    assert "checkpoint clear" in phase1_text, (
        "Phase 1 should run checkpoint clear, not checkpoint validate"
    )

    # Phases 2-5 must each have PRE-GATE with checkpoint validate
    for phase_num in range(2, 6):
        heading = f"## Phase {phase_num}"
        start = content.find(heading)
        assert start != -1, f"{heading} not found in orchestration.md"
        next_phase = content.find(f"## Phase {phase_num + 1}", start + 1)
        section = content[start:next_phase] if next_phase != -1 else content[start:]
        assert "PRE-GATE" in section, (
            f"{heading} missing PRE-GATE section in orchestration.md"
        )
        assert "checkpoint validate" in section, (
            f"{heading} PRE-GATE missing 'checkpoint validate' in orchestration.md"
        )
```

**File:** `v22/references/orchestration.md`
**Action:** Modify

For each phase, add PRE-GATE before entry criteria and POST-CHECKPOINT after exit criteria.

**Important:** All checkpoint CLI commands (`python3 scripts/manage_state.py checkpoint ...`) and git commit commands in PRE-GATE/POST-CHECKPOINT sections are executed by the active subagent for that phase, never by the parent orchestrator directly. The parent dispatches the subagent; the subagent runs the checkpoint commands as part of its phase work.

**Phase 1** — insert after `## Phase 1: Search` heading, before `### Entry Criteria`:

```markdown
### PRE-GATE

```bash
# Phase 1 starts fresh — clear any stale checkpoints
# Executed by the search subagent, not the parent orchestrator
python3 scripts/manage_state.py checkpoint clear
```

### BATCH-LEVEL COMMIT

After each search batch (each source query cycle), the search subagent MUST:

```bash
# Commit+push after EACH search batch to prevent data loss (6-version recurrence: V14/V16/V18/V19/V20/V21)
git add output/jobs/ && git commit -m "checkpoint(jsa): search batch N — $(date +%Y-%m-%d)" && git push origin main
# Update session-state.md after each batch (5-version recurrence: V14/V16/V18/V19/V21)
# Record: batch number, source queried, jobs found count, cumulative total
```
```

**Phase 1** — insert after `### Exit Criteria` bullet list, before `---`:

```markdown
### POST-CHECKPOINT

```bash
# Executed by the search subagent
python3 scripts/manage_state.py checkpoint write search --count N
git add output/.checkpoints/ output/jobs/ output/session-state.md && git commit -m "checkpoint(jsa): search complete — $(date +%Y-%m-%d)"
```
```

**Phase 2** — insert after `## Phase 2: Verify` heading, before `### Entry Criteria`:

```markdown
### PRE-GATE

```bash
# Executed by the verify subagent
python3 scripts/manage_state.py checkpoint validate search
```

If validation fails, STOP and report: "Phase 1 (Search) checkpoint missing — cannot proceed to Verify."
```

**Phase 2** — insert after `### Exit Criteria`, before `---`:

```markdown
### POST-CHECKPOINT

```bash
# Executed by the verify subagent
python3 scripts/manage_state.py checkpoint write verify --count N
git add output/.checkpoints/ output/verified/ && git commit -m "checkpoint(jsa): verify complete — $(date +%Y-%m-%d)"
```
```

**Phase 3** — insert after `## Phase 3: Dedup` heading:

```markdown
### PRE-GATE

```bash
# Executed by the dedup subagent
python3 scripts/manage_state.py checkpoint validate verify
```

If validation fails, STOP and report: "Phase 2 (Verify) checkpoint missing — cannot proceed to Dedup."
```

**Phase 3** — insert after exit criteria:

```markdown
### POST-CHECKPOINT

```bash
# Executed by the dedup subagent
python3 scripts/manage_state.py checkpoint write dedup --count N
git add output/.checkpoints/ output/verified/ output/_delta.json state.json && git commit -m "checkpoint(jsa): dedup complete — $(date +%Y-%m-%d)"
```
```

**Phase 4** — insert after `## Phase 4: Present` heading:

```markdown
### PRE-GATE

```bash
# Executed by the present subagent
python3 scripts/manage_state.py checkpoint validate dedup
```

If validation fails, STOP and report: "Phase 3 (Dedup) checkpoint missing — cannot proceed to Present."
```

**Phase 4** — insert after exit criteria:

```markdown
### POST-CHECKPOINT

```bash
# Executed by the present subagent
python3 scripts/manage_state.py checkpoint write present --count N
git add output/.checkpoints/ state.json && git commit -m "checkpoint(jsa): present complete — $(date +%Y-%m-%d)"
```
```

**Phase 5** — insert after `## Phase 5: Deliver` heading:

```markdown
### PRE-GATE

```bash
# Executed by the deliver subagent
python3 scripts/manage_state.py checkpoint validate present
```

If validation fails, STOP and report: "Phase 4 (Present) checkpoint missing — cannot proceed to Deliver."
```

**Phase 5** — insert after exit criteria:

```markdown
### POST-CHECKPOINT

**Email idempotency guard:** Before sending, verify `_status.json` `sent_at` is not already set for today's date. If already sent, skip email and log "already sent" (V15 regression).

```bash
# Executed by the deliver subagent
python3 scripts/manage_state.py checkpoint write deliver --count N
git add output/.checkpoints/ output/session-state.md state.json && git commit -m "checkpoint(jsa): deliver complete — $(date +%Y-%m-%d)"
```
```

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_workflow.py::test_orchestration_has_pregate_for_all_phases -v` (expect PASS)
- Lint: N/A (markdown file)

---

### Step 7: Add `background: true` to all agents with test

**File:** `v22/tests/test_workflow.py`
**Action:** Modify — append

```python
def test_all_agents_have_background_true() -> None:
    """Every agent .md file in .claude/agents/ must have background: true in YAML frontmatter."""
    from pathlib import Path
    import re
    agents_dir = Path(__file__).resolve().parent.parent / ".claude" / "agents"
    assert agents_dir.exists(), f"{agents_dir} does not exist"
    agent_files = sorted(agents_dir.glob("*.md"))
    assert len(agent_files) >= 6, f"Expected >= 6 agent files, found {len(agent_files)}"

    for agent_file in agent_files:
        content = agent_file.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert match, f"{agent_file.name} missing YAML frontmatter"
        frontmatter = match.group(1)
        assert re.search(r"^background:\s*true$", frontmatter, re.MULTILINE), (
            f"{agent_file.name} missing 'background: true' in YAML frontmatter"
        )
```

**File:** Each of the 6 agent `.md` files in `v22/.claude/agents/`
**Action:** Modify — add `background: true` as last line before closing `---`

For each agent file (`brief-generator.md`, `briefs-html.md`, `digest-email.md`, `onboarding.md`, `search-verify.md`, `source-researcher.md`), insert `background: true` as the last line of YAML frontmatter.

Example for `brief-generator.md` — change:
```yaml
---
name: brief-generator
description: Generate application brief for a single job match
tools: Bash, Read, Write, Glob, Grep
disallowedTools: WebFetch, WebSearch, NotebookEdit
skills: jsa-brief-generator
memory: project
model: inherit
---
```

To:
```yaml
---
name: brief-generator
description: Generate application brief for a single job match
tools: Bash, Read, Write, Glob, Grep
disallowedTools: WebFetch, WebSearch, NotebookEdit
skills: jsa-brief-generator
memory: project
model: inherit
background: true
---
```

Apply identical pattern to all 6 agents.

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_workflow.py::test_all_agents_have_background_true -v` (expect PASS)
- Lint: `cd 03_agents/tests/v22 && ruff check tests/test_workflow.py`

---

### Step 8: Remove foreground-fallback from CLAUDE.md with test

**File:** `v22/tests/test_claude_md.py`
**Action:** Modify — append after existing tests

```python
def test_no_foreground_fallback_guard() -> None:
    """CLAUDE.md must not contain foreground-fallback guard or dispatch_mode variable.

    V22: All subagents dispatch with background: true. No foreground fallback needed."""
    content = _read_claude_md().lower()
    assert "foreground-fallback" not in content, (
        "CLAUDE.md still contains 'foreground-fallback' — removed in V22"
    )
    assert "dispatch_mode" not in content, (
        "CLAUDE.md still contains 'dispatch_mode' — removed in V22"
    )
```

**File:** `v22/CLAUDE.md`
**Action:** Modify

**8a.** In `## ON STARTUP`, find and replace:

Old:
```
4. **Foreground-fallback guard:** On first subagent dispatch, if denied/errors: set `dispatch_mode = "foreground"`. If succeeds: `dispatch_mode = "background"`.
```

New:
```
4. **Subagent dispatch mode:** All subagents dispatch with `background: true`. No foreground fallback.
```

**8b.** In `## Context Budget`, find and replace:

Old:
```
**Foreground mode:** When `dispatch_mode = "foreground"`, all subagent dispatches run blocking. The subagent-only restriction still applies — the parent never executes these operations directly, even in foreground mode.
```

New:
```
**Dispatch mode:** All subagents run with `background: true`. The subagent-only restriction always applies — the parent never executes these operations directly.
```

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_claude_md.py::test_no_foreground_fallback_guard -v` (expect PASS)
- Lint: N/A (markdown file)

---

### Step 9: Update preflight.sh — add checkpoint validation

**File:** `v22/scripts/preflight.sh`
**Action:** Modify — insert into STRUCTURE TIER section

Insert after the existing orchestration.md phase heading check (after the presentation-rules.md check area):

```bash
    # orchestration.md contains checkpoint validate for phases 2-5
    if [[ -f "references/orchestration.md" ]]; then
        ORCH_CONTENT=$(cat "references/orchestration.md")
        if ! echo "$ORCH_CONTENT" | grep -q "checkpoint validate"; then
            fail "CRITICAL: references/orchestration.md missing 'checkpoint validate' for gated phases"
        fi

        if ! echo "$ORCH_CONTENT" | grep -q "checkpoint write"; then
            fail "CRITICAL: references/orchestration.md missing 'checkpoint write' for phase completion"
        fi

        if ! echo "$ORCH_CONTENT" | grep -q "checkpoint clear"; then
            fail "CRITICAL: references/orchestration.md missing 'checkpoint clear' in Phase 1"
        fi
    fi

    # .checkpoints/ directory exists (or output/.checkpoints/)
    if [[ ! -d "output/.checkpoints" ]]; then
        warn "WARNING: output/.checkpoints/ directory does not exist (will be created on first run)"
    fi

    # Each agent .md has background: true
    if [[ -d ".claude/agents" ]]; then
        for agent_file in .claude/agents/*.md; do
            [[ -f "$agent_file" ]] || continue
            if ! grep -q "^background: true$" "$agent_file"; then
                fail "CRITICAL: $agent_file missing 'background: true' in frontmatter"
            fi
        done
    fi
```

Note: The new checks above use `grep -q` partial string matching (e.g., `"checkpoint validate"`), consistent with existing preflight checks. Verify that existing checks in the STRUCTURE TIER also use partial matches rather than exact heading matches, to avoid fragile breakage from heading rewording.

**Verify:**
- Test: `cd 03_agents/tests/v22 && bash scripts/preflight.sh --structure`
- Lint: `cd 03_agents/tests/v22 && shellcheck scripts/preflight.sh` (if available)

---

### Step 10: Test preflight checkpoint validation

**File:** `v22/tests/test_preflight.py`
**Action:** Modify — append new test methods

```python
    def test_preflight_fails_missing_checkpoint_validate(
        self,
        tmp_path: Path,
    ) -> None:
        """orchestration.md missing checkpoint validate, exits 1."""
        _setup_passing_tree(tmp_path)
        # Overwrite orchestration.md without checkpoint commands
        (tmp_path / "references" / "orchestration.md").write_text(
            textwrap.dedent("""\
                # Orchestration

                ## Phase 1 — Search
                Search instructions.

                ## Phase 2 — Verify
                Verify instructions.

                ## Phase 3 — Dedup
                Dedup instructions.

                ## Phase 4 — Present
                Present instructions.

                ## Phase 5 — Deliver
                Deliver instructions.
            """),
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path), extra_args=["--structure"])
        assert result.returncode == 1, (
            f"preflight should fail when orchestration.md missing checkpoint validate.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_preflight_fails_agent_missing_background(
        self,
        tmp_path: Path,
    ) -> None:
        """Agent .md without background: true, exits 1."""
        _setup_passing_tree(tmp_path)
        agents_dir = tmp_path / ".claude" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "test-agent.md").write_text(
            textwrap.dedent("""\
                ---
                name: test-agent
                description: Test agent
                tools: Bash
                model: inherit
                ---
                You are a test agent.
            """),
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path), extra_args=["--structure"])
        assert result.returncode == 1, (
            f"preflight should fail when agent missing background: true.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
```

Also update `_setup_passing_tree` with these explicit modifications:

1. Add `(tree / "output" / ".checkpoints").mkdir(parents=True, exist_ok=True)` to create the checkpoint directory
2. Update the orchestration.md fixture content to include `checkpoint validate`, `checkpoint write`, and `checkpoint clear` strings (at minimum add to the existing Phase sections)
3. Create a sample agent file: `(tree / ".claude" / "agents").mkdir(parents=True, exist_ok=True)` then write `tree / ".claude" / "agents" / "test-agent.md"` with YAML frontmatter containing `background: true`

Example orchestration.md fixture addition (append to existing Phase content):
```python
# In _setup_passing_tree, update orchestration.md content to include:
orch_content = """\
## Phase 1 — Search
checkpoint clear
### Entry Criteria
...
### Exit Criteria
...
checkpoint write search

## Phase 2 — Verify
checkpoint validate search
...
checkpoint write verify

## Phase 3 — Dedup
checkpoint validate verify
...

## Phase 4 — Present
checkpoint validate dedup
...

## Phase 5 — Deliver
checkpoint validate present
...
"""
```

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_preflight.py -v`
- Lint: `cd 03_agents/tests/v22 && ruff check tests/test_preflight.py`

---

### Step 11: Simplify settings.local.json (read-then-merge)

**File:** `v22/.claude/settings.local.json`
**Action:** Modify using read-then-merge strategy (NOT full replacement — V18 regression: modifications must be additive, never overwrite)

The build step MUST:
1. Read the existing `settings.local.json` into a Python dict
2. Merge the new `permissions.allow` entries into the existing list (union, no duplicates)
3. Write the merged result back

New entries to merge into existing `permissions.allow`:
```json
[
  "Bash(bash scripts/*)",
  "Bash(python3:*)",
  "Bash(echo:*)",
  "Bash(test:*)",
  "Bash(exit:*)",
  "Bash(ls:*)",
  "Bash(find:*)",
  "Bash(git add:*)",
  "Bash(git commit:*)",
  "Bash(git push:*)",
  "Bash(curl:*)",
  "Bash(vercel:*)",
  "Bash(gh workflow:*)",
  "Bash(gh run list:*)",
  "Bash(gh run view:*)",
  "Read",
  "Write",
  "Glob",
  "Grep",
  "WebFetch",
  "WebSearch",
  "mcp__plugin_compound-engineering_pw__browser_navigate",
  "mcp__plugin_compound-engineering_pw__browser_snapshot",
  "mcp__plugin_compound-engineering_pw__browser_click",
  "mcp__plugin_compound-engineering_pw__browser_close"
]
```

Scope change note: this deliberately replaces per-domain `WebFetch(domain:...)` entries with wildcard `WebFetch`. This is a scope expansion from V21 and is intentional for V22 simplification.

**Test:** Add to `v22/tests/test_workflow.py`:

```python
def test_settings_local_json_preserves_existing_entries() -> None:
    """settings.local.json merge must preserve pre-existing permission entries."""
    import json
    from pathlib import Path
    settings_path = Path(__file__).resolve().parent.parent / ".claude" / "settings.local.json"
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    allow = data.get("permissions", {}).get("allow", [])
    # Core entries that must exist
    assert "Read" in allow
    assert "Write" in allow
    assert "WebFetch" in allow
    # Verify it's a list (not accidentally overwritten to something else)
    assert isinstance(allow, list)
    assert len(allow) >= 10, f"Expected >= 10 permission entries, got {len(allow)}"
```

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_workflow.py::test_settings_local_json_preserves_existing_entries -v`
- Lint: `cd 03_agents/tests/v22 && python3 -c "import json; json.load(open('.claude/settings.local.json'))"`

**Layer 2 commit:**
```bash
cd 03_agents/tests/v22 && pytest tests/ -v && \
git add references/orchestration.md .claude/agents/ CLAUDE.md scripts/preflight.sh .claude/settings.local.json tests/ && \
git commit -m "feat(jsa): add checkpoint gates, background:true, remove foreground-fallback"
```

---

### Step 12: Add regression-prevention tests for CLAUDE.md and orchestration.md

**File:** `v22/tests/test_claude_md.py`
**Action:** Modify — append after existing tests

```python
def test_startup_references_agent_memory() -> None:
    """CLAUDE.md ON STARTUP must reference reading agent-memory files.

    HC4 regression — V14/V17/V19 recurrence."""
    content = _read_claude_md()
    assert "agent-memory" in content.lower() or "agent_memory" in content.lower(), (
        "CLAUDE.md ON STARTUP must reference reading .claude/agent-memory/*/MEMORY.md"
    )


def test_claude_md_line_count() -> None:
    """CLAUDE.md must be <= 300 lines (V20 regression, Agent Decomposition Pattern)."""
    from pathlib import Path
    claude_md = Path(__file__).resolve().parent.parent / "CLAUDE.md"
    lines = claude_md.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 300, (
        f"CLAUDE.md is {len(lines)} lines, must be <= 300 (Agent Decomposition Pattern)"
    )
```

**File:** `v22/tests/test_workflow.py`
**Action:** Modify — append

```python
def test_no_model_parameter_in_dispatch_templates() -> None:
    """No Task dispatch in orchestration.md passes a model: parameter.

    V19 HC1 regression: model parameter causes dispatch failures.
    Scoped to orchestration.md only to avoid false positives from agent YAML frontmatter."""
    from pathlib import Path
    import re
    base = Path(__file__).resolve().parent.parent

    orch_path = base / "references" / "orchestration.md"
    if not orch_path.exists():
        return
    content = orch_path.read_text(encoding="utf-8")
    # Look for dispatch-block patterns that include model: parameter
    # Match lines containing dispatch keywords followed by model: on the same or next line
    for line_num, line in enumerate(content.splitlines(), 1):
        if re.search(r"^\s*(Task|dispatch|subagent)\b", line, re.IGNORECASE):
            # Check this line and next few lines for model: parameter
            block = "\n".join(content.splitlines()[line_num - 1:line_num + 4])
            model_match = re.search(r"\bmodel\s*:", block)
            assert model_match is None, (
                f"orchestration.md line ~{line_num} dispatch contains model: parameter "
                f"(V19 HC1 regression)"
            )


def test_dispatch_templates_include_working_directory() -> None:
    """Dispatch templates in orchestration.md must include absolute working directory.

    V19 regression: subagent dispatch prompts must include explicit absolute working directory."""
    from pathlib import Path
    orch_path = Path(__file__).resolve().parent.parent / "references" / "orchestration.md"
    content = orch_path.read_text(encoding="utf-8")
    # Check that dispatch sections reference working directory
    assert "working" in content.lower() and "directory" in content.lower(), (
        "orchestration.md dispatch templates must include absolute working directory variable"
    )


def test_clear_only_runs_in_phase1_context() -> None:
    """Verify orchestration.md only invokes checkpoint clear within Phase 1.

    Moved from test_manage_state.py — tests markdown layout, not Python logic."""
    from pathlib import Path
    import re
    orch_path = Path(__file__).resolve().parent.parent / "references" / "orchestration.md"
    content = orch_path.read_text(encoding="utf-8")
    # Find all occurrences of "checkpoint clear"
    clear_positions = [m.start() for m in re.finditer(r"checkpoint clear", content)]
    assert len(clear_positions) >= 1, "orchestration.md must contain at least one 'checkpoint clear'"
    # Each occurrence must be within Phase 1 section
    phase1_start = content.find("## Phase 1")
    phase2_start = content.find("## Phase 2")
    assert phase1_start != -1 and phase2_start != -1
    for pos in clear_positions:
        assert phase1_start <= pos < phase2_start, (
            "checkpoint clear must only appear within Phase 1 section"
        )


def test_phase1_cleanup_cross_references_state_json() -> None:
    """Phase 1 pre-run cleanup must cross-reference state.json before deleting files.

    V20/V21 regression: verified files must not be deleted without checking state.json."""
    from pathlib import Path
    orch_path = Path(__file__).resolve().parent.parent / "references" / "orchestration.md"
    content = orch_path.read_text(encoding="utf-8")
    phase1_start = content.find("## Phase 1")
    phase2_start = content.find("## Phase 2")
    assert phase1_start != -1 and phase2_start != -1
    phase1_text = content[phase1_start:phase2_start]
    assert "state.json" in phase1_text, (
        "Phase 1 must reference state.json for cross-referencing before file deletion"
    )


def test_phase5_uses_body_file_for_email() -> None:
    """Phase 5 must use --body-file when referencing send_email.py.

    V21 regression: send_email.py uses --body-file not --html."""
    from pathlib import Path
    orch_path = Path(__file__).resolve().parent.parent / "references" / "orchestration.md"
    content = orch_path.read_text(encoding="utf-8")
    phase5_start = content.find("## Phase 5")
    assert phase5_start != -1
    phase5_text = content[phase5_start:]
    # Only check if send_email.py is referenced in Phase 5
    if "send_email" in phase5_text:
        assert "--body-file" in phase5_text, (
            "Phase 5 must use --body-file (not --html) when referencing send_email.py (V21 regression)"
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_claude_md.py::test_startup_references_agent_memory tests/test_claude_md.py::test_claude_md_line_count tests/test_workflow.py::test_no_model_parameter_in_dispatch_templates tests/test_workflow.py::test_dispatch_templates_include_working_directory tests/test_workflow.py::test_clear_only_runs_in_phase1_context tests/test_workflow.py::test_phase1_cleanup_cross_references_state_json tests/test_workflow.py::test_phase5_uses_body_file_for_email -v`
- Lint: `cd 03_agents/tests/v22 && ruff check tests/test_claude_md.py tests/test_workflow.py`

---

### Step 13: Add search-verify subagent budget enforcement

**File:** `v22/references/orchestration.md`
**Action:** Modify — add budget enforcement instruction in Phase 1 and Phase 2 dispatch sections

Insert after the BATCH-LEVEL COMMIT section in Phase 1:

```markdown
### SUBAGENT BUDGET

Search-verify subagents MUST operate within a hard budget:
- **Time budget:** 15 minutes per source batch
- **Tool-use budget:** 50 tool calls per source batch
- On budget exhaustion: write checkpoint with current count and return. Do NOT continue searching.
```

**File:** `v22/.claude/agents/search-verify.md`
**Action:** Modify — add budget frontmatter or instruction

Add to the agent body (after frontmatter):

```markdown
## Budget Enforcement

You have a hard budget per dispatch:
- Maximum 15 minutes wall-clock time
- Maximum 50 tool calls
- On budget exhaustion: checkpoint current results and return immediately
```

**Verify:**
- Manual: confirm orchestration.md contains "SUBAGENT BUDGET" section
- Manual: confirm search-verify.md contains budget enforcement

---

### Step 14: Add Vercel link prerequisite step

**File:** `v22/references/orchestration.md`
**Action:** Modify — add prerequisite step for version transition

Insert at the top of orchestration.md, before Phase 1:

```markdown
## Prerequisites (Version Transition)

When transitioning from a previous version (e.g., v21 to v22), run the following BEFORE the first pipeline execution:

```bash
cd 03_agents/tests/v22
vercel link --project jsa-dashboard --yes && vercel --prod --yes
```

This ensures the Vercel dashboard is linked to the new version directory.
```

**Verify:**
- Manual: confirm orchestration.md contains "Prerequisites" section with vercel link

---

### Layer 3: Scheduling & Deployment

---

### Step 15: Write failing tests for workflow file

**File:** `v22/tests/test_workflow.py`
**Action:** Modify — append workflow test classes

```python
import yaml
from pathlib import Path


def _repo_root() -> Path:
    """Return the repository root (4 levels up from v22/tests/)."""
    return Path(__file__).resolve().parents[4]


def _load_workflow() -> dict:
    """Load and parse the daily-digest workflow YAML."""
    wf_path = _repo_root() / ".github" / "workflows" / "daily-digest.yml"
    assert wf_path.exists(), f"Workflow file not found: {wf_path}"
    return yaml.safe_load(wf_path.read_text())


def _workflow_text() -> str:
    """Return raw text of the daily-digest workflow."""
    wf_path = _repo_root() / ".github" / "workflows" / "daily-digest.yml"
    return wf_path.read_text()


class TestGitHubWorkflowUsesClaude:
    """Verify workflow uses claude-code-base-action, not claude --print."""

    def test_uses_claude_code_base_action(self):
        text = _workflow_text()
        assert "anthropics/claude-code-base-action" in text, (
            "Workflow must use anthropics/claude-code-base-action"
        )

    def test_does_not_use_claude_print(self):
        text = _workflow_text()
        # Only check non-comment lines
        active_lines = [l for l in text.splitlines() if not l.strip().startswith("#")]
        active_text = "\n".join(active_lines)
        assert "claude --print" not in active_text, (
            "Workflow must not contain active 'claude --print' (migrated to claude-code-base-action)"
        )

    def test_references_v22(self):
        text = _workflow_text()
        assert "v22" in text, "Workflow must reference v22 working directory"
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for old in ("v20", "v21"):
                if f"tests/{old}" in stripped:
                    pytest.fail(
                        f"Active (non-comment) line references old version {old}: {stripped}"
                    )

    def test_has_workflow_dispatch_trigger(self):
        text = _workflow_text()
        assert "workflow_dispatch" in text, (
            "Workflow must have workflow_dispatch trigger for manual testing"
        )


class TestWorkflowVercelDeployStep:
    """Verify workflow contains a Vercel deploy step."""

    def test_has_vercel_prod_deploy(self):
        text = _workflow_text()
        assert "vercel --prod" in text, (
            "Workflow must contain a step with 'vercel --prod' for dashboard deployment"
        )

    def test_vercel_step_uses_token_secret(self):
        text = _workflow_text()
        assert "VERCEL_TOKEN" in text, (
            "Workflow Vercel deploy step must reference VERCEL_TOKEN secret"
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_workflow.py::TestGitHubWorkflowUsesClaude tests/test_workflow.py::TestWorkflowVercelDeployStep -v` (expect FAIL)
- Lint: `cd 03_agents/tests/v22 && ruff check tests/test_workflow.py`

---

### Step 16: Migrate daily-digest.yml to claude-code-base-action

**File:** `.github/workflows/daily-digest.yml` (repo root)
**Action:** Replace entire file

```yaml
name: Daily Job Search Digest

on:
  schedule:
    - cron: '0 6 * * 1-5'  # 06:00 UTC = 7am BST. During GMT (winter) this runs at 6am local.
  workflow_dispatch: {}

concurrency:
  group: jsa-daily-digest
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  daily-digest:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    defaults:
      run:
        working-directory: 03_agents/tests/v22
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Python dependencies
        run: |
          pip install python-jobspy resend playwright
          python -m playwright install chromium

      - name: Preflight checks
        run: bash scripts/preflight.sh --env
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Run scheduled digest
        id: claude-run
        uses: anthropics/claude-code-base-action@beta
        with:
          prompt: |
            Run scheduled daily digest. SCHEDULED_RUN=true.
            Working directory: 03_agents/tests/v22/
            Execute the full scheduled pipeline: startup -> Search -> Verify -> Dedup -> Present -> Deliver -> final checkpoint.
          model: "claude-opus-4-6"
          max_turns: "50"
          allowed_tools: "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch"
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          claude_env: |
            RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
            SCHEDULED_RUN: true

      # Note: claude-code-base-action may create commits during its run.
      # The "Commit state" step handles any remaining uncommitted changes.
      # Expected git state after Claude action: working tree may have uncommitted
      # changes to state.json, output/, and session-state.md.
      # Note: claude-code-base-action handles permissions via `allowed_tools` param;
      # settings.local.json is not needed in CI (permissions are action-level).

      - name: Commit state
        run: |
          git config user.name "Job Search Agent"
          git config user.email "agent@autonomous.bot"
          git add state.json output/session-state.md output/verified/ output/_delta.json
          STAGED=$(git diff --staged --name-only)
          if [ -z "$STAGED" ]; then
            echo "No changes to commit"
            exit 0
          fi
          git diff --staged --quiet || git commit -m "chore(jsa): daily digest $(date +%Y-%m-%d)"
          git push origin main

      - name: Deploy dashboard to Vercel
        # Note: claude-code-base-action@beta may not emit 'conclusion' output (undocumented beta schema).
        # Using GitHub-native 'outcome' as fallback. If 'outcome' is also unavailable, always() ensures
        # the step runs and 'success' check prevents deploy after failures.
        # Verify at build time: check action docs for supported outputs.
        if: always() && steps.claude-run.outcome == 'success'
        run: |
          npm install -g vercel
          vercel link --project jsa-dashboard --yes && vercel --prod --yes
        working-directory: 03_agents/tests/v22
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

**Verify:**
- Test: `cd 03_agents/tests/v22 && pytest tests/test_workflow.py::TestGitHubWorkflowUsesClaude tests/test_workflow.py::TestWorkflowVercelDeployStep -v` (expect PASS)
- Lint: `yamllint .github/workflows/daily-digest.yml` (if available)

---

### Step 17: Add workflow version check to preflight.sh

**File:** `v22/scripts/preflight.sh`
**Action:** Modify — insert in ENV tier

```bash
    # Repo-root workflow references current version directory
    REPO_ROOT_WF="$(git rev-parse --show-toplevel 2>/dev/null)/.github/workflows/daily-digest.yml"
    if [[ -f "$REPO_ROOT_WF" ]]; then
        CURRENT_VERSION="v22"
        if grep -v '^\s*#' "$REPO_ROOT_WF" | grep -qE 'tests/v[0-9]+' && \
           ! grep -v '^\s*#' "$REPO_ROOT_WF" | grep -q "tests/${CURRENT_VERSION}"; then
            warn "WARNING: .github/workflows/daily-digest.yml does not reference ${CURRENT_VERSION} — update working-directory"
        fi
    else
        warn "WARNING: .github/workflows/daily-digest.yml not found at repo root"
    fi
```

**Verify:**
- Test: `cd 03_agents/tests/v22 && bash scripts/preflight.sh --env`
- Lint: N/A

---

### Step 18: Manual workflow_dispatch test

This is a manual verification step, not a code change.

**Copy spec:**
After all code changes are committed and pushed:
1. Run: `gh workflow run daily-digest.yml`
2. Monitor: `gh run list --workflow daily-digest.yml --limit 1`
3. Wait for completion: `gh run watch <run-id>`
4. Expected: completes in < 60 minutes without timeout
5. If fails: check `gh run view <run-id> --log` and revert to commented-out `claude --print` fallback

**Verify:**
- Manual: `gh workflow run daily-digest.yml && sleep 10 && gh run list --workflow daily-digest.yml --limit 1`

**Layer 3 commit:**
```bash
cd 03_agents/tests/v22 && pytest tests/test_workflow.py -v && \
git add tests/test_workflow.py scripts/preflight.sh && \
cd ../../../.. && \
git add .github/workflows/daily-digest.yml && \
git commit -m "feat(jsa): migrate workflow to claude-code-base-action, add Vercel deploy"
```

---

## Deployment Verification

### Pre-Deploy Checks

Run from `03_agents/tests/v22/`:

```bash
# Lint all modified Python files
ruff check scripts/ tests/ && ruff format --check scripts/ tests/

# Run full test suite (must be 101+ tests, all pass)
pytest tests/ -v --tb=short

# Verify checkpoint directory structure
test -d output/.checkpoints && echo "OK: checkpoint dir exists"
test -f output/.checkpoints/.gitkeep && echo "OK: .gitkeep exists"

# Verify foreground-fallback removed
grep -q "foreground-fallback" CLAUDE.md && echo "FAIL" || echo "OK: foreground-fallback removed"

# Verify background: true in all agents
for f in .claude/agents/*.md; do grep -q "^background: true$" "$f" && echo "OK: $f" || echo "FAIL: $f"; done

# Verify orchestration.md has checkpoint wrappers
grep -q "checkpoint validate" references/orchestration.md && echo "OK: pre-gate found"
grep -q "checkpoint write" references/orchestration.md && echo "OK: post-checkpoint found"
grep -q "checkpoint clear" references/orchestration.md && echo "OK: Phase 1 clear found"

# Verify workflow migration
grep -q "anthropics/claude-code-base-action" ../../../../.github/workflows/daily-digest.yml && echo "OK: workflow migrated"
grep -q "vercel --prod" ../../../../.github/workflows/daily-digest.yml && echo "OK: Vercel deploy present"

# Run preflight
bash scripts/preflight.sh
```

### Post-Deploy Checks

```bash
# Trigger manual workflow dispatch
gh workflow run daily-digest.yml

# Wait and check status (run within 5 minutes of dispatch)
sleep 120 && gh run list --workflow daily-digest.yml --limit 1 --json status,conclusion

# Dashboard health check
curl -s https://jsa-dashboard.vercel.app/api/state | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'run_date: {d.get(\"run_date\", \"MISSING\")}')"

# Checkpoint status check (after successful run)
cd 03_agents/tests/v22 && python3 scripts/manage_state.py checkpoint status
```

### Rollback Plan

```bash
# 1. Revert workflow to previous version
git checkout HEAD~1 -- .github/workflows/daily-digest.yml
git commit -m "revert(jsa): rollback workflow to claude --print"
git push origin main

# 2. If V22 source changes caused regressions, revert the V22 commits
git log --oneline -5  # identify V22 commits
git revert <commit-range> --no-edit
git push origin main

# 3. Redeploy dashboard with V21
cd 03_agents/tests/v21 && vercel link --project jsa-dashboard --yes && vercel --prod --yes

# 4. Verify rollback
curl -s https://jsa-dashboard.vercel.app/api/state | python3 -c "import sys,json; print(json.load(sys.stdin))"
```

---

## Handoff Contract

- **Total steps:** 18 (5 Layer 1 + 9 Layer 2 [Steps 6-14] + 4 Layer 3 [Steps 15-18])
- **Total phases:** 3
- **Files created:** `output/.checkpoints/.gitkeep`, `output/.checkpoints/.gitignore`
- **Files modified:** `scripts/manage_state.py`, `tests/test_manage_state.py`, `tests/test_workflow.py`, `tests/test_claude_md.py`, `tests/test_preflight.py`, `references/orchestration.md`, `.claude/agents/*.md` (6 files), `.claude/agents/search-verify.md` (budget), `CLAUDE.md`, `scripts/preflight.sh`, `.claude/settings.local.json`, `.github/workflows/daily-digest.yml`
- **Verification sequence:**
  1. Layer 1: `pytest tests/test_manage_state.py -v` (12 new + 20 existing = 32 pass)
  2. Layer 2: `pytest tests/test_workflow.py tests/test_claude_md.py tests/test_preflight.py -v`
  3. Layer 3: `pytest tests/test_workflow.py -v` (workflow tests)
  4. Full suite: `pytest tests/ -v` (101+ tests pass)
  5. Preflight: `bash scripts/preflight.sh`
  6. Manual: `gh workflow run daily-digest.yml` (< 60 min)
- **Deployment verification:** Pre-deploy (lint + test + preflight), Post-deploy (workflow_dispatch + dashboard health), Rollback (git revert + V21 dashboard redeploy)

<!-- STAGE COMPLETE: /plan, 2026-02-23 -->
<!-- STAGE COMPLETE: /revise after round 1, 2026-02-23 -->
<!-- STAGE COMPLETE: /revise after round 2, 2026-02-23 -->
<!-- STAGE COMPLETE: /revise after round 3, 2026-02-23 -->

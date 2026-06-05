# Plan: JSA V18 — Infrastructure + Backend + Dashboard Polish

## Overview

Three-phase sequential build combining 8 V17 analysis fixes and 10 dashboard visual enhancements:
- **Phase 1: Infrastructure** — CLAUDE.md startup/UX rules, GH Actions workflow fixes, preflight validation (inline)
- **Phase 2: Backend/State** — manage_state.py dedup subcommand, CLAUDE.md Step 13 update, post-render regex fix
- **Phase 3: Dashboard Visual Polish** — CSS tokens, component JS, HTML structure, app.js logic

## Risk Decisions

1. **preflight.sh → inline bash commands**: No monolithic script. Individual checks in CLAUDE.md startup and GH Actions workflow. Simpler, testable individually.
2. **dedup collision key**: `{source_domain}:{company}:{title}` — prevents false positives across companies and avoids `"unknown"` domain collisions when `source_url` is missing.
3. **CSS regression testing**: Subagent-automated screenshot capture + `verify_html.py` check as final Phase 3 step (no manual inspection). Prohibited colors inlined in `verify_html.py` (single consumer — extract to shared config when second consumer exists).
4. **CLAUDE.md edit ordering**: Phase 1 edits startup sequence (top) + UX rules. Phase 2 edits Step 13 (mid-section). No overlap.

## Files to Modify

### Phase 1
- `03_agents/tests/v17/CLAUDE.md` — Add HC4 memory read to startup, add CR5 UX rule, add Step 22 scheduled run enforcement
- `03_agents/tests/v17/.github/workflows/daily-digest.yml` — Add settings.local.json creation, add post-deploy smoke test, add inline preflight checks. **Note:** Nested path is intentional — this is the V17 test harness structure. The workflow is copied to repo root `.github/workflows/` during deployment. **Verification:** The `/build` agent must confirm the copy step works by verifying the workflow file exists at repo root after deployment (e.g., `test -f .github/workflows/daily-digest.yml` in the post-deploy checks).

### Phase 2
- `03_agents/tests/v17/scripts/manage_state.py` — Add `dedup` subcommand
- `03_agents/tests/v17/CLAUDE.md` — Update Step 13 to use `manage_state.py dedup`
- `03_agents/tests/v17/scripts/verify_html.py` (new) — Simplified CSS-context-aware color check (<30 lines, prohibited colors inlined — extract to shared config when second consumer exists)

### Phase 3
- `03_agents/tests/v17/public/css/dashboard.css` — Score tier tokens, card hover, header/stats, section headings, sidebar, layout width, empty/loading states, detail view, micro-interactions, dark mode comments
- `03_agents/tests/v17/public/js/components.js` — Tier class application, stacked stats, count badges, score bars, tag variants, empty state CTA
- `03_agents/tests/v17/public/index.html` — Summary date element, summary divider, sidebar label
- `03_agents/tests/v17/public/js/app.js` — Date display logic, section dividers, enhanced empty states, loading spinner

## Implementation Steps

### Phase 1: Infrastructure Fixes

#### Step 1: Write test for CLAUDE.md startup sequence enforcement
**File:** `03_agents/tests/v17/tests/test_claude_md.py` (new)
**Action:** Create
**Description:** Unit test that reads CLAUDE.md and asserts: (1) startup sequence contains agent-memory read step with log output, (2) UX rules contain CR5 prohibition on directing user to technical work, (3) Step 22 contains scheduled run prompt. Also includes Step 13 dedup assertion (used by Phase 2 Step 9).

```python
"""Tests for CLAUDE.md structural assertions — startup, UX rules, and workflow steps.
One assertion per concern to avoid brittle substring coupling."""

from __future__ import annotations

from pathlib import Path

CLAUDE_MD = Path(__file__).resolve().parent.parent / "CLAUDE.md"


def _read_claude_md() -> str:
    return CLAUDE_MD.read_text(encoding="utf-8")


def _extract_section(content: str, heading: str) -> str:
    """Extract a ## section by heading name."""
    start = content.find(heading)
    assert start != -1, f"Section '{heading}' not found"
    next_section = content.find("\n## ", start + 1)
    return content[start:next_section] if next_section != -1 else content[start:]


def test_startup_reads_agent_memory() -> None:
    """ON STARTUP section must reference agent-memory MEMORY.md with log output."""
    section = _extract_section(_read_claude_md(), "## ON STARTUP")
    assert "agent-memory" in section and "MEMORY.md" in section


def test_ux_rules_prohibit_technical_work_for_user() -> None:
    """UX RULES must prohibit directing user to technical work, delegating to subagents."""
    section = _extract_section(_read_claude_md(), "## UX RULES")
    assert "technical work" in section.lower() and "subagent" in section.lower()


def test_step_22_scheduled_run_prompt() -> None:
    """Step 22 must offer proactive scheduled runs via GitHub Actions."""
    content = _read_claude_md()
    step22_start = content.find("**Step 22:")
    assert step22_start != -1
    step23_start = content.find("**Step 23:", step22_start + 1)
    step22 = content[step22_start:step23_start] if step23_start != -1 else content[step22_start:]
    assert "scheduled" in step22.lower() and "github actions" in step22.lower()


def test_step_13_references_dedup_subcommand() -> None:
    """Step 13 must reference dedup with company/title/score logic."""
    content = _read_claude_md()
    step13_start = content.find("**Step 13:")
    assert step13_start != -1
    step14_start = content.find("**Step 14:", step13_start + 1)
    step13 = content[step13_start:step14_start] if step14_start != -1 else content[step13_start:]
    assert "dedup" in step13.lower()
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_claude_md.py -v`
- Expected: all assertions fail (code under test not yet implemented).
- Lint: `ruff check 03_agents/tests/v17/tests/test_claude_md.py`

#### Step 2: Implement CLAUDE.md startup + UX changes
**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify
**Description:** Three edits to CLAUDE.md:

**Edit 1 — Startup step 2 (agent memory read):** Add log count directive.
Find the line:
```
2. **Read agent memory:** Read all `.claude/agent-memory/*/MEMORY.md` files. Carry documented failure patterns as active constraints for the session.
```
Replace with:
```
2. **Read agent memory:** Read all `.claude/agent-memory/*/MEMORY.md` files. Log count read: "Agent memory: read {N} MEMORY.md files." Carry documented failure patterns as active constraints for the session.
```

**Edit 2 — UX RULES section:** Add CR5 rule. Find the line:
```
- Never ask user to run commands, edit files, or do technical work.
```
Add after it:
```
- Never direct the user to perform technical work (hard refresh, check URLs, inspect dashboards, run commands). Delegate technical actions to subagents.
```

**Edit 3 — Step 22:** Enhance scheduled run offer. Find the line:
```
Then ask: "Would you like to set up a daily scheduled run? I can configure GitHub Actions to run this automatically on weekday mornings."
```
Replace with:
```
Then proactively offer to set up scheduled daily runs via GitHub Actions: "Would you like to set up a daily scheduled run? I can configure GitHub Actions to run this automatically on weekday mornings — you'll get a digest email every weekday without lifting a finger."

After first successful interactive session, proactively offer to set up scheduled daily runs via GitHub Actions.
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_claude_md.py -v`

#### Step 3: Commit Phase 1a — CLAUDE.md startup + UX
**Action:** `git add 03_agents/tests/v17/tests/test_claude_md.py 03_agents/tests/v17/CLAUDE.md && git commit -m "fix(jsa): add HC4 memory read, CR5 UX rule, Step 22 scheduled run prompt"`

#### Step 4: Write test for GH Actions workflow
**File:** `03_agents/tests/v17/tests/test_workflow.py` (new)
**Action:** Create
**Description:** Test that reads `.github/workflows/daily-digest.yml` and asserts: (1) contains step creating `settings.local.json`, (2) contains post-deploy smoke test step curling `/api/jobs`, (3) contains inline preflight checks.

```python
"""Tests for .github/workflows/daily-digest.yml structural assertions.
One assertion per concern to avoid brittle substring coupling."""

from __future__ import annotations
from pathlib import Path
import yaml

WORKFLOW_PATH = (
    Path(__file__).resolve().parent.parent / ".github" / "workflows" / "daily-digest.yml"
)

def _load_workflow() -> dict:
    assert WORKFLOW_PATH.exists()
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)

def _all_step_runs() -> str:
    return "\n".join(
        step["run"] for job in _load_workflow().get("jobs", {}).values()
        for step in job.get("steps", []) if "run" in step
    )

def test_creates_settings_local_json() -> None:
    """Workflow must create settings.local.json with permissions allow."""
    assert "settings.local.json" in _all_step_runs()

def test_smoke_test_curls_api_jobs() -> None:
    """Workflow must include post-deploy smoke test hitting /api/jobs."""
    assert "/api/jobs" in _all_step_runs()

def test_preflight_checks_env_vars() -> None:
    """Workflow must include preflight step checking required env vars."""
    runs = _all_step_runs()
    assert "ANTHROPIC_API_KEY" in runs or "RESEND_API_KEY" in runs
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_workflow.py -v`
- Expected: all assertions fail (code under test not yet implemented).
- Lint: `ruff check 03_agents/tests/v17/tests/test_workflow.py`

#### Step 5: Implement GH Actions workflow changes
**File:** `03_agents/tests/v17/.github/workflows/daily-digest.yml`
**Action:** Modify
**Description:** Add three new steps to the workflow. Read the existing workflow first to find the right insertion points.

**New step 1 — "Create settings.local.json":** Insert before the validation/run step:
```yaml
      - name: Create settings.local.json
        run: |
          mkdir -p .claude
          echo '{"permissions": {"allow": []}}' > .claude/settings.local.json
```

**New step 2 — "Preflight checks":** Insert after settings creation:
```yaml
      - name: Preflight checks
        run: |
          echo "Checking workflow file exists..."
          test -f .github/workflows/daily-digest.yml || { echo "FAIL: daily-digest.yml not found"; exit 1; }
          echo "Checking required env vars..."
          test -n "$ANTHROPIC_API_KEY" || { echo "FAIL: ANTHROPIC_API_KEY not set"; exit 1; }
          test -n "$RESEND_API_KEY" || { echo "FAIL: RESEND_API_KEY not set"; exit 1; }
          echo "All preflight checks passed."
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
```

**New step 3 — "Post-deploy smoke test":** Insert after the main run step:
```yaml
      - name: Post-deploy smoke test
        if: success()
        run: |
          echo "Running smoke test..."
          curl -sf "${VERCEL_URL:-https://jsa-dashboard.vercel.app}/api/jobs" || exit 1
          echo "Smoke test passed."
        env:
          VERCEL_URL: ${{ vars.VERCEL_URL }}
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_workflow.py -v`
- Lint: `python -c "import yaml; yaml.safe_load(open('03_agents/tests/v17/.github/workflows/daily-digest.yml'))"`

#### Step 6: Commit Phase 1b — GH Actions workflow
**Action:** `git add 03_agents/tests/v17/tests/test_workflow.py 03_agents/tests/v17/.github/workflows/daily-digest.yml && git commit -m "fix(jsa): add settings.local.json creation, smoke test, inline preflight to workflow"`

---

### Phase 2: Backend/State Fixes

#### Step 7: Write test for manage_state.py dedup subcommand
**File:** `03_agents/tests/v17/tests/test_manage_state_dedup.py` (new)
**Action:** Create
**Description:** Unit tests for dedup subcommand. Tests run the CLI subprocess and verify behavior.

```python
"""Tests for manage_state.py dedup subcommand."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _write_verified_job(dir_path: Path, role: str, filename: str, data: dict) -> Path:
    """Write a verified job JSON into a role subdirectory."""
    role_dir = dir_path / role
    role_dir.mkdir(parents=True, exist_ok=True)
    filepath = role_dir / filename
    filepath.write_text(json.dumps(data), encoding="utf-8")
    return filepath


def _run_dedup(verified_dir: str) -> dict:
    """Run dedup subcommand and return parsed JSON output."""
    result = subprocess.run(
        ["python3", str(MANAGE_STATE), "dedup", "--verified-dir", verified_dir],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"dedup failed: {result.stderr}"
    return json.loads(result.stdout)


class TestDedupNoDuplicates:
    def test_all_unique_jobs_pass_through(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 85,
                "source_url": "https://example.com/acme-engineer"
            })
            _write_verified_job(Path(tmpdir), "crypto", "beta-analyst.json", {
                "company": "Beta", "title": "Analyst", "score": 90,
                "source_url": "https://other.com/beta-analyst"
            })
            result = _run_dedup(tmpdir)
            assert result["total_input"] == 2
            assert result["total_output"] == 2
            assert len(result["removed"]) == 0

    def test_status_files_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 85,
                "source_url": "https://example.com/acme-engineer"
            })
            _write_verified_job(Path(tmpdir), "ai-ml", "_status.json", {
                "status": "complete"
            })
            result = _run_dedup(tmpdir)
            assert result["total_input"] == 1


class TestDedupCrossRoleType:
    def test_higher_score_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 85,
                "source_url": "https://example.com/acme-engineer"
            })
            _write_verified_job(Path(tmpdir), "crypto", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 92,
                "source_url": "https://example.com/acme-engineer"
            })
            result = _run_dedup(tmpdir)
            assert result["total_output"] == 1
            assert len(result["kept"]) == 1
            assert result["kept"][0]["score"] == 92

    def test_different_sources_not_deduped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 85,
                "source_url": "https://example.com/acme-engineer"
            })
            _write_verified_job(Path(tmpdir), "crypto", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 92,
                "source_url": "https://other.com/acme-engineer"
            })
            result = _run_dedup(tmpdir)
            assert result["total_output"] == 2


class TestDedupCollisionKey:
    def test_collision_key_includes_source_domain(self) -> None:
        """Same filename from different sources should NOT collide."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 85,
                "source_url": "https://source-a.com/engineer"
            })
            _write_verified_job(Path(tmpdir), "crypto", "engineer.json", {
                "company": "Beta", "title": "Engineer", "score": 90,
                "source_url": "https://source-b.com/engineer"
            })
            result = _run_dedup(tmpdir)
            assert result["total_output"] == 2


class TestDedupJsonOutput:
    def test_output_has_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "job.json", {
                "company": "Co", "title": "Dev", "score": 80,
                "source_url": "https://example.com/job"
            })
            result = _run_dedup(tmpdir)
            assert "kept" in result
            assert "removed" in result
            assert "total_input" in result
            assert "total_output" in result


def _run_dedup_dry_run(verified_dir: str) -> dict:
    """Run dedup subcommand with --dry-run and return parsed JSON output."""
    result = subprocess.run(
        ["python3", str(MANAGE_STATE), "dedup", "--verified-dir", verified_dir, "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"dedup --dry-run failed: {result.stderr}"
    return json.loads(result.stdout)


class TestDedupDryRun:
    def test_dry_run_reports_duplicates_without_deleting(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 85,
                "source_url": "https://example.com/acme-engineer"
            })
            _write_verified_job(Path(tmpdir), "crypto", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 92,
                "source_url": "https://example.com/acme-engineer"
            })
            result = _run_dedup_dry_run(tmpdir)
            assert result["total_output"] == 1
            assert len(result["removed"]) == 1
            # File should still exist (not deleted in dry-run)
            remaining = list(Path(tmpdir).rglob("*.json"))
            assert len(remaining) == 2, "dry-run must not delete files"


class TestApplyDedupDeletesFiles:
    def test_non_dry_run_deletes_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 85,
                "source_url": "https://example.com/acme-engineer"
            })
            _write_verified_job(Path(tmpdir), "crypto", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 92,
                "source_url": "https://example.com/acme-engineer"
            })
            result = _run_dedup(tmpdir)
            assert result["total_output"] == 1
            # File should be deleted (non-dry-run)
            remaining = list(Path(tmpdir).rglob("*.json"))
            assert len(remaining) == 1, "non-dry-run must delete duplicate files"
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_manage_state_dedup.py -v`
- Expected: all assertions fail (code under test not yet implemented).
- Lint: `ruff check 03_agents/tests/v17/tests/test_manage_state_dedup.py`

#### Step 8: Implement dedup subcommand
**File:** `03_agents/tests/v17/scripts/manage_state.py`
**Action:** Modify
**Description:** Read the existing manage_state.py to understand its argparse structure. Add four things:

1. `import sys` at the top (if not already present)

2. New function `_compute_dedup(verified_dir: str) -> dict` (pure query — no disk mutations):
```python
def _compute_dedup(verified_dir: str) -> dict:
    """Cross-role deduplication (compute only, no disk changes).
    Collision key: {source_domain}:{company}:{title}.
    Returns dict with 'kept' and 'removed' job lists (clean, no internal keys)
    plus 'removed_paths' as a separate list for _apply_dedup."""
    from urllib.parse import urlparse
    verified = Path(verified_dir)
    jobs = []
    path_map: dict[int, str] = {}  # id(job) -> path
    for role_dir in sorted(verified.iterdir()):
        if not role_dir.is_dir():
            continue
        for f in sorted(role_dir.glob("*.json")):
            if f.name.startswith("_"):
                continue
            data = json.loads(f.read_text(encoding="utf-8"))
            path_map[id(data)] = str(f)
            jobs.append(data)

    collision_map: dict[str, list[dict]] = {}
    for job in jobs:
        source_url = job.get("source_url", "")
        domain = urlparse(source_url).netloc if source_url else "unknown"
        company = job.get("company", "unknown").lower().strip()
        title = job.get("title", "unknown").lower().strip()
        key = f"{domain}:{company}:{title}"
        collision_map.setdefault(key, []).append(job)

    kept, removed, removed_paths = [], [], []
    for key, group in collision_map.items():
        group.sort(key=lambda j: (-j.get("score", 0), path_map.get(id(j), "")))
        kept.append(group[0])
        for dup in group[1:]:
            removed.append(dup)
            removed_paths.append(path_map[id(dup)])

    return {
        "kept": kept,
        "removed": removed,
        "removed_paths": removed_paths,
        "total_input": len(jobs),
        "total_output": len(kept),
    }
```

3. New function `_apply_dedup(removed_paths: list[str]) -> None` (performs deletions):
```python
def _apply_dedup(removed_paths: list[str]) -> None:
    """Delete duplicate files. Takes a plain path list from _compute_dedup['removed_paths']."""
    for path in removed_paths:
        Path(path).unlink(missing_ok=True)
```

4. Add `dedup` subparser to `main()` and handler with `--dry-run` flag:
```python
# In the argparse setup:
dedup_parser = subparsers.add_parser("dedup", help="Cross-role deduplication")
dedup_parser.add_argument("--verified-dir", required=True)
dedup_parser.add_argument("--dry-run", action="store_true", help="Report duplicates without deleting")

# In the dispatch:
if args.command == "dedup":
    result = _compute_dedup(args.verified_dir)
    if not args.dry_run:
        _apply_dedup(result["removed_paths"])
    # Remove internal paths list from output (not needed by consumers)
    result.pop("removed_paths", None)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_manage_state_dedup.py -v`
- Lint: `ruff check 03_agents/tests/v17/scripts/manage_state.py`

#### Step 9: Update CLAUDE.md Step 13 to reference dedup subcommand
**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify
**Description:** Replace any inline Python dedup logic in Step 13 with: `python scripts/manage_state.py dedup --verified-dir output/verified`. Add note: "Never write inline python3 -c for dedup — use this CLI subcommand only."

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_claude_md.py -v` (add assertion for Step 13 dedup reference)

#### Step 10: Commit Phase 2a — dedup subcommand + CLAUDE.md
**Action:** `git add 03_agents/tests/v17/tests/test_manage_state_dedup.py 03_agents/tests/v17/scripts/manage_state.py 03_agents/tests/v17/CLAUDE.md && git commit -m "feat(jsa): add manage_state.py dedup subcommand, update Step 13"`

#### Step 11: Write test for CSS-context-aware color regex
**File:** `03_agents/tests/v17/tests/test_verify_html.py` (new)
**Action:** Create
**Description:** Tests for verify_html.py covering CSS-context-only detection.

```python
"""Tests for verify_html.py CSS-context-aware color detection."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

VERIFY_HTML = Path(__file__).resolve().parent.parent / "scripts" / "verify_html.py"


def _check_html(html_content: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html_content)
        f.flush()
        return subprocess.run(
            ["python3", str(VERIFY_HTML), f.name],
            capture_output=True,
            text=True,
        )


class TestDetectsInlineStyleColors:
    def test_flags_red_hex_in_style_attr(self) -> None:
        result = _check_html('<div style="color: #ff0000">text</div>')
        assert result.returncode == 1

    def test_flags_blue_hex_in_style_attr(self) -> None:
        result = _check_html('<div style="color: #2563eb">text</div>')
        assert result.returncode == 1

    def test_flags_named_red_in_style_attr(self) -> None:
        result = _check_html('<div style="color: red">text</div>')
        assert result.returncode == 1

    def test_flags_named_blue_in_style_attr(self) -> None:
        result = _check_html('<div style="background-color: blue">text</div>')
        assert result.returncode == 1


class TestDetectsStyleBlockColors:
    def test_flags_red_in_style_block(self) -> None:
        result = _check_html("<style>.foo { color: #ff0000; }</style>")
        assert result.returncode == 1

    def test_flags_amber_in_style_block(self) -> None:
        result = _check_html("<style>.foo { color: #f59e0b; }</style>")
        assert result.returncode == 1

    def test_flags_orange_in_style_block(self) -> None:
        result = _check_html("<style>.foo { color: orange; }</style>")
        assert result.returncode == 1


class TestDoesNotFlagPlainText:
    def test_preferred_in_text(self) -> None:
        result = _check_html("<p>This is a preferred candidate</p>")
        assert result.returncode == 0

    def test_credible_in_text(self) -> None:
        result = _check_html("<p>A credible source of information</p>")
        assert result.returncode == 0

    def test_prepared_in_text(self) -> None:
        result = _check_html("<p>Well prepared for the interview</p>")
        assert result.returncode == 0

    def test_red_in_text_content(self) -> None:
        result = _check_html("<p>The red team exercise was successful</p>")
        assert result.returncode == 0


class TestDoesNotFlagCSSClassNames:
    def test_class_with_red_substring(self) -> None:
        result = _check_html('<div class="bg-red-500">text</div>')
        assert result.returncode == 0

    def test_class_with_blue_substring(self) -> None:
        result = _check_html('<div class="text-blue-600">text</div>')
        assert result.returncode == 0


class TestCleanHTMLPasses:
    def test_clean_html_returns_zero(self) -> None:
        result = _check_html("""
        <html><head><style>
        .job-card { border: 1px solid #e5e0db; color: #1a1613; }
        </style></head><body>
        <div class="job-card" style="border-left: 4px solid #22c55e">
            <p>A preferred candidate who is well prepared</p>
        </div></body></html>
        """)
        assert result.returncode == 0

    def test_warm_palette_colors_allowed(self) -> None:
        result = _check_html('<div style="color: #1a1613; background: #faf8f5">ok</div>')
        assert result.returncode == 0
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_verify_html.py -v`
- Expected: all assertions fail (code under test not yet implemented).
- Lint: `ruff check 03_agents/tests/v17/tests/test_verify_html.py`

#### Step 12: Implement verify_html.py with inline prohibited colors
**Files:** `03_agents/tests/v17/scripts/verify_html.py` (new)
**Action:** Create
**Description:** Create simplified `verify_html.py` (<30 lines) with prohibited colors inlined. No external `config/palette.json` — premature extraction with only one consumer. Extract to shared config when a second consumer exists.

**File: `scripts/verify_html.py`**

```python
#!/usr/bin/env python3
"""Check HTML for prohibited colors in CSS contexts. Constants inlined (single consumer)."""
from __future__ import annotations
import re, sys
from pathlib import Path

PROHIBITED_NAMED = ["red", "blue", "orange", "amber"]
PROHIBITED_HEX = [
    "#0000ff", "#007bff", "#2563eb", "#3b82f6", "#1d4ed8", "#60a5fa", "#93c5fd",
    "#ff0000", "#dc2626", "#ef4444", "#b91c1c", "#f87171", "#fca5a5",
    "#f59e0b", "#d97706", "#fbbf24", "#92400e",
    "#f97316", "#ea580c", "#fb923c", "#c2410c",
]

def verify_html(filepath: str) -> list[str]:
    html = Path(filepath).read_text(encoding="utf-8")
    css_parts = [m.group(1) for m in re.finditer(r'style\s*=\s*["\']([^"\']*)["\']', html, re.I)]
    css_parts += [m.group(1) for m in re.finditer(r"<style[^>]*>(.*?)</style>", html, re.S | re.I)]
    css = "\n".join(css_parts).lower()
    violations = []
    for name in PROHIBITED_NAMED:
        if re.search(rf":\s*[^;]*\b{name}\b", css, re.I):
            violations.append(f"Prohibited named color: {name}")
    for hx in PROHIBITED_HEX:
        if hx.lower() in css:
            violations.append(f"Prohibited hex color: {hx}")
    return violations

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_html.py <html_file>", file=sys.stderr); sys.exit(2)
    vs = verify_html(sys.argv[1])
    if vs:
        for v in vs: print(v, file=sys.stderr)
        sys.exit(1)
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_verify_html.py -v`
- Lint: `ruff check 03_agents/tests/v17/scripts/verify_html.py`

#### Step 13: Commit Phase 2b — verify_html.py
**Action:** `git add 03_agents/tests/v17/tests/test_verify_html.py 03_agents/tests/v17/scripts/verify_html.py && git commit -m "feat(jsa): add CSS-context-aware color verification with inline palette"`

---

### Phase 3: Dashboard Visual Polish

**JS Ownership Contract:**
- `components.js` — Exports pure stateless render functions only (`getScoreTier`, `renderStat`, `renderCountBadge`, `renderEmptyState`, `renderJobCard`). No DOM queries, no event binding, no side effects. Returns HTML strings or modifies passed elements. Interactive elements use `data-action` attributes (e.g., `data-action="trigger-search"`) instead of inline `onclick` handlers.
- `app.js` — Owns DOM binding, orchestration, data fetching, event delegation, and state management. Calls component functions for rendering. Binds `data-action` attributes via event delegation (e.g., `document.addEventListener('click', ...)` checks `[data-action]`). Empty state rendering lives here (calls `renderEmptyState` from `components.js` but `app.js` is responsible for inserting it into the DOM and binding actions).

#### Step 14: Write complete dashboard frontend test file
**File:** `03_agents/tests/v17/tests/test_dashboard_frontend.py` (new)
**Action:** Create
**Description:** Consolidated frontend test file with class-per-file organization. All Phase 3 tests (CSS, components.js, index.html, app.js) are written upfront in this single file. Steps 15/17/19/21 implement CSS/JS/HTML and run these existing tests.

**Copy spec:**
- Score tier classes: `.tier-high` (90+, green left border 4px), `.tier-mid` (80-89, default 3px), `.tier-low` (70-79, muted 2px)
- No blue anywhere — warm stone/ink palette only
- No shadows on cards — borders only
- Empty state CTA: "Run Search" button text with `data-action="trigger-search"`
- Stacked stats format: `<span class="summary-stat-value">N</span><span class="summary-stat-label">LABEL</span>`
- Count badges format: `<span class="count-badge">N</span>`
- `<span id="summary-date">Last updated: {date}</span>`
- `<hr class="summary-divider">`
- `<span class="sidebar-label">Role Type</span>`
- Date format: "Last updated: Feb 16, 2026"
- Loading text: "Loading jobs..."
- Section divider: `<hr class="section-divider">`

```python
"""Consolidated dashboard frontend tests — one class per source file.
All tests written upfront; Steps 15/17/19/21 implement and run these."""

from __future__ import annotations

import re
from pathlib import Path

V17_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = V17_ROOT / "public" / "css" / "dashboard.css"
COMPONENTS_JS_PATH = V17_ROOT / "public" / "js" / "components.js"
INDEX_HTML_PATH = V17_ROOT / "public" / "index.html"
APP_JS_PATH = V17_ROOT / "public" / "js" / "app.js"


# --- CSS tests ---

def _read_css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


class TestScoreTierTokens:
    def test_tier_high_exists_with_green_border(self) -> None:
        css = _read_css()
        assert ".tier-high" in css
        # Find the tier-high rule block
        match = re.search(r"\.tier-high\s*\{([^}]+)\}", css)
        assert match, ".tier-high rule not found"
        rule = match.group(1)
        assert "4px" in rule
        assert "border-left" in rule or "border" in rule

    def test_tier_mid_exists(self) -> None:
        css = _read_css()
        assert ".tier-mid" in css
        match = re.search(r"\.tier-mid\s*\{([^}]+)\}", css)
        assert match
        assert "3px" in match.group(1)

    def test_tier_low_exists(self) -> None:
        css = _read_css()
        assert ".tier-low" in css
        match = re.search(r"\.tier-low\s*\{([^}]+)\}", css)
        assert match
        assert "2px" in match.group(1)


class TestNoBoxShadowOnCards:
    def test_job_card_has_no_box_shadow(self) -> None:
        css = _read_css()
        # Extract all .job-card rule blocks
        for match in re.finditer(r"\.job-card(?:\s*,\s*[^{]*|\s*)\{([^}]+)\}", css):
            rule = match.group(1)
            assert "box-shadow" not in rule, f"box-shadow found in .job-card: {rule[:100]}"


class TestNoBlueColorValues:
    def test_no_blue_hex_values(self) -> None:
        css = _read_css()
        blue_hexes = ["#0000ff", "#007bff", "#2563eb", "#3b82f6", "#1d4ed8", "#60a5fa"]
        for hex_val in blue_hexes:
            assert hex_val not in css.lower(), f"Blue hex {hex_val} found in CSS"

    def test_no_named_blue_as_value(self) -> None:
        css = _read_css()
        # Blue as a CSS property value (not in comments or class names)
        assert not re.search(r":\s*[^;]*\bblue\b", css, re.IGNORECASE), "Named 'blue' found as CSS value"


class TestLayoutConstraints:
    def test_max_width_960px(self) -> None:
        css = _read_css()
        assert "960px" in css

    def test_horizontal_padding_40px(self) -> None:
        css = _read_css()
        assert "40px" in css


class TestCommentedDarkMode:
    def test_dark_mode_section_commented(self) -> None:
        css = _read_css()
        assert "dark" in css.lower()
        # Should be inside a comment, not an active media query
        assert "prefers-color-scheme" in css
        # Verify it's commented out (inside /* */)
        dark_pos = css.lower().find("prefers-color-scheme: dark")
        assert dark_pos != -1
        # Find the nearest preceding /* before the dark mode reference
        comment_start = css.rfind("/*", 0, dark_pos)
        comment_end = css.find("*/", dark_pos)
        assert comment_start != -1 and comment_end != -1, "Dark mode should be inside a comment"


# --- components.js tests ---

def _read_components_js() -> str:
    return COMPONENTS_JS_PATH.read_text(encoding="utf-8")


class TestGetScoreTierFunction:
    """String-presence tests for getScoreTier. Behavioral validation is in
    tests/test_get_score_tier.js (Node.js unit test that executes the function)."""

    def test_function_exists(self) -> None:
        js = _read_components_js()
        assert "getScoreTier" in js or "get_score_tier" in js or "scoreTier" in js

    def test_maps_90_plus_to_high(self) -> None:
        js = _read_components_js()
        assert "tier-high" in js
        assert "90" in js

    def test_maps_80_to_mid(self) -> None:
        assert "tier-mid" in _read_components_js()

    def test_maps_below_80_to_low(self) -> None:
        assert "tier-low" in _read_components_js()


class TestStackedStatsRendering:
    def test_stat_value_class(self) -> None:
        assert "summary-stat-value" in _read_components_js()

    def test_stat_label_class(self) -> None:
        assert "summary-stat-label" in _read_components_js()


class TestCountBadges:
    def test_count_badge_class(self) -> None:
        assert "count-badge" in _read_components_js()


class TestEmptyStateCTA:
    def test_run_search_text(self) -> None:
        assert "Run Search" in _read_components_js()

    def test_empty_state_rendered_as_button(self) -> None:
        js = _read_components_js()
        assert "button" in js.lower() or "btn" in js

    def test_cta_uses_data_action_not_onclick(self) -> None:
        js = _read_components_js()
        assert 'data-action="trigger-search"' in js or "data-action" in js
        # Verify no inline onclick for triggerSearch
        assert 'onclick="triggerSearch()"' not in js


# --- index.html tests ---

def _read_index_html() -> str:
    return INDEX_HTML_PATH.read_text(encoding="utf-8")


class TestSummaryDateSpan:
    def test_summary_date_element_exists(self) -> None:
        html = _read_index_html()
        assert 'id="summary-date"' in html

    def test_summary_date_is_span(self) -> None:
        html = _read_index_html()
        assert "<span" in html and 'id="summary-date"' in html


class TestSummaryDivider:
    def test_summary_divider_exists(self) -> None:
        html = _read_index_html()
        assert 'class="summary-divider"' in html

    def test_summary_divider_is_hr(self) -> None:
        html = _read_index_html()
        assert "<hr" in html and "summary-divider" in html


class TestSidebarRoleLabels:
    def test_sidebar_label_class_exists(self) -> None:
        html = _read_index_html()
        assert 'class="sidebar-label"' in html

    def test_role_type_label_text(self) -> None:
        html = _read_index_html()
        assert "Role Type" in html


# --- app.js tests ---

def _read_app_js() -> str:
    return APP_JS_PATH.read_text(encoding="utf-8")


class TestDateDisplay:
    def test_references_summary_date(self) -> None:
        assert "summary-date" in _read_app_js()

    def test_has_date_formatting(self) -> None:
        js = _read_app_js()
        assert "toLocaleDateString" in js or "formatDate" in js or "Date" in js


class TestSectionDividers:
    def test_section_divider_class(self) -> None:
        assert "section-divider" in _read_app_js()

    def test_divider_is_hr(self) -> None:
        js = _read_app_js()
        assert "<hr" in js and "section-divider" in js


class TestEnhancedEmptyState:
    def test_no_jobs_found_message(self) -> None:
        assert "No jobs found" in _read_app_js()

    def test_run_search_cta(self) -> None:
        js = _read_app_js()
        assert "Run" in js and "search" in js.lower()


class TestLoadingSpinner:
    def test_loading_text(self) -> None:
        js = _read_app_js()
        assert "Loading" in js or "loading" in js

    def test_loading_class(self) -> None:
        js = _read_app_js()
        assert "loading" in js
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_dashboard_frontend.py -v`
- Expected: all assertions fail (code under test not yet implemented).
- Lint: `ruff check 03_agents/tests/v17/tests/test_dashboard_frontend.py`

#### Step 15: Implement dashboard.css changes
**File:** `03_agents/tests/v17/public/css/dashboard.css`
**Action:** Modify
**Description:** Read existing CSS, then add the following sections. Existing `--content-max-width` custom property changes from `800px` to `960px`. Content padding changes to `40px`.

**Add these CSS blocks at the end of the file (before the dark mode comment):**

```css
/* --- Score Tier Tokens --- */
.tier-high { border-left: 4px solid #22c55e; }
.tier-mid  { border-left: 3px solid var(--border-warm, #d6cfc7); }
.tier-low  { border-left: 2px solid var(--border-muted, #e5e0db); }

/* --- Score Bar --- */
.score-bar { display: flex; align-items: center; gap: 8px; }
.score-bar-fill { height: 4px; border-radius: 2px; transition: width 0.3s ease; }
.score-bar-fill.tier-high { background: #22c55e; border-left: none; }
.score-bar-fill.tier-mid  { background: var(--text-warm, #8a7e72); border-left: none; }
.score-bar-fill.tier-low  { background: var(--border-muted, #e5e0db); border-left: none; }

/* --- Card Hover (no shadow) --- */
.job-card { transition: border-color 0.15s ease, transform 0.15s ease; }
.job-card:hover { border-color: var(--text-warm, #8a7e72); transform: translateY(-1px); }

/* --- Stacked Summary Stats --- */
.summary-stat { display: flex; flex-direction: column; align-items: center; }
.summary-stat-value { font-size: 20px; font-weight: 600; line-height: 1.2; }
.summary-stat-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted, #8a7e72); }

/* --- Count Badges --- */
.count-badge {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 20px; height: 20px; padding: 0 6px;
    font-size: 11px; font-weight: 600; border-radius: 10px;
    background: var(--bg-warm, #f5f0eb); color: var(--text-warm, #8a7e72);
}

/* --- Sidebar Labels --- */
.sidebar-label {
    font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--text-muted, #8a7e72); margin-bottom: 4px;
}

/* --- Summary Divider --- */
.summary-divider {
    border: none; border-top: 1px solid var(--border-muted, #e5e0db);
    margin: 12px 0;
}
#summary-date { font-size: 12px; color: var(--text-muted, #8a7e72); }

/* --- Section Divider --- */
.section-divider {
    border: none; border-top: 1px solid var(--border-muted, #e5e0db);
    margin: 24px 0;
}

/* --- Loading Spinner --- */
.loading-spinner {
    display: inline-block; width: 20px; height: 20px;
    border: 2px solid var(--border-muted, #e5e0db);
    border-top-color: var(--text-primary, #1a1613);
    border-radius: 50%; animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* --- Empty State --- */
.empty-state { text-align: center; padding: 48px 24px; color: var(--text-muted, #8a7e72); }
.empty-state-cta {
    margin-top: 16px; padding: 8px 16px;
    border: 1px solid var(--border-warm, #d6cfc7); border-radius: 6px;
    background: transparent; color: var(--text-primary, #1a1613);
    cursor: pointer; transition: border-color 0.15s ease;
}
.empty-state-cta:hover { border-color: var(--text-warm, #8a7e72); }

/* --- Tag Variants --- */
.tag-skill { background: var(--bg-warm, #f5f0eb); }
.tag-gap { background: #fef3c7; color: #92400e; }
.tag-benefit { background: #ecfdf5; color: #065f46; }

/* --- Micro-interactions --- */
.btn, .count-badge, .tag-skill, .tag-gap, .tag-benefit {
    transition: transform 0.1s ease, opacity 0.1s ease;
}
.btn:active, .empty-state-cta:active { transform: scale(0.97); }

/* --- Responsive --- */
@media (max-width: 768px) {
    .summary-stat-value { font-size: 16px; }
    .summary-stat-label { font-size: 10px; }
}
```

**Also update the existing `--content-max-width` custom property:**
Find: `--content-max-width: 800px` (or similar)
Replace: `--content-max-width: 960px`

**Update content padding:**
Find the `.content` or main container padding and change to `padding: 0 40px`.

**Add commented dark mode at the very end:**
```css
/*
 * --- Dark Mode Token Mapping (future) ---
 * @media (prefers-color-scheme: dark) {
 *   :root {
 *     --bg-primary: #1a1613;
 *     --bg-warm: #2a2520;
 *     --text-primary: #faf8f5;
 *     --text-muted: #a09488;
 *     --border-muted: #3a352f;
 *     --border-warm: #4a443d;
 *   }
 * }
 */
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_dashboard_frontend.py -v`
- Lint: (CSS — no linter configured, skip)

#### Step 16: Implement components.js changes
**File:** `03_agents/tests/v17/public/js/components.js`
**Action:** Modify
**Description:** Read existing file, then add/modify the following. The build agent should find the appropriate insertion points.

**Add `getScoreTier` function** (at module level):
```javascript
function getScoreTier(score) {
  if (score >= 90) return 'tier-high';
  if (score >= 80) return 'tier-mid';
  return 'tier-low';
}
```

**Update `jobCard` function** — find where `.job-card` element is created and add tier class:
```javascript
// After creating the card element:
card.classList.add(getScoreTier(job.score));
```

**Update stats rendering** to use stacked format — find the stats/summary rendering function and change to:
```javascript
function renderStat(value, label) {
  return `<div class="summary-stat">
    <span class="summary-stat-value">${value}</span>
    <span class="summary-stat-label">${label}</span>
  </div>`;
}
```

**Add count badges to sidebar** — update sidebar count rendering:
```javascript
function renderCountBadge(count) {
  return `<span class="count-badge">${count}</span>`;
}
```

**Update empty state** — modify existing empty state function or add:
```javascript
function renderEmptyState(showCTA = true) {
  return `<div class="empty-state">
    <p>No jobs found. Run a search to get started.</p>
    ${showCTA ? '<button class="btn empty-state-cta" data-action="trigger-search">Run Search</button>' : ''}
  </div>`;
}
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_dashboard_frontend.py -v`

#### Step 17: Add Node.js behavioral unit test for getScoreTier
**File:** `03_agents/tests/v17/tests/test_get_score_tier.js` (new)
**Action:** Create
**Description:** Node.js unit test that `require()`s components.js and executes `getScoreTier` with real inputs, validating return values. This provides behavioral coverage that the Python string-presence tests cannot.

```javascript
// Behavioral unit test for getScoreTier — executes the function, not string matching.
// Run: node tests/test_get_score_tier.js

// Extract getScoreTier from components.js (module-level function)
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'public', 'js', 'components.js'), 'utf-8');
// Evaluate in isolated context to extract function
const vm = require('vm');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(src, ctx);

const assert = require('assert');
assert.strictEqual(ctx.getScoreTier(95), 'tier-high', '95 -> tier-high');
assert.strictEqual(ctx.getScoreTier(90), 'tier-high', '90 -> tier-high');
assert.strictEqual(ctx.getScoreTier(89), 'tier-mid', '89 -> tier-mid');
assert.strictEqual(ctx.getScoreTier(80), 'tier-mid', '80 -> tier-mid');
assert.strictEqual(ctx.getScoreTier(79), 'tier-low', '79 -> tier-low');
assert.strictEqual(ctx.getScoreTier(50), 'tier-low', '50 -> tier-low');
assert.strictEqual(ctx.getScoreTier(0), 'tier-low', '0 -> tier-low');
console.log('All getScoreTier tests passed.');
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && node tests/test_get_score_tier.js`
- Expected: passes after Step 16 implements `getScoreTier` in components.js

#### Step 18: Implement index.html changes
**File:** `03_agents/tests/v17/public/index.html`
**Action:** Modify
**Description:** Read existing index.html. Make three insertions:

**Insert 1 — Summary date and divider:** In the summary/header strip area, add after the title/heading:
```html
<hr class="summary-divider">
<span id="summary-date"></span>
```

**Insert 2 — Sidebar role label:** In the sidebar section, add before the role type filter list:
```html
<span class="sidebar-label">Pipeline</span>
```

**Insert 3 — Sidebar role type label:** Before the role type sidebar filter:
```html
<span class="sidebar-label">Role Type</span>
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_dashboard_frontend.py -v`

#### Step 19: Implement app.js changes
**File:** `03_agents/tests/v17/public/js/app.js`
**Action:** Modify
**Description:** Read existing file, then add/modify the following:

**Bind `data-action="trigger-search"` via event delegation** (at module level in `app.js` — owns event binding per ownership contract):
```javascript
// Event delegation for data-action attributes (components.js emits these, app.js binds them)
document.addEventListener('click', function(e) {
  const actionEl = e.target.closest('[data-action]');
  if (!actionEl) return;
  if (actionEl.dataset.action === 'trigger-search') {
    window.dispatchEvent(new CustomEvent('jsa:trigger-search'));
  }
});
```

**Add `formatDate` helper** (at module level):
```javascript
function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return 'Last updated: ' + d.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });
}
```

**Update `loadData` / data fetch function** — after receiving API response, populate date:
```javascript
const dateEl = document.getElementById('summary-date');
if (dateEl && data.last_run_date) {
  dateEl.textContent = formatDate(data.last_run_date);
}
```

**Update section rendering** — join role group sections with dividers:
```javascript
// Instead of sections.join('') use:
sections.join('<hr class="section-divider">');
```

**Update empty state rendering** — call `renderEmptyState()` from `components.js` (empty state HTML lives in components.js only per ownership contract):
```javascript
// When no jobs are found:
container.innerHTML = renderEmptyState(true);
```

**Add loading spinner** — show during API fetch:
```javascript
// Before fetch:
container.innerHTML = '<div class="loading-state"><span class="loading-spinner"></span> Loading jobs...</div>';
```

**Verify:**
- Test: `cd 03_agents/tests/v17 && python -m pytest tests/test_dashboard_frontend.py -v`

#### Step 20: Commit Phase 3 — Dashboard visual polish
**Action:** `git add 03_agents/tests/v17/tests/test_dashboard_frontend.py 03_agents/tests/v17/tests/test_get_score_tier.js 03_agents/tests/v17/public/css/dashboard.css 03_agents/tests/v17/public/js/components.js 03_agents/tests/v17/public/index.html 03_agents/tests/v17/public/js/app.js && git commit -m "feat(jsa): dashboard visual polish — tier tokens, stacked stats, layout, empty states"`

#### Step 21: Automated visual regression check
**Action:** Dispatch a subagent to open the dashboard at both 1280px and 768px widths and verify: no blue colors, no box-shadows on cards, 960px max-width, stacked stats render correctly. The subagent captures screenshots and reports pass/fail. No manual user action required.

**Verify:**
- Subagent opens `public/index.html` via local server, captures screenshots at 1280px and 768px
- Subagent runs `python scripts/verify_html.py public/index.html` to confirm no prohibited colors
- All checks automated — no manual browser inspection needed

---

## Deployment Verification

### Regression Verification Notes

- **Redis fallback (V17 regression):** API endpoints must fall back from Upstash Redis to `state.json` when Redis is unavailable. This is already implemented in V17 API handlers. Verify by confirming API returns data when `UPSTASH_REDIS_REST_URL` is unset.
- **Vercel deployment (V17 regression):** `vercel.json` must use `functions` + `rewrites` pattern (not legacy `routes`). API handlers must use Vercel-compatible exports (`export default function handler`). Auto-deploy from `main` must be active.
- **session-state.md (V14 regression):** `session-state.md` must be written after every search batch. Existing coverage in CLAUDE.md Step 16 handles this.
- **Digest email behavioral regressions (V14):** Hide zero-item sections and apply 70+ score threshold in digest email. These are enforced by existing CLAUDE.md workflow steps (Step 17 digest generation). No V18 changes affect this logic.

### Pre-Deploy Checks

Run from `03_agents/tests/v17/` before deploying:

```bash
# Full test suite
python -m pytest tests/ -v --tb=short

# Node.js behavioral test
node tests/test_get_score_tier.js

# Lint Python scripts
ruff check scripts/manage_state.py scripts/verify_html.py

# Validate workflow YAML
python -c "import yaml; yaml.safe_load(open('.github/workflows/daily-digest.yml'))"

# HTML color verification — dashboard and digest email
python scripts/verify_html.py public/index.html
# Also verify digest email HTML when generated (V14 regression: no blue hyperlinks in digest)
# python scripts/verify_html.py output/digest-email.html  (run post-generation)
```

All must pass (exit 0). Do not deploy if any check fails.

### Post-Deploy Checks

Run within 60 seconds of Vercel deployment:

```bash
# Health check
curl -sf "${VERCEL_URL}/api/jobs" && echo "API healthy"

# Dashboard loads
curl -sf "${VERCEL_URL}/" | grep -q 'class="dashboard"' && echo "Dashboard OK"

# No asset 404s — automated: curl key assets and verify 200 status
curl -sf "${VERCEL_URL}/css/dashboard.css" > /dev/null && echo "CSS OK"
curl -sf "${VERCEL_URL}/js/app.js" > /dev/null && echo "JS OK"
```

### Rollback Plan

```bash
# Revert all V18 commits
git revert --no-commit HEAD~5..HEAD
git commit -m "chore(jsa): rollback V18 changes"
git push origin main

# Wait for Vercel auto-deploy (~30-60s)
# Verify: curl -sf "${VERCEL_URL}/api/jobs"
```

## Handoff Contract

- Total steps: 21
- Total phases: 3
- Files created: `tests/test_claude_md.py`, `tests/test_workflow.py`, `tests/test_manage_state_dedup.py`, `tests/test_verify_html.py`, `scripts/verify_html.py`, `tests/test_dashboard_frontend.py`, `tests/test_get_score_tier.js`
- Files modified: `CLAUDE.md`, `.github/workflows/daily-digest.yml`, `scripts/manage_state.py`, `public/css/dashboard.css`, `public/js/components.js`, `public/index.html`, `public/js/app.js`
- Verification sequence: test_claude_md → test_workflow → test_manage_state_dedup → test_verify_html → test_dashboard_frontend + test_get_score_tier.js → visual regression
- Deployment verification: pre-deploy, post-deploy, rollback — all present

<!-- STAGE COMPLETE: /plan, 2026-02-16 -->
<!-- STAGE COMPLETE: /revise after round 1, 2026-02-16 -->
<!-- STAGE COMPLETE: /revise after round 2, 2026-02-16 -->

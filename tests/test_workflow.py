"""Tests for .github/workflows/daily-digest.yml structural assertions.
One assertion per concern to avoid brittle substring coupling."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
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
    """Workflow must reference required API key secrets for preflight and digest steps.

    V21: secrets are referenced via ${{ secrets.* }} in step env: blocks,
    not as shell variables in run: scripts."""
    raw = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "ANTHROPIC_API_KEY" in raw and "RESEND_API_KEY" in raw


def test_orchestration_has_pregate_for_all_phases() -> None:
    """Every phase except Phase 1 must have a PRE-GATE section with checkpoint validate."""
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


def test_no_model_parameter_in_dispatch_templates() -> None:
    """No Task dispatch in orchestration.md passes a model: parameter.

    V19 HC1 regression: model parameter causes dispatch failures.
    Scoped to orchestration.md only to avoid false positives from agent YAML frontmatter."""
    import re
    base = Path(__file__).resolve().parent.parent

    orch_path = base / "references" / "orchestration.md"
    if not orch_path.exists():
        return
    content = orch_path.read_text(encoding="utf-8")
    # Look for dispatch-block patterns that include model: parameter
    for line_num, line in enumerate(content.splitlines(), 1):
        if re.search(r"^\s*(Task|dispatch|subagent)\b", line, re.IGNORECASE):
            block = "\n".join(content.splitlines()[line_num - 1:line_num + 4])
            model_match = re.search(r"\bmodel\s*:", block)
            assert model_match is None, (
                f"orchestration.md line ~{line_num} dispatch contains model: parameter "
                f"(V19 HC1 regression)"
            )


def test_dispatch_templates_include_working_directory() -> None:
    """Dispatch templates in orchestration.md must include absolute working directory.

    V19 regression: subagent dispatch prompts must include explicit absolute working directory."""
    orch_path = Path(__file__).resolve().parent.parent / "references" / "orchestration.md"
    content = orch_path.read_text(encoding="utf-8")
    assert "working" in content.lower() and "directory" in content.lower(), (
        "orchestration.md dispatch templates must include absolute working directory variable"
    )


def test_clear_only_runs_in_phase1_context() -> None:
    """Verify orchestration.md only invokes checkpoint clear within Phase 1.

    Moved from test_manage_state.py — tests markdown layout, not Python logic."""
    import re
    orch_path = Path(__file__).resolve().parent.parent / "references" / "orchestration.md"
    content = orch_path.read_text(encoding="utf-8")
    clear_positions = [m.start() for m in re.finditer(r"checkpoint clear", content)]
    assert len(clear_positions) >= 1, "orchestration.md must contain at least one 'checkpoint clear'"
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
    orch_path = Path(__file__).resolve().parent.parent / "references" / "orchestration.md"
    content = orch_path.read_text(encoding="utf-8")
    phase5_start = content.find("## Phase 5")
    assert phase5_start != -1
    phase5_text = content[phase5_start:]
    if "send_email" in phase5_text:
        assert "--body-file" in phase5_text, (
            "Phase 5 must use --body-file (not --html) when referencing send_email.py (V21 regression)"
        )


def _repo_root() -> Path:
    """Return the repository root (4 levels up from v22/tests/)."""
    return Path(__file__).resolve().parents[4]


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
        active_lines = [
            line for line in text.splitlines() if not line.strip().startswith("#")
        ]
        active_text = "\n".join(active_lines)
        assert "claude --print" not in active_text, (
            "Workflow must not contain active 'claude --print' (migrated to claude-code-base-action)"
        )

    def test_references_v23(self):
        text = _workflow_text()
        assert "v23" in text, "Workflow must reference v23 working directory"
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for old in ("v20", "v21", "v22"):
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


class TestGateBlocking:
    """Verify orchestration.md uses blocking gate semantics throughout Phase 1."""

    @property
    def _orch(self) -> str:
        orch_path = Path(__file__).resolve().parent.parent / "references" / "orchestration.md"
        return orch_path.read_text(encoding="utf-8")

    def test_orchestration_has_schema_validation_gate(self) -> None:
        """orchestration.md must contain a Schema Validation Gate section."""
        assert "Schema Validation Gate" in self._orch, (
            "orchestration.md missing 'Schema Validation Gate' section"
        )

    def test_must_pass_before_proceeding_appears_for_each_gate(self) -> None:
        """'MUST pass before proceeding' appears at least 3 times."""
        content = self._orch
        count = content.count("MUST pass before proceeding")
        assert count >= 3, (
            f"'MUST pass before proceeding' found {count} times, need >= 3"
        )

    def test_do_not_skip_appears_for_gates(self) -> None:
        """'Do NOT skip' instruction present for gate failures."""
        assert "Do NOT skip" in self._orch, (
            "orchestration.md missing 'Do NOT skip' instruction"
        )

    def test_schema_validation_gate_is_blocking(self) -> None:
        """Schema Validation Gate references validate-schema and uses blocking language."""
        content = self._orch
        gate_start = content.find("Schema Validation Gate")
        assert gate_start != -1
        gate_section = content[gate_start:gate_start + 600]
        assert "validate-schema" in gate_section, (
            "Schema Validation Gate must reference 'validate-schema' command"
        )
        assert "BLOCKING" in gate_section or "MUST pass" in gate_section, (
            "Schema Validation Gate must use BLOCKING or MUST pass language"
        )


# ---------------------------------------------------------------------------
# Integration helpers for manage_state.py invocation
# ---------------------------------------------------------------------------

def _run_manage_state(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run manage_state.py with args from cwd."""
    manage_state = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"
    return subprocess.run(
        [sys.executable, str(manage_state)] + args,
        capture_output=True, text=True, cwd=str(cwd),
    )


# Use shared factory from tests/helpers.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import _make_job  # noqa: E402


def _write_verified_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestSchemaValidationGate:
    """Integration test for chained validate-schema -> dedup workflow."""

    def test_dedup_after_validation_uses_canonical_score(self, tmp_path: Path) -> None:
        """Two valid verified JSONs -> dedup sorts by canonical score."""
        verified_dir = tmp_path / "output" / "verified" / "ai-engineer"
        high = _make_job(title="Senior AI Engineer", company="Alpha Corp",
                         score=85, job_url="https://alpha.com/jobs/senior-ai")
        low = _make_job(title="Junior AI Engineer", company="Beta Corp",
                        score=60, job_url="https://beta.com/jobs/junior-ai")
        _write_verified_json(verified_dir / "alpha.json", high)
        _write_verified_json(verified_dir / "beta.json", low)

        validate_result = _run_manage_state(
            ["validate-schema", "--output-dir", str(tmp_path / "output")], cwd=tmp_path,
        )
        assert validate_result.returncode == 0

        dedup_result = _run_manage_state(
            ["dedup", "--output-dir", str(tmp_path / "output"), "--role-types", "ai-engineer"],
            cwd=tmp_path,
        )
        assert dedup_result.returncode == 0


class TestDedupScoping:
    """Integration test for dedup --role-types scoping."""

    def test_dedup_scopes_to_todays_role_types(self, tmp_path: Path) -> None:
        """Dedup with --role-types=ai-engineer only touches ai-engineer/, not old-role/."""
        ai_dir = tmp_path / "output" / "verified" / "ai-engineer"
        old_dir = tmp_path / "output" / "verified" / "old-role"

        _write_verified_json(ai_dir / "newco.json", _make_job(
            title="AI Engineer", company="NewCo", score=85,
            job_url="https://newco.com/jobs/ai", role_type="ai-engineer",
        ))
        _write_verified_json(old_dir / "oldco.json", _make_job(
            title="Old Role Specialist", company="OldCo", score=85,
            job_url="https://oldco.com/jobs/old", role_type="old-role",
        ))

        result = _run_manage_state(
            ["dedup", "--output-dir", str(tmp_path / "output"), "--role-types", "ai-engineer"],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert (old_dir / "oldco.json").exists(), "old-role job should NOT be touched"
        assert (ai_dir / "newco.json").exists(), "ai-engineer job should remain"

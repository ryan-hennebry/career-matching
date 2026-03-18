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

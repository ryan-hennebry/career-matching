"""Tests for manage_state.py filter-presentation (hard-gate enforcement).

Mirrors the dedup test pattern. Covers:
  - hard_gate_pass == false is suppressed from the presentation set
  - missing hard_gate_pass is treated as a legacy pass (not suppressed)
  - the suppressed-job list file records job_id/company/title/reasons
  - a whole role type being emptied logs a safety WARNING (does NOT abort)
  - validate-schema accepts files with/without the optional field, and
    rejects a wrong-typed hard_gate_pass.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import _make_job, _write_job  # noqa: E402

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run_filter_presentation(
    output_dir: str,
    *,
    role_types: str,
    out: str | None = None,
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "filter-presentation",
        "--output-dir",
        output_dir,
        "--role-types",
        role_types,
    ]
    if out is not None:
        cmd.extend(["--out", out])
    return subprocess.run(cmd, capture_output=True, text=True)


def _run_validate_schema(output_dir: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(MANAGE_STATE),
            "validate-schema",
            "--output-dir",
            output_dir,
        ],
        capture_output=True,
        text=True,
    )


class TestFilterPresentation:
    def test_gated_job_is_suppressed(self, tmp_path: Path) -> None:
        """hard_gate_pass == false -> excluded from presented set, recorded as suppressed."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        passing = _make_job(
            job_id="acme-eng", company="Acme", title="Engineer",
            hard_gate_pass=True, hard_gate_reasons=[],
        )
        gated = _make_job(
            job_id="beta-revops", company="Beta", title="RevOps Manager",
            hard_gate_pass=False,
            hard_gate_reasons=['requires-named-revops-stack: "must have Clay + Gong"'],
        )
        _write_job(verified / "ai-engineer", "acme-eng.json", passing)
        _write_job(verified / "ai-engineer", "beta-revops.json", gated)

        result = _run_filter_presentation(str(output_dir), role_types="ai-engineer")
        assert result.returncode == 0, f"failed: {result.stderr}\n{result.stdout}"

        summary = json.loads(result.stdout)
        assert summary["presented"] == 1
        assert summary["suppressed"] == 1

        # Files are LEFT IN PLACE (flag, not archive)
        assert (verified / "ai-engineer" / "beta-revops.json").exists()

        # Suppressed-list file records the gated job
        hard_gated = json.loads((output_dir / "_hard_gated.json").read_text())
        assert len(hard_gated) == 1
        entry = hard_gated[0]
        assert entry["job_id"] == "beta-revops"
        assert entry["company"] == "Beta"
        assert entry["title"] == "RevOps Manager"
        assert entry["hard_gate_reasons"] == [
            'requires-named-revops-stack: "must have Clay + Gong"'
        ]

    def test_missing_field_is_legacy_pass(self, tmp_path: Path) -> None:
        """A verified job with NO hard_gate_pass field is presented (legacy pass)."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        legacy = _make_job(job_id="legacy-1", company="OldCo", title="Operator")
        assert "hard_gate_pass" not in legacy
        _write_job(verified / "ai-engineer", "legacy-1.json", legacy)

        result = _run_filter_presentation(str(output_dir), role_types="ai-engineer")
        assert result.returncode == 0

        summary = json.loads(result.stdout)
        assert summary["presented"] == 1
        assert summary["suppressed"] == 0

        hard_gated = json.loads((output_dir / "_hard_gated.json").read_text())
        assert hard_gated == []

    def test_emptied_role_type_logs_safety_warning(self, tmp_path: Path) -> None:
        """If every job in a role type is gated, log a WARNING but do NOT abort."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        for i in range(2):
            gated = _make_job(
                job_id=f"co{i}", company=f"Co{i}", title="Coder",
                hard_gate_pass=False,
                hard_gate_reasons=[f'requires-coding: "must write Python {i}"'],
            )
            _write_job(verified / "ai-engineer", f"co{i}.json", gated)

        result = _run_filter_presentation(str(output_dir), role_types="ai-engineer")
        # Safety: log, do NOT abort -> exit 0
        assert result.returncode == 0, f"should not abort: {result.stderr}"
        assert "WARNING" in result.stderr
        assert "ai-engineer" in result.stderr

        summary = json.loads(result.stdout)
        assert summary["presented"] == 0
        assert summary["suppressed"] == 2
        # Files still in place
        assert (verified / "ai-engineer" / "co0.json").exists()


class TestValidateSchemaHardGate:
    def test_schema_accepts_present_and_missing_field(self, tmp_path: Path) -> None:
        """validate-schema passes whether or not the optional field is present."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        with_field = _make_job(
            job_id="a", job_url="https://example.com/jobs/123456",
            hard_gate_pass=True, hard_gate_reasons=[],
        )
        without_field = _make_job(job_id="b", job_url="https://example.com/jobs/789012")
        _write_job(verified / "ai-engineer", "a.json", with_field)
        _write_job(verified / "ai-engineer", "b.json", without_field)

        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0, f"schema should pass: {result.stderr}\n{result.stdout}"

    def test_schema_rejects_wrong_typed_field(self, tmp_path: Path) -> None:
        """validate-schema fails when hard_gate_pass is present but not a bool."""
        output_dir = tmp_path / "output"
        verified = output_dir / "verified"

        bad = _make_job(
            job_id="c", job_url="https://example.com/jobs/345678",
            hard_gate_pass="false",  # string, not bool
        )
        _write_job(verified / "ai-engineer", "c.json", bad)

        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1, "wrong-typed hard_gate_pass should fail schema"
        assert "hard_gate_pass" in (result.stdout + result.stderr)

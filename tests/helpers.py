"""Shared test helpers for JSA V24 tests.

All test files import from here instead of defining their own factories.
Single source of truth for verified job JSON construction and script invocation.
"""

import json
import subprocess
import sys
from pathlib import Path

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _make_job(**overrides) -> dict:
    """Single factory for verified job JSON. All 10 canonical fields with defaults."""
    defaults = {
        "job_id": "job-001", "title": "Engineer", "company": "Acme",
        "job_url": "https://example.com/job", "role_type": "ai-engineer",
        "score": 85, "source_channel": "direct-career-pages",
        "run_date": "2026-02-25", "location": "Remote", "status": "verified",
    }
    defaults.update(overrides)
    return defaults


def _write_job(dir_path: Path, filename: str, job_dict: dict) -> Path:
    """Write a job dict as JSON to a file in the given directory."""
    dir_path.mkdir(parents=True, exist_ok=True)
    filepath = dir_path / filename
    filepath.write_text(json.dumps(job_dict, indent=2), encoding="utf-8")
    return filepath


def _run_dedup(
    output_dir: str,
    *,
    role_types: str | None = None,
    auto_scope: bool = False,
    run_date: str | None = None,
    dry_run: bool = False,
    no_safety_bound: bool = False,
) -> subprocess.CompletedProcess:
    """Unified dedup helper supporting explicit role-types, auto-scope, and dry-run."""
    cmd = [
        sys.executable,
        str(MANAGE_STATE),
        "dedup",
        "--output-dir",
        output_dir,
    ]
    if role_types is not None:
        cmd.extend(["--role-types", role_types])
    if auto_scope:
        cmd.append("--auto-scope")
    if run_date is not None:
        cmd.extend(["--run-date", run_date])
    if dry_run:
        cmd.append("--dry-run")
    if no_safety_bound:
        cmd.append("--no-safety-bound")
    return subprocess.run(cmd, capture_output=True, text=True)

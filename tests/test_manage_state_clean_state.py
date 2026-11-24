"""Tests for manage_state.py verify-state-clean subcommand.

Covers RYA-6: verify-state-clean inspects state.json and decides whether it is a
clean, complete, inspectable state file.
  - clean, fully-formed file -> exit 0, no stderr
  - MISSING file -> exit 0 (absent == empty State, mirrors load_state)
  - corrupt JSON -> exit 1 with a clean stderr diagnostic (no traceback)
  - non-object top-level -> exit 1
  - missing required top-level key -> exit 1
  - an entry that fails to load into JobEntry -> exit 1
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run(state_path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MANAGE_STATE), "verify-state-clean", "--state", str(state_path)],
        capture_output=True,
        text=True,
    )


def _valid_state() -> dict:
    return {
        "last_run_date": "2026-06-30",
        "jobs": {
            "acme-eng": {
                "title": "Engineer",
                "company": "Acme",
                "score": 85,
                "role_type": "ai-engineer",
                "source": "jobspy",
                "first_seen": "2026-06-29",
                "last_seen": "2026-06-30",
                "active_status": "active",
                "job_url": "https://example.com/jobs/123456",
                "location": "Remote",
                "requirements_met": ["python", "ml"],
                "user_action": None,
                "expired_date": None,
                "reappeared": False,
            }
        },
        "expired_jobs": {},
    }


def test_clean_state_exits_zero(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(_valid_state(), indent=2), encoding="utf-8")

    result = _run(state_path)
    assert result.returncode == 0, f"expected clean: {result.stderr}"
    assert result.stderr == ""


def test_missing_file_exits_zero(tmp_path: Path) -> None:
    state_path = tmp_path / "does-not-exist.json"
    assert not state_path.exists()

    result = _run(state_path)
    assert result.returncode == 0
    assert result.stderr == ""


def test_corrupt_json_exits_nonzero(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text('{"jobs": {', encoding="utf-8")

    result = _run(state_path)
    assert result.returncode != 0
    assert str(state_path) in result.stderr
    assert "corrupt" in result.stderr


def test_not_an_object_exits_nonzero(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text("[]", encoding="utf-8")

    result = _run(state_path)
    assert result.returncode != 0
    assert "not a JSON object" in result.stderr


def test_missing_required_key_exits_nonzero(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps({"jobs": {}, "expired_jobs": {}}, indent=2), encoding="utf-8"
    )

    result = _run(state_path)
    assert result.returncode != 0
    assert "last_run_date" in result.stderr


def test_bad_entry_exits_nonzero(tmp_path: Path) -> None:
    state = _valid_state()
    # Drop a required JobEntry field so JobEntry(**entry) raises.
    del state["jobs"]["acme-eng"]["title"]
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    result = _run(state_path)
    assert result.returncode != 0
    assert "fails to load" in result.stderr

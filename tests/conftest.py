"""Shared fixtures for JSA V26 tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Add scripts/ to import path so tests can import manage_state directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def make_valid_job(**overrides) -> dict:
    """Create a valid job dict with sensible defaults. Override any field via kwargs."""
    defaults = {
        "job_id": "test-001", "title": "Engineer", "company": "Acme",
        "job_url": "https://boards.greenhouse.io/acme/jobs/12345",
        "role_type": "ai-engineer", "score": 85, "source_channel": "direct",
        "run_date": "2026-03-20", "location": "Remote", "status": "verified",
        "active_status": "live",
    }
    defaults.update(overrides)
    return defaults


def write_job(dir_path: Path, filename: str, job_dict: dict) -> Path:
    """Write a job dict to a JSON file, creating directories as needed."""
    dir_path.mkdir(parents=True, exist_ok=True)
    filepath = dir_path / filename
    filepath.write_text(json.dumps(job_dict, indent=2), encoding="utf-8")
    return filepath


def make_verified_json(
    *,
    title: str = "Founder Associate",
    company: str = "Duku AI",
    score: int = 78,
    role_type: str = "founders-associate",
    source: str = "linkedin",
    location: str = "London, England, UK",
    active_status: str = "verified",
    job_url: str = "https://www.linkedin.com/jobs/view/4344764433",
    **overrides: Any,
) -> dict[str, Any]:
    """Create a verified job JSON dict from the fixture template.

    Loads the real V13 fixture as the base, then overrides specified fields.
    This ensures the fixture matches the actual verified JSON schema.
    """
    with open(FIXTURE_DIR / "verified-job-template.json", encoding="utf-8") as f:
        template = json.load(f)

    template["title"] = title
    template["company"] = company
    template["score"] = score
    template["source"] = source
    template["location"] = location
    template["active_status"] = active_status
    template["job_url"] = job_url

    for key, value in overrides.items():
        template[key] = value

    return template


@pytest.fixture
def verified_dir(tmp_path: Path) -> Path:
    """Create a temporary verified directory with default role type subdirs."""
    for role in ("community-manager", "devrel"):
        (tmp_path / role).mkdir()
    return tmp_path


@pytest.fixture
def empty_state():
    """Return a fresh empty State instance."""
    from manage_state import State
    return State()

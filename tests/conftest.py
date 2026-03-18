"""Shared fixtures for JSA V17 tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Add scripts/ to import path so tests can import manage_state directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


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

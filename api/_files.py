"""Shared file reading helpers for Vercel serverless functions.

Reads Git-committed output files bundled in the Vercel deployment.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _get_base_dir() -> Path:
    """Get the base directory for the V17 project.

    Uses __file__ to navigate from api/_files.py up to project root.
    Works both locally and in Vercel (where CWD is also the project root).
    """
    return Path(__file__).resolve().parent.parent


def read_json(relative_path: str) -> Any | None:
    """Read a JSON file relative to the project root. Returns None if not found."""
    path = _get_base_dir() / relative_path
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_text(relative_path: str) -> str | None:
    """Read a text file relative to the project root. Returns None if not found."""
    path = _get_base_dir() / relative_path
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def list_verified_jobs() -> list[dict[str, Any]]:
    """Scan output/verified/ for all job JSON files. Returns list of dicts with 'key' added."""
    base = _get_base_dir() / "output" / "verified"
    if not base.exists():
        return []

    jobs = []
    for role_dir in sorted(base.iterdir()):
        if not role_dir.is_dir():
            continue
        role_type = role_dir.name
        for json_file in sorted(role_dir.glob("*.json")):
            if json_file.name.startswith("_"):
                continue
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                data["_key"] = f"{role_type}/{json_file.stem}"
                data["_role_type"] = role_type
                jobs.append(data)
            except (json.JSONDecodeError, OSError):
                continue

    return jobs


def read_state_json() -> dict[str, Any]:
    """Read state.json from project root."""
    return read_json("state.json") or {}


def read_delta_json() -> dict[str, Any]:
    """Read output/_delta.json."""
    return read_json("output/_delta.json") or {}

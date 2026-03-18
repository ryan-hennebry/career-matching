"""Tests for manage_state.py preflight subcommands.

Covers check-session-resume, check-model-settings, and check-dashboard-url.
All tests invoke manage_state.py via subprocess with tmp_path for isolation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a manage_state.py command and return the completed process."""
    return subprocess.run(
        [sys.executable, str(MANAGE_STATE), *cmd],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# TestCheckSessionResume
# ---------------------------------------------------------------------------


class TestCheckSessionResume:
    """Tests for the check-session-resume subcommand."""

    def test_exits_one_when_digest_sent_today(self, tmp_path: Path) -> None:
        """_status.json with today's sent_at date causes exit 1."""
        run_date = "2026-02-24"
        status_file = tmp_path / "_status.json"
        status_file.write_text(
            json.dumps({"sent_at": f"{run_date}T10:00:00Z", "count": 3}),
            encoding="utf-8",
        )

        result = _run([
            "check-session-resume",
            "--status-path", str(status_file),
            "--run-date", run_date,
        ])

        assert result.returncode == 1
        assert run_date in result.stdout

    def test_exits_zero_when_digest_sent_different_day(self, tmp_path: Path) -> None:
        """_status.json with an old sent_at date causes exit 0."""
        run_date = "2026-02-24"
        status_file = tmp_path / "_status.json"
        status_file.write_text(
            json.dumps({"sent_at": "2026-02-23T10:00:00Z", "count": 2}),
            encoding="utf-8",
        )

        result = _run([
            "check-session-resume",
            "--status-path", str(status_file),
            "--run-date", run_date,
        ])

        assert result.returncode == 0

    def test_exits_zero_when_no_status_file(self, tmp_path: Path) -> None:
        """Missing _status.json causes exit 0 (first run of the day)."""
        missing_path = tmp_path / "nonexistent" / "_status.json"

        result = _run([
            "check-session-resume",
            "--status-path", str(missing_path),
            "--run-date", "2026-02-24",
        ])

        assert result.returncode == 0


# ---------------------------------------------------------------------------
# TestCheckModelSettings
# ---------------------------------------------------------------------------


def _write_agent(agents_dir: Path, filename: str, frontmatter: str) -> Path:
    """Write a minimal agent markdown file with the given frontmatter block."""
    content = f"---\n{frontmatter}\n---\n\n# Agent\n"
    path = agents_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


class TestCheckModelSettings:
    """Tests for the check-model-settings subcommand."""

    def test_passes_with_valid_models(self, tmp_path: Path) -> None:
        """Agents with model: haiku and model: sonnet pass validation."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir, "search-verify.md", "name: search-verify\nmodel: haiku")
        _write_agent(agents_dir, "brief-generator.md", "name: brief-generator\nmodel: sonnet")

        result = _run([
            "check-model-settings",
            "--agents-dir", str(agents_dir),
        ])

        assert result.returncode == 0
        assert "All agent model settings validated" in result.stdout

    def test_fails_with_model_inherit(self, tmp_path: Path) -> None:
        """Agent with model: inherit fails validation."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir, "bad-agent.md", "name: bad-agent\nmodel: inherit")

        result = _run([
            "check-model-settings",
            "--agents-dir", str(agents_dir),
        ])

        assert result.returncode == 1
        assert "bad-agent.md" in result.stdout
        assert "inherit" in result.stdout

    def test_fails_with_missing_model(self, tmp_path: Path) -> None:
        """Agent with no model: line fails validation."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir, "no-model-agent.md", "name: no-model-agent\nskills: search")

        result = _run([
            "check-model-settings",
            "--agents-dir", str(agents_dir),
        ])

        assert result.returncode == 1
        assert "no-model-agent.md" in result.stdout

    def test_fails_with_model_opus(self, tmp_path: Path) -> None:
        """Agent with model: opus fails validation."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _write_agent(agents_dir, "opus-agent.md", "name: opus-agent\nmodel: opus")

        result = _run([
            "check-model-settings",
            "--agents-dir", str(agents_dir),
        ])

        assert result.returncode == 1
        assert "opus-agent.md" in result.stdout
        assert "opus" in result.stdout


# ---------------------------------------------------------------------------
# TestCheckDashboardUrl
# ---------------------------------------------------------------------------


def _write_context(path: Path, content: str) -> None:
    """Write a context.md file with the given content."""
    path.write_text(content, encoding="utf-8")


class TestCheckDashboardUrl:
    """Tests for the check-dashboard-url subcommand."""

    def test_exits_zero_with_valid_url(self, tmp_path: Path) -> None:
        """context.md with a Dashboard: URL causes exit 0 and prints the URL."""
        context_file = tmp_path / "context.md"
        _write_context(
            context_file,
            "## Delivery\nDashboard: https://jsa-dashboard.vercel.app/#digest\n\n## Other\nfoo\n",
        )

        result = _run([
            "check-dashboard-url",
            "--context-path", str(context_file),
        ])

        assert result.returncode == 0
        assert "https://jsa-dashboard.vercel.app/#digest" in result.stdout

    def test_exits_one_with_empty_url(self, tmp_path: Path) -> None:
        """context.md with Dashboard: (empty) causes exit 1."""
        context_file = tmp_path / "context.md"
        _write_context(
            context_file,
            "## Delivery\nDashboard:\n\n## Other\nfoo\n",
        )

        result = _run([
            "check-dashboard-url",
            "--context-path", str(context_file),
        ])

        assert result.returncode == 1
        assert "missing or empty" in result.stdout

    def test_exits_one_when_missing(self, tmp_path: Path) -> None:
        """context.md without a Dashboard: line causes exit 1."""
        context_file = tmp_path / "context.md"
        _write_context(
            context_file,
            "## Delivery\nEmail: user@example.com\n\n## Other\nfoo\n",
        )

        result = _run([
            "check-dashboard-url",
            "--context-path", str(context_file),
        ])

        assert result.returncode == 1
        assert "missing or empty" in result.stdout

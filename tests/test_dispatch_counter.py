"""Tests for dispatch counter subcommands in manage_state.py.

Tests increment-dispatch-counter, check-dispatch-budget, and CLAUDE.md ceiling."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANAGE_STATE = PROJECT_ROOT / "scripts" / "manage_state.py"
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


def _run_manage_state(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MANAGE_STATE)] + args,
        capture_output=True, text=True, cwd=str(cwd),
    )


class TestIncrementDispatchCounter:
    def test_increment_creates_budget_section(self, tmp_path: Path) -> None:
        """increment-dispatch-counter creates ## Budget section if missing."""
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Search Progress\n- channel 1 done\n", encoding="utf-8")
        result = _run_manage_state(
            ["increment-dispatch-counter", "--session-state-path", str(ss)],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        content = ss.read_text(encoding="utf-8")
        assert "## Budget" in content
        assert "dispatch_count: 1" in content

    def test_increment_bumps_existing_counter(self, tmp_path: Path) -> None:
        """increment-dispatch-counter increments existing count."""
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Budget\ndispatch_count: 5\n", encoding="utf-8")
        result = _run_manage_state(
            ["increment-dispatch-counter", "--session-state-path", str(ss)],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        content = ss.read_text(encoding="utf-8")
        assert "dispatch_count: 6" in content


class TestCheckDispatchBudget:
    def test_under_ceiling_exits_0(self, tmp_path: Path) -> None:
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Budget\ndispatch_count: 10\n", encoding="utf-8")
        result = _run_manage_state(
            ["check-dispatch-budget", "--session-state-path", str(ss), "--ceiling", "25"],
            cwd=tmp_path,
        )
        assert result.returncode == 0

    def test_at_ceiling_exits_1(self, tmp_path: Path) -> None:
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Budget\ndispatch_count: 25\n", encoding="utf-8")
        result = _run_manage_state(
            ["check-dispatch-budget", "--session-state-path", str(ss), "--ceiling", "25"],
            cwd=tmp_path,
        )
        assert result.returncode == 1

    def test_over_ceiling_exits_1(self, tmp_path: Path) -> None:
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Budget\ndispatch_count: 30\n", encoding="utf-8")
        result = _run_manage_state(
            ["check-dispatch-budget", "--session-state-path", str(ss), "--ceiling", "25"],
            cwd=tmp_path,
        )
        assert result.returncode == 1

    def test_missing_budget_section_exits_0(self, tmp_path: Path) -> None:
        ss = tmp_path / "session-state.md"
        ss.write_text("# Session State\n\n## Search Progress\n- done\n", encoding="utf-8")
        result = _run_manage_state(
            ["check-dispatch-budget", "--session-state-path", str(ss), "--ceiling", "25"],
            cwd=tmp_path,
        )
        assert result.returncode == 0


class TestClaudeMdDispatchCeiling:
    def test_claude_md_has_dispatch_ceiling(self) -> None:
        content = CLAUDE_MD.read_text(encoding="utf-8")
        assert "DISPATCH_CEILING" in content
        assert "25" in content

"""Tests for preflight.sh startup checks (11 tests).

All tests are expected to FAIL until preflight.sh is implemented.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import shutil
import textwrap
from pathlib import Path

# Absolute path to the real preflight.sh in the worktree
PREFLIGHT_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "preflight.sh"


def _run_preflight(
    cwd: str,
    *,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess:
    """Run preflight.sh from *cwd* and return the completed process."""
    cmd = ["bash", str(PREFLIGHT_SCRIPT)]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def _setup_passing_tree(base: Path) -> None:
    """Populate *base* with the minimum file tree that passes all preflight checks.

    Mirrors the real V21 directory layout:
        context.md          — contains Dashboard URL
        .claude/settings.local.json  — required permissions
        .github/jsa-config.json      — valid JSON config
        scripts/manage_state.py      — executable stub
        CLAUDE.md           — valid structure (<=280 lines, required sections)
        references/         — orchestration.md, presentation-rules.md,
                              subagent-search-verify.md, subagent-digest-email.md
        .claude/agent-memory/search-verify/MEMORY.md — non-empty memory
    """
    # --- context.md ---
    (base / "context.md").write_text(
        textwrap.dedent("""\
            # Job Search Agent - Context

            ## Profile
            - Name: Test User

            ## Delivery
            - Dashboard: https://jsa-dashboard.vercel.app/#digest
        """),
        encoding="utf-8",
    )

    # --- .claude/settings.local.json ---
    settings_dir = base / ".claude"
    settings_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "settings.local.json").write_text(
        json.dumps(
            {
                "permissions": {
                    "allow": [
                        "Bash(python3 scripts/*)",
                        "Bash(bash scripts/*)",
                        "Read",
                        "Write",
                        "Glob",
                        "Grep",
                    ],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # --- .github/jsa-config.json ---
    github_dir = base / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)
    (github_dir / "jsa-config.json").write_text(
        json.dumps(
            {
                "agent": {"version": "v21"},
                "roles": [{"title": "Community Manager", "slug": "community-manager"}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # --- scripts/manage_state.py (executable stub) ---
    scripts_dir = base / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    manage_state = scripts_dir / "manage_state.py"
    manage_state.write_text(
        textwrap.dedent("""\
            #!/usr/bin/env python3
            import sys
            if len(sys.argv) > 1:
                if sys.argv[1] == "cleanup":
                    print("cleanup done")
                elif sys.argv[1] == "dedup":
                    print("dedup done")
            sys.exit(0)
        """),
        encoding="utf-8",
    )
    manage_state.chmod(manage_state.stat().st_mode | stat.S_IEXEC)

    # --- CLAUDE.md (valid structure) ---
    # Must be <=280 lines, have required sections, phase dispatch table with
    # 5 phases referencing references/*.md, ON STARTUP referencing preflight.sh
    # and manage_state.py.
    phase_table = (
        "| Phase | Entry Criteria | Exit Criteria | Load Reference |\n"
        "|-------|----------------|---------------|----------------|\n"
        "| Search | Session started | Raw jobs collected | `references/orchestration.md` (Phase 1) |\n"
        "| Verify | Raw jobs exist | Verified JSONs | `references/orchestration.md` (Phase 2) |\n"
        "| Dedup | Verified JSONs exist | Duplicates archived | `references/orchestration.md` (Phase 3) |\n"
        "| Present | Dedup complete | User reviewed | `references/presentation-rules.md` |\n"
        "| Deliver | User approved | Email sent | `references/orchestration.md` (Phase 5) |\n"
    )
    claude_md = textwrap.dedent(f"""\
        # Job Search Agent

        ## Hard Constraints
        1. Never pass model.

        ## Context Budget
        Parent reads status files only.

        ## ON STARTUP
        1. Run preflight: `bash scripts/preflight.sh`
        2. Read context.md
        3. Run manage_state.py sync
        4. Read .claude/agent-memory files

        ## Phase Dispatch
        {phase_table}
        ## Onboarding
        First-time flow.

        ## Communication Style
        Keep it concise.
    """)
    (base / "CLAUDE.md").write_text(claude_md, encoding="utf-8")

    # --- references/ ---
    refs_dir = base / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)

    # orchestration.md — needs 5 phase headings + checkpoint commands
    (refs_dir / "orchestration.md").write_text(
        textwrap.dedent("""\
            # Orchestration

            ## Phase 1 — Search
            Search instructions.
            Run checkpoint clear to reset before searching.

            ## Phase 2 — Verify
            Run checkpoint validate to ensure Phase 1 complete.
            Verify instructions.
            Run checkpoint write after verification.

            ## Phase 3 — Dedup
            Dedup instructions.

            ## Phase 4 — Present
            Present instructions.

            ## Phase 5 — Deliver
            Deliver instructions.
        """),
        encoding="utf-8",
    )

    # --- output/.checkpoints/ ---
    (base / "output" / ".checkpoints").mkdir(parents=True, exist_ok=True)

    # presentation-rules.md — needs table format section
    (refs_dir / "presentation-rules.md").write_text(
        textwrap.dedent("""\
            # Presentation Rules

            ## Table Format
            Use markdown tables for job presentation.
        """),
        encoding="utf-8",
    )

    (refs_dir / "subagent-search-verify.md").write_text(
        "# Search-Verify Subagent\nInstructions.\n",
        encoding="utf-8",
    )
    (refs_dir / "subagent-digest-email.md").write_text(
        "# Digest-Email Subagent\nInstructions.\n",
        encoding="utf-8",
    )

    # --- .claude/agent-memory/ (non-empty) ---
    memory_dir = settings_dir / "agent-memory" / "search-verify"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "MEMORY.md").write_text(
        "# Search-Verify Memory\n- Known issue: example.\n",
        encoding="utf-8",
    )

    # --- .claude/agents/ (agent files with background: true) ---
    agents_dir = base / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "test-agent.md").write_text(
        textwrap.dedent("""\
            ---
            name: test-agent
            description: Test agent
            tools: Bash
            model: haiku
            background: true
            ---
            You are a test agent.
        """),
        encoding="utf-8",
    )
    (agents_dir / "search-verify.md").write_text(
        textwrap.dedent("""\
            ---
            name: search-verify
            description: Search job sources and verify active listings
            tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
            model: sonnet
            background: true
            ---
            You are a search-verify subagent.
        """),
        encoding="utf-8",
    )


class TestPreflight:
    """Tests for scripts/preflight.sh."""

    # ------------------------------------------------------------------
    # 1. All present → passes
    # ------------------------------------------------------------------
    def test_preflight_passes_when_all_present(self, tmp_path: Path) -> None:
        """All required files present, exits 0."""
        _setup_passing_tree(tmp_path)
        result = _run_preflight(str(tmp_path))
        assert result.returncode == 0, (
            f"preflight should pass when all files present.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # ------------------------------------------------------------------
    # 2. Missing Dashboard URL → exit 1
    # ------------------------------------------------------------------
    def test_preflight_fails_missing_dashboard_url(self, tmp_path: Path) -> None:
        """context.md missing Dashboard URL, exits 1 with error message."""
        _setup_passing_tree(tmp_path)
        # Overwrite context.md without Dashboard line
        (tmp_path / "context.md").write_text(
            textwrap.dedent("""\
                # Job Search Agent - Context

                ## Profile
                - Name: Test User

                ## Delivery
                - Email: test@example.com
            """),
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path))
        assert result.returncode == 1, "preflight should fail when Dashboard URL missing"
        combined = result.stdout + result.stderr
        assert "CRITICAL: Dashboard URL missing from context.md" in combined, (
            f"Expected dashboard URL error message. Got:\n{combined}"
        )

    # ------------------------------------------------------------------
    # 3. Missing permissions → exit 1
    # ------------------------------------------------------------------
    def test_preflight_fails_missing_permissions(self, tmp_path: Path) -> None:
        """settings.local.json missing required permissions, exits 1."""
        _setup_passing_tree(tmp_path)
        # Overwrite settings.local.json with minimal permissions (missing Read, Write, Glob, Grep)
        (tmp_path / ".claude" / "settings.local.json").write_text(
            json.dumps({"permissions": {"allow": ["Bash(python3 scripts/*)"]}}, indent=2),
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path))
        assert result.returncode == 1, "preflight should fail when required permissions missing"
        combined = result.stdout + result.stderr
        assert "CRITICAL: Required permissions missing from settings.local.json" in combined, (
            f"Expected permissions error message. Got:\n{combined}"
        )

    # ------------------------------------------------------------------
    # 4. Invalid config JSON → exit 1
    # ------------------------------------------------------------------
    def test_preflight_fails_invalid_config_json(self, tmp_path: Path) -> None:
        """.github/jsa-config.json is invalid JSON, exits 1."""
        _setup_passing_tree(tmp_path)
        (tmp_path / ".github" / "jsa-config.json").write_text(
            "{ invalid json content !!!",
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path))
        assert result.returncode == 1, "preflight should fail on invalid JSON config"
        combined = result.stdout + result.stderr
        assert "CRITICAL: .github/jsa-config.json is invalid JSON" in combined, (
            f"Expected invalid JSON error message. Got:\n{combined}"
        )

    # ------------------------------------------------------------------
    # 5. Missing manage_state.py → exit 1
    # ------------------------------------------------------------------
    def test_preflight_fails_missing_manage_state(self, tmp_path: Path) -> None:
        """scripts/manage_state.py doesn't exist, exits 1."""
        _setup_passing_tree(tmp_path)
        os.remove(tmp_path / "scripts" / "manage_state.py")
        result = _run_preflight(str(tmp_path))
        assert result.returncode == 1, "preflight should fail when manage_state.py missing"
        combined = result.stdout + result.stderr
        assert "CRITICAL: scripts/manage_state.py not found or not executable" in combined, (
            f"Expected manage_state.py error message. Got:\n{combined}"
        )

    # ------------------------------------------------------------------
    # 6. Empty agent memory → warning, exit 0
    # ------------------------------------------------------------------
    def test_preflight_warns_empty_agent_memory(self, tmp_path: Path) -> None:
        """Agent-memory files empty, exits 0 with warning."""
        _setup_passing_tree(tmp_path)
        # Overwrite memory file with empty content
        memory_file = tmp_path / ".claude" / "agent-memory" / "search-verify" / "MEMORY.md"
        memory_file.write_text("", encoding="utf-8")
        result = _run_preflight(str(tmp_path))
        assert result.returncode == 0, (
            f"preflight should pass (warning only) for empty agent memory.\n"
            f"stderr: {result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "WARNING: Agent memory files are empty" in combined, (
            f"Expected agent memory warning. Got:\n{combined}"
        )

    # ------------------------------------------------------------------
    # 7. Missing reference files → warning, exit 0
    # ------------------------------------------------------------------
    def test_preflight_warns_missing_reference_files(self, tmp_path: Path) -> None:
        """references/ missing expected files, exits 0 with warning."""
        _setup_passing_tree(tmp_path)
        # Remove one expected reference file
        os.remove(tmp_path / "references" / "subagent-search-verify.md")
        result = _run_preflight(str(tmp_path))
        assert result.returncode == 0, (
            f"preflight should pass (warning only) for missing reference files.\n"
            f"stderr: {result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "WARNING: Missing reference files:" in combined, (
            f"Expected missing reference files warning. Got:\n{combined}"
        )

    # ------------------------------------------------------------------
    # 8. Idempotent — running twice produces same result
    # ------------------------------------------------------------------
    def test_preflight_idempotent(self, tmp_path: Path) -> None:
        """Running preflight twice produces same result."""
        _setup_passing_tree(tmp_path)
        result1 = _run_preflight(str(tmp_path))
        assert result1.returncode == 0, (
            f"preflight first run should pass.\nstderr: {result1.stderr}"
        )
        result2 = _run_preflight(str(tmp_path))
        assert result2.returncode == 0, (
            f"preflight second run should pass.\nstderr: {result2.stderr}"
        )
        assert result1.returncode == result2.returncode, (
            "preflight should be idempotent (same exit code on repeated runs)"
        )
        assert result1.stdout == result2.stdout, (
            "preflight should be idempotent (same stdout on repeated runs)"
        )

    # ------------------------------------------------------------------
    # 9. Runs manage_state cleanup and dedup
    # ------------------------------------------------------------------
    def test_preflight_runs_manage_state_cleanup_and_dedup(
        self,
        tmp_path: Path,
    ) -> None:
        """After critical checks pass, preflight.sh invokes cleanup and dedup."""
        _setup_passing_tree(tmp_path)
        result = _run_preflight(str(tmp_path))
        assert result.returncode == 0, (
            f"preflight should pass.\nstderr: {result.stderr}"
        )
        combined = result.stdout + result.stderr
        # The stub manage_state.py prints "cleanup done" and "dedup done"
        assert "cleanup" in combined.lower(), (
            f"Expected evidence of cleanup invocation. Got:\n{combined}"
        )
        assert "dedup" in combined.lower(), (
            f"Expected evidence of dedup invocation. Got:\n{combined}"
        )

    # ------------------------------------------------------------------
    # 10. --env skips structure checks
    # ------------------------------------------------------------------
    def test_preflight_env_only_skips_structure_checks(
        self,
        tmp_path: Path,
    ) -> None:
        """preflight.sh --env runs environment checks, skips CLAUDE.md structure checks."""
        _setup_passing_tree(tmp_path)
        # Break CLAUDE.md structure so structure checks would fail
        (tmp_path / "CLAUDE.md").write_text(
            "# Minimal file\nNo required sections here.\n",
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        # --env should skip structure validation, so this should still pass
        # (all environment files are present)
        assert result.returncode == 0, (
            f"preflight --env should pass even with broken CLAUDE.md structure.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # ------------------------------------------------------------------
    # 11. --structure skips env checks
    # ------------------------------------------------------------------
    def test_preflight_structure_only_skips_env_checks(
        self,
        tmp_path: Path,
    ) -> None:
        """preflight.sh --structure runs structure checks, skips environment checks."""
        _setup_passing_tree(tmp_path)
        # Remove settings.local.json so env checks would fail
        os.remove(tmp_path / ".claude" / "settings.local.json")
        result = _run_preflight(str(tmp_path), extra_args=["--structure"])
        # --structure should skip environment checks, so this should still pass
        # (CLAUDE.md structure is valid)
        assert result.returncode == 0, (
            f"preflight --structure should pass even with missing settings.local.json.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # ------------------------------------------------------------------
    # 12. Missing checkpoint validate in orchestration.md → exit 1
    # ------------------------------------------------------------------
    def test_preflight_fails_missing_checkpoint_validate(
        self,
        tmp_path: Path,
    ) -> None:
        """orchestration.md missing checkpoint validate, exits 1."""
        _setup_passing_tree(tmp_path)
        # Overwrite orchestration.md without checkpoint commands
        (tmp_path / "references" / "orchestration.md").write_text(
            textwrap.dedent("""\
                # Orchestration

                ## Phase 1 — Search
                Search instructions.

                ## Phase 2 — Verify
                Verify instructions.

                ## Phase 3 — Dedup
                Dedup instructions.

                ## Phase 4 — Present
                Present instructions.

                ## Phase 5 — Deliver
                Deliver instructions.
            """),
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path), extra_args=["--structure"])
        assert result.returncode == 1, (
            f"preflight should fail when orchestration.md missing checkpoint validate.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # ------------------------------------------------------------------
    # 13. Agent missing background: true → exit 1
    # ------------------------------------------------------------------
    def test_preflight_fails_agent_missing_background(
        self,
        tmp_path: Path,
    ) -> None:
        """Agent .md without background: true, exits 1."""
        _setup_passing_tree(tmp_path)
        agents_dir = tmp_path / ".claude" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "bad-agent.md").write_text(
            textwrap.dedent("""\
                ---
                name: bad-agent
                description: Test agent
                tools: Bash
                model: inherit
                ---
                You are a test agent.
            """),
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path), extra_args=["--structure"])
        assert result.returncode == 1, (
            f"preflight should fail when agent missing background: true.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


class TestPreflightGitPull:
    """Tests for git pull behaviour in interactive vs scheduled mode."""

    # ------------------------------------------------------------------
    # 14. Interactive mode — git pull runs (no SCHEDULED_RUN env var)
    # ------------------------------------------------------------------
    def test_git_pull_runs_in_interactive_mode(self, tmp_path: Path) -> None:
        """No SCHEDULED_RUN env var: preflight does NOT print skip message."""
        _setup_passing_tree(tmp_path)
        env = {k: v for k, v in os.environ.items() if k != "SCHEDULED_RUN"}
        result = subprocess.run(
            ["bash", str(PREFLIGHT_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env=env,
        )
        combined = result.stdout + result.stderr
        assert "Skipping git pull (scheduled run)" not in combined, (
            f"Interactive mode should NOT skip git pull, but got skip message.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # ------------------------------------------------------------------
    # 15. Scheduled mode — git pull skipped
    # ------------------------------------------------------------------
    def test_git_pull_skipped_in_scheduled_mode(self, tmp_path: Path) -> None:
        """SCHEDULED_RUN=true: preflight prints 'Skipping git pull (scheduled run)'."""
        _setup_passing_tree(tmp_path)
        env = {**os.environ, "SCHEDULED_RUN": "true"}
        result = subprocess.run(
            ["bash", str(PREFLIGHT_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env=env,
        )
        combined = result.stdout + result.stderr
        assert "Skipping git pull (scheduled run)" in combined, (
            f"Scheduled mode should print skip message.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


class TestPreflightAgentMemory:
    """Tests for CLAUDE.md agent-memory startup read check (HC4)."""

    # ------------------------------------------------------------------
    # 16. CLAUDE.md references .claude/agent-memory → exit 0
    # ------------------------------------------------------------------
    def test_passes_when_claude_md_has_agent_memory_ref(self, tmp_path: Path) -> None:
        """CLAUDE.md contains .claude/agent-memory reference, exits 0."""
        _setup_passing_tree(tmp_path)
        # _setup_passing_tree already writes a CLAUDE.md that references
        # agent-memory via "ON STARTUP" — ensure the reference is present.
        claude_md_text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        if ".claude/agent-memory" not in claude_md_text:
            # Append agent-memory reference to ON STARTUP block
            (tmp_path / "CLAUDE.md").write_text(
                claude_md_text.replace(
                    "3. Run manage_state.py sync",
                    "3. Run manage_state.py sync\n4. Read .claude/agent-memory files",
                ),
                encoding="utf-8",
            )
        result = _run_preflight(str(tmp_path), extra_args=["--structure"])
        assert result.returncode == 0, (
            f"preflight should pass when CLAUDE.md has agent-memory ref.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "CLAUDE.md missing agent-memory startup read (HC4)" not in combined, (
            f"Should not emit HC4 warning when ref is present.\nGot:\n{combined}"
        )

    # ------------------------------------------------------------------
    # 17. CLAUDE.md missing .claude/agent-memory → FAILED=1 with HC4 message
    # ------------------------------------------------------------------
    def test_warns_when_claude_md_missing_agent_memory_ref(self, tmp_path: Path) -> None:
        """CLAUDE.md without agent-memory reference, fails with HC4 message."""
        _setup_passing_tree(tmp_path)
        # Write a CLAUDE.md that has all required sections but no agent-memory ref
        phase_table = (
            "| Phase | Entry Criteria | Exit Criteria | Load Reference |\n"
            "|-------|----------------|---------------|----------------|\n"
            "| Search | Session started | Raw jobs collected | `references/orchestration.md` (Phase 1) |\n"
            "| Verify | Raw jobs exist | Verified JSONs | `references/orchestration.md` (Phase 2) |\n"
            "| Dedup | Verified JSONs exist | Duplicates archived | `references/orchestration.md` (Phase 3) |\n"
            "| Present | Dedup complete | User reviewed | `references/presentation-rules.md` |\n"
            "| Deliver | User approved | Email sent | `references/orchestration.md` (Phase 5) |\n"
        )
        (tmp_path / "CLAUDE.md").write_text(
            textwrap.dedent(f"""\
                # Job Search Agent

                ## Hard Constraints
                1. Never pass model.

                ## Context Budget
                Parent reads status files only.

                ## ON STARTUP
                1. Run preflight: `bash scripts/preflight.sh`
                2. Read context.md
                3. Run manage_state.py sync

                ## Phase Dispatch
                {phase_table}
                ## Onboarding
                First-time flow.

                ## Communication Style
                Keep it concise.
            """),
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path), extra_args=["--structure"])
        assert result.returncode == 1, (
            f"preflight should fail when CLAUDE.md missing agent-memory ref.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "CLAUDE.md missing agent-memory startup read (HC4)" in combined, (
            f"Expected HC4 message. Got:\n{combined}"
        )


class TestPreflightSchemaValidation:
    """Tests for schema validation and model-tier checks added in Step 21."""

    @staticmethod
    def _write_manage_state_stub(scripts_dir: Path, validate_exit: int) -> None:
        import stat as _stat

        manage_state = scripts_dir / "manage_state.py"
        manage_state.write_text(
            textwrap.dedent(f"""\
                #!/usr/bin/env python3
                import sys
                if len(sys.argv) > 1:
                    cmd = sys.argv[1]
                    if cmd == "cleanup":
                        print("cleanup done")
                        sys.exit(0)
                    elif cmd == "dedup":
                        print("dedup done")
                        sys.exit(0)
                    elif cmd == "validate-schema":
                        sys.exit({validate_exit})
                sys.exit(0)
            """),
            encoding="utf-8",
        )
        manage_state.chmod(manage_state.stat().st_mode | _stat.S_IEXEC)

    @staticmethod
    def _write_search_verify_agent(agents_dir: Path, model: str) -> None:
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "search-verify.md").write_text(
            textwrap.dedent(f"""\
                ---
                name: search-verify
                description: Search job sources and verify active listings
                tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
                model: {model}
                background: true
                ---
                You are a search-verify subagent.
            """),
            encoding="utf-8",
        )

    @staticmethod
    def _seed_verified(tmp_path: Path) -> None:
        """Create a verified JSON file so first-run detection is bypassed."""
        vdir = tmp_path / "output" / "verified" / "ai-engineer"
        vdir.mkdir(parents=True, exist_ok=True)
        (vdir / "seed-job.json").write_text(
            json.dumps({"job_id": "seed-001", "title": "Eng"}),
            encoding="utf-8",
        )

    def test_preflight_runs_schema_validation(self, tmp_path: Path) -> None:
        """Mock validate-schema to exit 0 -> preflight passes this check."""
        _setup_passing_tree(tmp_path)
        self._seed_verified(tmp_path)
        self._write_manage_state_stub(tmp_path / "scripts", validate_exit=0)
        self._write_search_verify_agent(tmp_path / ".claude" / "agents", "sonnet")
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 0, (
            f"preflight should pass when validate-schema exits 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_preflight_fails_on_invalid_schema(self, tmp_path: Path) -> None:
        """Mock validate-schema to exit 1 -> preflight reports failure."""
        _setup_passing_tree(tmp_path)
        self._seed_verified(tmp_path)
        self._write_manage_state_stub(tmp_path / "scripts", validate_exit=1)
        self._write_search_verify_agent(tmp_path / ".claude" / "agents", "sonnet")
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 1, (
            f"preflight should fail when validate-schema exits 1.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "[PREFLIGHT FAIL] Schema validation failed" in combined

    def test_preflight_checks_search_verify_model(self, tmp_path: Path) -> None:
        """Preflight checks for model: sonnet in search-verify agent."""
        _setup_passing_tree(tmp_path)
        self._seed_verified(tmp_path)
        self._write_manage_state_stub(tmp_path / "scripts", validate_exit=0)
        self._write_search_verify_agent(tmp_path / ".claude" / "agents", "haiku")
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 1, (
            f"preflight should fail when search-verify is not on Sonnet tier.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "[PREFLIGHT FAIL] search-verify agent not on Sonnet tier" in combined


class TestPreflightFirstRun:
    """Tests for first-run detection: empty output/verified/ skips safety bounds."""

    def test_first_run_empty_verified_exits_zero(self, tmp_path: Path) -> None:
        """Empty output/verified/ (first run) should exit 0 even with --env."""
        _setup_passing_tree(tmp_path)
        # Ensure output/verified/ exists but is empty (no role subdirs with jobs)
        verified_dir = tmp_path / "output" / "verified"
        verified_dir.mkdir(parents=True, exist_ok=True)
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 0, (
            f"First run (empty verified/) should exit 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_first_run_missing_verified_exits_zero(self, tmp_path: Path) -> None:
        """Missing output/verified/ (first run) should exit 0 even with --env."""
        _setup_passing_tree(tmp_path)
        # Remove output/verified/ entirely if it exists
        verified_dir = tmp_path / "output" / "verified"
        if verified_dir.exists():
            shutil.rmtree(verified_dir)
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 0, (
            f"First run (missing verified/) should exit 0.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_existing_output_uses_normal_bounds(self, tmp_path: Path) -> None:
        """Existing output/verified/ with data uses normal safety bounds."""
        _setup_passing_tree(tmp_path)
        # Create a verified dir with actual job files
        verified_dir = tmp_path / "output" / "verified" / "ai-engineer"
        verified_dir.mkdir(parents=True, exist_ok=True)
        (verified_dir / "acme-job.json").write_text(
            json.dumps({
                "job_id": "acme-001", "title": "Engineer", "company": "Acme",
                "job_url": "https://example.com", "role_type": "ai-engineer",
                "score": 85, "source_channel": "direct-career-pages",
                "run_date": "2026-02-27", "location": "Remote", "status": "verified",
            }),
            encoding="utf-8",
        )
        result = _run_preflight(str(tmp_path), extra_args=["--env"])
        assert result.returncode == 0, (
            f"Existing output should pass normal bounds.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

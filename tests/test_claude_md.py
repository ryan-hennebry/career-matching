"""Tests for CLAUDE.md structural assertions — startup, UX rules, and workflow steps.
One assertion per concern to avoid brittle substring coupling.

V21 note: Phase 2 decomposed CLAUDE.md into a compact orchestrator plus
references/ files.  Step-numbered content (Step 11, 13, 22, 23) moved to
references/orchestration.md.  Section headings changed from ALL-CAPS to
Title Case (e.g. '## CORE RULES' → '## Core Rules').  Tests updated to
read from the correct files."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"
ORCHESTRATION_MD = PROJECT_ROOT / "references" / "orchestration.md"


def _read_claude_md() -> str:
    return CLAUDE_MD.read_text(encoding="utf-8")


def _read_orchestration_md() -> str:
    return ORCHESTRATION_MD.read_text(encoding="utf-8")


def _extract_section(content: str, heading: str) -> str:
    """Extract a ## section by heading name."""
    start = content.find(heading)
    assert start != -1, f"Section '{heading}' not found"
    next_section = content.find("\n## ", start + 1)
    return content[start:next_section] if next_section != -1 else content[start:]


def test_startup_reads_agent_memory() -> None:
    """ON STARTUP section must reference agent-memory MEMORY.md with log output."""
    section = _extract_section(_read_claude_md(), "## ON STARTUP")
    assert "agent-memory" in section and "MEMORY.md" in section


def test_ux_rules_prohibit_technical_work_for_user() -> None:
    """UX Rules must prohibit directing user to technical work."""
    section = _extract_section(_read_claude_md(), "## UX Rules")
    assert "technical work" in section.lower()


def test_step_22_scheduled_run_prompt() -> None:
    """Phase 5 Step 22 must offer proactive daily runs via GitHub Actions.

    V21: Step 22 moved from CLAUDE.md to references/orchestration.md Phase 5.
    Wording changed from 'scheduled runs' to 'daily runs'."""
    content = _read_orchestration_md()
    assert "Step 22" in content, "Step 22 not found in orchestration.md"
    step22_start = content.find("Step 22")
    rest = content[step22_start:]
    lower = rest[:500].lower()
    assert "github actions" in lower and ("scheduled" in lower or "daily" in lower)


def test_step_13_references_dedup_subcommand() -> None:
    """Phase 3 Step 13 must reference dedup with manage_state.py CLI.

    V21: Step 13 moved from CLAUDE.md to references/orchestration.md Phase 3."""
    content = _read_orchestration_md()
    assert "Step 13" in content, "Step 13 not found in orchestration.md"
    step13_start = content.find("Step 13")
    rest = content[step13_start:]
    assert "dedup" in rest[:500].lower()


def test_api_key_piping_uses_stdin_not_inline() -> None:
    """Security section must require piping API keys via stdin, never inline.

    V21: API key piping constraint is in CLAUDE.md ## Security section and
    Hard Constraints item 9 (not a Step 23 section)."""
    content = _read_claude_md()

    security_section = _extract_section(content, "## Security")
    lower = security_section.lower()
    assert "stdin" in lower or "pipe" in lower or "piping" in lower, (
        "Security section must instruct piping keys via stdin — "
        "found neither 'stdin' nor 'pipe'."
    )

    assert "never" in lower or "do not" in lower, (
        "Security section must explicitly warn against inline key usage."
    )


def test_settings_local_json_instructions_use_merge_language() -> None:
    """Any settings.local.json instruction must use merge/preserve language, not blind overwrite."""
    content = _read_claude_md()

    idx = content.find("settings.local.json")
    if idx == -1:
        return

    snippet_start = max(0, idx - 100)
    snippet_end = min(len(content), idx + 700)
    snippet = content[snippet_start:snippet_end].lower()

    assert "merge" in snippet or "preserve" in snippet or "read existing" in snippet, (
        "settings.local.json instructions must use 'merge', 'preserve', or 'read existing' language "
        "to prevent overwriting user config."
    )

    import re
    blind_overwrite = re.search(r'\bwrite\b.*settings\.local\.json', snippet)
    if blind_overwrite:
        assert "merge" in snippet or "preserve" in snippet, (
            "settings.local.json instructions mention 'write' without 'merge' or 'preserve' — "
            "this risks silently overwriting existing user settings."
        )


def test_session_state_written_per_batch_not_only_at_end() -> None:
    """Session-state.md must be written after each batch, not just at end.

    V21: Core rules are in '## Core Rules' (title case).  Per-batch checkpoint
    language is in references/orchestration.md Phase 1 step 7."""
    claude_content = _read_claude_md()
    orch_content = _read_orchestration_md()

    core_rules_section = _extract_section(claude_content, "## Core Rules")

    combined = (core_rules_section + " " + orch_content).lower()

    has_per_batch = "per-batch" in combined or "each batch" in combined or "every batch" in combined
    has_checkpoint = "checkpoint" in combined
    has_not_defer = "not defer" in combined or "do not defer" in combined

    assert has_per_batch or (has_checkpoint and has_not_defer), (
        "CLAUDE.md + orchestration.md must explicitly require session-state.md to be written "
        "after each search batch (not deferred to end of session). "
        "Expected 'each batch', 'per-batch', or 'checkpoint' + 'not defer' language."
    )


def test_never_directs_user_to_perform_technical_actions() -> None:
    """CLAUDE.md must not direct users to run commands or perform technical setup steps."""
    content = _read_claude_md()
    lower = content.lower()

    # Check for phrases that direct the user to perform technical actions
    directive_phrases = [
        "please run",
        "you need to run",
        "execute the following",
        "run this command",
        "you should run",
    ]
    for phrase in directive_phrases:
        assert phrase not in lower, (
            f"CLAUDE.md contains '{phrase}' which directs the user to perform technical actions. "
            "The agent must perform all technical operations itself, never instruct the user."
        )


def test_no_foreground_fallback_guard() -> None:
    """CLAUDE.md must not contain foreground-fallback guard or dispatch_mode variable.

    V22: All subagents dispatch with background: true. No foreground fallback needed."""
    content = _read_claude_md().lower()
    assert "foreground-fallback" not in content, (
        "CLAUDE.md still contains 'foreground-fallback' — removed in V22"
    )
    assert "dispatch_mode" not in content, (
        "CLAUDE.md still contains 'dispatch_mode' — removed in V22"
    )


def test_startup_references_agent_memory() -> None:
    """CLAUDE.md ON STARTUP must reference reading agent-memory files.

    HC4 regression — V14/V17/V19 recurrence."""
    content = _read_claude_md()
    assert "agent-memory" in content.lower() or "agent_memory" in content.lower(), (
        "CLAUDE.md ON STARTUP must reference reading .claude/agent-memory/*/MEMORY.md"
    )


def test_claude_md_line_count() -> None:
    """CLAUDE.md must be <= 300 lines (V20 regression, Agent Decomposition Pattern)."""
    lines = CLAUDE_MD.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 300, (
        f"CLAUDE.md is {len(lines)} lines, must be <= 300 (Agent Decomposition Pattern)"
    )


def test_search_verify_model_is_sonnet() -> None:
    """search-verify agent frontmatter must declare model: sonnet (V24 tier promotion)."""
    import re
    agent_path = PROJECT_ROOT / ".claude" / "agents" / "search-verify.md"
    assert agent_path.exists(), f"search-verify.md not found at {agent_path}"
    content = agent_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, "search-verify.md missing YAML frontmatter"
    frontmatter = match.group(1)
    assert re.search(r"^model:\s*sonnet$", frontmatter, re.MULTILINE), (
        "search-verify agent must declare 'model: sonnet' in YAML frontmatter "
        "(V24 tier promotion -- was haiku in V23)"
    )

"""Tests for orchestration.md structural assertions — V25 Layer 2 + Layer 3.

Grep-based tests that verify orchestration.md contains specific patterns
for gates, tiered delivery, dispatch counter, compaction recovery,
constraint compliance, context validation, and task ID persistence.

Consolidated into 4 test classes:
- TestPhase1Gates: channel dispatch + commit gate + session-state gate
- TestPhase5Delivery: tiered delivery + task ID persistence
- TestArchitecturalCompliance: constraint compliance + context validation + compaction + settings.local.json
- TestUxProtocol: all 6 UX format rules
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORCHESTRATION_MD = PROJECT_ROOT / "references" / "orchestration.md"
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


def _read_orch() -> str:
    return ORCHESTRATION_MD.read_text(encoding="utf-8")


def _read_claude() -> str:
    return CLAUDE_MD.read_text(encoding="utf-8")


def _phase1_text() -> str:
    content = _read_orch()
    start = content.find("## Phase 1")
    end = content.find("## Phase 2")
    assert start != -1 and end != -1
    return content[start:end]


def _phase5_text() -> str:
    content = _read_orch()
    start = content.find("## Phase 5")
    assert start != -1
    return content[start:]


def _extract_section(content: str, heading: str) -> str:
    """Extract a section from markdown content by heading."""
    start = content.find(heading)
    if start == -1:
        return ""
    # Find the next same-level heading
    level = heading.split(" ")[0]  # e.g., "##"
    rest = content[start + len(heading):]
    next_heading = rest.find(f"\n{level} ")
    if next_heading == -1:
        return content[start:]
    return content[start:start + len(heading) + next_heading]


# ---- Phase 1 Gates (channel dispatch + commit gate + session-state gate) ----

class TestPhase1Gates:
    # -- Channel dispatch --
    def test_phase1_enumerates_all_5_channels(self) -> None:
        """Phase 1 must enumerate all 5 search channels as mandatory dispatches."""
        text = _phase1_text()
        for channel in ("direct-career-pages", "linkedin", "indeed", "builtin", "google-jobs"):
            assert channel in text, f"Phase 1 must enumerate channel '{channel}'"

    def test_channel_dispatch_is_unconditional(self) -> None:
        """Channel dispatch must use unconditional/mandatory language."""
        text = _phase1_text().lower()
        assert "must be dispatched" in text or "mandatory" in text or "unconditional" in text, (
            "Channel dispatch must use mandatory/unconditional language"
        )

    # -- Commit gate --
    def test_phase1_contains_verify_and_commit(self) -> None:
        """Phase 1 must reference verify-and-commit gate-check dispatch."""
        text = _phase1_text()
        assert "verify-and-commit" in text, (
            "Phase 1 must contain 'verify-and-commit' gate-check dispatch"
        )

    def test_verify_and_commit_is_blocking(self) -> None:
        """verify-and-commit must use blocking language."""
        text = _phase1_text()
        idx = text.find("verify-and-commit")
        assert idx != -1
        surrounding = text[max(0, idx - 200):idx + 400]
        assert "MUST pass" in surrounding or "BLOCKING" in surrounding or "blocks progression" in surrounding.lower(), (
            "verify-and-commit gate must use blocking language (MUST pass, BLOCKING, or blocks progression)"
        )

    def test_verify_and_commit_exit_codes(self) -> None:
        """verify-and-commit section must document exit code 1 = retry, exit code 2 = STOP."""
        text = _phase1_text()
        idx = text.find("verify-and-commit")
        assert idx != -1
        surrounding = text[idx:idx + 600]
        assert "exit code 1" in surrounding.lower() or "exit 1" in surrounding.lower(), (
            "verify-and-commit must document exit code 1 = retry"
        )
        assert "exit code 2" in surrounding.lower() or "exit 2" in surrounding.lower(), (
            "verify-and-commit must document exit code 2 = STOP"
        )

    # -- Session-state gate --
    def test_phase1_contains_verify_session_state_written(self) -> None:
        """Phase 1 must reference verify-session-state-written gate-check."""
        text = _phase1_text()
        assert "verify-session-state-written" in text, (
            "Phase 1 must contain 'verify-session-state-written' gate-check dispatch"
        )

    def test_session_state_gate_is_blocking(self) -> None:
        """verify-session-state-written must use blocking language."""
        text = _phase1_text()
        idx = text.find("verify-session-state-written")
        assert idx != -1
        surrounding = text[max(0, idx - 200):idx + 400]
        assert "MUST pass" in surrounding or "BLOCKING" in surrounding or "blocks progression" in surrounding.lower(), (
            "verify-session-state-written gate must use blocking language"
        )


# ---- Phase 5 Delivery (tiered delivery + task ID persistence) ----

class TestPhase5Delivery:
    # -- Tiered delivery --
    def test_phase5_has_brief_generator(self) -> None:
        assert "brief-generator" in _phase5_text()

    def test_phase5_has_digest_email(self) -> None:
        assert "digest-email" in _phase5_text()

    def test_phase5_has_send_email(self) -> None:
        assert "send_email.py" in _phase5_text()

    def test_phase5_has_budget_check(self) -> None:
        text = _phase5_text()
        assert "check-dispatch-budget" in text or "budget" in text.lower(), (
            "Phase 5 must include dispatch budget check"
        )

    def test_phase5_has_briefs_html_conditional(self) -> None:
        text = _phase5_text()
        assert "briefs-html" in text
        assert "budget" in text.lower() or "conditional" in text.lower() or "if budget" in text.lower()

    def test_phase5_has_deferred_logging_with_user_message(self) -> None:
        text = _phase5_text().lower()
        assert "deferred" in text or "skip" in text
        assert "user" in text or "briefs html deferred" in text, (
            "Phase 5 must include user-facing notification when Tier 2 is skipped"
        )

    def test_tiered_delivery_order(self) -> None:
        """Phase 5 tiered delivery steps must appear in correct order."""
        text = _phase5_text()
        pos_brief_gen = text.find("brief-generator")
        pos_digest = text.find("digest-email")
        pos_send = text.find("send_email.py")
        pos_budget = text.lower().find("check-dispatch-budget")
        if pos_budget == -1:
            pos_budget = text.lower().find("budget check")
        pos_briefs_html = text.find("briefs-html")

        assert pos_brief_gen < pos_digest, "brief-generator must come before digest-email"
        assert pos_digest < pos_send, "digest-email must come before send_email.py"
        assert pos_send < pos_budget, "send_email.py must come before budget check"
        assert pos_budget < pos_briefs_html, "budget check must come before briefs-html"

    # -- Task ID persistence --
    def test_orchestration_has_task_id_persistence(self) -> None:
        content = _read_orch().lower()
        assert "task id" in content or "task_id" in content
        assert "active tasks" in content

    # -- body-file enforcement --
    def test_send_email_uses_body_file_not_html(self) -> None:
        """orchestration.md must use --body-file and NOT --html for send_email.py."""
        content = _read_orch()
        assert "--body-file" in content, "send_email.py must use --body-file"
        # Ensure --html flag is not used (V21/V23 recurrence)
        import re
        html_flags = re.findall(r"--html\b", content)
        assert len(html_flags) == 0, "send_email.py must NOT use --html flag (use --body-file instead)"


# ---- Architectural Compliance (compaction + constraints + context + settings.local.json) ----

class TestArchitecturalCompliance:
    # -- Post-compaction recovery --
    def test_orchestration_has_compaction_recovery(self) -> None:
        content = _read_orch()
        assert "compaction" in content.lower()

    def test_compaction_references_session_state(self) -> None:
        content = _read_orch().lower()
        idx = content.find("## post-compaction recovery")
        assert idx != -1, "orchestration.md must have ## Post-Compaction Recovery section"
        surrounding = content[idx:idx + 800]
        assert "session-state" in surrounding

    def test_compaction_has_immediate_status(self) -> None:
        content = _read_orch().lower()
        idx = content.find("## post-compaction recovery")
        assert idx != -1, "orchestration.md must have ## Post-Compaction Recovery section"
        surrounding = content[idx:idx + 800]
        assert "immediate" in surrounding or "1-2 sentence" in surrounding

    def test_claude_md_has_compaction_rule(self) -> None:
        content = _read_claude().lower()
        assert "compaction" in content

    # -- Constraint compliance (HC-5, HC-10, CR-7, CR-12, git pull) --
    def test_hc5_list_active_role_types_in_parent_allowed(self) -> None:
        content = _read_claude()
        budget_start = content.find("## Context Budget")
        if budget_start == -1:
            budget_start = content.find("Parent-allowed")
        assert budget_start != -1
        section = content[budget_start:budget_start + 1000]
        assert "list-active-role-types" in section

    def test_hc10_dispatch_templates_have_mandatory_vars(self) -> None:
        content = _read_orch()
        for var in ("working_dir", "output_directory", "dashboard_url"):
            assert var in content, f"orchestration.md must include '{var}' (HC-10)"

    def test_cr7_absolute_file_paths_reminder(self) -> None:
        content = _read_orch().lower()
        assert "absolute" in content and ("file path" in content or "absolute path" in content)

    def test_cr12_post_dispatch_directory_verification(self) -> None:
        content = _read_orch().lower()
        assert "post-dispatch" in content or ("verify" in content and "directory" in content)

    def test_startup_git_pull_before_preflight(self) -> None:
        content = _read_claude()
        startup_start = content.find("## ON STARTUP")
        assert startup_start != -1
        startup_section = content[startup_start:startup_start + 800]
        assert "git pull" in startup_section

    def test_settings_local_json_merge_rule(self) -> None:
        """orchestration.md must contain settings.local.json additive merge rule."""
        content = _read_orch().lower()
        assert "settings.local.json" in content
        assert "merge" in content or "additive" in content

    # -- Context.md target format validation --
    def test_orchestration_validates_target_format(self) -> None:
        content = _read_orch()
        assert "list-active-role-types" in content
        lower = content.lower()
        assert "verify" in lower and ("slug" in lower or "role type" in lower)

    # -- Foreground-only dispatch rule (V23) --
    def test_foreground_only_dispatch_rule(self) -> None:
        """orchestration.md or CLAUDE.md must prohibit background subagent dispatches."""
        orch = _read_orch().lower()
        claude = _read_claude().lower()
        combined = orch + claude
        assert "foreground" in combined or "background" in combined, (
            "Must contain explicit foreground-only or background-prohibition rule"
        )

    def test_vercel_deploy_after_push(self) -> None:
        """orchestration.md must contain mandatory Vercel deploy step after push."""
        content = _read_orch().lower()
        assert "vercel" in content, "orchestration.md must reference Vercel deploy"
        assert "vercel --prod" in content or "vercel deploy" in content, (
            "orchestration.md must contain vercel --prod deploy command"
        )


# ---------------------------------------------------------------------------
# Layer 3 — UX Protocol (all format rules in single class)
# ---------------------------------------------------------------------------


class TestUxProtocol:
    def test_ux_brief_progress_format(self) -> None:
        """orchestration.md UX Protocol must contain one-liner brief progress format."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "Brief {N}/{total} done" in section, (
            "UX Protocol must contain brief progress format: "
            "'Brief {N}/{total} done — {company name}'"
        )
        assert "{company name}" in section or "{company}" in section

    def test_ux_timed_status_format(self) -> None:
        """orchestration.md UX Protocol must contain proactive timed status format."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "Still running: {N}/{total} complete" in section

    def test_ux_post_compaction_immediate_status(self) -> None:
        """orchestration.md UX Protocol must require immediate status after compaction."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        lower = section.lower()
        assert "compaction" in lower
        assert "1-2 sentence summary" in lower

    def test_ux_unified_numbered_selection(self) -> None:
        """orchestration.md UX Protocol must require single numbered list across role types."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        lower = section.lower()
        assert "single numbered list" in lower or "unified numbered" in lower

    def test_ux_section_headers_with_counts(self) -> None:
        """orchestration.md UX Protocol must contain section header format with counts."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "{Role Type} ({N} new, {M} active)" in section

    def test_ux_one_question_at_a_time(self) -> None:
        """orchestration.md UX Protocol must contain one-question-at-a-time rule (CR-4)."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        lower = section.lower()
        assert "one question" in lower, (
            "UX Protocol must contain one-question-at-a-time rule (CR-4)"
        )

    def test_ux_gate_failure_alert_format(self) -> None:
        """orchestration.md UX Protocol must contain gate failure alert format."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "[GATE FAILED]" in section, (
            "UX Protocol must contain gate failure alert format: "
            "'[GATE FAILED] {gate-name} — {reason}. Action: {what happens next}.'"
        )

    def test_ux_session_resume_prompt_format(self) -> None:
        """orchestration.md UX Protocol must contain session resume prompt format."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "resume" in section.lower() and "abort" in section.lower(), (
            "UX Protocol must contain session resume prompt format with resume/abort options"
        )

    def test_ux_end_of_session_completion_summary(self) -> None:
        """orchestration.md UX Protocol must contain end-of-session completion summary format."""
        content = _read_orch()
        section = _extract_section(content, "## UX Protocol")
        assert "Session complete" in section or "session complete" in section.lower(), (
            "UX Protocol must contain end-of-session completion summary format"
        )

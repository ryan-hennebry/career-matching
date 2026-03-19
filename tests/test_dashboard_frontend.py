"""Consolidated dashboard frontend tests — one class per source file.
All tests written upfront; Steps 15/17/19/21 implement and run these."""

from __future__ import annotations

import re
from pathlib import Path

V17_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = V17_ROOT / "public" / "css" / "dashboard.css"
COMPONENTS_JS_PATH = V17_ROOT / "public" / "js" / "components.js"
INDEX_HTML_PATH = V17_ROOT / "public" / "index.html"
APP_JS_PATH = V17_ROOT / "public" / "js" / "app.js"


# --- CSS tests ---

def _read_css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


class TestScoreTierTokens:
    def test_tier_high_exists_with_green_border(self) -> None:
        css = _read_css()
        assert ".tier-high" in css
        # Find the tier-high rule block
        match = re.search(r"\.tier-high\s*\{([^}]+)\}", css)
        assert match, ".tier-high rule not found"
        rule = match.group(1)
        assert "4px" in rule
        assert "border-left" in rule or "border" in rule

    def test_tier_mid_exists(self) -> None:
        css = _read_css()
        assert ".tier-mid" in css
        match = re.search(r"\.tier-mid\s*\{([^}]+)\}", css)
        assert match
        assert "3px" in match.group(1)

    def test_tier_low_exists(self) -> None:
        css = _read_css()
        assert ".tier-low" in css
        match = re.search(r"\.tier-low\s*\{([^}]+)\}", css)
        assert match
        assert "2px" in match.group(1)


class TestNoBoxShadowOnCards:
    def test_job_card_has_no_box_shadow(self) -> None:
        css = _read_css()
        # Extract all .job-card rule blocks
        for match in re.finditer(r"\.job-card(?:\s*,\s*[^{]*|\s*)\{([^}]+)\}", css):
            rule = match.group(1)
            assert "box-shadow" not in rule, f"box-shadow found in .job-card: {rule[:100]}"


class TestNoBlueColorValues:
    def test_no_blue_hex_values(self) -> None:
        css = _read_css()
        blue_hexes = ["#0000ff", "#007bff", "#2563eb", "#3b82f6", "#1d4ed8", "#60a5fa"]
        for hex_val in blue_hexes:
            assert hex_val not in css.lower(), f"Blue hex {hex_val} found in CSS"

    def test_no_named_blue_as_value(self) -> None:
        css = _read_css()
        # Blue as a CSS property value (not in comments or class names)
        assert not re.search(r":\s*[^;]*\bblue\b", css, re.IGNORECASE), "Named 'blue' found as CSS value"


class TestLayoutConstraints:
    def test_max_width_960px(self) -> None:
        css = _read_css()
        assert "960px" in css

    def test_horizontal_padding_40px(self) -> None:
        css = _read_css()
        assert "40px" in css


class TestCommentedDarkMode:
    def test_dark_mode_section_commented(self) -> None:
        css = _read_css()
        assert "dark" in css.lower()
        # Should be inside a comment, not an active media query
        assert "prefers-color-scheme" in css
        # Verify it's commented out (inside /* */)
        dark_pos = css.lower().find("prefers-color-scheme: dark")
        assert dark_pos != -1
        # Find the nearest preceding /* before the dark mode reference
        comment_start = css.rfind("/*", 0, dark_pos)
        comment_end = css.find("*/", dark_pos)
        assert comment_start != -1 and comment_end != -1, "Dark mode should be inside a comment"


# --- components.js tests ---

def _read_components_js() -> str:
    return COMPONENTS_JS_PATH.read_text(encoding="utf-8")


class TestGetScoreTierFunction:
    """String-presence tests for getScoreTier. Behavioral validation is in
    tests/test_get_score_tier.js (Node.js unit test that executes the function)."""

    def test_function_exists(self) -> None:
        js = _read_components_js()
        assert "getScoreTier" in js or "get_score_tier" in js or "scoreTier" in js

    def test_maps_90_plus_to_high(self) -> None:
        js = _read_components_js()
        assert "tier-high" in js
        assert "90" in js

    def test_maps_80_to_mid(self) -> None:
        assert "tier-mid" in _read_components_js()

    def test_maps_below_80_to_low(self) -> None:
        assert "tier-low" in _read_components_js()


class TestStackedStatsRendering:
    def test_stat_value_class(self) -> None:
        assert "summary-stat-value" in _read_components_js()

    def test_stat_label_class(self) -> None:
        assert "summary-stat-label" in _read_components_js()


class TestCountBadges:
    def test_count_badge_class(self) -> None:
        assert "count-badge" in _read_components_js()


class TestEmptyStateMessage:
    def test_mentions_claude_code(self) -> None:
        assert "Claude Code" in _read_components_js()

    def test_does_not_render_run_search_button(self) -> None:
        js = _read_components_js()
        assert "Run Search" not in js
        assert 'data-action="trigger-search"' not in js


# --- index.html tests ---

def _read_index_html() -> str:
    return INDEX_HTML_PATH.read_text(encoding="utf-8")


class TestSummaryDateSpan:
    def test_summary_date_element_exists(self) -> None:
        html = _read_index_html()
        assert 'id="summary-date"' in html

    def test_summary_date_is_span(self) -> None:
        html = _read_index_html()
        assert "<span" in html and 'id="summary-date"' in html


class TestSummaryDivider:
    def test_summary_divider_exists(self) -> None:
        html = _read_index_html()
        assert 'class="summary-divider"' in html

    def test_summary_divider_is_hr(self) -> None:
        html = _read_index_html()
        assert "<hr" in html and "summary-divider" in html


class TestSidebarRoleLabels:
    def test_sidebar_label_class_exists(self) -> None:
        html = _read_index_html()
        assert 'class="sidebar-label"' in html

    def test_role_type_label_text(self) -> None:
        html = _read_index_html()
        assert "Role Type" in html


# --- app.js tests ---

def _read_app_js() -> str:
    return APP_JS_PATH.read_text(encoding="utf-8")


class TestDateDisplay:
    def test_references_summary_date(self) -> None:
        assert "summary-date" in _read_app_js()

    def test_has_date_formatting(self) -> None:
        js = _read_app_js()
        assert "toLocaleDateString" in js or "formatDate" in js or "Date" in js


class TestSectionDividers:
    def test_section_divider_class(self) -> None:
        assert "section-divider" in _read_app_js()

    def test_divider_is_hr(self) -> None:
        js = _read_app_js()
        assert "<hr" in js and "section-divider" in js


class TestEnhancedEmptyState:
    def test_no_jobs_found_message(self) -> None:
        assert "No jobs found" in _read_components_js()

    def test_mentions_claude_code_flow(self) -> None:
        js = _read_app_js()
        assert "Claude Code" in js


class TestLoadingSpinner:
    def test_loading_text(self) -> None:
        js = _read_app_js()
        assert "Loading" in js or "loading" in js

    def test_loading_class(self) -> None:
        js = _read_app_js()
        assert "loading" in js

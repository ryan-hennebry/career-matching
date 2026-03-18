"""Tests for verify_html.py CSS-context-aware color detection."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

VERIFY_HTML = Path(__file__).resolve().parent.parent / "scripts" / "verify_html.py"


def _check_html(html_content: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html_content)
        f.flush()
        return subprocess.run(
            ["python3", str(VERIFY_HTML), f.name],
            capture_output=True,
            text=True,
        )


class TestDetectsInlineStyleColors:
    def test_flags_red_hex_in_style_attr(self) -> None:
        result = _check_html('<div style="color: #ff0000">text</div>')
        assert result.returncode == 1

    def test_flags_blue_hex_in_style_attr(self) -> None:
        result = _check_html('<div style="color: #2563eb">text</div>')
        assert result.returncode == 1

    def test_flags_named_red_in_style_attr(self) -> None:
        result = _check_html('<div style="color: red">text</div>')
        assert result.returncode == 1

    def test_flags_named_blue_in_style_attr(self) -> None:
        result = _check_html('<div style="background-color: blue">text</div>')
        assert result.returncode == 1


class TestDetectsStyleBlockColors:
    def test_flags_red_in_style_block(self) -> None:
        result = _check_html("<style>.foo { color: #ff0000; }</style>")
        assert result.returncode == 1

    def test_flags_amber_in_style_block(self) -> None:
        result = _check_html("<style>.foo { color: #f59e0b; }</style>")
        assert result.returncode == 1

    def test_flags_orange_in_style_block(self) -> None:
        result = _check_html("<style>.foo { color: orange; }</style>")
        assert result.returncode == 1


class TestDoesNotFlagPlainText:
    def test_preferred_in_text(self) -> None:
        result = _check_html("<p>This is a preferred candidate</p>")
        assert result.returncode == 0

    def test_credible_in_text(self) -> None:
        result = _check_html("<p>A credible source of information</p>")
        assert result.returncode == 0

    def test_prepared_in_text(self) -> None:
        result = _check_html("<p>Well prepared for the interview</p>")
        assert result.returncode == 0

    def test_red_in_text_content(self) -> None:
        result = _check_html("<p>The red team exercise was successful</p>")
        assert result.returncode == 0


class TestDoesNotFlagCSSClassNames:
    def test_class_with_red_substring(self) -> None:
        result = _check_html('<div class="bg-red-500">text</div>')
        assert result.returncode == 0

    def test_class_with_blue_substring(self) -> None:
        result = _check_html('<div class="text-blue-600">text</div>')
        assert result.returncode == 0


class TestCleanHTMLPasses:
    def test_clean_html_returns_zero(self) -> None:
        result = _check_html("""
        <html><head><style>
        .job-card { border: 1px solid #e5e0db; color: #1a1613; }
        </style></head><body>
        <div class="job-card" style="border-left: 4px solid #22c55e">
            <p>A preferred candidate who is well prepared</p>
        </div></body></html>
        """)
        assert result.returncode == 0

    def test_warm_palette_colors_allowed(self) -> None:
        result = _check_html('<div style="color: #1a1613; background: #faf8f5">ok</div>')
        assert result.returncode == 0

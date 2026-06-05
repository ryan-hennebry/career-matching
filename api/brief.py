"""GET /api/brief?key=... — Render individual brief as HTML.

Brief format lookup order:
1. Individual markdown file: output/briefs/{slug}-brief.md (rendered to HTML via markdown lib)
2. Consolidated HTML file: output/briefs/briefs-YYYY-MM-DD.html (returned as-is, contains all briefs)

The briefs-html subagent generates a consolidated HTML file. Individual markdown briefs
may also exist if the brief-generator subagent ran. The API tries individual first,
then falls back to consolidated."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._files import _get_base_dir, read_text
from api._response import json_response


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        key = params.get("key", [None])[0]

        if not key:
            json_response(self, {"error": "key parameter required"}, 400)
            return

        # key format: role-type-slug/company-slug-title-slug
        # Brief filename: company-slug-title-slug-brief.md
        slug = key.split("/", 1)[-1] if "/" in key else key

        # Strategy 1: Individual markdown brief
        brief_md = read_text(f"output/briefs/{slug}-brief.md")
        if brief_md:
            try:
                import markdown
                html = markdown.markdown(brief_md, extensions=["tables", "fenced_code"])
            except ImportError:
                html = f"<pre>{brief_md}</pre>"

            json_response(self, {"key": key, "html": html, "format": "individual_md"})
            return

        # Strategy 2: Consolidated HTML file (briefs-YYYY-MM-DD.html)
        briefs_dir = _get_base_dir() / "output" / "briefs"
        if briefs_dir.exists():
            html_files = sorted(briefs_dir.glob("briefs-*.html"), reverse=True)
            if html_files:
                consolidated_html = html_files[0].read_text(encoding="utf-8")
                json_response(self, {"key": key, "html": consolidated_html, "format": "consolidated_html"})
                return

        json_response(self, {"error": "brief not found"}, 404)

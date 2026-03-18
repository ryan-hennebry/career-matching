"""GET /api/context — Profile section names from context.md.

Returns section NAMES by default (no content, no raw text — protects PII).
Use ?sections=Profile,Target to return specific section content.
Never serves the full raw context.md text."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._files import read_text
from api._response import json_response


def parse_context_sections(text: str) -> dict[str, str]:
    """Extract sections from context.md as {name: content}."""
    sections = {}
    current_section = None
    current_content = []

    for line in text.split("\n"):
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        text = read_text("context.md")

        if not text:
            json_response(self, {"error": "context.md not found"}, 404)
            return

        all_sections = parse_context_sections(text)

        # Check if specific sections are requested
        params = parse_qs(urlparse(self.path).query)
        requested = params.get("sections", [None])[0]

        if requested:
            # Return content for requested sections only
            requested_names = [s.strip() for s in requested.split(",")]
            result = {
                "sections": {name: all_sections.get(name, "") for name in requested_names if name in all_sections},
                "available": list(all_sections.keys()),
            }
        else:
            # Default: return section names only (no content, no raw text)
            result = {
                "available": list(all_sections.keys()),
            }

        json_response(self, result)

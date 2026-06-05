"""POST /api/run — Trigger GitHub Actions search (authenticated).
GET /api/run — Poll workflow run status (public).

Security: POST requires Authorization: Bearer {JSA_RUN_SECRET} header.
GET is unauthenticated (read-only status polling)."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen

from api._response import cors_preflight, json_response


GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GITHUB_PAT = os.environ.get("GITHUB_PAT", "")
JSA_RUN_SECRET = os.environ.get("JSA_RUN_SECRET", "")
WORKFLOW_FILE = "jsa-search.yml"


class handler(BaseHTTPRequestHandler):
    def _check_auth(self) -> bool:
        """Verify Bearer token matches JSA_RUN_SECRET. Returns True if authorized."""
        if not JSA_RUN_SECRET:
            # No secret configured — reject all POST requests
            return False
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {JSA_RUN_SECRET}"

    def do_POST(self):
        if not self._check_auth():
            json_response(self, {"error": "unauthorized"}, 403)
            return

        if not all([GITHUB_OWNER, GITHUB_REPO, GITHUB_PAT]):
            json_response(self, {"error": "GitHub not configured"}, 503)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length))
        role_types = body.get("role_types", [])

        if not role_types:
            json_response(self, {"error": "role_types required"}, 400)
            return

        # Dispatch GitHub Actions workflow
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
        payload = json.dumps({
            "ref": "main",
            "inputs": {"role_types": ",".join(role_types)},
        }).encode()

        req = Request(url, data=payload, method="POST")
        req.add_header("Authorization", f"Bearer {GITHUB_PAT}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Content-Type", "application/json")

        try:
            resp = urlopen(req)
            if resp.status == 204:
                json_response(self, {"ok": True, "message": "Workflow dispatched"})
            else:
                json_response(self, {"error": f"GitHub returned {resp.status}"}, resp.status)
        except Exception as e:
            json_response(self, {"error": str(e)}, 500)

    def do_GET(self):
        """GET /api/run — poll latest workflow run status."""
        if not all([GITHUB_OWNER, GITHUB_REPO, GITHUB_PAT]):
            json_response(self, {"error": "GitHub not configured"}, 503)
            return

        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/runs?per_page=1"
        req = Request(url)
        req.add_header("Authorization", f"Bearer {GITHUB_PAT}")
        req.add_header("Accept", "application/vnd.github+json")

        try:
            resp = urlopen(req)
            data = json.loads(resp.read())
            runs = data.get("workflow_runs", [])
            if runs:
                run = runs[0]
                result = {
                    "status": run.get("status"),
                    "conclusion": run.get("conclusion"),
                    "created_at": run.get("created_at"),
                    "updated_at": run.get("updated_at"),
                    "html_url": run.get("html_url"),
                }
            else:
                result = {"status": "none", "message": "No workflow runs found"}

            json_response(self, result)
        except Exception as e:
            json_response(self, {"error": str(e)}, 500)

    def do_OPTIONS(self):
        cors_preflight(self)

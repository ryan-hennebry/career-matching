"""GET /api/job?key=... — Single job detail."""

from __future__ import annotations

import re
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._files import read_json
from api._response import json_response
from api._upstash import get_redis, get_user_action_for_job

# Validates key format: role-type-slug/company-slug-title-slug (lowercase alphanumeric + hyphens only)
_KEY_PATTERN = re.compile(r"^[a-z0-9-]+/[a-z0-9-]+$")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        key = params.get("key", [None])[0]

        if not key:
            json_response(self, {"error": "key parameter required"}, 400)
            return

        # Path traversal protection: validate key matches expected format
        if not _KEY_PATTERN.match(key):
            json_response(self, {"error": "invalid key format"}, 400)
            return

        # key format: role-type-slug/company-slug-title-slug
        job = read_json(f"output/verified/{key}.json")
        if not job:
            json_response(self, {"error": "job not found"}, 404)
            return

        # Get user action from Upstash, falling back to state.json
        redis = get_redis()
        user_action = get_user_action_for_job(redis, key)

        job["_key"] = key
        job["user_action"] = user_action

        json_response(self, job)

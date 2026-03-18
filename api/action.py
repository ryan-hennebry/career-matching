"""POST /api/action — Write user action to Upstash Redis."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from api._response import cors_preflight, json_response
from api._upstash import get_redis

VALID_ACTIONS = {"accepted", "rejected", "brief_requested"}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            json_response(self, {"error": "invalid JSON"}, 400)
            return

        key = data.get("key")
        action = data.get("action")

        if not key or not action:
            json_response(self, {"error": "key and action required"}, 400)
            return

        if action not in VALID_ACTIONS:
            json_response(self, {"error": f"invalid action: {action}"}, 400)
            return

        redis = get_redis()
        if not redis:
            json_response(self, {"error": "Redis not configured"}, 503)
            return

        try:
            redis.set(f"action:{key}", action)
        except Exception as e:
            json_response(self, {"error": str(e)}, 500)
            return

        json_response(self, {"ok": True, "key": key, "action": action})

    def do_OPTIONS(self):
        cors_preflight(self)

"""GET /api/state — Summary counts for dashboard header."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler

from api._files import list_verified_jobs, read_delta_json, read_state_json
from api._response import json_response
from api._upstash import get_redis, get_user_actions
from api.jobs import derive_stage


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        delta = read_delta_json()
        state = read_state_json()
        jobs = list_verified_jobs()

        redis = get_redis()
        actions = get_user_actions(redis)

        counts = {
            "new": 0,
            "reviewing": 0,
            "brief_requested": 0,
            "applied": 0,
            "rejected": 0,
            "expired": 0,
            "total_jobs": len(jobs),
        }

        new_keys = set(delta.get("new_jobs", []))
        expired_keys = set(state.get("expired_jobs", {}).keys())
        last_run = state.get("last_run_date", "")

        for job in jobs:
            key = job.get("_key", "")
            action = actions.get(key)
            stage = derive_stage(key, action, new_keys, expired_keys)
            counts[stage] += 1

        json_response(self, {
            "run_date": last_run,
            "counts": counts,
        })

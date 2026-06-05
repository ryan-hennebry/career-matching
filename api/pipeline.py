"""GET /api/pipeline — Jobs grouped by pipeline stage."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler

from api._files import list_verified_jobs, read_delta_json, read_state_json
from api._response import json_response
from api._upstash import get_redis, get_user_actions
from api.jobs import derive_stage


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        jobs = list_verified_jobs()
        delta = read_delta_json()
        state = read_state_json()

        redis = get_redis()
        actions = get_user_actions(redis)

        new_keys = set(delta.get("new_jobs", []))
        expired_keys = set(state.get("expired_jobs", {}).keys())

        pipeline = {}
        for job in jobs:
            key = job.get("_key", "")
            action = actions.get(key)
            stage = derive_stage(key, action, new_keys, expired_keys)

            if stage not in pipeline:
                pipeline[stage] = {"count": 0, "jobs": []}

            pipeline[stage]["count"] += 1
            pipeline[stage]["jobs"].append({
                "key": key,
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "score": job.get("score", 0),
                "location": job.get("location", ""),
            })

        # Sort jobs within each stage by score descending
        for stage_data in pipeline.values():
            stage_data["jobs"].sort(key=lambda j: j["score"], reverse=True)

        json_response(self, pipeline)

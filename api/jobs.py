"""GET /api/jobs — Job list with scores and pipeline stages."""

from __future__ import annotations

import json
import traceback
from http.server import BaseHTTPRequestHandler

from api._files import list_verified_jobs, read_delta_json, read_state_json
from api._response import json_response
from api._upstash import get_redis, get_user_actions


def _extract_score(job: dict) -> int:
    """Extract score from verified JSON, handling multiple schema formats."""
    # 1. Try score_breakdown.total
    sb = job.get("score_breakdown")
    if isinstance(sb, dict) and "total" in sb:
        try:
            return int(sb["total"])
        except (ValueError, TypeError):
            pass
    # 2. Try scoring.total_score (direct-career-pages, web-search-discovery)
    scoring = job.get("scoring")
    if isinstance(scoring, dict) and "total_score" in scoring:
        try:
            return int(scoring["total_score"])
        except (ValueError, TypeError):
            pass
    # 3. Try top-level score
    score = job.get("score")
    if isinstance(score, (int, float)):
        return int(score)
    if isinstance(score, dict) and "total" in score:
        try:
            return int(score["total"])
        except (ValueError, TypeError):
            pass
    return 0


def derive_stage(key: str, action: str | None, new_keys: set, expired_keys: set) -> str:
    """Derive pipeline stage for a job.

    Priority: expired > rejected > applied > brief_requested > new > reviewing.
    If a job has both an expired status and a user action, expired wins
    (user can re-find via new search).
    """
    if key in expired_keys:
        return "expired"
    if action == "rejected":
        return "rejected"
    if action == "accepted":
        return "applied"
    if action == "brief_requested":
        return "brief_requested"
    if key in new_keys:
        return "new"
    return "reviewing"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            jobs = list_verified_jobs()
            delta = read_delta_json()
            state = read_state_json()

            redis = get_redis()
            actions = get_user_actions(redis)

            new_keys = set(delta.get("new_jobs", []))
            expired_keys = set(state.get("expired_jobs", {}).keys())

            result = []
            for job in jobs:
                key = job.get("_key", "")
                action = actions.get(key)
                stage = derive_stage(key, action, new_keys, expired_keys)

                result.append({
                    "key": key,
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "score": _extract_score(job),
                    "source": job.get("source", ""),
                    "job_url": job.get("job_url"),
                    "role_type": job.get("_role_type", ""),
                    "stage": stage,
                    "user_action": action,
                    "date_posted": job.get("date_posted"),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "currency": job.get("currency"),
                })

            result.sort(key=lambda j: j["score"], reverse=True)

            json_response(self, result)
        except Exception as e:
            json_response(self, {"error": str(e), "trace": traceback.format_exc()}, status=500)

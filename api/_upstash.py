"""Shared Upstash Redis helper for all API functions."""

from __future__ import annotations

import os
from typing import Any

from api._files import read_state_json


def get_redis():
    """Get Upstash Redis client. Returns None if credentials not set."""
    try:
        from upstash_redis import Redis
    except ImportError:
        return None

    url = os.environ.get("UPSTASH_REDIS_REST_URL")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

    if not url or not token:
        return None

    return Redis(url=url, token=token)


def _actions_from_state_json() -> dict[str, str]:
    """Extract user actions from state.json as fallback when Upstash is unavailable.

    Returns {job_key: action} for all jobs that have a non-null user_action.
    """
    state = read_state_json()
    actions = {}
    for key, job_data in state.get("jobs", {}).items():
        action = job_data.get("user_action")
        if action:
            actions[key] = action
    return actions


def get_user_actions(redis) -> dict[str, str]:
    """Get all user actions from Redis, falling back to state.json.

    Uses keys() + mget() for 2 round-trips total (instead of N+1).
    Note: keys("action:*") is an O(N) scan of the Upstash keyspace.
    For the current scale (~100 jobs) this is fine. If the keyspace grows
    to 10K+ keys, migrate to a Redis hash (HGETALL jsa:actions) instead.

    Fallback: if Redis is unavailable or returns no actions, reads
    user_action fields from state.json instead.
    """
    if redis is None:
        return _actions_from_state_json()

    try:
        keys = redis.keys("action:*")
        if not keys:
            return _actions_from_state_json()
        # Batch fetch all values in a single mget() call
        values = redis.mget(*keys)
        actions = {}
        for key, val in zip(keys, values):
            if val:
                job_key = key.replace("action:", "", 1)
                actions[job_key] = val
        if not actions:
            return _actions_from_state_json()
        return actions
    except Exception:
        return _actions_from_state_json()


def get_user_action_for_job(redis, job_key: str) -> str | None:
    """Get user action for a single job, falling back to state.json.

    Used by the single-job detail endpoint.
    """
    if redis:
        try:
            action = redis.get(f"action:{job_key}")
            if action:
                return action
        except Exception:
            pass

    # Fallback: check state.json
    state = read_state_json()
    job_data = state.get("jobs", {}).get(job_key, {})
    return job_data.get("user_action")

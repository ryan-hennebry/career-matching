"""Validate the manifest and the exact set of records eligible for publication."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

POLICY = "references/matching-policy.md"
ROOT = Path(__file__).resolve().parents[1]
REVIEW_STATUSES = {"fetched", "parsed", "assessed", "assessed-provisional", "incomplete", "pending"}
REVIEWED = {"assessed", "assessed-provisional"}
LIVE = {"live", "active", "open", "confirmed", "verified"}
ACTIONABLE = {"apply_now", "apply_if_time"}


def iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("expected YYYY-MM-DD")
    return date.fromisoformat(value)


def evidence_date(value):
    if isinstance(value, str) and "T" in value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    return iso_date(value)


def read_object(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    return data


def web_url(value):
    if not isinstance(value, str) or any(c.isspace() or c in '\\<>"' for c in value):
        return False
    try:
        url = urlsplit(value)
        return url.scheme in {"http", "https"} and bool(url.hostname) and url.username is None
    except ValueError:
        return False


def _record_paths(items):
    if not isinstance(items, list):
        raise ValueError("expected a list of records/ paths")
    if not all(isinstance(p, str) and re.fullmatch(r"records/[a-zA-Z0-9_-]+\.json", p) for p in items):
        raise ValueError("expected safe, relative records/<name>.json paths")
    if len(set(items)) != len(items):
        raise ValueError("duplicate record path")
    return items


def _presentation_problems(record, run_date):
    from manage_state import _is_specific_job_url

    for field in ("company", "exact_title", "central_work"):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            yield f"missing or blank {field}"
    status = record.get("review_status")
    disposition = record.get("disposition")
    if status not in REVIEWED:
        yield f"review_status {status!r} is not assessed or assessed-provisional"
    if disposition not in ACTIONABLE:
        yield f"disposition {disposition!r} is not actionable"
    if status == "assessed-provisional" and disposition == "apply_now":
        yield "assessed-provisional record cannot have disposition apply_now"
    if str(record.get("active_status", "")).strip().lower() not in LIVE:
        yield "active_status is not confirmed live"
    try:
        checked = evidence_date(record.get("checked_at"))
        if run_date is not None and checked != run_date:
            yield "checked_at must be the run date"
    except (TypeError, ValueError):
        yield "missing checked_at or invalid date"
    if not web_url(record.get("url")) or not _is_specific_job_url(record["url"]):
        yield "url is not a specific job URL"
    eligibility = record.get("practical_eligibility")
    if eligibility not in ("eligible", "conditional"):
        yield "practical_eligibility is not eligible/conditional"
    if eligibility == "conditional" and disposition == "apply_now":
        yield "conditional eligibility cannot have disposition apply_now"


def validate_run(manifest_path, *, today=None, max_age_days=2):
    """Return a machine-readable result and the validated presentation records in order."""
    problems = []
    result = {
        "passed": False,
        "violations": problems,
        "records_checked": 0,
        "presented": 0,
        "zero_recommendations": False,
        "title_rule_rejections": 0,
    }

    try:
        manifest = read_object(manifest_path)
    except (OSError, ValueError) as error:
        problems.append(f"manifest missing or unreadable ({error})")
        return result, []

    run_date = None
    try:
        run_date = iso_date(manifest.get("run_date"))
        current_date = iso_date(today) if today is not None else date.today()
        age = (current_date - run_date).days
        if age < 0:
            problems.append("manifest run_date is in the future")
        if age > max_age_days:
            problems.append(f"manifest stale: {age} days old (max {max_age_days})")
    except ValueError:
        problems.append("manifest run_date or comparison date is missing or invalid")

    if manifest.get("completed") is not True:
        problems.append("run not completed (completed is not true)")
    if not isinstance(manifest.get("run_id"), str) or not manifest["run_id"].strip():
        problems.append("manifest run_id must be a nonblank string")
    if not isinstance(manifest.get("coverage"), dict):
        problems.append("manifest coverage must be an object")
    if manifest.get("policy") != POLICY or not (ROOT / POLICY).is_file():
        problems.append("policy file missing or unexpected")

    try:
        expected = _record_paths(manifest.get("expected_records"))
        presentation = _record_paths(manifest.get("presentation_set"))
    except ValueError as error:
        problems.append(f"invalid expected_records or presentation_set: {error}")
        return result, []

    presented = set(presentation)
    result["presented"] = len(presentation)
    for rel in sorted(presented.difference(expected)):
        problems.append(f"presentation item not in expected_records: {rel}")
    main = manifest.get("main_set")
    if main is not None:
        try:
            main = _record_paths(main)
            if len(main) > 10 or not set(main).issubset(presented):
                problems.append("main_set must be a subset of presentation_set, with at most 10 records")
        except ValueError as error:
            problems.append(f"invalid main_set: {error}")

    base = manifest_path.parent.resolve()
    selected = {}
    for rel in expected:
        path = base / rel
        try:
            if path.resolve() != path:
                raise ValueError("record may not be a symlink or resolve outside the run")
            record = read_object(path)
        except (OSError, RuntimeError, ValueError) as error:
            problems.append(f"{rel}: expected record missing or unreadable ({error})")
            continue

        result["records_checked"] += 1
        status, disposition = record.get("review_status"), record.get("disposition")
        if not isinstance(status, str) or status not in REVIEW_STATUSES:
            problems.append(f"{rel}: unknown review_status {status!r}")
            continue
        if disposition is not None and not isinstance(disposition, str):
            problems.append(f"{rel}: invalid disposition")
            continue
        previous = record.get("previous_disposition")
        reason = record.get("change_reason")
        if previous and previous != disposition and (not isinstance(reason, str) or not reason.strip()):
            problems.append(f"{rel}: disposition changed without change_reason")
        if status == "incomplete" and disposition not in {None, "", "pending", "incomplete"}:
            problems.append(f"{rel}: incomplete record has a verdict")
        if disposition == "skip" and rel not in presented:
            if record.get("review_method") == "title_rule":
                result["title_rule_rejections"] += 1
            elif status not in REVIEWED:
                problems.append(f"{rel}: rejection needs an assessed record or a title_rule")
        if rel in presented:
            problems.extend(f"{rel}: {p}" for p in _presentation_problems(record, run_date))
            selected[rel] = record

    result["passed"] = not problems
    result["zero_recommendations"] = result["passed"] and not presentation
    records = [selected[rel] for rel in presentation] if result["passed"] else []
    return result, records

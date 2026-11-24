"""Normalize bounded discovery from employer boards and reviewed local snapshots."""

from __future__ import annotations

import hashlib
import json
from html import unescape
import re
from collections import defaultdict
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from run_validation import evidence_date, iso_date, read_object, web_url

ENDPOINTS = {
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{board}",
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true",
}
MAX_RESPONSE_BYTES = 10 * 1024 * 1024


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class _JobText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def _text(value):
    return value.strip() if isinstance(value, str) else ""


def _job_text(value):
    parser = _JobText()
    parser.feed(unescape(_text(value)))
    parser.close()
    return " ".join(" ".join(parser.parts).split())


def _date_text(value):
    try:
        return evidence_date(value).isoformat()
    except (TypeError, ValueError):
        return None


def _key(*parts):
    raw = json.dumps(parts, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def _normalized(value):
    return " ".join(value.casefold().split())


def _normalize(job, provider, company, observed):
    if not isinstance(job, dict):
        raise ValueError("every posting must be an object")
    if provider == "ashby":
        url = _text(job.get("jobUrl"))
        active = job.get("isListed") is not False
        location = _text(job.get("location"))
        description = _text(job.get("descriptionPlain")) or _job_text(job.get("descriptionHtml"))
        dates = [("publication", job.get("publishedAt"))]
    elif provider == "greenhouse":
        url = _text(job.get("absolute_url"))
        active = True
        location_object = job.get("location")
        location = _text(location_object.get("name")) if isinstance(location_object, dict) else ""
        description = _job_text(job.get("content"))
        dates = [("updated", job.get("updated_at")), ("publication", job.get("first_published"))]
    else:
        url = _text(job.get("url"))
        active = job.get("active") is True
        location = _text(job.get("location"))
        description = _text(job.get("description"))
        dates = [(kind, job.get(kind)) for kind in ("original_publication", "publication", "updated")]

    from manage_state import _is_specific_job_url

    title = _text(job.get("title"))
    if not title or not web_url(url) or not _is_specific_job_url(url):
        raise ValueError("posting lacks a title or a specific HTTP(S) job URL")

    posting_id = str(job.get("id") or urlsplit(url).path or url)
    source_kind = "aggregator" if provider == "aggregator" else "first_party"
    evidence = [{"kind": "observed", "date": observed}]
    for kind, value in dates:
        when = _date_text(value)
        if when and when <= observed:
            evidence.append({"kind": kind, "date": when})

    return {
        "provider": provider, "source_kind": source_kind, "posting_id": posting_id,
        "company": company, "exact_title": title, "location": location, "url": url,
        "description": description, "checked_at": observed, "active": active,
        "date_evidence": [
            {**item, "posting_id": posting_id, "source_kind": source_kind, "url": url}
            for item in evidence
        ],
    }


def _alias_index(aliases):
    result = {}
    for group in aliases:
        if not isinstance(group, dict):
            raise ValueError("alias groups must be objects")
        canonical = group.get("canonical_url")
        equivalents = group.get("equivalent_urls")
        reason = group.get("evidence")
        if not web_url(canonical) or not isinstance(equivalents, list) or not equivalents or not _text(reason):
            raise ValueError("an alias group needs canonical_url, equivalent_urls and evidence")
        for url in [canonical, *equivalents]:
            if not web_url(url) or url in result:
                raise ValueError("alias groups must use distinct HTTP(S) URLs")
            result[url] = (canonical, reason)
    return result


def collect_snapshots(snapshots, *, run_date, queries=(), blocked=(), aliases=()):
    """Group identical employer seats across posting IDs, keeping dated provenance."""
    alias_index = _alias_index(aliases)
    observations = defaultdict(list)
    coverage = {"queries": list(queries), "sources": [], "caps_hit": [], "blocked_sources": list(blocked)}
    latest = {}
    for snapshot in snapshots:
        provider = snapshot.get("provider")
        company = _text(snapshot.get("company"))
        board = _text(snapshot.get("board")) or company
        observed = iso_date(snapshot.get("observed_at")).isoformat()
        jobs = snapshot.get("jobs")
        if provider not in (*ENDPOINTS, "employer", "aggregator") or not company or not isinstance(jobs, list):
            raise ValueError("snapshot needs provider, company, observed_at, and jobs")
        if observed > run_date:
            raise ValueError("snapshot observed_at is after the run date")
        source = (provider, _normalized(company), _normalized(board))
        latest[source] = max(latest.get(source, observed), observed)
        coverage["sources"].append({"provider": provider, "company": company, "board": board,
                                    "observed_at": observed, "postings": len(jobs)})
        if snapshot.get("cap_hit") is True:
            coverage["caps_hit"].append({"provider": provider, "board": board})

        for job in jobs:
            item = _normalize(job, provider, company, observed)
            identity = tuple(map(_normalized, (company, item["exact_title"], item["location"])))
            alias = alias_index.get(item["url"])
            if alias:
                canonical, reason = alias
                key = _key(identity[0], canonical)
                item["identity_evidence"] = reason
            elif item["description"]:
                key = _key(*identity, _normalized(item["description"]))
            else:
                key = _key(*identity, item["url"])
            observations[key].append((source, item))

    candidates = []
    for key, items in sorted(observations.items()):
        current = [
            item for source, item in items
            if item["checked_at"] == run_date == latest[source]
        ]
        if not current:
            continue
        current.sort(key=lambda item: (
            item["source_kind"] != "first_party", not item["active"],
            not item["description"], item["url"],
        ))
        primary = current[0]
        all_evidence = [entry for _, item in items for entry in item["date_evidence"]]
        evidence = list({json.dumps(entry, sort_keys=True): entry for entry in all_evidence}.values())
        candidates.append({
            **primary, "seat_key": key, "date_evidence": sorted(
                evidence, key=lambda entry: (entry["date"], entry["url"], entry["kind"])
            ),
            "source_urls": sorted({item["url"] for _, item in items}),
        })
    return candidates, coverage


def snapshot_files(directory):
    return [read_object(path) for path in sorted(Path(directory).glob("*.json"))]


def fetch_boards(config, *, run_date=None, opener=None):
    """Fetch configured public ATS endpoints with no auth headers or redirects."""
    today = run_date or date.today().isoformat()
    opener = opener or build_opener(_NoRedirects()).open
    boards = config.get("boards")
    if not isinstance(boards, list) or not boards:
        raise ValueError("board configuration must contain a nonempty boards list")

    snapshots = []
    blocked = []
    for board in boards:
        if not isinstance(board, dict):
            raise ValueError("board configuration entries must be objects")
        provider = board.get("provider")
        slug = _text(board.get("board"))
        company = _text(board.get("company"))
        if provider not in ENDPOINTS or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}", slug) or not company:
            raise ValueError("board needs a supported provider, a board slug and a company label")
        request = Request(ENDPOINTS[provider].format(board=slug), headers={
            "Accept": "application/json",
            "User-Agent": "CareerMatching/1.0 (public job-board reader)",
        })
        try:
            with opener(request, timeout=15) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError("response exceeded 10 MiB")
            payload = json.loads(raw)
            if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
                raise ValueError("response lacked a jobs array")
            candidates = {**board, "observed_at": today, "jobs": payload["jobs"]}
            for job in candidates["jobs"]:
                _normalize(job, provider, company, today)
            snapshots.append(candidates)
        except HTTPError as error:
            blocked.append({"provider": provider, "board": slug, "reason": f"HTTP {error.code}"})
        except (OSError, URLError, ValueError) as error:
            blocked.append({"provider": provider, "board": slug, "reason": type(error).__name__})
    return snapshots, blocked


def jobspy_snapshots(payload, *, run_date):
    """Import aggregator leads. Liveness remains unresolved until separately checked."""
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        raise ValueError("JobSpy output must contain a jobs array")
    grouped = defaultdict(list)
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError("JobSpy jobs must be objects")
        company = _text(job.get("company"))
        url = _text(job.get("job_url"))
        if company and web_url(url) and _text(job.get("title")):
            grouped[company].append({
                "id": job.get("id"), "title": job["title"], "location": _text(job.get("location")),
                "description": _text(job.get("description")), "url": url, "active": False,
                "publication": job.get("date_posted"),
            })
    return [
        {"provider": "aggregator", "board": "jobspy", "company": company,
         "observed_at": run_date, "jobs": rows} for company, rows in sorted(grouped.items())
    ]

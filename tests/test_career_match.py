from __future__ import annotations

import io
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

import career_match
from manage_state import _is_specific_job_url, classify_url
from preview_board import presentation_payload
from ranking import rank_key
from run_validation import iso_date, read_object, validate_run
from search_sources import collect_snapshots, fetch_boards, jobspy_snapshots, snapshot_files


@pytest.fixture
def local(monkeypatch, tmp_path):
    monkeypatch.setattr(career_match, "OUTPUT", tmp_path / "output")
    monkeypatch.setattr(career_match, "PROFILE", tmp_path / "context.md")
    monkeypatch.setattr(career_match, "TRACKER", tmp_path / "private" / "tracker.sqlite3")
    return tmp_path


@pytest.fixture
def synthetic_run(local):
    career_match._demo(SimpleNamespace(run="demo", date="2026-01-15"))
    return local / "output" / "demo" / "ranked"


def test_onboarding_preserves_an_existing_profile(local):
    career_match._onboard()
    profile = local / "context.md"
    assert "## Constraints" in profile.read_text(encoding="utf-8")
    profile.write_text("Fictional custom profile", encoding="utf-8")
    career_match._onboard()
    assert profile.read_text(encoding="utf-8") == "Fictional custom profile"


def test_offline_search_and_ranking(synthetic_run):
    status, _ = validate_run(synthetic_run / "_run-manifest.json", today="2026-01-15")
    assert status["passed"]
    assert status["records_checked"] == 5
    assert status["presented"] == 3

    records = {r["exact_title"]: r for r in (
        read_object(p) for p in (synthetic_run / "records").glob("*.json")
    )}
    relisted = records["Implementation Operations Lead"]
    assert relisted["disposition"] == "skip"
    assert relisted["recency"]["earliest_publication"] == "2025-11-21"
    assert len(relisted["source_urls"]) == 2
    assert relisted["identity_evidence"]
    assert records["Customer Education Lead"]["recency"]["original_posted_status"] == "unknown"
    assert records["Customer Enablement Partner"]["review_status"] == "assessed-provisional"
    assert records["Operations Programme Manager"]["disposition"] == "pending"
    board = presentation_payload(synthetic_run)
    assert [r["disposition"] for r in board["main"]] == ["apply_now", "apply_if_time"]
    assert board["appendix"][0]["placement"] == "optional"
    assert board["coverage"] == {
        "candidates": 5, "pending": 1, "skipped": 1, "stale": 1, "sources": 4,
        "caps_hit": 1, "blocked_sources": 0,
    }
    assert all("description" not in r and "requirements" not in r for r in board["main"] + board["appendix"])


def test_tampered_preview_does_not_serve_other_data(synthetic_run):
    path = synthetic_run / "board.json"
    board = read_object(path)
    board["main"][0]["private_profile"] = "Fictional sensitive field"
    path.write_text(json.dumps(board), encoding="utf-8")
    with pytest.raises(ValueError, match="differs from the validated"):
        presentation_payload(synthetic_run)


def test_adapter_calls_only_the_public_endpoint_and_reports_errors():
    calls = []

    def opener(request, *, timeout):
        calls.append((request.full_url, request.get_method(), set(k for k, _ in request.header_items()), timeout))
        if request.full_url.startswith("https://api.ashbyhq.com/"):
            snapshot = read_object(career_match.FIXTURES / "snapshots" / "01-larkspur-current.json")
            raw = json.dumps({"jobs": snapshot["jobs"]}).encode()
            return io.BytesIO(raw)
        raise HTTPError(request.full_url, 503, "Unavailable", {}, None)

    config = {"boards": [
        {"provider": "ashby", "board": "larkspur", "company": "Larkspur Works"},
        {"provider": "greenhouse", "board": "bracken", "company": "Bracken Studio"},
    ]}
    snapshots, blocked = fetch_boards(config, run_date="2026-01-15", opener=opener)
    assert len(snapshots) == 1
    assert blocked == [{"provider": "greenhouse", "board": "bracken", "reason": "HTTP 503"}]
    assert calls == [
        ("https://api.ashbyhq.com/posting-api/job-board/larkspur", "GET", {"Accept", "User-agent"}, 15),
        ("https://boards-api.greenhouse.io/v1/boards/bracken/jobs?content=true", "GET", {"Accept", "User-agent"}, 15),
    ]
    config["boards"][0]["board"] = "elsewhere/../../"
    with pytest.raises(ValueError, match="board slug"):
        fetch_boards(config, opener=opener)


def test_unverified_jobspy_lead_is_kept_pending(local):
    today = date.today().isoformat()
    path = local / "leads.json"
    path.write_text(json.dumps({"query": "Customer support", "jobs": [
        {"title": "Support Specialist", "company": "Fictional Studio",
         "job_url": "https://board.example.org/jobs/50001", "location": "Unspecified",
         "description": "Support customers by email.", "date_posted": today},
    ]}), encoding="utf-8")
    career_match._run_discover(SimpleNamespace(
        run="lead", boards=None, snapshots=[], jobspy=[path], query=[], aliases=None,
    ))
    run = local / "output" / "lead"
    assert next(iter(read_object(run / "reviews.json")["reviews"].values()))["review_status"] == "pending"
    board = career_match._write_ranked(run, max_days=35)
    assert board["main"] == []
    assert board["coverage"]["pending"] == 1
    assert board["coverage"]["queries"] == ["Customer support"]


def test_discovery_needs_same_day_evidence():
    snapshots = snapshot_files(career_match.FIXTURES / "snapshots")
    candidates, _ = collect_snapshots(snapshots, run_date="2026-01-16")
    assert candidates == []


def test_tracking_suppresses_only_confirmed_seat(local):
    today = date.today().isoformat()
    career_match._demo(SimpleNamespace(run="demo", date=today))
    demo = local / "output" / "demo"
    discovery = read_object(demo / "candidates.json")
    reviews = read_object(demo / "reviews.json")
    for name in ("initial", "followup"):
        run = local / "output" / name
        career_match._write_json(run / "candidates.json", {**discovery, "synthetic": False})
        career_match._write_json(run / "reviews.json", reviews)
    initial = career_match._write_ranked(local / "output" / "initial", max_days=35)
    first = initial["main"][0]
    career_match._track(SimpleNamespace(run="initial", seat_key=first["seat_key"], status="submitted"))
    followup = career_match._write_ranked(local / "output" / "followup", max_days=35)
    assert [item["exact_title"] for item in followup["main"]] == ["Customer Education Lead"]
    with pytest.raises(ValueError, match="synthetic"):
        career_match._track(SimpleNamespace(run="demo", seat_key=first["seat_key"], status="submitted"))


def test_weekly_carry_counts_distinct_weeks(local):
    role = {"seat_key": "fictional", "placement": "main"}
    for n, day in enumerate(("2026-01-01", "2026-01-02", "2026-01-09", "2026-01-09")):
        career_match._write_json(
            local / f"output/week{n}/ranked/board.json",
            {"run_date": day, "synthetic": n == 3, "main": [role], "appendix": []},
        )
    weeks, expired = career_match._read_board_history(iso_date("2026-01-15"), local / "current")
    assert weeks == {"fictional": {(2026, 1), (2026, 2)}}
    assert not expired


def test_disposition_precedes_screener_and_screener_breaks_ties(synthetic_run):
    first, second = presentation_payload(synthetic_run)["main"]
    records = {r["exact_title"]: r for r in (
        read_object(p) for p in (synthetic_run / "records").glob("*.json")
    )}
    talent = records[first["exact_title"]]
    manager = records[second["exact_title"]]
    assert rank_key(talent) < rank_key(manager)
    assert rank_key(manager) < rank_key({**talent, "disposition": "apply_if_time"})


@pytest.mark.parametrize("url", [
    "https://jobs.ashbyhq.com/example",
    "https://jobs.ashbyhq.com/example/jobs",
    "https://www.linkedin.com/jobs/search/",
    "https://evil.example.org/jobs?source=ashbyhq.com",
    "https://fake-user:fake-password@jobs.ashbyhq.com/example/ab12",
    "javascript:alert(1)",
])
def test_non_listing_urls_are_rejected(url):
    assert not _is_specific_job_url(url)


def test_url_classification_uses_host_not_search_text():
    assert classify_url("https://evil.example.org/?source=ashbyhq.com")["type"] == "unknown"
    assert classify_url("https://jobs.ashbyhq.com.evil.example.org/a/b")["type"] == "unknown"
    assert _is_specific_job_url("https://employer.example.org/careers?gh_jid=123456")


@pytest.mark.parametrize("field,value", [
    ("expected_records", ["../other.json"]),
    ("expected_records", [{"path": "records/id.json"}]),
    ("presentation_set", ["records/id.json", "records/id.json"]),
    ("run_date", "2026-02-01"),
    ("coverage", []),
])
def test_manifest_fails_safely_on_invalid_inputs(synthetic_run, field, value):
    path = synthetic_run / "_run-manifest.json"
    manifest = read_object(path)
    manifest[field] = value
    path.write_text(json.dumps(manifest), encoding="utf-8")
    result, records = validate_run(path, today="2026-01-15")
    assert result["violations"]
    assert not records


def test_checkout_ignores_private_paths():
    root = Path(career_match.__file__).resolve().parents[1]
    paths = [
        "context.md", "state.json", "output/run/ranked/board.json", ".career-matching/tracker.sqlite3",
        ".env.local", ".claude/agent-memory/example/state.json", ".codex/config.toml", "private-cv.pdf",
    ]
    result = subprocess.run(
        ["git", "check-ignore", "-z", "--stdin"],
        input=("\0".join(paths) + "\0").encode("utf-8"),
        capture_output=True, check=True, cwd=root,
    )
    assert result.stdout.decode("utf-8").rstrip("\0").split("\0") == paths
    assert sys.version_info >= (3, 11)

#!/usr/bin/env python3
"""Local entry points for Career Matching."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import sqlite3
from collections import defaultdict
from contextlib import closing
from datetime import date
from pathlib import Path

from ranking import assess, rank_key
from run_validation import ACTIONABLE, POLICY, ROOT, iso_date, read_object, validate_run
from search_sources import collect_snapshots, fetch_boards, jobspy_snapshots, snapshot_files

OUTPUT = ROOT / "output"
PROFILE = ROOT / "context.md"
FIXTURES = ROOT / "examples" / "offline"
TRACKER = ROOT / ".career-matching" / "tracker.sqlite3"
TRACKING = ("interested", "dismissed", "submitted", "interviewing", "clear")
RUN_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}")


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        temp = Path(handle.name)
        try:
            json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
        except BaseException:
            handle.close()
            temp.unlink(missing_ok=True)
            raise
    try:
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def _run_dir(run_id):
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("run name must contain only letters, numbers, underscores and hyphens")
    path = OUTPUT / run_id
    if OUTPUT.is_symlink() or path.is_symlink():
        raise ValueError("output directories may not be symlinks")
    return path


def _coverage(candidates, coverage):
    return {**coverage, "candidates": len(candidates)}


def _discover(run, snapshots, *, run_date, queries=(), blocked=(), synthetic=False, aliases=()):
    candidates, coverage = collect_snapshots(snapshots, run_date=run_date, queries=queries, blocked=blocked, aliases=aliases)
    OUTPUT.mkdir(exist_ok=True)
    if run.exists():
        raise ValueError(f"run {run.name} already exists; choose a new name")
    with tempfile.TemporaryDirectory(prefix=".discovery-", dir=OUTPUT) as temporary:
        stage = Path(temporary) / "run"
        _write_json(stage / "candidates.json", {
            "run_id": run.name, "run_date": run_date, "synthetic": synthetic,
            "coverage": _coverage(candidates, coverage), "candidates": candidates,
        })
        _write_json(stage / "reviews.json", {
            "reviews": {item["seat_key"]: {"review_status": "pending"} for item in candidates}
        })
        for index, snapshot in enumerate(snapshots):
            _write_json(stage / "snapshots" / f"{index:03}.json", snapshot)
        stage.rename(run)
    return candidates


def _read_board_history(before, current):
    weeks = defaultdict(set)
    expired = set()
    for path in OUTPUT.glob("*/ranked/board.json"):
        if path.parent.parent == current:
            continue
        try:
            board = read_object(path)
            run_date = iso_date(board.get("run_date"))
        except (OSError, ValueError):
            continue
        if board.get("synthetic") is True or run_date >= before:
            continue
        iso = run_date.isocalendar()
        for record in board.get("main", []):
            weeks[record["seat_key"]].add((iso.year, iso.week))
        for record in board.get("appendix", []):
            if record.get("placement") == "carry_over_expired":
                expired.add(record["seat_key"])
    return weeks, expired


def _board_record(record, placement):
    fields = (
        "seat_key", "company", "exact_title", "location", "url", "disposition",
        "central_work", "fit_reason", "practical_notes", "screener", "source_kind", "recency",
        "interview_prospect", "confidence", "optional_reason", "recommended_effort", "checked_at",
    )
    return {key: record[key] for key in fields if key in record} | {"placement": placement}


def _write_ranked(run, *, max_days):
    discovery = read_object(run / "candidates.json")
    if not 1 <= max_days <= 365:
        raise ValueError("max-days must be between 1 and 365")
    run_date = iso_date(discovery["run_date"])
    if (run / "ranked").exists():
        raise ValueError("run already finalized; start a fresh run to reassess")
    reviews = read_object(run / "reviews.json").get("reviews")
    if not isinstance(reviews, dict) or not all(isinstance(review, dict) for review in reviews.values()):
        raise ValueError("reviews.json must contain a reviews object keyed by seat_key")
    candidates = discovery["candidates"]
    expected_keys = {item["seat_key"] for item in candidates}
    if len(expected_keys) != len(candidates) or not all(
        isinstance(key, str) and re.fullmatch(r"[a-f0-9]{24}", key) for key in expected_keys
    ):
        raise ValueError("discovery contains an invalid or duplicate seat_key")
    if set(reviews) != expected_keys:
        raise ValueError("review keys must match discovery; use pending for unresolved candidates")
    synthetic = discovery.get("synthetic") is True
    if not synthetic and run_date != date.today():
        raise ValueError("discovery is from another day; recheck listings in a new run")
    tracked = _read_tracking() if not synthetic else {}
    weeks, expired = _read_board_history(run_date, run) if not synthetic else ({}, set())
    now = run_date.isocalendar()
    this_week = (now.year, now.week)

    records = []
    for candidate in candidates:
        key = candidate["seat_key"]
        try:
            records.append(assess(candidate, reviews[key], run_date=run_date.isoformat(),
                                  max_days=max_days, tracked=tracked.get(key)))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"review {key}: {error}") from error

    main, appendix = [], []
    actionable = [record for record in records if record["disposition"] in ACTIONABLE]
    for record in sorted(actionable, key=rank_key):
        key = record["seat_key"]
        earlier_weeks = weeks.get(key, set()) - {this_week}
        if len(earlier_weeks) >= 2 and tracked.get(key) != "interested":
            if key not in expired:
                appendix.append(_board_record(record, "carry_over_expired"))
        elif record.get("optional_reason"):
            appendix.append(_board_record(record, "optional"))
        elif len(main) < 10:
            main.append(_board_record(record, "main"))
        else:
            appendix.append(_board_record(record, "appendix"))

    coverage = {**discovery["coverage"], "pending": sum(
        record["disposition"] in ("pending", "incomplete") for record in records
    ), "skipped": sum(record["disposition"] == "skip" for record in records),
        "stale": sum(record["disposition"] == "skip" and record["recency"]["verdict"] == "stale"
                     for record in records)}
    board = {
        "run_date": run_date.isoformat(), "synthetic": synthetic, "main": main,
        "appendix": appendix, "coverage": coverage,
    }

    def record_path(record):
        return f"records/{record['seat_key']}.json"

    manifest = {
        "run_id": run.name, "run_date": board["run_date"], "policy": POLICY,
        "completed": True, "coverage": coverage, "synthetic": synthetic,
        "expected_records": [record_path(record) for record in records],
        "presentation_set": [record_path(record) for record in main + appendix],
        "main_set": [record_path(record) for record in main],
    }
    with tempfile.TemporaryDirectory(prefix=".ranking-", dir=run) as temporary:
        stage = Path(temporary) / "ranked"
        for record in records:
            _write_json(stage / record_path(record), record)
        _write_json(stage / "_run-manifest.json", manifest)
        validation, _ = validate_run(stage / "_run-manifest.json", today=board["run_date"])
        if not validation["passed"]:
            raise ValueError("run validation failed: " + "; ".join(validation["violations"]))
        _write_json(stage / "board.json", board)
        stage.rename(run / "ranked")
    return board


def _onboard():
    if PROFILE.is_symlink():
        raise ValueError("profile may not be a symlink")
    template = (ROOT / "context.md.example").read_text(encoding="utf-8")
    try:
        with PROFILE.open("x", encoding="utf-8") as handle:
            handle.write(template)
    except FileExistsError:
        print("Existing context.md kept.")
    else:
        print("Created local context.md. Fill in your goals, evidence and constraints.")


def _demo(args):
    run_date = iso_date(args.date) if args.date else date.today()
    baseline = iso_date("2026-01-15")
    shift = run_date - baseline
    snapshots = snapshot_files(FIXTURES / "snapshots")
    for snapshot in snapshots:
        snapshot["observed_at"] = (iso_date(snapshot["observed_at"]) + shift).isoformat()
        for job in snapshot["jobs"]:
            for field in ("publishedAt", "updated_at", "first_published", "publication"):
                if job.get(field):
                    job[field] = (iso_date(job[field]) + shift).isoformat()
    run = _run_dir(args.run)
    candidates = _discover(
        run, snapshots, run_date=run_date.isoformat(), queries=["operations", "customer education"],
        synthetic=True, aliases=read_object(FIXTURES / "aliases.json")["aliases"],
    )
    reviews = read_object(FIXTURES / "reviews.json")["reviews"]
    _write_json(run / "reviews.json", {"reviews": {
        item["seat_key"]: reviews[item["exact_title"]] for item in candidates
    }})
    _show(_write_ranked(run, max_days=35), run)
    for path in sorted((run / "ranked" / "records").glob("*.json")):
        record = read_object(path)
        when = record["recency"]["earliest_publication"]
        if record["disposition"] == "skip" and when and record["recency"]["verdict"] == "stale":
            print(f"Relisted example: {record['exact_title']} was first published on {when}.")
            print("The newer listing did not reset its age.")


def _show(board, run):
    for section, title in (("main", "Shortlist"), ("appendix", "Appendix")):
        print(f"{title} ({len(board[section])})")
        for record in board[section]:
            label = record["disposition"].replace("_", " ")
            if record["placement"] != section:
                label = record["placement"].replace("_", " ")
            print(f"  {record['company']} — {record['exact_title']} [{label}]")
    print(f"Pending or incomplete: {board['coverage']['pending']}")
    coverage = board["coverage"]
    print(f"Skipped: {coverage['skipped']} ({coverage['stale']} past the recency window)")
    print(f"Sources capped: {len(coverage['caps_hit'])}. Sources blocked: {len(coverage['blocked_sources'])}.")
    print(f"Validated output: {run.relative_to(OUTPUT.parent) / 'ranked'}")


def _run_discover(args):
    run_date = date.today().isoformat()
    snapshots, blocked = [], []
    queries = list(args.query)
    if args.boards:
        snapshots, blocked = fetch_boards(read_object(args.boards), run_date=run_date)
    for directory in args.snapshots:
        snapshots.extend(snapshot_files(directory))
    for path in args.jobspy:
        payload = read_object(path)
        snapshots.extend(jobspy_snapshots(payload, run_date=run_date))
        if isinstance(payload.get("query"), str):
            queries.append(payload["query"])
    if not (args.boards or snapshots):
        raise ValueError("add --boards, --snapshots or --jobspy discovery input")
    aliases = read_object(args.aliases).get("aliases") if args.aliases else []
    if not isinstance(aliases, list):
        raise ValueError("alias configuration must contain an aliases list")
    run = _run_dir(args.run)
    candidates = _discover(run, snapshots, run_date=run_date, queries=queries, blocked=blocked, aliases=aliases)
    print(f"{len(candidates)} candidates. Review {run.relative_to(OUTPUT.parent) / 'reviews.json'}.")
    if blocked:
        print(f"{len(blocked)} blocked source(s); see candidates.json coverage.")


def _read_tracking():
    if not TRACKER.exists():
        return {}
    with closing(sqlite3.connect(TRACKER)) as connection, connection:
        connection.execute("CREATE TABLE IF NOT EXISTS roles (seat_key TEXT PRIMARY KEY, status TEXT NOT NULL)")
        return dict(connection.execute("SELECT seat_key, status FROM roles"))


def _track(args):
    board = read_object(_run_dir(args.run) / "ranked" / "board.json")
    if board.get("synthetic"):
        raise ValueError("synthetic runs cannot update personal tracking")
    if args.seat_key not in {item["seat_key"] for item in board["main"] + board["appendix"]}:
        raise ValueError("seat key is absent from this run's board")
    TRACKER.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(TRACKER)) as connection, connection:
        connection.execute("CREATE TABLE IF NOT EXISTS roles (seat_key TEXT PRIMARY KEY, status TEXT NOT NULL)")
        if args.status == "clear":
            connection.execute("DELETE FROM roles WHERE seat_key = ?", (args.seat_key,))
        else:
            connection.execute(
                "INSERT INTO roles VALUES (?, ?) ON CONFLICT(seat_key) DO UPDATE SET status = excluded.status",
                (args.seat_key, args.status),
            )
    print(f"Tracking updated: {args.status}.")


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="check the local checkout")
    sub.add_parser("onboard", help="create a private search profile template")
    demo = sub.add_parser("demo", help="replay the synthetic search without network access")
    demo.add_argument("--run", default="demo")
    demo.add_argument("--date", help="render synthetic fixture dates relative to this date")
    discover = sub.add_parser("discover", help="collect and deduplicate job leads")
    discover.add_argument("--run", required=True)
    discover.add_argument("--boards", type=Path, help="config with public Ashby or Greenhouse boards")
    discover.add_argument("--snapshots", type=Path, action="append", default=[])
    discover.add_argument("--aliases", type=Path, help="confirmed cross-title listing aliases")
    discover.add_argument("--jobspy", type=Path, action="append", default=[])
    discover.add_argument("--query", action="append", default=[], help="record an external query in coverage")
    rank = sub.add_parser("rank", help="finalize and validate reviewed records")
    rank.add_argument("--run", required=True)
    rank.add_argument("--max-days", type=int, default=35)
    track = sub.add_parser("track", help="record a candidate-authorized action locally")
    track.add_argument("--run", required=True)
    track.add_argument("--seat-key", required=True)
    track.add_argument("--status", choices=TRACKING, required=True)
    preview = sub.add_parser("preview", help="open a read-only loopback dashboard")
    preview.add_argument("--run", default="demo")
    preview.add_argument("--port", type=int, default=8765)
    return parser


def main():
    parser = _parser()
    args = parser.parse_args()
    try:
        if args.command == "check":
            needed = (POLICY, "context.md.example", "AGENTS.md", "CLAUDE.md", "public/index.html")
            missing = [name for name in needed if not (ROOT / name).is_file()]
            if sys.version_info < (3, 11) or missing:
                raise ValueError(f"Python 3.11+ and a complete checkout are required; missing: {missing}")
            print("Checkout ready. Run the offline demo or initialize your local profile.")
        elif args.command == "onboard":
            _onboard()
        elif args.command == "demo":
            _demo(args)
        elif args.command == "discover":
            _run_discover(args)
        elif args.command == "rank":
            run = _run_dir(args.run)
            _show(_write_ranked(run, max_days=args.max_days), run)
        elif args.command == "track":
            _track(args)
        elif args.command == "preview":
            from preview_board import serve

            serve(_run_dir(args.run) / "ranked", args.port)
    except (KeyError, OSError, TypeError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Career Matching: {error}\n")
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()

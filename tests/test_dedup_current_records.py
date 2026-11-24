"""RED tests: dedup must not use legacy numeric score as archival authority.

Policy: references/matching-policy.md section 8 ("no selection or archival authority").
tmp_path only; never touches the live repo output.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANAGE_STATE = ROOT / "scripts" / "manage_state.py"
PREFLIGHT = ROOT / "scripts" / "preflight.sh"


def _job(company: str, title: str, url: str, role: str, **extra) -> dict:
    d = {
        "job_id": f"{company}-{title}".lower().replace(" ", "-"),
        "company": company, "title": title, "job_url": url, "role_type": role,
        "source_channel": "direct", "location": "London", "status": "verified",
        "active_status": "live", "run_date": "2026-10-19",
    }
    d.update(extra)
    return d


def _write(dirpath: Path, name: str, data: dict) -> Path:
    dirpath.mkdir(parents=True, exist_ok=True)
    p = dirpath / name
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def _dedup(output_dir: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MANAGE_STATE), "dedup", "--output-dir", str(output_dir), *extra],
        capture_output=True, text=True,
    )


def _archived(output_dir: Path) -> list[Path]:
    arch = output_dir / "archive"
    return [p for p in arch.rglob("*.json")] if arch.exists() else []


def _filler(verified: Path, role: str, n: int = 3) -> None:
    """High-score distinct records so the 50% safety bound never masks behaviour."""
    for i in range(n):
        _write(verified / role, f"filler{i}.json",
               _job(f"Filler{i}-{role}", f"Role{i}", f"https://jobs.ashbyhq.com/f{i}-{role}/{i}", role, score=90))


class TestDefaultDedupIgnoresScore:
    def test_low_score_unique_record_survives_default_dedup(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        v = out / "verified"
        p = _write(v / "founding-marketer", "acme-fm.json",
                   _job("Acme", "Founding Marketer", "https://jobs.ashbyhq.com/acme/1", "founding-marketer",
                        score=55, salary_flag="below_50k"))
        _filler(v, "founding-marketer")
        res = _dedup(out)
        assert res.returncode == 0, res.stderr
        assert p.exists(), "score 55 record must not be archived by default"
        assert not _archived(out)

    def test_record_without_score_field_survives_and_no_crash(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        v = out / "verified"
        p = _write(v / "founding-marketer", "tier-only.json",
                   _job("TierCo", "Founding Marketer", "https://jobs.ashbyhq.com/tierco/2", "founding-marketer",
                        review_status="assessed", disposition="apply_now"))
        _filler(v, "founding-marketer")
        res = _dedup(out)
        assert res.returncode == 0, res.stderr
        assert "Traceback" not in res.stderr
        assert p.exists(), "tier-only record must survive"

    def test_true_duplicates_consolidate_and_history_preserved(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        v = out / "verified"
        a = _write(v / "founding-marketer", "dup.json",
                   _job("DupCo", "Founding Marketer", "https://jobs.ashbyhq.com/dupco/1", "founding-marketer", score=85))
        b = _write(v / "growth-generalist", "dup.json",
                   _job("DupCo", "Founding Marketer", "https://jobs.ashbyhq.com/dupco/1b", "growth-generalist", score=80))
        _filler(v, "founding-marketer")
        _filler(v, "growth-generalist")
        res = _dedup(out)
        assert res.returncode == 0, res.stderr
        assert [a.exists(), b.exists()].count(True) == 1, "exactly one duplicate must remain"
        arch = _archived(out)
        assert len(arch) == 1, "the other duplicate must be archived, not deleted"

    def test_true_duplicates_tier_only_consolidate(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        v = out / "verified"
        a = _write(v / "founding-marketer", "dup.json",
                   _job("DupCo", "Founding Marketer", "https://jobs.ashbyhq.com/dupco/1", "founding-marketer",
                        review_status="assessed"))
        b = _write(v / "growth-generalist", "dup.json",
                   _job("DupCo", "Founding Marketer", "https://jobs.ashbyhq.com/dupco/1b", "growth-generalist",
                        review_status="assessed"))
        _filler(v, "founding-marketer")
        _filler(v, "growth-generalist")
        res = _dedup(out)
        assert res.returncode == 0, res.stderr
        assert [a.exists(), b.exists()].count(True) == 1
        assert len(_archived(out)) == 1


class TestLegacyOptIn:
    def test_legacy_score_archive_flag_archives_low_score(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        v = out / "verified"
        p = _write(v / "founding-marketer", "acme-fm.json",
                   _job("Acme", "Founding Marketer", "https://jobs.ashbyhq.com/acme/1", "founding-marketer", score=55))
        _filler(v, "founding-marketer")
        res = _dedup(out, "--legacy-score-archive")
        assert res.returncode == 0, res.stderr
        assert not p.exists(), "legacy opt-in must archive score < 70"
        assert (out / "archive" / "founding-marketer" / "acme-fm.json").exists()


class TestScopedProcessing:
    def test_role_types_scope_leaves_other_role_untouched(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        v = out / "verified"
        _filler(v, "a")
        b1 = _write(v / "b", "x1.json", _job("BCo", "Marketer", "https://jobs.ashbyhq.com/bco/1", "b", score=40))
        b2 = _write(v / "b", "x2.json", _job("BCo", "Marketer", "https://jobs.ashbyhq.com/bco/2", "b", score=30))
        res = _dedup(out, "--role-types", "a")
        assert res.returncode == 0, res.stderr
        assert b1.exists() and b2.exists(), "records outside --role-types must be untouched"
        assert not (out / "archive" / "b").exists()



def test_mixed_group_uses_recency_and_keeps_existing_archive(tmp_path: Path) -> None:
    out = tmp_path / "output"
    verified = out / "verified"
    role = "operations"
    url = "https://sample.example.org/jobs/12345"
    for name, date, score in (("high", "2026-01-10", 90), ("new", "2026-01-15", None),
                              ("low", "2026-01-12", 60)):
        _write(verified / role, name + ".json",
               _job("Example Workshop", "Operations Manager", url, role, score=score, checked_at=date))
    _filler(verified, role)
    previous = _write(out / "archive" / role, "high.json", {"older_archive": True})
    result = _dedup(out)
    assert result.returncode == 0, result.stderr
    assert (verified / role / "new.json").exists()
    assert not (verified / role / "high.json").exists()
    assert json.loads(previous.read_text(encoding="utf-8")) == {"older_archive": True}
    assert (previous.parent / "high-1.json").exists()

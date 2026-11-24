"""RED tests: `manage_state.py validate-run --manifest <path> [--today D] [--max-age-days N]`.

Policy: references/matching-policy.md section 9. All fixtures live in tmp_path.
Exit 0 = pass, 1 = fail; stdout is JSON with a "passed" key.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANAGE_STATE = ROOT / "scripts" / "manage_state.py"
POLICY_REL = "references/matching-policy.md"
TODAY = "2026-10-19"


def make_record(**over: Any) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "company": "Acme",
        "exact_title": "Founding Marketer",
        "url": "https://jobs.ashbyhq.com/acme/1234-abcd",
        "review_status": "assessed",
        "review_method": "human",
        "active_status": "live",
        "checked_at": TODAY,
        "practical_eligibility": "eligible",
        "central_work": "Owns positioning, launches and acquisition across channels.",
        "disposition": "apply_now",
    }
    rec.update(over)
    return rec


class Run:
    """Builds a run dir with record files and a manifest, then invokes validate-run."""

    def __init__(self, tmp_path: Path) -> None:
        self.dir = tmp_path / "run"
        self.dir.mkdir()
        # NOTE: manifest "policy" is a repo-root-relative path; tests run with cwd=ROOT.
        self.records: dict[str, dict[str, Any]] = {}
        self.manifest: dict[str, Any] = {
            "run_id": "test-run",
            "run_date": TODAY,
            "policy": POLICY_REL,
            "completed": True,
            "coverage": {"queries": 3, "caps_hit": [], "blocked_sources": []},
            "expected_records": [],
            "presentation_set": [],
        }

    def add(self, name: str, rec: dict[str, Any], *, present: bool, write: bool = True) -> str:
        rel = f"records/{name}.json"
        if write:
            p = self.dir / rel
            p.parent.mkdir(exist_ok=True)
            p.write_text(json.dumps(rec), encoding="utf-8")
        self.manifest["expected_records"].append(rel)
        if present:
            self.manifest["presentation_set"].append(rel)
        return rel

    @property
    def path(self) -> Path:
        return self.dir / "_run-manifest.json"

    def write_manifest(self) -> Path:
        self.path.write_text(json.dumps(self.manifest), encoding="utf-8")
        return self.path

    def run(self, *extra: str, manifest: Path | None = None) -> subprocess.CompletedProcess:
        m = manifest if manifest is not None else self.write_manifest()
        return subprocess.run(
            [sys.executable, str(MANAGE_STATE), "validate-run", "--manifest", str(m),
             "--today", TODAY, *extra],
            capture_output=True, text=True, cwd=str(ROOT),
        )


def parse(res: subprocess.CompletedProcess) -> dict[str, Any]:
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"stdout is not JSON.\nstdout={res.stdout!r}\nstderr={res.stderr!r}")


def assert_pass(res: subprocess.CompletedProcess) -> dict[str, Any]:
    assert res.returncode == 0, f"expected pass.\nstdout={res.stdout}\nstderr={res.stderr}"
    out = parse(res)
    assert out["passed"] is True
    return out


def assert_fail(res: subprocess.CompletedProcess) -> dict[str, Any]:
    assert res.returncode == 1, f"expected exit 1.\nstdout={res.stdout}\nstderr={res.stderr}"
    out = parse(res)
    assert out["passed"] is False
    return out


def two_valid(tmp_path: Path) -> Run:
    r = Run(tmp_path)
    r.add("acme", make_record(), present=True)
    r.add("beta", make_record(company="Beta", url="https://jobs.lever.co/beta/9f8e7d6c"), present=True)
    return r


class TestManifestLevel:
    def test_valid_manifest_with_two_presented_records_passes(self, tmp_path: Path) -> None:
        assert_pass(two_valid(tmp_path).run())

    def test_missing_manifest_fails(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        assert_fail(r.run(manifest=tmp_path / "nope" / "_run-manifest.json"))

    def test_stale_manifest_fails_default_max_age(self, tmp_path: Path) -> None:
        r = two_valid(tmp_path)
        r.manifest["run_date"] = "2026-10-10"
        assert_fail(r.run())

    def test_manifest_within_max_age_passes(self, tmp_path: Path) -> None:
        r = two_valid(tmp_path)
        r.manifest["run_date"] = "2026-10-17"  # 2 days old
        for path in (r.dir / "records").glob("*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            path.write_text(json.dumps(record | {"checked_at": "2026-10-17"}), encoding="utf-8")
        assert_pass(r.run())

    def test_max_age_days_override_makes_old_manifest_stale(self, tmp_path: Path) -> None:
        r = two_valid(tmp_path)
        r.manifest["run_date"] = "2026-10-17"
        assert_fail(r.run("--max-age-days", "1"))

    def test_incomplete_run_fails(self, tmp_path: Path) -> None:
        r = two_valid(tmp_path)
        r.manifest["completed"] = False
        assert_fail(r.run())

    def test_missing_expected_record_file_fails(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("acme", make_record(), present=True)
        r.add("ghost", make_record(company="Ghost"), present=False, write=False)
        assert_fail(r.run())

    def test_presentation_item_not_in_expected_fails(self, tmp_path: Path) -> None:
        r = two_valid(tmp_path)
        r.manifest["presentation_set"].append("records/stranger.json")
        assert_fail(r.run())

    def test_policy_file_missing_fails(self, tmp_path: Path) -> None:
        r = two_valid(tmp_path)
        r.manifest["policy"] = "references/does-not-exist.md"
        assert_fail(r.run())

    def test_manifest_missing_expected_records_key_fails(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        del r.manifest["expected_records"]
        assert_fail(r.run())

    def test_zero_result_run_with_empty_lists_passes(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        out = assert_pass(r.run())
        assert out.get("zero_recommendations") is True


class TestPresentedRecords:
    @pytest.mark.parametrize("status", ["fetched", "parsed", "pending"])
    def test_non_assessed_presented_record_fails(self, tmp_path: Path, status: str) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(review_status=status), present=True)
        assert_fail(r.run())

    def test_unverified_active_status_fails(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(active_status="unverified"), present=True)
        assert_fail(r.run())

    def test_missing_checked_at_fails(self, tmp_path: Path) -> None:
        rec = make_record()
        del rec["checked_at"]
        r = Run(tmp_path)
        r.add("x", rec, present=True)
        assert_fail(r.run())

    def test_generic_careers_url_fails(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(url="https://example.com/careers"), present=True)
        assert_fail(r.run())

    def test_ineligible_presented_record_fails(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(practical_eligibility="ineligible"), present=True)
        assert_fail(r.run())

    def test_conditional_presented_record_passes(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(practical_eligibility="conditional", disposition="apply_if_time"), present=True)
        assert_pass(r.run())

    def test_skip_disposition_presented_fails(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(disposition="skip"), present=True)
        assert_fail(r.run())

    def test_changed_disposition_without_reason_fails(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(previous_disposition="apply_if_time", disposition="apply_now"), present=True)
        assert_fail(r.run())

    def test_changed_disposition_with_reason_passes(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(previous_disposition="apply_if_time", disposition="apply_now",
                               change_reason="Reposted 2026-10-18; pay now disclosed at 65k."), present=True)
        assert_pass(r.run())


class TestRecordCompleteness:
    @pytest.mark.parametrize("field", ["company", "exact_title", "central_work"])
    @pytest.mark.parametrize("blank", ["missing", "empty", "whitespace"])
    def test_presented_record_missing_identity_or_central_work_fails(
        self, tmp_path: Path, field: str, blank: str
    ) -> None:
        rec = make_record()
        if blank == "missing":
            del rec[field]
        else:
            rec[field] = "" if blank == "empty" else "   "
        r = Run(tmp_path)
        r.add("x", rec, present=True)
        assert_fail(r.run())

    @pytest.mark.parametrize("presented", [True, False])
    def test_unknown_review_status_fails(self, tmp_path: Path, presented: bool) -> None:
        r = Run(tmp_path)
        r.add("good", make_record(), present=True)
        r.add("odd", make_record(company="Odd", url="https://jobs.lever.co/odd/12ab",
                                 review_status="reviewed", disposition="skip"), present=presented)
        out = assert_fail(r.run())
        assert any("unknown review_status" in v for v in out["violations"])

    def test_missing_review_status_on_unpresented_record_fails(self, tmp_path: Path) -> None:
        rec = make_record(disposition="skip")
        del rec["review_status"]
        r = Run(tmp_path)
        r.add("x", rec, present=False)
        assert_fail(r.run())


class TestRejectionsNeedAssessment:
    def _run_with_rejection(self, tmp_path: Path, **rec_over: Any) -> subprocess.CompletedProcess:
        r = Run(tmp_path)
        r.add("good", make_record(), present=True)
        r.add("rej", make_record(company="Rej", url="https://jobs.ashbyhq.com/rej/55", disposition="skip",
                                 **rec_over), present=False)
        return r.run()

    def test_skip_with_parsed_status_and_non_title_method_fails(self, tmp_path: Path) -> None:
        assert_fail(self._run_with_rejection(tmp_path, review_status="parsed", review_method="model_reviewer"))

    def test_skip_with_title_rule_passes_and_is_counted(self, tmp_path: Path) -> None:
        out = assert_pass(self._run_with_rejection(tmp_path, review_status="parsed", review_method="title_rule"))
        assert out.get("title_rule_rejections") == 1

    def test_skip_with_assessed_status_passes(self, tmp_path: Path) -> None:
        assert_pass(self._run_with_rejection(tmp_path, review_status="assessed", review_method="human"))


class TestZeroRecommendations:
    def test_completed_with_empty_presentation_set_passes_and_reports_zero(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("rej1", make_record(disposition="skip", review_status="assessed"), present=False)
        r.add("rej2", make_record(company="B", url="https://jobs.lever.co/b/77aa", disposition="skip",
                                  review_status="assessed"), present=False)
        out = assert_pass(r.run())
        assert out.get("zero_recommendations") is True


class TestProvisionalAndIncomplete:
    """matching-policy.md sections 7 and 9: assessed-provisional and incomplete statuses."""

    def test_presented_provisional_apply_if_time_passes(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(review_status="assessed-provisional", disposition="apply_if_time"), present=True)
        assert_pass(r.run())

    def test_presented_provisional_apply_now_fails(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(review_status="assessed-provisional", disposition="apply_now"), present=True)
        out = assert_fail(r.run())
        assert any("provisional" in v for v in out["violations"])

    def test_presented_incomplete_fails(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("x", make_record(review_status="incomplete", disposition="pending"), present=True)
        assert_fail(r.run())

    @pytest.mark.parametrize("disposition", ["skip", "apply_now", "apply_if_time"])
    def test_unpresented_incomplete_with_verdict_fails(self, tmp_path: Path, disposition: str) -> None:
        r = Run(tmp_path)
        r.add("good", make_record(), present=True)
        r.add("inc", make_record(company="Inc", url="https://jobs.lever.co/inc/12ab",
                                 review_status="incomplete", disposition=disposition), present=False)
        out = assert_fail(r.run())
        assert any("incomplete record has a verdict" in v for v in out["violations"])

    @pytest.mark.parametrize("disposition", ["pending", "incomplete", None])
    def test_unpresented_incomplete_without_verdict_passes(self, tmp_path: Path, disposition: str | None) -> None:
        rec = make_record(review_status="incomplete", disposition=disposition)
        if disposition is None:
            del rec["disposition"]
        r = Run(tmp_path)
        r.add("good", make_record(), present=True)
        r.add("inc", rec, present=False)
        assert_pass(r.run())

    def test_unpresented_provisional_skip_passes(self, tmp_path: Path) -> None:
        r = Run(tmp_path)
        r.add("good", make_record(), present=True)
        r.add("rej", make_record(company="Rej", url="https://jobs.ashbyhq.com/rej/55",
                                 review_status="assessed-provisional", disposition="skip"), present=False)
        assert_pass(r.run())

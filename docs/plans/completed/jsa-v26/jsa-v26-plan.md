# Plan: JSA V26 — Gate Chaining + Verification Infrastructure

## Overview

Gate chaining makes recurring regressions structurally impossible. Instead of text constraints (which the agent can skip), gate chains ensure step N+1 checks that step N's gate was passed. Three-Layer build: L1 (Python infrastructure), L2 (orchestration wiring), L3 (validation + tests).

**From design Handoff Contract:**
- 4 new manage_state.py subcommands (validate-url-type, verify-before-archive, validate-presentation, verify-session-state-written) + 2 enhanced + 2 bug fixes
- 4 gate chains + 2 contradiction resolutions + 4 enforcement strengthening
- 3 preflight enhancements + 7 test suites

## Files to Modify

**Python (manage_state.py):**
- `03_agents/tests/v25/scripts/manage_state.py` — New subcommands, enhancements, bug fixes
- `03_agents/career-matching/scripts/manage_state.py` — Mirror of above (keep in sync)

**Documentation:**
- `03_agents/tests/v25/CLAUDE.md` — Gate enforcement, constraints, recovery protocol
- `03_agents/tests/v25/references/orchestration.md` — Gate chains, sentinel paths
- `03_agents/tests/v25/references/subagent-search-verify.md` — JobSpy constraint

**Shell:**
- `03_agents/tests/v25/scripts/preflight.sh` — Session-state touch, memory print, doc validation

**New test files:**
- `03_agents/tests/v25/tests/conftest.py`
- `03_agents/tests/v25/tests/test_validate_url_type.py`
- `03_agents/tests/v25/tests/test_verify_before_archive.py`
- `03_agents/tests/v25/tests/test_validate_presentation.py`
- `03_agents/tests/v25/tests/test_schema_url_validation.py`
- `03_agents/tests/v25/tests/test_safety_bound_gap.py`
- `03_agents/tests/v25/tests/test_dedup_role_types_slug.py`
- `03_agents/tests/v25/tests/test_gate_chains.py`
- `03_agents/tests/v25/tests/test_manage_state_sync.py`
- `03_agents/tests/v25/tests/test_preflight_sync.py`
- `03_agents/tests/v25/tests/test_verify_and_commit_check_only.py`

---

## Implementation Steps

### Phase 1: L1 Foundation — validate-url-type (Steps 1-4)

#### Step 1: Write test for validate-url-type
**File:** `03_agents/tests/v25/tests/test_validate_url_type.py`
**Action:** Create

```python
"""Tests for manage_state.py validate-url-type subcommand (9 tests).

Verifies URL classification: known ATS patterns -> source,
aggregator patterns -> aggregator, unknown -> unknown.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run_validate_url_type(url: str) -> dict:
    """Run validate-url-type subcommand and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, str(MANAGE_STATE), "validate-url-type", "--url", url],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


class TestValidateUrlType:
    """Tests for the validate-url-type subcommand of manage_state.py."""

    def test_greenhouse_url_is_source(self) -> None:
        output = _run_validate_url_type("https://boards.greenhouse.io/acme/jobs/1234567")
        assert output["type"] == "source"
        assert output["pattern_matched"] == "greenhouse"
        assert output["url"] == "https://boards.greenhouse.io/acme/jobs/1234567"

    def test_ashby_url_is_source(self) -> None:
        output = _run_validate_url_type("https://jobs.ashbyhq.com/acme/abc-123")
        assert output["type"] == "source"
        assert output["pattern_matched"] == "ashby"

    def test_lever_url_is_source(self) -> None:
        output = _run_validate_url_type("https://jobs.lever.co/acme/some-position-id")
        assert output["type"] == "source"
        assert output["pattern_matched"] == "lever"

    def test_workable_url_is_source(self) -> None:
        output = _run_validate_url_type("https://apply.workable.com/acme-corp/j/ABC123/")
        assert output["type"] == "source"
        assert output["pattern_matched"] == "workable"

    def test_rippling_url_is_source(self) -> None:
        output = _run_validate_url_type("https://ats.rippling.com/acme/jobs/abc-def-123")
        assert output["type"] == "source"
        assert output["pattern_matched"] == "rippling"

    def test_indeed_url_is_aggregator(self) -> None:
        output = _run_validate_url_type("https://www.indeed.com/viewjob?jk=abc123def456")
        assert output["type"] == "aggregator"
        assert output["pattern_matched"] == "indeed"

    def test_linkedin_url_is_aggregator(self) -> None:
        output = _run_validate_url_type("https://www.linkedin.com/jobs/view/4344764433")
        assert output["type"] == "aggregator"
        assert output["pattern_matched"] == "linkedin"

    def test_glassdoor_url_is_aggregator(self) -> None:
        output = _run_validate_url_type("https://www.glassdoor.com/job-listing/engineer-acme-JV_IC12345.htm")
        assert output["type"] == "aggregator"
        assert output["pattern_matched"] == "glassdoor"

    def test_unknown_domain_returns_unknown(self) -> None:
        output = _run_validate_url_type("https://www.randomstartup.com/careers/engineer")
        assert output["type"] == "unknown"
        assert output["pattern_matched"] == "unknown"
        assert output["url"] == "https://www.randomstartup.com/careers/engineer"
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_validate_url_type.py -v` — expect FAIL (subcommand doesn't exist yet)
- Lint: `ruff check 03_agents/tests/v25/tests/test_validate_url_type.py`

#### Step 2: Implement validate-url-type subcommand
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify

Add after the existing `_cli_check_dispatch_budget` function (around line 1466), before the `# CLI entrypoint` section:

```python
# ---------------------------------------------------------------------------
# validate-url-type subcommand
# ---------------------------------------------------------------------------

# Patterns that indicate a direct source (company ATS or career page)
_SOURCE_PATTERNS: dict[str, re.Pattern[str]] = {
    "greenhouse": re.compile(r"greenhouse\.io", re.IGNORECASE),
    "ashby": re.compile(r"ashbyhq\.com", re.IGNORECASE),
    "lever": re.compile(r"lever\.co", re.IGNORECASE),
    "workable": re.compile(r"workable\.com", re.IGNORECASE),
    "rippling": re.compile(r"rippling\.com", re.IGNORECASE),
    "breezy": re.compile(r"breezy\.hr", re.IGNORECASE),
    "jazz": re.compile(r"jazz\.co", re.IGNORECASE),
    "applytojob": re.compile(r"applytojob\.com", re.IGNORECASE),
    "smartrecruiters": re.compile(r"smartrecruiters\.com", re.IGNORECASE),
    "recruitee": re.compile(r"recruitee\.com", re.IGNORECASE),
    "bamboohr": re.compile(r"bamboohr\.com", re.IGNORECASE),
    "personio": re.compile(r"personio\.de|personio\.com", re.IGNORECASE),
    "icims": re.compile(r"icims\.com", re.IGNORECASE),
    "taleo": re.compile(r"taleo\.net", re.IGNORECASE),
    "successfactors": re.compile(r"successfactors\.com|successfactors\.eu", re.IGNORECASE),
    "myworkday": re.compile(r"myworkday\.com|myworkdayjobs\.com|wd\d+\.myworkdaysite\.com", re.IGNORECASE),
}

# Patterns that indicate an aggregator (job board)
_AGGREGATOR_PATTERNS: dict[str, re.Pattern[str]] = {
    "indeed": re.compile(r"indeed\.com", re.IGNORECASE),
    "linkedin": re.compile(r"linkedin\.com", re.IGNORECASE),
    "glassdoor": re.compile(r"glassdoor\.com|glassdoor\.co", re.IGNORECASE),
    "studysmarter": re.compile(r"studysmarter\.co", re.IGNORECASE),
    "ziprecruiter": re.compile(r"ziprecruiter\.com", re.IGNORECASE),
    "monster": re.compile(r"monster\.com", re.IGNORECASE),
    "simplyhired": re.compile(r"simplyhired\.com", re.IGNORECASE),
}


def classify_url(url: str) -> dict[str, str]:
    """Classify a URL as source, aggregator, or unknown.

    Returns a dict with keys: url, type, pattern_matched.
    """
    for name, pattern in _SOURCE_PATTERNS.items():
        if pattern.search(url):
            return {"url": url, "type": "source", "pattern_matched": name}

    for name, pattern in _AGGREGATOR_PATTERNS.items():
        if pattern.search(url):
            return {"url": url, "type": "aggregator", "pattern_matched": name}

    return {"url": url, "type": "unknown", "pattern_matched": "unknown"}


def _cli_validate_url_type(args: argparse.Namespace) -> None:
    """CLI validate-url-type subcommand: classify a URL as source/aggregator/unknown."""
    result = classify_url(args.url)
    print(json.dumps(result))
```

Add argparse registration in `main()`, before `args = parser.parse_args()`:

```python
    # --- validate-url-type ---
    vut_parser = subparsers.add_parser(
        "validate-url-type",
        help="Classify a URL as source (ATS), aggregator, or unknown",
    )
    vut_parser.add_argument(
        "--url",
        required=True,
        help="The URL to classify",
    )
    vut_parser.set_defaults(func=_cli_validate_url_type)
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_validate_url_type.py -v` — expect PASS (9 tests)
- Lint: `ruff check 03_agents/tests/v25/scripts/manage_state.py`
- Type check: `mypy 03_agents/tests/v25/scripts/manage_state.py --ignore-missing-imports`

#### Step 3: Mirror to career-matching + add sync enforcement
**File:** `03_agents/career-matching/scripts/manage_state.py`
**Action:** Modify — apply identical changes from Step 2

Additionally, add a canonical source comment at the top of BOTH copies of manage_state.py (after the module docstring):

```python
# CANONICAL SOURCE: 03_agents/tests/v25/scripts/manage_state.py
# This file MUST be kept in sync with 03_agents/career-matching/scripts/manage_state.py.
# After any edit, run: diff 03_agents/tests/v25/scripts/manage_state.py 03_agents/career-matching/scripts/manage_state.py
# CI enforcement: see 03_agents/tests/v25/tests/test_manage_state_sync.py
```

**Also create** `03_agents/tests/v25/tests/test_manage_state_sync.py`:

```python
"""CI guard: ensures manage_state.py copies are byte-identical."""

from pathlib import Path

CANONICAL = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"
MIRROR = CANONICAL.parent.parent.parent.parent / "career-matching" / "scripts" / "manage_state.py"


def test_manage_state_copies_are_identical() -> None:
    """Both copies of manage_state.py must be byte-identical."""
    assert MIRROR.exists(), f"Mirror file not found: {MIRROR}"
    canonical_text = CANONICAL.read_text(encoding="utf-8")
    mirror_text = MIRROR.read_text(encoding="utf-8")
    assert canonical_text == mirror_text, (
        "manage_state.py copies have drifted! "
        f"Canonical: {CANONICAL}, Mirror: {MIRROR}. "
        "Run: diff 03_agents/tests/v25/scripts/manage_state.py "
        "03_agents/career-matching/scripts/manage_state.py"
    )
```

**Also add** a `check-sync` Makefile target in `03_agents/tests/v25/Makefile` (create if not exists):

```makefile
.PHONY: check-sync
check-sync:
	python -m pytest tests/test_manage_state_sync.py tests/test_preflight_sync.py -v
```

This provides an explicit command (`make check-sync`) to run before any commit touching `manage_state.py` or `preflight.sh`.

**Verify:**
- Diff: `diff 03_agents/tests/v25/scripts/manage_state.py 03_agents/career-matching/scripts/manage_state.py` — should show no differences
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_manage_state_sync.py -v` — expect PASS

#### Step 4: Commit Phase 1
**Action:** Git commit

```bash
git add 03_agents/tests/v25/tests/test_validate_url_type.py \
       03_agents/tests/v25/tests/test_manage_state_sync.py \
       03_agents/tests/v25/Makefile \
       03_agents/tests/v25/scripts/manage_state.py \
       03_agents/career-matching/scripts/manage_state.py
git commit -m "feat(jsa): add validate-url-type subcommand — 16 ATS + 7 aggregator patterns, 9 tests, sync enforcement, Makefile"
```

---

### Phase 2: L1 Core — Remaining Subcommands + Enhancements (Steps 5-17)

#### Step 5: Create shared test fixtures + write test for verify-before-archive
**File:** `03_agents/tests/v25/tests/conftest.py`
**Action:** Create — shared fixtures used by all V26 test files

```python
"""Shared test fixtures for V26 test suites."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def make_valid_job(**overrides) -> dict:
    """Create a valid job dict with sensible defaults. Override any field via kwargs."""
    defaults = {
        "job_id": "test-001", "title": "Engineer", "company": "Acme",
        "job_url": "https://boards.greenhouse.io/acme/jobs/12345",
        "role_type": "ai-engineer", "score": 85, "source_channel": "direct",
        "run_date": "2026-03-20", "location": "Remote", "status": "verified",
        "active_status": "live",
    }
    defaults.update(overrides)
    return defaults


def write_job(dir_path: Path, filename: str, job_dict: dict) -> Path:
    """Write a job dict to a JSON file, creating directories as needed."""
    dir_path.mkdir(parents=True, exist_ok=True)
    filepath = dir_path / filename
    filepath.write_text(json.dumps(job_dict, indent=2), encoding="utf-8")
    return filepath
```

**Note:** All subsequent test files in Steps 5, 7, 9, 14, and 30 MUST import `make_valid_job` and `write_job` from `conftest` instead of defining their own `_make_valid_job` and `_write_job` helpers. This eliminates fixture duplication and ensures a single update point when the schema changes.

**File:** `03_agents/tests/v25/tests/test_verify_before_archive.py`
**Action:** Create

```python
"""Tests for verify-before-archive subcommand.

Mocks HTTP HEAD requests to validate URL liveness classification.
Uses source-first strategy: aggregator URLs return 'unverified' instead of
'live' on HTTP 200, since aggregators return 200 for expired listings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from conftest import make_valid_job

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


class TestVerifyBeforeArchiveUnit:
    """Unit tests using direct import and mocking requests.head."""

    def test_live_url_200(self, tmp_path: Path) -> None:
        """HTTP 200 -> status=live."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test-job.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "live"
        assert result["evidence"] == "HTTP 200"

    def test_live_url_301(self, tmp_path: Path) -> None:
        """HTTP 301 redirect -> status=live."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 301
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "live"

    def test_expired_url_404(self, tmp_path: Path) -> None:
        """HTTP 404 -> status=expired."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "expired"
        assert result["evidence"] == "HTTP 404"

    def test_expired_url_410(self, tmp_path: Path) -> None:
        """HTTP 410 Gone -> status=expired."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 410
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "expired"

    def test_timeout_unreachable(self, tmp_path: Path) -> None:
        """Timeout -> status=unreachable."""
        import manage_state
        import requests as req_lib

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        with patch("manage_state.requests.head", side_effect=req_lib.Timeout("timed out")):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "unreachable"
        assert result["evidence"] == "timeout"

    def test_connection_error_unreachable(self, tmp_path: Path) -> None:
        """Connection error -> status=unreachable."""
        import manage_state
        import requests as req_lib

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        with patch("manage_state.requests.head", side_effect=req_lib.ConnectionError("refused")):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "unreachable"
        assert result["evidence"] == "error: refused"

    def test_aggregator_url_200_returns_unverified(self, tmp_path: Path) -> None:
        """Aggregator URL with HTTP 200 -> status=unverified (source-first strategy)."""
        import manage_state

        job = make_valid_job(
            job_url="https://www.indeed.com/viewjob?jk=abc123",
            active_status="verified",
        )
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "unverified"
        assert result["url_type"] == "aggregator"

    def test_read_only_by_default(self, tmp_path: Path) -> None:
        """Default mode does NOT write to the JSON file."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("manage_state.requests.head", return_value=mock_response):
            manage_state.verify_before_archive(job_file)

        updated = json.loads(job_file.read_text(encoding="utf-8"))
        assert updated["active_status"] == "verified"  # unchanged

    def test_write_flag_updates_file(self, tmp_path: Path) -> None:
        """With write=True, verdict IS written to the JSON file."""
        import manage_state

        job = make_valid_job(active_status="verified")
        job_file = tmp_path / "test.json"
        job_file.write_text(json.dumps(job), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("manage_state.requests.head", return_value=mock_response):
            manage_state.verify_before_archive(job_file, write=True)

        updated = json.loads(job_file.read_text(encoding="utf-8"))
        assert updated["active_status"] == "expired"
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_verify_before_archive.py -v` — expect FAIL (9 tests)
- Lint: `ruff check 03_agents/tests/v25/tests/test_verify_before_archive.py`

#### Step 6: Implement verify-before-archive subcommand
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify

Add `import requests` (with fallback) near the top imports:

```python
try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]
```

Add library function after the validate-url-type code block:

```python
# ---------------------------------------------------------------------------
# verify-before-archive subcommand
# ---------------------------------------------------------------------------


def verify_before_archive(input_path: Path, *, write: bool = False) -> dict[str, str]:
    """Check if a job URL is still live via HTTP HEAD (source-first strategy).

    Returns dict with keys: status, evidence, url.
    Does NOT modify the file unless --write is explicitly passed.

    Source-first strategy (V25 regression fix): classifies the URL first.
    - Source URLs: HTTP HEAD result is definitive.
    - Aggregator URLs: HTTP HEAD is unreliable (aggregators return 200 for
      expired listings). Returns status="unverified" instead of "live".
    - Unknown URLs: HTTP HEAD result is used but marked as "unverified-source".
    """
    if requests is None:
        raise ImportError("requests library required for verify-before-archive")

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    job_url = data.get("job_url", "")
    result: dict[str, str] = {"url": job_url}

    # Classify URL first (source-first strategy)
    url_classification = classify_url(job_url)
    url_type = url_classification["type"]
    result["url_type"] = url_type

    try:
        from urllib.parse import urlparse

        original_domain = urlparse(job_url).netloc
        resp = requests.head(job_url, timeout=10, allow_redirects=True)
        code = resp.status_code
        result["evidence"] = f"HTTP {code}"

        # Redirect detection: if final URL domain changed significantly,
        # the listing may have redirected to a generic "no longer accepting" page
        final_url = resp.url if hasattr(resp, "url") else job_url
        final_domain = urlparse(final_url).netloc
        redirected_to_different_domain = (
            original_domain != final_domain
            and not final_domain.endswith(original_domain)
            and not original_domain.endswith(final_domain)
        )

        if 200 <= code <= 399:
            if redirected_to_different_domain:
                result["status"] = "unverified-redirect"
                result["evidence"] = (
                    f"HTTP {code} after redirect to {final_domain} "
                    f"(original: {original_domain}) — possible generic page"
                )
            elif url_type == "source":
                result["status"] = "live"
            elif url_type == "aggregator":
                # Aggregators return 200 for expired listings — NOT definitive
                result["status"] = "unverified"
                result["evidence"] = (
                    f"HTTP {code} (aggregator — not definitive, "
                    f"source-first strategy requires ATS verification)"
                )
            else:
                result["status"] = "unverified-source"
                result["evidence"] = f"HTTP {code} (unknown domain — unverified)"
        elif code in (404, 410):
            result["status"] = "expired"
        else:
            result["status"] = "unreachable"

    except requests.Timeout:
        result["status"] = "unreachable"
        result["evidence"] = "timeout"
    except requests.ConnectionError as exc:
        result["status"] = "unreachable"
        result["evidence"] = f"error: {exc}"
    except requests.RequestException as exc:
        result["status"] = "unreachable"
        result["evidence"] = f"error: {exc}"

    # Only write verdict to file if explicitly requested
    if write:
        data["active_status"] = result["status"]
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return result


def _cli_verify_before_archive(args: argparse.Namespace) -> None:
    """CLI verify-before-archive subcommand."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    result = verify_before_archive(input_path, write=args.write)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
```

Add argparse registration in `main()`:

```python
    # --- verify-before-archive ---
    vba_parser = subparsers.add_parser(
        "verify-before-archive",
        help="Check if a job URL is still live via HTTP HEAD",
    )
    vba_parser.add_argument(
        "--input",
        required=True,
        help="Path to verified JSON file",
    )
    vba_parser.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Write verdict to the JSON file's active_status field (default: read-only check)",
    )
    vba_parser.set_defaults(func=_cli_verify_before_archive)
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_verify_before_archive.py -v` — expect PASS (9 tests)
- Lint: `ruff check 03_agents/tests/v25/scripts/manage_state.py`

#### Step 7: Write test for validate-presentation
**File:** `03_agents/tests/v25/tests/test_validate_presentation.py`
**Action:** Create

```python
"""Tests for validate-presentation subcommand.

Validates verified JSON files are presentation-ready: ATS URLs, non-null
active_status, no expired entries in active list.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import make_valid_job, write_job

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run_validate_presentation(output_dir: str, role_types: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MANAGE_STATE), "validate-presentation",
         "--output-dir", output_dir, "--role-types", role_types],
        capture_output=True, text=True,
    )


class TestValidatePresentation:

    def test_all_valid_passes(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "ai-engineer", "valid.json", make_valid_job())
        result = _run_validate_presentation(str(output_dir), "ai-engineer")
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["passed"] is True
        assert output["violations"] == []

    def test_generic_careers_url_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(job_url="https://example.com/careers")
        write_job(output_dir / "verified" / "ai-engineer", "bad.json", job)
        result = _run_validate_presentation(str(output_dir), "ai-engineer")
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert output["passed"] is False
        assert len(output["violations"]) >= 1

    def test_null_active_status_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(active_status=None)
        write_job(output_dir / "verified" / "ai-engineer", "null.json", job)
        result = _run_validate_presentation(str(output_dir), "ai-engineer")
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert any("active_status" in v for v in output["violations"])

    def test_expired_in_active_list_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(active_status="expired")
        write_job(output_dir / "verified" / "ai-engineer", "expired.json", job)
        result = _run_validate_presentation(str(output_dir), "ai-engineer")
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert any("expired" in v.lower() for v in output["violations"])

    def test_mixed_valid_and_invalid(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "ai-engineer", "good.json", make_valid_job())
        write_job(output_dir / "verified" / "ai-engineer", "bad-url.json",
                   make_valid_job(job_url="https://example.com/jobs"))
        write_job(output_dir / "verified" / "ai-engineer", "null-status.json",
                   make_valid_job(active_status=None))
        result = _run_validate_presentation(str(output_dir), "ai-engineer")
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert len(output["violations"]) >= 2

    def test_multiple_role_types(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "ai-engineer", "good.json", make_valid_job())
        write_job(output_dir / "verified" / "founder-s-associate", "bad.json",
                   make_valid_job(active_status="expired"))
        result = _run_validate_presentation(str(output_dir), "ai-engineer,founder-s-associate")
        assert result.returncode == 1
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_validate_presentation.py -v` — expect FAIL
- Lint: `ruff check 03_agents/tests/v25/tests/test_validate_presentation.py`

#### Step 8: Implement validate-presentation subcommand
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify

Add URL validation helpers and the subcommand after verify-before-archive:

```python
# ---------------------------------------------------------------------------
# validate-presentation subcommand
# ---------------------------------------------------------------------------

# Generic career page patterns — only checked for URLs that classify_url()
# returns "unknown" for. Known source/aggregator URLs bypass this check entirely
# via the classify_url delegation at the top of _is_specific_job_url.
_GENERIC_CAREER_PATTERNS = [
    r"^https?://[^/]+/careers/?$",
    r"^https?://[^/]+/jobs/?$",
    r"^https?://[^/]+/careers/?\?",
    r"^https?://[^/]+/jobs/?\?",
    r"/careers/?#",
    r"/jobs/?#",
]


def _is_specific_job_url(url: str) -> bool:
    """Check if a URL points to a specific job listing (not a generic career page).

    Returns True if the URL matches a known ATS pattern, contains a job-ID-like
    path segment (4+ digits or UUID), is from a known source/aggregator, or has
    sufficient path depth (>2 segments after domain) suggesting a specific listing.

    NOTE: This function maintains _GENERIC_CAREER_PATTERNS alongside classify_url.
    The classify_url delegation at the top handles known sources/aggregators.
    The fallback heuristics (job-ID, path depth, generic patterns) only apply
    to unknown domains. Flag for future cleanup if unknown-URL heuristics grow.
    """
    if not url:
        return False

    # Known ATS sources and aggregators are always specific enough
    classification = classify_url(url)
    if classification["type"] in ("source", "aggregator"):
        return True

    # Check for job-ID-like path segment: 4+ digits or UUID
    path_segments = url.split("/")
    for segment in path_segments:
        if re.match(r"^\d{4,}$", segment):
            return True
        if re.match(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
                     segment, re.IGNORECASE):
            return True

    # Reject generic career page patterns
    for pattern in _GENERIC_CAREER_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return False

    # Path depth heuristic: URLs with >2 meaningful path segments after domain
    # (e.g., careers.stripe.com/listing/senior-engineer) are likely specific
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        meaningful_segments = [s for s in parsed.path.split("/") if s]
        if len(meaningful_segments) > 2:
            return True
    except Exception:
        pass

    # Unknown URL with no job ID and shallow path — reject conservatively
    return False


def _cli_validate_presentation(args: argparse.Namespace) -> None:
    """CLI validate-presentation: check verified JSONs are presentation-ready."""
    output_dir = Path(args.output_dir)
    verified_dir = output_dir / "verified"
    role_types = [rt.strip() for rt in args.role_types.split(",") if rt.strip()]

    violations: list[str] = []

    for role_type in role_types:
        role_dir = verified_dir / role_type
        if not role_dir.is_dir():
            continue

        for json_file in sorted(role_dir.glob("*.json")):
            if json_file.name.startswith("_"):
                continue

            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                violations.append(f"{json_file.name}: JSON read error - {exc}")
                continue

            job_url = data.get("job_url", "")
            active_status = data.get("active_status")

            if not _is_specific_job_url(job_url):
                violations.append(
                    f"{json_file.name}: job_url is a generic career page, "
                    f"not a specific listing - {job_url}"
                )

            if active_status is None:
                violations.append(f"{json_file.name}: active_status is null")

            if active_status == "expired":
                violations.append(
                    f"{json_file.name}: expired job in active verified list"
                )

    passed = len(violations) == 0
    result = {"passed": passed, "violations": violations}
    sys.stdout.write(json.dumps(result, indent=2) + "\n")

    if not passed:
        sys.exit(1)
```

Add argparse registration:

```python
    # --- validate-presentation ---
    vp_parser = subparsers.add_parser(
        "validate-presentation",
        help="Validate verified JSONs are presentation-ready",
    )
    vp_parser.add_argument(
        "--output-dir", dest="output_dir",
        default=str(Path(__file__).resolve().parent.parent / "output"),
        help="Base output directory",
    )
    vp_parser.add_argument(
        "--role-types", required=True,
        help="Comma-separated role type slugs to validate",
    )
    vp_parser.set_defaults(func=_cli_validate_presentation)
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_validate_presentation.py -v` — expect PASS (6 tests)
- Lint: `ruff check 03_agents/tests/v25/scripts/manage_state.py`

#### Step 9: Write test for enhanced validate-schema
**File:** `03_agents/tests/v25/tests/test_schema_url_validation.py`
**Action:** Create

```python
"""Tests for enhanced validate-schema URL and active_status checks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import make_valid_job, write_job

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run_validate_schema(output_dir: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MANAGE_STATE), "validate-schema", "--output-dir", output_dir],
        capture_output=True, text=True,
    )


class TestSchemaURLValidation:

    def test_valid_ats_url_passes(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "ai-engineer", "valid.json", make_valid_job())
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0

    def test_generic_careers_page_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(job_url="https://example.com/careers")
        write_job(output_dir / "verified" / "ai-engineer", "bad.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1

    def test_generic_jobs_without_id_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(job_url="https://example.com/jobs")
        write_job(output_dir / "verified" / "ai-engineer", "bad.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1

    def test_url_with_job_id_segment_passes(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(job_url="https://careers.example.com/positions/87654")
        write_job(output_dir / "verified" / "ai-engineer", "good.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0

    def test_url_with_uuid_passes(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(
            job_url="https://jobs.lever.co/acme/a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        write_job(output_dir / "verified" / "ai-engineer", "uuid.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0

    def test_null_active_status_after_verification_fails(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(active_status=None, verification_date="2026-03-20")
        write_job(output_dir / "verified" / "ai-engineer", "null.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 1

    def test_linkedin_url_passes(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        job = make_valid_job(job_url="https://www.linkedin.com/jobs/view/4344764433")
        write_job(output_dir / "verified" / "ai-engineer", "li.json", job)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0

    def test_pre_existing_valid_job_still_passes(self, tmp_path: Path) -> None:
        """Regression: a known-good fixture that passed before enhancements must still pass.

        Ensures new URL/active_status checks don't break existing validation rules.
        """
        output_dir = tmp_path / "output"
        known_good = make_valid_job(
            job_url="https://boards.greenhouse.io/acme/jobs/12345",
            score=85, status="verified",
        )
        write_job(output_dir / "verified" / "ai-engineer", "known-good.json", known_good)
        result = _run_validate_schema(str(output_dir))
        assert result.returncode == 0, f"Known-good fixture broke: {result.stderr}"
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_schema_url_validation.py -v` — expect FAIL (8 tests)
- Lint: `ruff check 03_agents/tests/v25/tests/test_schema_url_validation.py`

#### Step 10: Enhance validate-schema with URL + active_status checks
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify `_handle_validate_schema` function

In the per-file validation loop (around line 1047-1062), after the existing `score` type check and before `if file_errors`, add:

```python
                # URL quality check: reject generic career pages
                job_url = data.get("job_url", "")
                if job_url and not _is_specific_job_url(job_url):
                    file_errors.append(
                        f"job_url is a generic career page, not a specific listing - {job_url}"
                    )

                # active_status check: must be non-null after verification
                has_verification = (
                    "verification_date" in data
                    or "verified_at" in data
                    or data.get("active_status") in ("expired", "live")
                )
                if has_verification and data.get("active_status") is None:
                    file_errors.append(
                        "active_status is null after verification"
                    )
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_schema_url_validation.py -v` — expect PASS (8 tests)
- Lint: `ruff check 03_agents/tests/v25/scripts/manage_state.py`

#### Step 11: Write test for safety bound gap detection
**File:** `03_agents/tests/v25/tests/test_safety_bound_gap.py`
**Action:** Create

```python
"""Tests for _check_safety_bound gap-aware threshold adjustment.

When gap between last_run_date and today exceeds 7 days, threshold
auto-adjusts from 50% to 90%.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import manage_state


from conftest import make_valid_job


def _make_jobs_and_archive(total: int, archived: int, role: str = "ai-engineer"):
    jobs = []
    to_archive = {}
    for i in range(total):
        job = make_valid_job(
            job_id=f"job-{i}", company=f"Co{i}", title=f"Title{i}",
            score=80, role_type=role,
        )
        job["_filepath"] = Path(f"/tmp/fake/{role}/job-{i}.json")
        job["_role"] = role
        job["_filename"] = f"job-{i}.json"
        jobs.append(job)
    for i in range(archived):
        to_archive[jobs[i]["_filepath"]] = jobs[i]
    return jobs, to_archive


class TestSafetyBoundGap:

    def test_1_day_gap_uses_default(self) -> None:
        """1-day gap: 30% archival passes with 50% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 3)
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=yesterday, today=today)
        assert errors == []

    def test_7_day_gap_uses_default(self) -> None:
        """7-day gap: 60% archival fails with 50% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 6)
        today = datetime.now().strftime("%Y-%m-%d")
        seven_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=seven_ago, today=today)
        assert len(errors) > 0

    def test_8_day_gap_adjusts_to_90(self) -> None:
        """8-day gap: 60% archival passes with 90% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 6)
        today = datetime.now().strftime("%Y-%m-%d")
        eight_ago = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=eight_ago, today=today)
        assert errors == []

    def test_30_day_gap_adjusts_to_90(self) -> None:
        """30-day gap: 60% archival passes with 90% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 6)
        today = datetime.now().strftime("%Y-%m-%d")
        thirty_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=thirty_ago, today=today)
        assert errors == []

    def test_8_day_gap_still_rejects_above_90(self) -> None:
        """8-day gap: 95% archival still fails."""
        jobs, to_archive = _make_jobs_and_archive(20, 19)
        today = datetime.now().strftime("%Y-%m-%d")
        eight_ago = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=eight_ago, today=today)
        assert len(errors) > 0

    def test_no_last_run_date_uses_default(self) -> None:
        """None last_run_date: 60% fails with 50% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 6)
        today = datetime.now().strftime("%Y-%m-%d")
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=None, today=today)
        assert len(errors) > 0

    def test_default_args_both_none_uses_default(self) -> None:
        """Both last_run_date and today as None: falls back to 50% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 6)
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=None, today=None)
        assert len(errors) > 0  # 60% exceeds default 50%

    def test_default_args_30pct_passes(self) -> None:
        """Both args None, 30% archival: passes with default 50% threshold."""
        jobs, to_archive = _make_jobs_and_archive(10, 3)
        errors = manage_state._check_safety_bound(
            jobs, to_archive, last_run_date=None, today=None)
        assert errors == []
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_safety_bound_gap.py -v` — expect FAIL
- Lint: `ruff check 03_agents/tests/v25/tests/test_safety_bound_gap.py`

#### Step 12: Enhance _check_safety_bound with gap detection
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify `_check_safety_bound` function (around line 478)

Change the function signature and add gap detection logic:

**OLD signature:**
```python
def _check_safety_bound(
    jobs: list[dict[str, Any]],
    to_archive: dict[Path, dict[str, Any]],
) -> list[str]:
```

**NEW signature + gap detection:**
```python
def _check_safety_bound(
    jobs: list[dict[str, Any]],
    to_archive: dict[Path, dict[str, Any]],
    *,
    last_run_date: str | None = None,
    today: str | None = None,
) -> list[str]:
    """Check the safety bound per role type.

    Gap detection: if last_run_date is provided and gap > 7 days,
    threshold auto-adjusts from 50% to 90%.
    """
    threshold = SAFETY_BOUND_PCT
    if last_run_date and today:
        try:
            last_dt = datetime.strptime(last_run_date, "%Y-%m-%d")
            today_dt = datetime.strptime(today, "%Y-%m-%d")
            gap_days = (today_dt - last_dt).days
            if gap_days > 7:
                threshold = 90
                print(
                    f"WARNING: {gap_days}-day gap since last run - "
                    f"safety bound adjusted from {SAFETY_BOUND_PCT}% to {threshold}%",
                    file=sys.stderr,
                )
        except ValueError:
            pass
```

Then replace `SAFETY_BOUND_PCT` with `threshold` in the comparison:

```python
        if pct > threshold:
```

Also update the caller in `_cli_dedup` (around line 603):

```python
        state_path = output_dir.parent / "state.json"
        _last_run_date: str | None = None
        if state_path.exists():
            try:
                with open(state_path, encoding="utf-8") as f:
                    state_data = json.load(f)
                _last_run_date = state_data.get("last_run_date")
            except (json.JSONDecodeError, OSError):
                pass
        _today = run_date or datetime.now().strftime("%Y-%m-%d")
        bound_errors = _check_safety_bound(
            jobs, to_archive,
            last_run_date=_last_run_date, today=_today,
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_safety_bound_gap.py -v` — expect PASS (8 tests)
- Lint: `ruff check 03_agents/tests/v25/scripts/manage_state.py`

#### Step 13: Fix SyntaxWarning (IF7)
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify — line ~1408

**OLD:**
```python
    Uses regex-replace approach: if `dispatch_count: \d+` exists, replace in-place.
```

**NEW:**
```python
    Uses regex-replace approach: if ``dispatch_count: \\d+`` exists, replace in-place.
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -W error::SyntaxWarning -c "exec(open('scripts/manage_state.py').read())"` — expect no SyntaxWarning
- Lint: `ruff check 03_agents/tests/v25/scripts/manage_state.py`

#### Step 14: Write test for dedup --role-types slug format
**File:** `03_agents/tests/v25/tests/test_dedup_role_types_slug.py`
**Action:** Create

```python
"""Tests for dedup --role-types slug format requirement.

Confirms --role-types must use directory slug format (kebab-case).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import write_job

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


def _run_dedup(output_dir: str, *, role_types: str | None = None,
               no_safety_bound: bool = False) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(MANAGE_STATE), "dedup", "--output-dir", output_dir]
    if role_types is not None:
        cmd.extend(["--role-types", role_types])
    if no_safety_bound:
        cmd.append("--no-safety-bound")
    return subprocess.run(cmd, capture_output=True, text=True)


def _make_low_score_job(role: str) -> dict:
    return {"company": "TestCo", "title": "Junior Role", "score": 40,
            "job_url": f"https://example.com/jobs/{role}/123",
            "role_type": role, "location": "Remote", "source": "linkedin"}


class TestDedupRoleTypesSlugs:

    def test_slug_format_finds_files(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "founder-s-associate",
                   "testco-junior.json", _make_low_score_job("founder-s-associate"))
        result = _run_dedup(str(output_dir), role_types="founder-s-associate",
                           no_safety_bound=True)
        assert result.returncode == 0
        summary = json.loads(result.stdout)
        assert summary["total_input"] > 0

    def test_display_name_format_finds_zero_files(self, tmp_path: Path) -> None:
        """Display name format does NOT match directory slugs."""
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "founder-s-associate",
                   "testco-junior.json", _make_low_score_job("founder-s-associate"))
        result = _run_dedup(str(output_dir), role_types="Founder's Associate",
                           no_safety_bound=True)
        assert result.returncode == 0
        summary = json.loads(result.stdout)
        assert summary["total_input"] == 0

    def test_empty_role_types_returns_zero(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "output"
        write_job(output_dir / "verified" / "ai-engineer",
                   "job.json", _make_low_score_job("ai-engineer"))
        result = _run_dedup(str(output_dir), role_types="")
        assert result.returncode == 0
        summary = json.loads(result.stdout)
        assert summary["total_input"] == 0
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_dedup_role_types_slug.py -v` — expect PASS (documents existing behavior)
- Lint: `ruff check 03_agents/tests/v25/tests/test_dedup_role_types_slug.py`

#### Step 15: Implement verify-session-state-written subcommand
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify

Add after the verify-and-commit code block, before the CLI entrypoint:

```python
# ---------------------------------------------------------------------------
# verify-session-state-written subcommand
# ---------------------------------------------------------------------------


def _cli_verify_session_state_written(args: argparse.Namespace) -> None:
    """Verify that session-state.md was written for the current run date.

    Exits 0 if session-state.md exists and contains the run_date.
    Exits 1 if missing or stale.
    """
    session_path = Path(args.session_state_path)
    run_date = args.run_date

    if not session_path.exists():
        print(f"FAIL: session-state.md not found at {session_path}", file=sys.stderr)
        sys.exit(1)

    content = session_path.read_text(encoding="utf-8")
    if run_date and run_date not in content:
        print(
            f"FAIL: session-state.md does not contain run_date {run_date}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(json.dumps({"status": "ok", "session_state_path": str(session_path)}))
```

Add argparse registration in `main()`:

```python
    # --- verify-session-state-written ---
    vssw_parser = subparsers.add_parser(
        "verify-session-state-written",
        help="Verify session-state.md was written for the current run date",
    )
    vssw_parser.add_argument(
        "--session-state-path",
        required=True,
        help="Path to session-state.md",
    )
    vssw_parser.add_argument(
        "--run-date",
        required=False,
        default=None,
        help="Expected run date string to find in session-state.md",
    )
    vssw_parser.set_defaults(func=_cli_verify_session_state_written)
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python scripts/manage_state.py verify-session-state-written --help` — expect help text
- Lint: `ruff check 03_agents/tests/v25/scripts/manage_state.py`

#### Step 15b: Implement --check-only flag for verify-and-commit
**File:** `03_agents/tests/v25/scripts/manage_state.py`
**Action:** Modify — add `--check-only` flag to the `verify-and-commit` argparse registration and handler

In the `verify-and-commit` argparse registration (in `main()`), add:

```python
    vac_parser.add_argument(
        "--check-only",
        action="store_true",
        default=False,
        help="Check git status for uncommitted output files and exit non-zero without committing",
    )
```

In the `_cli_verify_and_commit` handler function, add at the top (before any commit logic):

```python
    if args.check_only:
        # Check for uncommitted changes in output directory
        result = subprocess.run(
            ["git", "status", "--porcelain", str(Path(args.output_dir))],
            capture_output=True, text=True,
        )
        uncommitted = [
            line for line in result.stdout.strip().splitlines()
            if line.strip()
        ]
        if uncommitted:
            print(
                f"FAIL: {len(uncommitted)} uncommitted output files detected",
                file=sys.stderr,
            )
            for line in uncommitted:
                print(f"  {line}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps({"status": "ok", "uncommitted_files": 0}))
        return
```

**Also create** `03_agents/tests/v25/tests/test_verify_and_commit_check_only.py`:

```python
"""Tests for verify-and-commit --check-only flag."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


class TestVerifyAndCommitCheckOnly:

    def test_check_only_clean_exits_zero(self, tmp_path: Path) -> None:
        """Clean git repo with no uncommitted output files exits 0."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"],
                       cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"],
                       cwd=str(tmp_path), capture_output=True)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / ".gitkeep").write_text("")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"],
                       cwd=str(tmp_path), capture_output=True)

        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "verify-and-commit",
             "--output-dir", str(output_dir), "--phase-label", "search",
             "--check-only"],
            capture_output=True, text=True, cwd=str(tmp_path))
        assert result.returncode == 0

    def test_check_only_dirty_exits_nonzero(self, tmp_path: Path) -> None:
        """Git repo with uncommitted output files exits non-zero."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"],
                       cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"],
                       cwd=str(tmp_path), capture_output=True)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / ".gitkeep").write_text("")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"],
                       cwd=str(tmp_path), capture_output=True)
        # Create uncommitted file
        (output_dir / "new-job.json").write_text('{"test": true}')

        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "verify-and-commit",
             "--output-dir", str(output_dir), "--phase-label", "search",
             "--check-only"],
            capture_output=True, text=True, cwd=str(tmp_path))
        assert result.returncode != 0
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_verify_and_commit_check_only.py -v` — expect PASS (2 tests)
- Lint: `ruff check 03_agents/tests/v25/tests/test_verify_and_commit_check_only.py`

#### Step 16: Mirror all Phase 2 changes to career-matching
**File:** `03_agents/career-matching/scripts/manage_state.py`
**Action:** Modify — apply identical changes from Steps 6, 8, 10, 12, 13, 15, 15b

**Verify:**
- Diff: `diff 03_agents/tests/v25/scripts/manage_state.py 03_agents/career-matching/scripts/manage_state.py` — must show zero differences
- Sync test: `cd 03_agents/tests/v25 && python -m pytest tests/test_manage_state_sync.py -v` — expect PASS

#### Step 17: Commit Phase 2
**Action:** Git commit

```bash
git add 03_agents/tests/v25/tests/conftest.py \
       03_agents/tests/v25/tests/test_verify_before_archive.py \
       03_agents/tests/v25/tests/test_validate_presentation.py \
       03_agents/tests/v25/tests/test_schema_url_validation.py \
       03_agents/tests/v25/tests/test_safety_bound_gap.py \
       03_agents/tests/v25/tests/test_dedup_role_types_slug.py \
       03_agents/tests/v25/tests/test_verify_and_commit_check_only.py \
       03_agents/tests/v25/scripts/manage_state.py \
       03_agents/career-matching/scripts/manage_state.py
git commit -m "feat(jsa): add verify-before-archive, validate-presentation, --check-only flag, enhance schema+safety-bound, fix SyntaxWarning — 6 test suites"
```

---

### Phase 3: L2 — Gate Chaining + Documentation (Steps 18-26)

#### Step 18: Add batch progression gates to orchestration.md
**File:** `03_agents/tests/v25/references/orchestration.md`
**Action:** Modify

Insert a new `### Batch Progression Gates (MANDATORY)` section BEFORE the existing `### Channel Dispatch` section:

```markdown
### Batch Progression Gates (MANDATORY)

BEFORE dispatching any search batch (including the initial 5-channel dispatch), verify the previous batch was committed:

1. **Commit gate:** Run `python3 scripts/manage_state.py verify-and-commit --phase-label search --output-dir output --check-only` (via gate-check subagent). The `--check-only` flag checks git status for uncommitted output files and exits non-zero WITHOUT committing (Python-level structural gate — not prose). If exit code is non-zero, STOP — previous batch not committed. Do NOT dispatch the next batch until this passes.
2. **Session-state gate:** Run `python3 scripts/manage_state.py verify-session-state-written --session-state-path output/session-state.md --run-date {run_date}` (via gate-check subagent). If exit code is non-zero, STOP — session state not written for previous batch.

These gates apply to re-dispatches and retries, not only the initial dispatch. Skip only for the very first batch of a fresh session (no previous batch exists).

**Mandatory dispatch variables (HC10):** Every channel dispatch MUST include these variables:
- `working_dir` — absolute path to the agent working directory
- `output_directory` — path to the output directory
- `sentinel_path` — path to the `.done` sentinel for this channel
```

**Verify:**
- Lint: `grep -c 'Batch Progression Gates' 03_agents/tests/v25/references/orchestration.md` — expect 1
- Lint: `grep -c 'Mandatory dispatch variables' 03_agents/tests/v25/references/orchestration.md` — expect 1

#### Step 19: Add presentation gate to orchestration.md
**File:** `03_agents/tests/v25/references/orchestration.md`
**Action:** Modify

Insert a `### Pre-Presentation Validation Gate (MANDATORY)` section BEFORE the existing Phase 4 `### Steps` in the Present section:

```markdown
### Pre-Presentation Validation Gate (MANDATORY)

BEFORE presenting results to the user, dispatch a gate-check subagent to run:

```bash
python3 scripts/manage_state.py validate-presentation --role-types {active_role_types} --output-dir output
```

**Gate: `validate-presentation`** — MUST pass before presenting. Blocks progression. No skip option.
- Exit code 0: Proceed to presentation.
- Exit code non-zero: Fix violations first. Re-dispatch gate-check after correction.
```

**Verify:**
- Lint: `grep -c 'Pre-Presentation Validation Gate' 03_agents/tests/v25/references/orchestration.md` — expect 1

#### Step 20: Add verify-before-archive gate to orchestration.md
**File:** `03_agents/tests/v25/references/orchestration.md`
**Action:** Modify

Insert a new step in the Phase 3 (Dedup) steps, before the existing "Log dedup actions" step:

```markdown
4. **Verify-before-archive gate (MANDATORY for removals).** BEFORE recommending removal of any job, dispatch a gate-check subagent:

   ```bash
   python3 scripts/manage_state.py verify-before-archive --input {json_path}
   ```

   - If status is NOT `expired`, do NOT recommend removal.
   - Applies to ALL removal paths: dedup archival, score-threshold archival, manual removal.
```

Renumber subsequent steps (existing 4→5, 5→6, 6→7, 7→8).

**Verify:**
- Lint: `grep -c 'verify-before-archive' 03_agents/tests/v25/references/orchestration.md` — expect >=2

#### Step 21: Resolve foreground/background contradiction (IF4)
**File:** `03_agents/tests/v25/CLAUDE.md`
**Action:** Modify

Find and replace the stale foreground-only text:

**OLD:**
```
**All subagent dispatches MUST be foreground-only.** Do NOT use background Task dispatches (`run_in_background: true`). Every subagent dispatch must block until completion so gate-checks can run immediately after. Background dispatches bypass gate enforcement and cause untracked state. (V23 regression.)
```

**NEW:**
```
**Gate enforcement with background dispatch:** All subagents dispatch with `background: true` (matching agent frontmatter). After receiving the background completion notification, the parent MUST run the applicable gate-check BEFORE proceeding to the next dispatch. Gates are enforced sequentially even though subagents run in background mode. Never skip a gate-check because the subagent already returned.
```

**Verify:**
- Test: `grep -c 'foreground-only' 03_agents/tests/v25/CLAUDE.md` — expect 0
- Test: `grep -c 'Gate enforcement with background dispatch' 03_agents/tests/v25/CLAUDE.md` — expect 1

#### Step 22: Resolve .done sentinel path contradiction (IF2)
**File:** `03_agents/tests/v25/references/orchestration.md`
**Action:** Modify

Replace the single `.done` sentinel reference with clarification of both sentinels:

**OLD:**
```
Each search-verify subagent writes a `.done` file to `.channels/{channel-name}.done` on completion.
```

**NEW:**
```
**Two distinct `.done` sentinels (do NOT confuse):**
- **Channel sentinel:** `.channels/{channel-name}.done` — written by the parent (or gate-check) after all search-verify subagents for that channel return. Checked by `verify-channels-dispatched`. Path: `.channels/{channel_name}.done`.
- **Role-type sentinel:** `output/verified/{role_type_slug}/.done` — written by each search-verify subagent as its mandatory final step. Signals verification for a specific role type is complete.

Both sentinels are required. The channel sentinel gates Phase 1 progression; the role-type sentinel gates per-role-type status checks.

**Mandatory dispatch variable:** Include `sentinel_path: "{working_dir}/output/.channels/{channel_name}.done"` in the dispatch variables template for each channel dispatch. This makes the sentinel path explicit and prevents hardcoding drift.
```

**Verify:**
- Test: `grep -c 'Two distinct' 03_agents/tests/v25/references/orchestration.md` — expect 1

#### Step 23: Strengthen recovery protocol / inline Python prevention (IF6)
**File:** `03_agents/tests/v25/CLAUDE.md`
**Action:** Modify

In the Recovery Protocol section, add inline Python prohibition:

**OLD:**
```
## Recovery Protocol

**All search-verify subagents MUST write `_summary.md`** — parent's ONLY view into results.

When a subagent completes work but fails to write `_status.json` or `_summary.md`:
1. Do NOT read individual verified JSONs in parent context.
2. Dispatch a recovery subagent to read verified files, count, extract title/company/score/location, and write `_status.json` + `_summary.md`.
3. After recovery, read `_summary.md` (not individual JSONs).
4. If recovery also fails, log and continue with other role types.
```

**NEW:**
```
## Recovery Protocol

**All search-verify subagents MUST write `_summary.md`** — parent's ONLY view into results.

**On subagent truncation or failure:** Re-dispatch with Sonnet tier. NEVER use parent inline Python as a workaround. The parent context MUST NOT run `python3 -c`, `python3 -m`, or any inline Python snippet — even for "simple" data extraction. All Python execution goes through named scripts dispatched to subagents, or the explicitly allowed parent CLI commands listed in Context Budget above.

When a subagent completes work but fails to write `_status.json` or `_summary.md`:
1. Do NOT read individual verified JSONs in parent context.
2. Dispatch a recovery subagent (Sonnet tier) to read verified files, count, extract title/company/score/location, and write `_status.json` + `_summary.md`.
3. After recovery, read `_summary.md` (not individual JSONs).
4. If recovery also fails, log and continue with other role types.
5. NEVER fall back to parent inline Python — even after multiple subagent failures.
```

**Verify:**
- Test: `grep -c 'inline Python' 03_agents/tests/v25/CLAUDE.md` — expect >=2

#### Step 24: Add JobSpy hard constraint (IF3)
**File:** `03_agents/tests/v25/CLAUDE.md`
**Action:** Modify — add HC12 after HC11

```markdown
12. **JobSpy channel MUST run `scripts/jobspy_search.py`.** WebSearch/WebFetch fallback is PROHIBITED for JobSpy aggregator results. If `jobspy_search.py` fails, log the failure and proceed to other channels — do NOT substitute with WebSearch/WebFetch queries to Indeed/LinkedIn/etc. (IF3: JobSpy integrity constraint.)
13. **`validate-presentation` MUST pass before any user-facing output.** Run `python3 scripts/manage_state.py validate-presentation --role-types {active_role_types} --output-dir output` before presenting results. Exit code non-zero blocks presentation. No skip option. (V25 expired-jobs-in-rankings regression.)
```

**Also modify:** `03_agents/tests/v25/references/subagent-search-verify.md`
Add before the search workflow step 1:

```markdown
**JobSpy hard constraint (HC12):** The JobSpy aggregator channel MUST use `scripts/jobspy_search.py`. WebSearch/WebFetch fallback is PROHIBITED for aggregator results. If `jobspy_search.py` fails after retry, log failure in `_status.json` and proceed to specialty sources — do NOT substitute WebSearch queries.
```

**Verify:**
- Test: `grep -c 'JobSpy' 03_agents/tests/v25/CLAUDE.md` — expect >=1
- Test: `grep -c 'HC12' 03_agents/tests/v25/references/subagent-search-verify.md` — expect 1

#### Step 25: Add subagent tier for data reads (IF11)
**File:** `03_agents/tests/v25/CLAUDE.md`
**Action:** Modify — add after the model tier "Source of truth" paragraph

```markdown
**Tier selection for data reads and scoring (IF11):** Data extraction from multi-file JSON sets (reading `output/verified/*/` directories, aggregating scores, building presentation tables) MUST use Sonnet tier. Search-verify subagents that perform profile-matching scoring MUST use Sonnet tier minimum. Haiku is restricted to mechanical tasks only: gate-checks, file moves, single-file reads, and simple pass/fail validations.
```

**Verify:**
- Test: `grep -c 'IF11' 03_agents/tests/v25/CLAUDE.md` — expect 1

#### Step 26: Commit Phase 3
**Action:** Git commit

```bash
git add 03_agents/tests/v25/CLAUDE.md \
       03_agents/tests/v25/references/orchestration.md \
       03_agents/tests/v25/references/subagent-search-verify.md
git commit -m "feat(jsa): wire 4 gate chains, resolve IF2/IF4 contradictions, strengthen IF3/IF5/IF6/IF11 enforcement"
```

---

### Phase 4: L3 — Preflight Enhancements + Tests (Steps 27-33)

#### Step 27: Add session-state.md touch to preflight.sh
**File:** `03_agents/tests/v25/scripts/preflight.sh`
**Action:** Modify

Insert after the critical checks pass and before `python3 scripts/manage_state.py cleanup`:

```bash
    # Verify requests library is available (required by verify-before-archive)
    if ! python3 -c "import requests" 2>/dev/null; then
        fail "CRITICAL: Python 'requests' library not installed (required by verify-before-archive)"
    fi

    # Ensure session-state.md exists (prevents Write tool failure on first attempt)
    if [[ ! -f "output/session-state.md" ]]; then
        mkdir -p output
        touch output/session-state.md
        echo "Created output/session-state.md (first run)"
    fi
```

**Verify:**
- Test: `bash -n 03_agents/tests/v25/scripts/preflight.sh` — expect no syntax errors

#### Step 28: Add agent memory printing to preflight.sh (IF5)
**File:** `03_agents/tests/v25/scripts/preflight.sh`
**Action:** Modify

In the non-critical checks section, after the existing agent-memory emptiness check loop, add:

```bash
        # Print agent memory contents so they are in parent context (HC4)
        for mem_file in .claude/agent-memory/*/MEMORY.md; do
            if [[ -f "$mem_file" ]]; then
                echo "=== Agent Memory: $mem_file ==="
                cat "$mem_file"
                echo ""
            fi
        done
```

**Verify:**
- Test: `bash -n 03_agents/tests/v25/scripts/preflight.sh` — expect no syntax errors

#### Step 29: Add sentinel path validation to preflight.sh
**File:** `03_agents/tests/v25/scripts/preflight.sh`
**Action:** Modify

In the STRUCTURE TIER block, before the final `if [[ "$FAILED" -ne 0 ]]; then exit 1; fi`, add:

```bash
    # Sentinel path consistency: orchestration.md and subagent-search-verify.md
    # Uses specific patterns (not bare filenames) to avoid false positives from
    # documentation text or backtick-wrapped references.
    if [[ -f "references/orchestration.md" && -f "references/subagent-search-verify.md" ]]; then
        ORCH_HAS_STATUS=$(grep -cE '(output|verified)/.*_status\.json' "references/orchestration.md" 2>/dev/null || echo "0")
        SV_HAS_STATUS=$(grep -cE '(output|verified)/.*_status\.json' "references/subagent-search-verify.md" 2>/dev/null || echo "0")
        ORCH_HAS_SUMMARY=$(grep -cE '(output|verified)/.*_summary\.md' "references/orchestration.md" 2>/dev/null || echo "0")
        SV_HAS_SUMMARY=$(grep -cE '(output|verified)/.*_summary\.md' "references/subagent-search-verify.md" 2>/dev/null || echo "0")

        if [[ "$ORCH_HAS_STATUS" -eq 0 || "$SV_HAS_STATUS" -eq 0 ]]; then
            fail "CRITICAL: Sentinel path pattern for _status.json missing from orchestration.md or subagent-search-verify.md"
        fi
        if [[ "$ORCH_HAS_SUMMARY" -eq 0 || "$SV_HAS_SUMMARY" -eq 0 ]]; then
            fail "CRITICAL: Sentinel path pattern for _summary.md missing from orchestration.md or subagent-search-verify.md"
        fi
    fi
```

**Verify:**
- Test: `bash -n 03_agents/tests/v25/scripts/preflight.sh` — expect no syntax errors

#### Step 30: Write gate chain regression tests
**File:** `03_agents/tests/v25/tests/test_gate_chains.py`
**Action:** Create

```python
"""Regression tests for gate chaining.

Tests that verify-and-commit, validate-presentation, and verify-before-archive
enforce their preconditions correctly.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import make_valid_job, write_job

MANAGE_STATE = Path(__file__).resolve().parent.parent / "scripts" / "manage_state.py"


class TestVerifyAndCommitGate:

    def test_clean_git_repo_exits_zero(self, tmp_path: Path) -> None:
        """Clean git repo with nothing to commit exits 0."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"],
                       cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"],
                       cwd=str(tmp_path), capture_output=True)
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / ".gitkeep").write_text("")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"],
                       cwd=str(tmp_path), capture_output=True)

        result = subprocess.run(
            [sys.executable, str(MANAGE_STATE), "verify-and-commit",
             "--output-dir", str(tmp_path / "output"), "--phase-label", "search",
             "--no-push"],
            capture_output=True, text=True, cwd=str(tmp_path))
        assert result.returncode == 0


class TestVerifyBeforeArchiveGate:
    """Tests unique to the verify-and-commit -> verify-before-archive gate chain.

    Note: validate-presentation pass/fail tests are already covered in
    test_validate_presentation.py — not duplicated here.
    """

    def test_aggregator_url_returns_unverified(self, tmp_path: Path) -> None:
        """Aggregator URL through gate chain returns unverified, not live."""
        from unittest.mock import MagicMock, patch
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        import manage_state

        job_file = tmp_path / "test.json"
        import json as _json
        job_file.write_text(_json.dumps(make_valid_job(
            job_url="https://www.indeed.com/viewjob?jk=abc123")), encoding="utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch("manage_state.requests.head", return_value=mock_response):
            result = manage_state.verify_before_archive(job_file)
        assert result["status"] == "unverified"
```

**Verify:**
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_gate_chains.py -v` — expect PASS (depends on Phase 1+2 implementation)
- Lint: `ruff check 03_agents/tests/v25/tests/test_gate_chains.py`

#### Step 31: Mirror preflight changes to career-matching
**File:** `03_agents/career-matching/scripts/preflight.sh`
**Action:** Modify — apply identical changes from Steps 27, 28, 29

Additionally, add a canonical source comment at the top of BOTH copies of preflight.sh:

```bash
# CANONICAL SOURCE: 03_agents/tests/v25/scripts/preflight.sh
# This file MUST be kept in sync with 03_agents/career-matching/scripts/preflight.sh.
# After any edit, run: diff 03_agents/tests/v25/scripts/preflight.sh 03_agents/career-matching/scripts/preflight.sh
```

**Also create** `03_agents/tests/v25/tests/test_preflight_sync.py` (mirrors `test_manage_state_sync.py`):

```python
"""CI guard: ensures preflight.sh copies are byte-identical."""

from pathlib import Path


CANONICAL = Path(__file__).resolve().parent.parent / "scripts" / "preflight.sh"
MIRROR = CANONICAL.parent.parent.parent.parent / "career-matching" / "scripts" / "preflight.sh"


def test_preflight_copies_are_identical() -> None:
    """Both copies of preflight.sh must be byte-identical."""
    assert MIRROR.exists(), f"Mirror file not found: {MIRROR}"
    canonical_text = CANONICAL.read_text(encoding="utf-8")
    mirror_text = MIRROR.read_text(encoding="utf-8")
    assert canonical_text == mirror_text, (
        "preflight.sh copies have drifted! "
        f"Canonical: {CANONICAL}, Mirror: {MIRROR}. "
        "Run: diff 03_agents/tests/v25/scripts/preflight.sh "
        "03_agents/career-matching/scripts/preflight.sh"
    )
```

**Verify:**
- Diff: `diff 03_agents/tests/v25/scripts/preflight.sh 03_agents/career-matching/scripts/preflight.sh` — must show zero differences
- Test: `cd 03_agents/tests/v25 && python -m pytest tests/test_preflight_sync.py -v` — expect PASS

#### Step 32: Run full test suite + integration validation
**Action:** Verify all tests pass, then run full verification suite as final sanity check. These commands were already run incrementally in Steps 1-16, but we re-run here to confirm nothing regressed during Phase 3-4 documentation and preflight changes.

```bash
cd 03_agents/tests/v25
python -m pytest tests/ -v
ruff check .
mypy scripts/manage_state.py --ignore-missing-imports
python -W error::SyntaxWarning -c "exec(open('scripts/manage_state.py').read())"
bash -n scripts/preflight.sh
python scripts/manage_state.py validate-url-type --help
python scripts/manage_state.py verify-before-archive --help
python scripts/manage_state.py validate-presentation --help
python scripts/manage_state.py verify-session-state-written --help
```

All must pass / display help text without error.

#### Step 33: Commit Phase 4
**Action:** Git commit. Use explicit file list (not `git add -A`).

```bash
git add 03_agents/tests/v25/scripts/preflight.sh \
       03_agents/career-matching/scripts/preflight.sh \
       03_agents/tests/v25/tests/test_gate_chains.py \
       03_agents/tests/v25/tests/test_preflight_sync.py
git commit -m "feat(jsa): preflight enhancements (session-state touch, memory print, doc validation) + gate chain regression tests + preflight sync test"
```

---

## Deployment Verification

### Pre-Deploy Checks

Run from `03_agents/tests/v25/`:

```bash
# 1. Full test suite
python -m pytest tests/ -v

# 2. Lint
ruff check scripts/manage_state.py tests/

# 3. Type check
mypy scripts/manage_state.py --ignore-missing-imports

# 4. Verify new subcommands parse
python scripts/manage_state.py validate-url-type --help
python scripts/manage_state.py verify-before-archive --help
python scripts/manage_state.py validate-presentation --help
python scripts/manage_state.py verify-session-state-written --help

# 5. No SyntaxWarning
python -W error::SyntaxWarning -c "exec(open('scripts/manage_state.py').read())"

# 6. Preflight syntax valid
bash -n scripts/preflight.sh

# 7. No debug artifacts in docs
grep -rn '<<<<<<\|>>>>>>\|TODO-REMOVE\|FIXME-DEPLOY' CLAUDE.md references/orchestration.md references/subagent-search-verify.md && echo "FAIL" && exit 1 || echo "PASS"
```

### Post-Deploy Checks

After committing to main, in a fresh shell:

```bash
cd 03_agents/tests/v25

# 1. Confirm commit
git log --oneline -1

# 2. Smoke-test preflight
bash scripts/preflight.sh

# 3. Re-run tests from clean state
python -m pytest tests/ -v --tb=short

# 4. Verify gate chain keywords in orchestration.md
grep -c 'validate-presentation' references/orchestration.md
grep -c 'verify-before-archive' references/orchestration.md
grep -c 'Batch Progression Gates' references/orchestration.md

# 5. Verify constraints in CLAUDE.md
grep -c 'JobSpy' CLAUDE.md
grep -c 'IF11' CLAUDE.md
grep -c 'inline Python' CLAUDE.md
```

### Rollback Plan

```bash
# Identify pre-V26 commit
git log --oneline | head -10

# Revert V26 commits
git revert --no-commit <v26-first-commit>..HEAD
git commit -m "revert: rollback V26 gate chaining + verification infrastructure"

# Verify rollback
cd 03_agents/tests/v25 && python -m pytest tests/ -v --tb=short
```

---

## Handoff Contract
- Total steps: 33 (Step 15b inserted, Phase 5 Steps 34-35 folded into Step 32), Total phases: 4
- Files created: `conftest.py`, `test_validate_url_type.py`, `test_verify_before_archive.py`, `test_validate_presentation.py`, `test_schema_url_validation.py`, `test_safety_bound_gap.py`, `test_dedup_role_types_slug.py`, `test_gate_chains.py`, `test_manage_state_sync.py`, `test_preflight_sync.py`, `test_verify_and_commit_check_only.py`, `Makefile`
- Files modified: `manage_state.py` (both copies, with canonical source comments), `CLAUDE.md`, `orchestration.md`, `subagent-search-verify.md`, `preflight.sh` (both copies, with canonical source comments)
- Verification sequence: pytest → ruff → mypy → SyntaxWarning check → preflight syntax → subcommand smoke tests
- Deployment verification: pre-deploy (7 checks), post-deploy (5 checks), rollback (3 steps)

<!-- STAGE COMPLETE: /plan, 2026-03-23 -->

<!-- STAGE COMPLETE: /revise after round 1, 2026-03-23 -->

<!-- STAGE COMPLETE: /revise after round 2, 2026-03-23 -->

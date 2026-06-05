# Research: Job Search Agent V9 Test Failures

## Current State

The career-matching is a **Claude-native agent** — no traditional codebase (no agent.py, no server). It runs via Claude CLI with:
- `CLAUDE.md` — Agent instructions defining behavior, workflows, principles
- `context.md` — Mutable user profile storing preferences, constraints, sources
- Python scripts — Helper utilities for job searching and email delivery
- Output files — JSON jobs, Markdown briefs and digests

### V9 Session Outcome

V9 **completed the core workflow** (onboarding → search → digest → briefs → email) but exposed **7 failure modes** that need architectural and implementation fixes.

**Session stats:**
- Duration: ~15 minutes active work
- Context usage: Exceeded 40% (user flagged mid-session)
- Wins: 6 | Failures: 7 | Edge cases: 2

---

## The 7 Failures

### Failure 1: "Lead" Title Not Excluded

**What:** "Growth & Community Lead @ Neya" ranked #1 despite "lead" being in exclude list.

**Root cause:** Title exclusion via `--exclude-titles` only applied to JobSpy results. WebFetch sources (Early & Exec newsletter) bypassed the filter entirely.

**Code reference:** `03_agents/tests/v9/scripts/jobspy_search.py:33-54` — `filter_jobs_by_title()` only runs on JobSpy output.

**Classification:** Implementation gap — inconsistent filtering across sources.

---

### Failure 2: Scoring Not Deterministic

**What:** User asked "how can we know rankings would be the same on a future run?"

**Root cause:** Scoring rubric exists only in agent reasoning, not persisted to `context.md`.

**Code reference:** No scoring rubric section in `03_agents/tests/v9/context.md`.

**Classification:** Architectural gap — scoring should be stored and reproducible.

---

### Failure 3: Digest and Briefs Out of Sync

**What:** Digest sent with Neya #1, but briefs excluded Neya after user correction.

**Root cause:** Agent generated briefs from corrected list but didn't regenerate digest from same data state.

**Code reference:** No digest workflow documented in `03_agents/tests/v9/CLAUDE.md:47-51`.

**Classification:** Workflow gap — no single source of truth enforcement.

---

### Failure 4: Context Burn from Raw JSON Reads

**What:** Context exceeded 40% at ~60 jobs worth of descriptions.

**Root cause:** Agent read full JobSpy JSON files (~500-1000 words per job × 60 jobs) directly into context.

**Code reference:** `03_agents/tests/v9/CLAUDE.md:36-39` — Context management section exists but has no preventive mechanism.

**Classification:** Implementation gap — "Conserve context" principle violated despite explicit instruction.

---

### Failure 5: WebFetch Sources Not Filtered

**What:** Jobs from Early & Exec newsletter weren't passed through seniority filter.

**Root cause:** No post-processing filter for WebFetch results — only JobSpy has `--exclude-titles`.

**Code reference:** Only `jobspy_search.py` has filtering; no universal filter script exists.

**Classification:** Implementation gap — inconsistent filtering approach.

---

### Failure 6: Newsletter Added Without Content Validation

**What:** Agent added "Early & Exec" as a source, but it's exec-focused (publishes "Early" and "Exec" editions).

**Root cause:** Source discovery step doesn't validate content matches user's seniority constraints.

**Code reference:** `03_agents/tests/v9/CLAUDE.md:21-26` — Source Discovery only checks accessibility, not content relevance.

**Classification:** Architectural gap — incomplete source validation.

---

### Failure 7: API Key Exposed in Transcript

**What:** Resend API key visible in session output.

**Root cause:** User provided key directly; agent used it inline instead of requiring `.env` storage.

**Code reference:** `03_agents/tests/v9/scripts/send_email.py:42-45` — Correctly reads from env var, but no guidance in CLAUDE.md about requiring .env setup.

**Classification:** Security gap — no credential handling guidance.

---

## Code References

### Scripts

| File | Lines | Purpose |
|------|-------|---------|
| `jobspy_search.py` | 128 | Searches Indeed/LinkedIn/Glassdoor with optional title filtering |
| `send_email.py` | 81 | Sends emails via Resend API with markdown→HTML conversion |

### Key Functions

- `jobspy_search.py:33-54` — `filter_jobs_by_title()`: Title exclusion logic (only applies to JobSpy)
- `jobspy_search.py:80-124` — `main()`: Executes search, applies filter, outputs JSON
- `send_email.py:42-45` — Reads `RESEND_API_KEY` from environment (correct pattern)
- `send_email.py:29-36` — `markdown_to_html()`: Basic markdown conversion

### Configuration

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent instructions (principles, workflows, capabilities) |
| `context.md` | User profile (skills, experience, constraints, sources) |
| `.claude/settings.local.json` | Permitted domains and API permissions |

---

## Patterns Found

### What Works

1. **One-question onboarding:** Clean profile extraction
2. **Multi-source search:** JobSpy + WebFetch combination
3. **Title filtering at script level:** `--exclude-titles` flag works for JobSpy
4. **Brief quality:** Complete structure with CV tailoring, cover letter points
5. **Email delivery:** Resend integration works end-to-end

### What Doesn't Work

1. **Filtering is source-specific:** Only JobSpy has filtering; WebFetch results bypass it
2. **Scoring is ephemeral:** Lives in agent reasoning, not persisted
3. **No single source of truth:** Digest and briefs can be generated from different data states
4. **Raw JSON burns context:** No summarization layer to prevent context overflow
5. **Source validation incomplete:** Checks accessibility but not content relevance

---

## Related Files

### V9 Test Environment
```
03_agents/tests/v9/
├── CLAUDE.md                    # Agent instructions
├── context.md                   # User profile (populated during session)
├── .claude/settings.local.json  # Permissions
├── scripts/
│   ├── jobspy_search.py         # Job search with title filtering
│   └── send_email.py            # Resend email delivery
└── output/
    ├── jobs/                    # Raw job JSON files (3)
    ├── briefs/                  # Application briefs (5)
    └── digests/                 # Email digests (2)
```

### Documentation
```
docs/plans/active/
├── jsa-v9-analysis.md           # Full session analysis (7 failures)
├── jsa-v9-design.md             # V9 design rationale
├── jsa-v9-plan.md               # V9 implementation plan
├── jsa-v9-reviews.md            # Multi-agent review rounds
└── jsa-v9-transcript.txt        # Complete session transcript (1317 lines)
```

---

## Historical Context

### Version History

| Version | Focus | Status |
|---------|-------|--------|
| V7 | Initial architecture | Completed |
| V8 | Multi-source, briefs | Completed |
| V9 | Clean test environment, failure discovery | Current |
| V10 | Fix V9 failures | Next |

### V9 Was Intentionally Minimal

V9 design doc (`jsa-v9-design.md`) explains: V9 was a **fresh start** test environment to discover failure modes, not to fix them. The 7 failures were expected outcomes, not bugs.

---

## Existing Fix Proposals (from V9 Analysis)

The `jsa-v9-analysis.md` proposes these fixes:

1. **Add `scripts/filter_jobs.py`** — Universal title filtering for any source
2. **Add `scripts/summarize_jobs.py`** — One-line summaries to prevent context burn
3. **Add `## Scoring Rubric`** to context.md template — Persisted, deterministic scoring
4. **Add `## Digest Workflow`** to CLAUDE.md — Single-pass generation from same data
5. **Update Source Discovery** — Include content validation step
6. **Add excluded titles** to context.md Constraints — Explicit storage

Code samples for `filter_jobs.py` and `summarize_jobs.py` are provided in `jsa-v9-analysis.md:147-230`.

---

## Summary

V9 exposed 7 failures across 3 categories:

| Category | Failures | Fix Type |
|----------|----------|----------|
| Filtering inconsistency | 1, 5 | New scripts + workflow |
| Scoring non-determinism | 2 | Template addition |
| Single source of truth | 3, 4 | Workflow documentation |
| Source validation | 6 | CLAUDE.md update |
| Security | 7 | Guidance addition |

The failures are **implementation-level fixes**, not architectural redesigns. V10 should be a refinement release.

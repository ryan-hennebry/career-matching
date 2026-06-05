# Research: Job Search Agent V14

## Context

V14 is the current release, built on V13's named subagent architecture. V13 proved end-to-end pipeline delivery: onboarding, search-verify across 2 role types, 17 verified jobs, 5 briefs, digest email with PDF attachment. All 8 V12 failures were addressed architecturally. V14 adds: design system upgrade (Newsreader + DM Sans, warm neutral palette), skills-as-templates pattern (replacing `references/subagent-*.md`), persistent state management (`state.json` + `manage_state.py`), HTML-only briefs output (no PDF rendering), onboarding subagent, 20-step orchestration workflow, scheduled runs via GitHub Actions, and a 14-test suite for state management.

This document captures the complete V14 codebase state.

---

## V14 Directory Structure

```
03_agents/tests/v14/
├── CLAUDE.md                          # Orchestrator instructions (20 workflow steps)
├── context.md                         # User profile, constraints, sources
├── state.json                         # Persistent job lifecycle tracking (cross-run)
├── .env.example                       # API key template
├── .env                               # (gitignored) Actual API keys
├── .gitignore
│
├── scripts/
│   ├── jobspy_search.py               # JobSpy wrapper (Indeed/LinkedIn/Glassdoor)
│   ├── filter_jobs.py                 # Title exclusion filter
│   ├── summarize_jobs.py              # Context-efficient one-line summaries
│   ├── manage_state.py                # State management: lifecycle, delta, expiry, actions
│   └── send_email.py                  # Resend API email sender (HTML body + HTML attachment)
│
├── references/
│   └── algorithms.md                  # Scoring rubric, normalization rules, CV parsing
│
├── .claude/
│   ├── agents/
│   │   ├── search-verify.md           # Named agent definition (skills: jsa-search-verify)
│   │   ├── brief-generator.md         # Named agent definition (skills: jsa-brief-generator)
│   │   ├── digest-email.md            # Named agent definition (skills: jsa-design-system, jsa-digest-email)
│   │   ├── briefs-pdf.md              # Named agent definition (skills: jsa-design-system, jsa-briefs-pdf)
│   │   └── onboarding.md             # Named agent definition (skills: jsa-onboarding)
│   ├── agent-memory/
│   │   ├── search-verify/MEMORY.md    # Source reliability, industry qualifiers, scoring notes
│   │   ├── brief-generator/MEMORY.md  # Research patterns, brief pitfalls
│   │   ├── digest-email/MEMORY.md     # Dark editorial links, 3 score tiers, zero-value rule
│   │   ├── briefs-pdf/MEMORY.md       # HTML only (no PDF), brief parsing, score badges
│   │   └── onboarding/MEMORY.md       # CV parsing patterns, source reliability
│   ├── skills/
│   │   ├── jsa-design-system.md       # Unified design system (Newsreader + DM Sans, warm neutrals)
│   │   ├── jsa-search-verify.md       # Search+verify template (14 variables)
│   │   ├── jsa-brief-generator.md     # Brief generation template (7 variables)
│   │   ├── jsa-digest-email.md        # Email HTML template (7 variables)
│   │   ├── jsa-briefs-pdf.md          # Briefs HTML compilation template (1 variable)
│   │   └── jsa-onboarding.md          # CV parsing + source discovery template (5 variables)
│   └── settings.local.json            # Permissions (WebFetch domains, Bash patterns)
│
├── .github/
│   └── workflows/
│       └── daily-digest.yml           # GitHub Actions scheduled run (07:00 UTC weekdays)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures: make_verified_json, verified_dir, empty_state
│   ├── fixtures/
│   │   └── verified-job-template.json # Fixture template for test verified JSONs
│   ├── test_filter_jobs.py            # 3 tests: exclusions, field preservation, no-op
│   ├── test_summarize_jobs.py         # 3 tests: format, max limit, NaN handling
│   └── test_manage_state.py           # 14 tests: state lifecycle, expiry, resurrection, delta, actions
│
└── output/                            # Generated artifacts (per-run)
    ├── session-state.md               # Human-readable run log (not checkpoint)
    ├── _delta.json                    # Computed delta (new_jobs, still_active, expired, rejected)
    ├── _onboarding_draft.json         # Structured profile + sources from onboarding subagent
    ├── _additional_sources.json       # Extra sources discovered during onboarding
    ├── jobs/
    │   ├── {role}-aggregator.json     # Raw JobSpy results
    │   └── {role}-filtered.json       # After title exclusions
    ├── verified/
    │   └── {role-slug}/
    │       ├── {company}-{title}.json # Verified job data
    │       ├── _status.json           # Completion status
    │       └── _summary.md            # Role type summary table
    ├── briefs/
    │   ├── {company}-{title}-brief.md # Application briefs (6 sections)
    │   ├── briefs-{date}.html         # Compiled briefs HTML (final output, viewed in browser)
    │   └── _status.json               # Completion status
    └── digests/
        ├── {date}-email.html          # Email body HTML
        └── _status.json               # Status + sent_at after delivery
```

---

## Named Subagent Architecture

### Pattern

Agent definitions live in `.claude/agents/{name}.md` with YAML frontmatter (name, description, model, tools, disallowedTools, skills, memory). All agents use `model: inherit` to inherit the parent's model. Each agent's instructions are preloaded via the `skills:` frontmatter field — skills in `.claude/skills/jsa-{name}.md` contain the full template and workflow. Parent dispatches via Task tool with `subagent_type: "{name}"` and a compact JSON blob of template variables. Named agents do NOT inherit parent CLAUDE.md — skills must be declared in frontmatter.

### Agent Definitions

| Agent | Tools | Skills | Variables | Purpose |
|-------|-------|--------|-----------|---------|
| `search-verify` | Bash, Read, Write, Glob, Grep, WebFetch, WebSearch | jsa-search-verify | 14 | Search sources, verify listings, score against profile |
| `brief-generator` | Bash, Read, Write, Glob, Grep, WebFetch, WebSearch | jsa-brief-generator | 7 | Company research + 6-section application brief |
| `digest-email` | Bash, Read, Write, Glob, Grep | jsa-design-system, jsa-digest-email | 7 | HTML email body with digest content |
| `briefs-pdf` | Bash, Read, Write, Glob, Grep | jsa-design-system, jsa-briefs-pdf | 1 | Compile briefs into styled HTML file (not PDF) |
| `onboarding` | Bash, Read, Write, Glob, Grep, WebFetch, WebSearch | jsa-onboarding | 5 | CV parsing + source discovery |

**Key design decisions:**
- `digest-email` and `briefs-pdf` have WebFetch and WebSearch disallowed — they are rendering-only agents, not research agents.
- All agents have NotebookEdit disallowed.
- No `pip`/`pip3` restriction on visual agents — no PDF rendering means no need for fpdf2/reportlab/pdfkit blocking.

### Agent Memory Contents

**search-verify:** WebFetch rate-limited after ~10-15 calls. Adding industry qualifiers (e.g., "crypto AI startup") prevents off-industry aggregator results. JobSpy "Marketing Associate" without qualifiers returns fashion/FMCG. Cross-reference via WebSearch when WebFetch fails (LinkedIn JS-rendered). Specialty sources (CryptocurrencyJobs, Web3.Career) yield better matches for crypto/AI roles. Many sources block WebFetch (403/404). Title exclusion must be applied manually to specialty source results. "Founder's Associate crypto AI startup" returns 0 results — drop industry qualifiers for FA, filter manually. `_summary.md` written after `_status.json`.

**brief-generator:** WebFetch often auto-denied in subagent — fallback to WebSearch. Run 2-3 parallel searches (company basics, job details, news). Always tail-check for `<!-- BRIEF COMPLETE -->` sentinel. Don't confuse similar company names on Glassdoor. Self-reported skills must be flagged with "Prepare to demonstrate."

**digest-email:** 7 variables (run_date, user_email, user_name, total_briefs, new_today, still_active, verified_dir). Does NOT read `state.json` — reads verified JSON from `output/verified/`. Links: dark editorial style `color:#1c1917` (NOT blue). Score accents: 3 tiers only (green 90+, default 80-89, muted stone 70-79). No red or amber. Zero-value rule: never show stat with value 0 in summary strip. Never use colored text for warnings. Gmail link override: `u + #body a { color: inherit !important }`.

**briefs-pdf:** HTML only — NO PDF rendering. Output is `briefs-{run_date}.html`. Chromium PDF pagination is fundamentally broken. Brief separators: bold border-top (`4px solid #1c1917`). Cover page with TOC and anchor links. Score badges use 3-tier design system. Salary warnings use secondary text color (#57534e) with bold label, no colored text.

**onboarding:** CV formats vary; use algorithms.md CV Parsing rules. Skill extraction patterns: comma-separated, bullet points, parenthetical, version numbers. Many specialty boards block WebFetch (403/404). Best results from Web3.Career, CryptocurrencyJobs, BeInCrypto Jobs, AI Jobs. WebSearch more reliable than WebFetch in subagent context.

---

## Orchestration Workflow (20 Steps)

1. Capture run date (`date +%Y-%m-%d`)
2. Git pull (interactive mode only) — ensures `state.json` is current from scheduled runs
3. Load state from `state.json`
4. Pre-run cleanup: if `last_run_date` differs from today, clean stale output directories. If same date, resume (don't clean).
5. Read `context.md` for profile, skills, constraints, sources, target role types
6. If profile section empty, dispatch onboarding subagent (5 variables: cv_path, existing_context_path, run_date, target_industries, target_roles). Agent writes `output/_onboarding_draft.json`. Parent presents draft to user for correction, then writes final `context.md`.
7. Prepare 14 template variables per role type (includes `industry_qualifiers`)
8. Dispatch search-verify subagents in sequential batches of 2-3 (avoid rate limiting)
9. After each batch: read `_status.json` files, checkpoint in `session-state.md` after every 3 role types
10. Read `_summary.md` for each completed role type
11. Cross-role-type deduplication (same company+title across role types — keep highest score)
12. Update state via `python3 scripts/manage_state.py sync` — syncs verified jobs, handles new/returning/expired lifecycle
13. Compute delta — read `output/_delta.json` for `new_jobs`, `still_active`, `expired_count`, `rejected_count`
14. Present results to user — "New Today" (card treatment for new jobs) and "Still Active" (compact table for returning jobs)
15. Collect user feedback — accept/reject per job, record via `record_action()`
16. Save state after user feedback
17. Dispatch brief-generator subagents for accepted jobs (7 variables each)
18. Dispatch digest-email (7 variables) + briefs-pdf (1 variable) in parallel
19. Send email (PARENT-ORCHESTRATED) — idempotency check, three-way briefs gate, `scripts/send_email.py` with `--body-file` + `--attachment` (HTML briefs file)
20. Write `output/session-state.md` as human-readable run summary

**HARD CONSTRAINTS:** (1) Never pass `model:` to Task tool — agents use `model: inherit`. (2) CSS is canonical in the design system skill — never embed CSS copies in prompts.

**AUTO-RETRY PROTOCOL:** First failure: retry once. Second failure: log error, continue. Never retry more than once per subagent per run.

**SCHEDULED RUNS:** When `$SCHEDULED_RUN` is set: skip onboarding, skip user feedback (steps 14-16), no briefs generated, digest-email only (no briefs-pdf), state committed to main by GitHub Actions.

---

## Design System (jsa-design-system.md)

| Property | Value |
|----------|-------|
| Heading font | Newsreader (serif), Google Fonts import |
| Body font | DM Sans (sans-serif), Google Fonts import |
| Heading fallback | `'Newsreader', 'Georgia', 'Times New Roman', serif` |
| Body fallback | `'DM Sans', 'Helvetica Neue', 'Arial', sans-serif` |
| H1 | Newsreader 28px, weight 600, line-height 1.25, letter-spacing -0.01em |
| H2 | Newsreader 22px, weight 600, line-height 1.3 |
| H3 | Newsreader 18px, weight 500, line-height 1.35 |
| Body | DM Sans 15px, weight 400, line-height 1.6, letter-spacing 0.01em |
| Table cell | DM Sans 14px |
| Table header | DM Sans 12px, weight 600, uppercase, letter-spacing 0.06em |
| Background | `#ffffff` |
| Background subtle | `#f8f8f6` (warm off-white) |
| Background inset | `#f0efeb` (table headers, panels) |
| Primary text | `#1c1917` (warm black) |
| Secondary text | `#57534e` |
| Tertiary text | `#a8a29e` |
| Borders | `#e7e5e4` |
| Border strong | `#d6d3d1` (section dividers) |
| Links | `#1c1917` (dark editorial, same as text-primary) |
| Link underline | `#d6d3d1` (stone gray, subtle) |
| Score green (90+) | text `#15803d`, bg `#f0fdf4` |
| Score default (80-89) | text `#1c1917`, bg `#f8f8f6` |
| Score muted (70-79) | text `#78716c`, bg `#f8f8f6` |
| Briefs HTML max-width | 800px, padding 48px 56px |
| Email max-width | 600px, padding 32px 24px |
| Email layout | Inline styles only, table-based (no flexbox/grid) |
| Rendering | HTML only — no PDF rendering anywhere |
| Brief separators | Bold border-top `4px solid #1c1917` (not page breaks) |
| Warnings/caveats | Bold text in secondary color (`#57534e`), never colored text |
| Aesthetic | Internal strategy document — clean, professional, editorial |

---

## Scoring Algorithm

### 100-Point Scale

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Required skills | 40 | `40 * (matched / total_required)` |
| Preferred skills | 20 | `20 * (matched / total_preferred)` |
| Experience fit | 15 | Exact=15, 1-level=10, 2+under=5, overqualified=10 |
| Industry match | 15 | Direct=15, related=10, neutral=5 |
| Location | 10 | Match=10, partial=5, none=0 |

### Thresholds

- 70+ = presented to user
- Below 70 = logged in session-state.md

### Skill Normalization

Maps aliases to canonical skills (e.g., `sql` -> `postgresql, mysql, database queries`). Full table in `references/algorithms.md`.

### Experience Level Mapping

| Level | Years | Title Signals |
|-------|-------|---------------|
| Junior | 0-2 | junior, associate, entry |
| Mid | 2-5 | Standard titles |
| Senior | 5-8 | senior, sr., staff |
| Lead | 8-12 | lead, principal, architect |
| Director+ | 12+ | director, vp, head of |

---

## Python Scripts

### jobspy_search.py
- Wraps python-jobspy for Indeed, LinkedIn, Glassdoor
- `--location`, `--country`, `--remote`, `--results 25`, `--exclude-titles`, `--output`
- Exclude-titles: comma-separated
- Output: JSON with `{query, location, remote, searched_at, count, excluded_by_title, jobs}`

### filter_jobs.py
- Universal title exclusion filter (post-aggregation)
- `--exclude-titles`: space-separated (not comma)
- Case-insensitive partial match
- Prints count: `Filtered 25 -> 18 (excluded 7)`

### summarize_jobs.py
- Context-efficient one-line summaries
- Format: `Title | Company | Location | Salary`
- `--max 20` (default), handles NaN salary values
- Prevents context burn from raw JSON

### manage_state.py
- State management library + CLI for daily delta tracking
- Tracks job lifecycle across runs: new, returning, expired, resurrected
- `State` dataclass: `last_run_date`, `jobs` (dict of `JobEntry`), `expired_jobs` (dict of `JobEntry`)
- `JobEntry` dataclass: title, company, score, role_type, source, first_seen, last_seen, active_status, job_url, location, requirements_met, user_action, expired_date, reappeared
- `load_state(path)` / `save_state(state, path)` — atomic writes via tempfile + os.replace
- `update_state(state, verified_dir, run_date, searched_role_types)` — scans verified directory, handles new/returning/expired jobs, 14-day expiry, resurrection from expired, role-type-scoped expiry
- `compute_delta(state, run_date)` — returns `{run_date, new_jobs, still_active, expired_count, rejected_count}`
- `record_action(state, job_key, action)` — records "accepted" or "rejected" on a job
- CLI: `python3 manage_state.py sync --verified-dir ... --run-date ... --searched-role-types ... --state ... --output ...`
- 14-day expiry: jobs not seen for 14+ days move to `expired_jobs`
- Resurrection: expired jobs reappearing get restored with `reappeared=True`, `user_action=None`, `expired_date=None`
- Role-type-scoped expiry: only jobs in searched role types can expire (unsearched role types preserved)

### send_email.py
- Resend API with HTML body + optional file attachment (HTML or PDF)
- `--to`, `--subject`, `--body-file` (required), `--attachment` (optional, single file)
- Auto-loads `.env` from parent directory
- Base64-encodes attachment regardless of file type
- Returns Resend email ID on success

---

## Verified Job JSON Schema

```json
{
  "title": "exact from listing",
  "company": "exact from website",
  "location": "...",
  "job_type": "Full-time",
  "work_arrangement": "Remote/Hybrid/In-person",
  "salary_min": null,
  "salary_max": null,
  "currency": null,
  "job_url": "extracted URL",
  "source": "...",
  "date_posted": "YYYY-MM-DD or null",
  "active_status": "confirmed/unverified",
  "industry": "...",
  "requirements_met": ["req: evidence"],
  "gaps": ["gap description"],
  "preferred_met": ["..."],
  "score": 85,
  "score_breakdown": {
    "required_skills": {"matched": 5, "total": 7, "points": 29, "calculation": "40 * (5/7) = 28.6"},
    "preferred_skills": {"matched": 3, "total": 5, "points": 12, "calculation": "20 * (3/5) = 12"},
    "experience_fit": {"points": 15, "calculation": "description of fit"},
    "industry_match": {"points": 15, "calculation": "description of match"},
    "location_match": {"points": 10, "calculation": "description of match"},
    "total": 85
  },
  "benefits": [],
  "notes": "optional context",
  "run_date": "2026-02-09",
  "verified_at": "2026-02-09"
}
```

---

## Brief Structure (6 Sections)

1. **Role Summary** -- Title, location, salary, score breakdown tree, requirements met, gaps, stretches
2. **Company Context** -- Snapshot (founded, employees, stage, product), recent signals, why this company, interview hooks (3-5), Glassdoor
3. **CV Tailoring Brief** -- Summary rewrite, bullet reorder, keywords, self-reported skill prep
4. **Cover Letter Brief** -- Hook, opening line, 3-4 talking points, structure
5. **Outreach Draft** -- Hiring manager (LinkedIn search) + personalized message OR "not identified"
6. **Application Checklist** -- Actionable steps

**Completion sentinel:** `<!-- BRIEF COMPLETE -->` must be last non-whitespace line. If missing, treated as corrupt/truncated.

---

## V14 Session Run Results (2026-02-09)

### Search Summary

| Role Type | Searched | Verified | Above 70 | Notes |
|-----------|----------|----------|----------|-------|
| Marketing Associate | ~50 | 3 | 2 | Aggregator off-target. Specialty sources (CryptocurrencyJobs) yielded 3. Mercuryo (63) below threshold. |
| Community Manager | ~45 | 5 | 4 | Aggregator "Community Manager crypto" returned 45 results. Synthesia (66) below threshold. |
| Founder's Associate | ~50 | 12 | 10 | JobSpy strong for this role. 2 below threshold: MAGIC AI (70), Greenpixie (70). |
| **Total** | **~145** | **20** | **16** | |

### Deduplication

No cross-role-type duplicates found.

### Below Threshold (4 jobs, 63-66)

Mercuryo (63), Synthesia (66). MAGIC AI (70) and Greenpixie (70) at exact threshold.

### Briefs Generated (4)

1. Anima -- Founder's Associate (95)
2. Linda AI -- Founders Associate (92)
3. Klink Finance -- Founder Associate (92)
4. Duku AI -- Founder Associate (90)

### Delivery

- Digest email: sent 2026-02-09
- Briefs HTML: `briefs-2026-02-09.html`, attached to email
- Recipient: ryanhennebry@gmail.com

### User Actions

- Accepted: Anima (95), Linda AI (92), Klink Finance (92), Duku AI (90)
- All other jobs: no action recorded

### State

- `state.json`: 21 jobs tracked, 0 expired, 0 rejected
- `_delta.json`: 21 new_jobs, 0 still_active (first run)

---

## V12-to-V13 Failure Fix Mapping

All 8 V12 failures were addressed. Status: all fixed architecturally, and V14 upgraded design quality.

| V12 Failure | V13 Fix | V14 Status |
|-------------|---------|------------|
| F1: Raw URLs in presentation | Reference footnote pattern (`[1]` with URLs below table) | Fixed |
| F2: Flat list instead of tables | Table format reinforced in CLAUDE.md | Fixed |
| F3: Briefs PDF used fpdf2 | Named agent with Playwright enforced | Fixed -- V14 eliminates PDF entirely (HTML only) |
| F4: Digest PDF used reportlab | Eliminated digest PDF -- digest is email HTML body | Fixed |
| F5: Inconsistent aesthetics | Unified `jsa-design-system.md` skill | Fixed -- V14 upgraded to Newsreader + DM Sans |
| F6: Email HTML didn't match PDF | Same design system applied via skill frontmatter | Fixed -- V14 uses same design system for email + briefs HTML |
| F7: Subagent couldn't send email | Email sending moved to parent orchestrator (step 19) | Fixed |
| F8: Salary note broke table | Asterisk `*` with footnote below URL list | Fixed |

---

## V13 Wins (10)

1. **Named subagent architecture worked.** 4 agents with frontmatter-declared skills, tools, memory. Parent dispatches compact JSON, agents read own templates. Context stays small.
2. **Onboarding flow clean.** One question at a time, CV parsed via pandoc, all fields stored correctly. Self-reported skills flagged.
3. **End-to-end pipeline delivered.** Search -> verify -> present -> feedback -> briefs -> digest -> PDF -> email. Full cycle completed.
4. **Design system unified across outputs.** Both digest email and briefs PDF used the same jsa-design-system.md skill. No more Fraunces-vs-Playfair-Display divergence.
5. **Parent-orchestrated email send.** No more Bash permission issues. send_email.py ran cleanly with `--body-file` + `--attachment`.
6. **Idempotency check on email send.** `_status.json` with `sent_at` prevents duplicate sends on resume.
7. **Reference footnote presentation.** Clean tables with `[N]` references and clickable URLs below. Salary concerns marked with `*`.
8. **Pre-run cleanup logic.** Stale output cleared for new runs, preserved for same-day resumes.
9. **Session state tracking.** `session-state.md` with Search Progress, Below Threshold, Briefs Generated, Delivery, Pipeline checkboxes.
10. **Briefs content quality strong.** 6-section briefs with thorough company research, specific CV tailoring advice, interview hooks, outreach draft.

---

## V13 Failures / Issues (9)

### F1: Design system uses generic system fonts -- output is "functional but plain"

The jsa-design-system.md specifies system sans-serif fonts, minimal colors, basic typography. Both digest email and briefs PDF look like developer documents, not professional strategy materials. User feedback: needs exceptional output quality.

**Root cause:** The design system was written as a basic CSS spec. The frontend-design skill was invoked at parent level but its output was never passed to subagents.

**V14 fix:** Complete design system rewrite. Newsreader (serif headings) + DM Sans (body). Warm neutral palette (stone tones). Dark editorial links. 3-tier score badges. **Resolved.**

### F2: Marketing Associate results were thin (3 from 43 searched)

JobSpy returned entirely off-target results for "Marketing Associate" (fashion, FMCG, consumer brands). Only specialty sources yielded target-industry matches.

**Root cause:** "Marketing Associate" is too generic as a search query.

**V14 fix:** Added `industry_qualifiers` as 14th variable for search-verify. Appends industry keywords to search queries. **Partially resolved** -- aggregator with qualifiers returns 0 results; specialty sources remain primary path.

### F3: Most Founder's Associate jobs marked "unverified"

7 of 7 above-threshold FA jobs had `active_status: "unverified"` -- the agent couldn't access LinkedIn listings to confirm they're still live.

**Root cause:** LinkedIn blocks WebFetch (JS-rendered pages, authentication walls).

**V14 status:** Cross-reference verification pattern documented in agent memory. Agents use WebSearch to find jobs on company careers pages, Lever, Greenhouse, Workable. Improved but not fully resolved -- some jobs remain unverified.

### F4: Brief agents couldn't access LinkedIn job descriptions

Several briefs note "full job description not available." Scoring and gap analysis were based on company research rather than actual requirements.

**Root cause:** Same LinkedIn access issue as F3.

**V14 status:** WebSearch workaround documented. Agents search StudySmarter, Workable, ZipRecruiter, Built In London for job details. Improved but not fully resolved.

### F5: Source discovery ran on Sonnet instead of Opus

The source discovery task was dispatched with explicit `model: sonnet`, degrading research quality.

**Root cause:** Developer error -- model override in Task dispatch.

**V14 fix:** HARD CONSTRAINT added: "Never pass `model:` to Task tool." All agents use `model: inherit` in frontmatter. **Resolved.**

### F6: Marketing Associate presentation missing quick notes

Initial presentation of Marketing Associate results omitted context notes. User had to call it out.

**Root cause:** Presentation format wasn't applied consistently across all role types.

**V14 fix:** Presentation workflow documented with explicit formatting rules in CLAUDE.md. Quick notes required for every company. **Resolved.**

### F7: Context usage at 58% -- above 50% target

Better than previous versions but still consuming too much context.

**Root cause:** Parent reads every individual verified JSON file. Brief agent prompts include full verified JSON + profile extract.

**V14 fix:** Search agents now write `_summary.md` per role type. Parent reads summaries instead of individual JSONs. **Partially resolved.**

### F8: Briefs PDF used multi-page A4 instead of single continuous page

MEMORY.md documented that Chromium poorly handles CSS page breaks. V13 used multi-page A4 format (33 pages). Risk of content cut-off.

**Root cause:** Template specified A4 format with `page-break-before: always`.

**V14 fix:** PDF rendering eliminated entirely. Output is HTML only (`briefs-{date}.html`), viewed in browser. Brief separators use bold border-top instead of page breaks. **Resolved.**

### F9: 2 specialty listings expired (Uphold, BitMEX)

In Marketing Associate search, 2 listings from specialty sources were found to be expired on verification.

**Root cause:** Specialty job boards don't consistently remove expired listings.

**V14 status:** Informational -- filtered during verification step (already happens). Agent memory documents expired listing patterns. **Unchanged.**

---

## GitHub Actions Scheduled Runs

**File:** `.github/workflows/daily-digest.yml`

- Schedule: `cron: '0 7 * * 1-5'` (07:00 UTC weekdays)
- Manual trigger: `workflow_dispatch`
- Concurrency: `jsa-daily-digest` group, cancel-in-progress: false
- Timeout: 30 minutes
- Environment: `SCHEDULED_RUN=true`, `ANTHROPIC_API_KEY`, `RESEND_API_KEY` from secrets
- Steps: checkout, setup Python 3.12, install deps (python-jobspy, resend, playwright), install Claude Code, verify settings.local.json permissions, run scheduled digest via `claude --model claude-opus-4-6 --print`, commit `state.json` + `session-state.md` to main
- Non-overlap: interactive runs don't commit state. Scheduled runs commit to main. Interactive sessions pull latest state on startup.

---

## Test Suite

### test_filter_jobs.py (3 tests)
- Excludes matching titles (case-insensitive)
- Preserves all fields on filtered jobs
- No exclusions returns all jobs

### test_summarize_jobs.py (3 tests)
- Output format contains title, company, location, salary
- Max jobs limit respected
- NaN salary values handled gracefully

### test_manage_state.py (14 tests across 7 classes)

| Class | Tests | Coverage |
|-------|-------|----------|
| TestStateInitialization | 2 | Empty state + load missing file |
| TestJobLifecycle | 5 | Returning jobs, 14-day expiry, new job delta, score update, user_action preserved |
| TestKeyDerivation | 1 | Key = `{role_type_slug}/{filename_stem}` |
| TestExpiryScoping | 1 | Only searched role types expire |
| TestExpiredJobResurrection | 2 | Resurrection + reappeared flag reset |
| TestDelta | 1 | still_active excludes rejected |
| TestRecordAction | 2 | Invalid action value + invalid key |

Shared fixtures in `conftest.py`: `make_verified_json()` (creates verified JSON from fixture template), `verified_dir` (tmp directory with role type subdirs), `empty_state` (fresh State instance).

---

## Historical Context (V7-V14)

| Version | Key Change | Outcome |
|---------|-----------|---------|
| V7 | First structured agent with CLAUDE.md | Basic pipeline, many manual steps |
| V8 | Subagent architecture, scoring rubric | 6 role types, 44 verified. Delivery broken. |
| V9 | 6 failure fixes from V8 | Improved but PDF/email still fragile |
| V10 | 6 more fixes, session management | 12 failures -- worst version |
| V11 | Complete rewrite (single-agent + subagent variants) | Architecture cleaner but still 8 issues |
| V12 | Compact JSON, subagent templates, presentation tables | 7 wins, 8 failures. Core pipeline solid, delivery broken. |
| V13 | Named subagents, unified design system, email-as-digest | 10 wins, 9 issues. End-to-end delivery works. Design quality gap. |
| V14 | Skills-as-templates, state management, design upgrade, HTML-only, scheduled runs | 20 jobs across 3 role types, 4 briefs, HTML delivery. Design system upgraded. |

**Trajectory:** Architecture stabilised in V12-V13. V14 completed the design system upgrade, eliminated PDF rendering, added persistent state management with cross-run delta tracking, introduced skills-as-templates pattern, and enabled scheduled runs via GitHub Actions. Remaining gaps: LinkedIn access for verification, aggregator ineffectiveness for niche industry marketing roles, some CLAUDE.md references still mention PDF.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3 (scripts), Markdown (briefs), HTML/CSS (email, briefs) |
| Job aggregation | python-jobspy (Indeed, LinkedIn, Glassdoor) |
| Email delivery | Resend API |
| State management | manage_state.py (Python dataclasses, atomic JSON writes) |
| Testing | pytest (20 tests across 3 test files) |
| Agent orchestration | Claude Code named agents with skills-as-templates |
| Scheduled automation | GitHub Actions (daily-digest.yml, weekday 07:00 UTC) |
| Browser automation | Playwright MCP (fallback for JS-rendered pages) |

---

## Delta: V14 Post-Build (2026-02-10)

### Files Changed

- **CLAUDE.md**: Rewritten from 15-step to 20-step workflow. Added HARD CONSTRAINTS section (never pass `model:` to Task, CSS canonical in design system), AUTO-RETRY PROTOCOL (retry once then continue), SCHEDULED RUNS section (`$SCHEDULED_RUN` env var), SESSION MANAGEMENT (state.json replaces session-state.md for persistence), steps 12-13 (manage_state.py sync + delta), steps 14-16 (New Today / Still Active presentation + user feedback + record_action), step 20 (session-state.md as human-readable log only).
- **context.md**: Reset for fresh onboarding. Populated profile with 20 sources table. Added `## Scoring & Algorithms` reference section.
- **state.json**: New file. Persistent job lifecycle tracking (20 jobs from 2026-02-09 run). Contains `last_run_date`, per-job `user_action`, `first_seen`, `last_seen`, `reappeared`, `expired_date`, and `expired_jobs`.
- **scripts/manage_state.py**: New script. State management library + CLI. Handles job lifecycle (new/returning/expired/resurrected), user actions, 14-day expiry, atomic writes, delta computation. CLI: `sync` subcommand.
- **scripts/send_email.py**: `--attachment` now handles HTML files (not just PDF).
- **.claude/agents/onboarding.md**: New agent. CV parsing + source discovery. 5 variables. Writes `output/_onboarding_draft.json`.
- **.claude/agents/briefs-pdf.md**: Updated -- explicitly "HTML file (not a PDF)". Added `jsa-briefs-pdf` skill.
- **.claude/agents/digest-email.md**: Updated -- now 7 variables (was 4). Added `jsa-digest-email` skill.
- **.claude/agents/search-verify.md**: Added `jsa-search-verify` skill. Now 14 variables (added `industry_qualifiers`).
- **.claude/agents/brief-generator.md**: Added `jsa-brief-generator` skill.
- **.claude/skills/jsa-design-system.md**: Complete rewrite. Newsreader (serif headings) + DM Sans (body). Warm neutral palette (stone tones). Dark editorial link styling (`#1c1917`, not blue). Score badges: 3 tiers only (green 90+, default 80-89, muted stone 70-79). Explicit "NO PDF rendering" rule.
- **.claude/skills/jsa-briefs-pdf.md**: New skill. HTML-only briefs with cover page TOC, anchor links, job title hyperlinking, two-column score tables.
- **.claude/skills/jsa-digest-email.md**: New skill. Card layout for New Today, compact table for Still Active. Gmail link color override. 7 variables.
- **.claude/skills/jsa-onboarding.md**: New skill. CV parsing, source discovery, `_onboarding_draft.json` schema.
- **.claude/skills/jsa-search-verify.md**: Migrated from `references/subagent-search-verify.md`. Added 14th variable (`industry_qualifiers`), `_summary.md` output, shell escaping notes.
- **.claude/skills/jsa-brief-generator.md**: Migrated from `references/subagent-brief-generator.md`.
- **references/subagent-briefs-pdf.md**: Deleted (moved to skill).
- **references/subagent-digest-email.md**: Deleted (moved to skill).
- **.github/workflows/daily-digest.yml**: New. GitHub Actions scheduled run (07:00 UTC weekdays). `SCHEDULED_RUN=true`. Commits state.json + session-state.md to main.
- **tests/conftest.py**: New. Shared fixtures: `make_verified_json`, `verified_dir`, `empty_state`.
- **tests/test_manage_state.py**: New. 14 tests across 7 classes covering state lifecycle, expiry, resurrection, delta, record_action.
- **All 5 agent memory files**: Updated with V14 learnings. briefs-pdf: "HTML only, NO PDF." digest-email: dark editorial links, 3 score tiers, zero-value rule.

### Assumptions Invalidated

- **`references/subagent-*.md` templates exist**: Deleted. Instructions moved to `.claude/skills/jsa-*.md` preloaded via agent frontmatter `skills:` field.
- **briefs-pdf produces PDF via Playwright**: Now HTML-only. Output is `briefs-{date}.html`. `_render_pdf.py` is a leftover artifact.
- **digest-email has 4 variables**: Now 7 (`run_date`, `user_email`, `user_name`, `total_briefs`, `new_today`, `still_active`, `verified_dir`).
- **search-verify has 13 variables**: Now 14 (added `industry_qualifiers`).
- **15-step orchestration**: Now 20 steps with state management, delta presentation, scheduled mode.
- **System sans-serif fonts**: Now Newsreader + DM Sans with warm neutral palette.
- **Score accents include amber/red**: Only 3 tiers (green, default, muted stone). No red or amber.
- **`session-state.md` for resume/checkpoint**: Now human-readable log only. `state.json` handles persistence.
- **`pip`/`pip3` blocked for visual agents**: No longer relevant -- no PDF rendering.
- **`send_email.py` sends PDF attachments**: Now sends HTML briefs attachment.

### New Patterns/Utilities

- **`scripts/manage_state.py`**: Full state management with job lifecycle, 14-day expiry, atomic writes, delta computation, user action recording.
- **`state.json`**: Cross-run persistence. Committed by scheduled runs.
- **`output/_delta.json`**: Computed delta (new_jobs, still_active, expired_count, rejected_count).
- **`output/_onboarding_draft.json`**: Onboarding subagent structured output.
- **Skills-as-templates pattern**: All subagent instructions in `.claude/skills/jsa-*.md`, preloaded via agent frontmatter.
- **New Today / Still Active presentation**: Card treatment for new; compact table for returning.
- **Scheduled runs via GitHub Actions**: `$SCHEDULED_RUN` skips onboarding, interactive feedback, briefs.
- **14-test suite**: Comprehensive TDD coverage of manage_state.py.

### Updated Code References

- **CLAUDE.md:7-13**: HARD CONSTRAINTS (never pass `model:`, CSS canonical in design system)
- **CLAUDE.md:94-103**: AUTO-RETRY PROTOCOL
- **CLAUDE.md:160-168**: Steps 12-13 manage_state.py sync + delta
- **CLAUDE.md:272-318**: PRESENTATION WORKFLOW (New Today / Still Active)
- **CLAUDE.md:339-349**: SCHEDULED RUNS section
- **scripts/manage_state.py:129-197**: `update_state()` core logic
- **scripts/manage_state.py:200-219**: `compute_delta()`
- **.claude/skills/jsa-design-system.md:12-27**: Google Fonts import
- **.claude/skills/jsa-design-system.md:189-220**: Link styling (dark editorial, Gmail override)
- **.claude/skills/jsa-design-system.md:458-468**: Rendering rules (HTML only, no PDF)

### Open Questions

1. `jsa-digest-email.md` line 102 still references `color:#2563eb` (blue) for links but MEMORY.md and design system say `color:#1c1917` (dark) -- skill file has a bug.
2. `_render_pdf.py` exists in output/briefs/ as a leftover artifact -- should be cleaned up or gitignored.
3. CLAUDE.md OUTPUTS section still references `application-briefs-{run_date}.pdf` -- needs updating to `.html`.
4. `send_email.py` `--attachment` flag: CLAUDE.md step 19 still references `.pdf` extension -- needs updating.

---

## Delta: V15 Post-Build (2026-02-11)

### Files Changed

- **`03_agents/tests/v15/CLAUDE.md`** (NEW): Complete V15 orchestrator, 409 lines. Added HARD CONSTRAINT #4 (read agent memory on startup), CORE RULES section (8 rules including preview.sh mandate, absolute path reporting), step 18b (post-render verification), SECURITY section with API key onboarding UX. `brief_requested` semantics NOT yet added (analysis fix #1 outstanding).
- **`03_agents/tests/v15/.claude/agents/briefs-html.md`** (NEW, renamed from `briefs-pdf.md`): Agent renamed to `briefs-html`. Skill changed to `jsa-briefs-html`. Explicitly states "No PDF rendering — output is HTML only."
- **`03_agents/tests/v15/.claude/agents/brief-generator.md`** (NEW): WebFetch and WebSearch now DISALLOWED (`disallowedTools: WebFetch, WebSearch, NotebookEdit`). Briefs generated from verified JSON + profile only, no live web research. Writes `_brief_generator_status.json` on failure.
- **`03_agents/tests/v15/.claude/agents/digest-email.md`** (NEW): Unchanged architecture from V14 concept. Added explicit "Does NOT read state.json" data access rule.
- **`03_agents/tests/v15/.claude/agents/search-verify.md`** (NEW): Same as V14.
- **`03_agents/tests/v15/.claude/agents/onboarding.md`** (NEW): Expanded from V14. Added detailed `_onboarding_draft.json` schema inline, null-handling for `target_industries`/`target_roles`, `_onboarding_status.json` failure path.
- **`03_agents/tests/v15/.claude/agent-memory/search-verify/MEMORY.md`** (populated): 30 lines of operational learnings from V15 run (JobSpy retry patterns, specialty source URLs, title exclusions, scoring patterns). All other 4 agent memory files are empty placeholders.
- **`03_agents/tests/v15/scripts/manage_state.py`** (NEW): Added `purge_expired()` function (removes expired jobs >90 days). Called in CLI sync. `VALID_ACTIONS` still `{"accepted", "rejected"}` — `brief_requested` not yet added.
- **`03_agents/tests/v15/scripts/preview.sh`** (NEW): HTML preview server on port 8800. Kills existing process, starts `python3 -m http.server`, health-checks, auto-opens in browser.
- **`03_agents/tests/v15/scripts/send_email.py`** (NEW): Identical to V14 functionally. Still uses `--body` CLI arg pattern for API keys (analysis fix #5 not yet applied).
- **`03_agents/tests/v15/scripts/filter_jobs.py`**, **`scripts/jobspy_search.py`**, **`scripts/summarize_jobs.py`** (NEW): Copied from V14 unchanged.
- **`03_agents/tests/v15/tests/test_manage_state.py`** (NEW): 16 tests across 7 classes (was 14 across 6 in V14). Added `TestPurgeExpired` (2 tests).
- **`03_agents/tests/v15/.github/workflows/daily-digest.yml`** (NEW): Cron changed to `0 6 * * 1-5` (was 07:00 UTC). Added staged-file verification loop (rejects unexpected staged files). Model pinned to `claude-opus-4-6`.
- **`03_agents/tests/v15/context.md`** (NEW): Pre-populated with user profile. Sources reduced to 6 (removed inaccessible sources). Two role types: Marketing Associate, Founder's Associate.
- **`.claude/regressions/jsa.md`** (MODIFIED): Added V15 section with 7 regressions from analysis.

### Assumptions Invalidated

- `briefs-pdf` agent → renamed to `briefs-html` (all references in research doc need updating)
- brief-generator has WebFetch/WebSearch access → V15 DISALLOWS both (speed optimization — no live company research, no hiring manager lookup, no Glassdoor/Crunchbase)
- 14 tests in test_manage_state.py → now 16 tests across 7 classes
- `VALID_ACTIONS = {"accepted", "rejected"}` → still true in source, but analysis demands `brief_requested` as third action (not yet implemented)
- Cron schedule 07:00 UTC → changed to 06:00 UTC
- Agent memory files have rich content → 4 of 5 are empty placeholders; only search-verify has operational learnings
- Sources table has ~20 entries → reduced to 6 in context.md
- `_render_pdf.py` exists as leftover → not present in V15, clean start
- V14 open questions 2-4 (PDF references) → resolved in V15

### New Patterns/Utilities

- **`scripts/preview.sh`**: Canonical HTML preview server, port 8800, auto-open, health-checked. CLAUDE.md CORE RULE #8 mandates its use.
- **`purge_expired()` in manage_state.py**: 90-day purge of expired jobs. Prevents unbounded state.json growth. Called in CLI sync.
- **Post-render verification (step 18b)**: Parent checks generated HTML for 4 things: link colors, score badge tiers, zero-count omission, no gray boxes. New validation pattern.
- **Staged-file verification in GitHub Actions**: Commit step validates only `state.json` and `output/session-state.md` are staged. Rejects unexpected files.
- **CORE RULES section**: 8 mandatory rules in CLAUDE.md (was implicit in V14). Includes absolute path reporting and preview.sh mandate.
- **HARD CONSTRAINT #4**: Read agent memory on startup — was implicit, now enforced.

### Updated Code References

- `CLAUDE.md:7-14` — HARD CONSTRAINTS (4 items, was 2)
- `CLAUDE.md:18-28` — CORE RULES (8 rules, new section)
- `CLAUDE.md:287-300` — Step 18b post-render verification (new)
- `CLAUDE.md:354-365` — SECURITY section with API key onboarding UX
- `CLAUDE.md:393-409` — OUTPUTS section (all HTML, no PDF)
- `scripts/manage_state.py:219-233` — `purge_expired()` (new function)
- `scripts/manage_state.py:259-260` — CLI sync calls `purge_expired()`
- `.github/workflows/daily-digest.yml:5` — Cron `0 6 * * 1-5`
- `.github/workflows/daily-digest.yml:51-58` — Staged-file verification loop (new)
- `.claude/agents/brief-generator.md:4` — `disallowedTools: WebFetch, WebSearch, NotebookEdit`
- `tests/test_manage_state.py:305-347` — `TestPurgeExpired` class (new)

---

## Handoff Contract

- **Files to modify**: `CLAUDE.md`, `context.md`, `state.json`, `scripts/manage_state.py` (add `brief_requested` action), all 5 agent definitions (`.claude/agents/*.md` — note `briefs-html.md` not `briefs-pdf.md`), all 6 skills (`.claude/skills/jsa-*.md` — note `jsa-briefs-html.md` not `jsa-briefs-pdf.md`), all 5 agent memory files, `tests/test_manage_state.py`, `tests/conftest.py`, `.github/workflows/daily-digest.yml`, `scripts/preview.sh`, `scripts/send_email.py`
- **Patterns to preserve**: Named agent architecture with frontmatter, skills-as-templates pattern, parent-orchestrated email send, `_status.json` completion signals, `<!-- BRIEF COMPLETE -->` sentinel, reference footnote presentation format, atomic state file writes, `_summary.md` per role type, post-render verification (step 18b), staged-file verification in GH Actions, preview.sh as canonical preview method, purge_expired in sync pipeline, brief-generator has NO web access (intentional speed optimization)
- **Hard constraints discovered**: (1) Never pass `model:` to Task tool, (2) CSS canonical in design system skill, (3) No PDF rendering anywhere, (4) Links must be dark editorial `#1c1917` (not blue), (5) Score accents 3 tiers only (no red/amber), (6) Never show zero-value stats in summary strip, (7) `state.json` is persistence (not session-state.md), (8) Digest-email does NOT read state.json, (9) `manage_state.py sync` must run before presentation, (10) Scheduled runs skip steps 14-16, (11) Read agent memory on startup — treat as hard constraints, (12) Use `scripts/preview.sh` for HTML preview (no ad-hoc servers), (13) State absolute file paths after generating output, (14) brief-generator must NOT use WebFetch/WebSearch (speed constraint), (15) Never write inline Python for state mutations — use CLI only, (16) Always provide source URL when requesting API keys, (17) Always offer scheduled run setup after first interactive session, (18) Selecting jobs for briefs must not reject unselected jobs
- **Open questions**: (1) `VALID_ACTIONS` still `{"accepted", "rejected"}` — does adding `brief_requested` need a new CLI subcommand or just extending the set? (2) brief-generator disallows WebFetch/WebSearch — was this intentional (speed) or error? If intentional, brief structure needs simplification (no Glassdoor, hiring manager, Crunchbase). (3) 4 of 5 agent memory files are empty — carry forward V14 memory content or rely on regressions file? (4) `send_email.py` / GH Actions `gh secret set` still uses `--body` flag for API keys — CLAUDE.md SECURITY section doesn't address stdin piping for gh secret setup.
- **Regression tests to include**: PDF generation must never be attempted, digest must not show blue links or zero-value sections, briefs must complete in <60s, session-state.md must be written after search batches, accept/reject semantics must preserve unselected jobs, email idempotency must check `_status.json` before send, git pull must execute at startup, API keys must not appear in bash command output
### User-Identified Issue: Source Discovery Quality (2026-02-11)

**Problem:** The search-verify subagent produced thin source output. Sources were correct but few and not niche enough to give the candidate a real edge. The quality of sources determines the quality of the entire downstream pipeline (scoring, briefs, digest).

**Current behavior:** Agent dispatches searches to a fixed list of ~6 sources from `context.md` (3 JobSpy aggregators + 3 specialty sites). No research phase to discover industry-specific or niche sources. No user approval of sources before searching.

**Desired behavior:**
1. Before searching, agent researches the best job boards for the user's specific target industries — including niche sources like email/Substack newsletters (e.g. Early & Exec), industry Slack communities with job channels, curated lists, and non-obvious high-value sources
2. Agent presents discovered sources to the user for approval/additions before proceeding with search
3. User can add specific sources the agent didn't find

**Classification:** This is a **design-level change** — the search stage needs a new research-first workflow with user confirmation gate, not just a fix to existing code.

---

- **Routing**: 7 implementation fixes + 1 architectural change (source discovery workflow) → **run `/design` next**

<!-- STAGE COMPLETE: /research [delta], 2026-02-11 -->

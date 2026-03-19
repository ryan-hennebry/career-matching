# Orchestration Reference

Five-phase workflow for the Job Search Agent. Parent reads this file on-demand during orchestration.

---

## Prerequisites (Version Transition)

When setting up a fresh clone or linking to a new Vercel project, run the following BEFORE the first pipeline execution:

```bash
vercel link --project jsa-dashboard --yes && vercel --prod --yes
```

This ensures the Vercel dashboard is linked to the project directory.

---

## State Architecture

| File | Owner | Purpose |
|------|-------|---------|
| `output/digests/_status.json` | digest-email subagent (write); parent (append `sent_at`/`to` after send) | Tracks email-sent status per run — authoritative idempotency gate |
| `output/session-state.md` | parent orchestrator | Tracks session progress — per-batch checkpoints + final run summary |
| `state.json` | parent orchestrator (via `manage_state.py` CLI) | Maps active/expired jobs across runs with lifecycle tracking |
| `output/_delta.json` | `manage_state.py sync` (write); parent (read) | Computed delta: new_jobs, still_active, expired, rejected counts |
| `output/verified/{role_type_slug}/_status.json` | search-verify subagent | Per-role-type search completion status |
| `output/verified/{role_type_slug}/_summary.md` | search-verify subagent | Per-role-type results summary — parent's ONLY view into subagent results |

---

## Context Budget

**Parent-callable tools (direct):**
- Task (dispatch subagents)
- Read (status files, session-state.md, _dashboard.md ONLY)
- git add, git commit, git push (via Bash)

**Subagent-only tools (NEVER called by parent):**
- All `manage_state.py` subcommands (dedup, verify-clean-working-tree, verify-channels-dispatched, verify-session-state-updated)
- WebFetch, WebSearch
- All script execution (python3 scripts/*)
- Write (source files, output files)

**Gate execution:** All verification gates (`verify-clean-working-tree`, `verify-channels-dispatched`, `verify-session-state-updated`) are invoked by a gate-check subagent dispatched by the parent. The parent reads the subagent's pass/fail result from its status output. The parent NEVER runs `python scripts/manage_state.py` directly.

---

## Phase 1: Search

5-channel parallel search with enforcement gates. Every run dispatches ALL 5 channels — no channel is optional.

### Active Role Types (Single Source of Truth)

The authoritative source for active role types is `context.md ## Target`. Extraction:

```bash
python3 scripts/manage_state.py list-active-role-types --context-path context.md
```

Both pre-search archival and `dedup --role-types` consume this same list. No other source of role types is valid.

### Clear Checkpoints

At the start of every new run, clear all phase checkpoints so gates enforce fresh completion:

```bash
python3 scripts/manage_state.py checkpoint clear
```

### Pre-Search Cleanup

Before dispatching any channels, archive role-type directories in `output/verified/` that are NOT in the active `--role-types` list. This is defense in depth against the stale-directory failure where old directories from prior runs caused dedup to incorrectly archive everything.

Dispatch a gate-check subagent to execute:

```bash
# Get active role types
ACTIVE=$(python3 scripts/manage_state.py list-active-role-types --context-path context.md)
# Archive directories not in active list
for dir in output/verified/*/; do
  slug=$(basename "$dir")
  if ! echo "$ACTIVE" | grep -q "$slug"; then
    mkdir -p output/archive/pre-search-cleanup/
    mv "$dir" output/archive/pre-search-cleanup/
  fi
done
```

Archival runs ONLY before search begins, never mid-phase. If `state.json` consistency matters, handle in a separate step after archival.

### Source Research Gate

Before dispatching search channels, check if `## Search Channels` exists in `context.md` with populated sources. If empty or missing, dispatch a `source-researcher` subagent (model: haiku) to populate the channels:

```
prompt: '{"working_dir": "<absolute_path>", "context_path": "context.md", "model": "haiku"}'
description: "Research and populate search channel sources"
subagent_type: "source-researcher"
```

The source-researcher reads `## Industries` + `## Target` from context.md and researches appropriate sources for each of the 5 channels. It writes the populated `## Search Channels` section (with subsections `### Direct Career Pages`, `### Industry Job Boards`, `### JobSpy Aggregator`, `### Niche Newsletters`, `### Web Search Discovery`) back to context.md.

### 5 Search Channels (ALL MANDATORY)

| Channel | Subagent | Model | Source |
|---------|----------|-------|--------|
| Direct Career Pages | search-verify | haiku | context.md `### Direct Career Pages` |
| Industry Job Boards | search-verify | haiku | context.md `### Industry Job Boards` |
| JobSpy Aggregator | search-verify | haiku | context.md `### JobSpy Aggregator` |
| Niche Newsletters | search-verify | haiku | WebSearch discovery based on Industries |
| Web Search Discovery | search-verify | haiku | WebSearch queries adapted to Industries + Target |

### Channel Dispatch (MANDATORY — 5-channel unconditional parallel)

All 5 search channels MUST be dispatched on every run. No channel may be skipped, deferred, or conditionally excluded. Dispatch all 5 in a single message (parallel):

1. **direct-career-pages** — search-verify subagent
2. **linkedin** — search-verify subagent
3. **indeed** — search-verify subagent
4. **builtin** — search-verify subagent
5. **google-jobs** — search-verify subagent

Each dispatch includes HC-10 mandatory variables: `working_dir` (absolute path to the repo root containing `context.md`, `scripts/`, and `output/`), `output_directory`, `dashboard_url`.

Failure to dispatch all 5 channels is a pipeline violation. If a channel returns zero results, that is acceptable — the channel was still dispatched.

**Common variables** (included in every channel's JSON blob):
- `working_dir` — absolute path to the repo root
- `output_directory` — `output/verified/`
- `dashboard_url` — from context.md `## Delivery` (HC10 mandatory)
- `model` — `haiku`
- `run_date` — session run date
- `role_types` — active role types from `list-active-role-types`

**Task ID Persistence:** After dispatching each search-verify subagent, append the task ID to `session-state.md ## Active Tasks`. Format: `- {task_id}: search-verify {channel-name} (dispatched {timestamp})`. This enables post-compaction recovery.

**Channel-specific additions:**

**Channel 1 — direct-career-pages:**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/verified/", "dashboard_url": "<url>", "model": "haiku", "run_date": "<date>", "role_types": [...], "channel": "direct-career-pages", "sources": [<from context.md ### Direct Career Pages>]}'
description: "Search direct career pages"
subagent_type: "search-verify"
```

**Channel 2 — linkedin:**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/verified/", "dashboard_url": "<url>", "model": "haiku", "run_date": "<date>", "role_types": [...], "channel": "linkedin", "sources": [<from context.md ### LinkedIn>]}'
description: "Search LinkedIn jobs"
subagent_type: "search-verify"
```

**Channel 3 — indeed:**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/verified/", "dashboard_url": "<url>", "model": "haiku", "run_date": "<date>", "role_types": [...], "channel": "indeed", "queries": [<from context.md ### Indeed>]}'
description: "Search Indeed jobs"
subagent_type: "search-verify"
```

**Channel 4 — builtin:**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/verified/", "dashboard_url": "<url>", "model": "haiku", "run_date": "<date>", "role_types": [...], "channel": "builtin", "queries": [<from context.md ### BuiltIn>]}'
description: "Search BuiltIn jobs"
subagent_type: "search-verify"
```

**Channel 5 — google-jobs:**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/verified/", "dashboard_url": "<url>", "model": "haiku", "run_date": "<date>", "role_types": [...], "channel": "google-jobs", "queries": [<discovery queries adapted to Industries + Target>]}'
description: "Search Google Jobs"
subagent_type: "search-verify"
```

Each search-verify subagent writes a `.done` file to `.channels/{channel-name}.done` on completion.

### SUBAGENT BUDGET

Search-verify subagents MUST operate within a hard budget:
- **Time budget:** 15 minutes per channel
- **Tool-use budget:** 50 tool calls per channel
- On budget exhaustion: write checkpoint with current count, write `.done` file, and return. Do NOT continue searching.

**Pre-run cleanup:** Cross-reference `state.json` active jobs before archiving or deleting verified files. Never blind-delete files that the dashboard depends on (V20/V21 regression).

### Per-Channel Commit Gate (MANDATORY)

After EACH channel's search-verify subagent returns, parent dispatches a gate-check subagent via Task tool:

```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "command": "python3 scripts/manage_state.py verify-and-commit --phase-label search --output-dir output", "gate_name": "commit-gate-{channel-name}"}'
description: "Gate-check: verify-and-commit for {channel-name}"
```

**Gate: `manage_state.py verify-and-commit`** — MUST pass before proceeding. Blocks progression. No skip option.
- Exit code 0 = clean or committed successfully. Proceed.
- Exit code 1 = push failure (transient). Retry gate-check. Do NOT skip.
- Exit code 2 = merge conflict or unrecoverable. STOP and alert user.

If gate-check fails: re-dispatch gate-check (max 1 retry, tracked in session-state.md `## Retry Log` as `{gate-name}: attempt {N}`). After 2 total attempts (1 original + 1 retry), STOP and alert user. Do NOT skip. This enforces incremental commits per-channel (6-version recurrence: V14/V16/V18/V19/V20/V21).

**Stderr reformatting (MANDATORY):** When a gate-check returns exit code 1 or 2, the parent MUST reformat the raw stderr output into the UX Protocol gate failure alert format before displaying to the user: `[GATE FAILED] {gate-name} — {reason}. Action: {next}.` Do NOT surface raw stderr directly — always apply the prescribed format.

**Post-dispatch directory verification (CR-12):** After the gate-check subagent returns, verify that the committed files exist in the expected output directories. State absolute file paths in the verification log.

### Per-Channel Session-State Gate (MANDATORY)

Same timing as the commit gate. The gate-check subagent also confirms `session-state.md` was written for this channel:

```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "command": "python3 scripts/manage_state.py verify-session-state-written --session-state-path output/session-state.md --run-date {run_date}", "gate_name": "session-state-gate"}'
description: "Gate-check: verify-session-state-written for {run_date}"
```

**Gate: `manage_state.py verify-session-state-written`** — MUST pass before proceeding. Blocks progression. No skip option.
- Exit code 0 = session-state.md contains today's date entry. Proceed.
- Exit code 1 = missing or stale. Re-dispatch gate-check. Do NOT skip.

(5-version recurrence: V14/V16/V18/V19/V21). State absolute file paths when reporting gate results (CR-7).

### Channel Verification Gate (MANDATORY)

After all 5 channels return, parent dispatches a gate-check subagent (model: haiku) to run:

```bash
python3 scripts/manage_state.py verify-channels-dispatched
```

This checks that all 5 channels have a `.done` file in `.channels/`. This gate MUST pass before proceeding. If gate-check fails: re-dispatch gate-check. Do NOT skip. Parent re-dispatches any missing channel (max 1 retry per channel).

### Cross-Role Dedup

After all channels complete and pass the channel verification gate, dispatch a gate-check subagent (model: haiku) to run:

```bash
ACTIVE=$(python3 scripts/manage_state.py list-active-role-types --context-path context.md)
python3 scripts/manage_state.py dedup --role-types $ACTIVE --output-dir output
```

This ensures dedup only operates on directories for currently active role types, preventing the V22 stale-directory failure.

### Schema Validation Gate

After all channels complete and before dedup runs, parent MUST dispatch a gate-check subagent (model: haiku) with mandatory variables (`working_dir`, `output_directory`, `dashboard_url` per HC10) to run schema validation:

```bash
python3 scripts/manage_state.py validate-schema --output-dir output
```

**This gate is BLOCKING.** Parent must check exit code:
- Exit code 0: PASS -- proceed to dedup.
- Exit code non-zero: STOP. Do NOT proceed to dedup. Print: "Schema validation failed -- fix search-verify output before continuing." Re-dispatch gate-check after correction. Do NOT skip.

Gate-check subagent writes result to `.channels/schema-validation.done` with `{"status": "pass"}` or `{"status": "fail", "errors": [...]}`.

**Gate order (post-search, MUST pass before proceeding to dedup):**
1. `verify-channels-dispatched` -- all 5 channels have `.done` files. MUST pass before proceeding. If gate-check fails: re-dispatch gate-check. Do NOT skip.
2. `validate-schema` (Schema Validation Gate above) -- all verified JSONs have 10 required fields. MUST pass before proceeding. If gate-check fails: re-dispatch gate-check. Do NOT skip.
3. `dedup` -- only after both gates above pass.

> **Note:** Startup sequence must include reading the repo's current agent-memory files before dispatching any search channels.

### Entry Criteria

- Startup sequence complete (run date captured, agent memory loaded, state loaded, context.md read)
- Profile exists in context.md (onboarding complete)
- All target role types read from `## Target` in context.md

### Exit Criteria

- All 5 channels dispatched and reported (`.done` files present)
- All per-channel commit gates passed (verify-clean-working-tree)
- All per-channel session-state gates passed (verify-session-state-updated)
- Channel verification gate passed (verify-channels-dispatched)
- Cross-role dedup complete
- Batch commit landed

### POST-CHECKPOINT

```bash
# Executed by gate-check subagent after all gates pass
python3 scripts/manage_state.py checkpoint write search --count N
git add output/.checkpoints/ output/verified/ output/session-state.md .channels/ && git commit -m "checkpoint(jsa): search complete — $(date +%Y-%m-%d)"
git push origin main
```

---

## Phase 2: Verify

Listing verification, fit scoring, and company context. Verification is handled by the search-verify subagent as part of Phase 1 dispatch — this phase documents the verification logic the subagent executes.

### PRE-GATE

```bash
# Executed by the verify subagent
python3 scripts/manage_state.py checkpoint validate search
```

If validation fails, STOP and report: "Phase 1 (Search) checkpoint missing — cannot proceed to Verify."

### Entry Criteria

- Phase 1 dispatched search-verify subagents
- Subagent has received its 15-variable JSON blob

### Steps (executed by search-verify subagent)

1. **Search sources.** Run `jobspy_search.py` for major boards. Use WebFetch for specialty sources listed in `sources_for_role`.

2. **Filter results.** Run `filter_jobs.py` to apply title exclusions from `exclude_titles`.

3. **Verify each listing.** For every candidate job:
   - Confirm listing is active (not expired/closed)
   - Extract exact title from listing (character-for-character)
   - Extract exact URL from page (never construct by pattern)
   - Extract company name as written on their website
   - If URL returns 404, mark as `active_status: "unverified"`

4. **Score against user profile.** For each verified listing, compute fit score using the 5-factor model (see `references/algorithms.md`):
   - Required skills (40 pts)
   - Preferred skills (20 pts)
   - Experience fit (15 pts)
   - Industry match (15 pts)
   - Location match (10 pts)
   - Apply salary penalty if applicable (-10 pts)
   - Show math for every score

5. **Write outputs.**
   - Individual verified JSONs: `output/verified/{role_type_slug}/{company_slug}-{title_slug}.json`
   - Status: `output/verified/{role_type_slug}/_status.json`
   - Summary: `output/verified/{role_type_slug}/_summary.md` (MANDATORY — parent's only view into results)

**Moderate trim (V21):** Keep listing analysis and requirement-by-requirement comparison. Drop external lookups (Crunchbase, hiring manager research, funding rounds) to keep brief generation under 60s.

### Exit Criteria

- `_status.json` written with `"complete"` or `"partial"` status
- `_summary.md` written with standard table format
- All verified JSONs contain: title, company, score, score_breakdown, active_status, job_url, location, requirements_met

### POST-CHECKPOINT

```bash
# Executed by the verify subagent
python3 scripts/manage_state.py checkpoint write verify --count N
git add output/.checkpoints/ output/verified/ && git commit -m "checkpoint(jsa): verify complete — $(date +%Y-%m-%d)"
```

---

## Phase 3: Dedup

Cross-role deduplication, same-URL dedup, and score threshold enforcement.

### PRE-GATE

```bash
# Executed by the dedup subagent
python3 scripts/manage_state.py checkpoint validate verify
```

If validation fails, STOP and report: "Phase 2 (Verify) checkpoint missing — cannot proceed to Dedup."

### Entry Criteria

- All search-verify batches complete (all role types have `_status.json`)
- `output/verified/` contains verified JSON files across role-type subdirectories

### Steps

1. **Read summaries (Step 12).** Read `_summary.md` for each completed role type. Do NOT read individual verified JSONs in parent context.

2. **Run dedup CLI (Step 13).** Execute in parent context (manage_state.py is a permitted parent CLI operation):

   ```bash
   python3 scripts/manage_state.py dedup --output-dir output
   ```

   This performs three operations in one pass:
   - **Cross-role dedup:** Scans all `output/verified/*/` directories (skipping `_`-prefixed files), identifies duplicate company+title filenames across role types, keeps highest-scoring copy, archives duplicates to `output/archive/`
   - **Same-URL dedup:** Within each role type, identifies listings with the same URL, keeps highest-scoring copy, archives duplicates
   - **Score threshold:** Archives jobs scoring below 70 (the `SCORE_THRESHOLD` constant in manage_state.py)

   **CLI flags (single source of truth — argparse in manage_state.py must match exactly):**
   - `dedup` — subcommand name
   - `--output-dir` — base output directory (default: `output/` relative to project root)
   - `--dry-run` — report duplicates without moving files (optional)

   Never write inline `python3 -c` for dedup. Always use this CLI subcommand.

3. **Selective cleanup (P6).** Run cleanup of temporary directories:

   ```bash
   python3 scripts/manage_state.py cleanup --output-dir output
   ```

   **CLI flags:**
   - `cleanup` — subcommand name
   - `--output-dir` — base output directory (default: `output/` relative to project root)
   - `--dry-run` — print actions without executing (optional)

   Removes: `output/raw/`, `output/search-results/`, `output/unverified/`

   **P9 (zsh safe cleanup):** For any ad-hoc file deletion outside manage_state.py, use `find -type f -delete` — never `rm -f dir/*`. Glob expansion fails silently when too many files match.

4. **Log dedup actions in session-state.md.** Append dedup summary (total input, archived, remaining) to the session-state checkpoint.

5. **Update state (Step 14).** Sync verified results into state.json:

   ```bash
   python3 scripts/manage_state.py sync \
     --verified-dir output/verified \
     --run-date {run_date} \
     --searched-role-types {comma_separated_role_types} \
     --state state.json \
     --output output/_delta.json
   ```

   **CLI flags (single source of truth):**
   - `sync` — subcommand name
   - `--verified-dir` — path to verified directory (required)
   - `--run-date` — session run date (required)
   - `--searched-role-types` — comma-separated list of role type slugs (required)
   - `--state` — path to state.json (default: `state.json`)
   - `--output` — path to write delta JSON (required)

6. **Read delta (Step 15).** Read `output/_delta.json` for `new_jobs`, `still_active`, `expired_count`, `rejected_count`.

7. **Incremental commit (interactive mode only, Step 11b continuation).** After dedup:

   ```bash
   git add output/ state.json
   git commit -m "chore(jsa): dedup + state sync — {run_date}"
   git push origin main
   ```

### Exit Criteria

- Dedup has run (duplicates archived to `output/archive/`, low-score jobs removed)
- `state.json` updated with current run data
- `output/_delta.json` written with delta classification
- Dedup summary logged in session-state.md
- Post-dedup commit landed (interactive mode)

### POST-CHECKPOINT

```bash
# Executed by the dedup subagent
python3 scripts/manage_state.py checkpoint write dedup --count N
git add output/.checkpoints/ output/verified/ output/_delta.json state.json && git commit -m "checkpoint(jsa): dedup complete — $(date +%Y-%m-%d)"
```

---

## Phase 4: Present

Format results tables, apply standardized table format, and run user feedback loop.

### PRE-GATE

```bash
# Executed by the present subagent
python3 scripts/manage_state.py checkpoint validate dedup
```

If validation fails, STOP and report: "Phase 3 (Dedup) checkpoint missing — cannot proceed to Present."

### Entry Criteria

- Phase 3 complete (dedup done, delta computed)
- `output/_delta.json` available with `new_jobs` and `still_active` lists
- All verified JSONs reflect post-dedup state

### Steps

1. **Present results to user (Step 16).** Use the presentation rules (see `references/presentation-rules.md`). Show per-role-type tables with "New Today" and "Still Active" subsections, then the Unified Selection View (all jobs ranked by score in one numbered list).

   Apply minimum score threshold: only present jobs scoring >= 70. If a role type has zero jobs above 70, present top 3 regardless of score with note: "No strong matches found. Here are the closest."

2. **Post-presentation verification (Step 16b, MANDATORY).** Verify dashboard URL was included:
   - If `context.md` `## Delivery` contains a `Dashboard:` line, the presentation MUST include `> View and manage all jobs at:` with the URL
   - If omitted, STOP and re-present the unified selection view with the URL included
   - Do NOT proceed to feedback until verified

3. **Collect user feedback (Step 17).** Ask which jobs the user wants briefs for. For selected jobs, record `brief_requested`:

   ```bash
   python3 scripts/manage_state.py record-action \
     --state state.json \
     --job-key "{key}" \
     --action "brief_requested"
   ```

   **CLI flags (single source of truth):**
   - `record-action` — subcommand name
   - `--state` — path to state.json (default: `state.json`)
   - `--job-key` — the job's key in state (required)
   - `--action` — one of: `accepted`, `rejected`, `brief_requested` (required)

   Do NOT reject unselected jobs — leave `user_action` as null. Only record `rejected` if user explicitly says "reject" for specific jobs.

4. **Optional Upstash rejection sync (Step 17b).** If `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` are set in `.env`:
   - Read action keys from Upstash via curl
   - For jobs where Upstash has `action == "rejected"`, skip brief generation even if selected
   - Log: "Skipping {job_title} at {company} -- rejected on dashboard"
   - If Upstash credentials not set, skip silently

### Exit Criteria

- User has seen all results in standardized table format
- Dashboard URL verified present (or confirmed absent from context.md)
- User selections recorded in state.json via `record-action` CLI
- Brief-requested jobs identified for Phase 5

### POST-CHECKPOINT

```bash
# Executed by the present subagent
python3 scripts/manage_state.py checkpoint write present --count N
git add output/.checkpoints/ state.json && git commit -m "checkpoint(jsa): present complete — $(date +%Y-%m-%d)"
```

---

## Phase 5: Deliver

Briefs generation, digest email with dashboard URL, and git commit.

### PRE-GATE

```bash
# Executed by the deliver subagent
python3 scripts/manage_state.py checkpoint validate present
```

If validation fails, STOP and report: "Phase 4 (Present) checkpoint missing — cannot proceed to Deliver."

### Entry Criteria

- Phase 4 complete (user feedback collected, brief_requested jobs identified)
- **Idempotency gate (MANDATORY):** Check `output/digests/_status.json` for `sent_at` field where `run_date` matches today's date. If `sent_at` exists AND `run_date` matches current session's `run_date`, the email has already been sent — skip email dispatch entirely. Log: "Email already sent for today's run -- skipping to avoid duplicate." This is the authoritative idempotency check at the orchestration layer; the delivery subagent retains its own defensive check but the parent gate is canonical.

### Steps (Tiered Delivery)

**Tier 1 — Mandatory (always executes):**

1. **Generate briefs (brief-generator x N).** For each `brief_requested` job, dispatch a brief-generator subagent. If 3+ briefs needed, dispatch all in a single message (parallel). After each brief completes, verify `output/briefs/{company_slug}-{title_slug}-brief.md` exists and last non-whitespace line is `<!-- BRIEF COMPLETE -->`. If sentinel missing, treat as corrupt.

   Task tool call per brief:
   ```
   prompt: '{"working_dir": "<abs_path>", "output_directory": "output/briefs/", "dashboard_url": "<url>", "job_title": "...", "company": "...", "company_slug": "...", "title_slug": "...", "run_date": "...", "profile_extract": "...", "job_json_with_verification": "..."}'
   description: "Generate brief for {job_title} at {company}"
   subagent_type: "brief-generator"
   ```

   After dispatching, append task ID to session-state.md `## Active Tasks`. State absolute file paths for all generated briefs (CR-7).

2. **Dispatch digest-email.** Dispatch digest-email subagent (mandatory, first delivery artifact):

   ```
   prompt: '{"working_dir": "<abs_path>", "output_directory": "output/digests/", "dashboard_url": "<url>", "run_date": "...", "user_email": "...", "user_name": "...", "total_briefs": N, "new_today": [...], "still_active": [...], "verified_dir": "output/verified/"}'
   description: "Generate digest email HTML"
   subagent_type: "digest-email"
   ```

   After dispatching, append task ID to session-state.md `## Active Tasks`. Verify completion via `output/digests/_status.json`.

   **Post-render file verification (MANDATORY):** `output/digests/{run_date}-email.html` must exist and be >0 bytes. If missing or empty, re-dispatch (max 1 retry).

   **Post-render style verification:** Parent reads generated HTML and checks: link colors are `#1c1917` (not `#2563eb`), score badges use only green/stone (no amber/red), zero-count sections omitted.

3. **Send email via send_email.py.** Parent-orchestrated. Do NOT ask user for send confirmation.

   ```bash
   python3 scripts/send_email.py \
     --to "{user_email}" \
     --subject "Job Search Update — {run_date}" \
     --body-file output/digests/{run_date}-email.html
   ```

   After successful send: update `output/digests/_status.json` with `sent_at` and `to` fields.

**Tier 2 — Budget-Gated (executes only if dispatch budget allows):**

4. **Budget check.** Read dispatch counter from session-state.md `## Budget` section:

   ```bash
   python3 scripts/manage_state.py check-dispatch-budget --session-state-path output/session-state.md
   ```

   - Exit code 0: under ceiling. Proceed to briefs-html.
   - Exit code 1: at or over ceiling. Skip to step 6.

5. **Dispatch briefs-html (conditional).** Only if budget check passed AND briefs were generated:

   ```bash
   python3 scripts/manage_state.py increment-dispatch-counter --session-state-path output/session-state.md
   ```

   ```
   prompt: '{"working_dir": "<abs_path>", "output_directory": "output/briefs/", "dashboard_url": "<url>", "run_date": "..."}'
   description: "Compile briefs into HTML"
   subagent_type: "briefs-html"
   ```

   After dispatching, append task ID to session-state.md `## Active Tasks`.

6. **Deferred logging + user notification.** If budget check failed (step 4 exit code 1) or zero briefs requested:
   - Log in session-state.md: "briefs-html deferred to next session — dispatch budget exhausted"
   - Emit user-facing message: "Briefs HTML deferred — dispatch budget reached. Will generate next session."
   - Skip briefs-html dispatch entirely

### Exit Criteria

- Briefs generated for all `brief_requested` jobs (or failures logged)
- Digest email HTML generated and style-verified
- Email sent (or skipped with logged reason)
- `output/digests/_status.json` updated with `sent_at` (if sent)
- Final run summary written to `output/session-state.md`
- Post-delivery commit landed (interactive mode)

### POST-CHECKPOINT

**Email idempotency guard:** Before sending, verify `_status.json` `sent_at` is not already set for today's date. If already sent, skip email and log "already sent" (V15 regression).

```bash
# Executed by the deliver subagent
python3 scripts/manage_state.py checkpoint write deliver --count N
git add output/.checkpoints/ output/session-state.md state.json && git commit -m "checkpoint(jsa): deliver complete — $(date +%Y-%m-%d)"
```

### Step 22: Scheduled Daily Runs via GitHub Actions

After the session completes, offer to set up scheduled daily runs using GitHub Actions. The workflow file (`.github/workflows/daily-digest.yml`) automates the full pipeline on a cron schedule (weekdays at 06:00 UTC). This enables hands-off daily execution without manual intervention.

Key details:
- Uses `workflow_dispatch` for manual triggers alongside the scheduled cron
- Runs the full pipeline with `SCHEDULED_RUN=true` environment variable
- Commits state changes and pushes automatically
- Includes post-deploy smoke test against the Vercel dashboard URL

---

### settings.local.json Additive Merge (V18 compliance)

When modifying `settings.local.json`, ALWAYS:
1. Read the existing file first (`json.load`)
2. Merge new entries into existing dict (additive, not overwrite)
3. Preserve all existing permissions and entries
4. Write back the merged result

NEVER overwrite `settings.local.json` with a fresh dict. This preserves user-configured permissions across runs.

**Bloat cap (V23):** If `settings.local.json` exceeds 50 entries after merge, log a warning and remove the oldest entries (by alphabetical key sort) to stay under 50. This prevents unbounded growth across runs.

---

### Vercel Dashboard Deploy (MANDATORY — once per session)

After the FINAL channel commit gate push in Phase 1 (i.e., after all 5 channels have been committed and pushed), dispatch a single subagent to redeploy the Vercel dashboard. Do NOT deploy after every individual channel push — this avoids triggering up to 5 redundant deploys. If Phase 5 send also pushes data, deploy once more after Phase 5 send completes.

```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "command": "vercel link --project jsa-dashboard --yes && vercel --prod --yes"}'
description: "Deploy Vercel dashboard after data push"
```

This is mandatory because the dashboard reads from the pushed data. Without redeployment, the dashboard shows stale results. (V21/V22 recurrence.)

---

## Post-Compaction Recovery Protocol

When context compaction occurs mid-session, follow this recovery sequence:

### Immediate Status (MANDATORY)

First user-visible output after compaction MUST be a 1-2 sentence summary of completed/pending work. Example:
> "Search complete for 5/5 channels. Proceeding to dedup and presentation."

No silent file reads before status. The user must see progress immediately.

### Task ID Recovery

All dispatched task IDs are persisted in session-state.md `## Active Tasks`. After compaction:

1. Read `session-state.md ## Active Tasks` to recover in-flight task IDs.
2. Check each task's status (completed, running, failed).
3. For completed tasks: read their output status files (`_status.json`, `_summary.md`).
4. For running tasks: wait for completion, then read outputs.
5. For failed tasks: re-dispatch (max 1 retry per subagent).

### Resume Logic

After recovery:
- Read `session-state.md ## Search Progress` to determine which phase to resume.
- Read `output/.checkpoints/` to determine last completed phase gate.
- Resume from the next uncompleted phase gate.
- NEVER reconstruct findings from conversation summary — re-dispatch subagents to get actual data (P2).

### State Absolute File Paths

When reporting recovery status, always state absolute file paths for:
- session-state.md location
- output directory location
- Any artifacts referenced in the recovery summary

---

### HC-10 Concrete Dispatch Templates

Every Task tool dispatch in orchestration.md MUST include `working_dir`, `output_directory`, and `dashboard_url` in the prompt JSON. The following templates are authoritative:

**Gate-check dispatch (commit gate):**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "command": "python3 scripts/manage_state.py verify-and-commit --phase-label {phase} --output-dir output", "gate_name": "commit-gate-{channel}"}'
```

**Gate-check dispatch (session-state gate):**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "command": "python3 scripts/manage_state.py verify-session-state-written --session-state-path output/session-state.md --run-date {run_date}", "gate_name": "session-state-gate"}'
```

**Recovery dispatch (post-compaction re-dispatch):**
```
prompt: '{"working_dir": "<abs_path>", "output_directory": "output/", "dashboard_url": "<url>", "recovery_context": "post-compaction", "failed_task_id": "{task_id}", "resume_phase": "{phase}"}'
description: "Recovery: re-dispatch {subagent_type} after compaction"
```

Search-verify, brief-generator, digest-email, and briefs-html templates already include HC-10 variables in their respective phase sections.

---

### Working Directory Validation (V19 compliance)

All dispatch prompts MUST set `working_dir` to the absolute repo-root path. NEVER use versioned `tests/v*` paths or relative `./` paths in dispatch prompts.

---

### Target Format Validation

After writing or modifying `context.md ## Target`, run:

```bash
python3 scripts/manage_state.py list-active-role-types --context-path context.md
```

Verify the output contains the expected number of clean slug entries (one per role type). Each slug must match `^[a-z0-9-]+$` (lowercase alphanumeric with hyphens only). If slug count does not match the number of bullet items in `## Target`, or any slug fails the format regex, STOP and fix the Target section formatting before proceeding.

---

## UX Protocol

Seven mandatory format rules for all user-facing output during orchestration.

### 1. Brief Progress (one-liner after each brief completes)

Format: `Brief {N}/{total} done — {company name}`

Emit this line immediately after each brief-generator subagent returns. Keeps the user informed without flooding the conversation. Full status table only once at end.

### 2. Proactive Timed Status (long-running phases)

Format: `Still running: {N}/{total} complete`

If a phase (search or brief generation) exceeds 90 seconds without user-visible output, emit this status line. Reset the timer after each emission.

**Implementation note:** Claude Code has no timer primitive. Parent counts tool-call round-trips as proxy. After ~3 consecutive subagent dispatches or gate-checks with no user-visible output, emit the timed status line.

### 3. Post-Compaction Immediate Status

First user-visible output after compaction MUST be a 1-2 sentence summary of completed/pending work. Never resume with a bare action or tool call — always orient the user first.

### 4. Unified Numbered Selection

When presenting jobs for user selection, use a single numbered list across all role types. Do not restart numbering per role type. The user picks by number; duplicate or reset numbering causes selection errors.

### 5. Section Headers with Counts

Format: `## {Role Type} ({N} new, {M} active)`

Every role-type section header in the presentation phase must include new and active counts. This gives the user an instant read on volume before scanning the table.

### 6. One Question at a Time (CR-4)

Ask one question per message. Never combine multiple questions in a single user-facing message. If you need answers to multiple things, ask the most important one first, wait for the response, then ask the next. This prevents user confusion and ensures clear signal per response.

### 7. Session Resume Prompt

When a digest was already sent today (detected during ON STARTUP), use this exact format:

`"A digest was already sent today ({sent_at}). Resume this session or abort? (resume/abort)"`

Do not rephrase or combine with other questions. Present this as a standalone decision prompt before any other action.

### End-of-Session Completion Summary

When the session completes successfully (all phases done, digest sent), emit:

`"Session complete: {N} new jobs found, {M} briefs generated, digest sent to {email}."`

This provides closure and confirms the session's output. Emit once, after Phase 5 send succeeds.

### Gate Failure Alert Format

When a gate-check fails, surface the failure to the user in this format:

`[GATE FAILED] {gate-name} — {reason}. Action: {what happens next}.`

Examples:
- `[GATE FAILED] commit-gate-linkedin — git push failed (transient). Action: retrying (attempt 2/2).`
- `[GATE FAILED] session-state-gate — session-state.md missing 2026-03-02 entry. Action: re-dispatching gate-check.`
- `[GATE FAILED] commit-gate-indeed — merge conflict (unrecoverable). Action: stopping pipeline, alerting user.`

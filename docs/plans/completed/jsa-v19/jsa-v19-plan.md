# Plan: JSA V19 — Constraint Enforcement + Regression Hardening

## Overview

V19 applies 8 constraint fixes identified by V18 analysis, plus 4 regression tests to prevent regressions. All fixes are in the constraint enforcement domain (CLAUDE.md edits, one script hardening, regression assertions). Single phase because all fixes are independent and share the same debugging workflow.

**From Design Handoff Contract:**
- CLAUDE.md: 7 edits (foreground-fallback guard, context budget, dashboard link, fabricated UI constraint, API key instruction, settings merge instruction, session-state enforcement)
- scripts/manage_state.py: domain normalization fix in dedup collision key
- Test files: 5 regression test groups (dedup key, API key handling, settings merge, session-state per-batch, tech-actions directive)

## Files to Modify

- `03_agents/tests/v19/CLAUDE.md` — 7 constraint edits (create via copy from v18, then modify)
- `03_agents/tests/v19/scripts/manage_state.py` — Domain normalization fix in `_compute_dedup` (line 298)
- `03_agents/tests/v19/tests/test_claude_md.py` — 4 new regression test functions
- `03_agents/tests/v19/tests/test_manage_state_dedup.py` — 1 new test class with 3 test methods

## Implementation Steps

---

### Step 1: Copy v18 → v19

**Action:** Create v19 directory as a copy of v18.

```bash
cp -R 03_agents/tests/v18 03_agents/tests/v19
```

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest -v` (all existing tests pass in the new directory)

---

### Step 2: Write regression tests — dedup collision key

**File:** `03_agents/tests/v19/tests/test_manage_state_dedup.py`
**Action:** Append new test class at end of file

**Pre-check:** Before appending the test class, verify that the required helper functions exist in the copied V18 test file:
- `_write_verified_job` — must exist in `tests/test_manage_state_dedup.py`
- `_run_dedup` — must exist in `tests/test_manage_state_dedup.py`

If either helper is missing, define it before appending the new test class. Do NOT proceed without verifying helpers exist.

```python
class TestDedupCollisionKeyDomainCompanyTitle:
    """Regression: dedup key must be domain+company+title, not title-only or company+title-only."""

    def test_same_title_different_companies_not_deduped(self) -> None:
        """Two jobs with the same title but different companies must NOT be merged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "acme-engineer.json", {
                "company": "Acme", "title": "Engineer", "score": 85,
                "source_url": "https://example.com/acme-engineer",
            })
            _write_verified_job(Path(tmpdir), "crypto", "beta-engineer.json", {
                "company": "Beta Corp", "title": "Engineer", "score": 88,
                "source_url": "https://example.com/beta-engineer",
            })
            result = _run_dedup(tmpdir)
            assert result["total_output"] == 2, (
                "Jobs with the same title but different companies must not be deduped. "
                "Dedup key must include company, not just title."
            )
            assert len(result["removed"]) == 0

    def test_same_company_and_title_different_domains_not_deduped(self) -> None:
        """Same company+title on different source domains must NOT be merged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "acme-engineer-linkedin.json", {
                "company": "Acme", "title": "Engineer", "score": 85,
                "source_url": "https://linkedin.com/jobs/view/111111",
            })
            _write_verified_job(Path(tmpdir), "crypto", "acme-engineer-indeed.json", {
                "company": "Acme", "title": "Engineer", "score": 85,
                "source_url": "https://indeed.com/jobs/view/222222",
            })
            result = _run_dedup(tmpdir)
            assert result["total_output"] == 2, (
                "Same company+title posted on different domains must not be deduped. "
                "Dedup key must include source domain."
            )
            assert len(result["removed"]) == 0

    def test_same_domain_company_title_is_deduped(self) -> None:
        """Same domain+company+title IS a true duplicate and should be merged, keeping highest score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_verified_job(Path(tmpdir), "ai-ml", "acme-engineer-v1.json", {
                "company": "Acme", "title": "Engineer", "score": 80,
                "source_url": "https://example.com/acme-engineer",
            })
            _write_verified_job(Path(tmpdir), "crypto", "acme-engineer-v2.json", {
                "company": "Acme", "title": "Engineer", "score": 90,
                "source_url": "https://example.com/acme-engineer",
            })
            result = _run_dedup(tmpdir)
            assert result["total_output"] == 1, (
                "Same domain+company+title must be treated as a single job."
            )
            assert result["kept"][0]["score"] == 90, "Higher score must win."
            assert len(result["removed"]) == 1
```

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest tests/test_manage_state_dedup.py::TestDedupCollisionKeyDomainCompanyTitle -v` (should FAIL — domain normalization not yet applied, but structure assertions should pass for existing correct key format; the test itself validates key behavior, not normalization — these should PASS with current key)

---

### Step 3: Write regression tests — CLAUDE.md constraints

**File:** `03_agents/tests/v19/tests/test_claude_md.py`
**Action:** Append 4 new test functions at end of file

**Pre-check:** Before appending the test functions, verify that the required helper functions exist in the copied V18 test file:
- `_read_claude_md` — must exist in `tests/test_claude_md.py`
- `_extract_section` — must exist in `tests/test_claude_md.py`

If either helper is missing, define it before appending the new test functions. Do NOT proceed without verifying helpers exist.

```python
def test_api_key_piping_uses_stdin_not_inline() -> None:
    """Step 23 must pipe API keys via stdin; no inline echo of key value in CLI args."""
    content = _read_claude_md()

    # Locate Step 23 section
    step23_start = content.find("**Step 23:")
    assert step23_start != -1, "Step 23 not found in CLAUDE.md"
    next_heading = content.find("\n---", step23_start + 1)
    step23 = content[step23_start:next_heading] if next_heading != -1 else content[step23_start:]

    lower = step23.lower()
    assert "stdin" in lower or "pipe" in lower, (
        "Step 23 must instruct piping keys via stdin — found neither 'stdin' nor 'pipe'."
    )

    # Concept-based: verify the instruction teaches stdin/pipe approach
    # and warns against inline key usage
    assert "never" in lower or "do not" in lower or "wrong" in lower, (
        "Step 23 must explicitly warn against inline key usage."
    )


def test_settings_local_json_instructions_use_merge_language() -> None:
    """Any settings.local.json instruction must use merge/preserve language, not blind overwrite."""
    content = _read_claude_md()

    idx = content.find("settings.local.json")
    if idx == -1:
        return

    snippet_start = max(0, idx - 100)
    snippet_end = min(len(content), idx + 700)
    snippet = content[snippet_start:snippet_end].lower()

    assert "merge" in snippet or "preserve" in snippet or "read existing" in snippet, (
        "settings.local.json instructions must use 'merge', 'preserve', or 'read existing' language "
        "to prevent overwriting user config."
    )

    import re
    blind_overwrite = re.search(r'\bwrite\b.*settings\.local\.json', snippet)
    if blind_overwrite:
        assert "merge" in snippet or "preserve" in snippet, (
            "settings.local.json instructions mention 'write' without 'merge' or 'preserve' — "
            "this risks silently overwriting existing user settings."
        )


def test_session_state_written_per_batch_not_only_at_end() -> None:
    """CLAUDE.md must require session-state.md to be written after each batch, not just end of session."""
    content = _read_claude_md()

    core_rules_section = _extract_section(content, "## CORE RULES")
    step11_start = content.find("**Step 11:")
    assert step11_start != -1, "Step 11 not found in CLAUDE.md"
    step12_start = content.find("**Step 12:", step11_start + 1)
    step11 = content[step11_start:step12_start] if step12_start != -1 else content[step11_start:]

    combined = (core_rules_section + " " + step11).lower()

    has_per_batch = "per-batch" in combined or "each batch" in combined or "every batch" in combined
    has_checkpoint = "checkpoint" in combined
    has_not_defer = "not defer" in combined or "do not defer" in combined

    assert has_per_batch or (has_checkpoint and has_not_defer), (
        "CLAUDE.md must explicitly require session-state.md to be written after each search batch "
        "(not deferred to end of session). "
        "Expected 'each batch', 'per-batch', or 'checkpoint' + 'not defer' language."
    )


def test_never_directs_user_to_perform_technical_actions() -> None:
    """CLAUDE.md must not direct users to run commands or perform technical setup steps."""
    content = _read_claude_md()
    lower = content.lower()

    # Check for phrases that direct the user to perform technical actions
    directive_phrases = [
        "please run",
        "you need to run",
        "execute the following",
        "run this command",
        "you should run",
    ]
    for phrase in directive_phrases:
        assert phrase not in lower, (
            f"CLAUDE.md contains '{phrase}' which directs the user to perform technical actions. "
            "The agent must perform all technical operations itself, never instruct the user."
        )
```

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest tests/test_claude_md.py::test_api_key_piping_uses_stdin_not_inline tests/test_claude_md.py::test_settings_local_json_instructions_use_merge_language tests/test_claude_md.py::test_session_state_written_per_batch_not_only_at_end tests/test_claude_md.py::test_never_directs_user_to_perform_technical_actions -v`
- Expected: 4 test functions added (test_api_key_piping_uses_stdin_not_inline, test_settings_local_json_instructions_use_merge_language, test_session_state_written_per_batch_not_only_at_end, test_never_directs_user_to_perform_technical_actions)

---

### Step 4: Apply CLAUDE.md Edit 1 — Foreground-fallback guard

**File:** `03_agents/tests/v19/CLAUDE.md`
**Action:** Insert step 2b after existing step 2 in `## ON STARTUP` section

**Old text (unique match):**
```
3. **Git pull (interactive mode only — MANDATORY):** If `$SCHEDULED_RUN` is NOT set, execute `git pull` and verify it succeeds BEFORE any file reads.
```

**New text:**
```
2b. **Foreground-fallback guard:** On the first real subagent dispatch of the session (typically the source-discovery or search subagent), observe the result:

   - If the Task tool call is **denied or errors**: set in-context variable `dispatch_mode = "foreground"`. All subsequent Task tool calls in this session MUST be dispatched in foreground (blocking, not background). Log: "Subagent dispatch denied — switching to dispatch_mode=foreground for this session."
   - If the Task tool call **succeeds**: proceed normally with background dispatch (`dispatch_mode = "background"`).
   - `dispatch_mode` only controls whether subagents run blocking vs background. It does NOT allow the parent to execute subagent-only operations directly. Even in foreground mode, the parent delegates all work to subagents.

3. **Git pull (interactive mode only — MANDATORY):** If `$SCHEDULED_RUN` is NOT set, execute `git pull` and verify it succeeds BEFORE any file reads.
```

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest tests/test_claude_md.py -v` (existing tests still pass)

---

### Step 5: Apply CLAUDE.md Edit 2 — Context budget section

**File:** `03_agents/tests/v19/CLAUDE.md`
**Action:** Insert new `## CONTEXT BUDGET` section between `## HARD CONSTRAINTS` and `## CORE RULES`

**Old text (unique match):**
```
---

## CORE RULES

These rules are mandatory. Violating any rule invalidates the session output.
```

**New text:**
```
---

## CONTEXT BUDGET

These rules define what the parent orchestrator may and may not execute directly. Violations bloat the parent context and reduce orchestration capacity.

**Parent-allowed operations:**
- Task tool dispatch (subagent invocation)
- Read — status files only (`_status.json`, `_summary.md`, `session-state.md`, `output/_delta.json`, `output/_subagent_test.txt`)
- Bash — git commands only (`git pull`, `git add`, `git commit`, `git push`)
- AskUserQuestion
- TaskCreate / TaskUpdate / TaskList

**Subagent-only operations (NEVER run in parent context):**
- WebFetch
- WebSearch
- `python3 scripts/*` (any script execution)
- Read of source files, verified JSONs, context.md beyond what ON STARTUP permits, or any file not listed in Parent-allowed above
- Filter logic, dedup logic, summarize logic
- Brief generation
- Email composition
- Any operation involving `output/jobs/`, `output/verified/`, or `output/briefs/` file contents

**Foreground mode interaction:** When `dispatch_mode = "foreground"`, all subagent dispatches run in foreground (blocking). The subagent-only restriction still applies — the parent never executes these operations directly, even in foreground mode.

**No escape hatch.** If a subagent dispatch fails, the parent MUST NOT execute the operation directly. Log the failure, report to user, and either retry the subagent dispatch or abort the operation. The parent never runs subagent-only operations regardless of failure count.

---

## CORE RULES

These rules are mandatory. Violating any rule invalidates the session output.
```

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest tests/test_claude_md.py -v` (existing tests still pass)

---

### Step 6: Apply CLAUDE.md Edit 3 — Dashboard link in presentation workflow

**File:** `03_agents/tests/v19/CLAUDE.md`
**Action:** Insert dashboard URL output step before the unified selection pattern instruction

**Old text (unique match):**
```
Apply this unified numbered list pattern to ALL user-facing selections: sources, jobs, role types. Present grouped tables for context, then a unified numbered list for selection.
```

**New text:**
```
After displaying the unified ranked list, output on a separate line:

> View and manage all jobs at: {dashboard_url}

Where `{dashboard_url}` is read from `context.md` `## Delivery` section (same value passed to `digest-email` subagent in Step 19). If no dashboard URL is stored in context.md, omit this line silently — do not fabricate a URL.

Apply this unified numbered list pattern to ALL user-facing selections: sources, jobs, role types. Present grouped tables for context, then a unified numbered list for selection.
```

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest tests/test_claude_md.py -v` (existing tests still pass)

---

### Step 7: Apply CLAUDE.md Edit 4 — Fabricated UI constraint

**File:** `03_agents/tests/v19/CLAUDE.md`
**Action:** Add item 6 to `## HARD CONSTRAINTS` section after existing item 5

**Old text (unique match):**
```
5. **Never write inline Python for state mutations.** All state changes must go through `scripts/manage_state.py` CLI subcommands. No `python3 -c` calls that import manage_state internals.

---

## CORE RULES
```

**New text:**
```
5. **Never write inline Python for state mutations.** All state changes must go through `scripts/manage_state.py` CLI subcommands. No `python3 -c` calls that import manage_state internals.
6. **Never give instructions about Claude Code UI features** (buttons, menus, settings panels, keyboard shortcuts, sidebar options) unless 100% certain the feature exists. If unsure, respond: "I'm not sure about that UI element — please check Claude Code documentation at docs.anthropic.com/claude-code."

---

## CORE RULES
```

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest tests/test_claude_md.py -v` (existing tests still pass)

---

### Step 8: Apply CLAUDE.md Edit 5 — API key handling (stdin piping only)

**File:** `03_agents/tests/v19/CLAUDE.md`
**Action:** Replace the `## SECURITY` section to add stdin-piping requirement

**Old text (unique match):**
```
## SECURITY

- **API key onboarding:** On first run, .env will NOT contain RESEND_API_KEY. When email is needed, check if set. If not, ask user: "I need a Resend API key to send your digest. Get one at resend.com/api-keys — click 'Create API Key', name it anything, and paste the key here." Write to .env silently. For Anthropic API key: "Get one at console.anthropic.com/settings/keys." Always include the source URL in the same message as the request.
- Never expose API keys in conversation.
- Store API keys in `.env` file, never inline in commands.
- Run email script with: `python3 scripts/send_email.py` (script auto-loads .env via Python dotenv)
```

**New text:**
```
## SECURITY

- **API key onboarding:** On first run, .env will NOT contain RESEND_API_KEY. When email is needed, check if set. If not, ask user: "I need a Resend API key to send your digest. Get one at resend.com/api-keys — click 'Create API Key', name it anything, and paste the key here." Write to .env silently. For Anthropic API key: "Get one at console.anthropic.com/settings/keys." Always include the source URL in the same message as the request.
- Never expose API keys in conversation.
- Store API keys in `.env` file, never inline in commands.
- **API keys in Bash: stdin piping ONLY.** Never echo, log, or embed API keys in Bash command strings or as positional arguments. Always pipe keys via stdin or pass via environment variables:
  ```bash
  # Correct — pipe via stdin
  echo "$RESEND_API_KEY" | gh secret set RESEND_API_KEY
  # Correct — env var
  RESEND_API_KEY="$RESEND_API_KEY" python3 scripts/send_email.py
  # WRONG — key in command string (exposes in process list and shell history)
  gh secret set RESEND_API_KEY --body "re_abc123..."
  ```
  This applies to all API keys: RESEND_API_KEY, ANTHROPIC_API_KEY, UPSTASH_REDIS_REST_TOKEN, and any future keys.
- Run email script with: `python3 scripts/send_email.py` (script auto-loads .env via Python dotenv)
```

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest tests/test_claude_md.py::test_api_key_piping_uses_stdin_not_inline -v` (should now PASS — stdin/pipe language present)

---

### Step 9: Apply CLAUDE.md Edit 6 — Settings.local.json merge protocol

**File:** `03_agents/tests/v19/CLAUDE.md`
**Action:** Append settings merge protocol after the non-overlap constraint in `## SCHEDULED RUNS`

**Old text (unique match):**
```
**Non-overlap constraint:** Interactive runs do not commit state, so no conflict with scheduled runs. If a scheduled run fires during an interactive session, the scheduled run's state is authoritative (committed to main); the interactive session's state.json becomes stale on next `git pull`.
```

**New text:**
```
**Non-overlap constraint:** Interactive runs do not commit state, so no conflict with scheduled runs. If a scheduled run fires during an interactive session, the scheduled run's state is authoritative (committed to main); the interactive session's state.json becomes stale on next `git pull`.

**settings.local.json write protocol:** When writing to `.claude/settings.local.json` (e.g., to persist scheduled run config, allowed tools, or environment entries):
1. Read existing `.claude/settings.local.json` if it exists → parse as JSON.
2. Merge new entries into the parsed object, preserving all existing keys (do NOT overwrite keys already present unless their values must change).
3. Write the merged object back to `.claude/settings.local.json`.
4. If the file does not exist, create it with only the required new entries — do not populate defaults for keys you don't need.

Never write `.claude/settings.local.json` from scratch if the file already exists. A destructive write would silently erase previously configured keys (e.g., allowed tools from a prior session).
```

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest tests/test_claude_md.py::test_settings_local_json_instructions_use_merge_language -v` (should PASS — merge language now present)

---

### Step 10: Apply CLAUDE.md Edit 7 — Session-state per-batch checkpoint fields

**File:** `03_agents/tests/v19/CLAUDE.md`
**Action:** Append per-batch checkpoint field requirements after Step 11 instruction

**Old text (unique match):**
```
**Step 11: After each batch:** Read each subagent's `_status.json`. Collect role types with "complete" or "partial" status into `searched_role_types` list. **MANDATORY: Write `output/session-state.md` after every search batch completes.** Do not defer checkpointing to the end of all batches.
```

**New text:**
```
**Step 11: After each batch:** Read each subagent's `_status.json`. Collect role types with "complete" or "partial" status into `searched_role_types` list. **MANDATORY: Write `output/session-state.md` after every search batch completes.** Do not defer checkpointing to the end of all batches.

Each per-batch checkpoint MUST include at minimum:
- Batch number (e.g., "Batch 2 of 4")
- Role types searched in this batch
- Jobs processed in this batch
- Cumulative jobs processed across all batches so far
- Status per role type

Append each checkpoint to `output/session-state.md` — do not overwrite earlier checkpoints. The final Step 21 summary is a separate section written at end of session and does not replace the per-batch blocks.

The agent may format the checkpoint naturally (headings, bullet lists, tables — any readable format). Tests verify the presence of required data fields, not specific markdown formatting.
```

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest tests/test_claude_md.py::test_session_state_written_per_batch_not_only_at_end -v` (should PASS)

**Post-edit safety check:** After all CLAUDE.md edits are complete, verify the agent-memory startup read survived:
```bash
grep -c "agent-memory" 03_agents/tests/v19/CLAUDE.md  # expect >= 1
```
If the count is 0, a CLAUDE.md edit accidentally deleted the agent-memory section — rollback and investigate.

---

### Step 11: Apply manage_state.py fix — Domain normalization in dedup

**File:** `03_agents/tests/v19/scripts/manage_state.py`
**Action:** Modify line 298 in `_compute_dedup` function

**Old text (unique match in `_compute_dedup`):**
```python
domain = urlparse(source_url).netloc if source_url else "unknown"
```

**New text:**
```python
raw_domain = urlparse(source_url).netloc.lower().strip() if source_url else "unknown"
domain = raw_domain.removeprefix("www.")
```

Additionally, ensure title and company fields are normalized with `.lower().strip()` in the dedup key computation. If the existing code already normalizes these, verify it; if not, add normalization.

**Verify:**
- Test: `cd 03_agents/tests/v19 && pytest tests/test_manage_state_dedup.py -v` (all dedup tests pass, including new collision key tests)

---

### Step 12: Run full test suite — verify all pass

**Action:** Run the complete test suite to confirm zero regressions.

```bash
cd 03_agents/tests/v19 && pytest -v
```

**Verify:**
- Test: All tests pass (0 failures, 0 errors)
- Expected new tests: 7 new test functions (3 in test_manage_state_dedup.py, 4 in test_claude_md.py)

---

### Step 13: Verify git diff — only constraint additions and test assertions

**Action:** Confirm no behavioral code changes beyond what's planned.

```bash
cd /Users/ryanhennebry/Projects/autonomous1 && git diff --stat
```

**Verify:**
- Only `03_agents/tests/v19/` files appear in diff (new directory)
- No files outside `03_agents/tests/v19/` were modified
- Changes are constraint text (CLAUDE.md), one normalization fix (manage_state.py line 298), and test assertions

---

### Step 14: Commit

```bash
cd /Users/ryanhennebry/Projects/autonomous1
git add 03_agents/tests/v19/
git commit -m "feat(jsa): V19 — 8 constraint fixes + 7 regression tests from V18 analysis

- Foreground-fallback guard in startup sequence
- Context budget section (parent vs subagent operations)
- Dashboard link in presentation workflow
- Fabricated UI constraint in hard constraints
- API key stdin-piping-only rule with examples
- settings.local.json merge protocol (no blind overwrites)
- Session-state per-batch checkpoint field requirements
- Domain normalization fix in dedup collision key
- 7 new regression tests across test_claude_md.py and test_manage_state_dedup.py

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Verify:**
- `git status` shows clean working tree after commit

---

## Deployment Verification

### Pre-Deploy Checks

```bash
# Run full test suite from agent directory
cd /Users/ryanhennebry/Projects/autonomous1/03_agents/tests/v19
pytest -v

# Verify new regression tests exist and pass individually
pytest tests/test_claude_md.py::test_api_key_piping_uses_stdin_not_inline -v
pytest tests/test_claude_md.py::test_settings_local_json_instructions_use_merge_language -v
pytest tests/test_claude_md.py::test_session_state_written_per_batch_not_only_at_end -v
pytest tests/test_claude_md.py::test_never_directs_user_to_perform_technical_actions -v
pytest tests/test_manage_state_dedup.py::TestDedupCollisionKeyDomainCompanyTitle -v

# Confirm CLAUDE.md constraint sections exist
grep -c "CONTEXT BUDGET" 03_agents/tests/v19/CLAUDE.md  # expect: 1
grep -c "foreground-fallback" 03_agents/tests/v19/CLAUDE.md  # expect: >= 1
grep -c "settings.local.json write protocol" 03_agents/tests/v19/CLAUDE.md  # expect: 1
grep -c "per-batch checkpoint" 03_agents/tests/v19/CLAUDE.md  # expect: >= 1

# Verify no GitHub Actions workflow references settings.local.json as if committed
grep -r "settings.local.json" .github/workflows/ && echo "WARNING: workflow references settings.local.json" || echo "OK: no workflow references settings.local.json"
```

### Post-Deploy Checks

No deployment — this is a local agent. Verification is:

1. Run a quick interactive session: `cd 03_agents/tests/v19 && claude`
2. Confirm the foreground-fallback guard fires during startup (test subagent dispatch)
3. Confirm the context budget section is readable in CLAUDE.md
4. Confirm `scripts/manage_state.py dedup --help` runs without error

### Rollback Plan

```bash
# V19 is a new directory — rollback is simply removing it
cd /Users/ryanhennebry/Projects/autonomous1
git revert HEAD --no-edit
# Or if uncommitted:
rm -rf 03_agents/tests/v19
```

## Handoff Contract

- Total steps: 14, Total phases: 1
- Files created: `03_agents/tests/v19/` (entire directory, copied from v18)
- Files modified (within v19):
  - `CLAUDE.md` — 7 constraint edits
  - `scripts/manage_state.py` — 1 line fix (domain normalization)
  - `tests/test_claude_md.py` — 4 new test functions appended
  - `tests/test_manage_state_dedup.py` — 1 new test class (3 methods) appended
- Verification sequence:
  1. `pytest -v` (full suite after copy)
  2. Individual test runs after each edit
  3. `pytest -v` (full suite final)
  4. `git diff --stat` (scope check)
- Deployment verification: pre-deploy (pytest + grep checks), post-deploy (interactive session), rollback (git revert)

<!-- STAGE COMPLETE: /plan, 2026-02-17 -->
<!-- STAGE COMPLETE: /revise after round 1, 2026-02-17 -->

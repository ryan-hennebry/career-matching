# Plan: JSA V17 — Incremental Fixes + Vercel Dashboard

## Overview

V17 applies 9 V16 fixes to a copied codebase and adds a Vercel-hosted dashboard (Python serverless + vanilla SPA) that reads Git-committed output files and stores user actions in Upstash Redis. GitHub Actions provides "Run Now" search capability.

From the design Handoff Contract:
- CLI Agent (9 fixes applied to copied V16 code)
- Dashboard (8 serverless functions + vanilla SPA)
- Design System (extended with dashboard tokens)
- GitHub Actions (JobSpy workflow dispatch)
- Email (full digest + dashboard links)

> **Architectural note — split-brain data model:** The dashboard has a split-brain data model: job data comes from Git-committed files (updated on deploy), user actions come from Upstash Redis (updated in real-time). There is no automatic reconciliation. If Redis is cleared, all user actions are lost. If Git files are updated without redeployment, the dashboard shows stale job data.

## Files to Modify

**Copied from V16 (then modified):**
- `03_agents/tests/v17/CLAUDE.md`
- `03_agents/tests/v17/references/algorithms.md`
- `03_agents/tests/v17/scripts/preview.sh`
- `03_agents/tests/v17/.claude/skills/jsa-design-system.md`
- `03_agents/tests/v17/.claude/skills/jsa-onboarding.md`
- `03_agents/tests/v17/.claude/skills/jsa-search-verify.md`
- `03_agents/tests/v17/.claude/skills/jsa-digest-email.md`
- `03_agents/tests/v17/.claude/agents/*.md` (all 6 agents — path updates)

**New files:**
- `03_agents/tests/v17/vercel.json`
- `03_agents/tests/v17/requirements.txt`
- `03_agents/tests/v17/.github/workflows/jsa-search.yml`
- `03_agents/tests/v17/api/state.py`
- `03_agents/tests/v17/api/jobs.py`
- `03_agents/tests/v17/api/job.py`
- `03_agents/tests/v17/api/action.py`
- `03_agents/tests/v17/api/brief.py`
- `03_agents/tests/v17/api/pipeline.py`
- `03_agents/tests/v17/api/context.py`
- `03_agents/tests/v17/api/run.py`
- `03_agents/tests/v17/public/index.html`
- `03_agents/tests/v17/public/css/dashboard.css`
- `03_agents/tests/v17/public/js/api.js`
- `03_agents/tests/v17/public/js/components.js`
- `03_agents/tests/v17/public/js/app.js`
- `03_agents/tests/v17/tests/test_salary_penalty.py`

> **Note:** API endpoint tests (`test_api_state.py`, `test_api_jobs.py`, `test_api_action.py`) will be added post-deployment after Vercel runtime behavior is confirmed. Vercel's serverless function environment differs from local Python — tests must target the actual runtime.

---

## Implementation Steps

### Phase 1: Foundation — Copy V16, Apply 9 Fixes

---

#### Step 1: Copy V16 to V17

**Action:** Create `03_agents/tests/v17/` as a copy of `03_agents/tests/v16/`, excluding `output/`, `state.json`, `.pytest_cache/`, `__pycache__/`, and `.claude/agent-memory/`.

```bash
mkdir -p 03_agents/tests/v17
# Copy all source files, excluding generated output
rsync -av --exclude='output/' --exclude='state.json' --exclude='.pytest_cache/' --exclude='__pycache__/' --exclude='.claude/agent-memory/' 03_agents/tests/v16/ 03_agents/tests/v17/
# Create empty output dirs
mkdir -p 03_agents/tests/v17/output/{jobs,verified,briefs,digests}
# Create empty state
echo '{}' > 03_agents/tests/v17/state.json
```

**Verify:**
```bash
ls 03_agents/tests/v17/CLAUDE.md  # exists
ls 03_agents/tests/v17/scripts/manage_state.py  # exists
ls 03_agents/tests/v17/.claude/agents/  # 6 agent files
```

---

#### Step 2: Update all path references from v16 to v17

**File:** All agent `.md` files in `03_agents/tests/v17/.claude/agents/`
**Action:** Modify — in each of the 6 agent files (`search-verify.md`, `onboarding.md`, `brief-generator.md`, `digest-email.md`, `briefs-html.md`, `source-researcher.md`), change:

- `03_agents/tests/v16/` → `03_agents/tests/v17/`

Files affected and the specific lines:

`03_agents/tests/v17/.claude/agents/search-verify.md` line 18:
```
**Working directory:** All paths are relative to `03_agents/tests/v17/`.
```
Line 19:
```
**First action:** `cd 03_agents/tests/v17/`
```

`03_agents/tests/v17/.claude/agents/onboarding.md` line 26-28:
```
**Working directory:** All paths are relative to `03_agents/tests/v17/`.

**First action:** `cd 03_agents/tests/v17/`
```

`03_agents/tests/v17/.claude/agents/brief-generator.md` line 18-19:
```
**Working directory:** All paths are relative to `03_agents/tests/v17/`.

**First action:** `cd 03_agents/tests/v17/`
```

`03_agents/tests/v17/.claude/agents/digest-email.md` line 22-23:
```
**Working directory:** All paths are relative to `03_agents/tests/v17/`.

**First action:** `cd 03_agents/tests/v17/`
```

`03_agents/tests/v17/.claude/agents/briefs-html.md` line 20-21:
```
**Working directory:** All paths are relative to `03_agents/tests/v17/`.

**First action:** `cd 03_agents/tests/v17/`
```

`03_agents/tests/v17/.claude/agents/source-researcher.md` line 20-21:
```
**Working directory:** All paths are relative to `03_agents/tests/v17/`.

**First action:** `cd 03_agents/tests/v17/`
```

Also update `03_agents/tests/v17/.claude/skills/jsa-search-verify.md` line 14:
```
**Working directory:** All paths in this template are relative to `03_agents/tests/v17/`.
```

Also update `03_agents/tests/v17/tests/conftest.py` line 1:
```python
"""Shared fixtures for JSA V17 tests."""
```

**Verify:**
```bash
grep -r "v16" 03_agents/tests/v17/.claude/agents/ 03_agents/tests/v17/.claude/skills/jsa-search-verify.md
# Should return empty (no v16 references remaining)
```

---

#### Step 3: Fix 1 — Unified Numbered Selection View (Architectural)

**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify — add unified selection instruction to PRESENTATION WORKFLOW section (after the "Still Active" subsection around line 432).

Insert after the existing formatting rules (after `- **No hyperlinks in table.** URLs are reference footnotes below, not markdown links.`):

```markdown

**Unified Selection View (MANDATORY before collecting user feedback):**

After presenting all per-role-type tables (New Today + Still Active), show a single ranked list across all role types for selection:

```
Here are all jobs ranked by score:

 #  | Score | Title                      | Company       | Type              |
----|-------|----------------------------|---------------|-------------------|
 1  | 95    | Associate PMM              | Triptease     | Marketing Assoc.  |
 2  | 92    | Founder Associate          | Duku AI       | Founder's Assoc.  |
 3  | 88    | DevRel Lead                | Acme Corp     | Community Manager |
 4  | 87    | Growth Lead                | MAGIC AI      | Marketing Manager |

Which jobs would you like briefs for? (e.g., "1, 3, 4")
```

Apply this unified numbered list pattern to ALL user-facing selections: sources, jobs, role types. Present grouped tables for context, then a unified numbered list for selection.
```

Also update Step 16 description (around line 257):

Replace:
```
**Step 16: Present results to user** — use PRESENTATION WORKFLOW (see below). Show "New Today" and "Still Active" subsections.
```

With:
```
**Step 16: Present results to user** — use PRESENTATION WORKFLOW (see below). Show "New Today" and "Still Active" subsections per role type, then the Unified Selection View (all jobs ranked by score in one numbered list).
```

**Verify:**
```bash
grep "Unified Selection View" 03_agents/tests/v17/CLAUDE.md
# Should match 2+ lines
```

---

#### Step 4: Fix 2 — Salary Validation Penalty (Architectural)

**File:** `03_agents/tests/v17/references/algorithms.md`
**Action:** Modify — add a new "Salary Validation" section after the "Location Match Scoring" table (after line 54).

Insert:

```markdown

### Salary Validation Penalty

After computing the base score (sum of 5 factors = /100), apply a salary penalty if applicable:

| Condition | Penalty |
|-----------|---------|
| Job salary_max < user salary_min | -10 points |
| Job salary_min < user salary_min AND salary_max >= user salary_min | No penalty (range overlaps) |
| No salary listed | No penalty |
| Currency mismatch (unable to compare) | No penalty |

**Rules:**
- Penalty applied AFTER base scoring (final score can go below 70 but job is still presented if base score was 70+)
- A penalized job can never outrank a salary-compliant job of equal base score
- Tag penalized jobs with "Below Salary Minimum" in presentation
- The penalty is visible in `score_breakdown` as a new `salary_penalty` field

**Verify:** `03_agents/tests/v17/.claude/skills/jsa-search-verify.md` Step 4 SCORE must reference salary penalty.

**File:** `03_agents/tests/v17/.claude/skills/jsa-search-verify.md`
**Action:** Modify — update Step 4: SCORE section (around line 101-112).

Replace the score table with:

```markdown
| Factor | Calculation | Points |
|--------|-------------|--------|
| Required skills | 40 × (matched / total required) | /40 |
| Preferred skills | 20 × (matched / total preferred) | /20 |
| Experience fit | See algorithms.md Experience Fit Scoring | /15 |
| Industry match | See algorithms.md Industry Match Scoring | /15 |
| Location | See algorithms.md Location Match Scoring | /10 |
| **BASE TOTAL** | | **/100** |
| Salary penalty | See algorithms.md Salary Validation Penalty | -10 or 0 |
| **FINAL SCORE** | | **BASE - penalty** |
```

Also update the verified JSON schema (Step 5, around line 138) to add `salary_penalty` to `score_breakdown`:

```json
"score_breakdown": {
    ...existing fields...,
    "salary_penalty": {
      "applied": false,
      "points": 0,
      "reason": "Salary range overlaps minimum"
    },
    "total": 85
}
```

**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify — add salary tagging to PRESENTATION WORKFLOW formatting rules (around line 407):

After the existing `* Triptease salary £25-35K, below your £40K minimum` footnote example, add:

```markdown
- **Salary penalty tag:** Jobs with salary_penalty applied display "⚠ Below Salary Minimum" after the company name in the table. These jobs appear at the bottom of their score tier (after all jobs of equal or higher unpunished score).
```

**Verify:**
```bash
grep -c "salary_penalty\|Salary Validation\|Below Salary Minimum" 03_agents/tests/v17/references/algorithms.md 03_agents/tests/v17/.claude/skills/jsa-search-verify.md 03_agents/tests/v17/CLAUDE.md
# Should show matches in all 3 files
```

---

#### Step 5: Fix 3 — Threshold Inclusivity

**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify — update the threshold line in PRESENTATION WORKFLOW (line 383).

Replace:
```
**Minimum score threshold: 70.** Only present jobs scoring 70+. Below 70 = not shown, logged in session-state.md.
```

With:
```
**Minimum score threshold: 70 (inclusive).** Only present jobs scoring >= 70. Score of exactly 70 IS shown. Below 70 = not shown, logged in session-state.md. Threshold comparison: `score >= 70`, not `score > 70`.
```

**Verify:**
```bash
grep "inclusive" 03_agents/tests/v17/CLAUDE.md
```

---

#### Step 6: Fix 4 — Auto-Retry via Subagent

**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify — update AUTO-RETRY PROTOCOL (around line 102-111).

Replace the section with:

```markdown
## AUTO-RETRY PROTOCOL

When a subagent fails (status file shows `"failed"` or no status file written):

1. **First failure:** Retry once as a subagent dispatch via Task tool — never inline in parent context. Same variables, same agent type. Subagent retry is a new Task tool call, not a manual retry in parent.
2. **Second failure:** Log the error, continue with remaining work. Do NOT retry again.
3. **Never retry more than once per subagent per run.**
4. **Never retry inline in parent.** All retries MUST go through Task tool named agent dispatch. Parent context must not grow from retry work.

This applies to all subagent types: source-researcher, search-verify, brief-generator, digest-email, briefs-html, onboarding.
```

**Verify:**
```bash
grep "never inline in parent" 03_agents/tests/v17/CLAUDE.md
```

---

#### Step 7: Fix 5 — Recovery Subagent for Partial Failures

**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify — add a new section after AUTO-RETRY PROTOCOL.

Insert:

```markdown

---

## RECOVERY PROTOCOL

When a subagent completes work (files exist in output directory) but fails to write `_status.json` or `_summary.md`:

1. **Do NOT read individual verified JSONs in parent context.** This bloats the context window.
2. **Dispatch a recovery subagent** via Task tool:
   - subagent_type: general-purpose
   - prompt: "Read all files in output/verified/{role_type_slug}/ (skip files starting with _). Count files. For each, extract title, company, score, location. Write _status.json with status='partial' and _summary.md with the standard table format. Working directory: 03_agents/tests/v17/"
3. After recovery subagent completes, read `_summary.md` (not individual JSONs).
4. If recovery subagent also fails, log the failure and continue with other role types.
```

**Verify:**
```bash
grep "RECOVERY PROTOCOL" 03_agents/tests/v17/CLAUDE.md
```

---

#### Step 8: Fix 6 — preview.sh Server Persistence

**File:** `03_agents/tests/v17/scripts/preview.sh`
**Action:** Rewrite — replace trap-based cleanup with nohup + PID file.

```bash
#!/bin/bash
# Preview an HTML file on localhost:8800
# Usage: scripts/preview.sh <filepath>
# Server persists after script exit. PID written to /tmp/jsa-preview.pid

set -e

if [ -z "$1" ]; then
  echo "Usage: scripts/preview.sh <filepath>"
  exit 1
fi

FILEPATH="$1"
if [ ! -f "$FILEPATH" ]; then
  echo "File not found: $FILEPATH"
  exit 1
fi

PARENT_DIR=$(dirname "$FILEPATH")
FILENAME=$(basename "$FILEPATH")
PORT=8800
PID_FILE="/tmp/jsa-preview.pid"

# Kill existing process on port
if [ -f "$PID_FILE" ]; then
  kill "$(cat "$PID_FILE")" 2>/dev/null || true
  rm -f "$PID_FILE"
fi
lsof -ti:$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true

# Start server in background with nohup — no trap cleanup
cd "$PARENT_DIR"
nohup python3 -m http.server $PORT --bind 127.0.0.1 &>/dev/null &
echo $! > "$PID_FILE"

# Health check
sleep 1
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/$FILENAME" | grep -q "200"; then
  echo "Preview: http://localhost:$PORT/$FILENAME"
  echo "Server PID: $(cat "$PID_FILE")"
  open "http://localhost:$PORT/$FILENAME"
else
  echo "Server failed to start"
  kill "$(cat "$PID_FILE")" 2>/dev/null || true
  rm -f "$PID_FILE"
  exit 1
fi
```

**Verify:**
```bash
grep -c "trap" 03_agents/tests/v17/scripts/preview.sh
# Should return 0 (no trap)
grep "nohup" 03_agents/tests/v17/scripts/preview.sh
# Should match
```

---

#### Step 9: Fix 7 — No Email Confirmation

**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify — update Step 20 (around line 308-331). After the "Pre-send gate:" section and before the bash command, add:

```markdown
**CRITICAL: Do NOT ask user for email send confirmation.** The pre-send gate checks (idempotency + briefs-html check) are the safety mechanism. Send immediately after all gate checks pass. No "are you happy for me to send?" or "let me know if you're happy" prompts.
```

**Verify:**
```bash
grep "Do NOT ask user for email send confirmation" 03_agents/tests/v17/CLAUDE.md
```

---

#### Step 10: Fix 8 — Session-State Per-Batch (Promote to Core Rule)

**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify — add a new core rule to the CORE RULES section (after line 31, as rule 10):

```markdown
10. **MUST write session-state.md after every search batch.** After each batch of search-verify subagents completes (Step 11), write `output/session-state.md` immediately. Do not defer to end of all batches. This is a checkpoint for resume capability.
```

**Verify:**
```bash
grep "MUST write session-state.md after every search batch" 03_agents/tests/v17/CLAUDE.md
```

---

#### Step 11: Fix 9 — Explicit Target Roles Question

**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify — update ONBOARDING step 5 (line 80).

Replace:
```
5. Ask: "What types of roles are you targeting?" → Store in `## Target`
```

With:
```
5. Ask: "What types of roles are you targeting?" even if roles were inferred from CV. Present inferred roles as a suggestion: "Based on your CV, I'd suggest: [inferred roles]. What types of roles are you targeting? Feel free to add, remove, or adjust." → Store confirmed list in `## Target`
```

**Verify:**
```bash
grep "even if roles were inferred" 03_agents/tests/v17/CLAUDE.md
```

---

#### Step 12: Fix Additional — Remove Duplicate Source Research from Onboarding

**File:** `03_agents/tests/v17/.claude/skills/jsa-onboarding.md`
**Action:** Modify — remove source discovery steps (Steps 3-4 become infer-only, Step 4: Source Discovery is removed entirely).

Replace the full content with:

```markdown
---
name: jsa-onboarding
description: Complete instructions for the onboarding subagent — CV parsing and profile extraction (no source discovery)
---

# Onboarding Skill

Parse a CV and extract structured profile data. Source discovery is handled separately by the source-researcher agent.

---

## Step 1: Read Inputs

1. Read the CV file from `cv_path`
2. If `existing_context_path` is not null, read the existing `context.md` for prior profile data
3. Note `target_industries` and `target_roles` — if null, infer from CV content

---

## Step 2: CV Parsing

Follow the CV Parsing rules from `references/algorithms.md`:

### Extraction Order
1. **Contact section:** name, email, phone, linkedin
2. **Summary:** Professional summary paragraph
3. **Experience:** List roles with company, title, dates, achievements, skills mentioned
4. **Education:** Degrees, certifications
5. **Skills section:** Explicitly listed skills

### Skill Extraction Patterns
- Comma-separated: "Python, JavaScript, SQL"
- Bullet points: "• Python • JavaScript"
- Parenthetical: "built APIs (Python, FastAPI)"
- Version numbers: Strip "Python 3.x" → "Python"

### Derived Fields

| Field | Derivation |
|-------|------------|
| `total_years` | Sum of experience durations (overlaps counted once) |
| `seniority` | From titles + years (see Experience Level Mapping in algorithms.md) |
| `industries` | From company types and role contexts |
| `skills` | Union of skills_section + skills mentioned in experience |

### Error Handling
If the CV is unreadable or missing critical sections, write `output/_onboarding_status.json` with `"status": "failed"` and a descriptive error message. Do not guess missing data.

---

## Step 3: Infer Target Industries and Roles (if null)

If `target_industries` is null:
- Derive from CV experience (company types, industry verticals)
- Include both direct matches and adjacent industries

If `target_roles` is null:
- Derive from CV job titles and progression
- Include both exact role types and logical next-step roles

---

## Step 4: Write Draft Output

Write `output/_onboarding_draft.json`:

```json
{
  "profile": {
    "contact": {
      "name": "...",
      "email": "...",
      "phone": "...",
      "linkedin": "..."
    },
    "summary": "Professional summary paragraph",
    "experience": [
      {
        "company": "...",
        "title": "...",
        "start_date": "YYYY-MM",
        "end_date": "YYYY-MM or present",
        "achievements": ["..."],
        "skills_used": ["..."]
      }
    ],
    "education": [
      {
        "institution": "...",
        "degree": "...",
        "year": "YYYY"
      }
    ],
    "skills": ["skill1", "skill2"],
    "total_years": 5,
    "seniority": "Mid",
    "industries": ["AI/ML", "SaaS"]
  },
  "inferred_roles": ["Founder's Associate", "Community Manager"],
  "inferred_industries": ["AI/ML", "Crypto"],
  "status": "complete"
}
```

Note: `discovered_sources` field is removed. Source discovery is handled by the source-researcher agent in a separate step.

---

## Step 5: Write Status File

Write `output/_onboarding_status.json`:
```json
{
  "status": "complete",
  "profile_fields_extracted": ["contact", "summary", "experience", "education", "skills"],
  "run_date": "{run_date}"
}
```

---

## Context.md Mapping (for parent reference)

The parent uses `_onboarding_draft.json` to write `context.md`. Field mapping:

| Draft Field | context.md Section |
|-------------|-------------------|
| `profile.contact` | `## Profile` |
| `profile.summary` | `## Profile` (subheading) |
| `profile.experience` | `## Experience` |
| `profile.education` | `## Education` |
| `profile.skills` | `## Skills` |
| `profile.total_years` | `## Experience` (derived) |
| `profile.seniority` | `## Experience` (derived) |
| `profile.industries` | `## Industries` |
| `inferred_roles` | Suggested to user during target roles question |

The parent adds additional sections after interactive Q&A: `## Target`, `## Constraints`, `## Delivery`, `## Skill Mappings`. Source discovery happens in a separate step via the source-researcher agent.
```

Also update `03_agents/tests/v17/.claude/agents/onboarding.md` — remove source discovery mention from description:

Replace line 3:
```
description: Parse CV, extract user profile data, and discover job sources for target industries
```
With:
```
description: Parse CV and extract user profile data (no source discovery — handled separately)
```

Replace line 13:
```
Your job is to parse a CV, extract structured profile data, and discover relevant job sources. You do NOT conduct the interactive Q&A — the parent handles that. Writes draft output to `output/_onboarding_draft.json` (structured profile data + discovered sources). The parent reads this draft, presents to user for correction, and writes the final `context.md`.
```
With:
```
Your job is to parse a CV and extract structured profile data. You do NOT conduct the interactive Q&A or discover job sources — the parent handles Q&A and source discovery is a separate step. Writes draft output to `output/_onboarding_draft.json` (structured profile data). The parent reads this draft, presents to user for correction, and writes the final `context.md`.
```

Replace the schema on line 17:
```
{"profile": {"contact": {...}, "summary": "...", "experience": [...], "education": [...], "skills": [...], "total_years": N, "seniority": "...", "industries": [...]}, "discovered_sources": [{"name": "...", "url": "...", "role_types": [...], "accessible": true}], "status": "complete"}
```
With:
```
{"profile": {"contact": {...}, "summary": "...", "experience": [...], "education": [...], "skills": [...], "total_years": N, "seniority": "...", "industries": [...]}, "inferred_roles": [...], "inferred_industries": [...], "status": "complete"}
```

Also update `03_agents/tests/v17/CLAUDE.md` ONBOARDING section — step 2 (line 69-75):

Replace:
```
2. **Dispatch onboarding subagent** for CV parse + source discovery:

   Task tool call:
     prompt: '{"cv_path": "path/to/cv.pdf", "existing_context_path": null, "run_date": "...", "target_industries": null, "target_roles": null}'
     description: "Parse CV and discover sources"
     subagent_type: "onboarding"

   Agent writes `output/_onboarding_draft.json` with structured profile data and discovered sources. Parent reads the draft and presents to user for correction.
```

With:
```
2. **Dispatch onboarding subagent** for CV parse + profile extraction:

   Task tool call:
     prompt: '{"cv_path": "path/to/cv.pdf", "existing_context_path": null, "run_date": "...", "target_industries": null, "target_roles": null}'
     description: "Parse CV and extract profile"
     subagent_type: "onboarding"

   Agent writes `output/_onboarding_draft.json` with structured profile data and inferred roles/industries. Parent reads the draft and presents to user for correction. Source discovery happens in Step 8 (separate).
```

Also update step 11 in ONBOARDING (line 86):

Replace:
```
11. Store any sources discovered during CV parsing as initial entries in `## Sources`. Full source research happens in the source research phase (Step 8) after onboarding.
```

With:
```
11. Do NOT discover sources during onboarding. Source discovery is exclusively handled by the source-researcher agent in Step 8 after onboarding completes.
```

**Verify (all 3 files must be consistent):**
```bash
# Onboarding skill: no discovered_sources reference
grep "discovered_sources" 03_agents/tests/v17/.claude/skills/jsa-onboarding.md
# Should return 0 matches

# Onboarding skill: source discovery only mentioned as "not done here"
grep "source discovery" 03_agents/tests/v17/.claude/skills/jsa-onboarding.md
# Should match only the "no source discovery" note

# Agent file: mentions sources are handled separately
grep "source discovery" 03_agents/tests/v17/.claude/agents/onboarding.md
# Should mention "handled separately"

# CLAUDE.md: onboarding references "Parse CV and extract profile" not "discover sources"
grep "Parse CV and extract profile" 03_agents/tests/v17/CLAUDE.md
# Should match
grep "Parse CV and discover sources" 03_agents/tests/v17/CLAUDE.md
# Should return 0 matches
```

---

#### Step 13: Commit Phase 1

```bash
cd 03_agents/tests/v17
git add -A 03_agents/tests/v17/
git commit -m "feat(jsa): create V17 foundation — copy V16 + apply 9 fixes

Applied: unified numbered selection, salary penalty, threshold inclusivity,
auto-retry subagent, recovery protocol, preview.sh persistence, no email
confirmation, session-state per-batch, explicit target roles, remove
duplicate source research from onboarding.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Verify:**
```bash
pytest 03_agents/tests/v17/tests/ -v
# Existing V16 tests should pass (they test manage_state.py which is unchanged)
```

---

### Phase 2: Design System Extension

---

#### Step 14: Extend Design System with Dashboard Tokens

**File:** `03_agents/tests/v17/.claude/skills/jsa-design-system.md`
**Action:** Modify — add dashboard extensions section after the existing "Aesthetic" section (line 475).

Append:

```markdown

---

### Dashboard Extensions

The following tokens extend the design system for interactive dashboard use. These are additive — all existing tokens remain unchanged.

**Interactive Tokens:**
```css
/* Buttons — ink on stone, not blue on white */
--btn-bg: #1c1917;
--btn-text: #ffffff;
--btn-bg-hover: #292524;
--btn-secondary-bg: transparent;
--btn-secondary-border: #d6d3d1;
--btn-secondary-hover-bg: #f8f8f6;
--btn-ghost-hover-bg: #f0efeb;

/* Focus ring — visible but not jarring */
--focus-ring: #78716c;
--focus-ring-offset: 2px;

/* Inputs */
--input-bg: #f8f8f6;
--input-border: #d6d3d1;
--input-border-focus: #1c1917;
```

**Elevation System:**
```css
--shadow-sm: none;
--shadow-dropdown: 0 4px 12px rgba(28,25,23,0.08);
--overlay-bg: rgba(28,25,23,0.3);
```

**Active/Selected States:**
```css
--sidebar-active-border: #1c1917;
--sidebar-active-bg: #f8f8f6;
--sidebar-hover-bg: #f0efeb;
--card-selected-border: #1c1917;
```

**Pipeline Status Tokens:**
```css
--status-new: #1c1917;
--status-new-bg: #f0efeb;
--status-reviewing: #57534e;
--status-brief: #15803d;
--status-brief-bg: #f0fdf4;
--status-applied: #15803d;
--status-applied-bg: #f0fdf4;
--status-rejected: #a8a29e;
--status-expired: #a8a29e;
```

**Spacing Scale:**
```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
```

**Transitions:**
```css
--transition-fast: 120ms ease;
--transition-base: 200ms ease;
```

**Button Patterns:**
```css
.btn {
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: var(--transition-fast);
  border: none;
}
.btn:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: var(--focus-ring-offset);
}
.btn-primary {
  background: var(--btn-bg);
  color: var(--btn-text);
}
.btn-primary:hover { background: var(--btn-bg-hover); }
.btn-secondary {
  background: var(--btn-secondary-bg);
  color: var(--text-primary);
  border: 1px solid var(--btn-secondary-border);
}
.btn-secondary:hover { background: var(--btn-secondary-hover-bg); }
.btn-ghost {
  background: transparent;
  color: var(--text-primary);
  border: none;
}
.btn-ghost:hover { background: var(--btn-ghost-hover-bg); }
```

**Sidebar Item Pattern:**
```css
.sidebar-item {
  padding: 8px 16px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: var(--text-secondary);
  border-left: 3px solid transparent;
  cursor: pointer;
  transition: var(--transition-fast);
}
.sidebar-item:hover { background: var(--sidebar-hover-bg); }
.sidebar-item.active {
  color: var(--text-primary);
  font-weight: 600;
  background: var(--sidebar-active-bg);
  border-left-color: var(--sidebar-active-border);
}
```

**Status Badge Pattern:**
```css
.status-badge {
  display: inline-block;
  font-family: 'DM Sans', sans-serif;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
```

**Hard Rule:** No blue anywhere. All interactive elements use warm stone/ink palette. Focus rings use `#78716c` (stone), not browser default blue.
```

**Verify:**
```bash
grep "Dashboard Extensions" 03_agents/tests/v17/.claude/skills/jsa-design-system.md
grep "btn-bg" 03_agents/tests/v17/.claude/skills/jsa-design-system.md
```

---

#### Step 15: Commit Phase 2

```bash
git add 03_agents/tests/v17/.claude/skills/jsa-design-system.md
git commit -m "feat(jsa): extend design system with dashboard interactive tokens

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Phase 3: Infrastructure

---

#### Step 16: Create vercel.json

**File:** `03_agents/tests/v17/vercel.json`
**Action:** Create

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/**/*.py",
      "use": "@vercel/python"
    },
    {
      "src": "public/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/$1" },
    { "src": "/(.*)", "dest": "/public/$1" }
  ],
  "functions": {
    "api/**/*.py": {
      "runtime": "@vercel/python",
      "maxDuration": 10
    }
  }
}
```

> Uses latest Vercel Python runtime. Pin to a specific version only if deployment breaks.

**Verify:**
```bash
python3 -c "import json; json.load(open('03_agents/tests/v17/vercel.json'))"
```

---

#### Step 17: Create requirements.txt

**File:** `03_agents/tests/v17/requirements.txt`
**Action:** Create

```
upstash-redis>=1.0.0
markdown>=3.5
```

**Verify:**
```bash
cat 03_agents/tests/v17/requirements.txt
```

---

#### Step 18: Create GitHub Actions Workflow

**File:** `03_agents/tests/v17/.github/workflows/jsa-search.yml`
**Action:** Create

```yaml
name: JSA Job Search (JobSpy)

on:
  workflow_dispatch:
    inputs:
      role_types:
        description: 'Comma-separated role types to search'
        required: true
        type: string
      location:
        description: 'Job search location'
        required: false
        default: 'London'
        type: string
      country:
        description: 'Country code for job search'
        required: false
        default: 'UK'
        type: string

concurrency:
  group: jsa-search
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  search:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        working-directory: 03_agents/tests/v17
        run: pip install python-jobspy

      - name: Run JobSpy search
        working-directory: 03_agents/tests/v17
        run: |
          IFS=',' read -ra ROLES <<< "${{ github.event.inputs.role_types }}"
          for role in "${ROLES[@]}"; do
            role_slug=$(echo "$role" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')
            echo "Searching: $role (slug: $role_slug)"
            python3 scripts/jobspy_search.py "$role" \
              --location "${{ github.event.inputs.location }}" \
              --country "${{ github.event.inputs.country }}" \
              --output "output/jobs/${role_slug}-aggregator.json" || echo "Warning: search failed for $role"
          done

      - name: Commit results
        working-directory: 03_agents/tests/v17
        run: |
          git config user.name "Job Search Agent"
          git config user.email "agent@autonomous.bot"
          git add output/jobs/
          git diff --staged --quiet || git commit -m "chore(jsa): JobSpy search results $(date +%Y-%m-%d)"
          git push origin main
```

> **Note:** This workflow commits and pushes directly to `main`. If the repository has branch protection rules requiring PR reviews, this workflow will fail. Either disable branch protection for the bot identity or modify the workflow to create a PR instead.

**Verify:**
```bash
python3 -c "import yaml; yaml.safe_load(open('03_agents/tests/v17/.github/workflows/jsa-search.yml'))" 2>/dev/null || echo "YAML check requires pyyaml"
```

---

#### Step 19: Commit Phase 3

```bash
git add 03_agents/tests/v17/vercel.json 03_agents/tests/v17/requirements.txt 03_agents/tests/v17/.github/workflows/jsa-search.yml
git commit -m "feat(jsa): add V17 infrastructure — Vercel config, requirements, GitHub Actions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Phase 4: Backend — Serverless Functions

---

#### Step 20: Create shared Upstash helper

**File:** `03_agents/tests/v17/api/_upstash.py`
**Action:** Create

```python
"""Shared Upstash Redis helper for all API functions."""

from __future__ import annotations

import os
from typing import Any


def get_redis():
    """Get Upstash Redis client. Returns None if credentials not set."""
    try:
        from upstash_redis import Redis
    except ImportError:
        return None

    url = os.environ.get("UPSTASH_REDIS_REST_URL")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

    if not url or not token:
        return None

    return Redis(url=url, token=token)


def get_user_actions(redis) -> dict[str, str]:
    """Get all user actions from Redis. Returns {job_key: action}.

    Uses keys() + mget() for 2 round-trips total (instead of N+1).
    Note: keys("action:*") is an O(N) scan of the Upstash keyspace.
    For the current scale (~100 jobs) this is fine. If the keyspace grows
    to 10K+ keys, migrate to a Redis hash (HGETALL jsa:actions) instead.
    """
    if redis is None:
        return {}

    try:
        keys = redis.keys("action:*")
        if not keys:
            return {}
        # Batch fetch all values in a single mget() call
        values = redis.mget(*keys)
        actions = {}
        for key, val in zip(keys, values):
            if val:
                job_key = key.replace("action:", "", 1)
                actions[job_key] = val
        return actions
    except Exception:
        return {}
```

---

#### Step 20b: Create shared response helper

**File:** `03_agents/tests/v17/api/_response.py`
**Action:** Create

```python
"""Shared response helpers for Vercel serverless functions.

Centralizes CORS headers and JSON response boilerplate used by all 8 endpoints.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler


def json_response(handler: BaseHTTPRequestHandler, data: dict, status: int = 200) -> None:
    """Send a JSON response with CORS headers."""
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode())


def cors_preflight(handler: BaseHTTPRequestHandler) -> None:
    """Handle CORS OPTIONS preflight request."""
    handler.send_response(200)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.end_headers()
```

> **Note for builder:** All subsequent API endpoint steps (22-29) should use `json_response()` and `cors_preflight()` from this helper instead of repeating the CORS boilerplate inline. The code in the plan shows inline patterns for clarity, but the builder should refactor to use the shared helper.

---

#### Step 21: Create shared file reader helper

**File:** `03_agents/tests/v17/api/_files.py`
**Action:** Create

```python
"""Shared file reading helpers for Vercel serverless functions.

Reads Git-committed output files bundled in the Vercel deployment.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _get_base_dir() -> Path:
    """Get the base directory for the V17 project.

    In Vercel, serverless functions run from the api/ directory.
    The project root is one level up.
    """
    return Path(__file__).resolve().parent.parent


def read_json(relative_path: str) -> Any | None:
    """Read a JSON file relative to the project root. Returns None if not found."""
    path = _get_base_dir() / relative_path
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_text(relative_path: str) -> str | None:
    """Read a text file relative to the project root. Returns None if not found."""
    path = _get_base_dir() / relative_path
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def list_verified_jobs() -> list[dict[str, Any]]:
    """Scan output/verified/ for all job JSON files. Returns list of dicts with 'key' added."""
    base = _get_base_dir() / "output" / "verified"
    if not base.exists():
        return []

    jobs = []
    for role_dir in sorted(base.iterdir()):
        if not role_dir.is_dir():
            continue
        role_type = role_dir.name
        for json_file in sorted(role_dir.glob("*.json")):
            if json_file.name.startswith("_"):
                continue
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                data["_key"] = f"{role_type}/{json_file.stem}"
                data["_role_type"] = role_type
                jobs.append(data)
            except (json.JSONDecodeError, OSError):
                continue

    return jobs


def read_state_json() -> dict[str, Any]:
    """Read state.json from project root."""
    return read_json("state.json") or {}


def read_delta_json() -> dict[str, Any]:
    """Read output/_delta.json."""
    return read_json("output/_delta.json") or {}
```

---

#### Step 22: Create api/state.py

**File:** `03_agents/tests/v17/api/state.py`
**Action:** Create

```python
"""GET /api/state — Summary counts for dashboard header."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from api._files import list_verified_jobs, read_delta_json, read_state_json
from api._upstash import get_redis, get_user_actions
from api.jobs import derive_stage


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        delta = read_delta_json()
        state = read_state_json()
        jobs = list_verified_jobs()

        redis = get_redis()
        actions = get_user_actions(redis)

        # Count by pipeline stage — uses derive_stage() for consistency with jobs.py
        counts = {
            "new": 0,
            "reviewing": 0,
            "brief_requested": 0,
            "applied": 0,
            "rejected": 0,
            "expired": 0,
            "total_jobs": len(jobs),
        }

        new_keys = set(delta.get("new_jobs", []))
        expired_keys = set(state.get("expired_jobs", {}).keys())
        last_run = state.get("last_run_date", "")

        for job in jobs:
            key = job.get("_key", "")
            action = actions.get(key)
            stage = derive_stage(key, action, new_keys, expired_keys)
            counts[stage] += 1

        result = {
            "run_date": last_run,
            "counts": counts,
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
```

---

#### Step 23: Create api/jobs.py

**File:** `03_agents/tests/v17/api/jobs.py`
**Action:** Create

```python
"""GET /api/jobs — Job list with scores and pipeline stages."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from api._files import list_verified_jobs, read_delta_json, read_state_json
from api._upstash import get_redis, get_user_actions


def derive_stage(key: str, action: str | None, new_keys: set, expired_keys: set) -> str:
    """Derive pipeline stage for a job.

    Priority: expired > rejected > applied > brief_requested > new > reviewing.
    If a job has both an expired status and a user action, expired wins
    (user can re-find via new search).
    """
    if key in expired_keys:
        return "expired"
    if action == "rejected":
        return "rejected"
    if action == "accepted":
        return "applied"
    if action == "brief_requested":
        return "brief_requested"
    if key in new_keys:
        return "new"
    return "reviewing"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        jobs = list_verified_jobs()
        delta = read_delta_json()
        state = read_state_json()

        redis = get_redis()
        actions = get_user_actions(redis)

        new_keys = set(delta.get("new_jobs", []))
        expired_keys = set(state.get("expired_jobs", {}).keys())

        result = []
        for job in jobs:
            key = job.get("_key", "")
            action = actions.get(key)
            stage = derive_stage(key, action, new_keys, expired_keys)

            result.append({
                "key": key,
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "score": job.get("score", 0),
                "source": job.get("source", ""),
                "job_url": job.get("job_url"),
                "role_type": job.get("_role_type", ""),
                "stage": stage,
                "user_action": action,
                "date_posted": job.get("date_posted"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "currency": job.get("currency"),
            })

        result.sort(key=lambda j: j["score"], reverse=True)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
```

---

#### Step 24: Create api/job.py

**File:** `03_agents/tests/v17/api/job.py`
**Action:** Create

```python
"""GET /api/job?key=... — Single job detail."""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._files import read_json
from api._upstash import get_redis

# Validates key format: role-type-slug/company-slug-title-slug (lowercase alphanumeric + hyphens only)
_KEY_PATTERN = re.compile(r"^[a-z0-9-]+/[a-z0-9-]+$")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        key = params.get("key", [None])[0]

        if not key:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "key parameter required"}).encode())
            return

        # Path traversal protection: validate key matches expected format
        if not _KEY_PATTERN.match(key):
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "invalid key format"}).encode())
            return

        # key format: role-type-slug/company-slug-title-slug
        job = read_json(f"output/verified/{key}.json")
        if not job:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "job not found"}).encode())
            return

        # Get user action from Upstash
        redis = get_redis()
        user_action = None
        if redis:
            try:
                user_action = redis.get(f"action:{key}")
            except Exception:
                pass

        job["_key"] = key
        job["user_action"] = user_action

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(job).encode())
```

---

#### Step 25: Create api/action.py

**File:** `03_agents/tests/v17/api/action.py`
**Action:** Create

```python
"""POST /api/action — Write user action to Upstash Redis."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from api._upstash import get_redis

VALID_ACTIONS = {"accepted", "rejected", "brief_requested"}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "invalid JSON"}).encode())
            return

        key = data.get("key")
        action = data.get("action")

        if not key or not action:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "key and action required"}).encode())
            return

        if action not in VALID_ACTIONS:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"invalid action: {action}"}).encode())
            return

        redis = get_redis()
        if not redis:
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Redis not configured"}).encode())
            return

        try:
            redis.set(f"action:{key}", action)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "key": key, "action": action}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
```

---

#### Step 26: Create api/brief.py

**File:** `03_agents/tests/v17/api/brief.py`
**Action:** Create

```python
"""GET /api/brief?key=... — Render individual brief as HTML.

Brief format lookup order:
1. Individual markdown file: output/briefs/{slug}-brief.md (rendered to HTML via markdown lib)
2. Consolidated HTML file: output/briefs/briefs-YYYY-MM-DD.html (returned as-is, contains all briefs)

The briefs-html subagent generates a consolidated HTML file. Individual markdown briefs
may also exist if the brief-generator subagent ran. The API tries individual first,
then falls back to consolidated."""

from __future__ import annotations

import json
import os
from datetime import date
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._files import read_text, _get_base_dir


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        key = params.get("key", [None])[0]

        if not key:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "key parameter required"}).encode())
            return

        # key format: role-type-slug/company-slug-title-slug
        # Brief filename: company-slug-title-slug-brief.md
        slug = key.split("/", 1)[-1] if "/" in key else key

        # Strategy 1: Individual markdown brief
        brief_md = read_text(f"output/briefs/{slug}-brief.md")
        if brief_md:
            try:
                import markdown
                html = markdown.markdown(brief_md, extensions=["tables", "fenced_code"])
            except ImportError:
                html = f"<pre>{brief_md}</pre>"

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"key": key, "html": html, "format": "individual_md"}).encode())
            return

        # Strategy 2: Consolidated HTML file (briefs-YYYY-MM-DD.html)
        briefs_dir = _get_base_dir() / "output" / "briefs"
        if briefs_dir.exists():
            # Find the most recent consolidated HTML file
            html_files = sorted(briefs_dir.glob("briefs-*.html"), reverse=True)
            if html_files:
                consolidated_html = html_files[0].read_text(encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"key": key, "html": consolidated_html, "format": "consolidated_html"}).encode())
                return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "brief not found"}).encode())
```

---

#### Step 27: Create api/pipeline.py

**File:** `03_agents/tests/v17/api/pipeline.py`
**Action:** Create

```python
"""GET /api/pipeline — Jobs grouped by pipeline stage."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from api._files import list_verified_jobs, read_delta_json, read_state_json
from api._upstash import get_redis, get_user_actions
from api.jobs import derive_stage


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        jobs = list_verified_jobs()
        delta = read_delta_json()
        state = read_state_json()

        redis = get_redis()
        actions = get_user_actions(redis)

        new_keys = set(delta.get("new_jobs", []))
        expired_keys = set(state.get("expired_jobs", {}).keys())

        pipeline = {}
        for job in jobs:
            key = job.get("_key", "")
            action = actions.get(key)
            stage = derive_stage(key, action, new_keys, expired_keys)

            if stage not in pipeline:
                pipeline[stage] = {"count": 0, "jobs": []}

            pipeline[stage]["count"] += 1
            pipeline[stage]["jobs"].append({
                "key": key,
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "score": job.get("score", 0),
                "location": job.get("location", ""),
            })

        # Sort jobs within each stage by score descending
        for stage_data in pipeline.values():
            stage_data["jobs"].sort(key=lambda j: j["score"], reverse=True)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(pipeline).encode())
```

---

#### Step 28: Create api/context.py

**File:** `03_agents/tests/v17/api/context.py`
**Action:** Create

```python
"""GET /api/context — Profile section names from context.md.

Returns section NAMES by default (no content, no raw text — protects PII).
Use ?sections=Profile,Target to return specific section content.
Never serves the full raw context.md text."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._files import read_text


def parse_context_sections(text: str) -> dict[str, str]:
    """Extract sections from context.md as {name: content}."""
    sections = {}
    current_section = None
    current_content = []

    for line in text.split("\n"):
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        text = read_text("context.md")

        if not text:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "context.md not found"}).encode())
            return

        all_sections = parse_context_sections(text)

        # Check if specific sections are requested
        params = parse_qs(urlparse(self.path).query)
        requested = params.get("sections", [None])[0]

        if requested:
            # Return content for requested sections only
            requested_names = [s.strip() for s in requested.split(",")]
            result = {
                "sections": {name: all_sections.get(name, "") for name in requested_names if name in all_sections},
                "available": list(all_sections.keys()),
            }
        else:
            # Default: return section names only (no content, no raw text)
            result = {
                "available": list(all_sections.keys()),
            }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
```

---

#### Step 29: Create api/run.py

**File:** `03_agents/tests/v17/api/run.py`
**Action:** Create

```python
"""POST /api/run — Trigger GitHub Actions search (authenticated).
GET /api/run — Poll workflow run status (public).

Security: POST requires Authorization: Bearer {JSA_RUN_SECRET} header.
GET is unauthenticated (read-only status polling)."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GITHUB_PAT = os.environ.get("GITHUB_PAT", "")
JSA_RUN_SECRET = os.environ.get("JSA_RUN_SECRET", "")
WORKFLOW_FILE = "jsa-search.yml"


class handler(BaseHTTPRequestHandler):
    def _check_auth(self) -> bool:
        """Verify Bearer token matches JSA_RUN_SECRET. Returns True if authorized."""
        if not JSA_RUN_SECRET:
            # No secret configured — reject all POST requests
            return False
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {JSA_RUN_SECRET}"

    def do_POST(self):
        if not self._check_auth():
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "unauthorized"}).encode())
            return

        if not all([GITHUB_OWNER, GITHUB_REPO, GITHUB_PAT]):
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "GitHub not configured"}).encode())
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length))
        role_types = body.get("role_types", [])

        if not role_types:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "role_types required"}).encode())
            return

        # Dispatch GitHub Actions workflow
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
        payload = json.dumps({
            "ref": "main",
            "inputs": {"role_types": ",".join(role_types)},
        }).encode()

        req = Request(url, data=payload, method="POST")
        req.add_header("Authorization", f"Bearer {GITHUB_PAT}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Content-Type", "application/json")

        try:
            resp = urlopen(req)
            if resp.status == 204:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "message": "Workflow dispatched"}).encode())
            else:
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        """GET /api/run/status — poll latest workflow run status."""
        if not all([GITHUB_OWNER, GITHUB_REPO, GITHUB_PAT]):
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "GitHub not configured"}).encode())
            return

        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/runs?per_page=1"
        req = Request(url)
        req.add_header("Authorization", f"Bearer {GITHUB_PAT}")
        req.add_header("Accept", "application/vnd.github+json")

        try:
            resp = urlopen(req)
            data = json.loads(resp.read())
            runs = data.get("workflow_runs", [])
            if runs:
                run = runs[0]
                result = {
                    "status": run.get("status"),
                    "conclusion": run.get("conclusion"),
                    "created_at": run.get("created_at"),
                    "updated_at": run.get("updated_at"),
                    "html_url": run.get("html_url"),
                }
            else:
                result = {"status": "none", "message": "No workflow runs found"}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
```

---

#### Step 30: Commit Phase 4

```bash
git add 03_agents/tests/v17/api/
git commit -m "feat(jsa): add V17 dashboard backend — 8 serverless API endpoints

Endpoints: state, jobs, job, action, brief, pipeline, context, run.
Shared helpers: _upstash.py (Redis client), _files.py (bundled file reader).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Phase 5: Frontend Shell + CSS

---

#### Step 31: Create public/css/dashboard.css

**File:** `03_agents/tests/v17/public/css/dashboard.css`
**Action:** Create

**Builder implements from spec.** The builder must implement this file using the design system skill tokens and the specifications below. The prose description serves as the implementation spec.

This file contains ALL CSS custom properties (existing design system + dashboard extensions) and the complete dashboard layout. It is the single canonical CSS file for the dashboard.

The full CSS should include:
- CSS custom properties block (`:root`) with all tokens from `jsa-design-system.md` including dashboard extensions
- Reset + base typography (DM Sans body, Newsreader headings)
- Layout grid: 240px sidebar + fluid main (max-width 800px, centered)
- Summary strip (persistent top bar)
- Sidebar styles (items, active state, counts)
- Job card styles
- Score badge styles (green/default/muted — same pattern as briefs)
- Button styles (primary/secondary/ghost)
- Data table styles
- Status badge styles
- Detail view styles
- Brief viewer styles
- Empty state styles
- Responsive: below 768px sidebar collapses to horizontal tab bar
- All transitions use `var(--transition-fast)` or `var(--transition-base)`
- No blue anywhere — focus rings use stone (`#78716c`)

The CSS custom properties in this file are the CANONICAL source at runtime. The skill file tokens are the design-time reference. If they diverge, dashboard.css wins. This file should be generated FROM the design system skill tokens, not manually duplicated.

**Verify:** Open `public/index.html` in browser — correct fonts load, warm stone palette visible, no blue.

---

#### Step 32: Create public/index.html

**File:** `03_agents/tests/v17/public/index.html`
**Action:** Create

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Job Search Agent</title>
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/dashboard.css">
</head>
<body>
  <!-- Summary Strip (persistent top bar) -->
  <header class="summary-strip" id="summary-strip">
    <div class="summary-strip-inner">
      <h1 class="summary-title">Job Search Agent</h1>
      <div class="summary-stats" id="summary-stats"></div>
      <button class="btn btn-primary" id="run-now-btn">Run Now</button>
    </div>
  </header>

  <div class="layout">
    <!-- Sidebar -->
    <nav class="sidebar" id="sidebar">
      <div class="sidebar-section">
        <div class="sidebar-item active" data-stage="all">All Jobs <span class="count" id="count-all"></span></div>
        <div class="sidebar-item" data-stage="new">New <span class="count" id="count-new"></span></div>
        <div class="sidebar-item" data-stage="reviewing">Reviewing <span class="count" id="count-reviewing"></span></div>
        <div class="sidebar-item" data-stage="brief_requested">Brief Requested <span class="count" id="count-brief"></span></div>
        <div class="sidebar-item" data-stage="applied">Applied <span class="count" id="count-applied"></span></div>
        <div class="sidebar-item" data-stage="rejected">Rejected <span class="count" id="count-rejected"></span></div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="content" id="content">
      <div class="loading">Loading...</div>
    </main>
  </div>

  <!-- Run Panel (hidden by default) -->
  <div class="overlay" id="run-overlay" style="display:none;">
    <div class="run-panel" id="run-panel">
      <h2>Run Job Search</h2>
      <p class="meta">Select role types to search via GitHub Actions (JobSpy only).</p>
      <div id="role-type-checkboxes"></div>
      <div class="run-panel-actions">
        <button class="btn btn-primary" id="run-confirm-btn">Search</button>
        <button class="btn btn-secondary" id="run-cancel-btn">Cancel</button>
      </div>
      <div id="run-status" style="display:none;"></div>
    </div>
  </div>

  <script src="/js/api.js"></script>
  <script src="/js/components.js"></script>
  <script src="/js/app.js"></script>
</body>
</html>
```

**Verify:**
```bash
ls 03_agents/tests/v17/public/index.html
```

---

#### Step 33: Commit Phase 5

```bash
git add 03_agents/tests/v17/public/index.html 03_agents/tests/v17/public/css/dashboard.css
git commit -m "feat(jsa): add V17 dashboard frontend shell — HTML + CSS design system

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Phase 6: Frontend Views + Interactivity

---

#### Step 34: Create public/js/api.js

**File:** `03_agents/tests/v17/public/js/api.js`
**Action:** Create

**Builder implements from spec.** The builder must implement this file using the design system skill tokens and the specifications below. The prose description serves as the implementation spec.

API client wrapping all backend endpoints:
- `API.getState()` → `GET /api/state`
- `API.getJobs()` → `GET /api/jobs`
- `API.getJob(key)` → `GET /api/job?key=...`
- `API.postAction(key, action)` → `POST /api/action`
- `API.getBrief(key)` → `GET /api/brief?key=...`
- `API.getPipeline()` → `GET /api/pipeline`
- `API.getContext()` → `GET /api/context`
- `API.triggerRun(roleTypes)` → `POST /api/run`
- `API.getRunStatus()` → `GET /api/run/status`

All methods return parsed JSON via `fetch()`. Error handling returns `{error: message}` on failure.

---

#### Step 35: Create public/js/components.js

**File:** `03_agents/tests/v17/public/js/components.js`
**Action:** Create

**Builder implements from spec.** The builder must implement this file using the design system skill tokens and the specifications below. The prose description serves as the implementation spec.

UI renderer functions:
- `Components.scoreBadge(score)` → `<span class="score-badge score-{tier}">score</span>` with green (90+), default (80-89), muted (70-79)
- `Components.jobCard(job)` → card HTML with score badge, title (linked if job_url), company, location, source, action buttons
- `Components.summaryStats(counts)` → stat items for summary strip
- `Components.jobList(jobs, heading)` → section with heading + cards
- `Components.jobDetail(job)` → full detail view with score breakdown table, requirements met, gaps, benefits, notes, action buttons
- `Components.briefViewer(html)` → rendered brief in design system styling
- `Components.emptyState(message)` → helpful empty state message
- `Components.sidebarCounts(counts)` → update sidebar count badges
- `Components.statusBadge(stage)` → stage-colored badge using pipeline status tokens
- `Components.runPanel(roleTypes)` → role type checkboxes for run dialog

All HTML generation uses textContent or manual escaping (never innerHTML with raw data).

---

#### Step 36: Create public/js/app.js

**File:** `03_agents/tests/v17/public/js/app.js`
**Action:** Create

**Builder implements from spec.** The builder must implement this file using the design system skill tokens and the specifications below. The prose description serves as the implementation spec.

Application router and view controller:
- Hash-based routing: `#digest` (default), `#pipeline`, `#detail/{key}`, `#brief/{key}`
- On load: fetch state + jobs, render summary strip, render digest view
- `renderDigest()` — "New" + "Reviewing" sections with job cards
- `renderPipeline()` — sidebar filtering, all stages
- `renderDetail(key)` — full job detail with action buttons
- `renderBrief(key)` — brief viewer
- Sidebar click → filter by stage
- Action button click → `API.postAction()` → optimistic UI update → refresh counts
- "Run Now" button → show overlay → role type checkboxes → confirm → `API.triggerRun()` → poll status → auto-refresh on complete

---

#### Step 37: Commit Phase 6

```bash
git add 03_agents/tests/v17/public/js/
git commit -m "feat(jsa): add V17 dashboard frontend — API client, components, router

Views: digest, pipeline, job detail, brief viewer.
Interactivity: user actions (Upstash), run controls (GitHub Actions).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Phase 7: Email Evolution

---

#### Step 38: Add "View on Dashboard" links to email template

**File:** `03_agents/tests/v17/.claude/skills/jsa-digest-email.md`
**Action:** Modify — add dashboard link to each job card.

In the card template (around line 86), after the company/location meta div, add:

```html
<!-- Dashboard link (if DASHBOARD_URL is set) -->
<div style="font-family:'DM Sans',sans-serif;font-size:12px;margin-top:8px;">
  <a href="{dashboard_url}/#detail/{job_key}" style="color:#1c1917;text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px;text-decoration-color:#d6d3d1;font-weight:500;font-size:12px;">View on Dashboard</a>
</div>
```

Also add `dashboard_url` as an optional 8th variable:
- `{dashboard_url}` — Vercel dashboard URL (e.g., `https://jsa-v17.vercel.app`). If null, omit "View on Dashboard" links.

Update the CLAUDE.md Step 19 digest-email dispatch to include dashboard_url:
```
prompt: '{"run_date": "...", "user_email": "...", "user_name": "...", "total_briefs": N, "new_today": [...], "still_active": [...], "verified_dir": "output/verified/", "dashboard_url": "..."}'
```

---

#### Step 39: Add incremental commit+push to CLI workflow

**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify — add commit+push instruction after each pipeline stage.

After Step 11 (search batch completion), add:

```markdown
**Step 11b: Incremental commit+push (interactive mode only).** After each search batch AND after dedup (Step 13), commit and push output:
```bash
git add output/ state.json
git commit -m "chore(jsa): search batch {N} — {run_date}"
git push origin main
```
This triggers Vercel redeployment so the dashboard shows incremental progress. Skip in scheduled mode (GitHub Actions handles its own commits).
```

Also add similar instruction after Step 18 (briefs) and Step 19 (digest):

```markdown
**Step 19c: Incremental commit+push (interactive mode only).** After digest+briefs HTML generation:
```bash
git add output/
git commit -m "chore(jsa): briefs + digest — {run_date}"
git push origin main
```
```

**Verify:**
```bash
grep "Incremental commit" 03_agents/tests/v17/CLAUDE.md
```

---

#### Step 40: Commit Phase 7

```bash
git add 03_agents/tests/v17/.claude/skills/jsa-digest-email.md 03_agents/tests/v17/CLAUDE.md
git commit -m "feat(jsa): email evolution — dashboard links + incremental commit+push

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Phase 8: CLI-Upstash Integration

---

#### Step 41: Add optional Upstash read to CLI for rejection filtering

**File:** `03_agents/tests/v17/CLAUDE.md`
**Action:** Modify — add optional Upstash read before brief generation (between Step 17 and Step 18).

Insert:

```markdown
**Step 17b: Optional Upstash rejection sync.** If `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` are set in `.env`:
1. Read all user action keys from Upstash via curl (no inline python — uses standard CLI tool):
   ```bash
   # Get all action keys
   curl -s -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN" "$UPSTASH_REDIS_REST_URL/keys/action:*"
   # Get value for a specific key
   curl -s -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN" "$UPSTASH_REDIS_REST_URL/get/action:role-type/company-title"
   ```
2. For any job where Upstash has `action == "rejected"`, skip brief generation even if user selected it in this session
3. Log: "Skipping {job_title} at {company} — rejected on dashboard"

The CLI agent uses `curl` to call the Upstash REST API directly. This avoids inline python (prohibited by regression list) and uses a standard CLI tool available in all environments.

If Upstash credentials are not set, skip this step silently. This is optional — the CLI works fully without dashboard integration.
```

**Verify:**
```bash
grep "Optional Upstash" 03_agents/tests/v17/CLAUDE.md
```

---

#### Step 42: Commit Phase 8

```bash
git add 03_agents/tests/v17/CLAUDE.md
git commit -m "feat(jsa): CLI-Upstash integration — optional rejection sync

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Phase 9: Tests

---

#### Step 43: Write test for salary penalty

**File:** `03_agents/tests/v17/tests/test_salary_penalty.py`
**Action:** Create — test that salary penalty logic works correctly when applied manually (since the penalty is applied by the search-verify agent, not by manage_state.py, we test the scoring rules as documented).

> **Note:** These tests verify the documented rules as arithmetic assertions. The actual penalty is applied by the search-verify agent during scoring. Integration testing requires a full agent run. Extract to a shared scoring function in a future iteration.

```python
"""Tests for salary validation penalty rules (V17 architectural fix)."""

from __future__ import annotations


class TestSalaryPenaltyRules:
    """Verify salary penalty application rules from algorithms.md."""

    def test_below_minimum_gets_penalty(self):
        """Job with salary_max below user's salary_min gets -10."""
        user_salary_min = 40000
        job_salary_max = 35000
        penalty = -10 if job_salary_max < user_salary_min else 0
        assert penalty == -10

    def test_overlapping_range_no_penalty(self):
        """Job where salary_min < user min but salary_max >= user min: no penalty."""
        user_salary_min = 40000
        job_salary_min = 25000
        job_salary_max = 60000
        penalty = -10 if job_salary_max < user_salary_min else 0
        assert penalty == 0

    def test_no_salary_listed_no_penalty(self):
        """Job with no salary info: no penalty."""
        job_salary_max = None
        penalty = -10 if (job_salary_max is not None and job_salary_max < 40000) else 0
        assert penalty == 0

    def test_penalty_can_push_below_threshold(self):
        """Base score 75 with -10 penalty = 65 (below 70 threshold but still presented)."""
        base_score = 75
        penalty = -10
        final_score = base_score + penalty
        assert final_score == 65
        # Job is still presented (base >= 70) but with penalty tag

    def test_penalized_cannot_outrank_compliant(self):
        """A penalized job with base 85 (final 75) ranks below compliant job with base 80."""
        job_a = {"base": 85, "penalty": -10, "final": 75}
        job_b = {"base": 80, "penalty": 0, "final": 80}
        ranked = sorted([job_a, job_b], key=lambda j: j["final"], reverse=True)
        assert ranked[0] == job_b  # compliant job ranks higher
```

---

#### Step 44: Update conftest for V17

**File:** `03_agents/tests/v17/tests/conftest.py`
**Action:** Already updated in Step 2 (comment change). Verify no v16 references remain.

---

#### Step 45: Run all tests

```bash
cd 03_agents/tests/v17
pytest tests/ -v
```

**Expected:** All existing manage_state tests pass + new salary penalty tests pass.

---

#### Step 46: Commit Phase 9

```bash
git add 03_agents/tests/v17/tests/
git commit -m "test(jsa): add V17 salary penalty tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Handoff Contract

- **Total steps:** 46
- **Total phases:** 9
- **Files created:**
  - `03_agents/tests/v17/` (full directory — copied from V16 + modified)
  - `03_agents/tests/v17/vercel.json`
  - `03_agents/tests/v17/requirements.txt`
  - `03_agents/tests/v17/.github/workflows/jsa-search.yml`
  - `03_agents/tests/v17/api/_upstash.py`
  - `03_agents/tests/v17/api/_response.py`
  - `03_agents/tests/v17/api/_files.py`
  - `03_agents/tests/v17/api/state.py`
  - `03_agents/tests/v17/api/jobs.py`
  - `03_agents/tests/v17/api/job.py`
  - `03_agents/tests/v17/api/action.py`
  - `03_agents/tests/v17/api/brief.py`
  - `03_agents/tests/v17/api/pipeline.py`
  - `03_agents/tests/v17/api/context.py`
  - `03_agents/tests/v17/api/run.py`
  - `03_agents/tests/v17/public/index.html`
  - `03_agents/tests/v17/public/css/dashboard.css`
  - `03_agents/tests/v17/public/js/api.js`
  - `03_agents/tests/v17/public/js/components.js`
  - `03_agents/tests/v17/public/js/app.js`
  - `03_agents/tests/v17/tests/test_salary_penalty.py`
- **Files modified:**
  - `03_agents/tests/v17/CLAUDE.md` (9 fixes + incremental push + Upstash integration)
  - `03_agents/tests/v17/references/algorithms.md` (salary penalty)
  - `03_agents/tests/v17/scripts/preview.sh` (server persistence)
  - `03_agents/tests/v17/.claude/skills/jsa-design-system.md` (dashboard extensions)
  - `03_agents/tests/v17/.claude/skills/jsa-onboarding.md` (remove source discovery)
  - `03_agents/tests/v17/.claude/skills/jsa-search-verify.md` (salary penalty in scoring + v17 path)
  - `03_agents/tests/v17/.claude/skills/jsa-digest-email.md` (dashboard links)
  - `03_agents/tests/v17/.claude/agents/*.md` (all 6 — v16→v17 path)
  - `03_agents/tests/v17/tests/conftest.py` (comment update)
- **Verification sequence:**
  1. `pytest 03_agents/tests/v17/tests/ -v` — all tests pass
  2. `grep -r "v16" 03_agents/tests/v17/.claude/` — no stale v16 references
  3. `grep "salary_penalty\|Salary Validation" 03_agents/tests/v17/references/algorithms.md` — salary fix present
  4. `grep "Unified Selection View" 03_agents/tests/v17/CLAUDE.md` — selection fix present
  5. `grep "nohup" 03_agents/tests/v17/scripts/preview.sh` — preview fix present
  6. `python3 -c "import json; json.load(open('03_agents/tests/v17/vercel.json'))"` — valid JSON
  7. Deploy to Vercel, navigate to dashboard URL — warm stone palette, no blue, correct fonts

<!-- STAGE COMPLETE: /plan, 2026-02-11 -->
<!-- STAGE COMPLETE: /revise after round 1, 2026-02-11 -->
<!-- STAGE COMPLETE: /revise after round 2, 2026-02-11 -->

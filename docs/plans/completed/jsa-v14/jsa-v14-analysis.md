# Session Analysis: Job Search Agent V14

## Summary
7 wins, 18 failures (2 critical, 9 major, 7 minor), 5 edge cases, 13 direct user complaints. The session completed all 20 orchestration steps successfully but spent ~3 hours on an intractable PDF pagination problem that was already documented as unsolvable in MEMORY.md from v12. The core pipeline (onboarding → search → verify → present → briefs → email) works end-to-end. Constraint compliance: 40/42 passed.

---

## What Went Well

1. **Onboarding flow executed cleanly** — CV parsing, profile extraction, source discovery, constraint derivation all completed with correct one-question-at-a-time pacing.
2. **Parallel subagent orchestration worked** — 3 search-verify, 4 brief generators, digest+briefs-pdf all dispatched correctly in batches.
3. **Cross-role deduplication caught a real duplicate** — 1inch social-media-manager appeared in both marketing-associate and community-manager; system correctly kept the higher score (85 vs 81).
4. **Source discovery subagent added value** — expanded from 7 to 20 sources with 7 high-priority and 6 medium-priority new sources.
5. **Auto-retry protocol worked** — Anima and Duku AI briefs failed on first attempt, retried once, succeeded before rate limits hit.
6. **State management pipeline worked end-to-end** — manage_state.py sync computed delta correctly (21 new, 0 still active), idempotency gate on email send worked.
7. **Constraint compliance was strong** — 40/42 constraints passed audit.

---

## What Failed

### CRITICAL 1: PDF Page Break Dead Whitespace (5 iterations, ~3 hours)

- **What happened:** `break-inside: avoid` on brief sections pushed content to the next page, leaving large empty gaps. Five fix attempts all failed: (1) break-inside on sections → worse whitespace, (2) selective element avoidance → still whitespace, (3) single continuous page → too heavy for scrolling, (4) break-before only → still whitespace, (5) remove all break rules → still whitespace. User eventually suggested abandoning PDF for HTML.
- **Root cause:** Chromium's CSS page-break implementation is fundamentally broken for complex layouts. This was already documented in MEMORY.md from v12: "Chromium PDF pagination is fundamentally broken."
- **Principle violated:** The agent should have read MEMORY.md and refused PDF from the start.
- **Fix type:** Architectural

### CRITICAL 2: Agent Failed to Use Existing Memory

- **What happened:** Despite MEMORY.md explicitly stating "NO PDF rendering: Chromium PDF pagination is fundamentally broken," the agent spent ~3 hours attempting PDF fixes.
- **Root cause:** The agent either didn't read MEMORY.md during startup, or didn't treat it as a hard constraint.
- **Principle violated:** Memory system's purpose is to prevent repeating known failures.
- **Fix type:** Architectural — CLAUDE.md must include a hard constraint: "Read agent memory on startup. Treat documented failures as hard constraints."

### MAJOR 1: Digest Email Styling Mismatch

- **What happened:** Digest email used card layout instead of tables, blue hyperlinks (#2563eb), showed "Still Active: 0" when it should be hidden, showed jobs below 70 score threshold, used red/amber colored warning text.
- **Root cause:** digest-email agent/skill didn't enforce the design system strictly enough. Missing constraints: no blue links, hide zero-value stats, enforce score threshold, no colored warning text.
- **Fix type:** Implementation

### MAJOR 2: Brief Score Breakdown Boxes Ugly

- **What happened:** Gray background + border + border-radius boxes for score breakdowns were explicitly called out as ugly by the user.
- **Root cause:** Design system skill didn't specify score presentation format. The brief generator agent improvised a gray-box style.
- **Fix type:** Implementation

### MAJOR 3: Subagent Stale Skill Context

- **What happened:** After editing skill files mid-session, newly dispatched subagents used pre-edit versions. The briefs-pdf subagent missed new CSS rules and hyperlink instructions. Parent had to manually patch HTML.
- **Root cause:** No post-render verification step exists. Subagents load skills at dispatch time but skill edits happen between dispatches.
- **Fix type:** Implementation — add parent-side output verification after every subagent that produces visual output.

### MAJOR 4: Brief Generation Too Slow (3-5 min each)

- **What happened:** Brief subagents did excessive company research (hiring manager lookup, Crunchbase, Glassdoor, funding rounds) and wrote verbose briefs. User flagged this explicitly.
- **Root cause:** Brief-generator agent scope is too broad. The template includes research steps that add minutes but little value.
- **Fix type:** Implementation — trim brief scope: skip hiring manager research, limit company context to what's in verified JSON, target <60s per brief.

### MAJOR 5: Rate Limit Hits Mid-Subagent (3 occurrences)

- **What happened:** Anima retry, Duku AI retry, and briefs-pdf re-render all hit Claude Max daily limits. Whether output was saved depended on timing luck.
- **Root cause:** No token budget awareness. The agent dispatches subagents without considering remaining capacity.
- **Fix type:** Implementation — warn user about rate limit risk after retries.

### MAJOR 6: HTTP Server Startup Failures (4 occurrences)

- **What happened:** Local Python HTTP server repeatedly failed (port conflicts, ERR_EMPTY_RESPONSE) across ports 8765-8787. Required multiple kill-and-restart cycles.
- **Root cause:** No standardized preview utility. Each attempt was ad-hoc.
- **Fix type:** Implementation — add a `scripts/preview.sh` utility with fixed port, kill-existing, health-check.

### MAJOR 7: Context Window Exhaustion (4 compactions)

- **What happened:** Session hit context limits at least 4 times, triggering compaction. Each compaction lost active context, requiring file re-reads.
- **Root cause:** The PDF fix iterations consumed massive context (5 rounds of edit-render-screenshot-analyze). Wouldn't have happened if PDF was avoided.
- **Fix type:** Architectural (resolved by removing PDF) + Implementation (delegate visual debugging to subagent).

### MAJOR 8: Briefs-PDF Subagent Re-Render Failed

- **What happened:** Briefs-pdf subagent re-render hit an "image size error" and failed completely. Parent had to render directly.
- **Root cause:** Subagent attempted to generate a PDF too large for the rendering pipeline.
- **Fix type:** Architectural (resolved by removing PDF for HTML-only).

### MAJOR 9: Connection Errors on First Brief Attempts

- **What happened:** Anima and Duku AI brief generators both hit connection errors on first attempt, producing no output. Required retries.
- **Root cause:** Likely transient network/API issues. Auto-retry handled it, but the initial failure cost time.
- **Fix type:** N/A — auto-retry protocol handled correctly.

### MINOR 1: No Pre-Run Cleanup Executed

- **What happened:** No evidence of `rm -f output/jobs/*` etc. cleanup commands despite CLAUDE.md specifying this for new runs.
- **Root cause:** Missing enforcement in startup sequence.
- **Fix type:** Implementation

### MINOR 2: No Mid-Session Checkpoint (Step 9)

- **What happened:** `session-state.md` only written once at Step 20, not after each search batch as specified in Step 9.
- **Root cause:** Constraint exists but isn't emphasized.
- **Fix type:** Implementation

### MINOR 3: Chrome PDF Viewer Blocked Screenshots

- **What happened:** Playwright couldn't screenshot Chrome's built-in PDF viewer (chrome-extension:// URL restriction).
- **Root cause:** Known browser security limitation. Moot once PDF is removed.
- **Fix type:** N/A (resolved by removing PDF)

### MINOR 4: User Opened Wrong File

- **What happened:** User opened stale PDF from ~/Downloads/ while agent referenced project directory copy.
- **Root cause:** Agent didn't provide explicit full file path.
- **Fix type:** Implementation — always state full absolute path after generating output.

### MINOR 5: Playwright Browser Launch Conflict

- **What happened:** Chrome already running, conflicting with Playwright's persistent context.
- **Root cause:** Known limitation when Chrome is already open.
- **Fix type:** Minor — use non-persistent context or document the limitation.

### MINOR 6-7: Port Conflicts and Sleep Timing

- **What happened:** Multiple port conflicts and need for sleep delays before HTTP server was responsive.
- **Root cause:** No standardized preview utility.
- **Fix type:** Implementation (covered by preview.sh utility fix).

---

## Edge Cases

1. **Stale subagent skill context** — Subagents launched after skill file edits used pre-edit versions. No invalidation mechanism.
2. **Rate limit mid-subagent** — Output saved depends on timing luck. No graceful handling.
3. **PDF vs HTML viewer routing** — Chrome's PDF viewer intercepted HTTP-served PDFs, blocking screenshot tools.
4. **User opening wrong file** — No mechanism to ensure user opens correct version when multiple copies exist.
5. **Chromium PDF pagination fundamentally broken** — Multiple CSS break strategies all failed. Irresolvable via CSS.

---

## Specific Fixes

### Architectural Changes

#### A1: Remove PDF Output — HTML-Only Briefs

The briefs output must be an HTML file opened in the browser. No PDF generation.

**Changes needed:**
- Rename/update `briefs-pdf` agent → `briefs-html`
- Remove all PDF-related code from agent and skill
- Update CLAUDE.md Step 18 to reference HTML output, not PDF
- Update Step 19 email to attach `.html` not `.pdf`
- Add HARD CONSTRAINT: "Never generate PDF output. Briefs are HTML files."
- HTML briefs: continuous scroll, border-top separators between briefs

#### A2: Add Memory-as-Hard-Constraint Rule

Add to HARD CONSTRAINTS in CLAUDE.md:

```diff
+ 3. **Read agent memory on startup.** Check `.claude/agent-memory/` for documented failures. Treat them as hard constraints — never re-attempt a known-broken approach.
```

### Implementation Fixes

#### I1: Digest Email — Enforce Design System Constraints

```diff
+ ## Digest Email Constraints
+ - No blue hyperlinks. Use the design system's link color.
+ - Hide any section with zero items (e.g., "Still Active: 0" → don't render)
+ - Only show jobs scoring 70+ (same threshold as presentation)
+ - No colored warning text (red, amber, orange). Use muted gray for footnotes.
+ - Desktop layout: use tables, not cards. Cards for mobile only.
+ - Remove score distribution and statistics section — keep it clean.
+ - Job links in 70+ section: make clickable but not ugly (white underline or bold, follow best practices).
```

#### I2: Score Breakdown Presentation

```diff
+ ## Score Breakdown
+ - No gray background boxes, no borders, no border-radius wrappers
+ - Present score breakdown as inline text or a minimal table
+ - Match the editorial aesthetic: clean, no visual clutter
```

#### I3: Brief Generator — Trim Scope for Speed

```diff
+ ## Speed Constraint
+ - Do NOT research hiring managers, Crunchbase profiles, Glassdoor reviews, or funding rounds
+ - Company context: use ONLY what's in the verified JSON (company name, description, industry)
+ - Target: complete each brief in <60 seconds
+ - Brief length: 300-500 words max
```

#### I4: Post-Render Verification Step

```diff
+ **Step 18b: Verify visual output.**
+ After digest-email and briefs-html subagents complete, the parent MUST:
+ 1. Read the generated HTML files
+ 2. Check for design system compliance (link colors, score presentation, layout)
+ 3. If non-compliant, patch directly or re-dispatch with explicit corrections
+ Do NOT assume subagents picked up recent skill edits.
```

#### I5: Pre-Run Cleanup Logging

```diff
+ Log: "Cleaning stale output from previous run ({last_run_date})."
+ If last_run_date is null (first run), log: "First run — no cleanup needed."
```

#### I6: Mid-Session Checkpoint Enforcement

```diff
- Checkpoint: write `output/session-state.md` progress after every 3 role types.
+ **MANDATORY:** Write `output/session-state.md` progress after EVERY search batch completes. This is not optional.
```

#### I7: Explicit File Path After Output Generation

```diff
+ ## OUTPUT PATHS
+ After generating any user-facing output file, always state the full absolute path.
+ This prevents the user from opening stale copies from other locations.
```

#### I8: Preview Utility Script

Create `scripts/preview.sh` with fixed port (8800), kill-existing, health-check-before-navigate pattern. Add to CLAUDE.md: "Use `scripts/preview.sh <file>` to preview HTML. Never start ad-hoc HTTP servers."

---

## Handoff Contract

- **Architectural fixes needed:** A1 (remove PDF, HTML-only briefs), A2 (memory-as-hard-constraint rule)
- **Implementation fixes needed:** I1 (digest email constraints), I2 (score breakdown style), I3 (brief generator speed), I4 (post-render verification), I5 (cleanup logging), I6 (checkpoint enforcement), I7 (explicit file paths), I8 (preview utility)
- **New constraints:** HARD 3 (read agent memory on startup), digest email design enforcement, brief speed constraint, post-render verification step
- **Regression tests to include:** PDF generation must never be attempted, digest must not show blue links or zero-value sections, briefs must complete in <60s, session-state.md must be written after search batches

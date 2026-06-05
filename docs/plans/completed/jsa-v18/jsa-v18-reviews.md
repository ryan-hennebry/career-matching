# JSA V18 Reviews

## Round 2 — 2026-02-16

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
None.

### Recommended Changes
- [x] **[Conf: 78] [architecture-strategist]** `renderEmptyState` in `components.js` contains inline `onclick="triggerSearch()"` but `triggerSearch` is defined in `app.js`. Hidden cross-module dependency violates the JS Ownership Contract ("no event binding" in components.js). -> Have `renderEmptyState` emit a `data-action="trigger-search"` attribute and let `app.js` bind via event delegation, consistent with the ownership contract.
- [x] **[Conf: 78] [architecture-strategist, code-simplicity-reviewer]** Phase 3 frontend tests are string-presence assertions against source files (e.g., `"tier-high" in js`), not behavioral tests. Cannot distinguish between functional code and comments containing the same string. -> Add at least one Node.js-based unit test for `getScoreTier` that executes the function, or document the accepted fidelity level. (overlaps with code-simplicity-reviewer finding on substring test fragility)
- [x] **[Conf: 75] [architecture-strategist]** `_compute_dedup` returns items with internal keys (`_path`) that `_apply_dedup` consumes. Coupling is fragile — reordering compute/apply/strip breaks deletion silently. -> Return paths as a separate list from `_compute_dedup` so `_apply_dedup` takes a plain path list.
- [x] **[Conf: 75] [regression-checker]** V14 "Digest email must not show blue hyperlinks" is not verified against digest email HTML. `verify_html.py` only checks `public/index.html`. -> Add note that post-render check or `verify_html.py` should also run against digest email HTML.
- [x] **[Conf: 72] [architecture-strategist, code-simplicity-reviewer]** `config/palette.json` is premature extraction — exactly one consumer (`verify_html.py`). The planned second consumer (CSS documentation) is not in V18 scope. -> Inline prohibited color constants in `verify_html.py` until a second consumer exists. (overlaps between architecture-strategist `--palette` finding and code-simplicity-reviewer premature extraction finding)
- [x] **[Conf: 72] [regression-checker]** V14 digest email behavioral regressions (hide zero-item sections, 70+ threshold) not mentioned in Regression Verification Notes. -> Add one-line note confirming these are covered by existing CLAUDE.md workflow steps.
- [x] **[Conf: 70] [code-simplicity-reviewer]** `_apply_dedup` and `--dry-run` flag are untested. No test verifies dry-run behavior or confirms files are actually deleted. -> Add tests for both paths, or defer `--dry-run` until needed.
- [x] **[Conf: 70] [regression-checker]** V17 GH Actions workflow copy mechanism from nested path to repo root is untested. -> Add verification note or test confirming deployment copies workflow to repo root.

### Nice-to-Have
- [x] **[Conf: 72] [code-simplicity-reviewer]** Steps 14/16/18/20 each append test classes to `test_dashboard_frontend.py` incrementally. Since all tests are known upfront, write the complete file once in Step 14. -> Write complete `test_dashboard_frontend.py` in Step 14; subsequent steps implement CSS/JS/HTML and run existing tests.
- [ ] **[Conf: 65] [architecture-strategist]** `_compute_dedup` collision key uses `"unknown"` as domain fallback when `source_url` is missing. Two jobs from different sources both lacking URLs would collide. -> Consider using role directory name as secondary differentiator.
- [ ] **[Conf: 65] [code-simplicity-reviewer]** `TestCommentedDarkMode` tests that dark mode CSS is present but commented out — tests a comment, not behavior. -> Remove until dark mode is active.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** JS Ownership Contract lives only in plan prose — not encoded in source file headers. Future contributors may not see it. (Conf: 55)
- **[architecture-strategist]** `test_dashboard_frontend.py` grows across Steps 14/16/18/20 with potential helper duplication. Minor cohesion concern. (Conf: 52)
- **[code-simplicity-reviewer]** `renderEmptyState` coupling to `triggerSearch` is acceptable at current scale. (Conf: 55)
- **[code-simplicity-reviewer]** Dedup collision key lowercases company/title but not domain — `urlparse().netloc` is lowercase in practice but explicit `.lower()` would be more consistent. (Conf: 50)
- **[regression-checker]** V14 brief generation speed, PDF, brief styling, and ad-hoc HTTP server regressions are runtime CLAUDE.md constraints unchanged by V18. No conflict. (Conf: 55)
- **[regression-checker]** V15/V16 behavioral regressions (brief selection, email idempotency, auto-retry, onboarding, salary) are runtime workflow concerns not touched by V18. No conflict. (Conf: 50)

### Per-Reviewer Verdicts
- architecture-strategist: APPROVED
- code-simplicity-reviewer: APPROVED
- regression-checker: APPROVED

### Statistics
- Total findings collected: 17
- Final actionable findings: 11 (0 Required, 8 Recommended, 3 Nice-to-Have, 6 informational)

---

## Round 1 — 2026-02-16

### Reviewers Active
- architecture-strategist
- code-simplicity-reviewer
- regression-checker

### Required Changes
- [x] **[Conf: 88] [code-simplicity-reviewer]** 8 redundant "verify fail" steps (Steps 2, 6, 10, 15, 19, 22, 25, 28) are pure ceremony — they run the same command listed in the preceding step's Verify block. -> Merge each "verify fail" step into its predecessor's Verify section as "Expected: all assertions fail." Reduces plan from 31 to 23 steps.
- [x] **[Conf: 88] [architecture-strategist, code-simplicity-reviewer]** `_dedup_verified` mutates filesystem (deletes files) inside what is also a query/reporting function. Mixes command and query responsibilities, preventing dry-run usage and making tests fragile. -> Split into `_compute_dedup(verified_dir) -> dict` (returns kept/removed without disk mutations) and `_apply_dedup(removed_list)` (performs deletions). CLI handler calls both; tests call compute-only. Add `--dry-run` flag. (overlaps with code-simplicity-reviewer finding on dedup side effects)
- [x] **[Conf: 85] [architecture-strategist]** `verify_html.py` hardcodes prohibited colors while `dashboard.css` defines the palette independently — two independent sources of truth that will drift. -> Extract color allowlist/blocklist into a shared data source (e.g., `config/palette.json`) referenced by both `verify_html.py` and CSS documentation.
- [x] **[Conf: 82] [architecture-strategist]** Unclear ownership boundary between `components.js` and `app.js` — both render empty states and reference "Run Search" CTA. -> Define explicit contract: `components.js` exports pure stateless render functions, `app.js` owns DOM binding and orchestration. Empty state rendering lives in exactly one file. Document in plan.
- [x] **[Conf: 82] [code-simplicity-reviewer]** `verify_html.py` is over-engineered: ~90-line script + dedicated test file for what amounts to a regex check over CSS contexts. -> Inline into existing test suite as a pytest function, or simplify to <30 lines by dropping the two-function `_extract_css_contexts`/`_check_css_for_prohibited` pattern. (overlaps with architecture-strategist dual-source finding above)
- [x] **[Conf: 78] [code-simplicity-reviewer]** `test_claude_md.py` and `test_workflow.py` are brittle string-matching tests against prose/YAML that break on any reword. -> Reduce to one assertion per concern (one for agent-memory, one for UX rule) instead of 6+ overlapping substring checks. (overlaps with architecture-strategist Conf 71 finding on Phase 3 string-matching tests)

### Recommended Changes
- [x] **[Conf: 80] [regression-checker]** V17 regression "API endpoints must fall back from Upstash Redis to state.json" is not addressed anywhere in the plan. -> Add a verification step or note confirming this is already implemented, or add a test asserting fallback behavior.
- [x] **[Conf: 78] [regression-checker]** V17 regressions: Vercel API handlers must use Vercel-compatible pattern, vercel.json must use modern config, auto-deploy from main must be verified. None addressed. -> Add verification step in Deployment Verification confirming vercel.json uses `functions` + `rewrites`, handlers use Vercel-compatible exports, auto-deploy is active.
- [x] **[Conf: 75] [regression-checker]** V17 regression: GitHub Actions workflows must live at repo root. Plan modifies `03_agents/tests/v17/.github/workflows/daily-digest.yml` (nested path). -> Clarify in plan that nested path is intentional for test harness structure, or move to repo root.
- [x] **[Conf: 75] [architecture-strategist, code-simplicity-reviewer]** Dedup collision key `{source_domain}:{filename_slug}` — fallback `"unknown"` domain causes false positives when multiple jobs lack `source_url`. -> Use `{source_domain}:{company}:{title}` as collision key (fields already in JSON), or add `_role` to fallback key. (overlaps between architecture-strategist and code-simplicity-reviewer)
- [x] **[Conf: 75] [code-simplicity-reviewer]** Phase 3 has 6 new test files doing the same pattern (read file, assert substrings). -> Consolidate into single `test_dashboard_frontend.py` with class-per-file organization.
- [x] **[Conf: 73] [architecture-strategist]** `triggerSearch()` referenced in HTML onclick handlers but never defined in the plan. Implicit interface. -> Define `triggerSearch` explicitly in plan (which file, what it does), or replace onclick with event-delegated handler in `app.js`.
- [x] **[Conf: 72] [regression-checker]** V14 regression (recurred V16): session-state.md must be written after every search batch. Not verified in plan. -> Add note confirming existing coverage or add test assertion.
- [x] **[Conf: 70] [code-simplicity-reviewer]** Step 31 references non-existent Playwright visual tests (`tests/visual/`) and includes "Manual: Open dashboard in browser" instruction that violates CR5 regression item (no technical work for user). -> Write Playwright test in earlier step or remove Step 31. Replace manual instruction with subagent delegation.

### Nice-to-Have
- [ ] **[Conf: 65] [architecture-strategist]** Phase 3 CSS is a single ~80-line append block with no logical grouping. -> Consider splitting into `tokens.css`, `components.css`, `layout.css`.
- [ ] **[Conf: 65] [code-simplicity-reviewer]** CSS block in Step 20 is ~85 lines of literal CSS pasted into plan, hard to scan. -> Reference a design spec or provide only token definitions, letting build agent compose full CSS.
- [ ] **[Conf: 65] [regression-checker]** V14 regression "Pre-run cleanup must execute and log when last_run_date differs from today" not verified. -> Consider adding structural test for CLAUDE.md pre-run cleanup logic.

### Reviewer Notes (informational only, no action)
- **[architecture-strategist]** Plan modifies CLAUDE.md in both Phase 1 (Step 3) and Phase 2 (Step 12) with non-overlapping edit regions. Documented in Risk Decision #4, appears safe, but concurrent builds could conflict. (Conf: 55)
- **[architecture-strategist]** Rollback plan uses `git revert HEAD~6..HEAD` assuming exactly 6 commits. Tag-based rollback would be more robust. (Conf: 58)
- **[code-simplicity-reviewer]** Rollback plan assumes exactly 6 commits — same concern as architecture-strategist. (Conf: 55)
- **[code-simplicity-reviewer]** Step 3 Edit 2 adds a UX rule that partially duplicates existing "Never ask user to run commands..." line. New line is superset; old could be removed. (Conf: 52)
- **[regression-checker]** V14 "Brief generation <60s" not in V18 scope. (Conf: 50)
- **[regression-checker]** V16 "Onboarding role question" not in V18 scope. (Conf: 50)

### Per-Reviewer Verdicts
- architecture-strategist: Needs Changes
- code-simplicity-reviewer: Needs Changes
- regression-checker: Needs Changes

### Statistics
- Total findings collected: 27
- Final actionable findings: 20 (6 Required, 8 Recommended, 3 Nice-to-Have, 6 informational)

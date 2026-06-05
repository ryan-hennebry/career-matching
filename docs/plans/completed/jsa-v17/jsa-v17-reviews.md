# JSA V17 Reviews

## Round 2 — 2026-02-11

### Reviewer: DHH (Rails/37signals Philosophy)

**Focus:** Scope discipline, shipping pragmatism, anti-complexity, security fundamentals.

**Round 1 fixes verified:** `get_user_actions()` now uses `mget()` with documented scaling note (checked). `api/run.py` now has Bearer token auth via `JSA_RUN_SECRET` (checked). Prose-only frontend steps now explicitly marked "Builder implements from spec" (checked). `_response.py` shared helper added (checked). GitHub Actions workflow now accepts location/country as inputs with defaults (checked). Step 12 verify block now covers all 3 files (checked).

#### Required Changes

- [ ] **Split the dashboard into its own version or ship the 9 fixes first, independently.** (Carried from Round 1 — unchecked, not addressed by revision.) The plan is still 46 steps across 9 phases. Phase 1 (steps 1-13) is a clean, shippable unit. Phases 2-9 are a dashboard product. These are two different deliverables coupled into one version. The risk: if any dashboard step blocks, the 9 fixes — which are known-good regression repairs — sit unshipped. This is the only Required finding remaining.

#### Recommended Changes

- [ ] **The `_files.py` helper assumes Vercel bundles the entire output directory at deploy time via Git-committed files.** (Carried from Round 1 — unchecked.) The architectural note at line 14 acknowledges the split-brain model, but there's still no documented staleness window or failure behavior when Vercel build cache serves stale files. The incremental commit+push in Step 39 mitigates but doesn't eliminate: a failed push leaves the dashboard stale with no indicator to the user. Add a "last updated" timestamp visible in the dashboard (derived from the most recent file mtime or a committed metadata file).

- [ ] **No `api/__init__.py` file.** (Carried from Round 1 — unchecked.) Vercel Python runtime may resolve `from api._files import ...` without `__init__.py` since each function runs independently, but this is runtime-dependent. The plan should either add an empty `__init__.py` to be safe, or add a note in the verification sequence (Step 7 of Handoff Contract) to test cross-module imports on the first Vercel deployment.

#### Nice-to-Have

- [ ] **The `preview.sh` rewrite uses `open` (macOS-only) without a cross-platform fallback.** (Carried from Round 1 — unchecked.) This is a development tool on a known macOS environment. Low priority, but a one-line fallback (`open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null || echo "Open: $URL"`) costs nothing.

- [x] **The `_response.py` helper is defined in Step 20b but the inline code in Steps 22-29 still shows the manual boilerplate pattern.** The builder note at line 1163 says to refactor, but showing one pattern in the plan code and expecting a different pattern at build time is confusing. This was partially addressed by the "builder should refactor" note — acceptable for build, but the code examples will be misleading during review.

**Approval Status: APPROVED for build** — The one remaining Required change (scope split) is a project management decision, not a technical defect. The plan is technically sound for build. All Round 1 technical issues have been addressed. The scope question should be resolved by the project owner, not blocked in review.

---

### Reviewer: Kieran (Rails Core / Architecture)

**Focus:** System architecture, separation of concerns, data flow integrity, consistency.

**Round 1 fixes verified:** `derive_stage()` now has documented priority table in docstring (checked). `state.py` now imports and uses `derive_stage()` from `jobs.py` with "expired" in counts dict (checked). API test files removed from manifest, replaced with post-deployment note at line 47 (checked). Upstash CLI integration now specifies `curl` as the concrete mechanism (checked). `brief.py` now has two-strategy lookup (individual MD then consolidated HTML, checked). `context.py` now returns section names by default, content only for requested sections (checked). Design system skill file now explicitly defines tokens-only role vs dashboard.css canonical source (checked).

#### Required Changes

None.

#### Recommended Changes

- [ ] **The `api/action.py` endpoint (Step 25) still uses inline CORS/response boilerplate instead of the `_response.py` helper defined in Step 20b.** All 8 endpoint files show the manual pattern. The builder note acknowledges this, but `action.py` is especially important to get right since it's a write endpoint. The plan code should at minimum show the import of `_response.py` in one endpoint as a reference implementation, so the builder has a concrete example of the refactored pattern.

- [x] **The `api/job.py` endpoint (Step 24) reads a JSON file using the `key` parameter directly in a file path (`output/verified/{key}.json`) without any path traversal sanitization.** If a malicious key like `../../secrets/credentials` is passed, it could read arbitrary files relative to the project root. Add validation that `key` matches the expected format (e.g., `^[a-z0-9-]+/[a-z0-9-]+$`) before constructing the file path.

#### Nice-to-Have

- [x] **The GitHub Actions workflow note (line 1045) and Vercel runtime note (line 949) are good additions from the revision.** These document assumptions that would otherwise be discovered only at deployment time.

**Approval Status: APPROVED for build** — All Round 1 Required changes addressed. The two new Recommended findings (response helper usage pattern, path traversal) are important for the builder to address but don't block the plan's approval.

---

### Reviewer: Code Simplicity

**Focus:** Clarity, maintainability, unnecessary complexity, plan-manifest consistency.

**Round 1 fixes verified:** `get_user_actions()` now uses `mget()` for 2 round-trips (checked). Test file manifest cleaned up — deferred API tests acknowledged in note at line 47 (checked). `_response.py` helper created in Step 20b (checked). Unused `re` import removed from `context.py` (checked). Steps 31/34/35/36 explicitly marked "Builder implements from spec" (checked). Salary penalty test note acknowledges arithmetic-only limitation and suggests future extraction (checked).

#### Required Changes

None.

#### Recommended Changes

- [ ] **The plan still shows inline CORS boilerplate in all 8 endpoint code blocks (Steps 22-29) despite defining `_response.py` in Step 20b.** The builder note at line 1163 says to refactor, but showing incorrect code in the plan is a maintenance trap. If anyone reviews the plan later, they'll see the inline pattern and assume that's the implementation. At minimum, update one endpoint (e.g., `state.py` in Step 22) to show the refactored `json_response()` usage as the canonical example.

#### Nice-to-Have

- [ ] **The `_files.py` `list_verified_jobs()` silently catches `json.JSONDecodeError` and `OSError`.** (Carried from Round 1 — unchecked.) Still no logging. For a dashboard that reads deployed files, a silently corrupt JSON file is invisible. Add `import logging; logger = logging.getLogger(__name__)` and `logger.warning(f"Skipping {json_file}: {e}")` in the except block.

- [ ] **The `run.py` handler docstring says "GET /api/run/status" but Vercel routing won't distinguish `/api/run` from `/api/run/status` — both route to `run.py`.** (Carried from Round 1 — unchecked.) The GET handler docstring at line 1856 is misleading. Update the docstring to say "GET /api/run" since that's the actual route.

**Approval Status: APPROVED for build** — All Required changes from Round 1 resolved. Remaining items are Recommended or Nice-to-Have. The plan is clear enough for a builder to execute successfully.

<!-- STAGE COMPLETE: /review round 2, 2026-02-11 -->

---

## Round 1 — 2026-02-11

### Reviewer: DHH (Rails/37signals Philosophy)

**Focus:** Scope discipline, shipping pragmatism, anti-complexity, security fundamentals.

#### Required Changes

- [ ] **Split the dashboard into its own version or ship the 9 fixes first, independently.** The plan title says "Incremental Fixes + Vercel Dashboard" but 46 steps across 9 phases with ~20 new files is not incremental. The fixes (Phase 1) are well-scoped and valuable. The dashboard (Phases 2-8) is a separate product surface. Coupling them means the fixes can't ship until the dashboard works, and the dashboard can't be evaluated without the fixes clouding the diff. Ship Phase 1 as V17, build the dashboard as V18 if it still makes sense after running V17.

- [x] **The `get_user_actions()` function uses `redis.keys("action:*")` which is an O(N) scan of the entire keyspace.** This is called on every single API endpoint (state, jobs, pipeline). For a small dataset it's fine, but it's a bad pattern to bake into the foundation. Use a Redis hash (`HGETALL jsa:actions`) or at minimum document the scaling limitation and when to migrate. Don't ship a known anti-pattern as the canonical implementation.

- [x] **The `api/run.py` stores a GitHub PAT in Vercel environment variables and exposes it through a POST endpoint with no authentication.** Anyone who discovers the dashboard URL can trigger GitHub Actions workflows. The endpoint needs at minimum a shared secret or session token. `Access-Control-Allow-Origin: *` on a write endpoint that dispatches CI jobs is a security hole, not a feature.

- [x] **Steps 31 (dashboard.css), 34 (api.js), 35 (components.js), and 36 (app.js) have no actual code -- just prose descriptions of what the files should contain.** A build plan where 4 of the most complex files say "this should include X, Y, Z" is a spec, not a plan. Either provide the implementation or acknowledge these need their own detailed steps. The builder will have to make dozens of undocumented decisions for these files.

#### Recommended Changes

- [ ] **The `_files.py` helper assumes Vercel bundles the entire output directory at deploy time via Git-committed files.** This is fragile -- the output directory changes every CLI run, meaning every run requires a git push + Vercel redeploy to update the dashboard. This coupling is documented in Step 39 but the failure mode isn't: what happens when the Vercel build cache serves stale files? Add a cache-busting mechanism or document the expected staleness window.

- [x] **8 separate serverless functions share the exact same CORS header pattern and JSON response boilerplate.** Every handler repeats `self.send_response()`, `self.send_header("Content-Type", "application/json")`, `self.send_header("Access-Control-Allow-Origin", "*")`, `self.end_headers()`. Extract a `_response.py` helper with `json_response(self, data, status=200)` and `cors_preflight(self)`. This is the kind of duplication that turns 8 files into a maintenance nightmare.

- [x] **The GitHub Actions workflow (Step 18) hardcodes `--location "London"` and `--country UK`.** These should come from context.md or be passed as workflow inputs. A "Run Now" dashboard feature that only works for London, UK isn't a dashboard feature -- it's a London feature.

- [ ] **No `api/__init__.py` file.** Vercel Python functions may or may not need it depending on the import resolution, but the cross-module imports (`from api._files import ...`, `from api.jobs import derive_stage`) are risky without an explicit package marker. Test this on Vercel before committing to the pattern.

- [x] **Step 12 replaces the ENTIRE onboarding skill file content** but then also modifies the agent file and CLAUDE.md. This is 3 coordinated edits in one step across different files. If any one edit is missed, the system breaks. Make these atomic -- verify all 3 files are consistent as part of the same step's verify block.

#### Nice-to-Have

- [x] **The salary penalty test (Step 43) tests arithmetic, not behavior.** These tests would be more valuable if they tested a scoring function directly. As written, they'll always pass regardless of whether the salary penalty is actually implemented.

- [ ] **The `preview.sh` rewrite uses `open` (macOS-only) without a cross-platform fallback.**

- [x] **The plan lists `test_api_state.py`, `test_api_jobs.py`, `test_api_action.py` in the Files to Modify section but Phase 9 only creates `test_salary_penalty.py`.** The other 3 test files are never written. Either add steps for them or remove them from the file list.

**Approval Status: Needs Changes**

---

### Reviewer: Kieran (Rails Core / Architecture)

**Focus:** System architecture, separation of concerns, data flow integrity, consistency.

#### Required Changes

- [x] **The `derive_stage()` function in `api/jobs.py` has an implicit priority ordering that isn't documented or tested.** Expired takes priority over rejected, which takes priority over accepted. But what if a job is both in `expired_keys` AND has a user action of "accepted"? The user accepted it, then it expired -- should it show as "expired" or "applied"? This business logic needs a documented priority table and corresponding tests.

- [x] **`api/state.py` and `api/jobs.py` both independently reconstruct pipeline stage counts, with subtly different logic.** `state.py` doesn't handle `expired_keys` at all (no "expired" in its counts dict), while `jobs.py` does via `derive_stage()`. These two endpoints will return inconsistent counts. Either `state.py` should import and use `derive_stage()` (like `pipeline.py` does), or extract the stage derivation into `_files.py` as the single source of truth.

- [x] **The plan lists 3 API test files (`test_api_state.py`, `test_api_jobs.py`, `test_api_action.py`) in the "Files to Modify" section but never provides implementation steps for them.** Phase 9 only creates `test_salary_penalty.py`. Add steps for at least `test_api_state.py` and `test_api_action.py`.

- [x] **The Upstash rejection sync (Step 41) doesn't specify the concrete mechanism for the CLI agent to call Upstash.** The plan says "if credentials are set in `.env`" but doesn't say how the Claude agent makes HTTP calls. The regression list says "Never write inline Python (`python3 -c`) that imports manage_state internals." Define the concrete mechanism (new script? curl? manage_state subcommand?).

#### Recommended Changes

- [x] **The dashboard reads from Git-committed files but writes to Upstash Redis, creating a split-brain data model.** There's no reconciliation mechanism if job files are deleted during cleanup but Redis actions persist, or if Redis is cleared but the deployment is stale. Add a reconciliation note or health endpoint.

- [x] **The `brief.py` endpoint assumes individual markdown brief files (`{slug}-brief.md`) exist, but the briefs-html subagent generates a consolidated HTML file (`briefs-YYYY-MM-DD.html`).** The plan needs to reconcile how individual briefs are stored vs. how the API serves them. If only consolidated HTML exists, `/api/brief` won't find anything.

- [x] **The `context.py` endpoint returns the raw `context.md` text containing the user's full CV data (name, email, phone, LinkedIn, work history) from an unauthenticated public endpoint.** Either add authentication or remove the raw text and only return section names/summaries.

- [x] **Phase 2 (Step 14) adds ~150 lines of CSS patterns to a Markdown skill file that must be manually transcribed into `dashboard.css` (Step 31).** This duplication means two files must be updated when the design system changes. Either generate `dashboard.css` from the skill file, or keep the skill file as token definitions only.

#### Nice-to-Have

- [x] **The `vercel.json` uses `@vercel/python@4.5.0` -- pinning to a specific runtime version.** Document the assumption that this version exists and is current at build time.

- [x] **The GitHub Actions workflow commits and pushes directly to `main` with a bot identity.** If the repo has branch protection rules requiring PR reviews, this workflow will fail silently. Document the assumption.

**Approval Status: Needs Changes**

---

### Reviewer: Code Simplicity

**Focus:** Clarity, maintainability, unnecessary complexity, plan-manifest consistency.

#### Required Changes

- [x] **The `_upstash.py` helper's `get_user_actions()` makes N+1 Redis calls** (one `keys()` + one `get()` per key). Use `mget()` to batch the value retrieval, reducing Redis round-trips from N+1 to 2.

- [x] **The plan declares 3 test files (`test_api_state.py`, `test_api_jobs.py`, `test_api_action.py`) in the "New files" manifest but never writes them.** This is a plan-manifest inconsistency. Either add implementation steps or remove them from the file list.

#### Recommended Changes

- [x] **Every API handler repeats the same 4-line response pattern across 8 files.** Extract to a shared response helper in `_response.py` or add methods to a base handler class. This reduces each endpoint by ~15 lines and centralizes CORS configuration.

- [x] **`api/context.py` imports `re` but never uses it.** Remove the unused import. Symbolic of code that hasn't been tested.

- [x] **Step 31 (dashboard.css) is a prose description, not an implementation.** The builder must manually synthesize CSS from 8 bullet points and the design system skill. Either provide the CSS or explicitly mark as "builder implements from spec."

- [x] **The salary penalty test (Step 43) doesn't test any actual code.** Extract the penalty logic into a shared function and test that function. Inline arithmetic assertions provide false confidence.

#### Nice-to-Have

- [ ] **The `_files.py` `list_verified_jobs()` silently catches `json.JSONDecodeError` and `OSError`.** Consider logging a warning when a JSON file fails to parse, so deployment issues are discoverable.

- [ ] **The `run.py` handler docstring says "GET /api/run/status" but Vercel routing won't distinguish `/api/run` from `/api/run/status` -- both route to `run.py`.** The GET handler fires for any GET to `/api/run`. Either clarify the routing or separate into two files.

**Approval Status: Needs Changes**

<!-- STAGE COMPLETE: /review round 1, 2026-02-11 -->

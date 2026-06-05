# Compound Proposals: JSA V17

## Proposal 1: Add `.claude/solutions/` to Cross-Version Memory
- Target: `CLAUDE.md` (section: Cross-Version Memory)
- Action: modify
- Rationale: Solutions files are a new compounding knowledge artifact produced by `/compound` alongside the decision log. The Cross-Version Memory section should reference them so `/build` can consult proven solutions and `/review` can verify they were applied. Currently only regressions, decision-log, and research-patterns are tracked.
- Proposed edit:
  - Old text (line ~135-140):
    ```
    **Cross-Version Memory:**
    - `.claude/regressions/<agent-abbrev>.md` tracks confirmed failures
    - `.claude/decision-log/<agent-abbrev>-v<version>.md` tracks design decisions
    - `.claude/research-patterns/<domain>.md` tracks external research findings
    - `/analyze` appends failures, `/build` checks them, `/review` includes them for reviewers
    - `/compound` extracts decisions, `/research` reads patterns
    ```
  - New text:
    ```
    **Cross-Version Memory:**
    - `.claude/regressions/<agent-abbrev>.md` tracks confirmed failures
    - `.claude/decision-log/<agent-abbrev>-v<version>.md` tracks design decisions
    - `.claude/research-patterns/<domain>.md` tracks external research findings
    - `.claude/solutions/<domain>.md` tracks reusable solution patterns (e.g., subagent-coordination, deployment, data-integrity)
    - `/analyze` appends failures, `/build` checks them, `/review` includes them for reviewers
    - `/compound` extracts decisions and solutions, `/research` reads patterns and solutions
    ```

## Proposal 2: Add Subagent Coordination Patterns to MEMORY.md
- Target: `/Users/ryanhennebry/.claude/MEMORY.md` (or equivalent user-level memory)
- Action: add
- Rationale: Three subagent coordination solutions emerged from V17 analysis that apply across all agent builds, not just JSA. These are general-purpose orchestration patterns: sentinel-based completion verification, explore-then-task debugging, and batched dispatch with checkpoints. Adding them to memory ensures they are consulted in future agent designs.
- Proposed edit:
  - Add new section after existing "Job Search Agent" section:
    ```
    ## Subagent Coordination Patterns (from JSA V17)

    ### Sentinel-Based Completion Verification
    - Each subagent writes a completion marker (e.g., `<!-- BRIEF COMPLETE -->`)
    - Parent greps all expected files before proceeding
    - Lightweight alternative to status-file polling

    ### Explore-Then-Task Debugging
    - Use read-only Explore subagent for diagnosis, then write-capable Task subagent for fix
    - Preserves parent context while handling complex debugging

    ### Batched Dispatch with Checkpoints
    - Split N subagents into batches of 2, commit between batches
    - Balances parallelism with rate-limit safety
    ```

## Proposal 3: Add Graceful Degradation Principle to Agent Development
- Target: `CLAUDE.md` (new subsection under Agent Development Workflow, or as a bullet in Named Agent Pattern)
- Action: add
- Rationale: V17 decision log established graceful degradation as a design principle (CLI works without Upstash, state.json fallback for Redis). The data-integrity solution reinforces this. Future agent designs should follow this pattern: external services are always optional with local fallback paths.
- Proposed edit:
  - Add after "Named Agent Pattern" subsection:
    ```
    ### Graceful Degradation Rule
    - External services (Redis, APIs, third-party data) must have local fallback paths
    - CLI/pipeline must remain fully functional without optional infrastructure
    - Pattern: try external service -> catch -> read from local file (e.g., state.json for Redis)
    ```

## Proposal 4: Add Vercel Python Deployment Config to Solutions Reference
- Target: `.claude/solutions/deployment.md`
- Action: modify
- Rationale: The current solution entry is terse. Adding the specific config shape (functions + rewrites instead of builds) makes it immediately actionable for future Vercel Python deployments without re-discovering the fix.
- Proposed edit:
  - Old text:
    ```
    ## vercel-python-api-config
    - source: jsa-v17-analysis.md
    - pattern: Migrate from legacy Vercel builds key to functions + rewrites config, add cleanUrls for extension stripping. Resolves 404s on /api/endpoint paths for Python serverless handlers.
    - status: proposed
    ```
  - New text:
    ```
    ## vercel-python-api-config
    - source: jsa-v17-analysis.md
    - pattern: Migrate from legacy Vercel builds key to functions + rewrites config, add cleanUrls for extension stripping. Resolves 404s on /api/endpoint paths for Python serverless handlers.
    - config shape: Use `"functions": {"api/*.py": {"runtime": "@vercel/python"}}` with `"rewrites": [{"source": "/api/(.*)", "destination": "/api/$1"}]` and `"cleanUrls": true`
    - status: proposed
    ```

## Proposal 5: Add User-Facing Selection UX Standard to MEMORY.md
- Target: `/Users/ryanhennebry/.claude/MEMORY.md`
- Action: add
- Rationale: V17 decision log established a UX standard for all user-facing selection moments: unified numbered view (single ranked table, row numbers 1-N). This applies to any interactive agent, not just JSA.
- Proposed edit:
  - Add to Job Search Agent section:
    ```
    ### User-Facing Selection UX
    - All selection moments (sources, jobs, role types) use a single ranked-by-score table with row numbers 1-N
    - Present grouped tables for context, then a unified numbered list for selection
    - Consistent pattern across all pipeline stages
    ```

## Proposal 6: Add Design System Single-Source-of-Truth Rule to MEMORY.md
- Target: `/Users/ryanhennebry/.claude/MEMORY.md`
- Action: modify (update existing "Design System - Critical Lesson" section)
- Rationale: V17 decision log reinforces and extends the V12 lesson: one canonical design system file extended per surface (dashboard, email, briefs). Adds the "no blue" rule established in V17. The existing MEMORY.md entry should be updated to reflect the V17 evolution.
- Proposed edit:
  - Old text (in MEMORY.md, under Design System):
    ```
    - **ALL outputs must use a unified design system**: briefs HTML, email HTML body — same fonts, colours, layout patterns
    ```
  - New text:
    ```
    - **ALL outputs must use a unified design system**: briefs HTML, email HTML body, dashboard — same fonts, colours, layout patterns
    - **Single canonical design system file** extended with surface-specific tokens (dashboard, email, briefs) — never separate files per surface
    - **Hard rule: no blue anywhere** — all interactive elements use warm stone/ink palette
    ```

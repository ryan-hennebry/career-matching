# Decision Log: JSA V17

## Decisions

### Overall Architecture: Incremental Fixes + Additive Dashboard
- Chosen: Option A — Apply all 9 V16 fixes to a copied V16 codebase, build dashboard as a separate read-only layer synced via Git
- Rejected: Option B (Unified Architecture Redesign) — Redesigning the agent around the dashboard as primary orchestrator. Rejected because it requires building an agent runtime in serverless, is fundamentally different from V16, and carries high risk and complexity
- Rationale: V16's pipeline already works. The 9 fixes are well-scoped. The dashboard is a viewer that reads Git-committed files and does not need to control the pipeline. Preserves the working system while adding a better interface
- Context: V16 completed a full interactive run (16 jobs, 5 briefs, email sent). The chat interface where the dashboard becomes the primary orchestrator is deferred to V18

### Salary Below Minimum Handling
- Chosen: -10pt soft score penalty for jobs below user's salary minimum
- Rejected: Hard filtering (removing below-minimum jobs entirely)
- Rationale: Visible but demoted. The user decides, not the system. A below-minimum job cannot outrank salary-compliant jobs of similar quality, but remains accessible
- Context: User's salary minimum is 40K GBP. Visual tag "Below Salary Minimum" applied for transparency

### User-Facing Selection UX: Unified Numbered View
- Chosen: Single ranked-by-score table with row numbers 1-N for ALL user-facing selections (sources, jobs, role types)
- Rejected: Inconsistent selection patterns across different pipeline stages
- Rationale: Consistent UX pattern. Present grouped tables for context, then a unified numbered list for selection
- Context: V16 analysis identified inconsistent selection interfaces as an architectural failure

### Email Digest Strategy
- Chosen: Keep full rich HTML digest email AND add "View on Dashboard" links per job card
- Rejected: Replacing email with dashboard-only notifications
- Rationale: Push notification (email) AND pull interface (dashboard) serve different purposes. Email continues at V16 quality with dashboard links as enhancement
- Context: Design system is shared across email, briefs HTML, and dashboard to prevent aesthetic divergence

### Run Now Scope
- Chosen: JobSpy search only for V17
- Rejected: Full pipeline dispatch via Run Now in V17
- Rationale: Scope control. Full pipeline orchestration via dashboard is deferred to V18 (chat interface)
- Context: GitHub Actions runs jobspy_search.py, commits results, pushes to trigger Vercel redeploy

### Chat Interface
- Chosen: Deferred to V18
- Rejected: Including chat interface in V17
- Rationale: Massive additional complexity. V17 scope is already large at 8 phases
- Context: V18 is when the dashboard becomes the primary orchestrator

### Directory Strategy
- Chosen: New v17/ directory (copy of V16, then modify)
- Rejected: In-place modification of V16
- Rationale: Clean separation from V16. Preserves V16 as a working reference
- Context: Standard versioning pattern for this project

### Source Research Separation
- Chosen: Onboarding extracts profile only (CV, roles, constraints, delivery). Source research is a separate explicit step
- Rejected: Combined onboarding + source discovery (V16 approach)
- Rationale: Faster onboarding, no duplication. The deep source-researcher agent is the only source discovery path
- Context: V16 analysis identified duplicate source research during onboarding as a failure

### Design System Governance
- Chosen: Single canonical jsa-design-system.md file extended with dashboard tokens
- Rejected: Separate design files per output surface (email, briefs, dashboard)
- Rationale: One source of truth prevents drift. Hard rule: no blue anywhere — all interactive elements use warm stone/ink palette
- Context: Previous version failures showed aesthetic incoherence when subagents each picked their own styles

### Git Push Timing
- Chosen: Incremental commit+push after each pipeline stage
- Rejected: Single push at pipeline completion
- Rationale: Dashboard shows incremental progress. Pipeline progress indicator handles the partial-data state
- Context: Vercel auto-deploys in ~30s after push, so incremental pushes give near-real-time dashboard updates

### Rejection Sync Between Dashboard and CLI
- Chosen: CLI optionally reads Upstash rejections before brief generation, with graceful degradation when credentials are absent
- Rejected: Tight coupling requiring Upstash credentials for CLI to function
- Rationale: Graceful degradation. CLI remains fully functional without dashboard infrastructure
- Context: Upstash stores user actions (accept/reject/brief_requested). CLI reads these optionally to skip rejected jobs

### Brief Rendering
- Chosen: Individual markdown briefs served via /api/brief endpoint
- Rejected: Bundled brief rendering or full-page brief views
- Rationale: Simpler routing, better detail views. Each brief is an independent markdown file rendered with design system styling
- Context: Briefs are Git-committed markdown files in output/briefs/

### State Sync Mechanism
- Chosen: Split — Git for job data and pipeline state, Upstash Redis for user actions only
- Rejected: Single state store for everything
- Rationale: Different data serves different purposes. Job data is structured files that benefit from Git versioning. User actions are ephemeral key-value pairs suited to Redis. No sync problem because they serve orthogonal concerns
- Context: Dashboard reads both sources and merges them to derive pipeline stage

### PAT Scope for GitHub Actions
- Chosen: GITHUB_TOKEN for commits + separate fine-grained PAT with minimal scope (actions:write only)
- Rejected: Single broad-scope token
- Rationale: Minimal scope per token reduces blast radius of credential compromise
- Context: GitHub Actions workflow dispatch requires actions:write. Commit operations use the built-in GITHUB_TOKEN

### Target Device
- Chosen: Desktop primary with basic 768px responsive breakpoint
- Rejected: Mobile-first or full responsive design
- Rationale: Personal tool used primarily on desktop. Basic responsiveness is sufficient
- Context: API cost also declared as not a concern since this is a personal tool

### Domain
- Chosen: Default vercel.app subdomain
- Rejected: Custom domain
- Rationale: Zero DNS configuration work. Acceptable for personal tool
- Context: Minimizing infrastructure overhead

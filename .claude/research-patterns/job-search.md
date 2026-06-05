# Research Patterns: Job Search Automation

### python-jobspy
- Pattern: Aggregator scraping LinkedIn/Indeed/Glassdoor/Google/ZipRecruiter concurrently
- Constraint: Python >= 3.10, numpy >= 1.26.0. No formal docs beyond GitHub README.
- Constraint: Scrapes HTML — any target site redesign breaks it silently. No deprecation policy.
- Constraint: Does not cover crypto/Web3-specific boards

### resend-python
- Pattern: Attachments as `{"filename": "f.pdf", "content": list(pdf_bytes), "content_type": "application/pdf"}`
- Constraint: Content must be `list(bytes)` (list of integers), not raw bytes
- Pattern: Tags for categorization: `[{"name": "type", "value": "digest"}]`
- Pattern: Post-send attachment retrieval via `Emails.Attachments.list(email_id)`

### upstash-redis-python
- Pattern: HTTP-based (REST API), no persistent TCP connections — ideal for serverless
- Pattern: Init via `Redis.from_env()` reads UPSTASH_REDIS_REST_URL + TOKEN
- Pattern: Pipelines `redis.pipeline()` for batched non-atomic, `redis.multi()` for atomic
- Pattern: JSON commands `redis.json.set()`, `redis.json.get()` for complex state
- Constraint: `rest_encoding="base64"` default — set to `None` for JSON perf

### claude-code-subagents
- Pattern: Named agents with YAML frontmatter in `.claude/agents/*.md`
- Pattern: Skills preloaded via `skills:` field
- Pattern: Status file protocol for completion signaling
- Constraint: No peer-to-peer messaging — results only flow back to parent

### crypto-web3-job-boards
- Accessible: Web3.Career (best), CryptocurrencyJobs.co, BeInCrypto Jobs, AI Jobs
- Blocked: CryptoJobsList, Wellfound, startup.jobs, TopStartups.io, Welcome to the Jungle
- Via aggregator: LinkedIn/Indeed/Glassdoor (mainstream roles, poor crypto/AI match)
- Gap: No crypto/Web3 job board APIs — all are scrape-only

### python-jobspy-updates (2026-02)
- Version: v1.1.82 (July 2025). Python >=3.10, <4.0. Python 3.13 supported.
- New boards: Bayt, Naukri added since last documented
- Community: JobSpy MCP Server (FastMCP-based) wraps jobspy behind MCP protocol
- Community: Dockerized JobSpy API (rainmanjam/jobspy-api) — FastAPI with auth/rate-limiting

### resend-updates (2026-02)
- SDK 2.0 stable since June 2024, no further breaking changes
- Batch Idempotency Keys (June 2025) — prevents duplicate sends on retry
- Automatic Plain Text generation (Aug 2025) — no manual text fallbacks needed
- Broadcast API (Feb 2026) — single-API-call batch sends
- CID image embedding (Aug 2025) — inline images in HTML emails

### claude-code-action (2026-02)
- v1.0 (Aug 2025) — native GitHub Action (`anthropics/claude-code-action@v1`)
- Replaces `claude --print --dangerously-skip-permissions` for scheduled runs
- Single `prompt` input + `claude_args` for CLI options
- Auto-detects automation mode on schedule triggers (no interactive prompts)
- Auth: ANTHROPIC_API_KEY secret, or Bedrock/Vertex/Foundry
- Breaking from v0.x — migration guide available

### ai-job-search-competitive (2026-02)
- Consumer SaaS: Sonara, LazyApply, Jobright, LoopCV, AIApply, JobHire.AI
- All optimize for auto-apply volume (50+ apps/day), ATS-optimized resumes
- None target startup generalist niche or crypto/Web3
- None provide intelligence/briefing layer (company analysis, scoring, strategic digest)
- JSA moat: curation quality over application volume

### claude-agent-sdk-updates (2026-02-23)
- `background: true` flag in agent YAML frontmatter — declares agent as always-background, removing per-dispatch `run_in_background=true`
- Task tool now returns token count, tool uses, and duration metrics in results
- Claude Agent SDK (renamed from Claude Code SDK) has documented subagent and hooks support

### resend-updates-late-feb (2026-02-23)
- Broadcast API single-request send (Feb 12, 2026) — create + send in one call
- Improved log search with status filters + actionable error guidance (Feb 2, 2026)

### vercel-updates (2026-02-23)
- Vercel Python SDK in beta (`pip install vercel`) — Sandbox, Blob, Runtime Cache API
- No breaking changes to existing api/ function patterns or Python 3.10+ floor

### rate-limit-recovery (2026-02-24)
- Pattern: Exponential backoff with jitter (250-750ms initial, ×2 factor), circuit breakers (trip at N consecutive failures)
- Pattern: Pre-dispatch quota check — estimate total API calls, validate against rate limits before dispatching
- Pattern: LangGraph checkpoint-based recovery — state snapshots at each step, resume from exact execution point
- Constraint: No established pattern for graceful stale-data detection during rate limits — most systems fail or retry

### multi-channel-search-orchestration (2026-02-24)
- Pattern: Channel registry with health checks (last_check, status, next_retry_time) — mandatory dispatch with loud failure on incomplete
- Pattern: MuleSoft Gateway Aggregation — dispatch to multiple backends in parallel, aggregate, validate completeness
- Pattern: Per-channel metrics (queries executed, results returned, dedup rate) at end of each run
- Constraint: No precedent for run-scoped search focus (narrowing channels per user context each run)

### context-aware-dedup (2026-02-24)
- Pattern: Run-scoped partition with run_id metadata — dedup only within active run's partitions
- Pattern: Pivot-detection on config changes — pre-archive old directories before new search dispatch
- Pattern: Scope flag (`--role-types`) to limit dedup to active role types, ignoring stale directories

### session-resume-guards (2026-02-24)
- Pattern: LangGraph Checkpointer — state snapshots at each step with thread_id, resume from exact node
- Pattern: Idempotency keys per subagent action — skip already-completed actions on resume
- Pattern: State versioning with schema migration path
- Constraint: LangGraph assumes linear workflow; parallel multi-channel dispatch needs custom checkpoint merging

### claude-code-agent-teams (2026-02-25)
- Pattern: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` enables multi-instance coordination — one lead, N teammates with inbox-based messaging
- Pattern: Background agents now prompt for tool permissions before launch (not mid-execution)
- Pattern: Ctrl+B backgrounding — send running task to background mid-execution
- Pattern: Tiered permission system (Allow/Ask/Deny) configurable per-tool in settings.local.json

### pydantic-v2-pipeline-validation (2026-02-25)
- Pattern: Pydantic v2.11 with Rust-backed validation (5-50x over v1)
- Pattern: `TypeAdapter` reuse to avoid re-creating validators per call
- Pattern: Strict unions with discriminators for polymorphic JSON schemas (e.g., multiple score formats)
- Pattern: `model_validate_json()` for direct JSON-to-model parsing (skips Python dict intermediary)
- Pattern: `@model_validator` for cross-field invariants, `@field_validator(mode="before")` for normalizing messy scraper output
- Pattern: Pydantic Settings for config + per-stage models for data contracts

### structural-enforcement-gates (2026-02-25)
- Pattern: Pre-execution assertion gates — validate preconditions before each pipeline stage, fail-fast
- Pattern: Machine-speed circuit breakers for autonomous agents (detect cascading failures: cost runaway, empty results, stale data)
- Pattern: Configurable thresholds (>3 consecutive failures = circuit open, hard time/cost budget stop)
- Pattern: Runtime invariant monitoring during execution (job count non-zero after dedup, brief count matches verified, email payload non-empty)

### resend-updates-late-feb-2 (2026-02-25)
- Pattern: Self-hosted webhook storage (Jan 26, 2026) — store all Resend webhook events in own DB
- Pattern: Bulk dashboard actions (Jan 15, 2026) — batch operations
- Pattern: Email scheduling up to 30 days in advance via Broadcasts or API
- Pattern: Suppressed status visibility (Jan 8, 2026) — new status type for tracking

### greenhouse-harvest-api-deprecation (2026-03-23)
- Constraint: Greenhouse Harvest API v1 and v2 deprecated after August 31, 2026 — any validation using Harvest endpoints must migrate
- Pattern: Greenhouse public boards API (`GET https://api.greenhouse.io/v1/boards/{clientname}/jobs?content=true`) remains available, no auth required
- Note: JSA currently uses public boards API for validation, not Harvest — no immediate action needed but monitor

### ashby-api-quirks (2026-03-23)
- Constraint: Ashby API errors return HTTP 200 with `success: false` in body — URL validation must check response body, not just status codes
- Pattern: HTTP Basic Auth required for Ashby API access
- Note: Multiple Ashby board slugs can exist per company (e.g., `jack-and-jill` vs `jack-jill-external-ats`) — must cross-reference

### ats-unified-apis (2026-03-23)
- Pattern: Unified API services (unified.to) emerging for multi-ATS integration — single SDK for Greenhouse, Lever, Ashby, Workable
- Pattern: Apify actors available for Greenhouse/Lever/Ashby scraping as alternative to direct API
- Note: JSA uses direct per-vendor integration; unified API would reduce maintenance but adds dependency

### python-jobspy-disambiguation
- Note: Two distinct "jobspy" packages on PyPI — use Cullen Watson's (github.com/cullenwatson/jobspy)

### resend-error-codes
- Constraint: 401=invalid key, 422=unverified domain

### job-board-scraping-rate-limiting
- Pattern: Randomized delays (1-5s), proxy rotation for high volume, exponential backoff on 429
- Constraint: Job boards tolerate scraping for visibility but enforce load limits
- Note: Many Indeed URLs return 403 on WebFetch; use aggregator description data instead

### claude-code-subagent-limits
- Constraint: 3-4 subagents max recommended to avoid orchestration overhead
- Pattern: Background dispatch for long-running subagent tasks

### eu-ai-act-awareness
- Pattern: "Reasoning Log" required for candidate-ranking AI systems from Aug 2, 2026
- Constraint: Not directly applicable to job-seeker tooling, but relevant if scoring used by recruiters

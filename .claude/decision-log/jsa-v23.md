# Decision Log: JSA V23

## D1: Three-Layer Architecture (Scripts, Orchestration+Config, Validation)
- Chosen: Option C — Three-Layer (Scripts -> Orchestration+Config -> Validation). Layer 1: manage_state.py new subcommands + tests. Layer 2: CLAUDE.md + orchestration.md + agent frontmatter + context.md. Layer 3: preflight.sh additions + integration validation.
- Rejected: Option A (Single Phase) — mixes code creation with config edits, making failure isolation impossible. Option B (Two-Layer) — conflates validation code with orchestration text edits, reducing bisectability.
- Rationale: Matches the V21 three-layer pattern that achieved 22/22 step completion. V23's scope mixes three distinct artifact types that benefit from layer isolation.
- Context: V22 had 8 remaining failures. V21's three-layer pattern is the proven precedent for mixed-artifact-type work.

## D2: Model Tiering Assignment (Haiku/Sonnet/Opus)
- Chosen: Tiered model assignment — Opus for parent only, Sonnet for brief-generator/digest-email/briefs-html/onboarding, Haiku for search-verify/source-researcher.
- Rejected: `model: inherit` (all Opus) — costs $4+/run, making daily use cost-prohibitive.
- Rationale: Search-verify does mechanical work that doesn't require Opus. Brief generation needs good writing but not Opus reasoning. Target: <$1.00/run.
- Context: V22 cost $4.09 for 80 turns and didn't complete. Cost ceiling makes daily scheduled runs impractical.

## D3: Reverse Hard Constraint 1 — Allow Model Passing to Task Tool
- Chosen: Replace "Never pass model: to Task tool" with "Pass model: matching the agent's designated tier."
- Rejected: Keeping HC1 — prevents parent from selecting the right model tier, blocking cost reduction.
- Rationale: HC1 was a safety constraint. With explicit model tiering in agent frontmatter and preflight validation, the constraint is replaced by a more precise enforcement mechanism.
- Context: HC1 directly blocked cost reduction. Replacement couples model selection with agent frontmatter (source of truth) and preflight validation (enforcement).

## D4: Context-Aware Dedup via --role-types Flag
- Chosen: Add `--role-types` flag to dedup subcommand. Only processes directories matching specified slugs. Ignores all others.
- Rejected: Pre-dedup cleanup (archiving old directories before search) — less targeted.
- Rationale: V22's dedup operated on ALL subdirectories with no context awareness. When user changed focus, old directories caused incorrect archival.
- Context: Critical (C-level) failure from V22. Fix must adapt to user's current context without manual cleanup.

## D5: 5-Channel Search as Fixed Infrastructure
- Chosen: Five mandatory search channels per run: direct career pages, industry job boards, JobSpy aggregator, niche newsletters, web search discovery. Each dispatches as a separate subagent.
- Rejected: V22's ad-hoc approach — defaulted to only direct career pages, requiring manual user intervention.
- Rationale: Search breadth determines everything downstream. Fixed channel infrastructure ensures breadth; parameterized content ensures relevance.
- Context: Critical (C-level) failure from V22. Design adds `verify-channels-dispatched` as a code-enforced gate.

## D6: Post-Batch Commit Gate via verify-batch-committed
- Chosen: New `verify-batch-committed` subcommand. Runs `git status --porcelain output/verified/` between batches. Exits non-zero if uncommitted files exist.
- Rejected: Relying on orchestration text instructions alone (V22 approach — advisory, not enforced).
- Rationale: V22's post-batch commit requirement was not code-enforced, leading to uncommitted intermediate state.
- Context: Critical failure from V22. Moving from advisory to executable verification follows V22 compound insight.

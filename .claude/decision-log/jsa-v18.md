# Decision Log: JSA V18

## Decisions

### Phase Granularity: Three-Phase Sequential vs Fewer Phases
- **Chosen:** Three-Phase Sequential (Infrastructure -> Backend -> Frontend)
- **Rejected:**
  - *Two-Phase (All Fixes -> Visual Polish):* Mixes infrastructure (GH Actions, YAML, file paths) and state logic (Python, JSON) in the same phase, creating entangled failure modes.
  - *Single Unified Phase:* Blast radius too large — 15+ files across infrastructure, backend, and frontend with no failure isolation.
- **Rationale:** Infrastructure failures and state logic failures have completely different debugging workflows. V17 analysis showed debugging was a pain point. Ordered by dependency: infrastructure must work before backend is testable in CI, backend state must be correct before dashboard displays it.
- **Context:** V17 post-build analysis exposed 11 failures across three distinct domains. All 8 fixes are implementation-level (no architectural changes).

### Prototyping: Skipped
- **Chosen:** No prototyping
- **Rejected:** Running prototypes for any of the three phases
- **Rationale:** All changes use existing technologies (Python CLI, Vercel serverless, vanilla CSS/JS) already proven in V17. No new libraries, no concurrent state, no unverifiable external APIs — none of the prototyping triggers were met.
- **Context:** Prototyping criteria require novel technology, complex concurrency, or unverifiable external dependencies.

### Pre-flight Validation: Script vs Inline Bash
- **Chosen:** New `scripts/preflight.sh` monolithic script (with acknowledged risk)
- **Rejected:** Folding checks directly into CLAUDE.md startup as individual bash commands
- **Rationale:** Centralized script is callable from both CLAUDE.md startup and GH Actions workflow steps, avoiding duplication. Least confident decision — Vercel deployment URLs vary between environments and secrets cannot be checked locally.
- **Context:** Plan must resolve the scope split: local-only checks (file existence, syntax) vs CI-only checks (API health, secrets). Fallback: inline bash commands if script proves brittle.

### Dedup Collision Key: CLI Subcommand vs Inline Python
- **Chosen:** `manage_state.py dedup` CLI subcommand with directory-based input
- **Rejected:** Inline Python dedup logic in parent orchestrator (V17 approach)
- **Rationale:** V17 used inline Python which violates "no inline Python for state" constraint. CLI subcommand keeps state mutations in canonical state management tool and is independently testable.
- **Context:** Risk: two different jobs at different companies with same slug could false-dedup. Plan must define exact collision key (filename + source domain or job URL hash).

### Dashboard Design Language: Warm Stone/Ink Palette
- **Chosen:** Left-edge score bars with tier-specific colors, stacked KPI stats, borders-only depth, warm stone/ink palette, 960px max-width
- **Rejected:** Blue in palette; box shadows on cards
- **Rationale:** Left-edge score bar communicates job quality at a glance. Borders-only depth and warm palette maintain clean, professional aesthetic from V17's design system.
- **Context:** 10 CSS/JS/HTML enhancements. All new classes use unique prefixes to avoid CSS specificity conflicts with existing V17 styles.

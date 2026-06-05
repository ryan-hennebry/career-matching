---
title: "Strict Evidence-Gated Re-Rank \u2192 v4"
type: session
date: '2026-06-03'
time: 08:51:28
session: 4c5578d1-02d7-4745-a03e-45bf370769bc
workflow: strict-evidence-gated-re-rank-v4
---

# Strict Evidence-Gated Re-Rank → v4

## Context

The current ranked list (`/tmp/jsa-fresh-2026-06-01/_FINAL_RANKED_v3_2026-06-03.md`, 42 active roles) was built optimizing for **title-to-identity fit** and **company signal**. Its CV-match scores are holistic estimates — they do **not strictly gate** on whether Ryan actually clears the hard requirements a hiring manager screens on. The result: roles Ryan can't realistically pass (Lovable at 50% CV-match, Decagon's "3+ yr implementations" floor, several FDE roles with production-coding requirements) still sit in "Apply Immediately" / "Apply This Week" tiers.

In a tough market, applying to roles you'll be auto-screened-out of wastes the limited effort that should go toward roles you can actually land. **Goal:** re-rank the ~40 apply-tier roles strictly against Ryan's real CV, where subagents read *every word* of each live job description and cross-reference reputable sources on what hiring managers truly screen for — then gate out roles he doesn't clear, keeping only genuinely-attainable roles in apply tiers.

**Decisions confirmed with user:**
1. **Strict gate** — any unambiguous hard requirement Ryan doesn't meet drops the role to a separate "Gated — likely auto-rejected" tier, with the exact disqualifying line quoted.
2. **JD + reputable research** — read every word of the live JD AND pull reputable external sources on per-archetype hiring screens.
3. **Apply tiers only** (~40 roles): Apply Immediately + Apply This Week + Apply If Time. Skip cold-outreach + do-not-apply.
4. **New v4 file** — leave v3 intact.

## Ryan's strict ground-truth (the gating baseline)

- 2:1 Business Management, Leeds (2017). **No CS/STEM degree, no MSc.**
- First employee at Minima (Mar 2019–Aug 2023, seed→Series A, 1→30): Founder's Associate (ops, investor comms, pitch decks, seed support) → Community Manager (Discord/Telegram 100k, node-runner onboarding 50k/75k nodes) → Marketing Manager (GTM: $4.5m presale on $300k = 15× ROI, positioning, events feeding $6.5m Series A, lifecycle, content engine 30k blog/5k YT/40k X, PR 2m views).
- Earlier: Content Marketer (BBOD, 20k users); Data Analyst (Amazon Alexa, 98% query success).
- Aug 2023–present: career break + ~1 yr building Claude Code agents (competitor-intel, growth-experiments).
- **Hard truths for gating:** NO production software engineering. NO formal "implementations consultant" title. NO quota-carrying/CSM sales. NO direct reports managed. NO government procurement. NO financial modelling. **Strongest shapes:** Founder's Associate / Operator / Generalist / GTM-Marketing / Community. **Can credibly claim:** scrappy technical literacy, AI-agent building, no-code/low-code, GTM, fundraising support, community.

## Gating Rubric

**Hard disqualifier → GATED tier** (role fails if JD states, in *required* language, any of):
- Coding-core required ("Python/SQL/TS **required**", "ship production code", "strong SWE background required"). — *Not a gate:* "Python a plus", "technical literacy", "no-code/low-code".
- Degree mandate Ryan lacks ("CS/STEM degree required", "MSc/PhD required"). — *Not a gate:* "degree preferred", "any discipline", "or equivalent experience".
- Years floor he can't meet even reframed: **floor ≥5 yrs, OR any floor in a domain Minima never touched** (formal implementations, quota sales, financial modelling, gov procurement) = HARD_FAIL. Floor ≤4 yrs in a Minima-touched domain (ops, GTM, community, fundraising-support) = reframeable, not gated.
- Formal function never held, stated as required: implementations-consultant years, quota/closing record, people-management, gov procurement, financial modelling.
- Geo/work-auth hard gate: must-be-in-SF/NYC/Stockholm/Milan/Copenhagen, US-citizen/US-auth required, active security clearance. (Verify suspected scraper artefacts like Encord's US-citizen string before gating.)

**Soft/reframeable gap → stays in Apply/Stretch, lowers score, gets reframe note:** "fast-paced startup" (clears outright), "customer-facing" (reframe via community/investor comms), "enterprise SaaS deployment" with no years floor (soft gap → Stretch), AI-tools-daily (clears), marketing/GTM/community/fundraising (clears), domain adjacency gaps with no stated domain requirement (minor penalty).

**Decision tree per role:** fetch JD → extract every requirement, classify required/preferred/nice-to-have by JD's own language → map required items to gate dimensions → **any required HARD_FAIL? → GATED** (record verbatim disqualifier quote); else count soft gaps → 0–1 soft gaps + strong core-function clearing quote = **APPLY**; 2+ soft gaps or reframe-dependent core = **STRETCH** → recompute scores. JD inaccessible + unconfirmable hard gate = **NEEDS-VERIFICATION** (never silently dropped, never scored clean).

**Re-score:** `cv_match_strict` = (required+preferred items CLEAR, reframeable soft gap = 0.5) / total × 100 (stricter than v3). `composite_v4` keeps v3's six factors but recomputes **fit** from the gate result (Apply-clean = high; Stretch = capped; reframe-heavy = penalised). Order within tier by composite_v4 desc, then cv_match_strict, then recency.

## Orchestration

Parent **orchestrates only** — all JD reading, research, scoring, and the single file write are delegated to **Opus** subagents (project rule + user feedback). Sequence:

**Phase 0 (parent):** Build a canonical role manifest from v3 — numbered list of every apply-tier role with company, title, archetype tag (O/F/I/C/M/B), URL/ATS, v3 row. Confirm exact count N. Partition into 5 batches **grouped by ATS platform** (not tier) so each batch faces a consistent fetch strategy. Each batch references roles by manifest ID — nothing silently dropped or double-counted.

**Phase 1 (parallel) — 6 archetype research subagents**, one each for: FDE/Deployment, Founder's-Associate/Operator, Implementation/Delivery Manager, Chief of Staff, Marketing/Growth, AI Builder. Each pulls reputable sources on the *real* hard screens for that archetype and whether an operator background substitutes. Named sources: Palantir's own FDE/Deployment-Strategist definitions + eng blog, Anthropic Applied-AI role posts, YC "Work at a Startup" / founder's-associate guidance, EF talent profiles, First Round Review / Lenny's, chiefofstaff.network, MKT1 / Elena Verna for growth, n8n/Hyde own posts + "AI Engineer" writing for builder. Output: ≤1500-word cited dossier each (quotes ≤15 words, attributed). Dossiers feed the JD readers so gate calls cite both JD and archetype norm.

**Phase 2 (parallel, overlaps Phase 1) — 5 JD-reader subagents, ~8 roles each.** Each reads **every word** of its assigned live JDs via a fetch-escalation ladder and applies the gating decision tree, returning a JSON array (schema below).

Fetch-escalation ladder (handles JS-rendered ATS — the main execution risk):
1. **WebFetch** first (SSR sites, Greenhouse, YC, many LinkedIn views).
2. On cross-host redirect → re-call WebFetch with the redirect URL.
3. On JS-shell/empty/403 (Ashby UUID pages, Lever, Notion, auth-walled LinkedIn) → **Chrome MCP**: `tabs_create_mcp` (own tab) → `navigate` → `get_page_text` on the rendered DOM.
4. Ashby board with no UUID (Light Inc LANDING) → navigate to org board root, `get_page_text` to enumerate, navigate into the target, `get_page_text` detail.
5. Still blocked → **WebSearch** for a corroborated mirror (Built In London, Glassdoor); mark `source: mirror` (lower confidence).
6. Unconfirmable hard requirement → `UNVERIFIED`, never fabricated, never scored clean.

Browser-contention mitigation: each subagent uses its **own tab** and closes it. If unstable, parent serialises the two Ashby-heavy batches while WebFetch-friendly batches run parallel.

**Phase 3 (sequential, last) — 1 synthesis subagent.** Inputs: all 5 JSON arrays + 6 dossiers + reads v3 for the diff. **Writes the only file:** `_FINAL_RANKED_v4_2026-06-03.md`. Pulls verbatim quotes straight from JSON (never re-typed).

**Phase 4 (parent) — verification** (read-only; re-dispatch on failure).

### Role-eval JSON schema (per role)

Extends the existing `_deep_check_batch*.json` convention. Key fields: `manifest_id, company, title, archetype, v3_tier/rank/composite/cv_match, direct_url, jd_access (OK|MIRROR|PARTIAL|BLOCKED), jd_access_rung, requirements[] {text_verbatim, jd_classification, gate_dimension, ryan_status (CLEAR|HARD_FAIL|SOFT_GAP|UNVERIFIED), ryan_evidence_verbatim, reframeable, reframe_note}, hard_gates[] {requirement_verbatim, gate_dimension, verdict, disqualifier_quote}, clearing_evidence[] {requirement_verbatim, clearing_quote_jd, ryan_evidence}, soft_gaps[], gate_outcome (APPLY|STRETCH|GATED|UNVERIFIED-HOLD), gated_reason_quote, cv_match_pct_strict, composite_v4, score_breakdown, research_alignment_note, changed_vs_v3, key_risk, recommended_action`. **Mandatory invariants:** every GATED role has non-null `disqualifier_quote`; every APPLY/STRETCH role has non-empty `clearing_evidence`.

## Output file structure (`_FINAL_RANKED_v4_2026-06-03.md`)

- **Header + count reconciliation vs v3** (roles re-evaluated N; Apply X / Stretch Y / Gated Z / Needs-Verification W; net promoted/demoted/newly-gated).
- **TIER 1 — APPLY** (clears all hard gates): per-role row with composite_v4, cv_match_strict, **verbatim clearing-evidence quote → Ryan proof**, archetype-research note, changed-vs-v3, action.
- **TIER 2 — STRETCH** (clears gates, weak/reframe-dependent): same + soft-gaps & reframe strategy.
- **TIER 3 — GATED — LIKELY AUTO-REJECTED**: company, title, **verbatim disqualifier quote**, gate dimension, could-be-unlocked-by, changed-vs-v3.
- **APPENDIX A — Needs Manual Verification** (JD blocked/unconfirmed): what to confirm, provisional lean.
- **APPENDIX B — Changed-vs-v3 ledger**: promoted / demoted / newly-gated (with the exact gating line) / score deltas.
- **APPENDIX C — Per-archetype hiring-screen summary** (from dossiers, cited).

## Critical files

- `/tmp/jsa-fresh-2026-06-01/_FINAL_RANKED_v3_2026-06-03.md` — role manifest + v3 baseline to diff (read-only).
- `/Users/ryanhennebry/Downloads/Ryan Hennebry – CV – Neutreeno (1).pdf` — strict CV ground-truth.
- `/tmp/jsa-fresh-2026-06-01/_deep_check_batch1.json` — existing JSON convention the role-eval output extends.
- `/tmp/jsa-fresh-2026-06-01/_FINAL_RANKED_v4_2026-06-03.md` — **NEW** output, written only by the synthesis subagent.

## Verification (parent, after synthesis)

1. **Count reconciliation:** Apply + Stretch + Gated + Needs-Verification = N; grep every manifest role → appears exactly once in exactly one tier (no silent drop).
2. **Apply/Stretch evidence:** every such row carries a quoted clearing line — flag empties.
3. **Gated disqualifier:** every Gated row carries a non-empty verbatim disqualifier quote.
4. **No-promotion-of-gated / no-silent-drop:** any v3-apply role now absent must appear in Gated or Needs-Verification with a reason; no role both Gated and in an apply tier.
5. **Changed-vs-v3 completeness:** every role has a non-empty change verdict.
6. **Access honesty:** every BLOCKED/MIRROR role visibly flagged; unconfirmed hard gates routed to Needs-Verification.
7. **Quote provenance spot-check:** parent re-fetches 3–4 random disqualifier quotes via WebFetch/Chrome to confirm they exist verbatim in the live JD (guards against hallucination on the load-bearing field).

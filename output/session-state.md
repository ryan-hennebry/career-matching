# Session State

## Run: 2026-06-08

**Mode:** Interactive (deep search, all subagents Opus)
**Profile updated this run:** Added AI Operations, AI Product Associate/Builder, Founding Generalist; removed Marketing Associate + Community Manager; salary £40k→£50k; removed "Chief" title exclusion; company scope = AI agent startups (top) → any AI company → AI-native operators.

**Active role types (5):**
- founder-s-associate-priority
- founding-operator-priority
- founding-generalist-priority
- ai-operations-ai-ops
- ai-product-associate-ai-product-builder

## Active Tasks

- a5e9581f3933b0da1: search-verify direct-career-pages (dispatched 2026-06-08, Opus, background)
- ae5018e87bc0f1d93: search-verify industry-job-boards (dispatched 2026-06-08, Opus, background)
- a4f77062483ef70e3: search-verify jobspy-aggregator (dispatched 2026-06-08, Opus, background)
- a139b4ab4293cea87: search-verify niche-newsletters (dispatched 2026-06-08, Opus, background)
- a901ef5c5177a046b: search-verify web-search-discovery (dispatched 2026-06-08, Opus, background)

All 5 channels cover all 5 role types. Sentinels in output/.channels/{channel}.done.

### Wave 2 (high-leverage sources + deep jobspy) — dispatched 2026-06-08
- ac40b6c463d745a54: curated-newsletters-wave2 (Lenny's/MKT1/Next Play/generalist.world/On Deck/Pallet)
- a0f3de1c3df872877: vc-talent-boards-wave2 (a16z/Index/Balderton/Atomico/Air Street/EF/Seedcamp/Getro)
- abc0267ca9b75ce6c: ats-sweep-wave2 (Ashby/Greenhouse/Lever/Workable/Pinpoint + YC WaaS)
- a4e8ab49278081810: jobspy-deep-wave2 (broad query matrix, raised counts, direct-URL resolution)
All dedup against the 12 current finds + output/_prior_runs_dedup.md (user's prior sheet).

## Search Progress

| Role Type | Status |
|-----------|--------|
| founder-s-associate-priority | pending |
| founding-operator-priority | pending |
| founding-generalist-priority | pending |
| ai-operations-ai-ops | pending |
| ai-product-associate-ai-product-builder | pending |

## Notes

- This is effectively a first run (state.json last_run_date was null).
- Fixed missing .claude/settings.local.json on startup (preflight CRITICAL).
- Attached "Competitor Intel Brief – Mozart AI.pdf" is NOT a CV — it's a competitor brief Ryan authored. Using existing context.md profile, not parsing it.

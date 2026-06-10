# Session State

## Run: 2026-06-10 (DELTA SWEEP)

**Mode:** Orchestrate-only delta sweep. 7 parallel channels + reverify-open + fresh finds.
**Primary lens:** operator (callback_op); secondary 8-factor callback_v3. Bias to recency (roles posted since 8 June).
**Applied (exclude):** Ankar FA, Alaro, Neutreeno, Mozart AI, Moss, Terra API, Installio.
**Closed (exclude):** Tilt, Assuric, Jack & Jill, Deel GTM.
**Reverify open:** Geordie AI, Dwelly x2, Corgi, Light, Togather, StudioB.
**Dedup against:** state.json + output/_prior_runs_dedup.md + all output/deep/*.json (→ output/_delta_exclusion.json).

### Delta dispatches:
- a9520150ccba17f67: build dedup exclusion set (output/_delta_exclusion.json) ✅ 93 pairs / 70 cos
- a2ce87cac4d16acc5: reverify-open (Geordie, Dwelly x2, Corgi, Light, Togather, StudioB)
- a175b5a401ff80765: delta-direct-careers
- a4e6b1609e07ce31b: delta-industry-boards
- a4ed6fa11bd628f16: delta-jobspy
- a5a176d19eb6ac312: delta-newsletters
- a0082ad40cc280390: delta-websearch
- ac815a823dddea07d: delta-ats-sweep
- aecfb3552b572b871: delta-vc-boards
All channels operator-lens, dedup vs _delta_exclusion.json, bias to roles posted since 2026-06-08.
Net-new written to output/deep/{slug}.json with callback_op + callback_v3 + source:"delta-*".
After all return: merge, stress-test anything top-10, present ranked + next-5, update state.json, commit.

### DELTA RESULT (2026-06-10): 5 net-new (Checkout.com 61, Lawhive 61, Ramp 59, Reflection AI 55, Tracer intern 54) — NONE beat carried leaders.
Top board unchanged: Geordie AI 80 > Dwelly Ops 78 > Gradient 77 > Dwelly Integration 74 > Corgi 65 > Light 63 > Checkout.com 61.
All 7 leaders reverified OPEN. CV (Ryan Hennebry – CV.pdf) confirmed identical to v2 — no rescore.
Deep FA sweep: 0 net-new UK FA (archetype exhausted; big AI cos run FA from US HQ; UK FA seats captured or closed). Letty closed (re-check if relists).
Recommended next-5 (operator-only): Geordie AI, Dwelly Ops, Gradient Labs, Specter, governr. #6 = Corgi.
Watch-list: Letty, Airspeed/Glyphic, Paid AI, Kohort, Inherent, CodeWords, Scope AI.
Output: output/_delta_final_ranking.json. Applied now = 7. Closed = Tilt/Assuric/Jack&Jill/Deel/Ankar-GTM.

---

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

### Prior-roles CV interview-match — dispatched 2026-06-08
Matching all 54 prior-sheet roles against real CV (output/_cv_parsed.json). Output → output/verified-prior/.
- acbc42592d2effb86: slice 1 (Metaview..Capital on Tap)
- abdbbfe5ab8947755: slice 2 (Specter..Lovable)
- a6d2d94af9042eac1: slice 3 (Distyl..Installo)
- aa9cf9eeaf99551e1: slice 4 (Euphoric..Stitch Health)
- a59bf9680301a1132: slice 5 (Natter..Apron)
- a3ebd6d19e8a04c7f: slice 6 (Dayjob..Marloo, marketing/growth)
Each: find live url → confirm open/closed → pull reqs → CV match → interview_likelihood.
After all 6: merge with the 20 new roles, rank all by interview_likelihood, present with direct links.

### DEEP multi-factor callback analysis — dispatched 2026-06-09
User applied to Ankar (FA) + Alaro — excluded. CV v2 parsed (output/_cv_parsed_v2.json, ~identical to baseline).
Analyzing 33 candidates (likelihood>=50) on 6 factors: requirements(30) / competition(20) / screening(15) / spike(20) / warmpath(8) / conversion(7) → callback_likelihood. Output → output/deep/.
- afde2ea330065efe2: batch1 (Conduct,Corgi Ops,Moss,ElevenLabs Growth,Capital on Tap,Gradient Labs)
- a16a773b855e25d76: batch2 (Sequence,Deel,Specter,Wing,Magentic,Neutreeno)
- a81a3b403310cee5b: batch3 (ivee,Jack&Jill,Marloo,n8n,Assuric,Dayjob)
- a9179cbbb07defddd: batch4 (Decagon,Mozart,StudioB,ElevenLabs DS,Scope,Terra API)
- aad84eb4be040face: batch5 (Ankar GTM,Seamflow,Siena,32Co,Tilt,governr)
- a1a72ae0264fcc394: batch6 (HappyRobot,Installio,Lovable + spike profile)
Final: merge output/deep/*.json, rank by callback_likelihood, recommend top 5 w/ reasoning.

### RECENCY re-rank — dispatched 2026-06-09
User feedback: posting-date under-weighted. Applied to 6 now (Ankar FA, Alaro, Neutreeno, Mozart, Moss, Terra API).
New 7-factor model: requirements .25 / RECENCY .25 / spike .18 / competition .12 / screening .12 / warmpath .05 / conversion .03 → callback_v2.
Re-researching real posting_date/applicant_count for 26 live roles, recomputing callback_v2 into output/deep/{slug}.json.
- aef0d316e2f70d40c: batch1 (Conduct,Sequence,Specter,Magentic,Gradient,Corgi)
- a69a872720ca4ea77: batch2 (Marloo,ivee,Scope,Wing,Capital on Tap,governr)
- ad57683807e290e9f: batch3 (StudioB,Installio,Jack&Jill,ElevenLabs Growth,Deel)
- a4695db305b5f63fc: batch4 (Dayjob,Seamflow,HappyRobot,Siena,Decagon)
- a11565a9605ee2468: batch5 (n8n,Lovable,ElevenLabs DS,32Co)
Final: rank 26 by callback_v2, show next ten (user wants the ranked list).

### APPLIED (exclude from all rankings): Ankar FA, Alaro, Neutreeno, Mozart AI, Moss, Terra API, Installio (7 total as of 2026-06-09)
### CLOSED (confirmed): Tilt, Assuric, Jack & Jill, Deel GTM AI Operator
### Alt-signal dating dispatched: a4c49bcfa24018311 — dating Specter, ivee, governr, Dayjob via LinkedIn/Wayback/social/sitemap (ATS exposes no date). New role added: Togather AI Ops Mgr (callback 56).

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

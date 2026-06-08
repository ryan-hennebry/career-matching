# VC Talent Boards Wave 2 — Summary (2026-06-08)

| Score | Title | Company | Location | Role Type | Status |
|-------|-------|---------|----------|-----------|--------|
| 89 | Agent Strategy Manager | Decagon | London | founding-generalist-priority | confirmed |
| 87 | Strategist, Agent Development | Sierra | London | ai-product-associate-ai-product-builder | confirmed |

**Net-new verified:** 2 | **Above 70:** 2

## Method
Mined VC portfolio talent boards (EF/joinef, Index/Getro, Seedcamp, Phoenix Court/LocalGlobe, Balderton, Atomico, a16z, Air Street) + named London AI portfolio companies via their direct ATS (Ashby GraphQL API).

## Boards reached vs gated
- Getro boards (EF, Index, Atomico, Balderton): job-data APIs gated behind api@getro.com; frontends JS-rendered — could not extract filtered listings programmatically.
- Consider boards (Phoenix Court/LocalGlobe, Balderton): JS-rendered, no public job API.
- Seedcamp board: readable default state only (surfaced Enzai FA — closed; Stackfix Ops Assoc — closed, <£50K, not core AI).
- a16z: US-heavy, no UK matches.
- Air Street Capital: no dedicated job board (network-based).
- WORKED WELL: Ashby GraphQL (`jobs.ashbyhq.com/api/non-user-graphql` op=ApiJobBoardWithTeams / ApiJobPosting) for direct portfolio-company ATS — bypasses JS rendering, returns full descriptions + comp + isListed. This is the reliable lever for these boards.

## Deduped out
- Gradient Labs (only AI Delivery Associate [set A] + AI Delivery Lead [excluded]; no Ops Generalist found)
- ElevenLabs Growth Generalist & Deployment Strategist Europe (= prior dedup set B)
- Lovable Deployment Strategist (set B); Lovable Finance & BizOps role evaluated but is FP&A specialist (IB/PE/CPQ/SQL gaps) — below 70
- Cognition Business Operations (SF, not UK)
- Synthesia Deal Strategy Analyst (deal-desk/CPQ/Salesforce specialist — below 70)
- Natter Founder Associate, Dwelly Ops (= prior dedup); Enzai FA & Stackfix Ops (closed)

## Notable London AI companies surfaced (for future waves)
Basis AI (agentic — "agents that operate for hours, end-to-end" for accounting firms; mostly NY/SF roles currently), Robin AI (legal AI, talent-pool only), Lovable, Decagon, Sierra, PolyAI (FDE roles US/Vancouver only), Wayve (operational/manager roles only), Humanloop, Synthesia.

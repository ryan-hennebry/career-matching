---
name: vc-talent-boards-jun2026
description: Jun 2026 VC portfolio talent boards — Getro/Consider APIs gated; Ashby GraphQL is the reliable lever for portfolio-company ATS. Decagon 89, Sierra 87.
metadata:
  type: reference
---

# VC Talent Boards Mining (Jun 2026, vc-talent-boards-wave2)

**Key lever — Ashby GraphQL** (bypasses JS-rendered Ashby boards, returns full data):
- List: `POST https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams` with body `{"operationName":"ApiJobBoardWithTeams","variables":{"organizationHostedJobsPageName":"<org-slug>"},"query":"query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) { jobBoard: jobBoardWithTeams(organizationHostedJobsPageName: $organizationHostedJobsPageName) { jobPostings { id title locationName } } }"}` — org-slug = the path in jobs.ashbyhq.com/<slug> (e.g. decagon, sierra, lovable, cohere, elevenlabs, harvey, perplexity, writer, synthesia, assembledhq).
- Detail: same endpoint `op=ApiJobPosting`, vars `{organizationHostedJobsPageName, jobPostingId}`, fields `title locationName employmentType descriptionHtml compensationTierSummary isListed`. NOTE: field is `descriptionHtml` (NOT descriptionPlain). Strip tags + html.unescape.
- The Ashby posting-api (`api.ashbyhq.com/posting-api/job-board/<slug>`) often 404s for these orgs even when the GraphQL works — prefer GraphQL.

**Gated/blocked:**
- Getro boards (EF portfolio.joinef.com, Index indexventures.getro.com, Atomico careers.atomico.com, Balderton careers.balderton.com): job data API returns "contact api@getro.com"; frontends JS-rendered. Not programmatically minable.
- Consider boards (Phoenix Court/LocalGlobe jobs.phoenixcourt.vc, Balderton): JS-rendered, no public job API.
- Seedcamp talent.seedcamp.com: WebFetch reads only default (unfiltered) state.
- a16z: US-heavy, no UK matches. Air Street Capital: no job board (network only).

**Net-new found:** Decagon Agent Strategy Manager (London, £105-140K, score 89, a16z/Accel/Index-backed, conversational AI agents) → founding-generalist. Sierra Strategist Agent Development (London, £125-245K, score 87, Bret Taylor/Clay Bavor agentic AI) → ai-product. Both via Ashby GraphQL.

**Deduped/excluded:** ElevenLabs Growth Generalist & Deployment Strategist (prior set), Lovable Deployment Strategist (prior); Lovable Finance & BizOps = FP&A specialist (IB/PE/CPQ gaps, <70); Cognition Business Operations = SF; Synthesia Deal Strategy Analyst = deal-desk/Salesforce/CPQ specialist (<70); Gradient Labs has only AI Delivery Associate/Lead; Enzai FA & Stackfix Ops = closed.

**Notable London AI cos for future waves:** Basis AI (agentic, agents run for hours end-to-end for accounting — currently NY/SF roles), Robin AI (legal AI, talent-pool only), PolyAI (FDE US/Vancouver only), Humanloop. See [[ats_endpoints_june2026]].

## Wave 3 (delta-vc-boards, 2026-06-10) — 0 net-new qualified
Fresh-raise cohort checked (May–Jun 2026): **Inherent** (Index, $50M, ex-DeepMind AI-science lab; jobs.ashbyhq slug `inherent` works = 6 postings, ALL Member-of-Technical-Staff/eng + General App — anti-fit, no operator role). **Tilt** (Balderton/Seedcamp/Vinted, $26M Jun 2; consumer live-commerce, NOT AI-product; FA already in exclusion/closed). **Gradient Labs** ($26M Jun 1; slug `gradient-labs` = AI Delivery Associate [excluded] + new Founding Platform & Security Engineer [eng]). **CodeWords/Agemo** (agentic workflow, $9M seed; NO Ashby/GH/Lever board, careers 404, applies via WTTJ only — not minable). **Poolside / Black Forest Labs / Sereact / Profluent** (Air Street): Poolside slug works but 0 operator UK; Sereact = Stuttgart/Boston only; BFL/Profluent NO Ashby board.
Encord: Lever slug `CordTechnologies` now returns EMPTY (0) and GH `encord` empty — the "Growth Strategy Operations Analyst" seen on YC London cache (posting 137e30c2…) is STALE/404. Encord careers = encord.com/careers (Series C $60M, "multimodal data layer for Physical AI").
Specialist-ops noise to SKIP (recurring, all anti-fit for Ryan's founding-generalist profile): ElevenLabs Data Ops/Tech Ops/Workplace Ops/Talent Ops; Harvey IT/User Ops + GTM Enablement; Perplexity People Ops Generalist; Writer AI Deployment Engineer; Granola People Ops Lead/Founding Legal Counsel; Legora RevOps/Engagement Associate; Sierra PM Agent Development (product-specialist, ×6 language variants). Lovable PM Enterprise = net-new but enterprise-PM gate.
**Letty** (EF, agentic PropTech, FA London £55-75K Hoxton 5d in-office): same role flagged Mar 2026 (score 91), start date Mar/Apr 2026 = STALE not net-new; no public ATS (StudySmarter/ZipRecruiter/BeBee mirrors only, slugs `letty`/`joinletty` no Ashby/GH). Do not treat aggregator "June 2026" framing as a real posting date.
**Verdict:** London AI operator market saturated vs the 70-co exclusion set. Fresh raises are eng/research-only or non-UK. Aggregators (topstartups.io, growthlist) surface scaled cos (Encord/Synthesia/PolyAI/Omnea), not fresh early-stage operator roles. Channel low-yield for delta sweeps until new seed cos with explicit FA/CoS postings appear.

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

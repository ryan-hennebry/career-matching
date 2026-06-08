---
name: curated-operator-boards-jun2026
description: Jun 2026 effectiveness of curated newsletter & operator-community job boards (Lenny's, MKT1, generalist.world, AI Operators, Chief of Staff Network, On Deck, etc.) for UK AI operator roles
metadata:
  type: reference
---

Curated newsletter / operator-community boards mined Jun 2026 for UK AI operator roles (Founder's Associate / Founding Operator / Founding Generalist / AI Ops / AI Product). Verdict: heavily US-skewed; very low UK yield — every UK role found was already in dedup.

**Best discovery (NEW): AI Operators newsletter by Evan Lee** — aioperators.substack.com. Bi-weekly "N Chief of Staff & BizOps jobs in AI", curated AI-startup operator roles with stage + location + direct ATS link in each issue. Vol. 027 = latest (Jun 2026). Each issue lists ~30-50 roles but only 2-4 are EMEA/UK; rest US. Mine the latest 2-3 vols each run. UK/EMEA seen: Natter (London FA — dedup), Dwelly (London Ops Mgr-Payments — senior, 5yr+20-30 reports, skip), Numeral (EMEA BizOps — dedup), Stacks (London/Amsterdam CoS — now CLOSED, not on Ashby board), Stilta (Stockholm), H Company (Paris).

**Chief of Staff Network** (chiefofstaff.network/jobs) — WebFetch works, returns UK roles with location tags. Most UK roles non-AI (Monzo, Bending Spoons) or in dedup (Jack & Jill CoS — needs McKinsey/BCG/Bain + 5yr). Decent for London CoS but low AI-operator yield.

**generalist.world/jobs** + /jobs/remote + /jobs/systems-thinkers — WebFetch works well, 260+ roles. Mostly US founder's-associate (Arcline YC W26 = AI-native legal, SF/NY no remote; RightFit SF/NY/Bangalore; Lorikeet/Decagon US). UK roles thin and already in dedup (ivee). Tag pages (/systems-thinkers) useful.

**MKT1 job board** (jobs.mkt1.co) — WebFetch works. B2B-marketing-focused (not operator). London AI roles surfaced: Clay Founding Marketer EMEA, Dust Founding Partnerships Lead UK, ElevenLabs Growth Generalist (dedup), Granola/Lovable marketing leads — all marketing-specialist, not target operator types.

**Gated / dead:** Lenny's board (lennys-jobs.pallet.com ECONNREFUSED; lennysjobs.com 403) — use lennys-jobs.pallet.com via WebSearch only. Operators Guild jobs = 404 (members-only newsletter). On Deck jobs.beondeck.com → 301 to joinodf.com (founder fellowship, not a job board). Elpha = cert expired. welcometothejungle = 403 (use Ashby posting-API instead).

**Pattern:** For H Company (Paris agentic AI, offices Paris/London/NYC) the Ashby posting-API api.ashbyhq.com/posting-api/job-board/hcompany shows -US and -London suffixed duplicates; the unsuffixed Catalyst/Implementation Strategist are "Hybrid Paris" (not UK). Always check the `location` field via the posting-API, not the title suffix. See [[ats_endpoints_june2026]].

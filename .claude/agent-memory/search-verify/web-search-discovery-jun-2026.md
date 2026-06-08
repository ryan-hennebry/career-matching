---
name: web-search-discovery-jun-2026
description: Web-search-discovery channel findings for Ryan's 5 founder/operator/AI-ops/product role types, June 2026 run.
metadata:
  type: project
---

Web Search Discovery channel run, 2026-06-08, for role types: founder-s-associate-priority, founding-operator-priority, founding-generalist-priority, ai-operations-ai-ops, ai-product-associate-ai-product-builder.

**Why:** Open-ended discovery to find AI-company roles not on standard boards.
**How to apply:** Reuse these source/exclusion findings on the next web-discovery run to avoid re-walking dead ends.

## Verified (clean URL)
- **Numeral** Business Operations Manager (International), EMEA remote, $55-75K+equity — AI-native tax (Benchmark+YC). Ashby API: api.ashbyhq.com/posting-api/job-board/numeral works. Score 75. Tax domain is the gap.
- **Dwelly** Operations Manager — Payments, London — AI-enabled lettings operator. EU Greenhouse (job-boards.eu.greenhouse.io/dwelly). Score 58, payments-mgmt-specific (manages 20-30), weak generalist fit.

## Verified active but NO per-role URL (held in output/_web_discoveries_pending_url/)
- **Specter** (tryspecter.com / specter.careers — AI-powered startup-data & deal-sourcing platform, bootstrapped, HQ London) has 3 strong open roles: Founder's Associate (£42-77K, score 95), Finance & Operations Associate (£30-60K, score 88), Product Specialist (from £39K, score 92). ALL apply via Notion hub (spectertech.notion.site/Specter-is-Hiring-5ef937c8a5584a3ba85d138339cc5eff) + careers@tryspecter.com. NO per-role URLs exist.
- **GOTCHA:** `jobs.ashbyhq.com/specter` is a DIFFERENT company (Specter Aerospace, SF hardware). Do not use it for the AI Specter.
- **Schema gate:** validate-schema `_is_specific_job_url` rejects the Notion hub URL (generic-hub, no UUID/4-digit ID, shallow path). Files moved OUT of output/verified/ tree (validator scans all subdirs) into output/_web_discoveries_pending_url/ so the 15 clean files pass 15/15.

## Excluded / dead ends
- Natter Founder Associate (London, AI video) — CLOSED. Ashby JS-rendered; Kindred Capital board (jobs.kindredcapital.vc) had full desc but role closed.
- Anima, Gendo, Brickwise FA roles — gone/replaced (Brickwise now only a $400-1k/mo social content creator).
- Metaview (AI recruiting agents, London) Operations Associate — no longer on live builtinlondon list.
- Gradient Labs Operations Generalist — stale aggregate; live Ashby has only eng + AI Delivery Lead (Lead-excluded).
- Decagon, SellScale Founding Operator, OpenAI/Cohere/Parsewise/Isidor/Synthflow FDE — all SF-only and/or coding-heavy engineering; not UK-generalist fits.
- Jack & Jill Chief of Staff (London AI) — chiefofstaff.network URL 404'd; flag for direct-career-pages channel.

## Source effectiveness
- aioperators.substack.com newsletter (Vol 027 "41 Chief of Staff & BizOps jobs") = good source for AI BizOps/CoS/FA roles with direct apply links (surfaced Dwelly, Numeral, Natter).
- api.ashbyhq.com/posting-api/job-board/{company}?includeCompensation=true = reliable for full listing extraction when Ashby pages are JS-rendered.
- wellfound.com job pages = 403. builtinlondon.uk company/jobs pages = good fallback.
- "Founding Operator" title = SF-skewed, near-zero UK. Confirms prior memory.

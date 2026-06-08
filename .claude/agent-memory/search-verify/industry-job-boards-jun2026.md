---
name: industry-job-boards-jun2026
description: Industry Job Boards channel findings June 2026 — Corgi Insurance, Lightning AI, board reachability for Ryan's AI operator/generalist search
metadata:
  type: project
---

Industry Job Boards channel run, 2026-06-08, role types: founder's-associate, founding-operator, founding-generalist, ai-operations, ai-product-associate.

**Why:** Capture which boards/companies were productive so future runs skip dead sources and re-check live AI-company roles.

**How to apply:** On next industry-job-boards run, re-verify these companies' boards first; treat dead boards as low priority.

## Productive findings
- **Corgi Insurance** (YC S24, AI financial infrastructure — designs/underwrites/prices/issues insurance with AI): best find. Multiple London roles via ycombinator.com/companies/corgi-insurance/jobs. Operations Associate (£50-70K, London, in-person, any level) scored 100. Strategic Projects Associate (USD 125-200K, London/Chicago, in-office 6-7 days) scored 95. NOTE: roles are in-office 6-7 days/week — intense for a Cambridge commuter. GTM Associate is Salt Lake City (US-only). Compliance and Operations Associate URL (n5Mex2P) 404s.
- **Lightning AI** (from PyTorch Lightning, merged Voltage Park; AI infra platform): Forward Deployed Engineer London hybrid, posted 2026-06-02. Heavily ML-infra (vLLM/TensorRT/Ray/K8s/GPU) — scored 60, below threshold for generalist profile. Listing via gravityer.com.

## Excluded / dead leads
- HappyRobot (AI agents for logistics) Founder's Associate = SF/remote-US — location excluded. $130-180K, 1-3yr consulting required.
- Nowadays (AI corporate event planning) Founding Operator = SF in-person — excluded.
- Natter (London conversational AI/video) Founder's Associate = "no longer accepting applications" (Kindred Capital board + jobs.ashbyhq.com/Natter).
- Brickwise (YC F25, London AI property manager) now lists ONLY Social Media Content Creator ($400-1K/mo) — no FA. FA from earlier 2026 runs is gone.
- AgentMail (YC S25, London, AI agent email inboxes) = Founding Strategy & Operations **Lead** — Lead title excluded. Found via generalist.world.
- Gradient Labs (London, AI agents for finance ops) — Ashby API api.ashbyhq.com/posting-api/job-board/gradient-labs works; only AI Delivery Lead (Lead, excluded) + engineering/sales. No associate/generalist ops role.
- OpenAI Forward Deployed (Software) Engineer London exists but career page 403s; core SWE role.

## Board reachability
- ycombinator.com/companies/{co}/jobs and individual /jobs/{slug} URLs: WebFetch works well. Best source this channel.
- ycombinator.com/jobs/location/london: works, shows ~50 roles but truncates ("create profile for full access").
- ycombinator.com/jobs/role/{role}/london: 404s (role-specific location URLs broken).
- jobs.ashbyhq.com/{co} HTML: JS-rendered, returns title only. Use api.ashbyhq.com/posting-api/job-board/{co} JSON instead — reliable.
- gradient-labs.ai/careers, jobs.ashbyhq.com pages: JS-rendered, no listings via WebFetch.
- Wellfound, Otta, Cord, aijobs.app, aijobsboard.net, workinai.xyz, remoteai.io: not directly fetched this run — WebSearch site: discovery + ATS follow-through remains the productive pattern (consistent with prior runs).
- generalist.world: good discovery source for founding/ops roles (surfaced AgentMail).

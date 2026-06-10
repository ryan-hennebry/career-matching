# Agent Memory

## Index (topic files)
- [Founding Operator direct-careers](founding_operator_direct_careers.md) — Jun 2026: big AI cos don't use founder titles; target Special Projects Eng / FDE / AI Outcomes Mgr. Cognition 92, Glean 85.
- [ATS endpoints June 2026](ats_endpoints_june2026.md) — working Greenhouse/Ashby/Lever/Workable slugs; correct gleanwork, perplexity, Sierra slugs.
- [FDAI Accelerator archetype Jun 2026](fdai-accelerator-archetype-jun2026.md) — "Forward Deployed AI Accelerator" (Stripe template, May 2026) is misleading: internal AI-build/ops role NOT enterprise FDE. Hits Ryan's Claude Code spike. Checkout.com 61.
- [Curated Operator Boards Jun 2026](curated-operator-boards-jun2026.md) — NEW best source: AI Operators newsletter (aioperators.substack). Lenny's/MKT1/generalist.world/CoS Network mostly US; UK roles all in dedup.
- [VC Talent Boards Jun 2026](vc-talent-boards-jun2026.md) — Getro/Consider VC boards gated/JS; Ashby GraphQL (op=ApiJobBoardWithTeams/ApiJobPosting) is reliable lever for portfolio-co ATS. Decagon 89, Sierra 87.
- [Web Search Discovery Jun 2026](web-search-discovery-jun-2026.md) — Specter (AI Specter=specter.careers, NOT ashby/specter=Aerospace) 3 strong London roles via Notion hub (no per-role URL, fails schema gate); Numeral/Dwelly verified; Founding Operator=SF-only.
- [JobSpy Deep Wave2 Jun 2026](jobspy-deep-wave2-jun2026.md) — glassdoor location-parse ALWAYS fails; LinkedIn desc=nan (WebSearch for desc+url). Net-new: Tilt 92, Fuse Energy FA 84/AI-Ops 80, Tomoro 78, Siena AI 74, Plum 72.
- [Delta Industry Boards Jun 2026](delta-industry-boards-jun2026.md) — Jun 10 delta: ZERO net-new operator roles (channel exhausted). hnhiring + startup.jobs = 403; api.ashbyhq.com/posting-api/job-board/{slug} works when HTML is JS-empty.
- [Delta Web-Search Jun 2026](delta-websearch-jun2026.md) — Jun 10 delta: ZERO net-new fit roles. Fresh-funded London agentic cos surfaced (Airspeed/Glyphic, Kohort, Paid AI) but operator roles US-based. Confido/Ema CoS=NY; Encord Lever 404s.

## Industry Job Boards (AI operator/generalist roles, Jun 2026)
See industry-job-boards-jun2026.md for detail. Key: Corgi Insurance (YC S24 AI fintech) is the standout — London Operations Associate (£50-70K, score 100) + Strategic Projects Associate (score 95), both in-office 6-7 days/wk. Lightning AI FDE London = ML-infra heavy, score 60. Excluded: HappyRobot/Nowadays (US), Natter FA (closed), Brickwise (FA gone), AgentMail/Gradient Labs (Lead title only). YC company /jobs pages + api.ashbyhq.com/posting-api/job-board/{co} are reliable; ashbyhq.com HTML + gradient-labs.ai JS-rendered.

## Source Effectiveness (Marketing Manager roles, Feb 2026)
- **Web3.Career**: Best source for crypto/web3 marketing roles. Returns structured data with salary estimates.
- **CryptocurrencyJobs**: Good supplementary source. Some roles overlap with Web3.Career.
- **YC Jobs (ycombinator.com/jobs)**: Good for startup roles with London presence. Returns structured listings.
- **Indeed/LinkedIn (via JobSpy)**: Returns mainly consumer brand/FMCG results for "Marketing Manager" queries. Need industry qualifiers in initial search but even then results are mainstream. Retry with broader query (drop industry qualifiers) gets volume but low relevance for crypto/AI.
- **Remote3, LaborX, AIJobs.app, AIJobs.ai, TheAIJobBoard**: Returned zero or near-zero relevant results. JS-rendered or blocked.
- **UK Startup Jobs**: Listings found but mostly expired.
- **Jumpstart-UK, Built In London, Escape the City, Techstars**: Low yield for marketing manager specifically.

## Search Patterns
- First JobSpy query with industry qualifiers ("crypto AI startup web3 machine learning") returns zero results. Broader retry without qualifiers returns volume but mostly irrelevant.
- Specialty sources (Web3.Career, CryptocurrencyJobs) are far more productive than aggregators for niche industry roles.
- Many Indeed job URLs return 403 on WebFetch. Use aggregator description data instead.

## Source Effectiveness (AI Agent Company Roles, Feb 2026)
- **Anthropic Greenhouse**: Best source by far. 35+ marketing roles, 6+ in London/EMEA. Direct career page fetch via greenhouse.io works well. Need to fetch /careers/jobs not /careers (landing page only).
- **ElevenLabs Ashby**: New finding. 3+ UK-remote marketing roles. Ashby JS-rendered but listing data extractable. WorkingNomads mirrors work for full descriptions.
- **Cohere Ashby**: London role is Customer Support Engineer only. No UK marketing roles as of Feb 2026.
- **OpenAI Careers**: 403 on direct fetch. Limited London roles visible via WebSearch.
- **Perplexity Ashby**: London roles limited to Customer Success and IT. No marketing in UK.
- **Cognition Ashby**: Account Director UK (London) but all marketing US-based (SF/NYC/Austin).
- **Cursor/Anysphere**: 403 on career page. All roles in SF via WebSearch.
- **Replit**: 403 on career page. All marketing roles Senior/Lead level via WebSearch.
- **Hugging Face Workable**: Community ML Research Engineer EMEA Remote exists but engineering-focused. No marketing.
- **Mistral AI Lever**: JS-rendered, unable to extract listings via WebFetch.
- **Stability AI, Mistral AI**: Career pages JS-rendered, unable to extract listings via WebFetch.

## AI Agent Company Search Patterns
- Most AI agent startups are SF-based and only hire locally. London presence is limited to Anthropic, ElevenLabs, Cohere, Cognition, Wayve, Synthesia, DeepMind.
- ElevenLabs has a London hub and hires UK-remote for marketing roles (B2B growth, performance marketing, creative).
- Anthropic's EMEA expansion is the dominant opportunity for AI agent company roles in UK.
- New Anthropic roles since 2026-02-19: Claude Evangelist Applied AI (Startups), Partner Marketing Lead EMEA, Product Support Specialist (Wed-Sun) London, Customer Marketing Manager EMEA (6+ years, £160K).
- Many Anthropic EMEA roles require 10-12+ years. The sweet spot is 5-8 year requirement roles.
- Anthropic Customer Marketing Manager EMEA (job 4971197008) requires 6+ years B2B customer marketing — community/content background is adjacent, not direct. Score 79/100.
- Anthropic career page: MUST fetch /careers/jobs (not /careers which is a landing page). Greenhouse job board returns full listings. WebFetch of individual job URLs works reliably.
- ZipRecruiter and WorkingNomads mirrors work when Ashby JS-rendered pages fail.
- Cognition AI has London Account Director but marketing roles are US-only.
- "Lead" title exclusion affects 3 of the top Anthropic results -- flag for parent to decide.
- Wayve careers redirect: wayve.ai/careers → wayve.firststage.co/jobs (307 redirect). Marketing Communications Lead role is in Sunnyvale CA.
- Character AI: All roles in Redwood City CA. No UK roles. jobs.ashbyhq.com/character/ works for listing extraction.
- Assembled: Field Marketing Manager in SF/NYC only. Customer Success Manager - Mid Market in London exists. Jobs at jobs.ashbyhq.com/assembledhq.
- Dust: Founding Growth Marketer (SF, in-person) — not remote. Careers at jobs.ashbyhq.com/dust (JS-rendered, use WebSearch instead).
- Jasper AI: jobs.ashbyhq.com/Jasper%20AI works for listing. Sr. Executive Communications Manager (London Remote) but "Senior" excluded.
- Sierra AI: Field Marketing Manager (London) at jobs.ashbyhq.com/Sierra — wrong role type (not marketing specialist/associate).
- CrewAI: apply.workable.com/crewai — JS-rendered. All engineering/CS roles. No marketing roles.

## Source Effectiveness (Niche Newsletters Channel, Feb 2026)
- **Early & Exec (earlyandexec.substack.com)**: Best niche newsletter source. Bi-weekly early-stage roles + exec roles for European tech. Feb 2026 issues skewed exec/senior (excluded) and non-UK locations. Founder-associate type roles appear in early-roles issues (published ~every 2 weeks). Fetch /archive to find latest issue slugs, then fetch individual posts.
- **HN Who Is Hiring thread**: Engineering-heavy, rare marketing/community roles. Low yield for non-technical roles.
- **Product Hunt Startup Roles thread**: 403 blocked — cannot fetch.
- **WorkInStartups.com**: Displayed sales roles rather than marketing in paginated view. Low yield.
- **Newsletter channel overall**: Low yield for marketing-associate, marketing-specialist, community-manager. Only useful for founder-associate type roles. Exec newsletter has 100 roles but all senior/director/VP level — excluded.

## Niche Newsletter Search Patterns
- Early & Exec archive URL: earlyandexec.substack.com/archive — fetch this to get latest issue slugs.
- Individual issue URL pattern: earlyandexec.substack.com/p/early-roles-{date} or /p/exec-roles-{date}.
- Magic AI (London) had Founder's Associate posted Feb 4, 2026, removed Feb 23 — role filled rapidly. Indicates strong competition for AI startup FA roles.
- Roles from newsletters are 1-4 weeks old when found — verify active status before scoring.
- Accel job board (jobs.accel.com) mirrors Tracebit and similar Accel portfolio companies well.

## JobSpy Aggregator Relevance (Founder's Associate / Community Manager, Feb 2026)
- **Founder's Associate**: 28 jobs returned. ~7 from genuine AI companies (Euphoric, Specter, White Circle, MaplePoint, Anima, Kernel). Most are VC, ops, or non-AI startups.
- **Community Manager**: 41 jobs returned. <5 from AI companies. Pret A Manger, NielsenIQ, customer success roles dominate. Very low signal for AI community roles.
- **Marketing Associate**: 29 jobs returned. Mostly non-AI. Valence (AI coaching) was the only strong AI company match from aggregator.
- **Marketing Specialist**: 31 jobs returned. Mostly SEO/digital agency/finance. ACCURACAST GEO Specialist (AI search optimisation) is the standout niche find.
- Ashby career pages: Use WebFetch of ashbyhq.com job URLs — works reliably for White Circle, Anima. White Circle deadline: always check application deadline from Ashby.

## New AI Company Findings (Feb 2026)
- **White Circle** (whitecircle.ai): AI safety/reliability infrastructure. Raised $11M from OpenAI/Anthropic/Mistral/HuggingFace/DeepMind. Founder's Associate Growth role requires Python/TypeScript — engineering-heavy not marketing.
- **Phyron AI** (phyron.com): AI video generation for automotive dealers. 30+ countries. Content & Community Manager role published Feb 24, 2026. Excellent match for Ryan's content+community skills. London remote-friendly.
- **Anima** (animahealth): YC-backed AI health tech. Founder's Associate role targets 0-3 years. Ryan is overqualified.
- **Valence** (valenceapp.com): AI-native enterprise coaching platform. Strategy & Operations Associate in London. Good startup generalist match.
- **ACCURACAST**: Digital marketing agency specialising in GEO (Gen AI Engine Optimisation). Emerging role for AI search visibility — good fit for content marketing + AI tools background.

## Source Effectiveness (Industry Job Boards Channel, Feb 2026)
- **Y Combinator Jobs (/location/london)**: Excellent — returned 50 London jobs including 3 Founder Associate roles and 1 ABM Marketing Manager. Use /jobs/location/london (not /jobs?q=marketing) for best results.
- **Y Combinator Jobs (/role/marketing/london)**: Only 1 result (Authologic ABM Manager). Less productive than /location/london.
- **Wellfound**: 403 on all category pages (/role/l/marketing/london, /role/r/marketing-associate). Blocked completely.
- **AI-Jobs.net**: Dead — redirects to foorilla.com. Do not attempt.
- **Work in AI (workinai.xyz)**: JS-rendered only, redirects to /lander. Returns no data.
- **RemoteAI.io**: 404 on /jobs endpoint.
- **Otta**: Redirected to uk.welcometothejungle.com — further queries return 404.
- **Cord.co**: Redirects to cord.com — JS-rendered, no listings extractable.
- **AI Jobs Board (aijobsboard.net)**: Redirects to dead domain (ww1.aijobsboard.net). Defunct.
- **AIJobs.ai (/marketing)**: Returns US-centric Senior/Lead/Director roles — low yield for UK non-senior.
- **Work at a Startup**: WebFetch works, returns YC community jobs (same data as /jobs/location/london, different format). Useful for verifying specific YC companies.
- **WebSearch discovery via LinkedIn/ZipRecruiter/BuiltIn**: More productive than job board direct fetches for this channel. Encord (Lever), Limio (direct careers page), Propel (LinkedIn), Pangaea Data (direct careers page) — all found via WebSearch.

## Industry Job Boards Channel Findings (Feb 2026)
- **Encord** (AI data quality for AI, YC-backed): Two open London roles — Growth Associate - Community (78 score) and Founder's Associate (expired June 2025). Lever at jobs.lever.co/CordTechnologies. Growth Associate - Community matches Ryan's skills well but targets entry/junior level.
- **Linda AI** (autonomous healthcare AI agents): Founders Associate in London, score 95, posted Jan 7 2026, expires Apr 7 2026. Apply with CV + pride piece + why Linda resonates.
- **Propel (recruiter)**: Placed Events Marketing Manager for undisclosed AI-native startup ($80M+, enterprise AI). £60-70K, London hybrid, 3-6yr events experience. Weekly evening events = Cambridge commuter challenge.
- **Pangaea Data** (AI precision medicine, LLMs in medicine): Marketing Specialist in London, confirmed active on careers page but minimal job description. Apply via email.
- **QFEX** (YC crypto fintech, Cambridge founders): Founder Associate London £60-100K but requires Oxbridge/STEM degree + 12hr/6day commitment — poor fit for Ryan.

## Source Effectiveness (LinkedIn Channel, Mar 2026)
- **LinkedIn direct fetch**: Blocked for most listing pages. Use WebSearch with site:linkedin.com to find individual job URLs, then verify via company career pages or ZipRecruiter mirrors.
- **LinkedIn AI startup aggregate pages** (uk.linkedin.com/jobs/ai-startup-jobs-london): Returns 389 jobs but only titles/companies visible — cannot extract descriptions without login. Low individual yield.
- **Company career pages via LinkedIn discovery**: Productive. Scandit found via LinkedIn, verified via builtin.com. Seal found via LinkedIn/YC cross-reference.
- **Founder Associate LinkedIn page** (uk.linkedin.com/jobs/founder-associate-jobs-london): Returns ~69 jobs. Mix of AI and non-AI companies. Most duplicates of existing verified set after filtering non-AI.
- **ZipRecruiter mirrors**: 403 blocked in Mar 2026 for Scandit job URL. Use builtin.com or direct career pages instead.
- **startup.jobs/locations/london**: 403 blocked.

## LinkedIn Channel Findings (Mar 2026)
- **Scandit** (scandit.com): Social Media and Community Manager, London hybrid, score 87. Unicorn (~550 employees). AI-adjacent (ML/CV for smart data capture). Role requires AI tools/LLMs proficiency — good match for Ryan. Active on LinkedIn (1 week old) and confirmed on builtin.com.
- **Seal** (seal.run): Founder Associate, London in-person, score 62, BELOW THRESHOLD. YC S20, AI-native GxP platform for pharma/life science. £40-60K + equity. Role requires coding/engineering skills not in Ryan CV. Execution-heavy, explicitly not strategy or marketing.
- **Bezos.AI**: E-commerce logistics fulfilment SaaS — NOT an AI product company. Graduate level ops role. Skip.
- **Nova/NOVA LinkedIn listing**: Resolves to Nova Founders Capital (VC firm), not AI product startup. Skip.
- **Gopuff**: Food delivery. FA role not AI-related. Skip.
- **Anima FA**: Duplicate from previous channel run (Ashby/jobspy). Already in verified set.

## Direct Career Pages Channel (Mar 2026)
- **Synthesia Ashby/Greenhouse**: Community Manager role (London hybrid, 3-5yr experience, Circle.so). Confirmed via TheHub.io (expiry Sept 2026). Greenhouse URL 4711805101 returns 404 on direct WebFetch but is valid — apply via thehub.io/jobs/6917c620cc00a86a102e5026. Synthesia uses EU Greenhouse (job-boards.eu.greenhouse.io/synthesia) but this also 404s. Use Ashby at jobs.ashbyhq.com/Synthesia for Synthesia job listings (Social Media Lead shown, Community Manager not listed — role may be on both Greenhouse and TheHub only).
- **Anthropic new EMEA roles (Mar 2026)**: 4 new London roles found — Marketing Events Lead (12+yr, Lead title), Segment Marketing Manager Industries (10+yr), Field Marketing Lead Industries (10+yr, Lead title), Developer Community Lead (8+yr, Lead title). ALL excluded: Lead title or 10-12+ year requirement. Anthropic EMEA expansion continues but roles are increasingly senior.
- **Anthropic EMEA roles (Mar 20, 2026)**: Re-confirmed all 6 Anthropic London marketing roles still active. Customer Marketing Lead Startups EMEA (5093547008) updated 2026-03-19 — role recently refreshed. All 6 still have Lead title or 10+ year requirement. No new Anthropic UK marketing roles since Mar 3.
- **Synthesia TheHub**: Best source for Synthesia jobs. TheHub.io listing confirmed active with expiry Sept 2026. Score 91 for Ryan's community management + ambassador programme design + AI tools background.
- **Glean Greenhouse**: Job ID 4467974005 maps to "AI Outcomes Manager" not "Field Marketing Specialist" — stale URL from WebSearch. Glean marketing roles are SF-based. Senior Director EMEA Marketing London found Mar 20 — Director level, excluded.
- **Vercel Partner Marketing Manager EMEA** (Mar 20 check): Active role at vercel.com/careers (£93-139K). Requires 6+ years B2B marketing + 3+ years partner/ecosystem marketing with GSIs/ISVs/cloud platforms. Score 69/100 — below threshold. Primary gaps: partner/channel marketing background not in Ryan's CV; Vercel is devtools/infrastructure not core AI company. Vercel Field Marketing Manager EMEA CLOSED as of Oct 15, 2025.
- **Writer UK**: All UK roles are engineering/sales/recruiting — no marketing roles.
- **Scandit**: Social Media and Community Manager London (87 score) found via LinkedIn channel by separate subagent dispatch.
- **ElevenLabs B2B Growth Marketing - Agents**: Working Nomads showed EXPIRED but ElevenLabs official careers page still lists as active (Mar 20, 2026). Always verify against official ElevenLabs careers page, not WorkingNomads mirror.
- **Magic AI (magic.dev)**: 12 open roles, all in San Francisco. No marketing roles. api.ashbyhq.com/posting-api/job-board/magic.dev works for listing extraction.
- **Jasper AI**: jobs.ashbyhq.com/Jasper%20AI API works. Only London role is Senior Executive Communications Manager (excluded). Account Based Marketing Manager is US-only.
- **Mistral AI Field Marketing Manager EMEA**: Paris-based (primary), requires French fluency, listed as archived on WelcomeToTheJungle. Do not pursue.
- **Runway ML Greenhouse**: api returns 37 roles — all engineering, finance, or creative (Art Director, Copywriter, Creative Director). No community/marketing specialist roles in UK.
- **Anthropic Partner Marketing Lead EMEA (Mar 25, 2026)**: New role (job 5118191008). Lead title excluded. £160K-£200K. Requires 5-8+ years partner/channel marketing with cloud ecosystems (AWS/Azure/GCP). Pattern: Anthropic EMEA roles require Lead title or specialist experience not in Ryan's generalist background.
- **ElevenLabs B2B Performance Marketer - Media Buyer**: Requires 3+ years paid campaign management (Google/Meta/LinkedIn). No paid advertising in Ryan CV. Below threshold.
- **ElevenLabs AI Creative Producer**: Requires deep AI image/video/audio prompting portfolio, video editing (Premiere Pro). Creative producer role, not marketing associate. Not a match.
- **Harvey AI (Ashby, Mar 25)**: 100+ roles. 8 UK/EMEA roles — all sales, customer success, legal specialist, GTM enablement. GTM Enablement Manager EMEA requires 3-6yr enablement/training — not Ryan's primary skill set. Legal AI, not consumer AI. No marketing/community roles.
- **Pixaera Founders Associate**: EXPIRED — Ashby API for pixaera shows only Enterprise Account Executive active (Jan 2026). FA listing still appears on aggregators but role gone. Always verify via api.ashbyhq.com/posting-api/job-board/pixaera.
- **Casca AI**: All roles SF-only. No UK roles. FA role now shows only SF engineering/product/deployment.
- **Founding Operator role type (Mar 25 launch)**: Zero verified jobs in founding-operator directory. Artificial Societies and Jack & Jill roles are in founder-s-associate (legacy). Direct career pages not productive for founding-operator — large AI companies don't use this title.

## Scoring Notes
- When no separate "preferred skills" section exists in a listing, award 20/20 (no requirements to fail on).
- When user's stated seniority ("Mid-level") conflicts with their years (7 years = Senior per algorithm), use the stated seniority for experience fit calculation.
- JobSpy AI filter: Many jobs from aggregator match "AI" keyword but are not genuine AI companies (Pret A Manger uses "AI" in description accidentally, Salesforce mentions "AI CRM"). Use strict company check: verify company name against known AI company list and read description for genuine AI product signals.
- Score top-level field: Some verified JSON files use `score` at top level, others use `scoring.percentage`. Always check both when calculating totals for _status.json.

## Source Effectiveness (Indeed/Aggregator Channel, Mar 2026)
- **Indeed via JobSpy**: LOW yield for AI startup roles. 313 raw results across 4 role types = 2 net-new verified roles.
- **Indeed best use**: Catching same-day postings from AI startups that cross-post to aggregators. Searchable Community & Cohorts Manager found posted same day (2026-03-03).
- **Indeed AI filter critical**: Most results mention AI in descriptions but aren't AI product companies. Filter by company name having AI signal, not description alone.
- **Omnea FA**: UK listing actually US-based (New York State). Always verify geography for "London" aggregator results.
- **Quaisr**: Founded Apr 2025 posting, still active Mar 2026. Digital twins/simulation AI from Imperial College London.
- **Searchable**: AI search visibility platform (track brand mentions in ChatGPT/Claude/Perplexity). £4M pre-seed. Community & Cohorts Manager £50K, 5 days/week London.

## New AI Company Findings (March 2026)
- **Letty AI** (joinletty.com): Agentic-AI PropTech. AI workers autonomously negotiate rents, book viewings, dispatch tradespeople, reconcile ledgers. Backed by Entrepreneurs First, $5.5M raised. Founders Associate in City of London — score 91. ZipRecruiter listings active (505183712). No dedicated careers page.
- **Magic AI**: Re-listed on Workable (apply.workable.com/magic-careers/j/A897B23B39/) March 2026. Previously removed from BuiltIn London Feb 23. Role appears to recur. Already in verified set.
- **K42**: Retail partnerships network (digital infrastructure for physical retail) — NOT an AI company. Skip.
- **Brickwise Social Media Content Creator**: Requires existing TikTok/YouTube/Instagram audience + going live daily — influencer/creator role. NOT a marketing associate match.

## Builtin Channel Patterns (March 2026)
- **YC Jobs London** returns same Founder Associate roles week-over-week (Fleek, QFEX, Humaans, Mytos CoS). Check before including.
- **Early & Exec newsletter**: No March 2026 issue published as of March 3. Latest remains Feb 16. Always check archive first.
- **ZipRecruiter.co.uk job pages**: Return 403 consistently. Use WebSearch to extract description snippets.
- **Encord Growth Associate - Community**: EXPIRED March 3, 2026. Lever URL (a5fcd85f-c3ad-43d1-ba72-443119ae5eb1) returns 404.
- **aijobs.app**: Timeout consistently. No usable listings for marketing/community roles.
- **Glassdoor listing pages**: 403 on direct WebFetch. Use search snippets only.
- **startup.jobs/locations/london/marketing**: 403 blocked.
- **WebSearch discovery** most productive for Founder's Associate in builtin channel. Query: "AI startup London founders associate March 2026".

## Industry Job Boards Channel Patterns (March 2026 Re-Run)
- **Channel exhaustion**: By March 20, 2026 industry-job-boards channel is fully exhausted. Zero net-new roles found vs Feb 26 run. All productive sources already covered.
- **Melotech Founders Associate**: London-based AI music startup (melotech.ai), backed by Cherry Ventures/Speedinvest. FA role requires "degree from globally top-tier university + 1yr from elite consulting/banking" — not a marketing/community background fit. Score ~50. EXCLUDE.
- **Conveo FA**: Confirmed expired — both YC URL (BgrTF87) and WorkAtAStartup URL (72965) return 404.
- **Linda AI FA**: Re-verified March 20, 2026. Active on StudySmarter mirror until July 6, 2026.
- **Elyos AI**: Series A London AI startup (AI agents for field services, $13M raised). Only engineering roles as of March 2026. No marketing/FA openings.
- **Diligent AI** (godiligent.ai): YC S23, London/Berlin-based, fintech compliance. Only Founding ML Engineer open. 2-person team.
- **Dex (meetdex.ai)**: Founding Growth and Marketing Lead = "Lead" title excluded + San Francisco only. Not UK.
- **topstartups.io aggregator**: International Event Marketing Manager (Adaptive Security) appeared but NOT confirmed on company career page — stale aggregator data. Always verify directly.
- **BuiltIn London /jobs/marketing**: Returns non-AI companies (Notion, FloQast, Taboola, Perk, HPE). Low yield for AI startup marketing roles.
- **startup.jobs/roles/community-manager**: 403 blocked.
- **Aphex Marketing Events Community Manager**: LinkedIn listing expired (301 redirect to expired_jd_redirect). Construction planning platform, not AI.
- **Intangible AI Growth & Community Manager**: San Francisco only (not London).

## Google-Jobs Channel Patterns (March 2026)
- WebSearch discovery is this channel's primary method. Most productive queries: company-specific ("{company} founders associate London 2026") rather than broad role queries.
- **Brickwise** (brickwiseai.com): AI property manager YC F25, London hybrid. Founder's Associate at £35K-£60K + 0.10-0.50% equity. 3+ years required. Score 91. Active on YC jobs board (ycombinator.com/companies/brickwise/jobs).
- **Brickwise Social Media Content Creator**: $400-1000/month contract — NOT a marketing associate role. Excluded.
- **Conveo** (conveo.ai): Founders Associate expired June 2025. Current open roles: enterprise account management only (6+ years, senior).
- **Gradient Labs** (gradient-labs.ai): Only engineering roles. No marketing roles. 3 open positions via Ashby.
- **Decagon** (decagon.ai): All marketing/GTM roles in San Francisco. London role is Agent Product Manager (technical). Ashby API at api.ashbyhq.com/posting-api/job-board/decagon works for listing extraction.
- **HN March 2026 hiring thread**: Engineering-heavy as expected. No marketing/community roles. Use hnhiring.com/march-2026.
- By March 2026, most AI startup FA/community/marketing roles in London are captured in earlier channels. Google-jobs channel yields diminishing returns — 1 net-new role found (Brickwise FA) after exhaustive search.
- **workatastartup.com company pages**: Return empty JS framework. Fetch individual job URLs directly instead.
- **api.ashbyhq.com/posting-api/job-board/{company}**: Works for Ashby companies when direct career page is JS-rendered. Fetches JSON job listings reliably.

## Niche Deep Search Channel Patterns (March 23, 2026)
- **generalist.world**: Useful discovery source for FA roles. Found Arcline (SF — excluded) and linked to Lua AI (YC F25, London). Senja Growth Marketer was remote but NOT an AI company.
- **Glassdoor Founder Associate London**: 210 results, 57 startup-filtered. Low signal — most are non-AI or expired. Specter Labs FA (78 score) found this way.
- **Specter Labs** (tryspecter.com): AI-powered startup data & deal sourcing platform (50M companies, 500M people, funding signals). Founded 2020, ~14 employees, £29-48K FA role. Posted late Feb 2026 via Glassdoor (ID: 1009945904014). Apply: careers@tryspecter.com (email only, no ATS). Ryan overqualified (targets 1-2yr, Ryan has 6yr). NOT a core AI product company — partial industry match (9/15). Score 78/100.
- **Fyxer AI** (fyxer.ai): Founder/Exec Associate deactivated January 5, 2026. Do not include in future runs.
- **Lua AI** (YC F25, heylua.ai): Mid-market AI agent platform. 0 jobs on YC as of March 23. StudySmart mirror listings appear active but are stale. Do not include.
- **Conveo Performance Marketer (Multi-Channel)**: £60-120K, London/NY. Role is PAID ADVERTISING (Google Search, YouTube, Meta, Reddit) — requires "proven track record scaling paid channels." No paid advertising in Ryan CV. Score ~25/100. Exclude.
- **Conveo Social Media Manager**: NY-primary per prior research. Still active on WelcomeToTheJungle.
- **Accel/Balderton/Index/EF portfolio job boards**: JS-rendered or return unfiltered results. Low yield for FA/marketing specifically without manual filtering. Not productively searchable via WebFetch.
- **Adaptive Security**: Cybersecurity AI ($81M Series B, Nvidia/a16z). No marketing roles on Ashby as of March 23 — BDRs and CSMs only. No Event Marketing Manager (topstartups stale).
- **Kernel AI**: 8 open roles in London — all engineering, sales, product. No FA or marketing roles.
- **Paid AI** (London, $21.6M seed Lightspeed): AI agent billing/revenue infrastructure. No open marketing/FA roles visible on BuiltIn.
- **London AI Hub Marketing & Operations Associate**: Expired July 29, 2025. Do not include.
- **INCA Solutions GmbH FA**: Berlin-based (not London). Excluded.
- **Arcline YC W26 FA**: San Francisco/New York only. Excluded.
- **PolyAI**: Only 1 job open (not marketing/FA). Series D $86M. Marketing roles not current.
- **Jack and Jill AI**: All roles Founding-level (£100-240K). Head of Growth excluded.
- **EF (Entrepreneurs First) portfolio.joinef.com**: Returns general listings (Passfort, Omnipresent). Not AI-specific and requires manual browsing.
- **topstartups.io/jobs AI London**: Shows only 1 marketing role per page fetch — low yield for batch discovery.
- **Channel overall**: 1 net-new verified role (Specter Labs FA 78) from exhaustive deep search. London FA market is genuinely saturated — most fresh sources have been covered across 8+ prior channel runs.

## LinkedIn Discovery Channel Patterns (March 24, 2026)
- **Channel result**: 0 net-new verified roles across all 4 role types. Channel exhausted.
- **site:linkedin.com/jobs queries**: Return aggregate category pages only — no individual listings fetchable. Low signal.
- **LinkedIn job view URLs**: Most return 404 or redirect to expired_jd_redirect when fetched directly.
- **YC Jobs London board** (ycombinator.com/jobs/location/london): Most productive LinkedIn-adjacent source. Full listings extractable. Revealed Artificial Societies (already in set), Corgi Insurance Founding BDR London.
- **Conveo Social Media Manager** (YC S24): Active on YC jobs (posted Feb 10 2026, $80-120K USD) but has "US citizen/visa only" visa requirement — NOT viable for UK applicant. NY-primary confirmed again.
- **Corgi Insurance Growth Marketer**: FILLED — LinkedIn post announces Josh Jung as hire. YC URL returns 404. Do not re-check.
- **Humanloop**: Acquired by Anthropic (March 2026). No independent hiring. Do not check.
- **Robin AI**: Current Ashby API shows talent pool + NYC engineering only. No London marketing roles.
- **Haiper AI Marketing Manager**: Posted Jan 2024, expired Jan 29 2024. WelcomeToTheJungle explicitly "no longer available". Do not re-check.
- **Unitary AI** (virtual agents, automation): Workable shows ML engineering + Senior AE only. FA from LinkedIn listing (job ID 3541951906) is old/expired. No community/marketing.
- **PolyAI Greenhouse** (March 24 check): 15 roles — all engineering, sales, AE, CSM. VP Product Marketing is US only. No community/marketing in London.
- **Stream Growth Marketing Associate** (LinkedIn 4332554930): EXPIRED redirect. Do not re-check.
- **Channel overall**: All London AI startup community/marketing/FA roles appear captured by earlier channel runs. LinkedIn is structurally poor for this search — aggregated pages not fetchable, individual URLs expire fast.

## Niche Newsletters Channel (March 24, 2026)
- **Early & Exec newsletter HIATUS confirmed (May 5, 2026)**: Most recent issue is Feb 16 2026. Archive shows zero posts after Feb 16 2026. Newsletter has been on hiatus since mid-Feb 2026. No March, April, or May 2026 issues exist.
- **Early & Exec "early roles / 8th april" URL**: Fetches April 8 **2025** issue — NOT 2026. Substack slugs don't include year — always check post date at top. Same for "early-roles-29th-april" = April 29 **2025**. Both confirmed 2025 via fetch + archive verification.
- **April 2025 issues (8th and 29th) reviewed May 2026**: All non-engineering UK roles expired/closed (13+ months old). Perlon AI Founding GTM confirmed CLOSED. Portia AI FA = now Rezonant (Founding Growth Lead, Lead title excluded). Zero qualifying roles.
- **Wondercat AI** (wondercat.ai): AI social media agents platform ("world's first social media agent"). Creates reels/slideshows/video ads using Sora2, Kling 3. Raised $4M. London in-person. Founder Associate at £40-60K. Score 91. Glassdoor job ID 1009992996372. Selection: fit interview + test task + meet all founders. Contact: contact@wondercat.ai.
- **Rezonant** (rezonant.app): Rebrand of Portia AI. Emma Burrows (ex-Stripe UK CTO, General Catalyst + Firstminute). AI software delivery orchestration layer between vision and engineering. Founding Growth Lead at £50-80K — EXCLUDED on Lead title. Already has Vincenzo Bianco as Founder's Associate. Contact: hello@rezonant.app.
- **Glassdoor "founders associate startup London"**: 57 results. Wondercat AI found this way. Productive discovery method for FA roles alongside newsletter monitoring.
- **generalist.world/jobs**: Lists Lottie Founding GTM (already verified), Wise Community Manager (fintech excluded), Saturn YC S24 GTM Lead (Lead excluded). Useful but mostly already-covered roles.
- **topstartups.io/jobs/?job_location=London&job_role=marketing**: Returns Omnea Founding Growth Marketing Lead (Lead excluded) and Adaptive Security CSM (wrong role type). Low yield.
- **Jack and Jill AI Founding Operator**: Already verified at 92/100 in exhaustive-fa-search channel (March 23). Do not re-verify.
- **HN Who Is Hiring March 2026 (hnhiring.com/locations/london)**: Engineering-only. Zero non-technical London roles. Confirmed across multiple runs — skip for marketing/community/FA searches.

## Niche Newsletters Channel Patterns (March 2026 Run)
- **Early & Exec March 18 issue** (earlyandexec.substack.com/p/early-roles-18th-march): Contains Kota FA (insurance, not AI), Light.inc AE/marketing (AI finance — Senior level excluded), engineering-heavy otherwise. No UK AI marketing/community roles.
- **Early & Exec March 25 issue** (earlyandexec.substack.com/p/early-roles-25th-march): Contains Candosa FA (business formation SaaS, not AI), 8returns FA (Berlin), Granola engineering/design. No UK AI marketing/community roles.
- **Kota** (kota.io): Insurance/benefits fintech. NOT an AI company. jobs.ashbyhq.com/kota shows current openings — Founders Associate NOT currently listed as of March 2026. Newsletter listing may have been stale or filled.
- **Candosa** (candosa.com): Business formation platform for France/Europe. NOT an AI company. Founder's Associate is Remote Europe, not UK-specific.
- **Melotech** (melotech.ai): Media/entertainment AI (music/video). Primary Ashby listing is Berlin. ZipRecruiter shows London but inconsistent. Requires top-tier university + management consulting/IB — profile mismatch for Ryan.
- **Fyxer AI** (fyxer.ai): London AI productivity startup ($30M ARR). jobs.ashbyhq.com/fyxer — only Lifecycle Manager (CRM) in marketing as of March 2026. Communications Marketing Manager (£70-90K) on ZipRecruiter appears stale/filled.
- **Granola AI** (granola.ai): London AI meeting notes ($250M valuation, $67M raised). Community Manager is SF-only. jobs at granola.ai/jobs — London roles are engineering and Account Executive only.
- **Light.inc** (light.inc): AI-native financial platform (multi-entity accounting). London office, $30M Series A. Senior Growth Marketer exists but "Senior" excluded. AE role is sales (Account Executive).
- **Ema** (ashbyhq.com/ema): Social Media & Community Manager is US Remote only. Not UK-eligible.
- **Peec AI** (ashbyhq.com/Peec): Community Manager is Berlin on-site only. Not UK-eligible.
- **Tracebit Founder's Associate**: Application deadline March 7, 2026 — now expired. Do not include in future runs.
- Newsletter channel overall: 0 net-new verified roles from March 2026 run. Cumulative: 2 verified roles ever (Phyron AI 93, Tracebit 74 now expired). Other channels far more productive.
- **March 23 re-run**: No new Early & Exec issue between March 20-23 (next ~April 8). Sana Labs GTM Associate (London-eligible) excluded — acquired by Workday Sept 2025 for $1.1B. Intangible AI Growth & Community Manager confirmed SF-only. Fyxer AI Communications Marketing Manager confirmed stale (not on Ashby). 0 net-new roles.
- **Sana Labs**: Acquired by Workday September 16, 2025. GTM Associate role still posted but company is Workday subsidiary. Do not include in future runs.

## Web-Search Discovery Channel (March 23, 2026 Re-Run)
- **0 net-new roles** across all 4 role types. Channel fully exhausted by March 23.
- **Artificial Societies** (YC W25, societies.io, London): Founding Operator £60-80K. Genuine AI (persona simulation for enterprise market research). Job description unavailable on any source. "New grads ok" = Ryan overqualified. Excluded. Not mapped to FA/community/marketing.
- **Paraglide AI** (paraglide.ai, $5M seed Bessemer, London): AI agents for AR automation. Sales roles only (AE, SDR). No marketing/community openings.
- **Ankar AI** (ankar.ai, $20M Series A Atomico, London): AI patent platform (IP/LegalTech). Not core AI product company. Founding GTM is enterprise sales-focused, not generalist.
- **Jack & Jill AI** (jackandjill.ai, $20M seed London): Conversational AI for hiring. All roles Founding-level (£100-240K). Head of Growth title excluded.
- **Conveo Social Media Manager**: NY-primary, requires 10,000+ personal social followers — influencer requirement. Not Ryan's profile.
- **LangChain Head of Field Marketing EMEA London**: Head of title excluded.
- **Profound Engagement Manager London**: Expired March 5, 2026.
- **Plinth FA**: Charity/govtech tools. Not AI company.
- **Scope AI FA**: Pre-seed industrial inspection AI. Not core AI product. No formal posting.

## Re-Verification Results (2026-03-20)
See [re-verification-march-2026.md](re-verification-march-2026.md) for full details. Summary:
- **8 roles expired** in 2-4 weeks: Synthesia CM, Encord CM, Brickwise FA, Dex FA, Tracebit FA, Ellipsis FA, Limio MA, Propel MS.
- **FA roles fill fastest** (2-3 weeks). Apply within days of finding.
- **TheHub expiry dates unreliable** — Synthesia showed Sept 2026 but was already removed from Ashby/Greenhouse.
- **Magentic URGENT** — valid to April 3, 2026 only.
- **URL fixes**: Scandit → ZipRecruiter 501905932; Seamflow → Ashby fcabd41c.

## JobSpy Script Patterns (March 20, 2026 — 10 queries, 353 raw results)
- **Glassdoor**: 400 errors throughout — location not parsed for UK. Consistent with prior run.
- **LinkedIn**: Primary active source. LinkedIn job view URLs (linkedin.com/jobs/view/{id}) work reliably for full description extraction.
- **Indeed UK**: Partial results. uk.indeed.com/viewjob?jk= URLs return 403 on WebFetch — use Greenhouse/Ashby/company career pages instead.
- **Net new verified**: 4 roles (Zettafleet FA 79, Topsort FMS EMEA 76, Meroka AI Growth Marketer 72, Writesonic Growth Marketer 66 below threshold).
- **Zettafleet** (zettafleet.com): LLM training infrastructure (distributed training across datacenters). Cambridge scientists, came out of stealth Feb 23, 2026. FA salary £70-90K + equity. Marketing/PR/community building explicitly listed as valid primary specialisation. LinkedIn job 4380369303 active.
- **Topsort** (topsort.com): AI-powered retail media AdTech, 40+ countries. Greenhouse URL job-boards.greenhouse.io/topsort/jobs/5157221008. Posted March 19 — very fresh.
- **Meroka** (meroka.com): AI healthcare startup. Apply URL: ats.rippling.com/meroka/jobs/d3340e6f. Claude fluency non-negotiable. Application requires 5-7min video + prototype.
- **Writesonic** (writesonic.com): YC-backed GEO/AI search. BuiltIn confirms UK-eligible remote. builtin.com/job/growth-marketer/7983881. 4 months old — may be near closure.
- **Non-AI false positives**: Oneleet (cybersecurity compliance, not AI), Moving Mountains (food tech), watchTowr (cybersecurity), Fiskl.AI Growth Marketer (5 months old/stale).
- **Native FA**: Recent graduate 2025/2026 only — automatic exclude for Ryan.
- **ElevenLabs Developer Relations Engineer**: Full-stack engineering role (demos, code), not marketing/community. London-eligible but wrong role type.

## JobSpy Aggregator Patterns (March 20, 2026 Run — 14 queries, 335 raw results)
- **Glassdoor**: 400 errors throughout — location not parsed for UK. Glassdoor effectively dead for UK JobSpy queries.
- **Indeed + LinkedIn**: Active sources. 335 unique jobs from 14 queries. 4 net-new verified roles.
- **New AI companies found**: Magentic (AI agent supply chain, Sequoia, London, £90-100K, founding growth hire), Prolific PMM AI (UK remote, Greenhouse active), Improbable Social Media Creator (web3/AI venture builder, £67-81K, London full-time), StoryKeeper FA (AI interviews, early-stage).
- **Aion Growth Engineer**: Location ambiguous. BuiltIn SF says San Francisco (in-person). Indeed/ZipRecruiter UK list London. Role description mentions "Bay Area meetups" as primary events. EXCLUDE until confirmed UK.
- **Taptap Send FA**: 6-10yr requirement + fintech (not AI product). Exclude.
- **Tessl Marketing Manager Demand Gen**: 4-8yr demand gen / paid acquisition — NOT in Ryan CV. Score 60. Exclude.
- **Improbable CMO Associate**: 7+ years marketing leadership (not community/content). Score 56. Exclude.
- **Jack & Jill** posts roles for many London startups — check for nPlan PMM, Marloo GTM, Letty FA. nPlan PMM not on nPlan careers page — may be stale. Marloo GTM is demos/sales not marketing.
- **WelcomeToTheJungle (Otta)**: Works for job listings. Magentic Founding Growth Marketer confirmed active at app.welcometothejungle.com/jobs/8oCuO_LE.
- **Prolific Greenhouse**: Main Greenhouse board (/prolific) doesn't list PMM AI but individual URL (jobs/4793933101) is active. Always try individual Greenhouse URLs from JobSpy even if not on main board.

## Industry Job Boards Channel Patterns (March 24, 2026 Re-Run)
- **Channel confirmed exhausted** for 5th consecutive run. Zero net-new verified roles.
- **Profound** (tryprofound.com): AI search visibility platform ($35M Series B Sequoia, King's Cross London). "Engagement Manager - London" is Customer Success/Account Management (2-3yr CS requirement), NOT marketing. jobs.ashbyhq.com/Profound is JS-rendered — use WebSearch to find role details. Exclude from future marketing/community searches.
- **Saturn** (YC S24): AI-powered compliance/back-office for wealth managers. GTM Lead London (£50-80K) — "Lead" title exclusion. Ignore in future FA/marketing searches.
- **Corgi Insurance** (YC S24): AI-native full-stack insurance carrier for startups, $108M raised. Growth Marketer role expired (404 on YC URL). Ex-Founder London role is US visa only + sales. SF-headquartered. Future runs: do not attempt until new London marketing role confirmed.

## Jill Job Board Channel (March 23, 2026)
- **Jack & Jill Ashby board** (jobs.ashbyhq.com/jack-jill-external-ats): 237 client company roles. API works via POST to /api/non-user-graphql with browser-like headers. Use jobBoardWithTeams query — jobPostings is on the board level (NOT on team level). Single job: use `jobPosting(organizationHostedJobsPageName:, jobPostingId:)` not `jobPosting(id:)`.
- **143 UK/London jobs** from 237 total. 37 match target keywords after exclusions. 4 verified above threshold.
- **nPlan PMM**: Series B AI (GV + DeepMind founder), £70-80K, construction forecasting. Score 81. Best find from this channel.
- **Godiligent.ai GTM Associate**: YC W24, fintech compliance AI, £35-50K, 1-2yr req (Ryan overqualified). Score 74.
- **Marloo GTM Associate**: AI-native fintech (financial advisers), £40-60K, 2+ yrs. Score 73. Demo/sales-heavy.
- **Centuro Global Content Marketing Manager**: £30-60K, global mobility SaaS with AI component (NOT core AI company). Score 70. Industry score capped.
- **Tunic Pay Growth & Commercial Strategy**: Score 63, BELOW THRESHOLD. Requires consulting/BizOps/enterprise banking background not in Ryan CV.
- **Seal.run FA**: £40-60K — already scored 62 in LinkedIn channel. Requires coding skills. Confirmed below threshold, do not re-score.
- **Board composition**: Mostly engineering roles. Sales/BDM roles outnumber marketing. True marketing/community roles sparse. Filter strictly by company AI product status (many are non-AI or AI-adjacent only).

## Web-Search-Discovery Channel Patterns (March 24, 2026 Re-Run)
- **Channel confirmed exhausted** for all 4 role types. Zero net-new verified roles above threshold.
- **AutogenAI Demand Generation Specialist**: Score 65/100, BELOW threshold. Greenhouse ID 5060057008, £50-65K, London hybrid, published Feb 25 2026. Core gap: paid media expertise (LinkedIn Ads, Google Ads) and HubSpot workflows are primary requirements NOT in Ryan's CV. AutogenAI = UK's fastest growing GenAI company (AI for bid/proposal writing). Future runs: only include if Ryan adds paid media experience.
- **hyperexponential ABM Manager**: EXPIRED Dec 15, 2024. Do not include in future searches.
- **Omnea Founding Growth Marketing Lead**: "Lead" title excluded. Active through April 23, 2026. 7+ years B2B performance marketing required. AI-native procurement platform, London hybrid.
- **Granola Content Lead**: "Lead" title excluded. Active London role. Granola = AI meeting notepad ($43M Series B, Series B-stage, Old Street London).
- **Granola Founding Marketer**: EXPIRED March 10, 2025. Already filled. Do not re-attempt.
- **PolyAI Community Manager**: WebSearch snippets reference this role but Greenhouse job board shows 15 current roles with NO community manager. Stale snippet — role does not exist. Do not attempt in future runs.
- **Lovable**: Community Program Lead is Stockholm in-person only. "Lead" title also excluded. Lovable is strong AI company (AI makes software from English) but no UK marketing roles.
- **YC W26 batch (196 companies, ~60% AI)**: No London-based FA/marketing roles visible from W26. Most are SF-based. Sitefire (marketing suite for agentic web) is US-only.
- **Fleek FA People**: HR/people operations role — requires 1-5yr payroll/HR ops (Deel, Remote). Not a generalist FA. Do not classify as FA in future.
- **Axle Energy FA**: Energy decarbonisation. NOT AI company. Industry mismatch. Exclude permanently.
- **Bunch FA UK**: EXPIRED May 2025. FinTech investment tech, not AI. Remove from future searches.
- **generalist.world/jobs**: Active discovery source. Found Lottie GTM (Lead title, excluded), Wise Community Manager (fintech, excluded), Saturn GTM Lead (Lead excluded), Metadvice (healthcare AI, CS role not marketing). Worth checking monthly.
- **seedtable.com London AI list**: 69 companies listed. Top funded are Wayve, Synthesia, Revolut (not AI), Quantexa, PolyAI. Useful for company discovery but no direct job listings.

## LinkedIn Channel Patterns (March 25, 2026 Run)
- **Alaro** (alaro.ai): AI-native law firm, $9M raised ($2M pre-seed + $7M seed, tier-1 US VC). Founders' Associate London on-site, posted Feb 19, 2026. Apply via jobs.ashbyhq.com/alaro/3ad71d5f-10bc-46ec-a5b3-0f37c3bfa796. Score 84. Generalist FA role (ops, growth, product/AI workflows, people). Main gaps: no legal ops specificity, no formal recruiting. Not agentic AI.
- **Alaro Founding Growth Lead**: "Lead" in title — excluded. Same company as above.
- **Finmile Founding GTM Operator**: AI-powered logistics SaaS, $38M Sequoia. City of London, March 9, 2026, £36-60K, remote/flexible. Requires logistics/ecommerce experience not in Ryan CV. Score ~55. EXCLUDE.
- **Jack & Jill Founding Operator LinkedIn listing** (4257447913): EXPIRED as of March 25 — redirects to expired_jd_redirect. Role was already in verified set from exhaustive-fa-search channel.
- **Founding-operator role type**: First LinkedIn run for this type. LinkedIn search for "founding operator" in London returns very few results (Jack & Jill expired, Bustem non-AI, Hadrius NY). Most genuine founding-operator roles from London already captured in founder-s-associate verified set.
- **Superfluid Community Manager**: Crypto/Web3 asset streaming — NOT AI product company. Exclude.
- **TimesOfAI Community Manager**: AI news platform — NOT AI product company (does not build AI products). Exclude.
- **Conveo Social Media Manager** (YC S24): £64-96K USD (listed on YC board as well). London listed but NY-primary confirmed. Personal social following requirement (10,000+) — not Ryan's profile.
- **societies.io/careers**: Job description page returns no job listing content — careers page is JS-rendered. Use YC job board URL instead for Artificial Societies.
- **generalist.world/jobs**: Returns operations/ops roles for non-AI companies. Low yield for AI-specifically-required roles.

## Google-Jobs Channel Patterns (March 25, 2026 Re-Run)
- **Net-new verified**: 2 roles (Clay Founding Marketer EMEA 74, Humaans Founder Associate 87).
- **Clay Labs** (clay.com): AI-powered GTM platform. $5B valuation (Jan 2026 tender offer). $100M Series C at $3.1B (Aug 2025). Uses AI agents for sales prospecting and outreach. Customers: Anthropic, Cursor, Canva, OpenAI, Notion. Founding Marketer EMEA (London, Remote), deadline March 31, 2026. Score 74. jobs.ashbyhq.com/claylabs/9724f8a6-0e59-4488-b3e1-110760d478c3. Not previously in scope.
- **Humaans** (humaans.io): YC-backed AI-powered HRIS. "Athena" agentic AI layer automates HR/IT/Finance/Operations workflows. YC-backed, Lachy Groom, founders of Slack/Figma/Shopify. Founder Associate, London Chancery Lane in-person (Mon/Tue/Thu), £36-60K + equity. Score 87. Posted Feb 4, 2026, valid May 5, 2026. jobs.ashbyhq.com/humaans. High fit for Ryan's direct FA background.
- **Mayday** (getmayday.com): Finance automation (Xero/QuickBooks). NOT an AI company. Founder Associate requires accounting/finance background explicitly. Exclude permanently.
- **Granola Operations Generalist**: Referenced in "Operate With Purpose" newsletter but NOT on Granola's careers page (verified via BuiltIn London March 25, 2026). Stale newsletter data. Do not include in future runs.
- **Operate With Purpose newsletter**: operatewithpurpose.substack.com. Useful for UK operator/FA roles. Found Humaans FA this run. Also lists Brickwise Operations Lead (already in set), Anthropic CSM (wrong role type).
- **Founding-operator: channel exhausted** — no net-new roles beyond what's in founder-s-associate. All UK founding-operator roles appear captured. AgentMail/Idler founding ops are SF-only.
- **Clay deadline CRITICAL**: March 31, 2026. Must apply before end of month.

## Builtin Channel Patterns (March 25, 2026 Run)
- **Early & Exec March 25 issue** (earlyandexec.substack.com/p/early-roles-25th-march): Published March 25, 2026. Exclusively engineering roles (Fyxer AI, MorphoAI, MODU Energy, Orbital Materials, flowstate, SAMMY Labs). No founding-operator, community, or marketing roles in London.
- **Early & Exec March 18 issue** confirmed: Engineering-heavy (Granola AE, Helmguard AI, SalesApe AI). Kota FA in London but insurance/benefits — NOT AI company.
- **generalist.world/jobs March 25**: Shows Lottie Founding GTM AI Agents (already in verified set, score 73), Wise Community Manager (fintech excluded), Arcline FA (SF only). Low net-new yield.
- **YC London operations board**: Artificial Societies Founding Operator confirmed active March 25 (£60-80K). Same roles as prior runs.
- **Founding-operator role type**: 3 verified roles from builtin channel run (cross-listings from founder-s-associate). YC London operations filter and generalist.world are best sources for this type.
- **Finmile Founding GTM Operator**: AI-powered logistics SaaS ($38M raised). Requires logistics/ecommerce background — not Ryan's profile. Score ~35. Do NOT include in future runs.
- **Conveo Social Media Manager**: 10,000+ personal social followers required (influencer role). US primary, visa holders only. Permanently excluded — do not re-check.
- **Jack & Jill External ATS board** (jack-jill-external-ats Ashby): All 11 listings are engineering roles only. Not a source for marketing/community/operator roles.
- **Granola Founding Ops Manager** (granola.ai/jobs/foundingops): 404 as of March 25. Role removed. Granola's current London openings: Customer Experience Specialist, Content Lead (excluded-Lead), engineers, AEs.
- **Builtin channel overall**: Fully exhausted for all 4 role types after March 25 run. 0 net-new roles for community-manager, founder-s-associate, marketing-associate. 3 net-new for founding-operator (cross-listings only).

## Indeed Channel Patterns (April 7, 2026 Run)
- **Net-new verified**: 1 role (Elyos AI Founders Associate, score 85). Previous run (March 25, 2026) yielded 0.
- **Elyos AI** (elyos.ai): YC S23, AI customer service agents for trades and field services (answers calls/email/WhatsApp, makes bookings, takes payments, operates CRM). $13M Series A (Jan 2026, Blackbird Ventures + Y Combinator + Pi Labs). ~30% MoM revenue growth. London onsite (Old St Station). Founders Associate supports Co-CEO commercially (GTM, RevOps, pipeline admin, investor updates). Score 85. Posted 2026-04-02. Indeed URL: uk.indeed.com/viewjob?jk=9d026bd01db29af0. Note: role not listed on elyos.ai/careers (uses Workable ATS for engineering) — indeed-only posting.
- **Indeed continues as a "fresh posting catcher"**: Most pipeline roles were already present. Indeed adds value when AI companies post directly to Indeed without updating their own ATS. Check weekly for time-sensitive postings.
- **Tilt Founders Associate**: Consumer commerce/social marketplace (not AI product company). Interesting co-build/AI automation remit but company mission is marketplace not AI. Exclude.
- **Lottie Founding Commercial Associate - AI Agents**: Eliza is AI voice agent for social care (Accel + General Catalyst). Role is full sales cycle (SDR/outbound/commission) not generalist FA. OTE £60-120K with sales structure. Exclude from FA type; could classify as sales role.
- **Kernel Commercial Associate**: AI-native CRM data (RevOps agentic data). Explicitly commission-based outbound sales. Listing states "do not apply if after operations or strategy." Exclude.
- **Cohere Brand Marketing Manager (London LinkedIn listing)**: LinkedIn shows London but Ashby API confirms role is New York/remote only. Always verify London Cohere listings against Ashby — LinkedIn data is stale/inaccurate for Cohere.
- **Flagright**: 3 London roles (Social & Distribution Lead, Marketing Ops & Analytics Manager, Partnerships Channel Sales). Social role has "Lead" in title (excluded). Marketing Ops requires HubSpot/Salesforce analytics expertise (not Ryan's background). Partnerships is channel sales. None qualify.
- **Lucida AI**: Consumer mobile app (AI English conversation practice, $7M). Both roles are paid acquisition specialists (Meta/Google/TikTok). No paid advertising in Ryan CV. Exclude permanently.
- **Okta Early Career Marketing Associate**: 12-month contract. Okta is identity/security (not AI product company). Exclude.
- **uk.indeed.com/viewjob?jk= URLs**: Return 403 on WebFetch consistently — use job description data from JobSpy search output files directly instead of fetching live URLs.

## Builtin Channel Patterns (April 7, 2026 Run)
- **Built In London /jobs/marketing/search/community-manager**: Most productive builtin source for community roles. Returned Metaview Social & Community Manager (AI recruiting, score 88). Use this URL directly in future runs.
- **Metaview** (metaview.ai): AI recruiting agents company. $50M+ raised, Google Ventures. London-based. Active Ashby board at api.ashbyhq.com/posting-api/job-board/metaview. Social & Community Manager (London, remote-eligible) confirmed active April 7, 2026. Score 88. Key gap: video on-camera content not in Ryan's CV.
- **Brickwise Founders Associate**: EXPIRED as of April 7, 2026. Only Social Media Content Creator ($400-1K/month contract) remains on YC jobs page. Do not re-check for FA role.
- **Early & Exec April 8 issue** (earlyandexec.substack.com/p/early-roles-8th-april): Portia AI FA (admin/logistics/EA style — excluded), Kriya FA (fintech not AI), no marketing or community roles.
- **Early & Exec April 15 issue** (earlyandexec.substack.com/p/early-roles-15th-april): Head of Growth roles (excluded), Berlin FAs. No UK marketing/community/FA roles.
- **Portia AI Founders Associate**: Admin/logistics/EA-style role (not strategic FA). £4.4M seed from General Catalyst. Do not include.
- **Omnea Founding Growth Associate**: US-primary (NY State) despite topstartups.io showing London. Permanently excluded.
- **Solve Intelligence Growth Marketer/GTM** (YC S23, London/NYC): AI patent drafting. Score 73 — below threshold. Core gap: paid acquisition (2+ channels) is must-have. £100-250K salary.
- **Ably Product Marketing Manager**: Real-time infrastructure, NOT AI product company. UK remote. Excluded.
- **Metaview Community and Events Manager** (Ashby 58024903): EXPIRED September 22, 2025. Do not re-verify.

## Google-Jobs Channel Patterns (April 7, 2026 Run)
- **Net-new verified**: 3 roles (re-verified from archive: Letty AI FA 91, Linda AI FA 95, Specter Labs FA 78). All for founder-s-associate-priority.
- **Humaans Founder Associate**: EXPIRED — Ashby board no longer lists FA role. Current Humaans: sales, engineering, finance only. Previous score 87.
- **Brickwise Founder's Associate**: Confirmed EXPIRED. YC board now only shows Social Media Content Creator contract. Do not re-check for FA.
- **Linda AI FA**: LinkedIn listing EXPIRED (301 redirect) as of April 7. StudySmarter listing valid through July 6, 2026 — use StudySmarter as authoritative URL.
- **Early & Exec**: No new issues since February 16, 2026. Newsletter on hiatus.
- **HN April 2026 Who Is Hiring**: Engineering-heavy, no marketing/FA/community roles. Consistent with all prior months.
- **Solve Intelligence Growth Marketer/GTM** (London, YC S23): Score below threshold. Paid acquisition is core must-have not in Ryan CV. See also Builtin channel entry (score 73 per that channel).
- **Founding-operator-priority**: Zero results permanently. No AI companies use this title for non-engineering roles. All genuine founding-operator work appears under founder-s-associate.

## Indeed Channel Patterns (May 5, 2026 Run)
- **Net-new verified**: 2 roles (Conduct Founding Brand & Growth 92 in founding-operator-priority; Valence Strategy & Operations Associate 72 in marketing-associate).
- **Conduct** (conductai.com or conduct.xyz): AI OS that absorbs SAP/enterprise complexity, $50M+ Series A, London in-person. Founding brand hire — generalist creative/marketing role, no specific background required. Score 92. Posted April 27, 2026. Strongest match this run.
- **Valence** (valenceapp.com): Already in memory from Feb 2026 as "good match." Finally verified this run. French fluency strongly preferred (gap). 3+ years B2B startup required. Posted March 2, 2026 — 2+ months old. Score 72.
- **Spektr Growth Associate**: AI compliance agents (genuine AI). But role is outbound sales/SDR (pipeline building, outbound sequences), not marketing. Score ~45. Exclude.
- **Heidi Clinical Associate - Growth**: AI Care Partner for clinicians. But role requires clinical/healthcare background (peer-to-peer clinician onboarding by doctors for doctors). Not a marketing role. Exclude.
- **FUKU/Corgi Insurance listings**: Same Corgi Insurance description appears in both founder-s-associate AND founding-operator buckets. Pure admin/ops generalist (EU expansion administration). Score ~50. Exclude.
- **LinkedIn US industrial/factory jobs contaminate founding-operator bucket**: 25/50 jobs in founding-operator-priority bucket are US manufacturing/factory operator roles (Nestlé, Kohler, Parker Hannifin, etc.). JobSpy "founding operator" query matches "operator" in industrial job titles. High noise ratio.
- **Indeed FA bucket UK filtering**: 28/43 jobs in founder-s-associate-priority are US-based LinkedIn listings. Only 15 UK candidates remain after location filter.
- **Ellipsis Marketing FA**: Confirmed excluded for 3rd consecutive run. Marketing agency not AI product company. Feb 2026 posting confirmed stale.

## LinkedIn-JobSpy-FA-Deep Channel (May 5, 2026 Run)
- **Net-new verified**: 0 roles. This was an exhaustive 12-query LinkedIn-via-JobSpy sweep specifically for FA/FO at AI companies in UK.
- **Filter funnel**: 176 raw (12 queries) → 91 unique → 62 after title exclusion → 59 after UK location filter → 42 after company skip → 8 AI company candidates → 0 with FA/FO role type match → 0 above threshold.
- **Key findings**: LinkedIn is saturated for FA/FO roles in UK AI. All genuine AI company FA/FO roles already captured in prior channel runs (Feb-Apr 2026). New queries using different angle terms (generative AI, LLM startup, AI seed startup, AI agents) returned no new companies.
- **Sequence Product Marketer - London**: Genuine AI company (AI revenue agents, $20M Series A, a16z+645V). Active role at jobs.ashbyhq.com/sequence/2354b86d-d72f-4853-99a7-2e3cabbfa26e. BUT: role type is Product Marketer, NOT FA/FO. Belongs in marketing-associate if ever re-dispatched. 2-4yr B2B SaaS, AI tools enthusiasm, creative generalist — good profile match for Ryan. London on-site.
- **Sequence Revenue Associate - London**: LinkedIn listing (job 4379276852) is STALE. Ashby board confirms this role is NYC only. Do not re-attempt.
- **SilverTree Equity Forward Deployed AI Operators**: PE firm (€1B AUM) embedding graduates into portfolio companies. NOT an AI product company. Graduate-level = Ryan overqualified. Do not include in future runs.
- **Contamination pattern confirmed**: "founding operator" queries on LinkedIn return large volumes of US industrial/factory "operator" roles (Nestlé, Kohler, Parker Hannifin). High noise ratio. UK location filter clears these, but initial raw count is misleading.
- **Channel verdict**: LinkedIn-via-JobSpy is fully exhausted for FA/FO. All productive sources covered in prior runs. Do not re-dispatch for FA/FO types.

## Niche Deep Search Channel (May 5, 2026 Run)
- **Net-new verified**: 0 roles. All productive niche sources exhausted or on hiatus.
- **Early & Exec confirmed on hiatus**: Archive shows last issue Feb 16, 2026. No March–May 2026 issues. Fetching earlyandexec.substack.com/p/early-roles-8th-april returns April 8 **2025** issue — NOT 2026. Do not confuse dates.
- **Operate With Purpose confirmed on hiatus**: Last post "Taking a Break" March 7, 2026. No issues since.
- **Humaans Founder Associate**: CONFIRMED EXPIRED — Ashby board (May 5, 2026) shows only Product Design Lead, Software Engineers, Head of Finance. FA role gone. Do not re-check.
- **Clay Labs Founding Marketer EMEA**: CONFIRMED EXPIRED — March 31, 2026 deadline passed. No EMEA marketing roles on Clay Labs Ashby.
- **Granola Community Manager**: San Francisco only — confirmed again. London roles are engineering/AE/design only.
- **Conveo Marketing Associate**: NEW — posted May 4, 2026 on BuiltIn London. "2 Locations Hybrid" (likely Antwerp+London). Description: "content creation, event logistics, customer research." Genuine AI (YC S24, AI market research). Entry-level. Cannot confirm UK-specific location from available data — monitor next run for full spec. Do NOT score without full requirements.
- **Wondercat AI → wonda.sh rebrand**: Wondercat.ai redirects to wonda.sh. No careers page on wonda.sh. Glassdoor listing (1009992996372) still indexed but contact@wondercat.ai likely stale. Role status unknown — skip until company confirms active hiring.
- **Ankar AI "Marketing and Comms Lead"**: London in-office. Lead title excluded. Do not re-check.
- **hnhiring.com May 2026**: 403 blocked. hnhiring.com April 2026: 403 blocked. Pattern: hnhiring.com non-default URLs consistently 403.
- **Decagon**: All SF — confirmed again. No UK roles at all.
- **Sierra**: All US — confirmed again.
- **Peec**: All Berlin — confirmed.
- **Ema**: India/SF only — confirmed.
- **Scope AI**: Ashby board returns empty/header-only. No formal FA posting accessible.

## JobSpy Deep Sweep - Founding Operator & Agent Startups (May 5, 2026)
- **Net-new verified**: 3 roles across 2 role types — Jack & Jill Founding Operator (87), Jack & Jill Founding GTM Operator (85), Mistral AI Marketing Programs Manager (90).
- **Jack & Jill AI** (jackandjill.ai): Agentic AI recruitment startup. $20M seed (Northzone, Initialized Capital, Anthropic angels, Lovable). 15-person team (10 ex-founders). Shoreditch London. Two founding operator roles open May 2026: Founding Operator (£100-180K CS/AM-focused) and Founding GTM Operator (£150K+ new business/sales engine). Both 5 days/week in-person. NOTE: Previous memory entries say "Jack and Jill already verified" — those were for the Jack & Jill AGGREGATOR/EXTERNAL ATS board (external client placements). These new roles are for Jack & Jill's INTERNAL team. Treat as separate entries. Ashby: jobs.ashbyhq.com/jack-and-jill.
- **Mistral AI Marketing Programs Manager**: London/Paris locations both listed. 3+ years program mgmt/consulting/ops/CoS in tech/SaaS/AI. Role is strategic right-hand to marketing leadership — CoS-adjacent, cross-functional coordination. Ryan's FA background is strong match. Master's degree preferred but not required (Ryan has BA). Lever: jobs.lever.co/mistral/59624055-8cc3-43dc-81d4-4f01d77e30c9.
- **FUKU is an aggregator for Corgi Insurance**: All FUKU-branded LinkedIn/Indeed listings (Founding Operator, Business Operations Generalist, Operations Generalist, Chief of Staff Operations) are actually Corgi Insurance roles. Corgi is already in skip list. Do not process FUKU listings.
- **HappyRobot Strategy & Operations**: LinkedIn shows "London" location but Ashby API confirms all S&O roles are in Madrid (not London). LinkedIn location field reflects EMEA office, not job location. Exclude HappyRobot S&O unless Ashby confirms London.
- **Descycle FA**: Deep-tech metals recycling company (e-waste DES chemistry). NOT an AI company. Exclude permanently.
- **Greyparrot Marketing Executive**: £33-36K salary is below £40K minimum threshold. Role is 1-2yr experience level. Exclude.
- **LangChain EMEA Deal Strategy & Operations Manager**: Deal ops role requiring SaaS CPQ/contract/revenue recognition expertise. Not a generalist ops role. Exclude.
- **Normal Computing Biz Ops Finance**: Finance Manager role — requires financial modeling/capital deployment expertise. Not a generalist ops match for Ryan.
- **Jumpstart aggregator listings**: All Jumpstart "Founder's Associate at VC Backed Startup", "Generalist", "AI Generalist", "Operations Associate" listings are for undisclosed companies — cannot verify as AI companies. Exclude for verification purposes.
- **SilverTree Equity Forward Deployed AI Operators**: PE firm (€1B AUM) embedding graduates into portfolio companies. NOT an AI product company. Graduate-level. Exclude permanently.
- **Jack & Jill "Founder's Associate at $4.5M Seed AI startup"**: This IS Jack & Jill themselves (they raised $4.5M with 14x oversubscription). FA role requires MBB/elite finance background (1-2yr). Not Ryan's profile. Exclude FA role; only Founding Operator and Founding GTM Operator qualify.
- **Jack & Jill "Marketing & Content Lead"**: "Lead" in title — excluded per title exclusions.
- **"founding operator" query contamination**: LinkedIn/Indeed queries for "founding operator" return large volumes of US industrial/factory "operator" roles + agricultural operators + UK-based property/estate operators. Location filter removes most; still high noise ratio. Pattern confirmed from multiple runs.

## Lever Agent Startups Deep Channel (May 5, 2026 Run)

- **Lever direct API (api.lever.co/v0/postings/{slug}?mode=json)**: Works for some companies (Encord/CordTechnologies, aeratechnology, levelai, improbable-2). Returns 404 for many (scale, multiverse, faculty, benevolent, luminance, quantexa, intercom — these companies have likely migrated ATS).
- **jobs.lever.co direct WebFetch**: 403 on all company listing pages and individual job pages. Use WebSearch + mirrors (BuiltIn, ZipRecruiter, crane.vc, competitiveenablementjobs.com) instead.
- **Net-new verified**: 1 role (Encord Field Marketing Manager Growth - score 73, marketing-associate).
- **Encord (CordTechnologies on Lever)**: Active London hiring. Field Marketing Manager, Growth (b350d648) posted April 1, 2026. 2-4yr required. $60M Series C. Older Field Marketing Manager UK (f64d87a2, crane.vc) closed July 2025. Use api.lever.co/v0/postings/CordTechnologies for listing extraction.
- **Mistral AI Lever**: JS-rendered main page (403). Individual job pages also 403. API endpoint returns Paris-only business roles. London roles confirmed via WebSearch but all technical or enterprise sales. No UK marketing roles.
- **Valence Lever** (jobs.lever.co/valence/99045f6d): Strategy & Operations Associate still active May 2026 — already in verified set from Indeed channel. Duplicate.
- **11xAI**: Relocated to SF. 0 open jobs as of May 2026. Watch for future openings.
- **Ekimetrics**: Data science consultancy (NOT AI agent company). Campaign Marketing Operations Associate (Paris or London) and Product Marketing Associate exist but company is consulting firm, not AI product. Excluded.
- **Aera Technology**: Associate PMM is Mountain View CA only (hybrid onsite required). No UK marketing roles despite having London office.
- **Anagram Security Founding Marketer**: USD salary ($140-160K), 401K, US benefits — effectively US role despite "worldwide" remote label. Not UK-eligible.
- **Model ML**: Marketing Lead London — "Lead" title excluded. YC-backed AI workspace for investment banking.
- **Groupthink Marketing Generalist**: Scottsdale AZ company, not London despite appearing in searches.
- **Lever Founder's Associate**: Low signal on Lever. Searches return Founders Factory (not AI), vivenu (Germany), Wing (non-UK). AI startup FA roles predominantly on Ashby/Greenhouse.
- **Lever Community Manager**: Zero results for AI company community manager roles in London. Lever is not a productive channel for community management at AI startups.

## YC Work at Startup Deep Channel (May 5, 2026 Run)

- **Net-new verified**: 1 role (Terra API Applied AI Strategist - Market Intelligence 82, in founder-s-associate-priority).
- **YC jobs board (/location/london and /location/united-kingdom)**: Server-side rendered, fully fetchable. Returns ~50 London listings. Primarily engineering. Non-engineering roles: 3 Terra API strategist roles, Solve Intelligence Growth Marketer/GTM, Corgi Insurance Growth Associate (skip list), CoLoop BDR/AE/CSM, Heron Data PM.
- **YC jobs board role-specific URLs (/role/operations/london, /role/marketing/london)**: 404 on /role/X/location format but work as /role/X/london. Operations board shows 8 London roles (mostly account exec + data analyst). Marketing board shows 3 roles (Head of Growth, VP Marketing, Growth Marketer/GTM — all excluded or visa-blocked).
- **WAAS (workatastartup.com)**: Confirmed definitively JS-rendered. All URL patterns return "Software Engineer jobs at Y Combinator startups" header only — no job listings extractable. WorkAtAStartup is not usable via WebFetch for any role type.
- **Terra API Applied AI Strategist** (YC W21, London, £40K-£120K): Genuine AI company (Tyran AI Health Agents, LLM health analysis). Applied AI Strategist = strategy/market research role working directly with founders — classifies as founder-s-associate-priority. 3+ years required, Ryan has 8. No health domain expertise is a gap (impacts preferred score). Score 82.
- **Terra API Founders Associate URL (NGbGJeN)**: Returns 404 — role appears in search index cache but has been removed from YC jobs board. Do not attempt in future runs.
- **Solve Intelligence Growth Marketer/GTM**: "US citizen/visa only" explicit requirement. Ryan is UK national — DISQUALIFIED regardless of skill match. Do not re-score in future runs. (Prior memory entry from April 7 noted score 73 — now confirmed disqualified on visa grounds.)
- **Terra API Video Strategist** (any level, £50K-£150K): Requires video editing portfolio (Premiere, Final Cut, DaVinci, After Effects, CapCut) — creator/editor role, not marketing strategy. Ryan has no video editing background. Exclude permanently.
- **Terra API Partner Strategist**: 6+ years required, enterprise deals focus. Too senior/sales-specific. Excluded.
- **Heron Data** (AI document automation for financial services, London): PM and engineering only. No marketing/FA/community roles. Monitor monthly.
- **CoLoop** (AI copilot for insights/strategy, YC S21, London, 16 people): BDR (£30-60K), AE (£60-80K), CSM (£30-40K). No marketing/FA roles. BDR/AE are sales roles, not target types.
- **Flagright** (AI-native AML compliance, YC W22, London): Marketing Ops & Analytics (HubSpot/Salesforce expertise) + Social & Distribution Lead (Lead title excluded). Neither matches Ryan's profile. Exclude marketing ops permanently.
- **Coinrule** (crypto trading automation, London): Digital Marketing Manager listed in search index but NOT an AI product company (algorithmic trading tool, not AI). Exclude.
- **topstartups.io/jobs AI**: Returns low signal for UK. Only Adaptive Security BDR London and Omnea engineering. Not productive for this channel.

## Recent Launches Deep Channel (May 5, 2026 Run)

- **Net-new verified**: 0 roles. Newly-launched UK AI agent companies are all in engineering-only hiring phase.
- **Trent AI** (trent.ai): Agentic security platform, London, $13M seed April 7 2026 (LocalGlobe/Cambridge Innovation Capital). Co-founded by ex-AWS (Eno Thereska, Zhenwen Dai, Neil Lawrence). Planning GTM expansion but no non-engineering UK roles posted yet. Only listed role: ML Scientist (US-based). No careers page on Ashby/Greenhouse — check trent.ai/careers periodically. Monitor for first marketing/growth hire.
- **Ineffable Intelligence**: London frontier AI lab ($1.1B seed, April 27 2026, Sequoia/Lightspeed). Founded by David Silver (ex-DeepMind). Ashby API returns empty jobs array. Research-only at this stage. Monitor for ops/comms hire when products launch.
- **Gradient Labs** (gradient-labs.ai): AI customer ops for financial services, London. Ashby API works reliably. Event Marketing Manager exists but is NY-only. London roles: AI Engineer, Product Engineer, Security Engineer, AI Delivery Lead, Enterprise AE. No London marketing roles. AI Delivery Lead (£75-95K, London hybrid) is a technical client implementation role — NOT a marketing/FA match.
- **Portia AI** (portialabs.ai): London, AI agent framework, £4.4M seed (General Catalyst). Founder's Associate appeared in Early & Exec April 8 newsletter — confirmed no longer accepting applications. Company has 7 employees, no open jobs on GC job board.
- **Perlon AI**: London, AI outbound sales agents (founded 2023, seed via Haatch). Founding GTM appeared in April 29 newsletter — LinkedIn listing confirms CLOSED/expired. Role was sales-focused (AE-style), not marketing associate.
- **Cosine** (YC-backed, Sovereign AI cohort): London, AI coding agent. Open roles: Senior Developer Evangelist + 4 engineering roles. Developer Evangelist is technical (3+ years software development required). Not a marketing/community match.
- **Callosum**: London, AI compute infrastructure, Sovereign AI equity investment. 4 Staff Engineer roles only. No non-engineering openings.
- **Early & Exec newsletter**: Apr 8 and Apr 29 issues checked. Portia AI FA (closed), Perlon AI Founding GTM (closed/sales-AE). Low yield for genuinely new AI agent companies in London.
- **YC W26 London companies**: Demo Day March 24 2026. No W26 London companies are hiring non-engineering roles at this stage (only Dayjob CSM from P26 batch).
- **UK Sovereign AI Fund cohort (7 companies, April 16 2026)**: Callosum, Prima Mente, Doubleword, Cosine, Cursive, Odyssey, Twig Bio. Only Cosine (agentic), Cursive (stealth agentic), Odyssey (world models) are AI agent adjacent. All engineering-only hiring in UK.
- **Companies to monitor monthly**: Trent AI (first GTM hire imminent), Ineffable Intelligence (first ops hire when public product launches), Round Treasury (London fintech AI, £5.1M seed April 2026 — Agentic Workflow Builder + Autonomous Payroll), inploi (London AI hiring platform, £3.4M April 2026 — expanding marketing team).
- **generalist.world/jobs**: Lists Lottie (skip list), Granola (skip list), Bob W (hotel hospitality — not AI), Metadvice (NHS AI — CS role). Low yield for AI FA/marketing.
- **W26 UK AI companies**: Seeing Systems (modular AI-commanded drones, London) is only confirmed W26 London AI startup. All engineering roles (Founding HW/SW Engineer). No marketing/FA roles expected in near term.
- **YC S25 UK AI companies**: Limited to 3 companies per search results. None of the 3 publicly identified have non-engineering London roles.
- **Channel conclusion**: YC/WAAS channel produces 1-2 net-new verified roles per monthly run for FA/marketing roles. Best approach: fetch /location/london + /location/united-kingdom boards + role-specific /operations/london + /marketing/london. Skip WAAS entirely (JS-rendered). Terra API is the most prolific YC London AI company for non-engineering roles.

## Direct Career Pages Channel (April 7, 2026 Run)
- **Net-new verified**: 1 role (Synthesia Community Manager 91 — file created this run, role active since before March 2026).
- **Synthesia Community Manager status**: Active until September 16, 2026 on TheHub.io. TheHub URL `https://thehub.io/jobs/6917c620cc00a86a102e5026` FAILS validate-schema (path depth heuristic — no hyphens in ID, not a UUID). Use Greenhouse EU URL instead: `https://job-boards.eu.greenhouse.io/synthesia/jobs/4711805101` (passes validation). Apply URL: TheHub link.
- **ElevenLabs April 7, 2026**: All 4 UK-remote marketing roles confirmed still active (Growth Content Writer 87, Growth Generalist 84, B2B Growth Marketing Agents 78, Product Marketing Agents 88). Ashby board API lists only 8 roles and omits these — always verify via direct job URL not board listing.
- **Anthropic April 7, 2026**: New role Influencer Marketing Manager Brand (5174844008, April 3) — SF/NYC only, US-only role. No new UK/EMEA marketing roles since March 25. All 6 London EMEA marketing roles remain Lead-titled or 10+ years.
- **Channel fully saturated**: All 35 companies checked. No new qualifying UK roles found beyond Synthesia file creation. Direct-career-pages channel has covered all productive sources since February 2026. Diminishing returns expected on future runs unless Anthropic EMEA expansion continues.
- **Founder-s-associate-priority and founding-operator-priority**: Both new role types yield zero from direct-career-pages. Large established AI companies do not post these titles. Expected result — these role types rely on other channels (YC Jobs, JobSpy, niche newsletters).

## VC Portfolio Deep Channel (May 5, 2026 Run)

- **Net-new verified**: 0 roles. VC portfolio job boards are JS-rendered (Consider/Getro framework) and show only unfiltered partial data regardless of URL query params.
- **Accel (jobs.accel.com)**: 25,262 jobs listed. No filter by location/role extractable via WebFetch. Returns unfiltered front-page listings (Decagon Strategic Account Director, etc.). Not usable for targeted search.
- **Atomico (careers.atomico.com)**: 2,048 jobs listed. Same issue — front-page listings only. JS-rendered, no filter result.
- **Balderton (careers.balderton.com)**: Consider-powered. No visible listings via WebFetch.
- **Bessemer (jobs.bvp.com)**: Consider-powered. No visible listings.
- **Sequoia (jobs.sequoiacap.com/jobs/europe)**: Consider-powered. No visible listings.
- **Entrepreneurs First (portfolio.joinef.com/jobs)**: Shows some listings but mostly non-AI (Passfort, Cleo DS roles, Nivoda). Not productively filterable.
- **Octopus Ventures (talent.octopusventures.com/jobs)**: Returns ~20 visible listings (mostly non-AI: Secret Escapes, Seatfrog, Semafone). Seatfrog Lifecycle Growth Marketing Strategist remote is fintech, not AI.
- **Antler (careers.antler.co/jobs)**: Shows ~20 listings, mostly non-UK or engineering (Capsa AI engineers London, Peec AI Berlin, NOVO remote).
- **Firstminute (jobs.firstminute.capital/jobs)**: Shows 431 total. Visible roles are Mistral AI (Paris), n8n (EU remote engineering), Wayve (SF). No UK marketing/FA.
- **Hoxton Ventures**: Both hoxtonventures.com/jobs and jobs.hoxtonventures.com are JS-rendered. No listings extractable.
- **Productive approach**: Extract portfolio company names from VC portfolio pages, then hit each company's career page directly (ashbyhq.com/{slug}, lever.co/{slug}, greenhouse.io/{slug}).
- **Index Ventures AI portfolio (key names)**: Ankar AI (skip), Humanloop (acquired by Anthropic), Wordsmith AI (Edinburgh-only), Deepnote (Marketing Associate USA remote only), /dev/agents, Superlinked, Cartesia, Fireworks AI.
- **Stacks AI** (stacks.ai): Agentic AI for enterprise accounting, London + Amsterdam. Lightspeed/EQT/General Catalyst. $23M Series A. Growth Marketer requires 3-5yr paid acquisition (LinkedIn/Google Ads) — score 69 (below threshold). Founding PMM requires 5-8yr B2B SaaS product marketing + active LinkedIn audience — score 64. Both below threshold. Monitor for junior GTM roles.
- **Wordsmith AI Product Marketing Manager** (Edinburgh): 5 days/week in Edinburgh office, relocation required. Not viable for Cambridge-based Ryan. Edinburgh-only = auto-exclude.
- **Cosine AI Senior Developer Evangelist** (London): "Senior" prefix excluded. Monitor for non-senior DevRel/community role. Company is agentic SWE (Genie product). 12 employees.
- **Anagram Security Founding Marketer**: USD salary ($140-160K), US benefits — effectively US role despite "worldwide remote" label. Score N/A, location fails UK requirement.
- **Trent AI**: Already in memory (line 492). Confirmed no jobs on trent.ai — careers page has no listings. Still in engineering-only phase as of May 5, 2026.
- **Genie AI (genieai.co)**: Open-source legal AI, London. Only Account Executive EMEA roles open via Workable. No community/marketing/FA roles.
- **Gradient Labs**: Already in memory. Confirmed: no London marketing roles. Head of Marketing hire incoming for US only.
- **Ineffable Intelligence**: Already in memory. Ashby returns empty. Research-only stage.
- **Ralio**: 5 employees, engineering-only. Too early for marketing hire.
- **Channel verdict**: VC portfolio deep sweep is LOW YIELD due to JS-rendering of all major VC job boards. True value is discovering portfolio company names and going directly to their career pages. Best method: fetch VC portfolio pages for company names → batch-check Ashby API for each company slug. Index Ventures, Atomico, and Balderton are the most productive VCs for London AI companies, but company-by-company checks are required. All major London AI companies from these portfolios now covered in direct-career-pages channel.
- [Newsletter channel Jun 2026](newsletter_channel_jun2026.md) — Mayday FA (87) only UK hit; Tracebit/Electric Twin now closed; E&E latest still Feb 16; generalist.world ~90%% US

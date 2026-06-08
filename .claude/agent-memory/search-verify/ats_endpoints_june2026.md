---
name: ats-endpoints-june2026
description: Working vs broken ATS API endpoints for direct-career-pages AI companies (June 2026)
metadata:
  type: reference
---

ATS endpoint resolution for the direct-career-pages company list (June 2026). Use these to skip trial-and-error.

**Greenhouse API (boards-api.greenhouse.io/v1/boards/{slug}/jobs) — WORKS:**
- anthropic, scaleai, vercel, gleanwork (NOT "glean" -> 404)
- Broken/404: writer, runwayml, moveworks, ramp, hebbia, cursor (these are not on this Greenhouse slug)

**Ashby posting API (api.ashbyhq.com/posting-api/job-board/{slug}) — WORKS:**
- elevenlabs, synthesia, cohere, dust, harvey, Sierra (capital S), cognition, perplexity (NOT "perplexity.ai" -> 404), replit, poolside, LangChain (capital), character (returns title only sometimes)
- Add ?includeCompensation=true for salary

**Lever API (api.lever.co/v0/postings/{slug}?mode=json) — WORKS:**
- mistral (paginated; partial responses common - all Paris/US AE roles as of June 2026)

**Workable:** Hugging Face -> apply.workable.com/api/v1/widget/accounts/huggingface?details=true works (EMEA roles all engineering/DevRel, Paris-based).

**JS-rendered / 403 (use WebSearch instead):** perplexity.ai/careers (403), cursor.com/careers, cognition.ai/careers, character.ai. Individual jobs.ashbyhq.com/{co}/{uuid} pages often return TITLE ONLY via WebFetch (JS-rendered) - use the posting-API JSON or WebSearch for full description. ZipRecruiter.co.uk = 403 (per prior memory, still true).

**Wayve:** wayve.firststage.co/jobs works. June 2026 London roles all domain ops (fleet/warehouse/policy), no generalist.

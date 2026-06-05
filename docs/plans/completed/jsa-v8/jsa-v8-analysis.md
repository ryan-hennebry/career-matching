# Session Analysis: Job Search Agent V8

## Summary

- **Session duration:** ~15 minutes active interaction
- **Context consumed:** 40%+ by user's own observation
- **5 wins, 6 failures, 3 user corrections**

The agent successfully completed its core mission (found 5 strong matches, generated briefs), but burned context inefficiently and needed user course-correction on multiple occasions.

---

## What Went Well

### 1. Onboarding flow worked smoothly
CV was read via docx skill, skills extracted, and constraints confirmed in 3 exchanges. Profile populated correctly in context.md.

### 2. Brief generation was high quality
The 5 briefs produced (Starknet, DIA, Polymarket, Prospect, Linjer) contained actionable content: match rationale, CV tailoring points, cover letter angles.

### 3. Seniority filtering was added correctly
When user said "exclude all senior roles", agent immediately added `exclude_titles` list to context.md.

### 4. Agent did honest fit assessment when challenged
User asked "are you sure I meet the requirements?" - agent re-read descriptions and provided candid fit ratings (No/Stretch/Good).

### 5. Agent acknowledged limitations on sources
When user pointed out missing sources, agent immediately expanded to crypto job boards rather than defending the initial approach.

---

## What Failed

### Failure 1: Context burn from unfiltered job descriptions

**What happened:** Agent pulled full job descriptions (2500+ chars each) for 10+ jobs into context before filtering, most of which weren't relevant.

**Root cause:** No pre-filtering strategy. JobSpy returned raw data, then agent read everything into context to filter.

**Principle violated:** Agent-native efficiency - the system should minimize context consumption.

**Fix type:** Implementation

**Specific fix:** JobSpy script should accept `--exclude-titles "Senior,Lead,Director"` flag to filter server-side before returning results to agent.

---

### Failure 2: Initial search returned unsuitable seniority levels

**What happened:** First search returned "Marketing Manager" roles at £70K+ (senior level), which user had to explicitly say "exclude all senior roles."

**Root cause:** Agent didn't infer from user's "junior/mid-level" statement and £35K minimum that senior-titled roles would be inappropriate.

**Principle violated:** Anticipate user needs - agent should infer constraints from context.

**Fix type:** Implementation (CLAUDE.md update)

---

### Failure 3: Single source assumption

**What happened:** Agent only searched LinkedIn/Indeed/Glassdoor via JobSpy. User had to point out "why are you only using jobsearch and not any other methods?"

**Root cause:** CLAUDE.md mentions "WebFetch for company career pages" but doesn't list specialty boards for the user's target industries.

**Principle violated:** Complete the mission - agent should exhaust relevant sources before declaring results.

**Fix type:** Architectural (context.md should store preferred sources)

---

### Failure 4: python vs python3 command

**What happened:** `python scripts/jobspy_search.py` failed with "command not found: python". Agent had to recover by finding python3.

**Root cause:** Script uses `/usr/bin/env python3` shebang but agent invoked with `python`.

**Principle violated:** None (recoverable error).

**Fix type:** Implementation (CLAUDE.md should specify `python3`)

---

### Failure 5: No context management strategy

**What happened:** User observed "40% context used, out of smart zone." Agent acknowledged the problem but didn't have a built-in strategy to prevent it.

**Root cause:** No guidance in CLAUDE.md about context efficiency or two-pass strategies.

**Principle violated:** Agent-native resource management.

**Fix type:** Architectural (add context management section to CLAUDE.md)

---

### Failure 6: Agent asked "what else can you do?" instead of suggesting high-leverage action

**What happened:** After generating briefs, agent listed 15+ capabilities without prioritizing. User had to ask "what would be most high-leverage?"

**Root cause:** CLAUDE.md lacks guidance on proactive next-step suggestion.

**Principle violated:** Proactive assistance - agent should recommend, not just list options.

**Fix type:** Implementation (CLAUDE.md update)

---

## User Feedback / Corrections

1. **"are you sure I meet the requirements?"** - User caught that agent hadn't verified fit before presenting results.

2. **"why are you only using jobsearch?"** - User had to prompt multi-source search.

3. **"what would be the most high-leverage activity?"** - User had to teach the agent to prioritize recommendations.

---

## Specific Fixes

### CLAUDE.md Changes

```diff
 # Job Search Agent

 You find relevant opportunities and prepare application briefs so the user focuses on interviews and decisions, not discovery and prep.

+## Principles
+
+1. **Verify fit before presenting** - Read full job descriptions and assess seniority/requirements match before showing to user
+2. **Exhaust sources** - Search specialty boards for user's industries (stored in context.md), not just LinkedIn/Indeed
+3. **Conserve context** - Filter server-side, store results in files, read summaries only until user confirms interest
+4. **Recommend, don't list** - After completing a task, suggest the single highest-leverage next action (with alternatives)

 ## On Startup

 1. Read context.md for profile and constraints
 2. Scan output/jobs/ for current state
 3. If no profile → ask for CV, extract skills/experience, confirm constraints
 4. Otherwise → show status, suggest next action

 ## Capabilities

-- Job search: `scripts/jobspy_search.py` for major boards (invoke via Bash), WebFetch for company career pages
+- Job search: `python3 scripts/jobspy_search.py` for major boards, WebFetch for specialty sources (per context.md)
 - Web research: WebFetch for company context, hiring manager lookup
 - File operations: JSON to output/jobs/, Markdown to output/briefs/ and output/digests/

+## Context Management
+
+To stay in the "smart zone":
+1. Store raw search results in output/jobs/*.json, not in context
+2. Read one-line summaries (title/company/location) first
+3. Only fetch full descriptions for jobs user confirms interest in
+4. Use Task tool for brief generation if context is tight

+## Sources Configuration
+
+Read `context.md ## Sources` for industry-specific job boards. For crypto: cryptocurrencyjobs.co, web3.career. For startups: wellfound.com, workatastartup.com.
```

### context.md Structure Addition

```diff
 ## Industries
 - Crypto
 - AI
 - Tech
 - Startups

+## Sources
+# Specialty boards for target industries
+crypto:
+  - https://cryptocurrencyjobs.co
+  - https://web3.career
+  - https://cryptojobslist.com
+startups:
+  - https://workatastartup.com
+  - https://wellfound.com
+newsletters:
+  - https://earlyandexec.substack.com

 ## Dream Companies
```

### scripts/jobspy_search.py Update

```diff
+ parser.add_argument("--exclude-titles", help="Comma-separated title keywords to exclude")
...
+ if args.exclude_titles:
+     exclude = [x.strip().lower() for x in args.exclude_titles.split(",")]
+     results = [j for j in results if not any(ex in j.get("title", "").lower() for ex in exclude)]
```

---

## Recommended Next Step

**Run `/plan`** to update implementation steps.

The failures are primarily implementation issues (CLAUDE.md guidance, script flags, context management) rather than architectural. The core design (trust agent judgment, hard constraints only) is sound.

Priority fixes:
1. Add "Principles" section to CLAUDE.md with verify-before-present and exhaust-sources guidance
2. Add "Context Management" section to CLAUDE.md
3. Add "Sources" section to context.md with specialty boards
4. Update jobspy_search.py with `--exclude-titles` flag

---

## Session Metrics

| Metric | Value |
|--------|-------|
| Jobs searched | 375+ raw |
| Jobs after filtering | ~120 |
| Strong matches | 5 |
| Briefs generated | 5 |
| User corrections | 3 |
| Context consumed | 40%+ |

---

## Handoff

Analysis saved. Recommended to run `/plan` to incorporate fixes into V9 implementation plan.

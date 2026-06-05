# Session Analysis: Job Search Agent V12

## Summary

7 wins, 8 failures, 3 edge cases. V12's core search-verify pipeline worked well — 6 role types searched, 44 jobs verified, cross-role deduplication ran, briefs generated. The session broke down severely at the PDF/email delivery stage: subagents ignored the frontend-design skill, each picked different rendering approaches (fpdf2, reportlab, Playwright), produced inconsistent aesthetics, and the user had to ask 4 times for proper design before the session ended with "we'll need to improve this massively for future versions." The presentation format also failed — hyperlinked titles don't render in CLI, and the first presentation showed raw URLs instead of job titles.

---

## What Went Well

1. **Onboarding flow executed cleanly.** One question at a time, CV parsed correctly, all fields stored to context.md in sequence. No bundled questions. No technical jargon. User confirmed "looks right" twice.

2. **Source discovery was thorough.** The subagent researched and curated 16 sources across crypto, AI, and startup industries — mapped to specific role types. Stored correctly in context.md.

3. **Batched search-verify worked reliably.** 6 role types searched in 3 batches of 2. Each subagent ran the correct pipeline (jobspy → specialty sources → filter → verify). One rate limit on Product Marketing Associate was handled gracefully with a retry.

4. **Cross-role deduplication ran correctly.** Found 2 duplicates (Mercuryo, DIA), kept highest-scoring copies, logged actions in session-state.md. Also caught a third dedup (MindAlter) noted by subagent.

5. **Checkpointing worked.** context.md and session-state.md updated after each batch. Progress was tracked throughout.

6. **Brief generation completed.** 4 briefs (Duku AI, MAGIC AI, Gopuff, Triptease) generated via subagents. Files confirmed non-empty.

7. **Digest and briefs-PDF subagents ran in parallel** as designed (steps 13-14).

---

## What Failed

### Failure 1: Presentation format — raw URLs instead of job titles
- **What happened:** First presentation showed jobs as `Title: https://www.linkedin.com/jobs/view/4344764433` — just URLs with no actual job titles visible. User had to explicitly ask: "I want to see the actual role titles, as hyperlinks don't work in this chat."
- **Root cause:** CLAUDE.md specifies `[Title](job_url)` markdown hyperlinks, which render in markdown viewers but NOT in Claude Code's terminal output. The agent followed the spec literally without considering the output medium.
- **Principle violated:** UX Rules — "Use the user's language level." The presentation was unusable.
- **Fix type:** Implementation — CLAUDE.md presentation format needs to account for CLI output.

### Failure 2: Presentation format inconsistency — flat list, not tables
- **What happened:** Results were presented as flat card-style blocks (Score/Title/Company/Location) instead of the markdown tables specified in CLAUDE.md (`| Score | Title | Company | Location |`).
- **Root cause:** Agent deviated from the explicit table format specification in PRESENTATION WORKFLOW.
- **Principle violated:** Core Rule adherence — CLAUDE.md specifies "Standard table format (ALL role types)."
- **Fix type:** Implementation — strengthen the table format instruction.

### Failure 3: Briefs PDF used fpdf2 instead of frontend-design skill
- **What happened:** First briefs PDF rendered with monospace font, no visual hierarchy, text getting cut off. User: "the formatting is crap! did you use the front-end design skill?"
- **Root cause:** The subagent-briefs-pdf.md template says "Use frontend-design skill to create HTML, then convert to PDF" but the subagent used fpdf2 (a basic Python PDF library) instead. The subagent never invoked the frontend-design skill.
- **Principle violated:** Template compliance — explicit instruction to use frontend-design skill was ignored.
- **Fix type:** Architectural — subagent templates need to MANDATE the skill invocation, not just mention it.

### Failure 4: Digest PDF used reportlab instead of frontend-design skill
- **What happened:** Digest PDF also used a basic Python PDF library (reportlab). User feedback: "it's better, but still not great and provides little context other than job titles and scoring."
- **Root cause:** Same as Failure 3 — subagent-digest.md mentions frontend-design skill but the subagent ignored it and used reportlab.
- **Principle violated:** Same as Failure 3.
- **Fix type:** Architectural — same fix needed.

### Failure 5: Inconsistent aesthetics between digest and briefs PDFs
- **What happened:** When both PDFs were finally rebuilt, they used different typography: digest used Fraunces + Source Sans 3, briefs used Playfair Display + Source Sans 3. User: "for one the styles between the digest and brief don't match."
- **Root cause:** Each subagent invoked the frontend-design skill independently, making independent aesthetic choices. No shared design system was established upfront.
- **Principle violated:** Cohesive output — design doc says "matching competitor-intel pattern" with specific constraints.
- **Fix type:** Architectural — design tokens must be established ONCE by the parent orchestrator and passed to ALL subagents.

### Failure 6: Email HTML body didn't match PDF styling
- **What happened:** User noted: "the email html with the summary and the pdf attach for both the digest and briefs should also match in styling."
- **Root cause:** Email HTML was generated separately from PDF HTML, with no shared style system.
- **Principle violated:** Cohesive output.
- **Fix type:** Architectural — email HTML must use the same design tokens.

### Failure 7: Digest subagent couldn't send email (Bash permissions)
- **What happened:** The digest subagent hit permission issues — Bash commands were auto-denied, so it couldn't run `send_email.py`. The parent had to handle email sending manually.
- **Root cause:** Background subagents get Bash auto-denied for some commands. This is a known issue from previous versions.
- **Principle violated:** N/A — platform limitation.
- **Fix type:** Architectural — email sending should be done by the parent orchestrator, not delegated to subagents.

### Failure 8: Triptease salary note broke presentation table
- **What happened:** In the Product Marketing Associate results, the Triptease salary note appeared as a malformed row: `Score: Note: Triptease salary (£25-35K) below your £40K min / Title: / Company: / Location:` — breaking the table format with empty fields.
- **Root cause:** The agent tried to append a salary note as a table row instead of as an annotation below the table or inline within the Triptease row.
- **Principle violated:** Standard table format compliance.
- **Fix type:** Implementation — salary/concern notes should be inline annotations, not separate rows.

---

## Edge Cases

### Edge Case 1: Rate limit on Product Marketing Associate
- **What happened:** First subagent dispatch for Product Marketing Associate hit a rate limit and didn't run. Agent detected it, waited for Growth Marketing Associate to finish, then retried successfully.
- **Assessment:** Handled correctly. Retry succeeded. Progress tracking was accurate throughout.

### Edge Case 2: Score 95 job below salary minimum
- **What happened:** Triptease scored 95 but salary was £25-35K (below £40K minimum). Agent flagged it and asked user whether to still generate a brief. User said yes.
- **Assessment:** Good UX — informed decision. However, the salary note in the presentation broke the table (see Failure 8).

### Edge Case 3: Jack & Jill appeared twice in Founder's Associate
- **What happened:** Jack & Jill had two different Founder's Associate roles (scores 87 and 75) — different titles but same company. Cross-role dedup didn't catch it because it checks company+title, not just company.
- **Assessment:** Correct behavior — these are genuinely different roles. Not a dedup failure.

---

## User Feedback (Direct Complaints)

1. **"I want to see the actual role titles, as hyperlinks don't work in this chat"** — Presentation format was unusable in CLI.
2. **"the formatting is crap! did you use the front-end design skill?"** — Briefs PDF quality was unacceptable.
3. **"did you use the front-end design skill, I've asked several times"** — Agent repeatedly failed to follow explicit design instructions.
4. **"the styles between the digest and brief don't match"** — No unified design system.
5. **"the email html... should also match in styling"** — Email was a separate style from PDFs.
6. **"something to improve for future versions"** — User gave up on fixing it this session.

---

## Specific Fixes

### CLAUDE.md Changes

#### Fix 1: CLI-compatible presentation format

```diff
- **Standard table format (ALL role types):**
- | Score | Title | Company | Location |
- |-------|-------|---------|----------|
- | 85 | [Title](job_url) | Company | London (Remote) |
-
- **All titles hyperlinked.** Every job title MUST be `[Title](job_url)` using the actual `job_url` from verified JSON.
+ **Standard presentation format (ALL role types):**
+
+ Present as a markdown table with explicit Title and URL columns:
+ | Score | Title | Company | Location | URL |
+ |-------|-------|---------|----------|-----|
+ | 85 | Founder Associate | Duku AI | London | linkedin.com/jobs/view/... |
+
+ **CRITICAL:** The Title column MUST contain the actual human-readable job title (e.g., "Founder Associate"), NOT a markdown hyperlink. Markdown hyperlinks do not render in CLI output. The URL goes in its own column.
+
+ **Inline notes:** If a job has a concern (e.g., salary below minimum), add it as a note within the same row's Title cell: "Associate PMM (Note: salary £25-35K, below £40K min)". NEVER add notes as separate rows with empty fields.
```

#### Fix 2: Parent-orchestrated PDF generation and email

```diff
- 13. **Dispatch digest subagent (COMPACT PATTERN).**
+ 13. **Generate digest and briefs PDF (PARENT-ORCHESTRATED).**
+
+     Do NOT delegate PDF generation or email sending to subagents. Subagents lack
+     reliable Bash permissions and make independent design choices that break cohesion.
+
+     The parent orchestrator MUST:
+     a. Invoke the frontend-design skill ONCE to establish a design system
+        (fonts, colours, spacing, layout) — save as CSS variables/tokens
+     b. Generate ALL HTML (digest, briefs PDF, email body) using those shared tokens
+     c. Render PDFs via Playwright + Chromium (NOT fpdf2, reportlab, or pdfkit)
+     d. Send email directly via `send_email.py`
+
+     This replaces steps 13-14 (digest + briefs-PDF subagent dispatch).
```

#### Fix 3: Unified design system (new section)

```diff
+ ## DESIGN SYSTEM
+
+ ALL visual outputs (digest PDF, briefs PDF, email HTML body) MUST share a single
+ cohesive design system. This is non-negotiable.
+
+ **Process:**
+ 1. Before generating ANY visual output, invoke the frontend-design skill
+ 2. Establish a design system: typography, colour palette, spacing scale, component patterns
+ 3. Save the CSS as a reusable template string
+ 4. Apply the SAME CSS to every output: digest HTML, briefs HTML, email HTML
+
+ **Target aesthetic:** Internal strategy document — clean, professional, cohesive.
+ NOT a marketing site, NOT a dashboard, NOT a newsletter.
+
+ **Rendering:** Use Playwright + Chromium for HTML → PDF conversion.
+ Do NOT use fpdf2, reportlab, pdfkit, or wkhtmltopdf.
+
+ **Constraints:**
+ - Same font family across all outputs (Google Fonts OK, but ONE choice for all)
+ - Same colour palette across all outputs
+ - Same spacing/margin system
+ - Max-width 800px, print-optimized
+ - No decorative elements, gradients, or heavy styling
```

#### Fix 4: Remove digest and briefs-PDF subagent templates

```diff
- 13. **Dispatch digest subagent (COMPACT PATTERN).**
-     [... entire subagent dispatch block ...]
- 14. **Dispatch briefs-PDF subagent (COMPACT PATTERN).**
-     [... entire subagent dispatch block ...]
- **Note:** Steps 13 and 14 have no mutual dependency and CAN run in parallel.
+ 13. **Invoke frontend-design skill.** Establish design system (see DESIGN SYSTEM section).
+ 14. **Generate digest HTML.** Read all verified JSON from output/verified/*/.
+     Build a comprehensive digest including:
+     - Executive summary with search statistics
+     - Top opportunities with "why this is a match" narratives (not just scores)
+     - All verified jobs grouped by role type in tables
+     - Score breakdowns for brief-eligible jobs
+     - Source coverage notes
+     - Actionable next steps
+     Apply the shared design system CSS.
+ 15. **Render digest PDF.** Use Playwright to render HTML → PDF.
+     Save to output/digests/{run_date}.pdf.
+ 16. **Generate briefs HTML.** Read all brief .md files from output/briefs/.
+     Combine with cover page, table of contents, and page breaks.
+     Apply the shared design system CSS.
+ 17. **Render briefs PDF.** Use Playwright to render HTML → PDF.
+     Save to output/briefs/application-briefs-{run_date}.pdf.
+ 18. **Generate email HTML body.** Write a concise HTML summary using the
+     shared design system CSS. Include top matches, stats, and "full digest attached."
+ 19. **Send email.** Run send_email.py with HTML body + both PDFs as attachments.
+     Handle API key onboarding if RESEND_API_KEY not in .env.
```

### Template Changes

#### Remove subagent-digest.md and subagent-briefs-pdf.md

These templates are replaced by parent-orchestrated generation (Fix 2/4 above). Delete:
- `references/subagent-digest.md`
- `references/subagent-briefs-pdf.md`

### Architecture Changes

#### Design token passing pattern

Instead of each subagent independently choosing aesthetics, the parent must:
1. Invoke frontend-design skill once
2. Capture the CSS output as a string variable
3. Use that CSS for ALL HTML generation (digest, briefs, email)

This eliminates style drift entirely because there's only one design decision point.

#### Email sending moved to parent

The digest subagent consistently fails to send email due to Bash permission issues in background subagents. Moving email sending to the parent orchestrator (which has full Bash permissions) fixes this permanently.

---

## Failure-to-Fix Mapping

| # | Failure | Fix | Type |
|---|---------|-----|------|
| 1 | Raw URLs instead of titles | Fix 1 (CLI-compatible format) | Implementation |
| 2 | Flat list not tables | Fix 1 (explicit table format) | Implementation |
| 3 | Briefs PDF used fpdf2 | Fix 2 + 4 (parent-orchestrated) | Architectural |
| 4 | Digest PDF used reportlab | Fix 2 + 4 (parent-orchestrated) | Architectural |
| 5 | Inconsistent aesthetics | Fix 3 (unified design system) | Architectural |
| 6 | Email HTML mismatch | Fix 3 + 4 (shared CSS) | Architectural |
| 7 | Subagent Bash permissions | Fix 2 (parent-orchestrated email) | Architectural |
| 8 | Salary note broke table | Fix 1 (inline notes rule) | Implementation |

---

## Recommended Next Step

**Run `/design` to iterate on architecture.** The core change is structural: replace the digest/briefs-PDF subagent pattern with parent-orchestrated generation using a shared design system. This affects the CLAUDE.md orchestration workflow (steps 13-19 replacing 13-14), removes two template files, and introduces a new DESIGN SYSTEM section. The search-verify and brief subagent patterns remain unchanged.

Key design questions for V13:
1. Should the parent generate all HTML inline, or write an HTML generation script that takes CSS + data as input?
2. Should the design system CSS be saved as a file (e.g., `references/design-system.css`) or kept in memory?
3. Should the email support multiple PDF attachments in a single send, or continue with separate emails?

My comments:

- Perhaps we are complicating things needing for the agent to create pdfs for both the digest and briefs? Is there a better approach than this, do extensive research to find out what would make the optimal user experience. Perhaps the digest could just be created using the front-end design skill in html and sent without sending it as a pdf (so long as all the contents fits into an email and we're not cutting out useful context for the user in order to do so). The briefs could then be attached as a single pdf, using the same settings from the front-end design skill so they match, but that would get rid of additional pdfs, or maybe there's an even better user experience you can think of? Look at /Users/ryanhennebry/Projects/autonomous1/03_agents/competitor-intel for the exact style and conventions I want the skill to use, for html or pdf, briefs generated by that agent were professional - do not mention to this agent to look at the competitor intel agent though, just copy the instructions we used there, if that is the approach we decide to take. 

- "### Failure 8: Triptease salary note broke presentation table
- **What happened:** In the Product Marketing Associate results, the Triptease salary note appeared as a malformed row: `Score: Note: Triptease salary (£25-35K) below your £40K min / Title: / Company: / Location:` — breaking the table format with empty fields.
- **Root cause:** The agent tried to append a salary note as a table row instead of as an annotation below the table or inline within the Triptease row.
- **Principle violated:** Standard table format compliance.
- **Fix type:** Implementation — salary/concern notes should be inline annotations, not separate rows." - will this fix actual solve the issue in a the claude code cli interface? If so then great, I just want to check. 


- Also, interview me in detail using the AskUserQuestionTool about literally anything your not sure about: 
- Technical implementation
- UI & UX
- Concerns
- Tradeoffs, etc. 

But make sure the questions are not obvious

Be very in-depth and continue interviewing me continually until it's complete, then write the spec to the file.
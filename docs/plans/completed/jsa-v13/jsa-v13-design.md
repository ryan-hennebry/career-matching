# Design: Job Search Agent V13

## Context

V12 analysis identified 8 failures (7 wins). The core search-verify pipeline works well — 6 role types searched, 44 jobs verified, cross-role deduplication ran, briefs generated. The session broke down at PDF/email delivery: subagents ignored the frontend-design skill, each picked different rendering approaches (fpdf2, reportlab), produced inconsistent aesthetics, and email HTML didn't match PDF styling.

Research into Claude Code subagent architecture revealed that **subagents do NOT inherit CLAUDE.md or skills from the parent** — they get a fresh context. V12's approach of mentioning "use frontend-design skill" in a template was just a suggestion the subagent could (and did) ignore. The fix is architectural: **named subagent definitions** in `.claude/agents/` with skills preloaded via frontmatter, tools restricted, and persistent memory enabled.

Additionally, the digest format is being simplified: **no digest PDF**. The full digest becomes the email HTML body. Only the briefs PDF is attached.

---

## Design Decisions (User-Confirmed)

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Digest format | Full digest as email HTML body + briefs PDF attachment | Eliminates one PDF. Digest directly visible. YAGNI on clipping fallback. |
| Design system | Dedicated skill file (`.claude/skills/jsa-design-system.md`) | Preloaded into visual subagents via `skills:` field. Deterministic, zero drift. |
| Subagent architecture | Named agents in `.claude/agents/` for ALL subagent types | Skills preloaded, tools restricted, persistent memory. Fixes V12 reliability failures. |
| Model routing | All inherit parent model | Simplest config. User controls quality via parent model choice. |
| Persistent memory | Enabled for all agent types | Search agents remember source reliability. Brief agents remember preferences. |
| CLI presentation URLs | Reference footnotes `[1]` | Clean table, full clickable URLs listed below. Academic citation pattern. |
| CLI salary/concern notes | Asterisk `*` + footnote | Consistent with URL footnote pattern. Table rows stay uniform width. |
| Digest content depth | Tiered — top 5 get rich detail, rest get score + 1-line | Best signal-to-noise for triage. Top matches are action items. |
| Email HTML generation | Digest subagent generates both email body + digest content | Same data read, no duplication. Parent handles actual email send. |
| Email script | Generalize `send_email.py` with `--body-file` + `--attachment` | One script for all email use cases. Replaces `send_alert.py`. |
| Variable passing | Keep compact JSON pattern in Task prompt | Proven V12 pattern. Agent definition = static identity, Task JSON = dynamic data. |
| CLAUDE.md update scope | Rewrite steps 13-19 only | Surgical replacement of broken delivery steps. Steps 1-12 untouched. |

---

## Architecture

### Named Subagent Definitions

Create 4 named subagents in `.claude/agents/` (project-level, at `03_agents/tests/v13/.claude/agents/`):

#### 1. `search-verify.md`
```yaml
---
name: search-verify
description: Search job sources, verify active listings, score against user profile
model: inherit
tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
disallowedTools: Skill, NotebookEdit
memory: project
---
```
- Preloaded references: reads `references/subagent-search-verify.md` + `references/algorithms.md` via prompt
- Memory learns: source reliability (403s, empty results), which specialty boards work per industry
- Compact JSON: 13 variables (unchanged from V12)

#### 2. `brief-generator.md`
```yaml
---
name: brief-generator
description: Generate application brief for a single job match
model: inherit
tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
disallowedTools: NotebookEdit
memory: project
---
```
- Preloaded references: reads `references/subagent-brief.md` + `references/templates.md` via prompt
- Memory learns: which brief sections user finds most valuable, common company research patterns
- Compact JSON: 7 variables (unchanged from V12)

#### 3. `digest-email.md`
```yaml
---
name: digest-email
description: Generate email digest HTML and briefs compilation content
model: inherit
tools: Bash, Read, Write, Glob, Grep
disallowedTools: pip, pip3, WebFetch, WebSearch, NotebookEdit
skills:
  - jsa-design-system
memory: project
---
```
- **Key change from V12:** `jsa-design-system` skill preloaded — agent CANNOT ignore it
- **`pip`/`pip3` blocked** — cannot install fpdf2, reportlab, pdfkit. Forced to use Playwright + Chromium.
- Generates TWO outputs: email HTML body file + digest content (same data)
- Does NOT send email (parent handles that)
- Memory learns: which HTML patterns render well in email clients, any clipping issues

#### 4. `briefs-pdf.md`
```yaml
---
name: briefs-pdf
description: Compile application briefs into a single styled PDF
model: inherit
tools: Bash, Read, Write, Glob, Grep
disallowedTools: pip, pip3, WebFetch, WebSearch, NotebookEdit
skills:
  - jsa-design-system
memory: project
---
```
- Same design system skill preloaded as digest-email agent
- Same tool restrictions (pip blocked, Playwright enforced)
- Generates cover page + TOC + individual brief pages
- Memory learns: PDF rendering edge cases, page break issues

### Design System Skill

Create `.claude/skills/jsa-design-system.md` — a skill file containing the exact CSS, typography, colors, and layout rules. This is preloaded into digest-email and briefs-pdf agents.

**Design specifications** (from competitor-intel's proven approach):

- **Typography:** System sans-serif (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`). 16px body, 14px tables.
- **Colors:** `#ffffff` background, `#1a1a1a` primary text, `#525252` secondary, `#737373` light, `#e5e5e5` borders, `#f5f5f5`/`#fafafa` section backgrounds.
- **Score accents:** `#16a34a` (green, 90+), `#d97706` (amber, 70-79), `#dc2626` (red, below salary min).
- **Layout:** Max-width 800px, 40px+ margins, single column, generous whitespace.
- **Tables:** Full-width, `1px solid #e5e5e5` borders, `10-12px` cell padding, `#fafafa` header background.
- **Email specifics:** Inline styles, `<table>` layout (not flexbox/grid), 600px max-width for email body.
- **PDF specifics:** `page-break-after: avoid` on headings, `page-break-inside: avoid` on sections/tables.
- **Rendering:** Playwright + Chromium ONLY. No fpdf2, reportlab, pdfkit, wkhtmltopdf, WeasyPrint.
- **Aesthetic:** Internal strategy document — clean, professional. NOT a marketing site, dashboard, or newsletter.

### Orchestration Flow (Steps 13-19 Replacement)

Replace V12 CLAUDE.md steps 13-14 with:

```
13. Dispatch digest-email agent (NAMED AGENT PATTERN).
    Agent: "digest-email" (from .claude/agents/)
    Compact JSON: {run_date, user_email, user_name, total_verified, total_briefs}

    Agent generates:
    - output/digests/{run_date}-email.html (full digest as email body)
    - output/digests/_status.json

    Email HTML content (tiered):
    - Header: "{user_name}'s Job Search Update — {run_date}"
    - Executive summary: total verified, total briefs, score distribution
    - Top 5 Opportunities: rich narrative + score breakdown (90%+ matches)
    - All Verified Jobs: tables per role type, score + 1-line match reason
    - Statistics: per-role counts, source coverage
    - Footer: "Application briefs attached as PDF"

14. Dispatch briefs-pdf agent (NAMED AGENT PATTERN). If any briefs generated.
    Agent: "briefs-pdf" (from .claude/agents/)
    Compact JSON: {run_date}

    Agent generates:
    - output/briefs/application-briefs-{run_date}.pdf
    - output/briefs/_briefs-pdf-status.json

    Note: Steps 13 and 14 have no mutual dependency and CAN run in parallel.

15. Verify completion. Read both status files.
    - digest: output/digests/_status.json
    - briefs-pdf: output/briefs/_briefs-pdf-status.json
    Handle failures per V12 pattern (complete/partial/failed).

16. Send email (PARENT-ORCHESTRATED).
    Parent runs:
    source .env && python3 scripts/send_email.py \
      --to "{user_email}" \
      --subject "Job Search Update — {run_date}" \
      --body-file output/digests/{run_date}-email.html \
      --attachment output/briefs/application-briefs-{run_date}.pdf

    If no briefs PDF (user rejected all jobs): omit --attachment flag.
    If RESEND_API_KEY not set: prompt user for key, write to .env.
```

### CLI Presentation Format (Steps 9-10)

Replace hyperlink table format with reference footnote pattern:

```
**Results: Community Manager** (8 verified, 5 above threshold)

| Score | Title                      | Company       | Location         |
|-------|----------------------------|---------------|------------------|
| 92    | Founder Associate [1]      | Duku AI       | London (Remote)  |
| 87    | Growth Lead [2]            | MAGIC AI      | London           |
| 95    | Associate PMM * [3]        | Triptease     | London (Hybrid)  |
| 82    | Community Manager [4]      | Gopuff        | London           |

[1] https://linkedin.com/jobs/view/4344764433
[2] https://web3.career/jobs/magic-ai-growth-lead
[3] https://linkedin.com/jobs/view/4355891722
[4] https://linkedin.com/jobs/view/4398712345

* Triptease salary £25-35K, below your £40K minimum
```

### send_email.py Rewrite

Generalize the script:
```
python3 scripts/send_email.py \
  --to user@email.com \
  --subject "Job Search Update — 2026-02-07" \
  --body-file output/digests/2026-02-07-email.html \
  --attachment output/briefs/application-briefs-2026-02-07.pdf
```

Interface:
- `--to` (required): recipient email
- `--subject` (required): email subject
- `--body-file` (required): path to HTML file for email body
- `--attachment` (optional, repeatable): path to PDF attachment
- `--test`: send without attachments

Removes: hardcoded HTML generation. `send_alert.py` becomes obsolete (use `send_email.py` with alert HTML body file instead).

---

## Files to Create

| File | Purpose |
|------|---------|
| `03_agents/tests/v13/.claude/agents/search-verify.md` | Named search+verify subagent definition |
| `03_agents/tests/v13/.claude/agents/brief-generator.md` | Named brief generation subagent definition |
| `03_agents/tests/v13/.claude/agents/digest-email.md` | Named digest + email HTML subagent definition |
| `03_agents/tests/v13/.claude/agents/briefs-pdf.md` | Named briefs PDF compilation subagent definition |
| `03_agents/tests/v13/.claude/skills/jsa-design-system.md` | Design system skill (CSS, fonts, colors, layout rules) |
| `03_agents/tests/v13/references/subagent-digest-email.md` | Template for digest-email agent (replaces subagent-digest.md) |
| `03_agents/tests/v13/references/subagent-briefs-pdf.md` | Updated template for briefs-pdf agent |

## Files to Modify

| File | Changes |
|------|---------|
| `03_agents/tests/v13/CLAUDE.md` | Rewrite steps 13-19 (delivery workflow). Update presentation format (reference footnotes). Add NAMED AGENT PATTERN section. Add DESIGN SYSTEM section. |
| `03_agents/tests/v13/scripts/send_email.py` | Generalize: `--body-file`, `--attachment` flags. Remove hardcoded HTML generation. |
| `03_agents/tests/v13/references/subagent-search-verify.md` | Path updates (v12 → v13) |
| `03_agents/tests/v13/references/subagent-brief.md` | Path updates (v12 → v13) |

## Files to Delete

| File | Reason |
|------|--------|
| `references/subagent-digest.md` | Replaced by `subagent-digest-email.md` |
| `scripts/send_alert.py` | Replaced by generalized `send_email.py` |

---

## Failure-to-Fix Mapping

| # | V12 Failure | V13 Fix | Mechanism |
|---|-------------|---------|-----------|
| 1 | Raw URLs in CLI | Reference footnotes `[1]` | CLAUDE.md presentation format rewrite |
| 2 | Flat list not tables | Tables enforced | CLAUDE.md presentation format (carried from V12 fix) |
| 3 | Briefs PDF used fpdf2 | Named agent: pip blocked, design skill preloaded | `.claude/agents/briefs-pdf.md` with `disallowedTools: pip, pip3` and `skills: jsa-design-system` |
| 4 | Digest used reportlab | Named agent: pip blocked, design skill preloaded | `.claude/agents/digest-email.md` with same restrictions |
| 5 | Inconsistent aesthetics | Single design system skill shared by all visual agents | `jsa-design-system.md` skill preloaded into both agents |
| 6 | Email HTML mismatch | Digest agent generates email HTML using same skill | One agent, one skill, one aesthetic |
| 7 | Subagent Bash permissions | Parent sends email | Step 16: parent runs `send_email.py` directly |
| 8 | Salary note broke table | Asterisk + footnote | CLAUDE.md presentation format: `*` marker, footnote below table |

---

## New Capabilities (Beyond V12 Fixes)

1. **Persistent agent memory** — Search agents remember source reliability across sessions. Brief agents learn user preferences. Design agents remember rendering edge cases.
2. **Tool restrictions** — Visual agents cannot install alternative PDF libraries. Search agents cannot accidentally modify output HTML.
3. **Deterministic design** — Design system is a skill, not a suggestion. Preloaded into context at startup.
4. **Generalized email** — One script handles digests, alerts, any future email needs.
5. **No digest PDF** — Digest is the email body. One fewer file to generate, style, and validate.

---

## Verification

### End-to-End Test
1. Copy V12 test directory to V13: `cp -r 03_agents/tests/v12 03_agents/tests/v13`
2. Apply all modifications (CLAUDE.md, scripts, agents, skills)
3. Run agent session against V13
4. Verify:
   - CLI presentation uses reference footnotes (no raw URLs, no hyperlinks)
   - Salary notes use asterisk + footnote (no broken table rows)
   - Digest email HTML uses correct design system (system sans-serif, #1a1a1a text, 800px max-width)
   - Briefs PDF uses same design system as email HTML (visual comparison)
   - Email sends successfully with HTML body + PDF attachment
   - All named subagents log to their memory directories
   - `pip`/`pip3` is never called by visual agents
   - No fpdf2, reportlab, pdfkit imports anywhere in output

### Unit Checks
- `send_email.py --test` sends test email with `--body-file` flag
- Named agent definitions parse correctly (valid YAML frontmatter)
- Design system skill file loads without errors
- Compact JSON variable count matches template expectations (13 for search, 7 for brief, 5 for digest, 1 for briefs-pdf)

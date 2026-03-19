# Career Matching Agent

Find live job matches, rank them against your background, and get application briefs for the roles worth pursuing.

No coding experience required.

<img src="assets/cli-demo-full.gif" alt="Career Matching CLI onboarding, ranked matches, brief selection, and digest demo" width="896" />

## Quick start

**Prerequisite:** Claude Code installed and authenticated. [Setup instructions](https://code.claude.com/docs/en/quickstart).

1. Paste this command into **Terminal** (Mac) or **PowerShell** (Windows):

```bash
git clone https://github.com/ryan-hennebry/career-matching.git && cd career-matching && claude --dangerously-skip-permissions
```

2. In Claude Code, paste or upload your CV when the agent asks, then answer the onboarding questions one at a time.

## The onboarding flow

- Paste or upload your CV
- Confirm or correct the profile the agent extracts
- Add any skills that are missing from the CV
- Choose the role types and industries you want to target
- Set location preferences and minimum salary
- Add your email for digests, and optionally a dashboard URL if you already have one
- The agent searches job boards and career pages, ranks the results, and asks which roles you want briefs for

## What you receive

Each run produces a shortlist with:

- Verified job matches scored across required skills, preferred skills, experience, industry, location, and salary
- A clear view of what is new today versus still active
- Reasons each role fits, where the gaps are, and which opportunities look strongest
- Application briefs for the roles you choose, including CV tailoring, cover letter talking points, outreach draft, and an application checklist
- An optional email digest, plus an optional dashboard view if you have the included dashboard deployed

## Once your first output has been generated

Keep working with the agent in Claude Code for faster triage:

- "Show only the jobs that are new today."
- "Which roles mention AI agents or Claude Code?"
- "Why did this role score higher than the others?"
- "Prepare briefs for jobs 1 and 3."
- "Mark this one rejected and keep tracking the rest."

## Optional delivery

Only set this up if you want ongoing updates:

- **Email digest via Resend:** when the agent asks, open [Resend](https://resend.com/api-keys), create an API key, and paste it into chat
- **Dashboard links:** if you already have the included dashboard deployed, paste its URL when the agent asks so digests can link back to it

## The agent's output

- Ranked job tables showing score, title, company, location, and source links
- A pipeline view of new, reviewing, brief-requested, applied, rejected, and expired jobs
- Per-job detail views with requirements met, gaps, score breakdown, and the original listing
- Application briefs for selected roles
- A digest email and browser dashboard view when those delivery options are configured

## How it works

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/how-it-works-dark.svg">
  <img src="assets/how-it-works-light.svg" alt="How Career Matching Agent works" width="560" />
</picture>

*Diagram source: `assets/how-it-works.mmd`.*

## Project standards

- [MIT License](LICENSE)
- [Security Policy](SECURITY.md)
- [Contributing Guide](CONTRIBUTING.md)

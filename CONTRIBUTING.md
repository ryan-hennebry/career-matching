# Contributing

Thanks for improving this project.

## Scope

- Keep onboarding simple and non-technical.
- Keep README claims aligned with actual agent behavior in `CLAUDE.md`, `context.md`, `references/`, `scripts/`, and the dashboard files in `api/` and `public/`.
- Prefer small, focused pull requests.

## Local checks

Run before opening a PR:

```bash
cd /Users/ryanhennebry/Projects/autonomous1/03_agents/career-matching
python3 -m pytest
bash scripts/preflight.sh --structure
```

## Pull request checklist

- Describe what changed and why.
- Include before/after screenshots or GIFs for README visual changes.
- Note any behavior changes in `CLAUDE.md`, `references/`, or dashboard endpoints.
- Confirm setup, delivery, and output details in README are still accurate.

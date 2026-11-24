# Career Matching

I built this to find open jobs that fit my experience and help me decide which ones to apply for.

Tell it what you've done and what you'd like to do next. It looks for roles and checks whether they're still open. You get a shortlist split into **Apply now** and **Apply if time**. Each recommendation links to the listing and explains why it fits and what you still need to check.

If it doesn't find a confirmed match, it tells you where it looked and what it couldn't verify. Once you mark a job as submitted, it stays off future shortlists.

## Try the demo

The demo uses fictional jobs and needs no account. You'll need [Git](https://git-scm.com/downloads) and [Python 3.11 or later](https://www.python.org/downloads/). Once you've cloned the repo, the demo runs offline.

```sh
git clone https://github.com/ryan-hennebry/career-matching.git
cd career-matching
python3 scripts/career_match.py demo
```

On Windows, use `py -3` in place of `python3`. To see the shortlist in your browser, run `python3 scripts/career_match.py preview` and open the address it prints.

## Search for your own roles

Install and sign in to [Claude Code](https://code.claude.com/docs/en/quickstart) or [Codex CLI](https://learn.chatgpt.com/docs/codex/cli). In the project folder, run `claude` or `codex` and ask for help setting up your search. When you find a role you like, ask for an application brief. [Usage guide](docs/usage.md)

Your search files stay on your computer. Your AI client may process what you share with it.

[MIT license](LICENSE)

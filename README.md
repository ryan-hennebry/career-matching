# Career Matching

Decide which jobs to apply for. Career Matching checks whether listings are still open and explains how each recommended role fits your experience and the work you want.

## Try the demo

You need [Git](https://git-scm.com/downloads) and [Python 3.11 or later](https://www.python.org/downloads/). After cloning, the demo runs offline with fictional jobs and needs no account.

```sh
git clone https://github.com/ryan-hennebry/career-matching.git
cd career-matching
python3 scripts/career_match.py demo
```

On Windows, use `py -3` in place of `python3`. To see the shortlist in your browser, run `python3 scripts/career_match.py preview` and open the address it prints.

## Search for your own roles

The shortlist groups roles into **Apply now** and **Apply if time**, with links, reasons and open questions. Each search shows which sources it checked and where it hit a limit. Mark a role as submitted to keep it off future shortlists.

Install and sign in to [Claude Code](https://code.claude.com/docs/en/quickstart) or [Codex CLI](https://learn.chatgpt.com/docs/codex/cli). In the project folder, run `claude` or `codex` and ask for help setting up your profile and finding roles that fit.

Ask for a brief when you find a role you want to pursue. [Usage guide](docs/usage.md)

Your search records stay on your computer. Your AI client may process what you share with it. You decide whether to apply.

[MIT license](LICENSE)

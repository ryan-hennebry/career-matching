# Career Matching

Career Matching helps you decide where to apply. It checks employer listings and shows why each recommended job fits your experience and the work you want.

In the fictional demo, an employer reposts a job under a new title. The repost is a day old. The original listing is 55 days old, outside the 35-day window, so Career Matching skips the job. A live listing with an update date and no original posting date stays in **Apply if time**.

## Try the demo

Install [Git](https://git-scm.com/downloads) and [Python 3.11 or later](https://www.python.org/downloads/).

```sh
git clone https://github.com/ryan-hennebry/career-matching.git
cd career-matching
python3 scripts/career_match.py demo
```

On Windows, use `py -3` in place of `python3`. After cloning, the demo runs offline without an account. For a browser view, run `python3 scripts/career_match.py preview` and open the address it prints.

## Search for your own roles

Install and sign in to [Claude Code](https://code.claude.com/docs/en/quickstart) or [Codex CLI](https://learn.chatgpt.com/docs/codex/cli). Run `claude` or `codex` in the project folder and ask it to help set up your profile and find jobs that fit.

The shortlist groups recommendations into **Apply now** and **Apply if time**. Each role comes with a listing link, a reason and any open questions. Each search shows which sources it checked and where it hit a limit.

Mark a role as submitted to keep it off future shortlists. Ask for a brief when you find one you want to pursue. [Usage guide](docs/usage.md)

Your search records stay on your computer. Your AI client may process the information you share with it. You decide whether to apply.

[MIT license](LICENSE)

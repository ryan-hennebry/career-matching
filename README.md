# Career Matching

Decide which jobs are worth applying for. Career Matching checks employer listings and explains how each recommended role fits your experience and the work you want.

In the fictional demo, an employer reposts a job under a new title. The repost is a day old. The original listing is 55 days old, so Career Matching skips it under the 35-day rule. A live listing with an update date and no original posting date stays in **Apply if time**. [See the replay test](tests/test_career_match.py).

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

The shortlist groups recommendations into **Apply now** and **Apply if time**. Each role comes with a reason and any open questions. Mark a role as submitted to keep that job off future shortlists. You can ask for a brief for any role you want to pursue. [Usage guide](docs/usage.md).

## What gets checked

To make the shortlist, a role needs a review, a link to the specific job, and a record that the listing was checked and open on the day of the search. The search report shows where the agent looked, which sources it couldn’t check, and where it hit a result limit. [Matching policy](references/matching-policy.md), [design notes](docs/design.md) and [automated checks](https://github.com/ryan-hennebry/career-matching/actions/workflows/ci.yml?query=branch%3Amain)

The project stores search records locally. Your AI client may process the information you share with it. You decide whether to apply.

[MIT license](LICENSE)

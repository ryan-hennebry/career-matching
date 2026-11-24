# Career Matching

Share your CV and tell the agent what you want from your next job. Career Matching looks for roles, checks which ones are still open and gives you a shortlist with a reason for each match.

The shortlist has **Apply now** and **Apply if time** groups. Each recommendation links to the listing and says what you still need to check. If there are no confirmed matches, you can see where it looked and what it couldn't verify. Jobs you mark as submitted stay off later shortlists.

## Try the demo

The demo uses fictional jobs and needs no account. You'll need [Git](https://git-scm.com/downloads) and [Python 3.11 or later](https://www.python.org/downloads/). Once you've cloned the repo, the demo runs offline.

```sh
git clone https://github.com/ryan-hennebry/career-matching.git
cd career-matching
python3 scripts/career_match.py demo
```

On Windows, use `py -3` in place of `python3`. To see the shortlist in your browser, run `python3 scripts/career_match.py preview` and open the address it prints.

## Search for your own roles

Install and sign in to [Claude Code](https://code.claude.com/docs/en/quickstart) or [Codex CLI](https://learn.chatgpt.com/docs/codex/cli). In the project folder, run `claude` or `codex`. Point the agent to your CV or describe your experience. Tell it what you'd like to do next and any firm limits, such as location or working hours. When you find a role you like, ask for an application brief. [Usage guide](docs/usage.md)

Your search files stay on your computer. Your AI client may process what you share with it.

[MIT license](LICENSE)

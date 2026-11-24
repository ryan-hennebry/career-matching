# Career Matching

I built this for my own job search. It gives me a shortlist and shows why each role fits and what I'd still need to check before applying.

I tell it what I've done and what I'd like to do next. It looks for roles, checks whether the listings are still open and puts the matches under **Apply now** or **Apply if time**. Each recommendation links to the listing.

If I get no confirmed matches, I can see where it looked and what it couldn't verify. Jobs I've marked as submitted stay off later shortlists.

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

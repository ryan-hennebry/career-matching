# Use Career Matching

## Run the example

Run `python3 scripts/career_match.py demo` from the repo. On Windows use `py -3`. Run `python3 scripts/career_match.py preview` and open the URL printed in the terminal. Use Ctrl+C to stop the preview. Give repeated demos a different name with `demo --run another-demo`.

The [fictional snapshots](../examples/offline/snapshots) include a relisted role, an employer listing with an unknown original date, a provisional copy and an unresolved lead. The [fictional reviews](../examples/offline/reviews.json) stand in for a review by you or your AI client. The demo runs discovery, ranking and validation without a model or network request.

## Start a search

Run `python3 scripts/career_match.py onboard` to create `context.md`. You can also ask Claude Code or Codex to help. Share only the CV and work samples you want your AI provider to process. Set the work you want, hard constraints and sources. Tell the agent about earlier applications to avoid surfacing them again.

Create `output/local/` and copy [the example board configuration](../examples/boards.example.json) there as `boards.json`. Replace the example slugs with real employer board slugs. Each Ashby or Greenhouse adapter reads a public board into one dated snapshot.

```sh
python3 scripts/career_match.py check
python3 scripts/career_match.py discover --run first-search --boards output/local/boards.json
```

Discovery writes `candidates.json`, `reviews.json` and local `snapshots/` under the run. Use a new run name each day. Add `--snapshots output/<earlier-run>/snapshots` to retain older evidence. Repeat `--snapshots` for sources you reviewed yourself. Record outside queries with `--query`. The coverage report includes failed sources and any caps you record.

To add JobSpy leads, install `requirements-jobspy.txt` in a virtual environment, run `python3 scripts/jobspy_search.py --help`, and import its JSON with `--jobspy`. Verify each lead against an employer or a reviewed source before it can appear on the shortlist. Keep uncertain locations visible for review.

## Add a reviewed source

Put each snapshot in a JSON file inside an ignored directory. Use `provider`, `company`, optional `board`, `observed_at` and a `jobs` array. Record checked dates as `YYYY-MM-DD`. Use `employer` for first-party pages you checked and `aggregator` for other job boards. An aggregator review stays provisional.

Each job needs an exact `title`, specific `url`, `description`, `location` when known and an `active` boolean. Mark a role active only when the reviewed page still offers that role. Include `id`, `original_publication`, `publication` or `updated` when the source supports that value. Use `cap_hit: true` for truncated results. Keep snapshots private and respect the source's terms.

Discovery joins records with the same company, title, location and description. Use `--aliases` with [the example alias file](../examples/offline/aliases.json) when evidence establishes that different titles or descriptions refer to one seat. Keep its canonical URL stable across runs. Retain the earlier snapshot for its date.

## Review and rank

Each entry in `reviews.json` has a `seat_key`. Leave unresolved entries pending or mark them incomplete. Record reviews using the [example reviews](../examples/offline/reviews.json) and [matching policy](../references/matching-policy.md). Fill in the role and candidate evidence. Python checks the rules and required fields.

```sh
python3 scripts/career_match.py rank --run first-search
python3 scripts/manage_state.py validate-run --manifest output/first-search/ranked/_run-manifest.json
python3 scripts/career_match.py preview --run first-search
```

Rank on the day you checked the listings. To revisit an older run, preview it by name. Check the displayed date and recheck the employer listing before applying.

Use `python3 scripts/career_match.py track --run first-search --seat-key <key> --status submitted` after a confirmed submission. The other statuses are `interested`, `dismissed`, `interviewing` and `clear`. Search records and drafts stay in the ignored `output/` folder. The local tracker lives in `.career-matching/`.

When you choose a role, ask your agent for a brief. Check the employer's need and your evidence before using it.

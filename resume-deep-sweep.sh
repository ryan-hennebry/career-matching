#!/bin/zsh
# Resume the career-matching session: kill the frozen process, restart with
# skip-permissions, and kick off a deep all-channel operator-lens sweep.
set -u

SESSION_ID="971321ee-ba85-4f1f-ad31-863a1d39d90b"
REPO="/tmp/career-matching"

# Kill any stale claude process still parked in this repo (the frozen session).
for pid in $(lsof +D "$REPO" 2>/dev/null | awk '$1 ~ /^[0-9.]+$/ || $1=="claude" {print $2}' | sort -u); do
  if ps -p "$pid" -o comm= 2>/dev/null | grep -qE 'claude|[0-9]+\.[0-9]+\.[0-9]+'; then
    echo "Killing stale claude process $pid"
    kill "$pid" 2>/dev/null
  fi
done
sleep 1

cd "$REPO" || exit 1

PROMPT=$(cat <<'EOF'
Fresh deep delta sweep, 2026-06-10. It has been two days since the last run (last commit: operator-lens re-score, 9 June).

ORCHESTRATE ONLY: you are the orchestrator. Dispatch subagents for everything: all file reading, all channel searches, all verification, all JD pulls, all scoring. You never read source files or fetch pages yourself; you integrate subagent summaries, decide, and commit.

Scope:
1. Go deep across all five channels (direct career pages, industry job boards, jobspy aggregator, niche newsletters, web search discovery) AND the wave-2 high-leverage sources (curated newsletters, VC talent boards, full ATS sweep: Ashby/Greenhouse/Lever/Workable/Pinpoint + YC WaaS). One subagent per channel, parallel, all role types.
2. Primary scoring lens is the new operator lens (callback_op), with the 8-factor callback_v3 as secondary. Focus the search itself through the operator lens: AI/agent operations, founders associate, founding operator/generalist, AI product associate.
3. Bias to recency: prioritise roles posted since 8 June; verify real posting dates.
4. Dedup against state.json, output/_prior_runs_dedup.md, and all roles already in output/deep/. Exclude applied (Ankar FA, Alaro, Neutreeno, Mozart AI, Moss, Terra API, Installio) and confirmed closed (Tilt, Assuric, Jack & Jill, Deel GTM).
5. Re-verify via subagents that the current operator-lens leaders are still open: Geordie AI Agent Operations Lead, both Dwelly roles, Corgi, Light, Togather, StudioB.
6. Score every net-new find with callback_op + callback_v3 (including the hidden-gate stress-test for anything that lands top 10), then present one merged ranked list of new + surviving roles with direct application links and a recommended next-5 to apply to.
7. Update state.json and output/session-state.md, commit when done.
EOF
)

exec claude --resume "$SESSION_ID" --dangerously-skip-permissions "$PROMPT"

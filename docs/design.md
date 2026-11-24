# Design

The agent learns what the candidate wants to do and compares employer requirements with evidence. Python applies rules that should give the same result when run again.

| Part | What it does |
| --- | --- |
| [Agent workflow](../references/orchestration.md) | Learns the goals, collects evidence and writes reviews. Both agent clients read the same instructions. |
| [Source adapters](../scripts/search_sources.py) | Read bounded snapshots and retain posting identity, dates and sources. |
| [Ranking](../scripts/ranking.py) | Applies evidence and recency rules, assigns tiers and orders each tier. |
| [Run validation](../scripts/run_validation.py) | Checks the exact records the candidate will see. The preview serves selected fields from those records. |

Eligibility, desired work and demonstrated skill answer different questions. The ranking keeps them separate. A new listing ID does not erase an older employer date. A Greenhouse update timestamp records a change to the posting and leaves the original date unknown.

Discovery compares exact evidence by default. A reviewed alias can join two URLs when employer evidence supports one seat. Automatic matching can miss edited descriptions. Keep disputed identities separate until reviewed.

The read-only preview serves fixed assets and the validated shortlist on loopback. It checks the board against the run records before serving it. The release retired the earlier hosted dashboard and scheduled email workflow, which expected run data in Git.

Legacy state commands remain in `scripts/manage_state.py`. Current runs use the tier manifest and local tracker. Current deduplication preserves unique jobs regardless of an older numeric score.

## Verify a change

See [Contributing](../CONTRIBUTING.md) for test commands. Test cases cover relists, unknown age, conditional eligibility, provisional results, pending coverage and invalid manifests. The offline tests exercise source parsing, ranking and presentation with fixed reviews. They leave live model accuracy and search recall unmeasured.

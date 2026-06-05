# Agent Memory

## Directory Mapping

- `still_active` keys may use `founders-associate/` but the actual verified dir is `founder-s-associate/`.
- `still_active` keys may use `ai-agent-roles/` but files may live in `marketing-associate/` or `community-manager/`.
- When a key path doesn't resolve, try alternate directory names before skipping.
- Files not found: skip silently, do not fail the digest.

## Score Field Resolution

Verified JSON files use inconsistent score field names. Resolution order:
1. `score_breakdown.total` (integer at top level of score_breakdown)
2. `scoring.total_score`
3. `score` (top level — sometimes 0 even when a real score exists elsewhere, check other fields first)

## Still Active Rendering

- Only render still_active rows for jobs where a verified JSON file can be read.
- Many still_active keys reference jobs from previous runs that no longer have files — skip those rows.
- Sort still_active table by score descending.

## Score Thresholds

- 90+ = green badge (color:#15803d; background:#f0fdf4)
- 70-89 = stone badge (color:#1c1917; background:#f8f8f6)
- Below 70 = omit entirely (do not render card or table row)

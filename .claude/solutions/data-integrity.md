# Solutions: data-integrity

## state-json-fallback-for-redis
- source: jsa-v17-analysis.md
- pattern: When Upstash Redis is unavailable, read action state from state.json. Enables graceful degradation for any external service dependency by maintaining a local fallback path.
- status: proposed

## semantic-dedup-over-slugs
- source: jsa-v18-analysis.md
- pattern: When automated dedup misses duplicates due to filename variation, dedup on normalized title+company fields inside the JSON rather than on filenames. Keep the highest-scoring version when duplicates are found.
- status: proposed

## presentation-layer-dedup-safety-net
- source: jsa-v19-analysis.md
- pattern: When data-layer dedup has limitations (e.g., slug-based matching misses cross-role duplicates), deduplicate at presentation time by keeping the highest-scoring instance per normalized company+title pair. Apply as a second dedup pass in any pipeline where upstream dedup is imperfect.
- status: proposed

## incremental-session-state-checkpointing
- source: jsa-v19-analysis.md
- pattern: Write session-state file after each batch (not just at session end) with batch number, role types processed, and cumulative counts. Enables resume capability on interruption. Apply to any multi-batch workflow that may be interrupted mid-session.
- status: proposed

## selective-cleanup-via-state-json
- source: jsa-v20-analysis.md
- pattern: Before pre-run cleanup of output files, read state.json to identify still-active entities. Delete only files for entities NOT tracked as active — preserve files for active entities across runs. Apply whenever a cleanup step could destroy data that downstream systems (e.g., dashboard APIs) depend on across multiple runs.
- status: proposed

## verify-before-brief-guard
- source: jsa-v21-analysis.md
- pattern: Before dispatching brief generators, glob for verified JSON existence. If missing, dispatch verification subagent first. Prevents wasted brief runs on incomplete upstream data. Apply to any pipeline with data-dependency gates between stages.
- status: proposed

## recovery-subagent-for-data-corruption
- source: jsa-v22-analysis.md
- pattern: When data corruption is detected mid-run (e.g., dedup archives live results), dispatch a dedicated recovery subagent to restore affected files rather than fixing inline in parent context. Note the root cause as a version-level fix rather than improvising a mid-run patch. Parent context stays clean; recovery is isolated.
- status: proposed

## unified-extract-score-function
- source: jsa-v23-analysis.md
- pattern: When multiple upstream sources produce the same semantic field (e.g., score) in different schema locations (top-level `score`, `scoring.total_score`, `score_breakdown.total`, `score.total`), build a single polymorphic extraction function that checks all known locations and returns a normalized value. Apply this defensive extraction at every consumption point rather than trusting upstream consistency. The reusable principle: in multi-source pipelines, normalize at consumption time, not at production time. Applied to manage_state.py and api/jobs.py.
- status: proposed

## schema-migration-gap-pattern
- source: eg-v2-analysis.md
- pattern: Schema changes made in create_tables() with IF NOT EXISTS are invisible to existing databases. All schema changes must use versioned migrations (ALTER TABLE with idempotency guards) rather than modifying the CREATE TABLE definition. When IF NOT EXISTS skips table creation, new columns are silently missing, causing IPC failures on any operation touching the database. Apply to any SQLite-backed app that evolves its schema across versions.
- status: proposed

## schema-migration-gate
- source: jsa-v24-analysis.md
- pattern: Validate → migrate → re-validate preserves data through format changes. Applicable to any pipeline with evolving output schemas. Apply as a 3-step guard when downstream processing requires a specific schema version and upstream output may be in legacy format.
- status: proposed

## unwrap-creep-error-propagation
- source: eg-v7-analysis.md
- pattern: When simplifying Rust return types by removing `Result` and using `.unwrap()`, recoverable errors become panics that crash the IPC bridge silently — the frontend receives no response, causing operations like Cmd+N to appear to do nothing. Prevention: enforce a clippy unwrap ban in all IPC command paths (`#[deny(clippy::unwrap_used)]`), require all Tauri commands to return `Result<T, EgError>`, and add CI grep for `.unwrap()` in `src-tauri/src/commands/`. Apply to any Rust backend where panics in command handlers produce silent frontend failures.
- status: proposed

## debounced-autosave-primary-mechanism
- source: eg-v15-analysis.md
- pattern: A 2-second debounced auto-save as the primary save mechanism is reliable and well-implemented. Manual save (Cmd+S) is secondary and supplements auto-save. Apply to any editor where content loss is the primary risk — auto-save eliminates the "forgot to save" class of data loss entirely.
- status: proposed

## filesystem-md-persistence
- source: eg-v15-analysis.md
- pattern: Persisting notes as .md files in a vault directory (vault/notes/) provides transparency, portability, and debuggability — files are readable in Finder, editable externally, and survive app crashes. The core principle: when the data format is human-readable text, store it as plain files rather than in a database. Apply when migrating from SQLite to filesystem-based storage for content that is inherently text.
- status: proposed

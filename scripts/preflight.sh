#!/usr/bin/env bash
# preflight.sh — V23 startup validation harness
#
# Usage:
#   preflight.sh             Run ALL tiers (env + structure)
#   preflight.sh --env       Run ONLY environment/runtime checks
#   preflight.sh --structure Run ONLY CLAUDE.md/reference structural checks
#
# Exit codes:
#   0 — all critical checks passed (warnings may have been emitted)
#   1 — one or more critical checks failed

set -euo pipefail

# ---------------------------------------------------------------------------
# Flag parsing (loop-based, supports --env and --structure)
# ---------------------------------------------------------------------------
RUN_ENV=false
RUN_STRUCTURE=false

if [[ $# -eq 0 ]]; then
    RUN_ENV=true
    RUN_STRUCTURE=true
else
    for arg in "$@"; do
        case "$arg" in
            --env)
                RUN_ENV=true
                ;;
            --structure)
                RUN_STRUCTURE=true
                ;;
            *)
                echo "Usage: preflight.sh [--env] [--structure]" >&2
                exit 1
                ;;
        esac
    done
fi

FAILED=0

fail() {
    echo "$1" >&2
    FAILED=1
}

warn() {
    echo "$1" >&2
}

# ===================================================================
# ENV TIER — environment / runtime checks
# ===================================================================
if [[ "$RUN_ENV" == "true" ]]; then

    # ------------------------------------------------------------------
    # Git pull (top of ENV tier)
    # ------------------------------------------------------------------
    if [[ "${SCHEDULED_RUN:-}" == "true" ]]; then
        echo "Skipping git pull (scheduled run)"
    else
        if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            git pull --ff-only 2>/dev/null || true
        fi
    fi

    # ------------------------------------------------------------------
    # Critical checks (exit 1 on failure)
    # ------------------------------------------------------------------

    # 1. Dashboard URL present in context.md
    if [[ ! -f "context.md" ]] || ! grep -q "Dashboard:" "context.md"; then
        fail "CRITICAL: Dashboard URL missing from context.md"
    fi

    # 2. settings.local.json has required permissions (Read, Write, Glob, Grep)
    #    Skipped in CI — claude-code-base-action handles permissions via allowed_tools param
    if [[ "${SCHEDULED_RUN:-}" == "true" ]]; then
        : # CI: permissions handled by action config, skip settings.local.json check
    elif [[ -f ".claude/settings.local.json" ]]; then
        SETTINGS_CONTENT=$(cat ".claude/settings.local.json")
        MISSING_PERMS=false
        for perm in Read Write Glob Grep; do
            if ! echo "$SETTINGS_CONTENT" | grep -q "\"$perm\""; then
                MISSING_PERMS=true
                break
            fi
        done
        if [[ "$MISSING_PERMS" == "true" ]]; then
            fail "CRITICAL: Required permissions missing from settings.local.json"
        fi
    else
        fail "CRITICAL: Required permissions missing from settings.local.json"
    fi

    # 3. .github/jsa-config.json exists and is valid JSON
    if [[ -f ".github/jsa-config.json" ]]; then
        if ! python3 -c "import json; json.load(open('.github/jsa-config.json'))" 2>/dev/null; then
            fail "CRITICAL: .github/jsa-config.json is invalid JSON"
        fi
    else
        fail "CRITICAL: .github/jsa-config.json is invalid JSON"
    fi

    # 4. scripts/manage_state.py exists and is executable
    if [[ ! -x "scripts/manage_state.py" ]]; then
        fail "CRITICAL: scripts/manage_state.py not found or not executable"
    fi

    # Bail early if any critical env check failed
    if [[ "$FAILED" -ne 0 ]]; then
        exit 1
    fi

    # ------------------------------------------------------------------
    # ON STARTUP state management (run after critical checks pass)
    # ------------------------------------------------------------------
    python3 scripts/manage_state.py cleanup
    python3 scripts/manage_state.py dedup

    # ------------------------------------------------------------------
    # CLI flag validation (exit 1 on failure)
    # ------------------------------------------------------------------
    if ! python3 scripts/manage_state.py dedup --dry-run --output-dir output 2>/dev/null; then
        fail "CRITICAL: manage_state.py dedup --dry-run flag validation failed"
    fi

    if [[ "$FAILED" -ne 0 ]]; then
        exit 1
    fi

    # ------------------------------------------------------------------
    # Non-critical checks (warn but continue)
    # ------------------------------------------------------------------

    # 1. .claude/agent-memory/ files are non-empty
    if [[ -d ".claude/agent-memory" ]]; then
        EMPTY_MEMORY=false
        while IFS= read -r -d '' memfile; do
            if [[ ! -s "$memfile" ]]; then
                EMPTY_MEMORY=true
                break
            fi
        done < <(find ".claude/agent-memory" -name "*.md" -print0 2>/dev/null)
        if [[ "$EMPTY_MEMORY" == "true" ]]; then
            warn "WARNING: Agent memory files are empty"
        fi
    fi

    # 2. references/ files exist for all phases
    MISSING_REFS=()
    EXPECTED_REFS=(orchestration.md presentation-rules.md subagent-search-verify.md subagent-digest-email.md)
    for ref in "${EXPECTED_REFS[@]}"; do
        if [[ ! -f "references/$ref" ]]; then
            MISSING_REFS+=("$ref")
        fi
    done
    if [[ ${#MISSING_REFS[@]} -gt 0 ]]; then
        warn "WARNING: Missing reference files: ${MISSING_REFS[*]}"
    fi

    # 3. No stale version references in GH Actions workflow
    if [[ -d ".github/workflows" ]]; then
        for wf in .github/workflows/*.yml .github/workflows/*.yaml; do
            [[ -f "$wf" ]] || continue
            if grep -qE "v[0-9]+[^0-9]" "$wf" 2>/dev/null; then
                # Check for references to old versions (not v22)
                if grep -E "v[0-9]+" "$wf" | grep -vq "v22" 2>/dev/null; then
                    warn "WARNING: Possible stale version references in $wf"
                fi
            fi
        done
    fi

    # 4. Repo-root workflow references current version directory
    REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    REPO_ROOT_WF="${REPO_ROOT}/.github/workflows/daily-digest.yml"
    if [[ -n "$REPO_ROOT" && -f "$REPO_ROOT_WF" ]]; then
        CURRENT_VERSION="v22"
        if grep -v '^\s*#' "$REPO_ROOT_WF" | grep -qE 'tests/v[0-9]+' && \
           ! grep -v '^\s*#' "$REPO_ROOT_WF" | grep -q "tests/${CURRENT_VERSION}"; then
            warn "WARNING: .github/workflows/daily-digest.yml does not reference ${CURRENT_VERSION} — update working-directory"
        fi
    else
        warn "WARNING: .github/workflows/daily-digest.yml not found at repo root"
    fi
fi

# ===================================================================
# STRUCTURE TIER — CLAUDE.md / reference structural checks
# ===================================================================
if [[ "$RUN_STRUCTURE" == "true" ]]; then

    # ------------------------------------------------------------------
    # Critical CLAUDE.md structure checks (exit 1 on failure)
    # ------------------------------------------------------------------

    if [[ ! -f "CLAUDE.md" ]]; then
        fail "CRITICAL: CLAUDE.md not found"
    else
        # 1. CLAUDE.md <= 280 lines
        LINE_COUNT=$(wc -l < "CLAUDE.md" | tr -d ' ')
        if [[ "$LINE_COUNT" -gt 280 ]]; then
            fail "CRITICAL: CLAUDE.md exceeds 280 lines ($LINE_COUNT lines)"
        fi

        # 2. Required sections exist
        for section in "## Hard Constraints" "## Context Budget" "## ON STARTUP"; do
            if ! grep -q "${section}" "CLAUDE.md"; then
                fail "CRITICAL: CLAUDE.md missing required section: $section"
            fi
        done

        # 3. Phase dispatch table has 5 phases
        for phase in Search Verify Dedup Present Deliver; do
            if ! grep -q "| ${phase} " "CLAUDE.md"; then
                fail "CRITICAL: CLAUDE.md missing phase in dispatch table: $phase"
            fi
        done

        # 4. Each dispatch row references a references/*.md file
        DISPATCH_ROWS=$(grep -E "^\| (Search|Verify|Dedup|Present|Deliver) " "CLAUDE.md" || true)
        if [[ -n "$DISPATCH_ROWS" ]]; then
            while IFS= read -r row; do
                if ! echo "$row" | grep -q "references/.*\.md"; then
                    fail "CRITICAL: Dispatch row missing references/*.md: $row"
                fi
            done <<< "$DISPATCH_ROWS"
        fi

        # 5. ON STARTUP references preflight.sh and manage_state.py
        if ! grep -q "preflight.sh" "CLAUDE.md"; then
            fail "CRITICAL: CLAUDE.md ON STARTUP missing preflight.sh reference"
        fi
        if ! grep -q "manage_state" "CLAUDE.md"; then
            fail "CRITICAL: CLAUDE.md ON STARTUP missing manage_state.py reference"
        fi
    fi

    # ------------------------------------------------------------------
    # Critical reference file content checks (exit 1 on failure)
    # ------------------------------------------------------------------

    # 1. references/orchestration.md contains phase headings for all 5 phases
    if [[ -f "references/orchestration.md" ]]; then
        for phase_num in 1 2 3 4 5; do
            if ! grep -q "## Phase ${phase_num}" "references/orchestration.md"; then
                fail "CRITICAL: references/orchestration.md missing Phase $phase_num heading"
            fi
        done
    else
        fail "CRITICAL: references/orchestration.md not found"
    fi

    # orchestration.md contains checkpoint validate for phases 2-5
    if [[ -f "references/orchestration.md" ]]; then
        ORCH_CONTENT=$(cat "references/orchestration.md")
        if ! echo "$ORCH_CONTENT" | grep -q "checkpoint validate"; then
            fail "CRITICAL: references/orchestration.md missing 'checkpoint validate' for gated phases"
        fi

        if ! echo "$ORCH_CONTENT" | grep -q "checkpoint write"; then
            fail "CRITICAL: references/orchestration.md missing 'checkpoint write' for phase completion"
        fi

        if ! echo "$ORCH_CONTENT" | grep -q "checkpoint clear"; then
            fail "CRITICAL: references/orchestration.md missing 'checkpoint clear' in Phase 1"
        fi
    fi

    # .checkpoints/ directory exists (or output/.checkpoints/)
    if [[ ! -d "output/.checkpoints" ]]; then
        warn "WARNING: output/.checkpoints/ directory does not exist (will be created on first run)"
    fi

    # Each agent .md has background: true
    if [[ -d ".claude/agents" ]]; then
        for agent_file in .claude/agents/*.md; do
            [[ -f "$agent_file" ]] || continue
            if ! grep -q "^background: true$" "$agent_file"; then
                fail "CRITICAL: $agent_file missing 'background: true' in frontmatter"
            fi
        done
    fi

    # Agent-memory startup read (HC4) — V14/V17/V19 three-time recurrence
    if [[ -f "CLAUDE.md" ]]; then
        if ! grep -q "\.claude/agent-memory" "CLAUDE.md"; then
            fail "CLAUDE.md missing agent-memory startup read (HC4)"
        fi
    fi

    # 2. references/presentation-rules.md contains table format section
    if [[ -f "references/presentation-rules.md" ]]; then
        if ! grep -q "Table Format" "references/presentation-rules.md"; then
            fail "CRITICAL: references/presentation-rules.md missing Table Format section"
        fi
    else
        fail "CRITICAL: references/presentation-rules.md not found"
    fi

    if [[ "$FAILED" -ne 0 ]]; then
        exit 1
    fi
fi

# ===================================================================
# SCHEMA TIER -- verified JSON schema validation checks
# ===================================================================
if [[ "$RUN_ENV" == "true" ]]; then

    # --- First-run detection ---
    # If output/verified/ is empty or missing, skip schema/model checks (nothing to validate).
    FIRST_RUN=false
    if [[ ! -d "output/verified" ]]; then
        FIRST_RUN=true
    else
        # Check if verified/ has any non-underscore JSON files in subdirs
        VERIFIED_COUNT=$(find "output/verified" -mindepth 2 -name "*.json" ! -name "_*" 2>/dev/null | head -1 | wc -l | tr -d ' ')
        if [[ "$VERIFIED_COUNT" -eq 0 ]]; then
            FIRST_RUN=true
        fi
    fi

    if [[ "$FIRST_RUN" == "true" ]]; then
        echo "First run detected (empty output/verified/) -- skipping schema validation"
    else
        # 1. Validate all verified JSONs conform to canonical schema
        if python3 scripts/manage_state.py validate-schema 2>/dev/null; then
            : # schema validation passed
        else
            fail "[PREFLIGHT FAIL] Schema validation failed -- run migrate-schema first"
        fi
    fi

    # 2. Verify search-verify agent is on Sonnet tier
    if [[ -f ".claude/agents/search-verify.md" ]]; then
        if ! grep -q "^model: sonnet$" ".claude/agents/search-verify.md"; then
            fail "[PREFLIGHT FAIL] search-verify agent not on Sonnet tier"
        fi
    else
        fail "[PREFLIGHT FAIL] search-verify agent not on Sonnet tier"
    fi

    if [[ "$FAILED" -ne 0 ]]; then
        exit 1
    fi
fi

# ===================================================================
# Final result
# ===================================================================
if [[ "$FAILED" -ne 0 ]]; then
    exit 1
fi

echo "Preflight checks passed."
exit 0

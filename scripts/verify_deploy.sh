#!/usr/bin/env bash
# verify_deploy.sh — Consolidated pre-deploy and post-deploy verification
# Run from the repo root: bash scripts/verify_deploy.sh
# Exits non-zero if any check fails.

set -euo pipefail

# ---------------------------------------------------------------------------
# Path setup — resolve repo root relative to this script's location
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# scripts/ -> repo root
AGENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# ---------------------------------------------------------------------------
# Counters and helpers
# ---------------------------------------------------------------------------
PASS=0
FAIL=0

pass() {
    echo "[PASS] $1"
    PASS=$(( PASS + 1 ))
}

fail() {
    echo "[FAIL] $1"
    FAIL=$(( FAIL + 1 ))
}

warn() {
    echo "[WARN] $1"
}

section() {
    echo ""
    echo "--- $1 ---"
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
echo "========================================"
echo "  JSA V23 Deployment Verification"
echo "========================================"
echo "Repo root : ${REPO_ROOT}"
echo "Agent dir : ${AGENT_DIR}"
echo ""

# ---------------------------------------------------------------------------
# 1. Lint
# ---------------------------------------------------------------------------
section "1. Lint (ruff)"
SCRIPTS_DIR="${AGENT_DIR}/scripts"
if ruff check "${SCRIPTS_DIR}" > /tmp/ruff_out 2>&1; then
    pass "ruff check ${SCRIPTS_DIR} exits 0"
else
    fail "ruff check ${SCRIPTS_DIR} — $(cat /tmp/ruff_out | head -5)"
fi

# ---------------------------------------------------------------------------
# 2. Test count
# ---------------------------------------------------------------------------
section "2. Test count (pytest)"
TESTS_DIR="${AGENT_DIR}/tests"
if pytest_out=$(python3 -m pytest "${TESTS_DIR}" --co -q 2>&1 | tail -1); then
    # Extract the leading number from lines like "160 tests collected" or "160 selected"
    count=$(echo "${pytest_out}" | grep -oE '^[0-9]+' || true)
    if [[ -n "${count}" ]] && (( count >= 160 )); then
        pass "pytest collected ${count} tests (>= 160 required)"
    else
        fail "pytest test count: '${pytest_out}' — expected >= 160 tests collected"
    fi
else
    fail "pytest --collect-only failed"
fi

# ---------------------------------------------------------------------------
# 3. Key file existence
# ---------------------------------------------------------------------------
section "3. Key file existence"

KEY_FILES=(
    "${AGENT_DIR}/CLAUDE.md"
    "${AGENT_DIR}/context.md"
    "${AGENT_DIR}/references/orchestration.md"
    "${AGENT_DIR}/scripts/manage_state.py"
    "${AGENT_DIR}/scripts/preflight.sh"
    "${AGENT_DIR}/scripts/send_email.py"
    "${REPO_ROOT}/.github/workflows/daily-digest.yml"
)

for f in "${KEY_FILES[@]}"; do
    if [[ -f "${f}" ]]; then
        # Print path relative to repo root for readability
        rel="${f#${REPO_ROOT}/}"
        pass "exists: ${rel}"
    else
        rel="${f#${REPO_ROOT}/}"
        fail "missing: ${rel}"
    fi
done

# ---------------------------------------------------------------------------
# 4. HC1 reversal — no "model: inherit" in agent frontmatter
# ---------------------------------------------------------------------------
section "4. HC1 reversal (no 'model: inherit' in agent files)"
AGENTS_DIR="${AGENT_DIR}/.claude/agents"
if [[ -d "${AGENTS_DIR}" ]]; then
    # Count matching files; grep exits 1 on no match, so use || true to avoid pipefail
    inherit_matches=0
    _tmp_inherit=$(grep -rl "model: inherit" "${AGENTS_DIR}" 2>/dev/null || true)
    if [[ -n "${_tmp_inherit}" ]]; then
        inherit_matches=$(echo "${_tmp_inherit}" | wc -l | tr -d ' ')
    fi
    if [[ "${inherit_matches}" -eq 0 ]]; then
        pass "zero 'model: inherit' occurrences found in ${AGENTS_DIR}"
    else
        fail "'model: inherit' found in ${inherit_matches} file(s) — HC1 reversal incomplete"
        echo "${_tmp_inherit}" | while IFS= read -r f; do
            [[ -n "${f}" ]] && echo "       -> ${f#${REPO_ROOT}/}"
        done
    fi
else
    fail "agents directory not found: ${AGENTS_DIR}"
fi

# ---------------------------------------------------------------------------
# 5. Model tier settings — at least 5 agent files with explicit "model:" line
# ---------------------------------------------------------------------------
section "5. Model tier settings (explicit model: in agent files)"
if [[ -d "${AGENTS_DIR}" ]]; then
    model_files=0
    _tmp_model=$(grep -rl "^model:" "${AGENTS_DIR}" 2>/dev/null || true)
    if [[ -n "${_tmp_model}" ]]; then
        model_files=$(echo "${_tmp_model}" | wc -l | tr -d ' ')
    fi
    if (( model_files >= 5 )); then
        pass "${model_files} agent file(s) have explicit 'model:' setting (>= 5 required)"
    else
        fail "only ${model_files} agent file(s) have explicit 'model:' setting — need >= 5"
    fi
else
    fail "agents directory not found: ${AGENTS_DIR}"
fi

# ---------------------------------------------------------------------------
# 6. Orchestration references
# ---------------------------------------------------------------------------
section "6. Orchestration references"
ORCH_FILE="${AGENT_DIR}/references/orchestration.md"

if [[ -f "${ORCH_FILE}" ]]; then
    # 6a. 5-channel search pattern
    channel_count=$(grep -cE "5-channel|five.channel|Five.Channel" "${ORCH_FILE}" 2>/dev/null || true)
    if (( channel_count >= 1 )); then
        pass "orchestration.md references 5-channel search (${channel_count} match(es))"
    else
        fail "orchestration.md has no '5-channel' / 'five channel' / 'Five Channel' references"
    fi

    # 6b. Gate references
    gate_count=$(grep -cE "verify-channels-dispatched|verify-session-state-updated|verify-clean-working-tree" "${ORCH_FILE}" 2>/dev/null || true)
    if (( gate_count >= 2 )); then
        pass "orchestration.md has ${gate_count} gate reference(s) (>= 2 required)"
    else
        fail "orchestration.md has only ${gate_count} gate reference(s) — need >= 2 (verify-channels-dispatched, verify-session-state-updated, verify-clean-working-tree)"
    fi
else
    fail "orchestration.md not found: ${ORCH_FILE}"
fi

# ---------------------------------------------------------------------------
# 7. Email CLI flag verification (V21 regression)
# ---------------------------------------------------------------------------
section "7. Email CLI flag verification (V21 regression)"

if [[ -f "${ORCH_FILE}" ]]; then
    # 7a. --body-file must be present
    bodyfile_count=$(grep -cE "body-file|--body-file" "${ORCH_FILE}" 2>/dev/null || true)
    if (( bodyfile_count >= 1 )); then
        pass "orchestration.md references --body-file (${bodyfile_count} match(es))"
    else
        fail "orchestration.md has no '--body-file' references — V21 regression fix may be missing"
    fi

    # 7b. --html (as a bare CLI flag) must NOT be present
    # We check for " --html " (space-bounded) to avoid false positives on "html": in JSON
    html_flag_count=$(grep -cE " --html " "${ORCH_FILE}" 2>/dev/null || true)
    if (( html_flag_count == 0 )); then
        pass "orchestration.md has zero ' --html ' CLI flag references (correct)"
    else
        fail "orchestration.md contains ${html_flag_count} ' --html ' CLI flag reference(s) — should use --body-file instead"
    fi
else
    fail "orchestration.md not found: ${ORCH_FILE}"
fi

# ---------------------------------------------------------------------------
# 8. Dashboard health check
# ---------------------------------------------------------------------------
section "8. Dashboard health (jsa-dashboard.vercel.app)"
DASHBOARD_URL="https://jsa-dashboard.vercel.app/api/state"
if response=$(curl -sf --max-time 10 "${DASHBOARD_URL}" 2>/dev/null); then
    if echo "${response}" | python3 -c "import sys, json; d=json.load(sys.stdin); assert 'run_date' in d" 2>/dev/null; then
        run_date=$(echo "${response}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('run_date','unknown'))" 2>/dev/null || echo "unknown")
        pass "dashboard API returned valid JSON with run_date='${run_date}'"
    else
        fail "dashboard API returned a response but missing 'run_date' key — response: ${response:0:200}"
    fi
else
    warn "dashboard health check skipped — no network access or endpoint unavailable (${DASHBOARD_URL})"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "========================================"
TOTAL=$(( PASS + FAIL ))
echo "  Summary: ${PASS} passed, ${FAIL} failed (${TOTAL} checks)"
echo "========================================"

if (( FAIL > 0 )); then
    exit 1
fi

exit 0

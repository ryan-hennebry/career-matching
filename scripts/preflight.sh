#!/usr/bin/env bash
# Bash wrapper for existing users. The Python entry point works without Bash.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
exec python3 scripts/career_match.py check "$@"

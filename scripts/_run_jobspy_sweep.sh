#!/usr/bin/env bash
# jun22 jobspy-script-proper-run sweep (tiered to limit LinkedIn rate-limiting)
set -u
cd "$(dirname "$0")/.."

slug() { echo "$1" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//; s/-$//'; }

run() {
  local role="$1" loc="$2"
  local rslug lslug out
  rslug=$(slug "$role"); lslug=$(slug "$loc")
  out="output/jobs/raw-${rslug}__${lslug}.json"
  echo ">>> ${role} @ ${loc} -> ${out}"
  python3 scripts/jobspy_search.py "$role" --location "$loc" --country UK --results 50 --hours-old 48 --output "$out" 2>>output/jobs/_sweep.log
  sleep 3
}

# Tier 1: ALL roles across the whole UK (captures remote + every city in one pass)
ALL_ROLES=(
  "founding marketer" "founding growth" "community manager" "community lead"
  "founder's associate" "chief of staff" "growth associate" "GTM associate"
  "operations associate" "member experience" "developer relations"
  "lifecycle marketing" "partnerships associate" "business operations associate"
)
for role in "${ALL_ROLES[@]}"; do
  run "$role" "United Kingdom"
done

# Tier 2: highest-signal founding/community/growth terms, city-scoped (regional hubs)
CITY_ROLES=("founding marketer" "founding growth" "community manager" "founder's associate" "growth associate" "chief of staff")
CITIES=("London, United Kingdom" "Cambridge, United Kingdom" "Oxford, United Kingdom" "Bristol, United Kingdom" "Edinburgh, United Kingdom" "Manchester, United Kingdom")
for role in "${CITY_ROLES[@]}"; do
  for city in "${CITIES[@]}"; do
    run "$role" "$city"
  done
done

echo "SWEEP_DONE"

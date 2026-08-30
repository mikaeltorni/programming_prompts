#!/usr/bin/env bash
# Self-test for diagnose_job.sh against synthetic Harbor job dirs.
# Usage: bash lib/self_test_diagnose.sh   (silent, no Docker, no GUI)
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/diagnose_job.sh"

fails=0
check() { # $1 label, $2 needle, $3 haystack
  if [[ "$3" == *"$2"* ]]; then
    echo "PASS $1"
  else
    echo "FAIL $1 (missing: $2)"
    fails=$((fails + 1))
  fi
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Case 1: containers removed mid-run.
job="$tmp/wiped"
mkdir -p "$job/trial-1"
printf 'Trial calculator cancelled\nno container found for service main\n' >"$job/job.log"
out="$(diagnose_failed_job "$job" wiped 1 2>&1)"
check "wiped: reports missing containers" "Trial containers disappeared mid-run" "$out"
check "wiped: shows counts" "missing-container=1" "$out"

# Case 2: cancellations without container removal.
job="$tmp/cancelled"
mkdir -p "$job/trial-1" "$job/trial-2"
printf 'Trial greeter cancelled\nTrial todo cancelled\n' >"$job/job.log"
out="$(diagnose_failed_job "$job" cancelled 1 2>&1)"
check "cancelled: reports cancellation" "Harbor cancelled trials before they scored" "$out"
check "cancelled: counts trial dirs" "trial dirs=2" "$out"

# Case 3: no log at all — must still return cleanly.
job="$tmp/empty"
mkdir -p "$job"
out="$(diagnose_failed_job "$job" empty 0 2>&1)"
check "empty: falls back to log pointer" "No cancellation signature found" "$out"

# Case 4: exception counting.
job="$tmp/exc"
mkdir -p "$job/trial-1" "$job/trial-2"
echo 'ApiRateLimitError' >"$job/trial-1/exception.txt"
echo 'EnvironmentStartTimeoutError' >"$job/trial-2/exception.txt"
got="$(count_trial_exceptions "$job" 'ApiRateLimitError')"
check "exceptions: counts matching only" "1" "$got"

if [[ "$fails" -gt 0 ]]; then
  echo "$fails case(s) failed"
  exit 1
fi
echo "all cases passed"

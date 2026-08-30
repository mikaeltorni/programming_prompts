# Explain why a Harbor job produced no usable trials.
#
# A wiped-out job used to abort the wrapper under `set -e`: Harbor exited
# non-zero, no summary was captured, no RESULTS.txt row was written, and the
# user was left with a bare "0/140" and nothing in the run archive to read.
# `diagnose_failed_job` turns that into an explicit, archived explanation.

# Count trials whose exception.txt matches a pattern.
#
# Parameters: $1 - Harbor job directory; $2 - extended regex.
# Prints the count on stdout (machine-readable; callers substitute it).
count_trial_exceptions() {
  local job_dir="$1"
  local pattern="$2"
  local count=0
  local f
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    if grep -Eq "$pattern" "$f"; then
      count=$((count + 1))
    fi
  done < <(find "$job_dir" -mindepth 2 -maxdepth 2 -name exception.txt 2>/dev/null)
  printf '%s\n' "$count"
}

# Report the likely cause of a job with no scored trials, on stderr.
#
# Parameters: $1 - Harbor job directory; $2 - job name; $3 - harbor exit code.
# Returns: 0 always (diagnosis is best-effort and never aborts delivery).
diagnose_failed_job() {
  local job_dir="$1"
  local job_name="$2"
  local harbor_rc="${3:-0}"
  local log_file="$job_dir/job.log"
  local trials cancelled no_container

  trials="$(find "$job_dir" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
  cancelled=0
  no_container=0
  if [[ -f "$log_file" ]]; then
    cancelled="$(grep -cE '^Trial .* cancelled' "$log_file" 2>/dev/null || true)"
    no_container="$(grep -cF 'no container found for service' "$log_file" 2>/dev/null || true)"
  fi
  : "${cancelled:=0}"
  : "${no_container:=0}"

  echo "DIAGNOSIS for job $job_name (harbor exit $harbor_rc):" >&2
  echo "  trial dirs=$trials cancelled=$cancelled missing-container=$no_container" >&2
  if [[ "$no_container" -gt 0 ]]; then
    echo "  Trial containers disappeared mid-run. Something removed them:" >&2
    echo "  an overlapping ./run_benchmark.sh reclaim sweep, a manual" >&2
    echo "  'docker rm/prune', or the Docker daemon restarting." >&2
    echo "  Reclaim now protects containers owned by a live run stamp; check" >&2
    echo "  'docker_networks: reclaim protects live run stamp(s)' on stderr." >&2
  elif [[ "$cancelled" -gt 0 ]]; then
    echo "  Harbor cancelled trials before they scored. Read $log_file and" >&2
    echo "  the per-trial exception.txt files under $job_dir." >&2
  else
    echo "  No cancellation signature found; read $log_file for the cause." >&2
  fi
  echo "  Full Harbor log: $log_file" >&2
  return 0
}

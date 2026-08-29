# Initialize, summarize, synchronize, and finalize benchmark archives.

print_summary() {
  python3 "$SCRIPT_DIR/lib/print_summary.py" "$1" "$2" "$3"
}

capture_print_summary() {
  local jobs_root="$1"
  local run_mode="$2"
  local skills_csv="$3"
  local summary_file="${4:-}"
  if [[ -z "$summary_file" ]]; then
    summary_file="$(mktemp)"
  fi
  # Capture stderr summary to a file, then replay it to the console.
  print_summary "$jobs_root" "$run_mode" "$skills_csv" 2>"$summary_file" || true
  cat "$summary_file" >&2
  SUMMARY_CAPTURE_FILE="$summary_file"
}

archive_sync_job() {
  local job_name="$1"
  local summary_file="${2:-${SUMMARY_CAPTURE_FILE:-}}"
  python3 "$SCRIPT_DIR/archive_benchmark_run.py" sync-job \
    --run-dir "$RUN_DIR" \
    --jobs-root "$JOBS" \
    --job-name "$job_name" \
    --summary-file "$summary_file" >/dev/null
  if [[ -n "$summary_file" && "$summary_file" == "$SUMMARY_CAPTURE_FILE" ]]; then
    rm -f "$SUMMARY_CAPTURE_FILE"
    SUMMARY_CAPTURE_FILE=""
  elif [[ -n "$summary_file" ]]; then
    rm -f "$summary_file"
  fi
  echo "written to: $RUN_DIR/jobs/$job_name" >&2
}

archive_finalize() {
  local summary_args=()
  if [[ -n "${SUMMARY_CAPTURE_FILE:-}" && -f "${SUMMARY_CAPTURE_FILE:-}" ]]; then
    summary_args=(--summary-file "$SUMMARY_CAPTURE_FILE")
  fi
  python3 "$SCRIPT_DIR/archive_benchmark_run.py" finalize \
    --run-dir "$RUN_DIR" \
    --jobs-root "$JOBS" \
    "${summary_args[@]}" >/dev/null
  if [[ -n "${SUMMARY_CAPTURE_FILE:-}" ]]; then
    rm -f "$SUMMARY_CAPTURE_FILE"
    SUMMARY_CAPTURE_FILE=""
  fi
  echo "written to: $RUN_DIR" >&2
}

init_run_archive() {
  local mode_label="$1"
  ATTEMPTS_PER_TASK=5
  local i
  for ((i = 0; i < ${#HARBOR_ARGS[@]}; i++)); do
    if [[ "${HARBOR_ARGS[$i]}" == "-k" || "${HARBOR_ARGS[$i]}" == "--n-attempts" ]]; then
      ATTEMPTS_PER_TASK="${HARBOR_ARGS[$((i + 1))]:-$ATTEMPTS_PER_TASK}"
    fi
  done
  # User -n is stripped before this runs. RESULTS n is the Harbor concurrency
  # the wrapper will set (always follow -k).
  CONCURRENT="$ATTEMPTS_PER_TASK"
  mkdir -p "$RUNS_ROOT"
  local -a archive_init_args=(
    --runs-root "$RUNS_ROOT"
    --timestamp "$RUN_STAMP"
    --mode "$mode_label"
    --attempts "$ATTEMPTS_PER_TASK"
    --concurrent "$CONCURRENT"
    --command "./run_benchmark.sh $(printf '%q ' "${ORIGINAL_ARGV[@]}")"
  )
  local _h _s _t
  for _h in "${SELECTED_HARNESSES[@]}"; do
    archive_init_args+=(--harness "$_h")
  done
  if [[ ${#SELECTED_EVAL_AGENTS[@]} -gt 0 ]]; then
    local _e
    for _e in "${SELECTED_EVAL_AGENTS[@]}"; do
      archive_init_args+=(--eval-agent "$_e")
    done
  fi
  for _s in "${SELECTED_SKILLS[@]}"; do
    archive_init_args+=(--skill "$_s")
  done
  for _t in "${SELECTED_TASKS[@]}"; do
    archive_init_args+=(--task "$_t")
  done
  if [[ "$RUN_SEPARATELY" -eq 1 ]]; then
    archive_init_args+=(--separately)
  fi
  RUN_DIR="$(python3 "$SCRIPT_DIR/archive_benchmark_run.py" init "${archive_init_args[@]}")"
  export RUN_DIR
  if [[ -n "$JOBS_FROM_ENV" ]]; then
    JOBS="$JOBS_FROM_ENV"
  else
    JOBS="$RUN_DIR/harbor"
  fi
  mkdir -p "$JOBS"
  echo "Run archive: $RUN_DIR" >&2
  echo "Jobs directory: $JOBS" >&2
}

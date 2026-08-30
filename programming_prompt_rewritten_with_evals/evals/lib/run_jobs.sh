# Configure and execute individual jobs and per-harness job groups.
# Combined (default): every selected skill in one agent session, all matching
# judges AND the same tree for Pass. --run-separately: still that one Harbor
# job (same trial count); judges run independently and Pass is not AND.

run_one_job() {
  local harness="$1"
  local job_name="$2"
  local run_mode="$3"
  shift 3
  local -a skill_paths=("$@")

  local skills_csv
  skills_csv="$(printf '%s,' "${SELECTED_SKILLS_FOR_JOB[@]:-}")"
  skills_csv="${skills_csv%,}"

  local tasks_root
  tasks_root="$(prepare_job_tasks "$job_name" "${SELECTED_SKILLS_FOR_JOB[@]}")"

  local config_file
  if [[ "$BASELINE" -eq 1 ]]; then
    config_file="$JOBS/harbor.${job_name}.yaml"
    write_job_config "$harness" "$config_file" "[]" "$tasks_root"
  else
    config_file="$JOBS/harbor.${job_name}.yaml"
    write_job_config "$harness" "$config_file" "$(skills_yaml_block "${skill_paths[@]}")" "$tasks_root"
  fi

  collect_artifact_flags
  local -a common=(
    -c "$config_file"
    -o "$JOBS"
    "${ARTIFACT_FLAGS[@]}"
  )

  local -a harbor_args=("${HARBOR_ARGS[@]}")
  local i
  if [[ ${#harbor_args[@]} -eq 0 ]]; then
    harbor_args=(--job-name "$job_name" -k 5)
  else
    local has_job_name=0
    for ((i = 0; i < ${#harbor_args[@]}; i++)); do
      if [[ "${harbor_args[$i]}" == "--job-name" ]]; then
        harbor_args[$((i + 1))]="${job_name}"
        has_job_name=1
      fi
    done
    if [[ "$has_job_name" -eq 0 ]]; then
      harbor_args=(--job-name "$job_name" "${harbor_args[@]}")
    fi
  fi

  local attempts_per_task=5
  for ((i = 0; i < ${#harbor_args[@]}; i++)); do
    if [[ "${harbor_args[$i]}" == "-k" || "${harbor_args[$i]}" == "--n-attempts" ]]; then
      attempts_per_task="${harbor_args[$((i + 1))]:-$attempts_per_task}"
    fi
  done
  # User -n is stripped in run_benchmark.sh. Harbor -n always follows -k so
  # docker compose build stays inside the 300s environment-start budget.
  local concurrent_for_job="$attempts_per_task"
  local task_count
  task_count="$(list_task_dirs | wc -l | tr -d ' ')"
  echo "Job $job_name [$harness] schedules about $((task_count * attempts_per_task)) trials ($attempts_per_task attempts × $task_count tasks)." >&2
  echo "Job $job_name judges: ${SELECTED_SKILLS_FOR_JOB[*]:-(none)} (isolated under $tasks_root)" >&2
  echo "Model default: $(harness_model_name "$harness") @ reasoning_effort=low (CLI $(harness_cli_version "$harness"))" >&2
  echo "Job $job_name evalAgent: $(eval_agents_csv_for_harness "$harness") (inherit if evalAgent omitted)" >&2
  echo "Job $job_name retries ApiRateLimitError up to 4 times (backoff 5–60s)." >&2

  local docker_holder="${RUN_STAMP}:${job_name}"
  local granted_slots=""
  if harbor_uses_per_trial_networks; then
    acquire_docker_slots "$docker_holder" "$concurrent_for_job" granted_slots
    echo "Job $job_name concurrent trials follow -k $attempts_per_task → $granted_slots." >&2
    if [[ "$granted_slots" != "$concurrent_for_job" ]]; then
      echo "Docker IPAM/LLM cap clamped job $job_name -n $concurrent_for_job → $granted_slots" >&2
    fi
    set_harbor_n_concurrent harbor_args "$granted_slots"
  elif harbor_uses_docker_env; then
    echo "Job $job_name: Harbor trials use Docker's default bridge (no per-trial user-defined network)." >&2
    acquire_docker_slots "$docker_holder" "$concurrent_for_job" granted_slots ignore-ipam
    echo "Job $job_name concurrent trials follow -k $attempts_per_task → $granted_slots." >&2
    if [[ "$granted_slots" != "$concurrent_for_job" ]]; then
      echo "LLM cap clamped job $job_name -n $concurrent_for_job → $granted_slots" >&2
    fi
    set_harbor_n_concurrent harbor_args "$granted_slots"
  else
    echo "Skipping Docker IPAM for $job_name (Harbor --env is not docker)." >&2
    echo "Job $job_name concurrent trials follow -k $attempts_per_task → $concurrent_for_job." >&2
    set_harbor_n_concurrent harbor_args "$concurrent_for_job"
  fi

  # Never let a non-zero Harbor exit abort the wrapper under `set -e`: a job
  # that lost its trials still has to release slots, summarize, and archive,
  # otherwise the user sees a bare 0/N with no RESULTS row and no reason.
  local harbor_rc=0
  run_harbor_for_harness "$harness" "${common[@]}" "${harbor_args[@]}" || harbor_rc=$?
  release_docker_slots
  reclaim_docker_leftovers
  if [[ "$harbor_rc" -ne 0 ]]; then
    echo "Harbor exited $harbor_rc for job $job_name; summarizing and archiving anyway." >&2
    diagnose_failed_job "$JOBS/$job_name" "$job_name" "$harbor_rc"
  fi
  local summary_file
  summary_file="$(mktemp)"
  capture_print_summary "$JOBS/$job_name" "$run_mode" "$skills_csv" "$summary_file"
  archive_sync_job "$job_name" "$summary_file"
  if [[ "$harbor_rc" -eq 0 ]] && ! job_scored_any_trial "$JOBS/$job_name"; then
    echo "Job $job_name scored 0 trials even though Harbor exited 0." >&2
    diagnose_failed_job "$JOBS/$job_name" "$job_name" "$harbor_rc"
  fi
  JOB_HARBOR_RC="$harbor_rc"
}

# Whether any trial in a Harbor job wrote a reward file.
#
# Parameters: $1 - Harbor job directory.
# Returns: 0 when at least one *reward*.json exists.
job_scored_any_trial() {
  local job_dir="$1"
  [[ -n "$(find "$job_dir" -mindepth 2 -maxdepth 2 -name '*reward*.json' -print -quit 2>/dev/null)" ]]
}

run_jobs_for_harness() {
  local harness="$1"
  if [[ "$RUN_SEPARATELY" -eq 1 ]]; then
    echo "NOTE: --run-separately is one Harbor job (same trial count as combined)." >&2
    echo "Skills are scored independently; Pass is not AND. Per-skill columns are the scores." >&2
  fi
  SELECTED_SKILLS_FOR_JOB=("${SELECTED_SKILLS[@]}")
  if [[ "$BASELINE" -eq 1 ]]; then
    run_one_job "$harness" "$(harbor_job_name "${harness}-baseline")" "baseline"
  else
    local -a skill_paths=()
    local skill
    for skill in "${SELECTED_SKILLS[@]}"; do
      skill_paths+=("$SKILLS_ROOT/$skill")
    done
    run_one_job "$harness" "$(harbor_job_name "${harness}-skills")" "positive" "${skill_paths[@]}"
  fi
}

# Configure and execute individual jobs and per-harness job groups.

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
  local user_passed_n=0
  local concurrent_for_job=5
  for ((i = 0; i < ${#harbor_args[@]}; i++)); do
    if [[ "${harbor_args[$i]}" == "-k" || "${harbor_args[$i]}" == "--n-attempts" ]]; then
      attempts_per_task="${harbor_args[$((i + 1))]:-$attempts_per_task}"
    fi
    if [[ "${harbor_args[$i]}" == "-n" || "${harbor_args[$i]}" == "--n-concurrent" ]]; then
      user_passed_n=1
      concurrent_for_job="${harbor_args[$((i + 1))]:-$concurrent_for_job}"
    fi
  done
  if [[ "$user_passed_n" -eq 0 ]]; then
    concurrent_for_job="$attempts_per_task"
  fi
  local task_count
  task_count="$(list_task_dirs | wc -l | tr -d ' ')"
  echo "Job $job_name [$harness] schedules about $((task_count * attempts_per_task)) trials ($attempts_per_task attempts × $task_count tasks)." >&2
  echo "Job $job_name judges: ${SELECTED_SKILLS_FOR_JOB[*]:-(none)} (isolated under $tasks_root)" >&2
  echo "Model default: $(harness_model_name "$harness") @ reasoning_effort=low (CLI $(harness_cli_version "$harness"))" >&2
  echo "Job $job_name evalAgent: $(eval_agents_csv_for_harness "$harness") (inherit if evalAgent omitted)" >&2

  local docker_holder="${RUN_STAMP}:${job_name}"
  local granted_slots=""
  if harbor_uses_per_trial_networks; then
    acquire_docker_slots "$docker_holder" "$concurrent_for_job" granted_slots
    if [[ "$user_passed_n" -eq 0 ]]; then
      echo "Job $job_name omitted -n; following -k $attempts_per_task → $granted_slots concurrent trial(s)." >&2
    elif [[ "$granted_slots" != "$concurrent_for_job" ]]; then
      echo "Docker IPAM/LLM cap clamped job $job_name -n $concurrent_for_job → $granted_slots" >&2
    fi
    set_harbor_n_concurrent harbor_args "$granted_slots"
  elif harbor_uses_docker_env; then
    echo "Job $job_name: Harbor trials use Docker's default bridge (no per-trial user-defined network)." >&2
    acquire_docker_slots "$docker_holder" "$concurrent_for_job" granted_slots ignore-ipam
    if [[ "$user_passed_n" -eq 0 ]]; then
      echo "Job $job_name omitted -n; following -k $attempts_per_task → $granted_slots concurrent trial(s)." >&2
    elif [[ "$granted_slots" != "$concurrent_for_job" ]]; then
      echo "LLM cap clamped job $job_name -n $concurrent_for_job → $granted_slots" >&2
    fi
    set_harbor_n_concurrent harbor_args "$granted_slots"
  else
    echo "Skipping Docker IPAM for $job_name (Harbor --env is not docker)." >&2
    if [[ "$user_passed_n" -eq 0 ]]; then
      echo "Job $job_name omitted -n; following -k $attempts_per_task → $concurrent_for_job concurrent trial(s)." >&2
      set_harbor_n_concurrent harbor_args "$concurrent_for_job"
    fi
  fi

  run_harbor_for_harness "$harness" "${common[@]}" "${harbor_args[@]}"
  release_docker_slots
  reclaim_docker_leftovers
  local summary_file
  summary_file="$(mktemp)"
  capture_print_summary "$JOBS/$job_name" "$run_mode" "$skills_csv" "$summary_file"
  archive_sync_job "$job_name" "$summary_file"
}

run_jobs_for_harness() {
  local harness="$1"
  if [[ "$RUN_SEPARATELY" -eq 1 ]]; then
    run_separately_jobs_for_harness "$harness"
  else
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
  fi
}

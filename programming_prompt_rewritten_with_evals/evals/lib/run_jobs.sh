# Configure and execute individual jobs and per-harness job groups.
# Combined (default): every selected skill in one agent session, all matching
# judges AND the same tree for Pass. --run-separately: still that one Harbor
# job (same trial count); judges run independently and Pass is not AND.

run_one_job() {
  # Run and archive one shared Harbor schedule for the selected task families.
  # Parameters: $1 - harness; $2 - job name; $3 - mode.
  # Returns: None; records the Harbor exit code in JOB_HARBOR_RC.
  local harness="$1"
  local job_name="$2"
  local run_mode="$3"

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
    local bundle="$JOBS/instruction-bundles/$job_name/global-instructions"
    prepare_instruction_bundle "$bundle" "${SELECTED_SKILLS_FOR_JOB[@]}" || return 1
    write_job_config "$harness" "$config_file" "$(skills_yaml_block "$bundle")" "$tasks_root"
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
  local task_count
  task_count="$(list_task_dirs | wc -l | tr -d ' ')"
  # Raw Harbor -n is stripped in run_benchmark.sh. The wrapper can explicitly
  # schedule distinct tasks together without multiplying attempts per task.
  local concurrent_for_job
  concurrent_for_job="$(resolve_job_concurrency "$attempts_per_task" \
    "$((task_count * attempts_per_task))" "$CONCURRENCY_ARG")"
  echo "Job $job_name [$harness] schedules about $((task_count * attempts_per_task)) trials ($attempts_per_task attempts × $task_count tasks)." >&2
  echo "Job $job_name judges: ${SELECTED_SKILLS_FOR_JOB[*]:-(none)} (isolated under $tasks_root)" >&2
  echo "Model default: $(harness_model_name "$harness") @ reasoning_effort=low (CLI $(harness_cli_version "$harness"))" >&2
  echo "Job $job_name evalAgent: $(eval_agents_csv_for_harness "$harness") (inherit if evalAgent omitted)" >&2
  echo "Job $job_name retries ApiRateLimitError up to 4 times (backoff 5–60s)." >&2

  local docker_holder="${RUN_STAMP}:${job_name}"
  local granted_slots=""
  if harbor_uses_per_trial_networks; then
    acquire_docker_slots "$docker_holder" "$concurrent_for_job" granted_slots
    echo "Job $job_name concurrent trials requested=$concurrent_for_job → $granted_slots." >&2
    if [[ "$granted_slots" != "$concurrent_for_job" ]]; then
      echo "Docker IPAM/LLM cap clamped job $job_name -n $concurrent_for_job → $granted_slots" >&2
    fi
    set_harbor_n_concurrent harbor_args "$granted_slots"
  elif harbor_uses_docker_env; then
    echo "Job $job_name: Harbor trials use Docker's default bridge (no per-trial user-defined network)." >&2
    acquire_docker_slots "$docker_holder" "$concurrent_for_job" granted_slots ignore-ipam
    echo "Job $job_name concurrent trials requested=$concurrent_for_job → $granted_slots." >&2
    if [[ "$granted_slots" != "$concurrent_for_job" ]]; then
      echo "LLM cap clamped job $job_name -n $concurrent_for_job → $granted_slots" >&2
    fi
    set_harbor_n_concurrent harbor_args "$granted_slots"
  else
    echo "Skipping Docker IPAM for $job_name (Harbor --env is not docker)." >&2
    echo "Job $job_name concurrent trials requested=$concurrent_for_job." >&2
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

# Whether any trial in a Harbor job wrote its aggregate reward file.
#
# Parameters: $1 - Harbor job directory.
# Returns: 0 when at least one trial/verifier/reward.json exists.
job_scored_any_trial() {
  local job_dir="$1"
  [[ -n "$(find "$job_dir" -mindepth 3 -maxdepth 3 -type f -path '*/verifier/reward.json' -print -quit 2>/dev/null)" ]]
}

run_jobs_for_harness() {
  # Submit all selected families to one Harbor scheduler and capacity budget.
  # Parameters: $1 - harness identifier.
  # Returns: None after the job finishes; propagates setup failures.
  local harness="$1"
  local -a SELECTED_SKILLS_FOR_JOB=() family_skills=()
  local family task skill known_skill selected has_coding=0 has_debug=0
  for task in "${SELECTED_TASKS[@]}"; do
    family="$(task_family "$task")" || return 1
    if [[ "$family" == coding ]]; then has_coding=1; else has_debug=1; fi
  done
  for family in coding debug; do
    if [[ "$family" == coding && "$has_coding" -eq 0 ]] || [[ "$family" == debug && "$has_debug" -eq 0 ]]; then
      continue
    fi
    mapfile -t family_skills < <(skills_for_task_family "$family" "${SELECTED_SKILLS[@]}")
    for skill in "${family_skills[@]}"; do
      selected=0
      for known_skill in "${SELECTED_SKILLS_FOR_JOB[@]:-}"; do
        [[ "$known_skill" == "$skill" ]] && selected=1
      done
      [[ "$selected" -eq 1 ]] || SELECTED_SKILLS_FOR_JOB+=("$skill")
    done
  done
  if [[ ${#SELECTED_SKILLS_FOR_JOB[@]} -eq 0 ]]; then
    echo 'No applicable skills for selected tasks' >&2
    return 1
  fi
  if [[ "$RUN_SEPARATELY" -eq 1 ]]; then
    echo "NOTE: --run-separately scores skills independently on their applicable task family." >&2
  fi
  local suffix='' mode=positive label=skills
  [[ "$has_coding" -eq 0 ]] && suffix=-debug
  if [[ "$BASELINE" -eq 1 ]]; then mode=baseline; label=baseline; fi
  echo "One Harbor job schedules coding=$has_coding debug=$has_debug together; trial policies and judges stay family-specific." >&2
  run_one_job "$harness" "$(harbor_job_name "${harness}${suffix}-${label}")" "$mode"
}

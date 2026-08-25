# Fan out --run-separately Harbor jobs under the Docker IPAM slot cap.

separately_requested_n() {
  # Each skill job's requested -n (defaults match run_one_job / init_run_archive).
  printf '%s\n' "${CONCURRENT:-5}"
}

run_one_separately_skill() {
  # One skill → one Harbor job. Used by both sequential fallback and the pool.
  local harness="$1"
  local skill="$2"
  SELECTED_SKILLS_FOR_JOB=("$skill")
  if [[ "$BASELINE" -eq 1 ]]; then
    run_one_job "$harness" "$(harbor_job_name "${harness}-baseline-$skill")" "baseline"
  else
    run_one_job "$harness" "$(harbor_job_name "${harness}-$skill")" "positive" "$SKILLS_ROOT/$skill"
  fi
}

_separately_plan() {
  # Print "n_per workers free" for *skill_n* jobs requesting *n_req* each.
  local skill_n="$1"
  local n_req="$2"
  if harbor_uses_docker_env; then
    python3 "$DOCKER_NETWORKS" fair-share --jobs "$skill_n" --requested "$n_req"
  else
    echo "Harbor --env is not docker; skipping IPAM fair-share for $skill_n separately job(s)." >&2
    printf '%s %s %s\n' "$n_req" "$skill_n" "-"
  fi
}

run_separately_jobs_for_harness() {
  # Launch one Harbor job per selected skill, concurrently, capped by IPAM.
  local harness="$1"
  local skill_n="${#SELECTED_SKILLS[@]}"
  local n_req
  n_req="$(separately_requested_n)"
  echo "Running each selected skill in its own prompt instance for harness=$harness (--run-separately)." >&2

  local n_per workers free
  read -r n_per workers free < <(_separately_plan "$skill_n" "$n_req")
  if [[ -z "$n_per" || -z "$workers" ]]; then
    echo "Failed to plan separately parallelism (n_per='$n_per' workers='$workers')." >&2
    return 1
  fi
  echo "=== separately: ${skill_n} skill job(s) for harness=${harness}; up to ${workers} in parallel at -n ${n_per} (requested -n ${n_req}; IPAM free=${free}) ===" >&2

  if [[ "$skill_n" -le 1 ]]; then
    local skill="${SELECTED_SKILLS[0]}"
    echo "=== separately skill 1/1: ${skill} (harness=${harness}) ===" >&2
    SEPARATELY_N_CONCURRENT="$n_per" SEPARATELY_QUIET=0 run_one_separately_skill "$harness" "$skill"
    return
  fi

  local fifo sem
  fifo="$(mktemp -u "${TMPDIR:-/tmp}/harbor-separately.XXXXXX")"
  mkfifo "$fifo"
  exec {sem}<>"$fifo"
  rm -f "$fifo"
  local token_i
  for ((token_i = 0; token_i < workers; token_i++)); do
    echo >&"$sem"
  done

  local -a pids=()
  local skill skill_i=0 quiet=0
  if [[ "$workers" -gt 1 ]]; then
    quiet=1
    echo "Harbor --quiet is on for parallel skill jobs so trial TUIs do not interleave; watch $JOBS/<job>/ and the skill banners." >&2
  fi
  for skill in "${SELECTED_SKILLS[@]}"; do
    skill_i=$((skill_i + 1))
    read -r -u "$sem"
    (
      _docker_slot_holder=""
      trap 'on_eval_shell_exit; echo >&'"$sem"' || true' EXIT
      echo "=== separately skill ${skill_i}/${skill_n}: ${skill} (harness=${harness}) [parallel] ===" >&2
      SEPARATELY_N_CONCURRENT="$n_per" SEPARATELY_QUIET="$quiet" \
        run_one_separately_skill "$harness" "$skill"
    ) &
    pids+=("$!")
    echo "Started separately skill ${skill_i}/${skill_n}: ${skill} pid=${pids[-1]}" >&2
  done

  local status=0 pid
  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      echo "Separately skill job pid=$pid failed for harness=$harness." >&2
      status=1
    fi
  done
  exec {sem}>&-
  return "$status"
}

# Fan out --run-separately Harbor jobs one skill at a time.

run_separately_jobs_for_harness() {
  # One Harbor job per selected skill, sequential. Parallel skill jobs used
  # to unpack a unique 3.6G trial image each and fire every coding agent at
  # once, which filled the disk and burned API rate limits.
  local harness="$1"
  local skill_n="${#SELECTED_SKILLS[@]}"
  echo "Running each selected skill in its own prompt instance for harness=$harness (--run-separately)." >&2
  echo "=== separately: ${skill_n} skill job(s) for harness=${harness}; sequential (one Harbor job at a time) ===" >&2
  local skill skill_i=0 status=0
  for skill in "${SELECTED_SKILLS[@]}"; do
    skill_i=$((skill_i + 1))
    echo "=== separately skill ${skill_i}/${skill_n}: ${skill} (harness=${harness}) ===" >&2
    if ! run_one_separately_skill "$harness" "$skill"; then
      echo "Separately skill job ${skill} failed for harness=$harness." >&2
      status=1
    fi
  done
  return "$status"
}

run_one_separately_skill() {
  # One skill → one Harbor job.
  local harness="$1"
  local skill="$2"
  SELECTED_SKILLS_FOR_JOB=("$skill")
  if [[ "$BASELINE" -eq 1 ]]; then
    run_one_job "$harness" "$(harbor_job_name "${harness}-baseline-$skill")" "baseline"
  else
    run_one_job "$harness" "$(harbor_job_name "${harness}-$skill")" "positive" "$SKILLS_ROOT/$skill"
  fi
}

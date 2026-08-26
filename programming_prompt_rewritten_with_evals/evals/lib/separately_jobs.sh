# --run-separately used to start one Harbor job per skill, which looked like
# the benchmark running again after the first skill's trials finished.

run_separately_jobs_for_harness() {
  # One Harbor job with every selected skill — same as combined mode.
  local harness="$1"
  echo "NOTE: --run-separately does not start extra Harbor jobs." >&2
  echo "All selected skills (${SELECTED_SKILLS[*]}) run together in one job for harness=$harness." >&2
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

# Name Harbor jobs and generate their YAML and artifact arguments.

harbor_job_name() {
  # Harbor refuses to reuse an existing job dir with a different config.
  printf '%s__%s\n' "$1" "$RUN_STAMP"
}

collect_artifact_flags() {
  # Download the simulated Projects/ tree (cloned repo + sibling .worktrees)
  # so the run archive can reconstruct the host layout. /app is a symlink
  # into /Projects/app; listing it separately would collide with /Projects.
  ARTIFACT_FLAGS=(--artifact /Projects)
}

write_job_config() {
  # Materialize one Harbor job YAML. Retry ApiRateLimitError so overlapping
  # -k 20 jobs can run at CPU/disk speed: a Codex 429 requeues the trial
  # with backoff instead of leaving an unmerged worktree. Pass harbor -r 0
  # to disable. Do not retry usage-limit / timeout / reward-file errors.
  # Parameters: $1 - harness; $2 - YAML destination; $3 - skills YAML; $4 - task root.
  # Returns: None; writes the job configuration.
  printf 'harness=%s config_file=%s skills_block=%s tasks_root=%s\n' "$1" "$2" "$3" "$4" >&2
  local harness="$1"
  local config_file="$2"
  local skills_block="$3"
  local tasks_root="$4"
  local import_path model_name version
  import_path="$(harness_import_path "$harness")"
  model_name="$(harness_model_name "$harness")"
  version="$(harness_cli_version "$harness")"
  cat >"$config_file" <<EOF
retry:
  max_retries: 4
  include_exceptions:
    - ApiRateLimitError
  wait_multiplier: 2.0
  min_wait_sec: 5.0
  max_wait_sec: 60.0

agents:
  - import_path: ${import_path}
    model_name: ${model_name}
    skills: ${skills_block}
    # Multi-stage agents were still progressing at the task's 600-second cutoff.
    # Extend only execution; setup/verifier limits and capacity stay independent.
    override_timeout_sec: 1200.0
    kwargs:
      version: "${version}"
      reasoning_effort: low

tasks:
$(yaml_task_entries "$tasks_root")
EOF
  printf 'None\n' >&2
}

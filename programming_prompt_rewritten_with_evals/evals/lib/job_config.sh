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
  local harness="$1"
  local config_file="$2"
  local skills_block="$3"
  local tasks_root="$4"
  local import_path model_name version
  import_path="$(harness_import_path "$harness")"
  model_name="$(harness_model_name "$harness")"
  version="$(harness_cli_version "$harness")"
  cat >"$config_file" <<EOF
agents:
  - import_path: ${import_path}
    model_name: ${model_name}
    skills: ${skills_block}
    kwargs:
      version: "${version}"
      reasoning_effort: low

tasks:
$(yaml_task_entries "$tasks_root")
EOF
}

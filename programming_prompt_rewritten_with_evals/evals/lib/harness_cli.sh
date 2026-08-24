# Resolve harness aliases, metadata, and evaluation-agent settings.

normalize_harness() {
  python3 "$HARNESS_SPEC" normalize "${1:-}"
}

harness_import_path() {
  python3 "$HARNESS_SPEC" field "$1" import_path
}

harness_model_name() {
  python3 "$HARNESS_SPEC" field "$1" model_name
}

harness_cli_version() {
  python3 "$HARNESS_SPEC" version "$1"
}

harness_mounts_json() {
  python3 "$HARNESS_SPEC" mounts "$@"
}

eval_agents_for_harness() {
  # Inherit the coding harness when evalAgent was omitted.
  if [[ ${#SELECTED_EVAL_AGENTS[@]} -eq 0 ]]; then
    printf '%s\n' "$1"
  else
    printf '%s\n' "${SELECTED_EVAL_AGENTS[@]}"
  fi
}

eval_agents_csv_for_harness() {
  local -a agents=()
  mapfile -t agents < <(eval_agents_for_harness "$1")
  local IFS=','
  printf '%s' "${agents[*]}"
}

resolve_eval_models_csv() {
  local agents_csv="$1"
  python3 "$HARNESS_SPEC" eval-models "$agents_csv" "$EVAL_AGENT_MODEL_ARG"
}

resolve_eval_efforts_csv() {
  local agents_csv="$1"
  python3 "$HARNESS_SPEC" eval-efforts "$agents_csv" "$EVAL_AGENT_EFFORT_ARG"
}

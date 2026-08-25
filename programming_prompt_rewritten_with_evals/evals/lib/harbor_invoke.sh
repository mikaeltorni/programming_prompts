# Assemble credentials, mounts, and arguments for one Harbor invocation.

run_harbor_for_harness() {
  local harness="$1"
  shift
  local -a eval_agents=()
  mapfile -t eval_agents < <(eval_agents_for_harness "$harness")
  local eval_csv models_csv efforts_csv
  eval_csv="$(eval_agents_csv_for_harness "$harness")"
  models_csv="$(resolve_eval_models_csv "$eval_csv")" || exit 1
  efforts_csv="$(resolve_eval_efforts_csv "$eval_csv")" || exit 1
  echo "Job evalAgent(s): ${eval_agents[*]} models=$models_csv effort=$efforts_csv" >&2

  local mounts version
  mounts="$(harness_mounts_json "$harness" "${eval_agents[@]}")"
  version="$(harness_cli_version "$harness")"
  local -a env_flags=()
  local -a seen_env_keys=()
  local line oauth_harness pair key
  # Static pairs must use "true", not "1": Harbor scrubs sensitive env VALUES
  # from trial outputs (keys matching AUTH/TOKEN/…). Value "1" rewrites every
  # reward 1.0 into invalid JSON ("[REDACTED].0") and breaks our summary.
  add_env_pair() {
    local candidate="$1"
    local cand_key="${candidate%%=*}"
    local existing
    for existing in "${seen_env_keys[@]:-}"; do
      if [[ "$existing" == "$cand_key" ]]; then
        return 0
      fi
    done
    seen_env_keys+=("$cand_key")
    env_flags+=("$candidate")
  }

  while IFS= read -r line; do
    [[ -n "$line" ]] && add_env_pair "$line"
  done < <(python3 "$HARNESS_SPEC" static-env "$harness")
  append_oauth_env "$harness" env_flags
  for oauth_harness in "${eval_agents[@]}"; do
    while IFS= read -r line; do
      [[ -n "$line" ]] && add_env_pair "$line"
    done < <(python3 "$HARNESS_SPEC" static-env "$oauth_harness")
    if [[ "$oauth_harness" != "$harness" ]]; then
      append_oauth_env "$oauth_harness" env_flags
    fi
  done
  add_env_pair "EVAL_AGENTS=$eval_csv"
  add_env_pair "EVAL_AGENT_MODELS=$models_csv"
  add_env_pair "EVAL_AGENT_REASONING_EFFORT=$efforts_csv"
  if [[ -n "${EVAL_JUDGE_WORKERS:-}" ]]; then
    add_env_pair "EVAL_JUDGE_WORKERS=$EVAL_JUDGE_WORKERS"
  fi
  # Verifier must see the same secrets (--ve). Agent phase still uses --ae.
  local -a ve_flags=(
    --ve "EVAL_AGENTS=$eval_csv"
    --ve "EVAL_AGENT_MODELS=$models_csv"
    --ve "EVAL_AGENT_REASONING_EFFORT=$efforts_csv"
  )
  for pair in "${env_flags[@]}"; do
    key="${pair%%=*}"
    case "$key" in
      EVAL_AGENTS|EVAL_AGENT_MODELS|EVAL_AGENT_REASONING_EFFORT) ;;
      *) ve_flags+=(--ve "$pair") ;;
    esac
  done

  # Judges run concurrently inside the verifier, so wall time is about one
  # judge timeout — not agents × skills. Leave Harbor's default multiplier.

  # Env vars must be visible to Harbor's agent process; export for this call only.
  # Clear EXIT so this subshell does not inherit the wrapper's slot/FIFO trap —
  # otherwise Harbor's return would release IPAM slots and separately worker
  # tokens before run_one_job finishes summarizing.
  (
    trap - EXIT
    export "${env_flags[@]}"
    local -a ae_flags=()
    for pair in "${env_flags[@]}"; do
      ae_flags+=(--ae "$pair")
    done
    harbor run \
      --mounts "$mounts" \
      --ak "version=$version" \
      "${ae_flags[@]}" \
      "${ve_flags[@]}" \
      "$@"
  )
}

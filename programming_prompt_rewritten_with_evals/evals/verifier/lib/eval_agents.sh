#!/usr/bin/env bash
# Parse eval-agent, model, and reasoning-effort configuration.

csv_trim_lower() {
  local raw="${1:-}"
  local IFS=','
  local -a parts=()
  local part
  read -r -a parts <<<"$raw"
  local -a out=()
  for part in "${parts[@]}"; do
    part="$(echo "$part" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
    [[ -n "$part" ]] && out+=("$part")
  done
  (IFS=','; printf '%s' "${out[*]}")
}

default_eval_model() {
  case "$1" in
    cc) printf '%s' "claude-opus-5" ;;
    grok) printf '%s' "grok-4.6" ;;
    *) printf '%s' "gpt-5.6-luna" ;;
  esac
}

configure_eval_agents() {
  local agents_csv models_csv efforts_csv agent_count idx value
  local -a model_parts=() models_trim=() effort_parts=() efforts_trim=()

  agents_csv="$(csv_trim_lower "${EVAL_AGENTS:-codex}")"
  [[ -n "$agents_csv" ]] || agents_csv="codex"
  IFS=',' read -r -a EVAL_AGENT_LIST <<<"$agents_csv"
  echo "Eval agent(s): ${EVAL_AGENT_LIST[*]}" >&2

  models_csv="${EVAL_AGENT_MODELS:-}"
  efforts_csv="$(csv_trim_lower "${EVAL_AGENT_REASONING_EFFORT:-}")"
  EVAL_MODELS=()
  EVAL_EFFORTS=()
  agent_count="${#EVAL_AGENT_LIST[@]}"

  if [[ -z "$models_csv" ]]; then
    for value in "${EVAL_AGENT_LIST[@]}"; do
      EVAL_MODELS+=("$(default_eval_model "$value")")
    done
  else
    IFS=',' read -r -a model_parts <<<"$models_csv"
    for value in "${model_parts[@]}"; do
      value="$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -n "$value" ]] && models_trim+=("$value")
    done
    if [[ "${#models_trim[@]}" -eq 1 ]]; then
      for ((idx = 0; idx < agent_count; idx++)); do
        EVAL_MODELS+=("${models_trim[0]}")
      done
    elif [[ "${#models_trim[@]}" -eq "$agent_count" ]]; then
      EVAL_MODELS=("${models_trim[@]}")
    else
      echo "EVAL_AGENT_MODELS has ${#models_trim[@]} value(s) but EVAL_AGENTS has $agent_count" >&2
      return 1
    fi
  fi

  if [[ -z "$efforts_csv" ]]; then
    for ((idx = 0; idx < agent_count; idx++)); do
      EVAL_EFFORTS+=("low")
    done
  else
    IFS=',' read -r -a effort_parts <<<"$efforts_csv"
    for value in "${effort_parts[@]}"; do
      value="$(echo "$value" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
      [[ -n "$value" ]] && efforts_trim+=("$value")
    done
    if [[ "${#efforts_trim[@]}" -eq 1 ]]; then
      for ((idx = 0; idx < agent_count; idx++)); do
        EVAL_EFFORTS+=("${efforts_trim[0]}")
      done
    elif [[ "${#efforts_trim[@]}" -eq "$agent_count" ]]; then
      EVAL_EFFORTS=("${efforts_trim[@]}")
    else
      echo "EVAL_AGENT_REASONING_EFFORT has ${#efforts_trim[@]} value(s) but EVAL_AGENTS has $agent_count" >&2
      return 1
    fi
  fi

  echo "Eval agent models: ${EVAL_MODELS[*]}" >&2
  echo "Eval agent reasoning effort: ${EVAL_EFFORTS[*]}" >&2
}

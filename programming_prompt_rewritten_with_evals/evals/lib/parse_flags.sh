# Canonical CLI flag parsing for run_benchmark.sh.
#
# One format for every wrapper parameter: a long, double-dashed, kebab-case
# flag whose value is the next argument — `--skills commits,srp`. The
# `--skills=commits,srp` spelling is accepted as the same flag for scripted
# callers; nothing else is.
#
# The wrapper used to accept four spellings per parameter (`--harness codex`,
# `--harness=codex`, `harness=codex`, and camelCase `--evalAgentModel`), so
# copied commands drifted between styles and a misspelling such as
# `harnes=codex` fell through to Harbor as an unknown positional instead of
# failing. Legacy spellings now fail with the canonical flag to use.
#
# Components:
#   benchmark_flag_die   — error helper (stderr, non-zero return)
#   benchmark_flag_value — read a required value for a flag
#   parse_benchmark_flags — the parser; sets the wrapper's globals
#
# Usage (from run_benchmark.sh): parse_benchmark_flags "$@" || exit 1

# Canonical value-taking flags, for error messages and the self-test.
BENCHMARK_VALUE_FLAGS=(--harness --eval-agent --eval-agent-model \
  --eval-agent-reasoning-effort --skills --tasks)

# Report a CLI error on stderr.
#
# Parameters: $@ - message words.
# Returns 1 always, so callers can `benchmark_flag_die … && return 1`.
benchmark_flag_die() {
  echo "$*" >&2
  return 1
}

# Reject a legacy spelling by naming the canonical flag.
#
# Parameters: $1 - the argument as typed; $2 - the canonical flag.
# Returns 1 always.
benchmark_flag_legacy() {
  benchmark_flag_die "Unsupported option format '$1' — use '$2 <value>'." \
    "Every wrapper parameter takes the same form: $(printf '%s ' "${BENCHMARK_VALUE_FLAGS[@]}")"
}

# Validate the value that follows a value-taking flag.
#
# Parameters: $1 - flag name; $2 - candidate value (may be empty/missing);
#             $3 - hint shown when the value is missing.
# Prints the value on stdout (machine-readable; the caller substitutes it).
# Returns 1 when the value is missing or is itself a flag.
benchmark_flag_value() {
  local flag="$1" value="${2:-}" hint="$3"
  if [[ -z "$value" || "$value" == -* ]]; then
    benchmark_flag_die "$flag requires a value ($hint)" || return 1
  fi
  printf '%s' "$value"
}

# Parse the wrapper's own flags, leaving everything else for Harbor.
#
# Parameters: $@ - the command line as given to run_benchmark.sh.
# Sets: INSTALL_ONLY, PIN_REFRESH, BASELINE, RUN_SEPARATELY, SKILLS_ARG,
# TASKS_ARG, HARNESS_ARG, EVAL_AGENT_ARG, EVAL_AGENT_MODEL_ARG,
# EVAL_AGENT_EFFORT_ARG, HARBOR_ARGS.
# Returns 1 on an unusable or legacy-format argument.
parse_benchmark_flags() {
  local harness_hint="${BENCHMARK_HARNESS_CHOICES:-codex, cc, grok, both, all}"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --install-only)
        INSTALL_ONLY=1
        shift
        ;;
      --no-pin-refresh)
        PIN_REFRESH=0
        shift
        ;;
      --pin-refresh)
        PIN_REFRESH=1
        shift
        ;;
      --baseline)
        BASELINE=1
        shift
        ;;
      --run-separately)
        RUN_SEPARATELY=1
        shift
        ;;
      --negative|--oneshot|--anti-srp)
        benchmark_flag_die \
          "Unknown option $1 (inverted-skill mode was removed; use --baseline for no-skill runs)" \
          || return 1
        ;;
      --harness)
        HARNESS_ARG="$(benchmark_flag_value --harness "${2:-}" "$harness_hint")" || return 1
        shift 2
        ;;
      --harness=*)
        HARNESS_ARG="$(benchmark_flag_value --harness "${1#*=}" "$harness_hint")" || return 1
        shift
        ;;
      --eval-agent)
        EVAL_AGENT_ARG="$(benchmark_flag_value --eval-agent "${2:-}" "$harness_hint")" || return 1
        shift 2
        ;;
      --eval-agent=*)
        EVAL_AGENT_ARG="$(benchmark_flag_value --eval-agent "${1#*=}" "$harness_hint")" || return 1
        shift
        ;;
      --eval-agent-model)
        EVAL_AGENT_MODEL_ARG="$(benchmark_flag_value --eval-agent-model "${2:-}" \
          "a model id, same idea as -m / --model")" || return 1
        shift 2
        ;;
      --eval-agent-model=*)
        EVAL_AGENT_MODEL_ARG="$(benchmark_flag_value --eval-agent-model "${1#*=}" \
          "a model id, same idea as -m / --model")" || return 1
        shift
        ;;
      --eval-agent-reasoning-effort)
        EVAL_AGENT_EFFORT_ARG="$(benchmark_flag_value --eval-agent-reasoning-effort "${2:-}" \
          "low, medium, or high")" || return 1
        shift 2
        ;;
      --eval-agent-reasoning-effort=*)
        EVAL_AGENT_EFFORT_ARG="$(benchmark_flag_value --eval-agent-reasoning-effort "${1#*=}" \
          "low, medium, or high")" || return 1
        shift
        ;;
      --skills)
        SKILLS_ARG="$(benchmark_flag_value --skills "${2:-}" "a list like srp,commenting")" || return 1
        shift 2
        ;;
      --skills=*)
        SKILLS_ARG="$(benchmark_flag_value --skills "${1#*=}" "a list like srp,commenting")" || return 1
        shift
        ;;
      --tasks)
        TASKS_ARG="$(benchmark_flag_value --tasks "${2:-}" "a list like todo,calculator")" || return 1
        shift 2
        ;;
      --tasks=*)
        TASKS_ARG="$(benchmark_flag_value --tasks "${1#*=}" "a list like todo,calculator")" || return 1
        shift
        ;;
      # Legacy spellings — same parameters, wrong format.
      --no-skill) benchmark_flag_legacy "$1" --baseline || return 1 ;;
      --offline-pins) benchmark_flag_legacy "$1" --no-pin-refresh || return 1 ;;
      --runSeparately) benchmark_flag_legacy "$1" --run-separately || return 1 ;;
      harness=*) benchmark_flag_legacy "$1" --harness || return 1 ;;
      evalAgent=*|eval-agent=*|--evalAgent|--evalAgent=*) \
        benchmark_flag_legacy "$1" --eval-agent || return 1 ;;
      evalAgentModel=*|eval-agent-model=*|--evalAgentModel|--evalAgentModel=*) \
        benchmark_flag_legacy "$1" --eval-agent-model || return 1 ;;
      evalAgentReasoningEffort=*|eval-agent-reasoning-effort=*|--evalAgentReasoningEffort|--evalAgentReasoningEffort=*) \
        benchmark_flag_legacy "$1" --eval-agent-reasoning-effort || return 1 ;;
      skills=*|-skills=*|-skills) benchmark_flag_legacy "$1" --skills || return 1 ;;
      tasks=*|task=*|-tasks=*|-task=*|-tasks|-task|--task|--task=*) \
        benchmark_flag_legacy "$1" --tasks || return 1 ;;
      --)
        shift
        HARBOR_ARGS+=("$@")
        break
        ;;
      *)
        HARBOR_ARGS+=("$1")
        shift
        ;;
    esac
  done
}

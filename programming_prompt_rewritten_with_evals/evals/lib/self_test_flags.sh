#!/usr/bin/env bash
# Self-test for parse_flags.sh — the canonical `--flag value` CLI format.
# Usage: bash lib/self_test_flags.sh   (silent, no Docker, no LLM, no GUI)
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/parse_flags.sh"

fails=0

# Reset the wrapper globals the parser writes into.
reset_globals() {
  INSTALL_ONLY=0
  PIN_REFRESH=1
  BASELINE=0
  RUN_SEPARATELY=0
  SKILLS_ARG=""
  TASKS_ARG=""
  HARNESS_ARG=""
  EVAL_AGENT_ARG=""
  EVAL_AGENT_MODEL_ARG=""
  EVAL_AGENT_EFFORT_ARG=""
  HARBOR_ARGS=()
}

check() { # $1 label, $2 expected, $3 actual
  if [[ "$3" == "$2" ]]; then
    echo "PASS $1"
  else
    echo "FAIL $1 (expected: $2 | actual: $3)"
    fails=$((fails + 1))
  fi
}

check_rejects() { # $1 label, $2 canonical flag expected in the message, $@ argv
  local label="$1" canonical="$2"
  shift 2
  reset_globals
  local out rc
  out="$(parse_benchmark_flags "$@" 2>&1)"
  rc=$?
  if [[ $rc -eq 0 ]]; then
    echo "FAIL $label (accepted instead of rejecting)"
    fails=$((fails + 1))
  elif [[ "$out" != *"$canonical"* ]]; then
    echo "FAIL $label (message did not name $canonical: $out)"
    fails=$((fails + 1))
  else
    echo "PASS $label"
  fi
}

# Case 1: canonical space-separated values (the documented format).
reset_globals
parse_benchmark_flags --harness codex --eval-agent codex --skills commits,srp \
  --tasks bank,stats --eval-agent-model gpt-5.6-luna \
  --eval-agent-reasoning-effort low -k 15
check "space form: harness" "codex" "$HARNESS_ARG"
check "space form: eval agent" "codex" "$EVAL_AGENT_ARG"
check "space form: skills" "commits,srp" "$SKILLS_ARG"
check "space form: tasks" "bank,stats" "$TASKS_ARG"
check "space form: eval agent model" "gpt-5.6-luna" "$EVAL_AGENT_MODEL_ARG"
check "space form: eval agent effort" "low" "$EVAL_AGENT_EFFORT_ARG"
check "space form: harbor passthrough" "-k 15" "${HARBOR_ARGS[*]}"

# Case 2: the `=` spelling of the same flags.
reset_globals
parse_benchmark_flags --harness=cc --eval-agent=codex --skills=logging \
  --tasks=todo --eval-agent-model=grok-4.6 --eval-agent-reasoning-effort=high
check "equals form: harness" "cc" "$HARNESS_ARG"
check "equals form: eval agent" "codex" "$EVAL_AGENT_ARG"
check "equals form: skills" "logging" "$SKILLS_ARG"
check "equals form: tasks" "todo" "$TASKS_ARG"
check "equals form: eval agent model" "grok-4.6" "$EVAL_AGENT_MODEL_ARG"
check "equals form: eval agent effort" "high" "$EVAL_AGENT_EFFORT_ARG"

# Case 3: switches and Harbor passthrough, including after `--`.
reset_globals
parse_benchmark_flags --install-only --no-pin-refresh --baseline \
  --run-separately -- --ak reasoning_effort=high
check "switch: install only" "1" "$INSTALL_ONLY"
check "switch: pin refresh off" "0" "$PIN_REFRESH"
check "switch: baseline" "1" "$BASELINE"
check "switch: run separately" "1" "$RUN_SEPARATELY"
check "passthrough after --" "--ak reasoning_effort=high" "${HARBOR_ARGS[*]}"
reset_globals
parse_benchmark_flags --pin-refresh
check "switch: pin refresh on" "1" "$PIN_REFRESH"

# Case 4: every legacy spelling is rejected and names its canonical flag.
check_rejects "legacy: bare harness=" "--harness" harness=codex
check_rejects "legacy: bare evalAgent=" "--eval-agent" evalAgent=codex
check_rejects "legacy: bare eval-agent=" "--eval-agent" eval-agent=codex
check_rejects "legacy: camelCase --evalAgent" "--eval-agent" --evalAgent codex
check_rejects "legacy: camelCase --evalAgent=" "--eval-agent" --evalAgent=codex
check_rejects "legacy: camelCase model" "--eval-agent-model" --evalAgentModel=grok-4.6
check_rejects "legacy: camelCase effort" "--eval-agent-reasoning-effort" \
  --evalAgentReasoningEffort=low
check_rejects "legacy: bare tasks=" "--tasks" tasks=bank
check_rejects "legacy: bare task=" "--tasks" task=bank
check_rejects "legacy: singular --task" "--tasks" --task bank
check_rejects "legacy: single-dash -skills=" "--skills" -skills=srp
check_rejects "legacy: single-dash -tasks=" "--tasks" -tasks=bank
check_rejects "legacy: --runSeparately" "--run-separately" --runSeparately
check_rejects "legacy: --no-skill" "--baseline" --no-skill
check_rejects "legacy: --offline-pins" "--no-pin-refresh" --offline-pins

# Case 5: a value flag with no value fails instead of eating the next flag.
check_rejects "missing value: --skills at end" "--skills requires a value" --skills
check_rejects "missing value: --tasks before a flag" "--tasks requires a value" \
  --tasks --harness codex
check_rejects "missing value: --harness empty =" "--harness requires a value" --harness=

# Case 6: removed inverted-skill modes still explain themselves.
check_rejects "removed: --negative" "--baseline" --negative

# Case 7: --help prints the canonical usage and asks the caller to exit 0.
reset_globals
help_out="$(parse_benchmark_flags --help)"; help_rc=$?
check "help: rc 10 (caller exits 0)" "10" "$help_rc"
if [[ "$help_out" == *"--harness <codex|cc|grok|both|all>"* ]]; then
  echo "PASS help: lists canonical flags"
else
  echo "FAIL help: usage text missing canonical flags"
  fails=$((fails + 1))
fi

if [[ $fails -eq 0 ]]; then
  echo "ALL FLAG PARSING SELF-TESTS PASSED"
else
  echo "$fails flag parsing self-test(s) failed"
fi
exit $((fails > 0))

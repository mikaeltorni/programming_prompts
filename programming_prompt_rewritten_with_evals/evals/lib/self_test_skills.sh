#!/usr/bin/env bash
# Self-test default and explicit skill discovery without Docker, a GUI, or LLMs.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/skills_tasks.sh"

fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT
SKILLS_ROOT="$fixture/skills"
JUDGES_ROOT="$fixture/judges"
mkdir -p "$SKILLS_ROOT/standard" "$SKILLS_ROOT/workflow" \
  "$SKILLS_ROOT/logging-vague" "$JUDGES_ROOT/standard" \
  "$JUDGES_ROOT/workflow" "$JUDGES_ROOT/logging"
printf '%s\n' '---' >"$SKILLS_ROOT/standard/SKILL.md"
printf '%s\n' '---' >"$SKILLS_ROOT/workflow/SKILL.md"
printf '%s\n' '---' >"$SKILLS_ROOT/logging-vague/SKILL.md"
printf '%s\n' 'explicit-only' >"$SKILLS_ROOT/workflow/.opt-in"
: >"$JUDGES_ROOT/standard/prompt.md"
: >"$JUDGES_ROOT/workflow/prompt.md"
: >"$JUDGES_ROOT/logging/prompt.md"

fails=0

check() { # $1 label, $2 expected, $3 actual
  if [[ "$3" == "$2" ]]; then
    echo "PASS $1"
  else
    echo "FAIL $1 (expected: $2 | actual: $3)"
    fails=$((fails + 1))
  fi
}

check "default excludes opt-in and vague skills" "standard" \
  "$(list_available_skills)"
check "default resolution stays legacy-only" "standard" \
  "$(resolve_skills '')"
check "explicit workflow selection resolves" "workflow" \
  "$(resolve_skills workflow)"
check "mixed explicit selection preserves order" $'standard\nworkflow' \
  "$(resolve_skills standard,workflow)"

SKILLS_ROOT="$(cd "$SCRIPT_DIR/../../prompts/programming-skills" && pwd)"
JUDGES_ROOT="$(cd "$SCRIPT_DIR/../judges" && pwd)"
eight=$'commenting\ncommits\ndebug\ndebug_logs\ndocs\nlogging\nsrp\ntesting\nworktree'
check "real default discovery is the available companions" "$eight" \
  "$(list_available_skills)"
check "omitting --skills resolves the available companions" "$eight" \
  "$(resolve_skills '')"
check "explicit workflow still resolves" "workflow" \
  "$(resolve_skills workflow)"
check "explicit logging-vague still resolves" "logging-vague" \
  "$(resolve_skills logging-vague)"


CODING_PROMPTS_DIR="$(cd "$SCRIPT_DIR/../coding-prompts" && pwd)"
DEBUG_PROMPTS_DIR="$(cd "$SCRIPT_DIR/../debug-prompts" && pwd)"
SUITE_ARG=''
SELECTED_SKILLS=(debug)
check "debug-only default selects repair cases" $'debug-catalog\ndebug-clock\ndebug-stock' "$(resolve_tasks '')"
SELECTED_SKILLS=(testing)
check "testing-only default keeps coding tasks" 8 "$(resolve_tasks '' | wc -l | tr -d ' ')"
if resolve_tasks debug-clock >"$fixture/output" 2>"$fixture/error"; then
  echo 'FAIL unrelated skill accepted explicit debug case' >&2; exit 1
fi
grep -q 'requires --skills debug' "$fixture/error"
SUITE_ARG=debug
if resolve_tasks '' >"$fixture/output" 2>"$fixture/error"; then
  echo 'FAIL unrelated skill accepted debug suite' >&2; exit 1
fi
SELECTED_SKILLS=(debug testing)
SUITE_ARG=''
check "mixed default includes both task families" 11 "$(resolve_tasks '' | wc -l | tr -d ' ')"
SUITE_ARG=coding
check "explicit coding suite excludes repairs" 8 "$(resolve_tasks '' | wc -l | tr -d ' ')"
if resolve_tasks debug-clock >"$fixture/output" 2>"$fixture/error"; then
  echo 'FAIL coding suite accepted debug case' >&2; exit 1
fi
SUITE_ARG=all
check "explicit mixed tasks resolve across families" $'counter\ndebug-clock' "$(resolve_tasks counter,debug-clock)"
echo 'ALL TASK FAMILY SELF-TESTS PASSED'

task_scope="$fixture/task-scope"
mkdir -p "$task_scope/counter/tests" "$task_scope/debug-clock/tests"
printf 'Original counter request\n' > "$task_scope/counter/tests/task.md"
printf 'Original debug request\n' > "$task_scope/debug-clock/tests/task.md"
cp "$task_scope/counter/tests/task.md" "$task_scope/counter/instruction.md"
cp "$task_scope/debug-clock/tests/task.md" "$task_scope/debug-clock/instruction.md"
cp "$SCRIPT_DIR/../debug-cases/debug-clock.json" "$task_scope/debug-clock/tests/debug-cases.json"
TASKS_DIR="$task_scope" "$SCRIPT_DIR/../sync_judges.sh" > "$fixture/sync.log" 2>&1 || exit 1
check "default judge sync isolates repair judges" $'debug\ndebug_behavior' \
  "$(find "$task_scope/debug-clock/tests/judges" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
check "coding tasks never receive debug behavior checker" absent \
  "$(if [[ ! -d "$task_scope/counter/tests/judges/debug_behavior" && ! -d "$task_scope/counter/tests/judges/debug" ]]; then echo absent; fi)"
TASKS_DIR="$task_scope" "$SCRIPT_DIR/../sync_judges.sh" testing > "$fixture/sync.log" 2>&1 || exit 1
check "partial coding sync preserves repair judges" $'debug\ndebug_behavior' \
  "$(find "$task_scope/debug-clock/tests/judges" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
check "partial coding sync limits coding judges" testing \
  "$(find "$task_scope/counter/tests/judges" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"

if [[ $fails -eq 0 ]]; then
  echo "ALL SKILL DISCOVERY SELF-TESTS PASSED"
else
  echo "$fails skill discovery self-test(s) failed"
fi
exit $((fails > 0))

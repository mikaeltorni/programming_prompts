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

task_root="$fixture/tasks"
mkdir -p "$task_root/calculator"
printf '%s\n' 'Follow every provided programming skill.' >"$task_root/calculator/instruction.md"
inject_selected_workflow_invocation "$task_root" standard
check "unselected workflow leaves task prompt intact" \
  'Follow every provided programming skill.' \
  "$(<"$task_root/calculator/instruction.md")"
inject_selected_workflow_invocation "$task_root" standard workflow
check "selected workflow receives an explicit invocation" \
  $'Use $workflow to coordinate this programming task from start to finish.\nEnabled programming skills for this task: standard, workflow.\n\nFollow every provided programming skill.' \
  "$(<"$task_root/calculator/instruction.md")"
inject_selected_workflow_invocation "$task_root" standard workflow
check "explicit invocation is idempotent" \
  $'Use $workflow to coordinate this programming task from start to finish.\nEnabled programming skills for this task: standard, workflow.\n\nFollow every provided programming skill.' \
  "$(<"$task_root/calculator/instruction.md")"

if [[ $fails -eq 0 ]]; then
  echo "ALL SKILL DISCOVERY SELF-TESTS PASSED"
else
  echo "$fails skill discovery self-test(s) failed"
fi
exit $((fails > 0))

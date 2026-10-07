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

if [[ $fails -eq 0 ]]; then
  echo "ALL SKILL DISCOVERY SELF-TESTS PASSED"
else
  echo "$fails skill discovery self-test(s) failed"
fi
exit $((fails > 0))

#!/usr/bin/env bash
# Runtime-only sync of the two (or selected) canonical judges into task tests/.
# Edit only evals/judges/<skill>/ — never the synced copies under tasks/*/tests/.
# Usage: ./sync_judges.sh [skill ...]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JUDGES_ROOT="$SCRIPT_DIR/judges"
TASKS_DIR="$SCRIPT_DIR/tasks"

if [[ ! -d "$JUDGES_ROOT" ]]; then
  echo "Missing judges root: $JUDGES_ROOT" >&2
  exit 1
fi

skills=("$@")
if [[ ${#skills[@]} -eq 0 ]]; then
  for judge_dir in "$JUDGES_ROOT"/*; do
    [[ -d "$judge_dir" ]] || continue
    skills+=("$(basename "$judge_dir")")
  done
fi

if [[ ${#skills[@]} -eq 0 ]]; then
  echo "No judges found under $JUDGES_ROOT" >&2
  exit 1
fi

copied_tasks=0
for tests_dir in "$TASKS_DIR"/*/tests; do
  [[ -d "$tests_dir" ]] || continue
  rm -rf "$tests_dir/judges"
  mkdir -p "$tests_dir/judges"
  for skill in "${skills[@]}"; do
    src="$JUDGES_ROOT/$skill"
    if [[ ! -f "$src/judge-prompt.md" || ! -f "$src/judge.toml" ]]; then
      echo "Missing judge files for skill '$skill' under $src" >&2
      exit 1
    fi
    mkdir -p "$tests_dir/judges/$skill"
    cp "$src/judge-prompt.md" "$src/judge.toml" "$tests_dir/judges/$skill/"
  done
  copied_tasks=$((copied_tasks + 1))
done

if [[ "$copied_tasks" -eq 0 ]]; then
  echo "No task tests directories under $TASKS_DIR" >&2
  exit 1
fi

echo "Synced judge(s) [${skills[*]}] into $copied_tasks task(s) (runtime copies only)" >&2

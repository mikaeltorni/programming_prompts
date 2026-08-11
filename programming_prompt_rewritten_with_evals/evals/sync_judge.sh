#!/usr/bin/env bash
# Copy the single shared judge into every task's tests/ directory.
# Edit only judge/judge-prompt.md (and judge.toml for harness wiring).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JUDGE_DIR="$SCRIPT_DIR/judge"
TASKS_DIR="$SCRIPT_DIR/tasks"

if [[ ! -f "$JUDGE_DIR/judge-prompt.md" || ! -f "$JUDGE_DIR/judge.toml" ]]; then
  echo "Missing shared judge under $JUDGE_DIR" >&2
  exit 1
fi

copied=0
for tests_dir in "$TASKS_DIR"/*/tests; do
  [[ -d "$tests_dir" ]] || continue
  cp "$JUDGE_DIR/judge-prompt.md" "$JUDGE_DIR/judge.toml" "$tests_dir/"
  printf '%s\n' "synced-from=evals/judge" >"$tests_dir/JUDGE_SYNCED"
  copied=$((copied + 1))
done

if [[ "$copied" -eq 0 ]]; then
  echo "No task tests directories under $TASKS_DIR" >&2
  exit 1
fi

echo "Synced shared judge into $copied task(s)" >&2

#!/usr/bin/env bash
# Runtime sync of canonical judges + shared verifier into generated task tests/.
# Edit only:
#   evals/judges/<skill>/prompt.md (+ judge.toml)
#   evals/verifier/run_judges.sh
#   evals/verifier/check_worktree.py
# Never edit the synced copies under .generated/tasks/*/tests/ (generated).
# Usage: ./sync_judges.sh [skill ...]
# Prefer ./sync_tasks.sh first so .generated/tasks/ exists.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JUDGES_ROOT="$SCRIPT_DIR/judges"
VERIFIER_SRC="$SCRIPT_DIR/verifier/run_judges.sh"
WORKTREE_CHECK_SRC="$SCRIPT_DIR/verifier/check_worktree.py"
# Allow callers to target an isolated job copy (see run_benchmark.sh).
TASKS_DIR="${TASKS_DIR:-$SCRIPT_DIR/.generated/tasks}"

if [[ ! -d "$TASKS_DIR" ]] || [[ -z "$(find "$TASKS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -1)" ]]; then
  echo "No generated tasks yet — running sync_tasks.sh first" >&2
  "$SCRIPT_DIR/sync_tasks.sh"
fi

if [[ ! -d "$JUDGES_ROOT" ]]; then
  echo "Missing judges root: $JUDGES_ROOT" >&2
  exit 1
fi
if [[ ! -f "$VERIFIER_SRC" ]]; then
  echo "Missing shared verifier: $VERIFIER_SRC" >&2
  exit 1
fi
if [[ ! -f "$WORKTREE_CHECK_SRC" ]]; then
  echo "Missing worktree checker: $WORKTREE_CHECK_SRC" >&2
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

prompt_file_for() {
  local src="$1"
  if [[ -f "$src/prompt.md" ]]; then
    printf '%s\n' "$src/prompt.md"
    return 0
  fi
  if [[ -f "$src/judge-prompt.md" ]]; then
    printf '%s\n' "$src/judge-prompt.md"
    return 0
  fi
  return 1
}

is_programmatic_judge() {
  local src="$1"
  [[ -f "$src/judge.toml" ]] && grep -qE '^judge[[:space:]]*=[[:space:]]*"programmatic"' "$src/judge.toml"
}

copied_tasks=0
for tests_dir in "$TASKS_DIR"/*/tests; do
  [[ -d "$tests_dir" ]] || continue
  rm -rf "$tests_dir/judges"
  mkdir -p "$tests_dir/judges"
  install -m 755 "$VERIFIER_SRC" "$tests_dir/run_judges.sh"
  install -m 755 "$WORKTREE_CHECK_SRC" "$tests_dir/check_worktree.py"
  for skill in "${skills[@]}"; do
    src="$JUDGES_ROOT/$skill"
    if is_programmatic_judge "$src"; then
      mkdir -p "$tests_dir/judges/$skill"
      cp "$src/judge.toml" "$tests_dir/judges/$skill/"
      continue
    fi
    prompt_src="$(prompt_file_for "$src" || true)"
    if [[ -z "$prompt_src" || ! -f "$src/judge.toml" ]]; then
      echo "Missing prompt.md (or judge-prompt.md) / judge.toml for skill '$skill' under $src" >&2
      exit 1
    fi
    mkdir -p "$tests_dir/judges/$skill"
    # Always install as prompt.md so judge.toml prompt_template stays stable.
    cp "$prompt_src" "$tests_dir/judges/$skill/prompt.md"
    cp "$src/judge.toml" "$tests_dir/judges/$skill/"
  done
  copied_tasks=$((copied_tasks + 1))
done

if [[ "$copied_tasks" -eq 0 ]]; then
  echo "No task tests directories under $TASKS_DIR" >&2
  exit 1
fi

echo "Synced verifier + judge(s) [${skills[*]}] into $copied_tasks task(s) (runtime copies only)" >&2

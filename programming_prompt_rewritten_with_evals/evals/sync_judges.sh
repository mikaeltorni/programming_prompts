#!/usr/bin/env bash
# Runtime sync of canonical judges + shared verifier into generated task tests/.
# Edit only:
#   evals/judges/<skill>/prompt.md (+ judge.toml)
#   evals/verifier/run_judges.sh
#   evals/verifier/judge_pool.py
#   evals/verifier/check_*.py
#   evals/verifier/run_llm_judge.py
#   evals/verifier/run_grok_judge.py
#   evals/verifier/llm_judge/*.py
#   evals/verifier/*_check/*.py
#   evals/verifier/lib/*.sh
# Never edit the synced copies under .generated/tasks/*/tests/ (generated).
# Usage: ./sync_judges.sh [skill ...]
# Prefer ./sync_tasks.sh first so .generated/tasks/ exists.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JUDGES_ROOT="$SCRIPT_DIR/judges"
VERIFIER_SRC="$SCRIPT_DIR/verifier/run_judges.sh"
GROK_JUDGE_SRC="$SCRIPT_DIR/verifier/run_grok_judge.py"
JUDGE_POOL_SRC="$SCRIPT_DIR/verifier/judge_pool.py"
LLM_JUDGE_CLI="$SCRIPT_DIR/verifier/run_llm_judge.py"
LLM_JUDGE_SRC="$SCRIPT_DIR/verifier/llm_judge"
VERIFIER_LIB_SRC="$SCRIPT_DIR/verifier/lib"
mapfile -t PROGRAMMATIC_CHECKERS < <(find "$SCRIPT_DIR/verifier" -maxdepth 1 -type f -name 'check_*.py' | sort)
mapfile -t PROGRAMMATIC_PACKAGES < <(find "$SCRIPT_DIR/verifier" -maxdepth 1 -type d -name '*_check' | sort)
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
if [[ ${#PROGRAMMATIC_CHECKERS[@]} -eq 0 ]]; then
  echo "Missing programmatic checkers under $SCRIPT_DIR/verifier/check_*.py" >&2
  exit 1
fi
if [[ ${#PROGRAMMATIC_PACKAGES[@]} -eq 0 ]]; then
  echo "Missing programmatic packages under $SCRIPT_DIR/verifier/*_check" >&2
  exit 1
fi
if [[ ! -f "$GROK_JUDGE_SRC" ]]; then
  echo "Missing Grok judge helper: $GROK_JUDGE_SRC" >&2
  exit 1
fi
if [[ ! -f "$JUDGE_POOL_SRC" ]]; then
  echo "Missing judge pool: $JUDGE_POOL_SRC" >&2
  exit 1
fi
if [[ ! -f "$LLM_JUDGE_CLI" ]]; then
  echo "Missing LLM judge helper: $LLM_JUDGE_CLI" >&2
  exit 1
fi
if [[ ! -f "$LLM_JUDGE_SRC/workspace.py" ]]; then
  echo "Missing LLM judge package: $LLM_JUDGE_SRC" >&2
  exit 1
fi
if [[ ! -f "$VERIFIER_LIB_SRC/eval_agents.sh" ]]; then
  echo "Missing verifier shell library: $VERIFIER_LIB_SRC" >&2
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
  for checker in "${PROGRAMMATIC_CHECKERS[@]}"; do
    install -m 755 "$checker" "$tests_dir/$(basename "$checker")"
  done
  for pkg in "${PROGRAMMATIC_PACKAGES[@]}"; do
    rm -rf "$tests_dir/$(basename "$pkg")"
    cp -r "$pkg" "$tests_dir/$(basename "$pkg")"
  done
  install -m 755 "$LLM_JUDGE_CLI" "$tests_dir/run_llm_judge.py"
  install -m 755 "$JUDGE_POOL_SRC" "$tests_dir/judge_pool.py"
  install -m 755 "$GROK_JUDGE_SRC" "$tests_dir/run_grok_judge.py"
  rm -rf "$tests_dir/lib"
  install -d "$tests_dir/lib"
  install -m 644 "$VERIFIER_LIB_SRC"/*.sh "$tests_dir/lib/"
  rm -rf "$tests_dir/llm_judge"
  mkdir -p "$tests_dir/llm_judge"
  install -m 644 "$LLM_JUDGE_SRC"/*.py "$tests_dir/llm_judge/"
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

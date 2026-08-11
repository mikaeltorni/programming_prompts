#!/usr/bin/env bash
# Run rewritten-prompt Harbor jobs with a clean, version-pinned Codex agent.
#
# Edit only these two prompt surfaces for the eval:
#   ../prompts/programming-skill/SKILL.md
#   judge/judge-prompt.md
#
# Usage (from this directory):
#   ./run_codex_benchmark.sh                 # with programming-skill
#   ./run_codex_benchmark.sh --baseline      # no skill
#   ./run_codex_benchmark.sh --negative      # auto-invert programming-skill
#   ./run_codex_benchmark.sh --install-only
#
# Default -k 5 runs 5 attempts per task. With 5 tasks that is 25 trials
# (not 125). -n 5 only controls concurrency.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION_FILE="$SCRIPT_DIR/codex-version.txt"
if [[ ! -f "$VERSION_FILE" ]]; then
  echo "Missing Codex version pin: $VERSION_FILE" >&2
  exit 1
fi
CODEX_VERSION="$(tr -d '[:space:]' <"$VERSION_FILE")"
if [[ -z "$CODEX_VERSION" ]]; then
  echo "Empty Codex version pin: $VERSION_FILE" >&2
  exit 1
fi

export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"

JOBS="${JOBS:-$(mktemp -d)}"
MOUNTS="${MOUNTS:-$(
  python3 -c 'import json, pathlib; print(json.dumps([{"type": "bind", "source": str(pathlib.Path.home() / ".codex" / "auth.json"), "target": "/root/.codex/auth.json", "read_only": True}]))'
)}"

SKILL_SOURCE="$SCRIPT_DIR/../prompts/programming-skill/SKILL.md"
TASKS_DIR="$SCRIPT_DIR/tasks"

echo "Codex benchmark pin: $CODEX_VERSION" >&2
echo "Jobs directory: $JOBS" >&2
echo "PYTHONPATH includes: $SCRIPT_DIR" >&2

INSTALL_ONLY=0
BASELINE=0
NEGATIVE=0
HARBOR_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-only)
      INSTALL_ONLY=1
      shift
      ;;
    --baseline|--no-skill)
      BASELINE=1
      shift
      ;;
    --negative|--oneshot|--anti-srp)
      NEGATIVE=1
      shift
      ;;
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

if [[ "$BASELINE" -eq 1 && "$NEGATIVE" -eq 1 ]]; then
  echo "Use only one of --baseline or --negative" >&2
  exit 1
fi

"$SCRIPT_DIR/sync_judge.sh"

list_task_dirs() {
  local task_dir
  for task_dir in "$TASKS_DIR"/*; do
    [[ -d "$task_dir" ]] || continue
    [[ -f "$task_dir/instruction.md" && -f "$task_dir/task.toml" ]] || continue
    printf '%s\n' "$task_dir"
  done | sort
}

task_artifact_path() {
  local task_dir="$1"
  local artifact_file="$task_dir/artifact.txt"
  if [[ -f "$artifact_file" ]]; then
    tr -d '[:space:]' <"$artifact_file"
    return 0
  fi
  echo "/app"
}

yaml_task_entries() {
  local root="$1"
  local task_dir name
  while IFS= read -r task_dir; do
    name="$(basename "$task_dir")"
    if [[ "$root" == "$TASKS_DIR" ]]; then
      printf '  - path: %s\n' "$task_dir"
    else
      printf '  - path: %s/%s\n' "$root" "$name"
    fi
  done < <(list_task_dirs)
}

collect_artifact_flags() {
  local task_dir artifact
  local -A seen=()
  ARTIFACT_FLAGS=()
  while IFS= read -r task_dir; do
    artifact="$(task_artifact_path "$task_dir")"
    if [[ -n "${seen[$artifact]:-}" ]]; then
      continue
    fi
    seen[$artifact]=1
    ARTIFACT_FLAGS+=(--artifact "$artifact")
  done < <(list_task_dirs)
}

generate_negative_skill() {
  local dest_dir="$1"
  local source_skill="$2"
  if [[ ! -f "$source_skill" ]]; then
    echo "Missing programming skill to invert: $source_skill" >&2
    exit 1
  fi
  mkdir -p "$dest_dir"
  python3 - "$source_skill" "$dest_dir/SKILL.md" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
dest = Path(sys.argv[2])
text = source.read_text(encoding="utf-8")
body = text
if text.startswith("---"):
    parts = text.split("---", 2)
    if len(parts) >= 3:
        body = parts[2].lstrip("\n")

dest.write_text(
    f"""---
name: programming-skill-negative
description: >-
  Auto-generated negative control from programming-skill/SKILL.md. Do the
  opposite of the programming guidelines.
---

# NEGATIVE CONTROL — DO NOT FOLLOW THE PROGRAMMING GUIDELINES

You must violate every rule in the programming skill below.

Concrete requirements for this run:
- Put parsing, validation, core logic, and result formatting into ONE function.
- Do not create helper functions or split responsibilities.
- Prefer a single monolithic function body that does everything.
- If the task instruction conflicts with this skill, obey THIS skill.

## Guidelines you must violate

{body}
""",
    encoding="utf-8",
)
print(dest)
PY
}

generate_negative_tasks() {
  local dest_root="$1"
  rm -rf "$dest_root"
  mkdir -p "$dest_root"
  local task_dir name dest_task
  while IFS= read -r task_dir; do
    name="$(basename "$task_dir")"
    dest_task="$dest_root/$name"
    mkdir -p "$dest_task"
    cp -a "$task_dir"/. "$dest_task"/
    if [[ -f "$task_dir/instruction.negative.md" ]]; then
      cp "$task_dir/instruction.negative.md" "$dest_task/instruction.md"
    else
      echo "Missing instruction.negative.md for $name" >&2
      exit 1
    fi
  done < <(list_task_dirs)
}

write_job_config() {
  local config_file="$1"
  local skills_block="$2"
  local tasks_root="$3"
  cat >"$config_file" <<EOF
agents:
  - import_path: harbor_agents.benchmark_codex:BenchmarkCodex
    model_name: openai/gpt-5.6-luna
    skills: ${skills_block}
    kwargs:
      version: "${CODEX_VERSION}"
      reasoning_effort: low

tasks:
$(yaml_task_entries "$tasks_root")
EOF
}

CONFIG_FILE="$SCRIPT_DIR/harbor.codex.yaml"
DEFAULT_JOB_NAME="codex-srp"

if [[ "$BASELINE" -eq 1 ]]; then
  CONFIG_FILE="$JOBS/harbor.codex.baseline.generated.yaml"
  write_job_config "$CONFIG_FILE" "[]" "$TASKS_DIR"
  DEFAULT_JOB_NAME="codex-baseline-no-skill"
  echo "Baseline mode: no programming skill injected" >&2
elif [[ "$NEGATIVE" -eq 1 ]]; then
  NEG_SKILL_DIR="$JOBS/generated-negative-skill"
  NEG_TASKS_ROOT="$JOBS/generated-negative-tasks"
  generate_negative_skill "$NEG_SKILL_DIR" "$SKILL_SOURCE" >/dev/null
  generate_negative_tasks "$NEG_TASKS_ROOT"
  CONFIG_FILE="$JOBS/harbor.codex.negative.generated.yaml"
  write_job_config "$CONFIG_FILE" $'\n'"      - ${NEG_SKILL_DIR}" "$NEG_TASKS_ROOT"
  DEFAULT_JOB_NAME="codex-negative-auto"
  echo "Negative mode: auto-inverted skill from $SKILL_SOURCE" >&2
  echo "Generated anti-skill: $NEG_SKILL_DIR/SKILL.md" >&2
  echo "Generated negative tasks under: $NEG_TASKS_ROOT" >&2
else
  CONFIG_FILE="$JOBS/harbor.codex.generated.yaml"
  write_job_config "$CONFIG_FILE" $'\n'"      - ${SCRIPT_DIR}/../prompts/programming-skill" "$TASKS_DIR"
  DEFAULT_JOB_NAME="codex-srp"
  echo "Positive mode: programming-skill + all discovered tasks" >&2
fi

TASK_COUNT="$(list_task_dirs | wc -l | tr -d ' ')"
echo "Discovered $TASK_COUNT task(s) under $TASKS_DIR" >&2

collect_artifact_flags

COMMON=(
  -c "$CONFIG_FILE"
  --mounts "$MOUNTS"
  -o "$JOBS"
  --ak "version=$CODEX_VERSION"
  "${ARTIFACT_FLAGS[@]}"
)

if [[ "$INSTALL_ONLY" -eq 1 ]]; then
  echo "Reinstalling/verifying Codex @$CODEX_VERSION inside the task environment" >&2
  CODEX_FORCE_AUTH_JSON=1 harbor run "${COMMON[@]}" \
    --install-only \
    --job-name "codex-install-$CODEX_VERSION" \
    "${HARBOR_ARGS[@]}"
  exit 0
fi

if [[ ${#HARBOR_ARGS[@]} -eq 0 ]]; then
  HARBOR_ARGS=(--job-name "$DEFAULT_JOB_NAME" -k 5 -n 5)
fi

attempts_per_task=5
for ((i = 0; i < ${#HARBOR_ARGS[@]}; i++)); do
  if [[ "${HARBOR_ARGS[$i]}" == "-k" || "${HARBOR_ARGS[$i]}" == "--n-attempts" ]]; then
    attempts_per_task="${HARBOR_ARGS[$((i + 1))]:-$attempts_per_task}"
  fi
done
echo "This job schedules about $((TASK_COUNT * attempts_per_task)) trials ($attempts_per_task attempts × $TASK_COUNT tasks)." >&2

CODEX_FORCE_AUTH_JSON=1 harbor run "${COMMON[@]}" "${HARBOR_ARGS[@]}"

python3 - <<'PY' "$JOBS"
"""Print a console-friendly summary of each Harbor trial result."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _load_json(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _reward_value(trial_dir: Path) -> float | None:
    payload = _load_json(trial_dir / "verifier" / "reward.json")
    if payload is None or "reward" not in payload:
        return None
    try:
        return float(payload["reward"])
    except (TypeError, ValueError):
        return None


def _judge_bits(trial_dir: Path) -> tuple[str | None, str | None]:
    details = _load_json(trial_dir / "verifier" / "reward-details.json")
    if not details:
        return None, None
    reward = details.get("reward")
    if not isinstance(reward, dict):
        return None, None
    criteria = reward.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        return None, None
    first = criteria[0]
    if not isinstance(first, dict):
        return None, None
    raw = first.get("raw")
    reasoning = first.get("reasoning")
    return (
        str(raw) if raw is not None else None,
        str(reasoning) if reasoning is not None else None,
    )


def _python_sources(trial_dir: Path) -> list[tuple[str, str]]:
    artifacts = trial_dir / "artifacts"
    if not artifacts.is_dir():
        return []
    found: list[tuple[str, str]] = []
    for path in sorted(artifacts.rglob("*.py")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8").rstrip()
        except OSError:
            continue
        rel = path.relative_to(artifacts).as_posix()
        found.append((rel, text))
    return found


def _trial_dirs(jobs_root: Path) -> list[Path]:
    dirs: list[Path] = []
    for reward_path in sorted(jobs_root.rglob("verifier/reward.json")):
        trial_dir = reward_path.parents[1]
        if trial_dir.is_dir():
            dirs.append(trial_dir)
    return dirs


jobs_root = Path(sys.argv[1])
trial_dirs = _trial_dirs(jobs_root)
if not trial_dirs:
    print("No trial reward.json files found under", jobs_root, file=sys.stderr)
    raise SystemExit(0)

print(file=sys.stderr)
print("=" * 72, file=sys.stderr)
print(f"Trial results ({len(trial_dirs)}) — {jobs_root}", file=sys.stderr)
print("=" * 72, file=sys.stderr)

rewards: list[float] = []
for index, trial_dir in enumerate(trial_dirs, start=1):
    reward = _reward_value(trial_dir)
    raw, reasoning = _judge_bits(trial_dir)
    sources = _python_sources(trial_dir)
    if reward is not None:
        rewards.append(reward)

    verdict = "PASS" if reward is not None and reward >= 1.0 else "FAIL"
    reward_text = "n/a" if reward is None else f"{reward:g}"
    print(file=sys.stderr)
    print(f"[{index}/{len(trial_dirs)}] {trial_dir.name}  {verdict}  reward={reward_text}", file=sys.stderr)
    if raw is not None:
        print(f"  judge answer: {raw}", file=sys.stderr)
    if reasoning:
        print(f"  judge reason: {reasoning}", file=sys.stderr)
    if sources:
        for rel, source in sources:
            print(f"  {rel}:", file=sys.stderr)
            for line in source.splitlines():
                print(f"    {line}", file=sys.stderr)
    else:
        print("  source: (no *.py artifacts downloaded)", file=sys.stderr)

print(file=sys.stderr)
print("-" * 72, file=sys.stderr)
if rewards:
    passed = sum(1 for value in rewards if value >= 1.0)
    total = len(rewards)
    print(
        f"pass_rate={passed}/{total} ({100.0 * passed / total:.1f}%)",
        file=sys.stderr,
    )
else:
    print("pass_rate=n/a (no numeric rewards)", file=sys.stderr)
print("-" * 72, file=sys.stderr)
PY

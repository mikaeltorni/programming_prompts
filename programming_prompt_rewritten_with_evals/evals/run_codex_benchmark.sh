#!/usr/bin/env bash
# Run rewritten-prompt Harbor jobs with a clean, version-pinned Codex agent.
#
# Edit surfaces:
#   ../prompts/programming-skills/<skill>/SKILL.md
#   judges/<skill>/prompt.md
#   coding-prompts/<task>.md
#
# Usage (from this directory):
#   ./run_codex_benchmark.sh
#   ./run_codex_benchmark.sh --tasks todo,calculator
#   ./run_codex_benchmark.sh --tasks=greeter --skills srp
#   ./run_codex_benchmark.sh task=todo,counter --baseline
#   ./run_codex_benchmark.sh --skills srp
#   ./run_codex_benchmark.sh --skills=srp,commenting
#   ./run_codex_benchmark.sh --skills srp,commenting --run-separately
#   ./run_codex_benchmark.sh --baseline --skills srp,commenting
#   ./run_codex_benchmark.sh --negative --skills srp
#   ./run_codex_benchmark.sh --install-only
#
# Default model stays gpt-5.6-luna at low reasoning effort.
# Default -k 5 is 5 attempts per coding task (× number of tasks, × skills when
# --run-separately).

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

SKILLS_ROOT="$SCRIPT_DIR/../prompts/programming-skills"
JUDGES_ROOT="$SCRIPT_DIR/judges"
CODING_PROMPTS_DIR="$SCRIPT_DIR/coding-prompts"
TASKS_DIR="$SCRIPT_DIR/tasks"

echo "Codex benchmark pin: $CODEX_VERSION" >&2
echo "Jobs directory: $JOBS" >&2
echo "PYTHONPATH includes: $SCRIPT_DIR" >&2

INSTALL_ONLY=0
BASELINE=0
NEGATIVE=0
RUN_SEPARATELY=0
SKILLS_ARG=""
TASKS_ARG=""
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
    --run-separately|--runSeparately)
      RUN_SEPARATELY=1
      shift
      ;;
    --skills)
      SKILLS_ARG="${2:-}"
      if [[ -z "$SKILLS_ARG" ]]; then
        echo "--skills requires a value like srp,commenting" >&2
        exit 1
      fi
      shift 2
      ;;
    --skills=*)
      SKILLS_ARG="${1#--skills=}"
      shift
      ;;
    -skills=*)
      SKILLS_ARG="${1#-skills=}"
      shift
      ;;
    --tasks|--task)
      TASKS_ARG="${2:-}"
      if [[ -z "$TASKS_ARG" ]]; then
        echo "--tasks requires a value like todo,calculator" >&2
        exit 1
      fi
      shift 2
      ;;
    --tasks=*|--task=*)
      TASKS_ARG="${1#*=}"
      shift
      ;;
    -tasks=*|-task=*)
      TASKS_ARG="${1#*=}"
      shift
      ;;
    tasks=*|task=*)
      TASKS_ARG="${1#*=}"
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

list_available_skills() {
  local skill_dir
  for skill_dir in "$SKILLS_ROOT"/*; do
    [[ -d "$skill_dir" && -f "$skill_dir/SKILL.md" ]] || continue
    printf '%s\n' "$(basename "$skill_dir")"
  done | sort
}

resolve_skills() {
  local raw="$1"
  local -a selected=()
  if [[ -z "$raw" ]]; then
    mapfile -t selected < <(list_available_skills)
  else
    local IFS=','
    local -a parts
    read -r -a parts <<<"$raw"
    local part
    for part in "${parts[@]}"; do
      part="$(echo "$part" | tr -d '[:space:]')"
      [[ -n "$part" ]] || continue
      selected+=("$part")
    done
  fi
  if [[ ${#selected[@]} -eq 0 ]]; then
    echo "No skills selected under $SKILLS_ROOT" >&2
    exit 1
  fi
  local skill
  for skill in "${selected[@]}"; do
    if [[ ! -f "$SKILLS_ROOT/$skill/SKILL.md" ]]; then
      echo "Unknown skill '$skill' (expected $SKILLS_ROOT/$skill/SKILL.md)" >&2
      exit 1
    fi
    if [[ ! -f "$JUDGES_ROOT/$skill/prompt.md" && ! -f "$JUDGES_ROOT/$skill/judge-prompt.md" ]]; then
      echo "Missing judge for skill '$skill' (expected $JUDGES_ROOT/$skill/prompt.md)" >&2
      exit 1
    fi
  done
  printf '%s\n' "${selected[@]}"
}

mapfile -t SELECTED_SKILLS < <(resolve_skills "$SKILLS_ARG")
echo "Selected skill(s): ${SELECTED_SKILLS[*]}" >&2

list_available_tasks() {
  local prompt
  for prompt in "$CODING_PROMPTS_DIR"/*.md; do
    [[ -f "$prompt" ]] || continue
    [[ "$(basename "$prompt")" == "README.md" ]] && continue
    printf '%s\n' "$(basename "$prompt" .md)"
  done | sort
}

resolve_tasks() {
  local raw="$1"
  local -a selected=()
  if [[ -z "$raw" ]]; then
    mapfile -t selected < <(list_available_tasks)
  else
    local IFS=','
    local -a parts
    read -r -a parts <<<"$raw"
    local part
    for part in "${parts[@]}"; do
      part="$(echo "$part" | tr -d '[:space:]')"
      [[ -n "$part" ]] || continue
      selected+=("$part")
    done
  fi
  if [[ ${#selected[@]} -eq 0 ]]; then
    echo "No coding tasks selected under $CODING_PROMPTS_DIR" >&2
    exit 1
  fi
  local task
  for task in "${selected[@]}"; do
    if [[ ! -f "$CODING_PROMPTS_DIR/$task.md" ]]; then
      echo "Unknown coding task '$task' (expected $CODING_PROMPTS_DIR/$task.md)" >&2
      echo "Available: $(list_available_tasks | tr '\n' ' ')" >&2
      exit 1
    fi
  done
  printf '%s\n' "${selected[@]}"
}

mapfile -t SELECTED_TASKS < <(resolve_tasks "$TASKS_ARG")
echo "Selected coding task(s): ${SELECTED_TASKS[*]}" >&2

task_is_selected() {
  local name="$1"
  local selected
  for selected in "${SELECTED_TASKS[@]}"; do
    if [[ "$selected" == "$name" ]]; then
      return 0
    fi
  done
  return 1
}

list_task_dirs() {
  local task_dir name
  for task_dir in "$TASKS_DIR"/*; do
    [[ -d "$task_dir" ]] || continue
    [[ -f "$task_dir/instruction.md" && -f "$task_dir/task.toml" ]] || continue
    name="$(basename "$task_dir")"
    task_is_selected "$name" || continue
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

skills_yaml_block() {
  local skill
  if [[ $# -eq 0 ]]; then
    printf '%s' "[]"
    return 0
  fi
  printf '\n'
  for skill_path in "$@"; do
    printf '      - %s\n' "$skill_path"
  done
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

generate_negative_skill() {
  local dest_dir="$1"
  local source_skill="$2"
  local skill_name="$3"
  if [[ ! -f "$source_skill" ]]; then
    echo "Missing programming skill to invert: $source_skill" >&2
    exit 1
  fi
  mkdir -p "$dest_dir"
  python3 - "$source_skill" "$dest_dir/SKILL.md" "$skill_name" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
dest = Path(sys.argv[2])
skill_name = sys.argv[3]
text = source.read_text(encoding="utf-8")
body = text
if text.startswith("---"):
    parts = text.split("---", 2)
    if len(parts) >= 3:
        body = parts[2].lstrip("\n")

if skill_name == "commenting":
    concrete = """Concrete requirements for this run:
- Do not write docstrings on any function.
- Omit description, Parameters, and Returns documentation entirely.
- Prefer bare function bodies with no documentation comments.
- If the task instruction conflicts with this skill, obey THIS skill."""
else:
    concrete = """Concrete requirements for this run:
- Put parsing, validation, core logic, and result formatting into ONE function.
- Do not create helper functions or split responsibilities.
- Prefer a single monolithic function body that does everything.
- If the task instruction conflicts with this skill, obey THIS skill."""

dest.write_text(
    f"""---
name: {skill_name}-negative
description: >-
  Auto-generated negative control from programming-skills/{skill_name}.
  Do the opposite of that skill.
---

# NEGATIVE CONTROL — DO NOT FOLLOW THE {skill_name.upper()} GUIDELINES

You must violate every rule in the programming skill below.

{concrete}

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
  local skill_name="$2"
  generate_negative_tasks_from_root "$dest_root" "$skill_name" "$TASKS_DIR"
}

generate_negative_tasks_from_root() {
  local dest_root="$1"
  local skill_name="$2"
  local source_root="$3"
  local anti_line
  case "$skill_name" in
    commenting)
      anti_line="Negative control: do not write docstrings (no description, Parameters, or Returns)."
      ;;
    *)
      anti_line="Negative control: put all logic in one function; do not create helpers."
      ;;
  esac
  rm -rf "$dest_root"
  mkdir -p "$dest_root"
  local task_dir name dest_task base_instruction src
  while IFS= read -r task_dir; do
    name="$(basename "$task_dir")"
    src="$source_root/$name"
    if [[ ! -d "$src" ]]; then
      src="$task_dir"
    fi
    dest_task="$dest_root/$name"
    mkdir -p "$dest_task"
    cp -a "$src"/. "$dest_task"/
    base_instruction="$(tr -d '\r' <"$src/instruction.md" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g; s/[[:space:]]*$//')"
    base_instruction="${base_instruction% Follow the provided programming skill.}"
    base_instruction="${base_instruction% Follow the provided programming skill}"
    printf '%s\n\n%s\n' "$base_instruction" "$anti_line" >"$dest_task/instruction.md"
  done < <(list_task_dirs)
}

prepare_job_tasks() {
  # Copy selected coding tasks into $JOBS/task-trees/<job>/ and sync only this
  # job's judges there. Returns the absolute path on stdout.
  local job_name="$1"
  shift
  local -a skills=("$@")
  local dest="$JOBS/task-trees/$job_name"
  local task_dir name
  rm -rf "$dest"
  mkdir -p "$dest"
  while IFS= read -r task_dir; do
    name="$(basename "$task_dir")"
    cp -a "$task_dir" "$dest/$name"
  done < <(list_task_dirs)
  if [[ ${#skills[@]} -eq 0 ]]; then
    TASKS_DIR="$dest" "$SCRIPT_DIR/sync_judges.sh"
  else
    TASKS_DIR="$dest" "$SCRIPT_DIR/sync_judges.sh" "${skills[@]}"
  fi
  local judge_count
  judge_count="$(find "$dest" -type d -path '*/tests/judges/*' 2>/dev/null | wc -l | tr -d ' ')"
  echo "Prepared isolated tasks for $job_name at $dest (judge dirs=$judge_count)" >&2
  printf '%s\n' "$dest"
}

print_summary() {
  local jobs_root="$1"
  local run_mode="$2"
  local skills_csv="$3"
  python3 - <<'PY' "$jobs_root" "$run_mode" "$skills_csv"
"""Print a console-friendly summary of each Harbor trial result."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
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


def _per_skill_rewards(trial_dir: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    verifier = trial_dir / "verifier"
    if not verifier.is_dir():
        return out
    for path in sorted(verifier.glob("reward-*.json")):
        skill = path.name[len("reward-") : -len(".json")]
        payload = _load_json(path)
        if payload is None or "reward" not in payload:
            continue
        try:
            out[skill] = float(payload["reward"])
        except (TypeError, ValueError):
            continue
    if out:
        return out
    details = _load_json(verifier / "reward-details.json")
    if not details:
        return out
    reward = details.get("reward")
    if not isinstance(reward, dict):
        return out
    criteria = reward.get("criteria")
    if not isinstance(criteria, list):
        return out
    for item in criteria:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("reward")
        if name is None or value is None:
            continue
        try:
            out[str(name)] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def _nested_criterion_bits(item: dict) -> tuple[str | None, str | None]:
    """Pull raw/reasoning from a criterion, including nested rewardkit details."""
    raw = item.get("raw")
    reasoning = item.get("reasoning")
    if (reasoning is None or reasoning == "") and isinstance(item.get("details"), dict):
        nested = item["details"].get("reward")
        if isinstance(nested, dict):
            nested_criteria = nested.get("criteria")
            if isinstance(nested_criteria, list) and nested_criteria:
                nested_first = nested_criteria[0]
                if isinstance(nested_first, dict):
                    if reasoning is None or reasoning == "":
                        reasoning = nested_first.get("reasoning")
                    if raw is None:
                        raw = nested_first.get("raw")
            if (reasoning is None or reasoning == "") and nested.get("judge_output"):
                reasoning = nested.get("judge_output")
    return (
        str(raw) if raw is not None else None,
        str(reasoning) if reasoning else None,
    )


def _judge_criteria(trial_dir: Path) -> list[tuple[str, str | None, str | None]]:
    """Return [(skill, raw, reasoning), ...] for every judge criterion."""
    details = _load_json(trial_dir / "verifier" / "reward-details.json")
    if not details:
        return []
    reward = details.get("reward")
    if not isinstance(reward, dict):
        return []
    criteria = reward.get("criteria")
    if not isinstance(criteria, list):
        return []
    out: list[tuple[str, str | None, str | None]] = []
    for item in criteria:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "judge")
        raw, reasoning = _nested_criterion_bits(item)
        out.append((name, raw, reasoning))
        # Also prefer dedicated per-skill details files when present.
        skill_details = _load_json(
            trial_dir / "verifier" / f"reward-{name}-details.json"
        )
        if skill_details and (reasoning is None or reasoning == ""):
            nested_reward = skill_details.get("reward")
            if isinstance(nested_reward, dict):
                nested_criteria = nested_reward.get("criteria")
                if isinstance(nested_criteria, list) and nested_criteria:
                    nested_first = nested_criteria[0]
                    if isinstance(nested_first, dict):
                        raw2, reasoning2 = _nested_criterion_bits(nested_first)
                        out[-1] = (name, raw or raw2, reasoning or reasoning2)
    return out


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


def _task_name(trial_dir: Path) -> str:
    name = trial_dir.name
    if "__" in name:
        return name.split("__", 1)[0]
    return name


def _fmt_rate(passed: int, total: int) -> str:
    if total <= 0:
        return "n/a"
    return f"{passed}/{total} ({100.0 * passed / total:.1f}%)"


jobs_root = Path(sys.argv[1])
run_mode = sys.argv[2] if len(sys.argv) > 2 else "unknown"
skills_csv = sys.argv[3] if len(sys.argv) > 3 else ""
trial_dirs = _trial_dirs(jobs_root)
if not trial_dirs:
    print("No trial reward.json files found under", jobs_root, file=sys.stderr)
    raise SystemExit(0)

print(file=sys.stderr)
print("=" * 72, file=sys.stderr)
print(
    f"Trial results ({len(trial_dirs)}) — mode={run_mode} skills={skills_csv or '-'} — {jobs_root}",
    file=sys.stderr,
)
print("=" * 72, file=sys.stderr)

by_task: dict[str, list[float | None]] = defaultdict(list)
by_skill: dict[str, list[float]] = defaultdict(list)
by_task_skill: dict[tuple[str, str], list[float]] = defaultdict(list)
rewards: list[float] = []

for index, trial_dir in enumerate(trial_dirs, start=1):
    reward = _reward_value(trial_dir)
    judge_rows = _judge_criteria(trial_dir)
    sources = _python_sources(trial_dir)
    task = _task_name(trial_dir)
    per_skill = _per_skill_rewards(trial_dir)
    by_task[task].append(reward)
    if reward is not None:
        rewards.append(reward)
    for skill, value in per_skill.items():
        by_skill[skill].append(value)
        by_task_skill[(task, skill)].append(value)

    verdict = "PASS" if reward is not None and reward >= 1.0 else "FAIL"
    reward_text = "n/a" if reward is None else f"{reward:g}"
    print(file=sys.stderr)
    print(
        f"[{index}/{len(trial_dirs)}] {trial_dir.name}  {verdict}  reward={reward_text}",
        file=sys.stderr,
    )
    if per_skill:
        bits = ", ".join(f"{name}={value:g}" for name, value in sorted(per_skill.items()))
        print(f"  per-skill: {bits}", file=sys.stderr)
    if judge_rows:
        for skill_name, raw, reasoning in judge_rows:
            if raw is not None:
                print(f"  judge[{skill_name}] answer: {raw}", file=sys.stderr)
            if reasoning:
                print(f"  judge[{skill_name}] reason: {reasoning}", file=sys.stderr)
            elif raw is not None:
                print(f"  judge[{skill_name}] reason: (none recorded)", file=sys.stderr)
    if sources:
        for rel, source in sources:
            print(f"  {rel}:", file=sys.stderr)
            for line in source.splitlines():
                print(f"    {line}", file=sys.stderr)
    else:
        print("  source: (no *.py artifacts downloaded)", file=sys.stderr)

print(file=sys.stderr)
print("=" * 72, file=sys.stderr)
print(f"Summary by coding task (mode={run_mode})", file=sys.stderr)
print("=" * 72, file=sys.stderr)
for task in sorted(by_task):
    values = [value for value in by_task[task] if value is not None]
    passed = sum(1 for value in values if value >= 1.0)
    print(f"  {task}: {_fmt_rate(passed, len(values))}", file=sys.stderr)

if by_skill:
    print(file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(f"Summary by skill judge (mode={run_mode})", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    for skill in sorted(by_skill):
        values = by_skill[skill]
        passed = sum(1 for value in values if value >= 1.0)
        print(f"  {skill}: {_fmt_rate(passed, len(values))}", file=sys.stderr)
        for task in sorted({task for task, name in by_task_skill if name == skill}):
            task_values = by_task_skill[(task, skill)]
            task_passed = sum(1 for value in task_values if value >= 1.0)
            print(
                f"    {task}: {_fmt_rate(task_passed, len(task_values))}",
                file=sys.stderr,
            )

print(file=sys.stderr)
print("-" * 72, file=sys.stderr)
if rewards:
    passed = sum(1 for value in rewards if value >= 1.0)
    total = len(rewards)
    print(f"TOTAL pass_rate={_fmt_rate(passed, total)}", file=sys.stderr)
else:
    print("TOTAL pass_rate=n/a (no numeric rewards)", file=sys.stderr)
print("-" * 72, file=sys.stderr)
PY
}

run_one_job() {
  local job_name="$1"
  local run_mode="$2"
  shift 2
  local -a skill_paths=("$@")

  local skills_csv
  skills_csv="$(printf '%s,' "${SELECTED_SKILLS_FOR_JOB[@]:-}")"
  skills_csv="${skills_csv%,}"

  # Isolate Harbor task trees per job so live-mounted /tests/judges cannot be
  # clobbered by --run-separately's next skill or by a concurrent benchmark.
  local tasks_root
  tasks_root="$(prepare_job_tasks "$job_name" "${SELECTED_SKILLS_FOR_JOB[@]}")"

  local config_file
  if [[ "$BASELINE" -eq 1 ]]; then
    config_file="$JOBS/harbor.${job_name}.yaml"
    write_job_config "$config_file" "[]" "$tasks_root"
  elif [[ "$NEGATIVE" -eq 1 ]]; then
    local skill="${SELECTED_SKILLS_FOR_JOB[0]}"
    local neg_skill_dir="$JOBS/generated-negative-skill-$skill"
    local neg_tasks_root="$JOBS/generated-negative-tasks-$skill"
    generate_negative_skill "$neg_skill_dir" "$SKILLS_ROOT/$skill/SKILL.md" "$skill" >/dev/null
    # Build negatives from the already-isolated tree (selected tasks only).
    generate_negative_tasks_from_root "$neg_tasks_root" "$skill" "$tasks_root"
    config_file="$JOBS/harbor.${job_name}.yaml"
    write_job_config "$config_file" "$(skills_yaml_block "$neg_skill_dir")" "$neg_tasks_root"
    tasks_root="$neg_tasks_root"
    echo "Negative mode for skill=$skill" >&2
  else
    config_file="$JOBS/harbor.${job_name}.yaml"
    write_job_config "$config_file" "$(skills_yaml_block "${skill_paths[@]}")" "$tasks_root"
  fi

  collect_artifact_flags
  local -a common=(
    -c "$config_file"
    --mounts "$MOUNTS"
    -o "$JOBS"
    --ak "version=$CODEX_VERSION"
    "${ARTIFACT_FLAGS[@]}"
  )

  local -a harbor_args=("${HARBOR_ARGS[@]}")
  if [[ ${#harbor_args[@]} -eq 0 ]]; then
    harbor_args=(--job-name "$job_name" -k 5 -n 5)
  else
    # Ensure job name is unique when looping skills separately.
    local has_job_name=0
    local i
    for ((i = 0; i < ${#harbor_args[@]}; i++)); do
      if [[ "${harbor_args[$i]}" == "--job-name" ]]; then
        harbor_args[$((i + 1))]="${job_name}"
        has_job_name=1
      fi
    done
    if [[ "$has_job_name" -eq 0 ]]; then
      harbor_args=(--job-name "$job_name" "${harbor_args[@]}")
    fi
  fi

  local attempts_per_task=5
  for ((i = 0; i < ${#harbor_args[@]}; i++)); do
    if [[ "${harbor_args[$i]}" == "-k" || "${harbor_args[$i]}" == "--n-attempts" ]]; then
      attempts_per_task="${harbor_args[$((i + 1))]:-$attempts_per_task}"
    fi
  done
  local task_count
  task_count="$(list_task_dirs | wc -l | tr -d ' ')"
  echo "Job $job_name schedules about $((task_count * attempts_per_task)) trials ($attempts_per_task attempts × $task_count tasks)." >&2
  echo "Job $job_name judges: ${SELECTED_SKILLS_FOR_JOB[*]:-(none)} (isolated under $tasks_root)" >&2

  CODEX_FORCE_AUTH_JSON=1 harbor run "${common[@]}" "${harbor_args[@]}"
  # Summarize this job only (not sibling jobs under $JOBS).
  print_summary "$JOBS/$job_name" "$run_mode" "$skills_csv"
}

# --- install-only path uses a minimal generated config ---
if [[ "$INSTALL_ONLY" -eq 1 ]]; then
  SELECTED_SKILLS_FOR_JOB=("${SELECTED_SKILLS[@]}")
  "$SCRIPT_DIR/sync_tasks.sh"
  tasks_root="$(prepare_job_tasks "codex-install-$CODEX_VERSION" "${SELECTED_SKILLS[@]}")"
  collect_artifact_flags
  CONFIG_FILE="$JOBS/harbor.codex.install.yaml"
  write_job_config "$CONFIG_FILE" "$(skills_yaml_block "$SKILLS_ROOT/${SELECTED_SKILLS[0]}")" "$tasks_root"
  echo "Reinstalling/verifying Codex @$CODEX_VERSION inside the task environment" >&2
  CODEX_FORCE_AUTH_JSON=1 harbor run \
    -c "$CONFIG_FILE" \
    --mounts "$MOUNTS" \
    -o "$JOBS" \
    --ak "version=$CODEX_VERSION" \
    "${ARTIFACT_FLAGS[@]}" \
    --install-only \
    --job-name "codex-install-$CODEX_VERSION" \
    "${HARBOR_ARGS[@]}"
  exit 0
fi

"$SCRIPT_DIR/sync_tasks.sh"
TASK_COUNT="$(list_task_dirs | wc -l | tr -d ' ')"
echo "Discovered $TASK_COUNT coding task(s) under $TASKS_DIR" >&2

if [[ "$RUN_SEPARATELY" -eq 1 ]]; then
  echo "Running each selected skill in its own prompt instance (--run-separately)." >&2
  for skill in "${SELECTED_SKILLS[@]}"; do
    SELECTED_SKILLS_FOR_JOB=("$skill")
    if [[ "$BASELINE" -eq 1 ]]; then
      run_one_job "codex-baseline-$skill" "baseline"
    elif [[ "$NEGATIVE" -eq 1 ]]; then
      run_one_job "codex-negative-$skill" "negative"
    else
      run_one_job "codex-$skill" "positive" "$SKILLS_ROOT/$skill"
    fi
  done
  echo "Combined summary across separately-run skill jobs:" >&2
  if [[ "$BASELINE" -eq 1 ]]; then
    print_summary "$JOBS" "baseline-all" "${SELECTED_SKILLS[*]}"
  elif [[ "$NEGATIVE" -eq 1 ]]; then
    print_summary "$JOBS" "negative-all" "${SELECTED_SKILLS[*]}"
  else
    print_summary "$JOBS" "positive-all" "${SELECTED_SKILLS[*]}"
  fi
else
  SELECTED_SKILLS_FOR_JOB=("${SELECTED_SKILLS[@]}")
  if [[ "$NEGATIVE" -eq 1 && ${#SELECTED_SKILLS[@]} -gt 1 ]]; then
    echo "Combined --negative with multiple skills is ambiguous; use --run-separately." >&2
    exit 1
  fi
  if [[ "$BASELINE" -eq 1 ]]; then
    run_one_job "codex-baseline" "baseline"
  elif [[ "$NEGATIVE" -eq 1 ]]; then
    run_one_job "codex-negative-${SELECTED_SKILLS[0]}" "negative"
  else
    skill_paths=()
    for skill in "${SELECTED_SKILLS[@]}"; do
      skill_paths+=("$SKILLS_ROOT/$skill")
    done
    run_one_job "codex-skills" "positive" "${skill_paths[@]}"
  fi
fi

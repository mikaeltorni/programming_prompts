#!/usr/bin/env bash
# Run rewritten-prompt Harbor jobs with clean, version-pinned coding agents.
#
# Harnesses: Codex (`codex`) and Claude Code (`cc`). Omit --harness / harness=
# to run both. Defaults:
#   codex → openai/gpt-5.6-luna @ reasoning_effort=low
#   cc    → claude-opus-5       @ reasoning_effort=low (Claude CLI --effort)
#
# Edit surfaces:
#   ../prompts/programming-skills/<skill>/SKILL.md
#   judges/<skill>/prompt.md
#   coding-prompts/<task>.md
#
# Usage (from this directory):
#   ./run_benchmark.sh
#   ./run_benchmark.sh harness=codex
#   ./run_benchmark.sh harness=cc
#   ./run_benchmark.sh --harness both --skills srp,commenting --run-separately -k 5 -n 5
#   ./run_benchmark.sh --baseline --skills srp,commenting -k 5 -n 5
#   ./run_benchmark.sh --negative --skills srp harness=codex
#   ./run_benchmark.sh --skills srp,logging -k 2 -n 2
#   ./run_benchmark.sh --skills srp,logging-vague -k 2 -n 2
#   ./run_benchmark.sh --install-only harness=cc
#
# Trial count (rule of thumb): harnesses × (skills if --run-separately else 1)
# × tasks × -k. Example: both harnesses, 2 skills separately, 5 tasks, -k 5
# → 2 × 2 × 5 × 5 = 100 trials.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
ORIGINAL_ARGV=("$@")

CODEX_VERSION_FILE="$SCRIPT_DIR/codex-version.txt"
CLAUDE_VERSION_FILE="$SCRIPT_DIR/claude-version.txt"
if [[ ! -f "$CODEX_VERSION_FILE" ]]; then
  echo "Missing Codex version pin: $CODEX_VERSION_FILE" >&2
  exit 1
fi
if [[ ! -f "$CLAUDE_VERSION_FILE" ]]; then
  echo "Missing Claude Code version pin: $CLAUDE_VERSION_FILE" >&2
  exit 1
fi
CODEX_VERSION="$(tr -d '[:space:]' <"$CODEX_VERSION_FILE")"
CLAUDE_VERSION="$(tr -d '[:space:]' <"$CLAUDE_VERSION_FILE")"
if [[ -z "$CODEX_VERSION" ]]; then
  echo "Empty Codex version pin: $CODEX_VERSION_FILE" >&2
  exit 1
fi
if [[ -z "$CLAUDE_VERSION" ]]; then
  echo "Empty Claude Code version pin: $CLAUDE_VERSION_FILE" >&2
  exit 1
fi

export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"

JOBS="${JOBS:-$(mktemp -d)}"
# Unique per invocation so a shared/reused $JOBS dir never collides on Harbor
# job names (FileExistsError) or archive dirname when terminals run in parallel.
RUN_STAMP="$(date +%Y-%m-%d_%H%M%S)_$$"
RUNS_ROOT="${RUNS_ROOT:-$SCRIPT_DIR/runs}"
SKILLS_ROOT="$SCRIPT_DIR/../prompts/programming-skills"
JUDGES_ROOT="$SCRIPT_DIR/judges"
CODING_PROMPTS_DIR="$SCRIPT_DIR/coding-prompts"
TASKS_DIR="$SCRIPT_DIR/.generated/tasks"

echo "Codex pin: $CODEX_VERSION | Claude Code pin: $CLAUDE_VERSION" >&2
echo "Jobs directory: $JOBS" >&2
echo "Run stamp: $RUN_STAMP" >&2
echo "PYTHONPATH includes: $SCRIPT_DIR" >&2

harbor_job_name() {
  # Harbor refuses to reuse an existing job dir with a different config.
  printf '%s__%s\n' "$1" "$RUN_STAMP"
}

INSTALL_ONLY=0
BASELINE=0
NEGATIVE=0
RUN_SEPARATELY=0
SKILLS_ARG=""
TASKS_ARG=""
HARNESS_ARG=""
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
    --harness)
      HARNESS_ARG="${2:-}"
      if [[ -z "$HARNESS_ARG" ]]; then
        echo "--harness requires a value: codex | cc | both" >&2
        exit 1
      fi
      shift 2
      ;;
    --harness=*)
      HARNESS_ARG="${1#--harness=}"
      shift
      ;;
    harness=*)
      HARNESS_ARG="${1#harness=}"
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

normalize_harness() {
  local raw="${1,,}"
  raw="$(echo "$raw" | tr -d '[:space:]')"
  case "$raw" in
    ""|both|all)
      printf '%s\n' "codex" "cc"
      ;;
    codex|openai|gpt)
      printf '%s\n' "codex"
      ;;
    cc|claude|claude-code|claudecode|anthropic)
      printf '%s\n' "cc"
      ;;
    *)
      echo "Unknown harness '$1' (use codex, cc, or both)" >&2
      exit 1
      ;;
  esac
}

mapfile -t SELECTED_HARNESSES < <(normalize_harness "$HARNESS_ARG")
echo "Selected harness(es): ${SELECTED_HARNESSES[*]}" >&2

# Control skills named <base>-vague inject a vague SKILL.md but are scored by
# judges/<base>/ (they have no judge of their own).
judge_for_skill() {
  local skill="$1"
  if [[ "$skill" == *-vague ]]; then
    printf '%s\n' "${skill%-vague}"
  else
    printf '%s\n' "$skill"
  fi
}

list_available_skills() {
  # Default discovery skips *-vague controls; pass them explicitly via --skills.
  local skill_dir name
  for skill_dir in "$SKILLS_ROOT"/*; do
    [[ -d "$skill_dir" && -f "$skill_dir/SKILL.md" ]] || continue
    name="$(basename "$skill_dir")"
    [[ "$name" == *-vague ]] && continue
    printf '%s\n' "$name"
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
  local skill judge
  for skill in "${selected[@]}"; do
    if [[ ! -f "$SKILLS_ROOT/$skill/SKILL.md" ]]; then
      echo "Unknown skill '$skill' (expected $SKILLS_ROOT/$skill/SKILL.md)" >&2
      exit 1
    fi
    judge="$(judge_for_skill "$skill")"
    if [[ ! -f "$JUDGES_ROOT/$judge/prompt.md" && ! -f "$JUDGES_ROOT/$judge/judge-prompt.md" ]]; then
      echo "Missing judge for skill '$skill' (expected $JUDGES_ROOT/$judge/prompt.md)" >&2
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
  # One directory download covers every coding-prompt artifact under /app and
  # avoids Harbor trying unrelated sibling files (e.g. calculator.py on a
  # counter trial) when multiple --artifact paths are listed.
  ARTIFACT_FLAGS=(--artifact /app)
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

harness_import_path() {
  case "$1" in
    codex) printf '%s' "harbor_agents.benchmark_codex:BenchmarkCodex" ;;
    cc) printf '%s' "harbor_agents.benchmark_claude_code:BenchmarkClaudeCode" ;;
    *)
      echo "Internal error: unknown harness '$1'" >&2
      exit 1
      ;;
  esac
}

harness_model_name() {
  case "$1" in
    codex) printf '%s' "openai/gpt-5.6-luna" ;;
    cc) printf '%s' "claude-opus-5" ;;
  esac
}

harness_cli_version() {
  case "$1" in
    codex) printf '%s' "$CODEX_VERSION" ;;
    cc) printf '%s' "$CLAUDE_VERSION" ;;
  esac
}

harness_mounts_json() {
  local harness="$1"
  python3 - "$harness" <<'PY'
import json
import pathlib
import sys

harness = sys.argv[1]
home = pathlib.Path.home()
# Judges always use Codex (see judges/*/judge.toml). Mount auth.json for every
# harness so the verifier can score Claude Code trials too.
mounts = [
    {
        "type": "bind",
        "source": str(home / ".codex" / "auth.json"),
        "target": "/root/.codex/auth.json",
        "read_only": True,
    }
]
if harness == "cc":
    mounts.append(
        {
            "type": "bind",
            "source": str(home / ".claude" / ".credentials.json"),
            "target": "/root/.claude/.credentials.json",
            "read_only": True,
        }
    )
elif harness != "codex":
    raise SystemExit(f"unknown harness {harness}")
print(json.dumps(mounts))
PY
}

claude_oauth_token() {
  # Prints accessToken only — never log this value.
  python3 - <<'PY'
import json
from pathlib import Path

path = Path.home() / ".claude" / ".credentials.json"
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except OSError:
    raise SystemExit(0)
oauth = data.get("claudeAiOauth") or {}
token = oauth.get("accessToken") if isinstance(oauth, dict) else None
if isinstance(token, str) and token.strip():
    print(token.strip(), end="")
PY
}

write_job_config() {
  local harness="$1"
  local config_file="$2"
  local skills_block="$3"
  local tasks_root="$4"
  local import_path model_name version
  import_path="$(harness_import_path "$harness")"
  model_name="$(harness_model_name "$harness")"
  version="$(harness_cli_version "$harness")"
  cat >"$config_file" <<EOF
agents:
  - import_path: ${import_path}
    model_name: ${model_name}
    skills: ${skills_block}
    kwargs:
      version: "${version}"
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
  local task_dir name skill judge
  local -a judges=()
  rm -rf "$dest"
  mkdir -p "$dest"
  while IFS= read -r task_dir; do
    name="$(basename "$task_dir")"
    cp -a "$task_dir" "$dest/$name"
  done < <(list_task_dirs)
  if [[ ${#skills[@]} -eq 0 ]]; then
    TASKS_DIR="$dest" "$SCRIPT_DIR/sync_judges.sh"
  else
    # Map *-vague skill names onto their real judge directories; dedupe.
    local already j
    for skill in "${skills[@]}"; do
      judge="$(judge_for_skill "$skill")"
      already=0
      for j in "${judges[@]:-}"; do
        if [[ "$j" == "$judge" ]]; then
          already=1
          break
        fi
      done
      if [[ "$already" -eq 0 ]]; then
        judges+=("$judge")
      fi
    done
    TASKS_DIR="$dest" "$SCRIPT_DIR/sync_judges.sh" "${judges[@]}"
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
"""Print a categorized console summary of Harbor trial results."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def _load_json(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    # Harbor scrubs sensitive env VALUES from trial outputs. Flags like
    # CODEX_FORCE_AUTH_JSON=1 make the literal "1" a secret, so
    # {"reward": 1.0} becomes invalid {"reward": [REDACTED].0}. Restore only
    # that numeric reward pattern (not long-token [REDACTED] placeholders).
    if "[REDACTED]" in text:
        text = re.sub(
            r'("reward"\s*:\s*)\[REDACTED\](\.0\b)?',
            lambda m: f"{m.group(1)}1{m.group(2) or ''}",
            text,
        )
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _reward_from_job_result(trial_dir: Path) -> float | None:
    """Fall back to the parent Harbor job result.json reward_stats map."""
    job_result = trial_dir.parent / "result.json"
    payload = _load_json(job_result)
    if not payload:
        return None
    stats = payload.get("stats")
    if not isinstance(stats, dict):
        return None
    evals = stats.get("evals")
    if not isinstance(evals, dict):
        return None
    trial_name = trial_dir.name
    for eval_payload in evals.values():
        if not isinstance(eval_payload, dict):
            continue
        reward_stats = eval_payload.get("reward_stats")
        if not isinstance(reward_stats, dict):
            continue
        reward_map = reward_stats.get("reward")
        if not isinstance(reward_map, dict):
            continue
        for value_key, trial_names in reward_map.items():
            if not isinstance(trial_names, list):
                continue
            if trial_name not in trial_names:
                continue
            try:
                return float(value_key)
            except (TypeError, ValueError):
                continue
    return None


def _reward_value(trial_dir: Path) -> float | None:
    payload = _load_json(trial_dir / "verifier" / "reward.json")
    if payload is not None and "reward" in payload:
        try:
            return float(payload["reward"])
        except (TypeError, ValueError):
            pass
    return _reward_from_job_result(trial_dir)


def _per_skill_rewards(trial_dir: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    verifier = trial_dir / "verifier"
    if not verifier.is_dir():
        return out
    for path in sorted(verifier.glob("reward-*.json")):
        skill = path.name[len("reward-") : -len(".json")]
        if skill.endswith("-details"):
            continue
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


def _harness_of(trial_dir: Path, jobs_root: Path) -> str:
    try:
        rel = trial_dir.relative_to(jobs_root)
        top = rel.parts[0] if rel.parts else ""
    except ValueError:
        top = trial_dir.parent.name
    for candidate in (top, trial_dir.parent.name, *trial_dir.parts):
        if candidate.startswith("cc-") or candidate.startswith("claude"):
            return "cc"
        if candidate.startswith("codex-"):
            return "codex"
    return "unknown"


def _fmt_rate(passed: int, total: int) -> str:
    if total <= 0:
        return "n/a"
    return f"{passed}/{total} ({100.0 * passed / total:.1f}%)"


def _section(title: str) -> None:
    print(file=sys.stderr)
    print("=" * 78, file=sys.stderr)
    print(title, file=sys.stderr)
    print("=" * 78, file=sys.stderr)


def _rate_line(label: str, values: list[float]) -> None:
    passed = sum(1 for value in values if value >= 1.0)
    print(f"  {label}: {_fmt_rate(passed, len(values))}", file=sys.stderr)


jobs_root = Path(sys.argv[1])
run_mode = sys.argv[2] if len(sys.argv) > 2 else "unknown"
skills_csv = sys.argv[3] if len(sys.argv) > 3 else ""
trial_dirs = _trial_dirs(jobs_root)
if not trial_dirs:
    print("No trial reward.json files found under", jobs_root, file=sys.stderr)
    raise SystemExit(0)

_section(
    f"Trial results ({len(trial_dirs)}) — mode={run_mode} "
    f"skills={skills_csv or '-'} — {jobs_root}"
)

by_harness: dict[str, list[float]] = defaultdict(list)
by_harness_skill: dict[tuple[str, str], list[float]] = defaultdict(list)
by_harness_task: dict[tuple[str, str], list[float]] = defaultdict(list)
by_harness_task_skill: dict[tuple[str, str, str], list[float]] = defaultdict(list)
by_skill: dict[str, list[float]] = defaultdict(list)
by_task: dict[str, list[float | None]] = defaultdict(list)
rewards: list[float] = []

for index, trial_dir in enumerate(trial_dirs, start=1):
    reward = _reward_value(trial_dir)
    judge_rows = _judge_criteria(trial_dir)
    sources = _python_sources(trial_dir)
    task = _task_name(trial_dir)
    harness = _harness_of(trial_dir, jobs_root)
    per_skill = _per_skill_rewards(trial_dir)
    by_task[task].append(reward)
    if reward is not None:
        rewards.append(reward)
        by_harness[harness].append(reward)
        by_harness_task[(harness, task)].append(reward)
    for skill, value in per_skill.items():
        by_skill[skill].append(value)
        by_harness_skill[(harness, skill)].append(value)
        by_harness_task_skill[(harness, task, skill)].append(value)

    verdict = "PASS" if reward is not None and reward >= 1.0 else "FAIL"
    reward_text = "n/a" if reward is None else f"{reward:g}"
    print(file=sys.stderr)
    print(
        f"[{index}/{len(trial_dirs)}] [{harness}] {trial_dir.name}  "
        f"{verdict}  reward={reward_text}",
        file=sys.stderr,
    )
    if per_skill:
        bits = ", ".join(
            f"{name}={value:g}" for name, value in sorted(per_skill.items())
        )
        print(f"  per-skill: {bits}", file=sys.stderr)
    if judge_rows:
        for skill_name, raw, reasoning in judge_rows:
            if raw is not None:
                print(f"  judge[{skill_name}] answer: {raw}", file=sys.stderr)
            if reasoning:
                print(f"  judge[{skill_name}] reason: {reasoning}", file=sys.stderr)
            elif raw is not None:
                print(
                    f"  judge[{skill_name}] reason: (none recorded)",
                    file=sys.stderr,
                )
    if sources:
        for rel, source in sources:
            print(f"  {rel}:", file=sys.stderr)
            for line in source.splitlines():
                print(f"    {line}", file=sys.stderr)
    else:
        print("  source: (no *.py artifacts downloaded)", file=sys.stderr)

_section(f"By harness (mode={run_mode})")
for harness in sorted(by_harness):
    _rate_line(harness, by_harness[harness])

_section(f"By harness × skill (mode={run_mode})")
for harness, skill in sorted(by_harness_skill):
    _rate_line(f"{harness} / {skill}", by_harness_skill[(harness, skill)])

_section(f"By harness × coding task (mode={run_mode})")
for harness, task in sorted(by_harness_task):
    _rate_line(f"{harness} / {task}", by_harness_task[(harness, task)])

_section(f"By harness × task × skill (mode={run_mode})")
for harness, task, skill in sorted(by_harness_task_skill):
    _rate_line(
        f"{harness} / {task} / {skill}",
        by_harness_task_skill[(harness, task, skill)],
    )

if by_skill:
    _section(f"By skill judge — all harnesses (mode={run_mode})")
    for skill in sorted(by_skill):
        _rate_line(skill, by_skill[skill])

_section(f"By coding task — all harnesses (mode={run_mode})")
for task in sorted(by_task):
    values = [value for value in by_task[task] if value is not None]
    passed = sum(1 for value in values if value >= 1.0)
    print(f"  {task}: {_fmt_rate(passed, len(values))}", file=sys.stderr)

if len(by_harness) >= 2:
    _section("Harness comparison (same mode/skills/tasks)")
    print(
        f"  {'harness':<10} {'pass_rate':<22} {'passed':>7} {'total':>7}",
        file=sys.stderr,
    )
    for harness in sorted(by_harness):
        values = by_harness[harness]
        passed = sum(1 for value in values if value >= 1.0)
        print(
            f"  {harness:<10} {_fmt_rate(passed, len(values)):<22} "
            f"{passed:>7} {len(values):>7}",
            file=sys.stderr,
        )

print(file=sys.stderr)
print("-" * 78, file=sys.stderr)
if rewards:
    passed = sum(1 for value in rewards if value >= 1.0)
    total = len(rewards)
    print(f"GRAND TOTAL pass_rate={_fmt_rate(passed, total)}", file=sys.stderr)
else:
    print("GRAND TOTAL pass_rate=n/a (no numeric rewards)", file=sys.stderr)
print("-" * 78, file=sys.stderr)
PY
}

capture_print_summary() {
  local jobs_root="$1"
  local run_mode="$2"
  local skills_csv="$3"
  SUMMARY_CAPTURE_FILE="$(mktemp)"
  # Capture stderr summary to a file, then replay it to the console.
  print_summary "$jobs_root" "$run_mode" "$skills_csv" 2>"$SUMMARY_CAPTURE_FILE" || true
  cat "$SUMMARY_CAPTURE_FILE" >&2
}

archive_sync_job() {
  local job_name="$1"
  python3 "$SCRIPT_DIR/archive_benchmark_run.py" sync-job \
    --run-dir "$RUN_DIR" \
    --jobs-root "$JOBS" \
    --job-name "$job_name" \
    --summary-file "$SUMMARY_CAPTURE_FILE" >/dev/null
  rm -f "$SUMMARY_CAPTURE_FILE"
  SUMMARY_CAPTURE_FILE=""
  echo "written to: $RUN_DIR/jobs/$job_name" >&2
}

archive_finalize() {
  local summary_args=()
  if [[ -n "${SUMMARY_CAPTURE_FILE:-}" && -f "${SUMMARY_CAPTURE_FILE:-}" ]]; then
    summary_args=(--summary-file "$SUMMARY_CAPTURE_FILE")
  fi
  python3 "$SCRIPT_DIR/archive_benchmark_run.py" finalize \
    --run-dir "$RUN_DIR" \
    --jobs-root "$JOBS" \
    "${summary_args[@]}" >/dev/null
  if [[ -n "${SUMMARY_CAPTURE_FILE:-}" ]]; then
    rm -f "$SUMMARY_CAPTURE_FILE"
    SUMMARY_CAPTURE_FILE=""
  fi
  echo "written to: $RUN_DIR" >&2
}

run_harbor_for_harness() {
  local harness="$1"
  shift
  local mounts version
  mounts="$(harness_mounts_json "$harness")"
  version="$(harness_cli_version "$harness")"
  local -a env_flags=()
  case "$harness" in
    codex)
      # Use "true", not "1": Harbor scrubs sensitive env VALUES from trial
      # outputs (keys matching AUTH/TOKEN/…). Value "1" rewrites every reward
      # 1.0 into invalid JSON ("[REDACTED].0") and breaks our summary.
      env_flags+=(CODEX_FORCE_AUTH_JSON=true)
      ;;
    cc)
      local token
      token="$(claude_oauth_token || true)"
      if [[ -z "$token" ]]; then
        echo "Claude harness needs ~/.claude/.credentials.json with claudeAiOauth.accessToken" \
          "(or export CLAUDE_CODE_OAUTH_TOKEN before running)." >&2
        exit 1
      fi
      env_flags+=(
        CLAUDE_FORCE_OAUTH=true
        "CLAUDE_CODE_OAUTH_TOKEN=$token"
      )
      ;;
  esac
  # Env vars must be visible to Harbor's agent process; export for this call only.
  (
    export "${env_flags[@]}"
    # Also pass through Harbor --ae so the trial container sees them.
    local -a ae_flags=()
    local pair
    for pair in "${env_flags[@]}"; do
      ae_flags+=(--ae "$pair")
    done
    harbor run \
      --mounts "$mounts" \
      --ak "version=$version" \
      "${ae_flags[@]}" \
      "$@"
  )
}

run_one_job() {
  local harness="$1"
  local job_name="$2"
  local run_mode="$3"
  shift 3
  local -a skill_paths=("$@")

  local skills_csv
  skills_csv="$(printf '%s,' "${SELECTED_SKILLS_FOR_JOB[@]:-}")"
  skills_csv="${skills_csv%,}"

  local tasks_root
  tasks_root="$(prepare_job_tasks "$job_name" "${SELECTED_SKILLS_FOR_JOB[@]}")"

  local config_file
  if [[ "$BASELINE" -eq 1 ]]; then
    config_file="$JOBS/harbor.${job_name}.yaml"
    write_job_config "$harness" "$config_file" "[]" "$tasks_root"
  elif [[ "$NEGATIVE" -eq 1 ]]; then
    local skill="${SELECTED_SKILLS_FOR_JOB[0]}"
    local neg_skill_dir="$JOBS/generated-negative-skill-$harness-$skill"
    local neg_tasks_root="$JOBS/generated-negative-tasks-$harness-$skill"
    generate_negative_skill "$neg_skill_dir" "$SKILLS_ROOT/$skill/SKILL.md" "$skill" >/dev/null
    generate_negative_tasks_from_root "$neg_tasks_root" "$skill" "$tasks_root"
    config_file="$JOBS/harbor.${job_name}.yaml"
    write_job_config "$harness" "$config_file" "$(skills_yaml_block "$neg_skill_dir")" "$neg_tasks_root"
    tasks_root="$neg_tasks_root"
    echo "Negative mode for harness=$harness skill=$skill" >&2
  else
    config_file="$JOBS/harbor.${job_name}.yaml"
    write_job_config "$harness" "$config_file" "$(skills_yaml_block "${skill_paths[@]}")" "$tasks_root"
  fi

  collect_artifact_flags
  local -a common=(
    -c "$config_file"
    -o "$JOBS"
    "${ARTIFACT_FLAGS[@]}"
  )

  local -a harbor_args=("${HARBOR_ARGS[@]}")
  if [[ ${#harbor_args[@]} -eq 0 ]]; then
    harbor_args=(--job-name "$job_name" -k 5 -n 5)
  else
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
  echo "Job $job_name [$harness] schedules about $((task_count * attempts_per_task)) trials ($attempts_per_task attempts × $task_count tasks)." >&2
  echo "Job $job_name judges: ${SELECTED_SKILLS_FOR_JOB[*]:-(none)} (isolated under $tasks_root)" >&2
  echo "Model default: $(harness_model_name "$harness") @ reasoning_effort=low (CLI $(harness_cli_version "$harness"))" >&2

  run_harbor_for_harness "$harness" "${common[@]}" "${harbor_args[@]}"
  capture_print_summary "$JOBS/$job_name" "$run_mode" "$skills_csv"
  archive_sync_job "$job_name"
}

run_jobs_for_harness() {
  local harness="$1"
  if [[ "$RUN_SEPARATELY" -eq 1 ]]; then
    echo "Running each selected skill in its own prompt instance for harness=$harness (--run-separately)." >&2
    local skill
    for skill in "${SELECTED_SKILLS[@]}"; do
      SELECTED_SKILLS_FOR_JOB=("$skill")
      if [[ "$BASELINE" -eq 1 ]]; then
        run_one_job "$harness" "$(harbor_job_name "${harness}-baseline-$skill")" "baseline"
      elif [[ "$NEGATIVE" -eq 1 ]]; then
        run_one_job "$harness" "$(harbor_job_name "${harness}-negative-$skill")" "negative"
      else
        run_one_job "$harness" "$(harbor_job_name "${harness}-$skill")" "positive" "$SKILLS_ROOT/$skill"
      fi
    done
  else
    SELECTED_SKILLS_FOR_JOB=("${SELECTED_SKILLS[@]}")
    if [[ "$NEGATIVE" -eq 1 && ${#SELECTED_SKILLS[@]} -gt 1 ]]; then
      echo "Combined --negative with multiple skills is ambiguous; use --run-separately." >&2
      exit 1
    fi
    if [[ "$BASELINE" -eq 1 ]]; then
      run_one_job "$harness" "$(harbor_job_name "${harness}-baseline")" "baseline"
    elif [[ "$NEGATIVE" -eq 1 ]]; then
      run_one_job "$harness" "$(harbor_job_name "${harness}-negative-${SELECTED_SKILLS[0]}")" "negative"
    else
      local -a skill_paths=()
      local skill
      for skill in "${SELECTED_SKILLS[@]}"; do
        skill_paths+=("$SKILLS_ROOT/$skill")
      done
      run_one_job "$harness" "$(harbor_job_name "${harness}-skills")" "positive" "${skill_paths[@]}"
    fi
  fi
}

# --- install-only path uses a minimal generated config ---
if [[ "$INSTALL_ONLY" -eq 1 ]]; then
  SELECTED_SKILLS_FOR_JOB=("${SELECTED_SKILLS[@]}")
  "$SCRIPT_DIR/sync_tasks.sh"
  for install_harness in "${SELECTED_HARNESSES[@]}"; do
    install_version="$(harness_cli_version "$install_harness")"
    install_job_name="$(harbor_job_name "${install_harness}-install-$install_version")"
    install_tasks_root="$(prepare_job_tasks "$install_job_name" "${SELECTED_SKILLS[@]}")"
    collect_artifact_flags
    install_config="$JOBS/harbor.${install_job_name}.yaml"
    write_job_config "$install_harness" "$install_config" "$(skills_yaml_block "$SKILLS_ROOT/${SELECTED_SKILLS[0]}")" "$install_tasks_root"
    echo "Reinstalling/verifying $install_harness @$install_version inside the task environment" >&2
    run_harbor_for_harness "$install_harness" \
      -c "$install_config" \
      -o "$JOBS" \
      "${ARTIFACT_FLAGS[@]}" \
      --install-only \
      --job-name "$install_job_name" \
      "${HARBOR_ARGS[@]}"
  done
  exit 0
fi

"$SCRIPT_DIR/sync_tasks.sh"
TASK_COUNT="$(list_task_dirs | wc -l | tr -d ' ')"
echo "Discovered $TASK_COUNT coding task(s) under $TASKS_DIR" >&2

# Estimate total trials for the user.
ATTEMPTS_PER_TASK=5
CONCURRENT=5
for ((i = 0; i < ${#HARBOR_ARGS[@]}; i++)); do
  if [[ "${HARBOR_ARGS[$i]}" == "-k" || "${HARBOR_ARGS[$i]}" == "--n-attempts" ]]; then
    ATTEMPTS_PER_TASK="${HARBOR_ARGS[$((i + 1))]:-$ATTEMPTS_PER_TASK}"
  fi
  if [[ "${HARBOR_ARGS[$i]}" == "-n" || "${HARBOR_ARGS[$i]}" == "--n-concurrent" ]]; then
    CONCURRENT="${HARBOR_ARGS[$((i + 1))]:-$CONCURRENT}"
  fi
done
SKILL_FACTOR=1
if [[ "$RUN_SEPARATELY" -eq 1 ]]; then
  SKILL_FACTOR=${#SELECTED_SKILLS[@]}
fi
HARNESS_FACTOR=${#SELECTED_HARNESSES[@]}
ESTIMATED_TRIALS=$((HARNESS_FACTOR * SKILL_FACTOR * TASK_COUNT * ATTEMPTS_PER_TASK))
echo "Estimated trials ≈ $ESTIMATED_TRIALS (= $HARNESS_FACTOR harness(es) × $SKILL_FACTOR skill-job(s) × $TASK_COUNT task(s) × $ATTEMPTS_PER_TASK attempts)." >&2

if [[ "$BASELINE" -eq 1 ]]; then
  RUN_MODE_LABEL="baseline"
elif [[ "$NEGATIVE" -eq 1 ]]; then
  RUN_MODE_LABEL="negative"
else
  RUN_MODE_LABEL="positive"
fi
# RUN_STAMP already set at startup (timestamp + pid) for Harbor job uniqueness.
mkdir -p "$RUNS_ROOT"
ARCHIVE_INIT_ARGS=(
  --runs-root "$RUNS_ROOT"
  --timestamp "$RUN_STAMP"
  --mode "$RUN_MODE_LABEL"
  --attempts "$ATTEMPTS_PER_TASK"
  --concurrent "$CONCURRENT"
  --jobs-temp "$JOBS"
  --command "./run_benchmark.sh $(printf '%q ' "${ORIGINAL_ARGV[@]}")"
)
for _h in "${SELECTED_HARNESSES[@]}"; do
  ARCHIVE_INIT_ARGS+=(--harness "$_h")
done
for _s in "${SELECTED_SKILLS[@]}"; do
  ARCHIVE_INIT_ARGS+=(--skill "$_s")
done
for _t in "${SELECTED_TASKS[@]}"; do
  ARCHIVE_INIT_ARGS+=(--task "$_t")
done
if [[ "$RUN_SEPARATELY" -eq 1 ]]; then
  ARCHIVE_INIT_ARGS+=(--separately)
fi
RUN_DIR="$(python3 "$SCRIPT_DIR/archive_benchmark_run.py" init "${ARCHIVE_INIT_ARGS[@]}")"
echo "Run archive: $RUN_DIR" >&2

for HARNESS in "${SELECTED_HARNESSES[@]}"; do
  echo "======== harness=$HARNESS ========" >&2
  run_jobs_for_harness "$HARNESS"
done

if [[ ${#SELECTED_HARNESSES[@]} -gt 1 || "$RUN_SEPARATELY" -eq 1 ]]; then
  echo "Combined categorized summary across all jobs in $JOBS:" >&2
  if [[ "$BASELINE" -eq 1 ]]; then
    capture_print_summary "$JOBS" "baseline-all" "${SELECTED_SKILLS[*]}"
  elif [[ "$NEGATIVE" -eq 1 ]]; then
    capture_print_summary "$JOBS" "negative-all" "${SELECTED_SKILLS[*]}"
  else
    capture_print_summary "$JOBS" "positive-all" "${SELECTED_SKILLS[*]}"
  fi
fi
archive_finalize

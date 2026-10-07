# Discover selected skills and tasks and render task YAML fragments.

judge_for_skill() {
  # Score <base>-vague controls with the real <base> judge.
  local skill="$1"
  if [[ "$skill" == *-vague ]]; then
    printf '%s\n' "${skill%-vague}"
  else
    printf '%s\n' "$skill"
  fi
}

list_available_skills() {
  # Default discovery skips controls and explicit-only skills; callers can
  # still select either one by name with --skills.
  local skill_dir name
  for skill_dir in "$SKILLS_ROOT"/*; do
    [[ -d "$skill_dir" && -f "$skill_dir/SKILL.md" ]] || continue
    name="$(basename "$skill_dir")"
    [[ "$name" == *-vague ]] && continue
    [[ -f "$skill_dir/.opt-in" ]] && continue
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
    if [[ -f "$JUDGES_ROOT/$judge/prompt.md" || -f "$JUDGES_ROOT/$judge/judge-prompt.md" ]]; then
      continue
    fi
    if [[ -f "$JUDGES_ROOT/$judge/judge.toml" ]] && grep -qE '^judge[[:space:]]*=[[:space:]]*"programmatic"' "$JUDGES_ROOT/$judge/judge.toml"; then
      continue
    fi
    echo "Missing judge for skill '$skill' (expected $JUDGES_ROOT/$judge/prompt.md or a programmatic judge.toml)" >&2
    exit 1
  done
  printf '%s\n' "${selected[@]}"
}

task_prompt_path() {
  local name="$1" directory
  for directory in "$CODING_PROMPTS_DIR" "${DEBUG_PROMPTS_DIR:-$CODING_PROMPTS_DIR/../debug-prompts}"; do
    if [[ -f "$directory/$name.md" && "$name" != README ]]; then
      printf '%s\n' "$directory/$name.md"
      return 0
    fi
  done
  return 1
}

default_task_suite() {
  local skill has_debug=0 has_coding=0
  for skill in "${SELECTED_SKILLS[@]:-}"; do
    if [[ "$skill" == debug ]]; then has_debug=1; else has_coding=1; fi
  done
  if [[ "$has_debug" -eq 1 && "$has_coding" -eq 1 ]]; then
    printf '%s\n' all
  elif [[ "$has_debug" -eq 1 ]]; then
    printf '%s\n' debug
  else
    printf '%s\n' coding
  fi
}

task_family() {
  local path
  path="$(task_prompt_path "$1")" || return 1
  if [[ "$(dirname "$path")" == "${DEBUG_PROMPTS_DIR:-$CODING_PROMPTS_DIR/../debug-prompts}" ]]; then
    printf '%s\n' debug
  else
    printf '%s\n' coding
  fi
}

list_available_tasks() {
  local suite="${1:-${SUITE_ARG:-$(default_task_suite)}}" directory prompt
  local -a directories=()
  [[ "$suite" == coding || "$suite" == all ]] && directories+=("$CODING_PROMPTS_DIR")
  [[ "$suite" == debug || "$suite" == all ]] && directories+=("${DEBUG_PROMPTS_DIR:-$CODING_PROMPTS_DIR/../debug-prompts}")
  for directory in "${directories[@]}"; do
    for prompt in "$directory"/*.md; do
      [[ -f "$prompt" && "$(basename "$prompt")" != README.md ]] || continue
      printf '%s\n' "$(basename "$prompt" .md)"
    done
  done | sort
}

resolve_tasks() {
  local raw="$1"
  local -a selected=()
  if [[ -z "$raw" ]]; then
    mapfile -t selected < <(list_available_tasks)
  else
    local IFS=',' part
    local -a parts
    read -r -a parts <<<"$raw"
    for part in "${parts[@]}"; do
      part="$(echo "$part" | tr -d '[:space:]')"
      [[ -n "$part" ]] && selected+=("$part")
    done
  fi
  if [[ ${#selected[@]} -eq 0 ]]; then
    echo "No tasks selected for suite ${SUITE_ARG:-coding}" >&2
    return 1
  fi
  local task path
  for task in "${selected[@]}"; do
    path="$(task_prompt_path "$task")" || {
      echo "Unknown task '$task'; available: $(list_available_tasks all | tr '\n' ' ')" >&2
      return 1
    }
    if [[ "$(task_family "$task")" == debug ]]; then
      if [[ " ${SELECTED_SKILLS[*]:-} " != *" debug "* ]]; then
        echo "Debug task '$task' requires --skills debug (alone or alongside other skills)" >&2
        return 1
      fi
    elif [[ "$(default_task_suite)" == debug ]]; then
      echo "Coding task '$task' has no applicable selected coding skill; use --suite debug or add a coding skill" >&2
      return 1
    fi
    if [[ -n "${SUITE_ARG:-}" && "$SUITE_ARG" != all ]]; then
      if ! list_available_tasks "$SUITE_ARG" | grep -qxF "$task"; then
        echo "Task '$task' is outside --suite $SUITE_ARG" >&2
        return 1
      fi
    fi
  done
  printf '%s\n' "${selected[@]}"
}

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

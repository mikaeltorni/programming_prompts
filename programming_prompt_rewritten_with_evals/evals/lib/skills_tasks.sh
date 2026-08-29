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

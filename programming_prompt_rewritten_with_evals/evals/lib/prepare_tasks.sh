# Prepare isolated generated task trees for each Harbor job.

prepare_instruction_bundle() {
  # Build family documents and an explicit instruction document for each task.
  # Parameters: $1 - transport bundle path; remaining arguments - selected policies.
  # Returns: None after generating the portable bundle; propagates build errors.
  local bundle="$1" task family csv skill
  shift
  local -a skills=("$@") applicable=()
  mkdir -p "$bundle/task-instructions" || return 1
  for task in "${SELECTED_TASKS[@]}"; do
    family="$(task_family "$task")" || return 1
    if [[ ! -f "$bundle/families/$family/instructions.md" ]]; then
      mapfile -t applicable < <(skills_for_task_family "$family" "${skills[@]}")
      [[ ${#applicable[@]} -gt 0 ]] || return 1
      csv=''
      for skill in "${applicable[@]}"; do csv+="${csv:+,}v2:$skill"; done
      python3 "$SCRIPT_DIR/../../scripts/global_instructions.py" \
        --source-root "$SCRIPT_DIR/../.." --skills "$csv" \
        --bundle-dir "$bundle/families/$family" || return 1
    fi
    cp "$bundle/families/$family/instructions.md" "$bundle/task-instructions/$task.md" || return 1
  done
  # Harbor discovers one transport root; it never registers nested policy skills.
  printf '%s\n' '---' 'name: global-instructions' \
    'description: Per-task global instructions for a shared benchmark schedule.' '---' > "$bundle/SKILL.md" || return 1
  cp "$SCRIPT_DIR/../../scripts/global_instructions.py" "$bundle/builder.py" || return 1
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
  if [[ "${RUN_SEPARATELY:-0}" -eq 1 ]]; then
    local copied
    for copied in "$dest"/*/; do
      mkdir -p "${copied}tests"
      printf '1\n' > "${copied}tests/eval_run_separately"
    done
    echo "Marked $dest tasks for independent skill Pass (not AND)." >&2
  fi
  printf '%s\n' "$dest"
}

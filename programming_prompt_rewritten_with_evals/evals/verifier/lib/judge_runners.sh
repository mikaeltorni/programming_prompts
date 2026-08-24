#!/usr/bin/env bash
# Build and run programmatic and LLM judge jobs.

run_llm_eval_agent() {
  local judge_dir="$1"
  local output_json="$2"
  local eval_agent="$3"
  local model="$4"
  local effort="$5"
  echo "Running $eval_agent eval agent (model=$model effort=$effort)" >&2
  python3 "$LLM_HELPER" \
    --agent "$eval_agent" \
    --judge-dir "$judge_dir" \
    --output "$output_json" \
    --workspace /Projects/app \
    --model "$model" \
    --reasoning-effort "$effort" || return 1
}

run_programmatic_judge() {
  local output_json="$1"
  local checker="$HERE/check_worktree.py"
  if [[ ! -f "$checker" ]]; then
    echo "Missing programmatic checker: $checker" >&2
    return 1
  fi
  python3 "$checker" --repo /Projects/app --output "$output_json"
}

run_one_judge() {
  local judge_dir="$1"
  local output_json="$2"
  local skill idx agent model effort agent_out
  skill="$(basename "$judge_dir")"
  if [[ -f "$judge_dir/judge.toml" ]] && grep -qE '^judge[[:space:]]*=[[:space:]]*"programmatic"' "$judge_dir/judge.toml"; then
    echo "Running programmatic judge for skill: $skill" >&2
    run_programmatic_judge "$output_json"
    return 0
  fi
  for idx in "${!EVAL_AGENT_LIST[@]}"; do
    agent="${EVAL_AGENT_LIST[$idx]}"
    model="${EVAL_MODELS[$idx]}"
    effort="${EVAL_EFFORTS[$idx]}"
    agent_out="/logs/verifier/reward-${skill}-${agent}.json"
    echo "Running judge for skill=$skill evalAgent=$agent" >&2
    if ! run_llm_eval_agent "$judge_dir" "$agent_out" "$agent" "$model" "$effort"; then
      echo "evalAgent=$agent failed for skill=$skill (continuing other agents/skills)" >&2
    fi
  done
  aggregate_eval_agent_rewards "$skill" "$output_json"
}

append_judge_job() {
  local label="$1"
  shift
  python3 - "$JOBS_FILE" "$label" "$@" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
label = sys.argv[2]
argv = sys.argv[3:]
jobs = json.loads(path.read_text(encoding="utf-8"))
jobs.append({"label": label, "argv": list(argv)})
path.write_text(json.dumps(jobs) + "\n", encoding="utf-8")
print(f"Queued judge job {label}", file=sys.stderr, flush=True)
PY
}

skill_is_llm() {
  local candidate="$1"
  local llm
  for llm in "${llm_skills[@]:-}"; do
    if [[ "$llm" == "$candidate" ]]; then
      return 0
    fi
  done
  return 1
}

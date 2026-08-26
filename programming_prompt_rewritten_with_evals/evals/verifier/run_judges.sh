#!/usr/bin/env bash
# Canonical Harbor verifier entrypoint for all coding tasks.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
LLM_HELPER="$HERE/run_llm_judge.py"
JUDGE_POOL="$HERE/judge_pool.py"
CODEX_AUTH_SOURCE=""

for library in "$HERE/lib/"*.sh; do
  # shellcheck source=/dev/null
  source "$library"
done

if [[ "${1:-}" == "--self-test" ]]; then
  exec python3 "$JUDGE_POOL" --self-test
fi

mkdir -p /logs/verifier
declare -a EVAL_AGENT_LIST=() EVAL_MODELS=() EVAL_EFFORTS=()
configure_eval_agents
detect_judge_requirements
preflight_judges

declare -a skill_names=() llm_skills=() skill_rewards=()
JOBS_FILE="$(mktemp)"
echo '[]' >"$JOBS_FILE"

if [[ -d /tests/judges ]]; then
  for judge_dir in /tests/judges/*; do
    [[ -d "$judge_dir" && -f "$judge_dir/judge.toml" ]] || continue
    skill="$(basename "$judge_dir")"
    skill_names+=("$skill")
    out="/logs/verifier/reward-${skill}.json"
    if grep -qE '^judge[[:space:]]*=[[:space:]]*"programmatic"' "$judge_dir/judge.toml"; then
      echo "Queue programmatic judge for skill: $skill" >&2
      append_judge_job "$skill" python3 "$HERE/check_worktree.py" \
        --repo /Projects/app --output "$out"
      continue
    fi
    llm_skills+=("$skill")
    for local_idx in "${!EVAL_AGENT_LIST[@]}"; do
      agent="${EVAL_AGENT_LIST[$local_idx]}"
      model="${EVAL_MODELS[$local_idx]}"
      effort="${EVAL_EFFORTS[$local_idx]}"
      agent_out="/logs/verifier/reward-${skill}-${agent}.json"
      echo "Queue judge for skill=$skill evalAgent=$agent" >&2
      append_judge_job "${skill}/${agent}" python3 "$LLM_HELPER" \
        --agent "$agent" \
        --judge-dir "$judge_dir" \
        --output "$agent_out" \
        --workspace /Projects/app \
        --model "$model" \
        --reasoning-effort "$effort"
    done
  done
fi

if [[ ${#skill_names[@]} -eq 0 ]]; then
  rm -f "$JOBS_FILE"
  run_one_judge /tests /logs/verifier/reward.json
  exit 0
fi

echo "Running judge jobs (EVAL_JUDGE_WORKERS=${EVAL_JUDGE_WORKERS:-4})" >&2
if ! python3 "$JUDGE_POOL" "$JOBS_FILE" >/logs/verifier/judge-pool-results.json; then
  echo "judge pool failed to run (continuing to aggregate whatever rewards exist)" >&2
fi
rm -f "$JOBS_FILE"

for skill in "${skill_names[@]}"; do
  out="/logs/verifier/reward-${skill}.json"
  if skill_is_llm "$skill"; then
    aggregate_eval_agent_rewards "$skill" "$out"
  fi
  skill_rewards+=("$(read_skill_reward "$out")")
  print_skill_bits "$skill"
done

write_overall_reward skill_names skill_rewards

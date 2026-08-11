#!/usr/bin/env bash
# Run each synced skill judge against /app and write per-skill + aggregate rewards.
set -euo pipefail

mkdir -p /logs/verifier

auth_source=""
for candidate in \
    "${CODEX_HOME:-}/auth.json" \
    /tmp/codex-home/auth.json \
    "${HOME}/.codex/auth.json"
do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
        auth_source="$candidate"
        break
    fi
done

if [[ -z "$auth_source" ]]; then
    echo "Codex authentication is required for the LLM verifier." >&2
    exit 1
fi

judge_home="$(mktemp -d)"
trap 'rm -rf "$judge_home"' EXIT
install -m 600 "$auth_source" "$judge_home/auth.json"
printf '%s\n' \
    'model_reasoning_effort = "low"' \
    'sandbox_mode = "danger-full-access"' \
    > "$judge_home/config.toml"

run_one_judge() {
    local judge_dir="$1"
    local output_json="$2"
    local work
    work="$(mktemp -d)"
    cp "$judge_dir/judge-prompt.md" "$judge_dir/judge.toml" "$work/"
    CODEX_HOME="$judge_home" uvx --from harbor-rewardkit@0.1.7 \
        rewardkit "$work" \
        --workspace /app \
        --output "$output_json"
    rm -rf "$work"
}

declare -a skill_names=()
declare -a skill_rewards=()

if [[ -d /tests/judges ]]; then
    for judge_dir in /tests/judges/*; do
        [[ -d "$judge_dir" && -f "$judge_dir/judge.toml" ]] || continue
        skill="$(basename "$judge_dir")"
        out="/logs/verifier/reward-${skill}.json"
        echo "Running judge for skill: $skill" >&2
        run_one_judge "$judge_dir" "$out"
        skill_names+=("$skill")
        reward="$(python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(float(payload.get("reward", 0)))
PY
)"
        skill_rewards+=("$reward")
    done
fi

if [[ ${#skill_names[@]} -eq 0 ]]; then
    # Fallback: single judge files at /tests root
    run_one_judge /tests /logs/verifier/reward.json
    exit 0
fi

python3 - <<'PY' /logs/verifier "${skill_names[@]}" -- "${skill_rewards[@]}"
from __future__ import annotations

import json
import sys
from pathlib import Path

args = sys.argv[1:]
sep = args.index("--")
out_dir = Path(args[0])
names = args[1:sep]
rewards = [float(value) for value in args[sep + 1 :]]

criteria = []
for name, reward in zip(names, rewards, strict=True):
    details_path = out_dir / f"reward-{name}.json"
    details = {}
    if details_path.is_file():
        try:
            details = json.loads(details_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            details = {}
    criteria.append(
        {
            "name": name,
            "reward": reward,
            "raw": "yes" if reward >= 1.0 else "no",
            "details": details,
        }
    )

overall = 1.0 if rewards and all(value >= 1.0 for value in rewards) else 0.0
(out_dir / "reward.json").write_text(
    json.dumps({"reward": overall}, indent=2) + "\n",
    encoding="utf-8",
)
(out_dir / "reward-details.json").write_text(
    json.dumps(
        {
            "reward": {
                "aggregation": "all_pass",
                "overall": overall,
                "criteria": criteria,
            }
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print(f"Aggregate reward={overall} across skills: {', '.join(names)}", flush=True)
PY

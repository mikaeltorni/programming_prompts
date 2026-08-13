#!/usr/bin/env bash
# Canonical Harbor verifier for all coding tasks.
# Synced into tasks/*/tests/run_judges.sh by sync_judges.sh; task test.sh execs it.
# Each skill keeps its own prompt at evals/judges/<skill>/prompt.md.
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
    local work prompt_file
    if [[ -f "$judge_dir/judge.toml" ]] && grep -qE '^judge[[:space:]]*=[[:space:]]*"programmatic"' "$judge_dir/judge.toml"; then
        HERE="$(cd "$(dirname "$0")" && pwd)"
        checker="$HERE/check_worktree.py"
        if [[ ! -f "$checker" ]]; then
            echo "Missing programmatic checker: $checker" >&2
            return 1
        fi
        python3 "$checker" --repo /app --output "$output_json"
        return 0
    fi
    work="$(mktemp -d)"
    prompt_file=""
    for candidate in "$judge_dir/prompt.md" "$judge_dir/judge-prompt.md"; do
        if [[ -f "$candidate" ]]; then
            prompt_file="$candidate"
            break
        fi
    done
    if [[ -z "$prompt_file" || ! -f "$judge_dir/judge.toml" ]]; then
        echo "Judge dir missing prompt.md/judge-prompt.md or judge.toml: $judge_dir" >&2
        rm -rf "$work"
        return 1
    fi
    cp "$prompt_file" "$judge_dir/judge.toml" "$work/"
    # Rewardkit reads prompt_template from judge.toml; keep the on-disk name stable.
    if [[ "$(basename "$prompt_file")" != "prompt.md" ]]; then
        cp "$prompt_file" "$work/prompt.md"
    fi
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
        # rewardkit always writes sibling reward-details.json; keep it per skill
        # before the next judge overwrites it.
        if [[ -f /logs/verifier/reward-details.json ]]; then
            mv /logs/verifier/reward-details.json \
                "/logs/verifier/reward-${skill}-details.json"
        fi
        skill_names+=("$skill")
        reward="$(python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(float(payload.get("reward", 0)))
PY
)"
        skill_rewards+=("$reward")
        python3 - "$skill" "/logs/verifier/reward-${skill}-details.json" <<'PY'
import json, sys
from pathlib import Path

skill, path_s = sys.argv[1], sys.argv[2]
path = Path(path_s)
reasoning = ""
raw = ""
if path.is_file():
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {}
    reward = payload.get("reward")
    if isinstance(reward, dict):
        criteria = reward.get("criteria") or []
        if criteria and isinstance(criteria[0], dict):
            reasoning = str(criteria[0].get("reasoning") or "")
            raw = str(criteria[0].get("raw") or "")
        if not reasoning:
            reasoning = str(reward.get("judge_output") or "")[:2000]
print(f"Judge {skill}: raw={raw or '?'} reasoning={reasoning or '(none)'}", flush=True)
PY
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


def _extract_bits(details: dict) -> tuple[str, str]:
    reward = details.get("reward")
    if not isinstance(reward, dict):
        return "", ""
    criteria = reward.get("criteria")
    if isinstance(criteria, list) and criteria and isinstance(criteria[0], dict):
        first = criteria[0]
        raw = first.get("raw")
        reasoning = first.get("reasoning") or ""
        if raw is None and first.get("value") is not None:
            try:
                raw = "yes" if float(first["value"]) >= 1.0 else "no"
            except (TypeError, ValueError):
                raw = first.get("value")
        return (str(raw) if raw is not None else ""), str(reasoning)
    return "", str(reward.get("judge_output") or "")


args = sys.argv[1:]
sep = args.index("--")
out_dir = Path(args[0])
names = args[1:sep]
rewards = [float(value) for value in args[sep + 1 :]]

criteria = []
for name, reward in zip(names, rewards, strict=True):
    details_path = out_dir / f"reward-{name}-details.json"
    details: dict = {}
    if details_path.is_file():
        try:
            details = json.loads(details_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            details = {}
    raw, reasoning = _extract_bits(details)
    if not raw:
        raw = "yes" if reward >= 1.0 else "no"
    criteria.append(
        {
            "name": name,
            "reward": reward,
            "raw": raw,
            "reasoning": reasoning,
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
for item in criteria:
    reason = item.get("reasoning") or "(none)"
    print(
        f"  {item['name']}: raw={item['raw']} reward={item['reward']} "
        f"reasoning={reason}",
        flush=True,
    )
PY

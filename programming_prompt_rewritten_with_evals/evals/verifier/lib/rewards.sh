#!/usr/bin/env bash
# Aggregate and report per-agent and per-skill rewards.

aggregate_eval_agent_rewards() {
  local skill="$1"
  local dest="$2"
  python3 - "$skill" "$dest" "${EVAL_AGENT_LIST[@]}" <<'PY'
from __future__ import annotations
import json
import sys
from pathlib import Path

skill = sys.argv[1]
dest = Path(sys.argv[2])
agents = sys.argv[3:]
verifier = Path("/logs/verifier")

def load(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}

def reward_of(path: Path) -> float:
    try:
        return float(load(path).get("reward", 0))
    except (TypeError, ValueError):
        return 0.0

def is_ratelimit(path: Path) -> bool:
    payload = load(path)
    if payload.get("ratelimit") is True:
        return True
    return str(payload.get("error") or "").lower() in {"ratelimit", "rate_limit"}

def bits(details: dict) -> tuple[str, str]:
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

per_agent = []
rewards = []
ratelimited = False
for agent in agents:
    path = verifier / f"reward-{skill}-{agent}.json"
    limited = is_ratelimit(path)
    ratelimited = ratelimited or limited
    reward = 0.0 if limited else reward_of(path)
    details = load(verifier / f"reward-{skill}-{agent}-details.json")
    raw, reasoning = bits(details)
    if limited:
        raw = "ratelimit"
        reasoning = reasoning or "failed due to ratelimit"
    if not raw:
        raw = "yes" if reward >= 1.0 else "no"
    per_agent.append({
        "agent": agent,
        "reward": reward,
        "raw": raw,
        "reasoning": reasoning,
        "ratelimit": limited,
        "details": details,
    })
    rewards.append(reward)
    print(
        f"Judge {skill}/{agent}: raw={raw} reward={reward} "
        f"reasoning={reasoning or '(none)'}",
        flush=True,
    )

overall = 0.0 if ratelimited else (
    1.0 if rewards and all(value >= 1.0 for value in rewards) else 0.0
)
skill_payload = {"reward": overall}
if ratelimited:
    skill_payload["ratelimit"] = True
    skill_payload["error"] = "ratelimit"
dest.write_text(json.dumps(skill_payload, indent=2) + "\n", encoding="utf-8")
details_dest = dest.parent / f"reward-{skill}-details.json"
payload = {
    "reward": {
        "aggregation": "all_pass",
        "overall": overall,
        "eval_agents": per_agent,
        "criteria": [{
            "name": skill,
            "reward": overall,
            "raw": "ratelimit" if ratelimited else ("yes" if overall >= 1.0 else "no"),
            "reasoning": "; ".join(
                f"{item['agent']}={item['raw']}" for item in per_agent
            ),
            "eval_agents": per_agent,
        }],
    }
}
details_dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(
    f"Judge {skill} aggregate evalAgents={','.join(agents)} reward={overall}",
    flush=True,
)
PY
}

read_skill_reward() {
  python3 - "$1" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file():
    print("0.0")
    raise SystemExit(0)
payload = json.loads(path.read_text(encoding="utf-8"))
print(float(payload.get("reward", 0)))
PY
}

print_skill_bits() {
  local skill="$1"
  python3 - "$skill" "/logs/verifier/reward-${skill}-details.json" <<'PY'
import json
import sys
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
        agents = reward.get("eval_agents")
        if not isinstance(agents, list) and criteria:
            agents = criteria[0].get("eval_agents")
        if isinstance(agents, list):
            for item in agents:
                if isinstance(item, dict):
                    print(
                        f"Judge {skill}/{item.get('agent')}: "
                        f"raw={item.get('raw') or '?'} "
                        f"reasoning={item.get('reasoning') or '(none)'}",
                        flush=True,
                    )
print(f"Judge {skill}: raw={raw or '?'} reasoning={reasoning or '(none)'}", flush=True)
PY
}

write_overall_reward() {
  local -n names_ref="$1"
  local -n rewards_ref="$2"
  python3 - <<'PY' /logs/verifier "${names_ref[@]}" -- "${rewards_ref[@]}"
from __future__ import annotations
import json
import sys
from pathlib import Path

def extract_bits(details: dict) -> tuple[str, str]:
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
rewards = [float(value) for value in args[sep + 1:]]
criteria = []
for name, reward in zip(names, rewards, strict=True):
    details_path = out_dir / f"reward-{name}-details.json"
    details = {}
    if details_path.is_file():
        try:
            details = json.loads(details_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            details = {}
    raw, reasoning = extract_bits(details)
    if not raw:
        raw = "yes" if reward >= 1.0 else "no"
    criteria.append({
        "name": name,
        "reward": reward,
        "raw": raw,
        "reasoning": reasoning,
        "details": details,
    })

overall = 1.0 if rewards and all(value >= 1.0 for value in rewards) else 0.0
ratelimited = False
for name in names:
    skill_path = out_dir / f"reward-{name}.json"
    if skill_path.is_file():
        try:
            skill_payload = json.loads(skill_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            skill_payload = {}
        if isinstance(skill_payload, dict) and skill_payload.get("ratelimit") is True:
            ratelimited = True
if ratelimited:
    overall = 0.0
reward_payload = {"reward": overall}
if ratelimited:
    reward_payload["ratelimit"] = True
    reward_payload["error"] = "ratelimit"
(out_dir / "reward.json").write_text(
    json.dumps(reward_payload, indent=2) + "\n", encoding="utf-8"
)
(out_dir / "reward-details.json").write_text(
    json.dumps({
        "reward": {
            "aggregation": "all_pass",
            "overall": overall,
            "criteria": criteria,
        }
    }, indent=2) + "\n",
    encoding="utf-8",
)
print(f"Aggregate reward={overall} across skills: {', '.join(names)}", flush=True)
for item in criteria:
    print(
        f"  {item['name']}: raw={item['raw']} reward={item['reward']} "
        f"reasoning={item.get('reasoning') or '(none)'}",
        flush=True,
    )
PY
}

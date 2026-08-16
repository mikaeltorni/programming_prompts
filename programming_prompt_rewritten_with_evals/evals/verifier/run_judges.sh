#!/usr/bin/env bash
# Canonical Harbor verifier for all coding tasks.
# Synced into tasks/*/tests/run_judges.sh by sync_judges.sh; task test.sh execs it.
# Each skill keeps its own prompt at evals/judges/<skill>/prompt.md.
#
# LLM judges run once per eval agent. Harbor --ve sets:
#   EVAL_AGENTS=codex            (default when unset — same as historical Codex)
#   EVAL_AGENTS=cc,codex,grok    (score the same workspace two/three times)
#   EVAL_AGENT_MODELS=...        (one value, or one per agent)
#   EVAL_AGENT_REASONING_EFFORT=low|medium|high  (same zip rules)
# Programmatic judges (worktree) run once and ignore evalAgent.
set -euo pipefail

mkdir -p /logs/verifier

HERE="$(cd "$(dirname "$0")" && pwd)"
GROK_HELPER="$HERE/run_grok_judge.py"

csv_trim_lower() {
  local raw="${1:-}"
  local IFS=','
  local -a parts=()
  local part
  read -r -a parts <<<"$raw"
  local -a out=()
  for part in "${parts[@]}"; do
    part="$(echo "$part" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
    [[ -n "$part" ]] && out+=("$part")
  done
  (IFS=','; printf '%s' "${out[*]}")
}

default_eval_model() {
  case "$1" in
    cc) printf '%s' "claude-opus-5" ;;
    grok) printf '%s' "grok-4.6" ;;
    *) printf '%s' "gpt-5.6-luna" ;;
  esac
}

rewardkit_backend() {
  case "$1" in
    cc) printf '%s' "claude-code" ;;
    grok) printf '%s' "grok" ;;
    *) printf '%s' "codex" ;;
  esac
}

EVAL_AGENTS_CSV="$(csv_trim_lower "${EVAL_AGENTS:-codex}")"
if [[ -z "$EVAL_AGENTS_CSV" ]]; then
  EVAL_AGENTS_CSV="codex"
fi
IFS=',' read -r -a EVAL_AGENT_LIST <<<"$EVAL_AGENTS_CSV"
echo "Eval agent(s): ${EVAL_AGENT_LIST[*]}" >&2

MODELS_CSV="${EVAL_AGENT_MODELS:-}"
EFFORTS_CSV="$(csv_trim_lower "${EVAL_AGENT_REASONING_EFFORT:-}")"
declare -a EVAL_MODELS=()
declare -a EVAL_EFFORTS=()
agent_count="${#EVAL_AGENT_LIST[@]}"
if [[ -z "$MODELS_CSV" ]]; then
  local_agent=""
  for local_agent in "${EVAL_AGENT_LIST[@]}"; do
    EVAL_MODELS+=("$(default_eval_model "$local_agent")")
  done
else
  IFS=',' read -r -a _model_parts <<<"$MODELS_CSV"
  declare -a _models_trim=()
  _m=""
  for _m in "${_model_parts[@]}"; do
    _m="$(echo "$_m" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -n "$_m" ]] && _models_trim+=("$_m")
  done
  if [[ "${#_models_trim[@]}" -eq 1 ]]; then
    idx=0
    for ((idx = 0; idx < agent_count; idx++)); do
      EVAL_MODELS+=("${_models_trim[0]}")
    done
  elif [[ "${#_models_trim[@]}" -eq "$agent_count" ]]; then
    EVAL_MODELS=("${_models_trim[@]}")
  else
    echo "EVAL_AGENT_MODELS has ${#_models_trim[@]} value(s) but EVAL_AGENTS has $agent_count" >&2
    exit 1
  fi
fi
if [[ -z "$EFFORTS_CSV" ]]; then
  idx=0
  for ((idx = 0; idx < agent_count; idx++)); do
    EVAL_EFFORTS+=("low")
  done
else
  IFS=',' read -r -a _effort_parts <<<"$EFFORTS_CSV"
  declare -a _efforts_trim=()
  _e=""
  for _e in "${_effort_parts[@]}"; do
    _e="$(echo "$_e" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
    [[ -n "$_e" ]] && _efforts_trim+=("$_e")
  done
  if [[ "${#_efforts_trim[@]}" -eq 1 ]]; then
    idx=0
    for ((idx = 0; idx < agent_count; idx++)); do
      EVAL_EFFORTS+=("${_efforts_trim[0]}")
    done
  elif [[ "${#_efforts_trim[@]}" -eq "$agent_count" ]]; then
    EVAL_EFFORTS=("${_efforts_trim[@]}")
  else
    echo "EVAL_AGENT_REASONING_EFFORT has ${#_efforts_trim[@]} value(s) but EVAL_AGENTS has $agent_count" >&2
    exit 1
  fi
fi
echo "Eval agent models: ${EVAL_MODELS[*]}" >&2
echo "Eval agent reasoning effort: ${EVAL_EFFORTS[*]}" >&2

needs_codex=0
needs_cc=0
needs_grok=0
for _agent in "${EVAL_AGENT_LIST[@]}"; do
  case "$_agent" in
    cc) needs_cc=1 ;;
    grok) needs_grok=1 ;;
    *) needs_codex=1 ;;
  esac
done

has_llm_judge=0
if [[ -d /tests/judges ]]; then
  for judge_dir in /tests/judges/*; do
    [[ -d "$judge_dir" && -f "$judge_dir/judge.toml" ]] || continue
    if grep -qE '^judge[[:space:]]*=[[:space:]]*"programmatic"' "$judge_dir/judge.toml"; then
      continue
    fi
    has_llm_judge=1
    break
  done
fi

codex_auth_source=""
find_codex_auth() {
  local candidate
  for candidate in \
      "${CODEX_HOME:-}/auth.json" \
      /tmp/codex-home/auth.json \
      "${HOME}/.codex/auth.json"
  do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      codex_auth_source="$candidate"
      return 0
    fi
  done
  return 1
}

if [[ "$has_llm_judge" -eq 1 && "$needs_codex" -eq 1 ]]; then
  if ! find_codex_auth; then
    echo "Codex authentication is required for the Codex eval agent." >&2
    exit 1
  fi
fi
if [[ "$has_llm_judge" -eq 1 && "$needs_cc" -eq 1 ]]; then
  if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && ! -f "${HOME}/.claude/.credentials.json" ]]; then
    echo "Claude Code eval agent needs CLAUDE_CODE_OAUTH_TOKEN or ~/.claude/.credentials.json" >&2
    exit 1
  fi
fi
if [[ "$has_llm_judge" -eq 1 && "$needs_grok" -eq 1 ]]; then
  if [[ -z "${XAI_API_KEY:-}" && ! -f "${HOME}/.grok/auth.json" ]]; then
    echo "Grok eval agent needs XAI_API_KEY or ~/.grok/auth.json" >&2
    exit 1
  fi
  if [[ ! -f "$GROK_HELPER" ]]; then
    echo "Missing Grok judge helper: $GROK_HELPER" >&2
    exit 1
  fi
  if ! command -v grok >/dev/null 2>&1; then
    echo "Grok eval agent needs the grok CLI on PATH" >&2
    exit 1
  fi
fi

setup_codex_home() {
  local effort="$1"
  local judge_home
  judge_home="$(mktemp -d)"
  if [[ -n "$codex_auth_source" && -f "$codex_auth_source" ]]; then
    install -m 600 "$codex_auth_source" "$judge_home/auth.json"
  fi
  printf '%s\n' \
      "model_reasoning_effort = \"${effort}\"" \
      'sandbox_mode = "danger-full-access"' \
      > "$judge_home/config.toml"
  printf '%s' "$judge_home"
}

# Writable Claude config for the judge. The trial bind-mounts
# /root/.claude/.credentials.json read-only; `claude -p` also writes sessions
# and may refresh that file, which is what produced is_error with 0 tokens.
setup_claude_home() {
  local judge_home cred_src="" candidate token=""
  judge_home="$(mktemp -d)"
  mkdir -p "$judge_home/debug" "$judge_home/projects" "$judge_home/skills"
  for candidate in \
      "${HOME}/.claude/.credentials.json" \
      /root/.claude/.credentials.json
  do
    if [[ -f "$candidate" ]]; then
      cred_src="$candidate"
      break
    fi
  done
  if [[ -n "$cred_src" ]]; then
    install -m 600 "$cred_src" "$judge_home/.credentials.json"
    echo "Claude eval agent: copied credentials.json into writable CLAUDE_CONFIG_DIR (value not logged)" >&2
  fi
  if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && -f "$judge_home/.credentials.json" ]]; then
    token="$(python3 - "$judge_home/.credentials.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(0)
oauth = data.get("claudeAiOauth") if isinstance(data, dict) else None
token = oauth.get("accessToken") if isinstance(oauth, dict) else None
if isinstance(token, str) and token.strip():
    sys.stdout.write(token.strip())
PY
)"
    if [[ -n "$token" ]]; then
      CLAUDE_CODE_OAUTH_TOKEN="$token"
      export CLAUDE_CODE_OAUTH_TOKEN
      echo "Claude eval agent: loaded CLAUDE_CODE_OAUTH_TOKEN from credentials.json (value not logged)" >&2
    fi
  fi
  if [[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" && ! -f "$judge_home/.credentials.json" ]]; then
    python3 - "$judge_home/.credentials.json" <<'PY'
import json
import os
import sys
from pathlib import Path

token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
path = Path(sys.argv[1])
path.write_text(
    json.dumps({"claudeAiOauth": {"accessToken": token}}) + "\n",
    encoding="utf-8",
)
path.chmod(0o600)
PY
    echo "Claude eval agent: wrote credentials.json from CLAUDE_CODE_OAUTH_TOKEN (value not logged)" >&2
  fi
  if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && ! -f "$judge_home/.credentials.json" ]]; then
    echo "Claude Code eval agent needs CLAUDE_CODE_OAUTH_TOKEN or ~/.claude/.credentials.json" >&2
    rm -rf "$judge_home"
    return 1
  fi
  if [[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]]; then
    umask 077
    printf '%s' "$CLAUDE_CODE_OAUTH_TOKEN" >"$judge_home/oauth_token"
  fi
  echo "Claude eval agent: CLAUDE_CONFIG_DIR=${judge_home} token_set=$([[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]] && echo yes || echo no) credentials=$([[ -f "$judge_home/.credentials.json" ]] && echo yes || echo no)" >&2
  printf '%s' "$judge_home"
}

# Inject --effort and bypassPermissions for Claude -p judge calls without
# breaking `claude --version`.
with_claude_effort() {
  local effort="$1"
  shift
  local real wrapper_dir
  real="$(command -v claude)"
  if [[ -z "$real" ]]; then
    echo "claude CLI not found on PATH for the Claude Code eval agent" >&2
    return 1
  fi
  wrapper_dir="$(mktemp -d)"
  cat >"$wrapper_dir/claude" <<EOF
#!/usr/bin/env bash
set -euo pipefail
real=$(printf '%q' "$real")
effort=$(printf '%q' "$effort")
for arg in "\$@"; do
  if [[ "\$arg" == "-p" || "\$arg" == "--print" ]]; then
    exec "\$real" --effort "\$effort" --permission-mode bypassPermissions "\$@"
  fi
done
exec "\$real" "\$@"
EOF
  chmod 755 "$wrapper_dir/claude"
  PATH="$wrapper_dir:$PATH" "$@"
  local rc=$?
  rm -rf "$wrapper_dir"
  return "$rc"
}

stash_rewardkit_details() {
  local dest="$1"
  if [[ -f /logs/verifier/reward-details.json ]]; then
    cp /logs/verifier/reward-details.json "$dest"
  fi
}

run_llm_eval_agent() {
  local judge_dir="$1"
  local output_json="$2"
  local eval_agent="$3"
  local model="$4"
  local effort="$5"
  local backend work
  backend="$(rewardkit_backend "$eval_agent")"
  echo "Running $eval_agent eval agent (backend=$backend model=$model effort=$effort)" >&2
  if [[ "$eval_agent" == "grok" ]]; then
    python3 "$GROK_HELPER" \
      --judge-dir "$judge_dir" \
      --output "$output_json" \
      --workspace /Projects/app \
      --model "$model" \
      --reasoning-effort "$effort"
    return 0
  fi
  work="$(mktemp -d)"
  local prompt_file=""
  local candidate
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
  if [[ "$(basename "$prompt_file")" != "prompt.md" ]]; then
    cp "$prompt_file" "$work/prompt.md"
  fi
  if [[ "$eval_agent" == "cc" ]]; then
    local judge_home
    judge_home="$(setup_claude_home)" || return 1
    if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && -f "$judge_home/oauth_token" ]]; then
      CLAUDE_CODE_OAUTH_TOKEN="$(cat "$judge_home/oauth_token")"
      export CLAUDE_CODE_OAUTH_TOKEN
    fi
    local -a claude_env=(
      "CLAUDE_FORCE_OAUTH=true"
      "REWARDKIT_FORCE_OAUTH=true"
      "CLAUDE_CONFIG_DIR=$judge_home"
      "IS_SANDBOX=1"
      "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
    )
    if [[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]]; then
      claude_env+=("CLAUDE_CODE_OAUTH_TOKEN=${CLAUDE_CODE_OAUTH_TOKEN}")
    fi
    with_claude_effort "$effort" \
      env "${claude_env[@]}" \
      uvx --from harbor-rewardkit@0.1.7 \
        rewardkit "$work" \
        --workspace /Projects/app \
        --output "$output_json" \
        --judge "$backend" \
        --model "$model"
    rm -rf "$judge_home"
  else
    local judge_home
    judge_home="$(setup_codex_home "$effort")"
    CODEX_HOME="$judge_home" \
      uvx --from harbor-rewardkit@0.1.7 \
        rewardkit "$work" \
        --workspace /Projects/app \
        --output "$output_json" \
        --judge "$backend" \
        --model "$model"
    rm -rf "$judge_home"
  fi
  rm -rf "$work"
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
    payload = load(path)
    try:
        return float(payload.get("reward", 0))
    except (TypeError, ValueError):
        return 0.0

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
for agent in agents:
    reward_path = verifier / f"reward-{skill}-{agent}.json"
    details_path = verifier / f"reward-{skill}-{agent}-details.json"
    reward = reward_of(reward_path)
    details = load(details_path)
    raw, reasoning = bits(details)
    if not raw:
        raw = "yes" if reward >= 1.0 else "no"
    per_agent.append(
        {
            "agent": agent,
            "reward": reward,
            "raw": raw,
            "reasoning": reasoning,
            "details": details,
        }
    )
    rewards.append(reward)
    print(
        f"Judge {skill}/{agent}: raw={raw} reward={reward} "
        f"reasoning={reasoning or '(none)'}",
        flush=True,
    )

overall = 1.0 if rewards and all(value >= 1.0 for value in rewards) else 0.0
dest.write_text(json.dumps({"reward": overall}, indent=2) + "\n", encoding="utf-8")
details_dest = dest.parent / f"reward-{skill}-details.json"
payload = {
    "reward": {
        "aggregation": "all_pass",
        "overall": overall,
        "eval_agents": per_agent,
        "criteria": [
            {
                "name": skill,
                "reward": overall,
                "raw": "yes" if overall >= 1.0 else "no",
                "reasoning": "; ".join(
                    f"{item['agent']}={item['raw']}" for item in per_agent
                ),
                "eval_agents": per_agent,
            }
        ],
    }
}
details_dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(
    f"Judge {skill} aggregate evalAgents={','.join(agents)} reward={overall}",
    flush=True,
)
PY
}

run_one_judge() {
    local judge_dir="$1"
    local output_json="$2"
    local skill
    skill="$(basename "$judge_dir")"
    if [[ -f "$judge_dir/judge.toml" ]] && grep -qE '^judge[[:space:]]*=[[:space:]]*"programmatic"' "$judge_dir/judge.toml"; then
        echo "Running programmatic judge for skill: $skill" >&2
        run_programmatic_judge "$output_json"
        return 0
    fi
    local idx agent model effort agent_out
    for idx in "${!EVAL_AGENT_LIST[@]}"; do
        agent="${EVAL_AGENT_LIST[$idx]}"
        model="${EVAL_MODELS[$idx]}"
        effort="${EVAL_EFFORTS[$idx]}"
        agent_out="/logs/verifier/reward-${skill}-${agent}.json"
        echo "Running judge for skill=$skill evalAgent=$agent" >&2
        run_llm_eval_agent "$judge_dir" "$agent_out" "$agent" "$model" "$effort"
        stash_rewardkit_details "/logs/verifier/reward-${skill}-${agent}-details.json"
    done
    aggregate_eval_agent_rewards "$skill" "$output_json"
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
        agents = reward.get("eval_agents")
        if not isinstance(agents, list) and criteria:
            agents = criteria[0].get("eval_agents")
        if isinstance(agents, list):
            for item in agents:
                if not isinstance(item, dict):
                    continue
                print(
                    f"Judge {skill}/{item.get('agent')}: "
                    f"raw={item.get('raw') or '?'} "
                    f"reasoning={item.get('reasoning') or '(none)'}",
                    flush=True,
                )
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

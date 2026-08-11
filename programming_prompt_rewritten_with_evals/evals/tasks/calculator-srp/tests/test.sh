#!/usr/bin/env bash
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

CODEX_HOME="$judge_home" uvx --from harbor-rewardkit@0.1.7 \
    rewardkit /tests \
    --workspace /app \
    --output /logs/verifier/reward.json

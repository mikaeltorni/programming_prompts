#!/usr/bin/env bash
# Detect configured judge types and validate their authentication prerequisites.

find_codex_auth() {
  local candidate
  for candidate in \
      "${CODEX_HOME:-}/auth.json" \
      /tmp/codex-home/auth.json \
      "${HOME}/.codex/auth.json"
  do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      CODEX_AUTH_SOURCE="$candidate"
      return 0
    fi
  done
  return 1
}

detect_judge_requirements() {
  NEEDS_CODEX=0
  NEEDS_CC=0
  NEEDS_GROK=0
  local agent judge_dir
  for agent in "${EVAL_AGENT_LIST[@]}"; do
    case "$agent" in
      cc) NEEDS_CC=1 ;;
      grok) NEEDS_GROK=1 ;;
      *) NEEDS_CODEX=1 ;;
    esac
  done

  HAS_LLM_JUDGE=0
  if [[ -d /tests/judges ]]; then
    for judge_dir in /tests/judges/*; do
      [[ -d "$judge_dir" && -f "$judge_dir/judge.toml" ]] || continue
      if grep -qE '^judge[[:space:]]*=[[:space:]]*"programmatic"' "$judge_dir/judge.toml"; then
        continue
      fi
      HAS_LLM_JUDGE=1
      break
    done
  fi
}

preflight_judges() {
  if [[ ! -f "$JUDGE_POOL" ]]; then
    echo "Missing judge pool: $JUDGE_POOL" >&2
    return 1
  fi
  if [[ "$HAS_LLM_JUDGE" -eq 1 && ! -f "$LLM_HELPER" ]]; then
    echo "Missing LLM judge helper: $LLM_HELPER" >&2
    return 1
  fi
  if [[ "$HAS_LLM_JUDGE" -eq 1 && "$NEEDS_CODEX" -eq 1 ]] && ! find_codex_auth; then
    echo "Codex authentication is required for the Codex eval agent." >&2
    return 1
  fi
  if [[ "$HAS_LLM_JUDGE" -eq 1 && "$NEEDS_CC" -eq 1 ]]; then
    if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && ! -f "${HOME}/.claude/.credentials.json" ]]; then
      echo "Claude Code eval agent needs CLAUDE_CODE_OAUTH_TOKEN or ~/.claude/.credentials.json" >&2
      return 1
    fi
  fi
  if [[ "$HAS_LLM_JUDGE" -eq 1 && "$NEEDS_GROK" -eq 1 ]]; then
    if [[ -z "${XAI_API_KEY:-}" && ! -f "${HOME}/.grok/auth.json" ]]; then
      echo "Grok eval agent needs XAI_API_KEY or ~/.grok/auth.json" >&2
      return 1
    fi
    if ! command -v grok >/dev/null 2>&1; then
      echo "Grok eval agent needs the grok CLI on PATH" >&2
      return 1
    fi
  fi
}

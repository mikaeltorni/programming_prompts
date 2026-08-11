#!/usr/bin/env bash
# Shared helpers for launching result-verification agents in a new terminal.
# shellcheck shell=bash

# lib/ -> testing/ -> evals/ -> programming_prompt_rewritten_with_evals/ -> repo root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SKILLS_ROOT="$REPO_ROOT/programming_prompt_rewritten_with_evals/prompts/programming-skills"
JUDGES_ROOT="$REPO_ROOT/programming_prompt_rewritten_with_evals/evals/judges"

build_verify_prompt() {
  local positive_dir="$1"
  local baseline_dir="$2"
  cat <<EOF
Verify the Harbor SRP+commenting eval results at these exact paths:

POSITIVE (with skills):
${positive_dir}/
  - ${positive_dir}/codex-srp/          (or codex-* skill job dirs)
  - ${positive_dir}/codex-commenting/

BASELINE (no skills):
${baseline_dir}/
  - ${baseline_dir}/codex-baseline-srp/
  - ${baseline_dir}/codex-baseline-commenting/

Skill definitions (must follow exactly):
- ${SKILLS_ROOT}/srp/SKILL.md
- ${SKILLS_ROOT}/commenting/SKILL.md

Judge prompts (scoring rules):
- ${JUDGES_ROOT}/srp/prompt.md
- ${JUDGES_ROOT}/commenting/prompt.md

For every trial under those job dirs:
1. Read artifacts/app/*.py and verifier/reward.json (+ reward-details.json / reward-*.json).
2. Check line-by-line that positive code follows BOTH skills for sure (SRP: parse helper + separate core-logic helper + thin entrypoint; commenting: every function docstring has description + Parameters: + Returns: exactly).
3. Confirm the judge verdict matches that structure (positive should be yes/1.0; baseline should be no/0.0).
4. Confirm baseline code does NOT follow the skills for sure (monolithic entrypoint and/or missing Parameters:/Returns:).
5. Report any false positives or false negatives with exact file paths. End with pass totals and whether the claimed scores are trustworthy.
EOF
}

open_new_terminal() {
  local title="$1"
  local command="$2"
  local wrapped
  wrapped=$(printf 'echo %q; echo; %s; echo; read -r -p %q' \
    "=== $title ===" \
    "$command" \
    "Press Enter to close this window...")

  if command -v gnome-terminal >/dev/null 2>&1; then
    echo "Opening new gnome-terminal window: $title" >&2
    gnome-terminal --title="$title" -- bash -lc "$wrapped"
    return 0
  fi
  if command -v x-terminal-emulator >/dev/null 2>&1; then
    echo "Opening new x-terminal-emulator window: $title" >&2
    x-terminal-emulator -T "$title" -e bash -lc "$wrapped"
    return 0
  fi
  echo "No graphical terminal found (tried gnome-terminal, x-terminal-emulator)." >&2
  echo "Running in the current shell instead." >&2
  bash -lc "$command"
}

require_result_dirs() {
  local positive_dir="$1"
  local baseline_dir="$2"
  if [[ -z "$positive_dir" || -z "$baseline_dir" ]]; then
    echo "Usage: $0 <positive_jobs_tmp_dir> <baseline_jobs_tmp_dir>" >&2
    echo "Example: $0 /tmp/tmp.oyg9LZOYsa /tmp/tmp.39s2xmt8PJ" >&2
    return 2
  fi
  if [[ ! -d "$positive_dir" ]]; then
    echo "Positive results dir not found: $positive_dir" >&2
    return 1
  fi
  if [[ ! -d "$baseline_dir" ]]; then
    echo "Baseline results dir not found: $baseline_dir" >&2
    return 1
  fi
  return 0
}

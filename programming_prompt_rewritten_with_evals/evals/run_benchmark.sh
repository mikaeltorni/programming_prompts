#!/usr/bin/env bash
# Run rewritten-prompt Harbor jobs with clean, version-pinned coding agents.
#
# Each new instance looks up the newest stable CLI (npm latest for Codex and
# Claude Code, Grok stable channel) and installs that in the trial. Committed
# *-version.txt files are fallbacks when the registry is unreachable.
# Pass --no-pin-refresh (or HARNESS_PIN_REFRESH=0) to use only those pins.
# Lookups are tiny HTTP GETs — they do not call an LLM.
#
# Harnesses: Codex (`codex`), Claude Code (`cc`), and Grok CLI (`grok`).
# Omit --harness / harness= to run Codex and Claude Code. Defaults:
#   codex → openai/gpt-5.6-luna @ reasoning_effort=low
#   cc    → claude-opus-5       @ reasoning_effort=low (Claude CLI --effort)
#   grok  → grok-4.6            @ reasoning_effort=low (Grok CLI --reasoning-effort)
#
# Harness aliases, models, mounts, and pin files live in
# harbor_agents/harness_spec.py — do not add another case ladder here.
#
# Edit surfaces:
#   ../prompts/programming-skills/<skill>/SKILL.md
#   judges/<skill>/prompt.md
#   coding-prompts/<task>.md
#
# Usage (from this directory):
#   ./run_benchmark.sh
#   ./run_benchmark.sh harness=codex
#   ./run_benchmark.sh harness=cc
#   ./run_benchmark.sh harness=grok
#   ./run_benchmark.sh --harness both --skills srp,commenting --run-separately -k 5 -n 5
#   ./run_benchmark.sh --baseline --skills srp,commenting -k 5 -n 5
#   ./run_benchmark.sh --skills srp,logging -k 2 -n 2
#   ./run_benchmark.sh --skills srp,worktree -k 2 -n 2
#   ./run_benchmark.sh --install-only harness=grok
#   ./run_benchmark.sh --no-pin-refresh --install-only harness=codex
#   ./run_benchmark.sh harness=codex evalAgent=cc,codex
#   ./run_benchmark.sh harness=cc evalAgent=grok evalAgentModel=grok-4.6 \
#       evalAgentReasoningEffort=low
#
# Trial count (rule of thumb): harnesses × (skills if --run-separately else 1)
# × tasks × -k. Example: both harnesses, 2 skills separately, 5 tasks, -k 5
# → 2 × 2 × 5 × 5 = 100 trials. evalAgent does not multiply trials; it reruns
# the LLM judge on each trial (2–3× verifier cost when several agents, same
# wall clock — judges run concurrently unless EVAL_JUDGE_WORKERS caps them).
#
# Parallel terminals: each Harbor trial creates a Docker network. Docker's
# default IPAM only has ~30 user-defined /16 slots, so a dozen -n 5 jobs
# crash with "all predefined address pools have been fully subnetted".
# docker_networks.py prunes leftover Harbor nets and holds a cross-process
# slot lock so extra jobs wait instead of exhausting IPAM.
# --run-separately used to start the next skill only after the previous
# skill's 25 trials finished (easy to mistake for a mysterious second run).
# Skill jobs now fan out in parallel, each -n fair-shared across free IPAM
# slots. Combined mode is still one Harbor job for all selected skills.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
ORIGINAL_ARGV=("$@")

CODEX_VERSION_FILE="$SCRIPT_DIR/codex-version.txt"
CLAUDE_VERSION_FILE="$SCRIPT_DIR/claude-version.txt"
GROK_VERSION_FILE="$SCRIPT_DIR/grok-version.txt"
if [[ ! -f "$CODEX_VERSION_FILE" ]]; then
  echo "Missing Codex version pin: $CODEX_VERSION_FILE" >&2
  exit 1
fi
if [[ ! -f "$CLAUDE_VERSION_FILE" ]]; then
  echo "Missing Claude Code version pin: $CLAUDE_VERSION_FILE" >&2
  exit 1
fi
if [[ ! -f "$GROK_VERSION_FILE" ]]; then
  echo "Missing Grok CLI version pin: $GROK_VERSION_FILE" >&2
  exit 1
fi
CODEX_VERSION="$(tr -d '[:space:]' <"$CODEX_VERSION_FILE")"
CLAUDE_VERSION="$(tr -d '[:space:]' <"$CLAUDE_VERSION_FILE")"
GROK_VERSION="$(tr -d '[:space:]' <"$GROK_VERSION_FILE")"
if [[ -z "$CODEX_VERSION" ]]; then
  echo "Empty Codex version pin: $CODEX_VERSION_FILE" >&2
  exit 1
fi
if [[ -z "$CLAUDE_VERSION" ]]; then
  echo "Empty Claude Code version pin: $CLAUDE_VERSION_FILE" >&2
  exit 1
fi
if [[ -z "$GROK_VERSION" ]]; then
  echo "Empty Grok CLI version pin: $GROK_VERSION_FILE" >&2
  exit 1
fi

export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"
HARNESS_SPEC="$SCRIPT_DIR/harbor_agents/harness_spec.py"
REFRESH_VERSIONS="$SCRIPT_DIR/harbor_agents/refresh_versions.py"
DOCKER_NETWORKS="$SCRIPT_DIR/docker_networks.py"
_docker_slot_holder=""

# Harbor output stays inside the run archive (evals/runs/<stamp>/harbor).
# Export JOBS=... only to override that; the default is no longer /tmp.
JOBS_FROM_ENV="${JOBS:-}"
# Unique per invocation so a shared/reused $JOBS dir never collides on Harbor
# job names (FileExistsError) or archive dirname when terminals run in parallel.
RUN_STAMP="$(date +%Y-%m-%d_%H%M%S)_$$"
RUNS_ROOT="${RUNS_ROOT:-$SCRIPT_DIR/runs}"
SKILLS_ROOT="$SCRIPT_DIR/../prompts/programming-skills"
JUDGES_ROOT="$SCRIPT_DIR/judges"
CODING_PROMPTS_DIR="$SCRIPT_DIR/coding-prompts"
TASKS_DIR="$SCRIPT_DIR/.generated/tasks"

source "$SCRIPT_DIR/lib/docker_slots.sh"
source "$SCRIPT_DIR/lib/harness_cli.sh"
source "$SCRIPT_DIR/lib/skills_tasks.sh"
source "$SCRIPT_DIR/lib/auth_tokens.sh"
source "$SCRIPT_DIR/lib/job_config.sh"
source "$SCRIPT_DIR/lib/prepare_tasks.sh"
source "$SCRIPT_DIR/lib/archive_run.sh"
source "$SCRIPT_DIR/lib/harbor_invoke.sh"
source "$SCRIPT_DIR/lib/run_jobs.sh"
source "$SCRIPT_DIR/lib/separately_jobs.sh"
trap on_eval_shell_exit EXIT

echo "Committed CLI fallbacks: Codex $CODEX_VERSION | Claude Code $CLAUDE_VERSION | Grok $GROK_VERSION" >&2
echo "Run stamp: $RUN_STAMP" >&2
echo "PYTHONPATH includes: $SCRIPT_DIR" >&2

INSTALL_ONLY=0
PIN_REFRESH=1
BASELINE=0
RUN_SEPARATELY=0
SKILLS_ARG=""
TASKS_ARG=""
HARNESS_ARG=""
EVAL_AGENT_ARG=""
EVAL_AGENT_MODEL_ARG=""
EVAL_AGENT_EFFORT_ARG=""
HARBOR_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-only)
      INSTALL_ONLY=1
      shift
      ;;
    --no-pin-refresh|--offline-pins)
      PIN_REFRESH=0
      shift
      ;;
    --pin-refresh)
      PIN_REFRESH=1
      shift
      ;;
    --baseline|--no-skill)
      BASELINE=1
      shift
      ;;
    --negative|--oneshot|--anti-srp)
      echo "Unknown option $1 (inverted-skill mode was removed; use --baseline for no-skill runs)" >&2
      exit 1
      ;;
    --run-separately|--runSeparately)
      RUN_SEPARATELY=1
      shift
      ;;
    --harness)
      HARNESS_ARG="${2:-}"
      if [[ -z "$HARNESS_ARG" ]]; then
        echo "--harness requires a value: $(python3 "$HARNESS_SPEC" choices)" >&2
        exit 1
      fi
      shift 2
      ;;
    --harness=*)
      HARNESS_ARG="${1#--harness=}"
      shift
      ;;
    harness=*)
      HARNESS_ARG="${1#harness=}"
      shift
      ;;
    --evalAgent|--eval-agent)
      EVAL_AGENT_ARG="${2:-}"
      if [[ -z "$EVAL_AGENT_ARG" ]]; then
        echo "--evalAgent requires a value: $(python3 "$HARNESS_SPEC" choices)" >&2
        exit 1
      fi
      shift 2
      ;;
    --evalAgent=*|--eval-agent=*)
      EVAL_AGENT_ARG="${1#*=}"
      shift
      ;;
    evalAgent=*|eval-agent=*)
      EVAL_AGENT_ARG="${1#*=}"
      shift
      ;;
    --evalAgentModel|--eval-agent-model)
      EVAL_AGENT_MODEL_ARG="${2:-}"
      if [[ -z "$EVAL_AGENT_MODEL_ARG" ]]; then
        echo "--evalAgentModel requires a model id (same idea as -m / --model)" >&2
        exit 1
      fi
      shift 2
      ;;
    --evalAgentModel=*|--eval-agent-model=*)
      EVAL_AGENT_MODEL_ARG="${1#*=}"
      shift
      ;;
    evalAgentModel=*|eval-agent-model=*)
      EVAL_AGENT_MODEL_ARG="${1#*=}"
      shift
      ;;
    --evalAgentReasoningEffort|--eval-agent-reasoning-effort)
      EVAL_AGENT_EFFORT_ARG="${2:-}"
      if [[ -z "$EVAL_AGENT_EFFORT_ARG" ]]; then
        echo "--evalAgentReasoningEffort requires low, medium, or high (same as --ak reasoning_effort=)" >&2
        exit 1
      fi
      shift 2
      ;;
    --evalAgentReasoningEffort=*|--eval-agent-reasoning-effort=*)
      EVAL_AGENT_EFFORT_ARG="${1#*=}"
      shift
      ;;
    evalAgentReasoningEffort=*|eval-agent-reasoning-effort=*)
      EVAL_AGENT_EFFORT_ARG="${1#*=}"
      shift
      ;;
    --skills)
      SKILLS_ARG="${2:-}"
      if [[ -z "$SKILLS_ARG" ]]; then
        echo "--skills requires a value like srp,commenting" >&2
        exit 1
      fi
      shift 2
      ;;
    --skills=*)
      SKILLS_ARG="${1#--skills=}"
      shift
      ;;
    -skills=*)
      SKILLS_ARG="${1#-skills=}"
      shift
      ;;
    --tasks|--task)
      TASKS_ARG="${2:-}"
      if [[ -z "$TASKS_ARG" ]]; then
        echo "--tasks requires a value like todo,calculator" >&2
        exit 1
      fi
      shift 2
      ;;
    --tasks=*|--task=*)
      TASKS_ARG="${1#*=}"
      shift
      ;;
    -tasks=*|-task=*)
      TASKS_ARG="${1#*=}"
      shift
      ;;
    tasks=*|task=*)
      TASKS_ARG="${1#*=}"
      shift
      ;;
    --)
      shift
      HARBOR_ARGS+=("$@")
      break
      ;;
    *)
      HARBOR_ARGS+=("$1")
      shift
      ;;
  esac
done

_norm_out="$(normalize_harness "$HARNESS_ARG")" || exit 1
mapfile -t SELECTED_HARNESSES <<< "$_norm_out"
unset _norm_out
echo "Selected harness(es): ${SELECTED_HARNESSES[*]}" >&2

# Empty evalAgent → inherit the coding harness for each job. Explicit values
# use the same aliases/groups as harness= (comma lists, both, all).
_eval_out="$(python3 "$HARNESS_SPEC" eval-agents "$EVAL_AGENT_ARG")" || exit 1
SELECTED_EVAL_AGENTS=()
if [[ -n "$_eval_out" ]]; then
  mapfile -t SELECTED_EVAL_AGENTS <<< "$_eval_out"
fi
unset _eval_out
if [[ ${#SELECTED_EVAL_AGENTS[@]} -eq 0 ]]; then
  echo "Eval agent: inherit coding harness (same CLI as harness=)" >&2
else
  echo "Eval agent(s): ${SELECTED_EVAL_AGENTS[*]}" >&2
fi
if [[ -n "$EVAL_AGENT_MODEL_ARG" ]]; then
  echo "Eval agent model override: $EVAL_AGENT_MODEL_ARG" >&2
fi
if [[ -n "$EVAL_AGENT_EFFORT_ARG" ]]; then
  echo "Eval agent reasoning effort override: $EVAL_AGENT_EFFORT_ARG" >&2
fi
# Fail fast on zip/length/effort errors before Harbor starts.
if [[ ${#SELECTED_EVAL_AGENTS[@]} -gt 0 ]]; then
  _eval_csv="$(IFS=','; printf '%s' "${SELECTED_EVAL_AGENTS[*]}")"
  python3 "$HARNESS_SPEC" eval-models "$_eval_csv" "$EVAL_AGENT_MODEL_ARG" >/dev/null || exit 1
  python3 "$HARNESS_SPEC" eval-efforts "$_eval_csv" "$EVAL_AGENT_EFFORT_ARG" >/dev/null || exit 1
  unset _eval_csv
else
  for _h in "${SELECTED_HARNESSES[@]}"; do
    python3 "$HARNESS_SPEC" eval-models "$_h" "$EVAL_AGENT_MODEL_ARG" >/dev/null || exit 1
    python3 "$HARNESS_SPEC" eval-efforts "$_h" "$EVAL_AGENT_EFFORT_ARG" >/dev/null || exit 1
  done
  unset _h
fi

# Look up newest stable CLIs for this instance (tiny registry GETs, no LLM).
if [[ "$PIN_REFRESH" -eq 0 ]]; then
  python3 "$REFRESH_VERSIONS" --offline >&2
else
  python3 "$REFRESH_VERSIONS" >&2
fi
CODEX_VERSION="$(python3 "$HARNESS_SPEC" version codex)"
CLAUDE_VERSION="$(python3 "$HARNESS_SPEC" version cc)"
GROK_VERSION="$(python3 "$HARNESS_SPEC" version grok)"
echo "Instance CLI versions: Codex $CODEX_VERSION | Claude Code $CLAUDE_VERSION | Grok $GROK_VERSION" >&2

mapfile -t SELECTED_SKILLS < <(resolve_skills "$SKILLS_ARG")
echo "Selected skill(s): ${SELECTED_SKILLS[*]}" >&2

mapfile -t SELECTED_TASKS < <(resolve_tasks "$TASKS_ARG")
echo "Selected coding task(s): ${SELECTED_TASKS[*]}" >&2

# --- install-only path uses a minimal generated config ---
if [[ "$INSTALL_ONLY" -eq 1 ]]; then
  init_run_archive "install"
  SELECTED_SKILLS_FOR_JOB=("${SELECTED_SKILLS[@]}")
  "$SCRIPT_DIR/sync_tasks.sh"
  for install_harness in "${SELECTED_HARNESSES[@]}"; do
    install_version="$(harness_cli_version "$install_harness")"
    install_job_name="$(harbor_job_name "${install_harness}-install-$install_version")"
    install_tasks_root="$(prepare_job_tasks "$install_job_name" "${SELECTED_SKILLS[@]}")"
    collect_artifact_flags
    install_config="$JOBS/harbor.${install_job_name}.yaml"
    write_job_config "$install_harness" "$install_config" "$(skills_yaml_block "$SKILLS_ROOT/${SELECTED_SKILLS[0]}")" "$install_tasks_root"
    echo "Reinstalling/verifying $install_harness @$install_version inside the task environment" >&2
    acquire_docker_slots "${RUN_STAMP}:${install_job_name}" 1 >/dev/null
    run_harbor_for_harness "$install_harness" \
      -c "$install_config" \
      -o "$JOBS" \
      "${ARTIFACT_FLAGS[@]}" \
      --install-only \
      --job-name "$install_job_name" \
      "${HARBOR_ARGS[@]}"
    release_docker_slots
  done
  exit 0
fi

"$SCRIPT_DIR/sync_tasks.sh"
TASK_COUNT="$(list_task_dirs | wc -l | tr -d ' ')"
echo "Discovered $TASK_COUNT coding task(s) under $TASKS_DIR" >&2

# Estimate total trials for the user.
SKILL_FACTOR=1
if [[ "$RUN_SEPARATELY" -eq 1 ]]; then
  SKILL_FACTOR=${#SELECTED_SKILLS[@]}
fi
HARNESS_FACTOR=${#SELECTED_HARNESSES[@]}

if [[ "$BASELINE" -eq 1 ]]; then
  RUN_MODE_LABEL="baseline"
else
  RUN_MODE_LABEL="positive"
fi
init_run_archive "$RUN_MODE_LABEL"

ESTIMATED_TRIALS=$((HARNESS_FACTOR * SKILL_FACTOR * TASK_COUNT * ATTEMPTS_PER_TASK))
echo "Estimated trials ≈ $ESTIMATED_TRIALS (= $HARNESS_FACTOR harness(es) × $SKILL_FACTOR skill-job(s) × $TASK_COUNT task(s) × $ATTEMPTS_PER_TASK attempts)." >&2

for HARNESS in "${SELECTED_HARNESSES[@]}"; do
  echo "======== harness=$HARNESS ========" >&2
  run_jobs_for_harness "$HARNESS"
done

if [[ ${#SELECTED_HARNESSES[@]} -gt 1 || "$RUN_SEPARATELY" -eq 1 ]]; then
  echo "Combined categorized summary across all jobs in $JOBS:" >&2
  if [[ "$BASELINE" -eq 1 ]]; then
    capture_print_summary "$JOBS" "baseline-all" "${SELECTED_SKILLS[*]}"
  else
    capture_print_summary "$JOBS" "positive-all" "${SELECTED_SKILLS[*]}"
  fi
fi
archive_finalize

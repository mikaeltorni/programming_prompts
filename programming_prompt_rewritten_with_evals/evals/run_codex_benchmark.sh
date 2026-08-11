#!/usr/bin/env bash
# Run rewritten-prompt Harbor jobs with a clean, version-pinned Codex agent.
#
# Usage (from this directory):
#   ./run_codex_benchmark.sh                 # 5x gpt-5.6-luna @ low + skill
#   ./run_codex_benchmark.sh --baseline      # same, but NO programming skill
#   ./run_codex_benchmark.sh --install-only  # reinstall/verify Codex pin only
#   ./run_codex_benchmark.sh -- -m openai/o3 --ak reasoning_effort=medium
#
# Default model/effort come from harbor.codex.yaml (openai/gpt-5.6-luna, low).
# With no Harbor flags, this wrapper runs -k 5 -n 5 (five concurrent attempts).
# --baseline switches to harbor.codex.baseline.yaml (skills: []) so you can
# measure baseline pass rate without the programming skill.
# The agent is BenchmarkCodex: fresh CODEX_HOME, wiped skill roots, and only
# the skills configured in the selected job config (or extra --skill flags).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION_FILE="$SCRIPT_DIR/codex-version.txt"
if [[ ! -f "$VERSION_FILE" ]]; then
  echo "Missing Codex version pin: $VERSION_FILE" >&2
  exit 1
fi
CODEX_VERSION="$(tr -d '[:space:]' <"$VERSION_FILE")"
if [[ -z "$CODEX_VERSION" ]]; then
  echo "Empty Codex version pin: $VERSION_FILE" >&2
  exit 1
fi

export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"

JOBS="${JOBS:-$(mktemp -d)}"
MOUNTS="${MOUNTS:-$(
  python3 -c 'import json, pathlib; print(json.dumps([{"type": "bind", "source": str(pathlib.Path.home() / ".codex" / "auth.json"), "target": "/root/.codex/auth.json", "read_only": True}]))'
)}"

echo "Codex benchmark pin: $CODEX_VERSION" >&2
echo "Jobs directory: $JOBS" >&2
echo "PYTHONPATH includes: $SCRIPT_DIR" >&2

INSTALL_ONLY=0
BASELINE=0
HARBOR_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-only)
      INSTALL_ONLY=1
      shift
      ;;
    --baseline|--no-skill)
      BASELINE=1
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

CONFIG_FILE="$SCRIPT_DIR/harbor.codex.yaml"
DEFAULT_JOB_NAME="codex-finnish"
if [[ "$BASELINE" -eq 1 ]]; then
  CONFIG_FILE="$SCRIPT_DIR/harbor.codex.baseline.yaml"
  DEFAULT_JOB_NAME="codex-baseline-no-skill"
  echo "Baseline mode: no programming skill injected" >&2
fi

COMMON=(
  -c "$CONFIG_FILE"
  --mounts "$MOUNTS"
  -o "$JOBS"
  --ak "version=$CODEX_VERSION"
)

if [[ "$INSTALL_ONLY" -eq 1 ]]; then
  echo "Reinstalling/verifying Codex @$CODEX_VERSION inside the task environment" >&2
  CODEX_FORCE_AUTH_JSON=1 harbor run "${COMMON[@]}" \
    --install-only \
    --job-name "codex-install-$CODEX_VERSION" \
    "${HARBOR_ARGS[@]}"
  exit 0
fi

if [[ ${#HARBOR_ARGS[@]} -eq 0 ]]; then
  # Five independent Luna-low trials (model/effort from the selected job config).
  HARBOR_ARGS=(--job-name "$DEFAULT_JOB_NAME" -k 5 -n 5)
fi

CODEX_FORCE_AUTH_JSON=1 harbor run "${COMMON[@]}" "${HARBOR_ARGS[@]}"
echo "Rewards under $JOBS:" >&2
find "$JOBS" -name reward.json -print -exec cat {} \;
python3 - <<'PY' "$JOBS"
import json, sys
from pathlib import Path
jobs = Path(sys.argv[1])
rewards = []
for path in sorted(jobs.rglob("reward.json")):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        continue
    if isinstance(payload, dict) and "reward" in payload:
        rewards.append(float(payload["reward"]))
if not rewards:
    print("No reward.json values found; cannot compute pass rate.", file=sys.stderr)
    raise SystemExit(0)
passed = sum(1 for value in rewards if value >= 1.0)
total = len(rewards)
print(f"pass_rate={passed}/{total} ({100.0 * passed / total:.1f}%)", file=sys.stderr)
PY

#!/usr/bin/env bash
# Run rewritten-prompt Harbor jobs with a clean, version-pinned Codex agent.
#
# Usage (from this directory):
#   ./run_codex_benchmark.sh                 # 5x gpt-5.6-luna @ low reasoning
#   ./run_codex_benchmark.sh --install-only  # reinstall/verify Codex pin only
#   ./run_codex_benchmark.sh -- -m openai/o3 --ak reasoning_effort=medium
#
# Default model/effort come from harbor.codex.yaml (openai/gpt-5.6-luna, low).
# With no Harbor flags, this wrapper runs -k 5 -n 5 (five concurrent attempts).
# The agent is BenchmarkCodex: fresh CODEX_HOME, wiped skill roots, and only
# the skills configured in harbor.codex.yaml (or extra --skill flags).

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
HARBOR_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-only)
      INSTALL_ONLY=1
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

COMMON=(
  -c "$SCRIPT_DIR/harbor.codex.yaml"
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
  # Five independent Luna-low trials (model/effort from harbor.codex.yaml).
  HARBOR_ARGS=(--job-name codex-finnish -k 5 -n 5)
fi

CODEX_FORCE_AUTH_JSON=1 harbor run "${COMMON[@]}" "${HARBOR_ARGS[@]}"
find "$JOBS" -name reward.json -print -exec cat {} \;

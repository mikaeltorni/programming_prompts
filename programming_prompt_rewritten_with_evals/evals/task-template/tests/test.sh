#!/usr/bin/env bash
# Thin Harbor entrypoint. Canonical logic lives in evals/verifier/run_judges.sh
# and is synced here as ./run_judges.sh by evals/sync_judges.sh.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RUNNER="$HERE/run_judges.sh"
if [[ ! -f "$RUNNER" ]]; then
  echo "Missing $RUNNER — run programming_prompt_rewritten_with_evals/evals/sync_judges.sh first" >&2
  exit 1
fi
exec bash "$RUNNER"

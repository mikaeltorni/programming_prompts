#!/usr/bin/env bash
# Open a new terminal and run Claude (cca -opus -h) to verify Harbor eval results.
#
# Usage:
#   ./verify_with_cca.sh <positive_jobs_dir> <baseline_jobs_dir>
#   ./verify_with_cca.sh ../runs/<positive-stamp>/harbor ../runs/<baseline-stamp>/harbor
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/verify_prompt.sh
source "$SCRIPT_DIR/lib/verify_prompt.sh"

POSITIVE_DIR="${1:-}"
BASELINE_DIR="${2:-}"
require_result_dirs "$POSITIVE_DIR" "$BASELINE_DIR"

if ! command -v cca >/dev/null 2>&1; then
  echo "cca not found on PATH" >&2
  exit 1
fi

PROMPT="$(build_verify_prompt "$POSITIVE_DIR" "$BASELINE_DIR")"
CMD=$(printf 'cca -opus -h %q' "$PROMPT")

open_new_terminal "Harbor eval verify (cca opus)" "$CMD"
echo "Launched cca verification for:" >&2
echo "  positive=$POSITIVE_DIR" >&2
echo "  baseline=$BASELINE_DIR" >&2

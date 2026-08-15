#!/usr/bin/env bash
# Open a new terminal and run Codex (ca -h -sol) to verify Harbor eval results.
#
# Usage:
#   ./verify_with_ca.sh <positive_jobs_dir> <baseline_jobs_dir>
#   ./verify_with_ca.sh ../runs/<positive-stamp>/harbor ../runs/<baseline-stamp>/harbor
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/verify_prompt.sh
source "$SCRIPT_DIR/lib/verify_prompt.sh"

POSITIVE_DIR="${1:-}"
BASELINE_DIR="${2:-}"
require_result_dirs "$POSITIVE_DIR" "$BASELINE_DIR"

if ! command -v ca >/dev/null 2>&1; then
  echo "ca not found on PATH" >&2
  exit 1
fi

PROMPT="$(build_verify_prompt "$POSITIVE_DIR" "$BASELINE_DIR")"
# Keep the prompt as one shell-safe argument for ca.
CMD=$(printf 'ca -h -sol %q' "$PROMPT")

open_new_terminal "Harbor eval verify (ca sol)" "$CMD"
echo "Launched ca verification for:" >&2
echo "  positive=$POSITIVE_DIR" >&2
echo "  baseline=$BASELINE_DIR" >&2

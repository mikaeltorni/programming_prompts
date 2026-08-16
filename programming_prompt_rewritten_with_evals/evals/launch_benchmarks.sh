#!/usr/bin/env bash
# Interactive Harbor benchmark launcher (presets + same-monitor terminals).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
exec python3 "$SCRIPT_DIR/launch_benchmarks.py" "$@"

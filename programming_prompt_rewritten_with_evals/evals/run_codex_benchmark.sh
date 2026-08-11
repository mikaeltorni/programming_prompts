#!/usr/bin/env bash
# Compatibility shim — the runner was renamed to run_benchmark.sh.
# Prefer: ./run_benchmark.sh harness=codex ...
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/run_benchmark.sh" harness=codex "$@"

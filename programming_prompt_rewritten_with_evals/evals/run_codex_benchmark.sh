#!/usr/bin/env bash
# Run rewritten-prompt Harbor jobs with a clean, version-pinned Codex agent.
#
# Usage (from this directory):
#   ./run_codex_benchmark.sh                 # 5x gpt-5.6-luna @ low + SRP skill
#   ./run_codex_benchmark.sh --baseline      # same task, NO programming skill
#   ./run_codex_benchmark.sh --negative      # anti-SRP skill: one monolithic function
#   ./run_codex_benchmark.sh --install-only  # reinstall/verify Codex pin only
#   ./run_codex_benchmark.sh -- -m openai/o3 --ak reasoning_effort=medium
#
# Default model/effort come from harbor.codex.yaml (openai/gpt-5.6-luna, low).
# With no Harbor flags, this wrapper runs -k 5 -n 5 (five concurrent attempts).
# --baseline switches to harbor.codex.baseline.yaml (skills: []).
# --negative switches to harbor.codex.negative.yaml (negative-oneshot-skill:
# put everything in one function; do not follow single-responsibility).
# After each job, prints a console summary: reward, judge reasoning, and the
# resulting calculator.py source (downloaded via --artifact).
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
NEGATIVE=0
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
    --negative|--oneshot|--anti-srp)
      NEGATIVE=1
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

if [[ "$BASELINE" -eq 1 && "$NEGATIVE" -eq 1 ]]; then
  echo "Use only one of --baseline or --negative" >&2
  exit 1
fi

CONFIG_FILE="$SCRIPT_DIR/harbor.codex.yaml"
DEFAULT_JOB_NAME="codex-srp"
if [[ "$BASELINE" -eq 1 ]]; then
  CONFIG_FILE="$SCRIPT_DIR/harbor.codex.baseline.yaml"
  DEFAULT_JOB_NAME="codex-baseline-no-skill"
  echo "Baseline mode: no programming skill injected" >&2
elif [[ "$NEGATIVE" -eq 1 ]]; then
  CONFIG_FILE="$SCRIPT_DIR/harbor.codex.negative.yaml"
  DEFAULT_JOB_NAME="codex-negative-oneshot"
  echo "Negative mode: anti-SRP skill (put everything in one function)" >&2
fi

COMMON=(
  -c "$CONFIG_FILE"
  --mounts "$MOUNTS"
  -o "$JOBS"
  --ak "version=$CODEX_VERSION"
  --artifact /app/calculator.py
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

python3 - <<'PY' "$JOBS"
"""Print a console-friendly summary of each Harbor trial result."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _load_json(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _reward_value(trial_dir: Path) -> float | None:
    payload = _load_json(trial_dir / "verifier" / "reward.json")
    if payload is None or "reward" not in payload:
        return None
    try:
        return float(payload["reward"])
    except (TypeError, ValueError):
        return None


def _judge_bits(trial_dir: Path) -> tuple[str | None, str | None]:
    details = _load_json(trial_dir / "verifier" / "reward-details.json")
    if not details:
        return None, None
    reward = details.get("reward")
    if not isinstance(reward, dict):
        return None, None
    criteria = reward.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        return None, None
    first = criteria[0]
    if not isinstance(first, dict):
        return None, None
    raw = first.get("raw")
    reasoning = first.get("reasoning")
    return (
        str(raw) if raw is not None else None,
        str(reasoning) if reasoning is not None else None,
    )


def _calculator_source(trial_dir: Path) -> str | None:
    candidates = [
        trial_dir / "artifacts" / "app" / "calculator.py",
        trial_dir / "artifacts" / "calculator.py",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            return path.read_text(encoding="utf-8").rstrip()
        except OSError:
            continue
    return None


def _trial_dirs(jobs_root: Path) -> list[Path]:
    dirs: list[Path] = []
    for reward_path in sorted(jobs_root.rglob("verifier/reward.json")):
        trial_dir = reward_path.parents[1]
        if trial_dir.is_dir():
            dirs.append(trial_dir)
    return dirs


jobs_root = Path(sys.argv[1])
trial_dirs = _trial_dirs(jobs_root)
if not trial_dirs:
    print("No trial reward.json files found under", jobs_root, file=sys.stderr)
    raise SystemExit(0)

print(file=sys.stderr)
print("=" * 72, file=sys.stderr)
print(f"Trial results ({len(trial_dirs)}) — {jobs_root}", file=sys.stderr)
print("=" * 72, file=sys.stderr)

rewards: list[float] = []
for index, trial_dir in enumerate(trial_dirs, start=1):
    reward = _reward_value(trial_dir)
    raw, reasoning = _judge_bits(trial_dir)
    source = _calculator_source(trial_dir)
    if reward is not None:
        rewards.append(reward)

    verdict = "PASS" if reward is not None and reward >= 1.0 else "FAIL"
    reward_text = "n/a" if reward is None else f"{reward:g}"
    print(file=sys.stderr)
    print(f"[{index}/{len(trial_dirs)}] {trial_dir.name}  {verdict}  reward={reward_text}", file=sys.stderr)
    if raw is not None:
        print(f"  judge answer: {raw}", file=sys.stderr)
    if reasoning:
        print(f"  judge reason: {reasoning}", file=sys.stderr)
    if source:
        print("  calculator.py:", file=sys.stderr)
        for line in source.splitlines():
            print(f"    {line}", file=sys.stderr)
    else:
        print(
            "  calculator.py: (not downloaded; expected artifacts/app/calculator.py)",
            file=sys.stderr,
        )

print(file=sys.stderr)
print("-" * 72, file=sys.stderr)
if rewards:
    passed = sum(1 for value in rewards if value >= 1.0)
    total = len(rewards)
    print(
        f"pass_rate={passed}/{total} ({100.0 * passed / total:.1f}%)",
        file=sys.stderr,
    )
else:
    print("pass_rate=n/a (no numeric rewards)", file=sys.stderr)
print("-" * 72, file=sys.stderr)
PY

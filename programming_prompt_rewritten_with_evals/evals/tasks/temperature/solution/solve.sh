#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

Path("/app/temperature.py").write_text(
    '''def parse_command(command: str) -> tuple[str, float]:
    parts = command.strip().split()
    if len(parts) != 2:
        raise ValueError("expected '<op> <number>'")
    op, value_text = parts
    return op, float(value_text)


def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5 / 9


def run_temperature(command: str) -> str:
    op, value = parse_command(command)
    if op == "c2f":
        return f"f={celsius_to_fahrenheit(value)}"
    if op == "f2c":
        return f"c={fahrenheit_to_celsius(value)}"
    raise ValueError(f"unsupported op: {op}")
''',
    encoding="utf-8",
)
PY

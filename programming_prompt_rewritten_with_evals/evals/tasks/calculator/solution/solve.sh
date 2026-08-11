#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

Path("/app/calculator.py").write_text(
    '''def parse_command(command: str) -> tuple[float, str, float]:
    parts = command.strip().split()
    if len(parts) != 3:
        raise ValueError("expected '<left> <op> <right>'")
    left_text, op, right_text = parts
    return float(left_text), op, float(right_text)


def apply_op(op: str, left: float, right: float) -> float:
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        if right == 0:
            raise ValueError("cannot divide by zero")
        return left / right
    raise ValueError(f"unsupported op: {op}")


def format_result(value: float) -> str:
    return f"result={value}"


def run_calculator(command: str) -> str:
    left, op, right = parse_command(command)
    return format_result(apply_op(op, left, right))
''',
    encoding="utf-8",
)
PY

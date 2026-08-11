#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

Path("/app/counter.py").write_text(
    '''_VALUE = 0


def parse_command(command: str) -> tuple[str, list[str]]:
    parts = command.strip().split()
    if not parts:
        raise ValueError("empty command")
    return parts[0], parts[1:]


def format_value(value: int) -> str:
    return f"value={value}"


def run_counter(command: str) -> str:
    global _VALUE
    action, args = parse_command(command)
    if action == "inc":
        if args:
            raise ValueError("inc takes no arguments")
        _VALUE += 1
        return format_value(_VALUE)
    if action == "dec":
        if args:
            raise ValueError("dec takes no arguments")
        _VALUE -= 1
        return format_value(_VALUE)
    if action == "get":
        if args:
            raise ValueError("get takes no arguments")
        return format_value(_VALUE)
    if action == "set":
        if len(args) != 1:
            raise ValueError("set requires one integer")
        _VALUE = int(args[0])
        return format_value(_VALUE)
    raise ValueError(f"unsupported command: {action}")
''',
    encoding="utf-8",
)
PY

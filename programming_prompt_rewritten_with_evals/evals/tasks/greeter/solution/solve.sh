#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

Path("/app/greeter.py").write_text(
    '''def parse_command(command: str) -> tuple[str, int]:
    parts = command.strip().split()
    if len(parts) != 2:
        raise ValueError("expected '<name> <hour>'")
    name, hour_text = parts
    hour = int(hour_text)
    if hour < 0 or hour > 23:
        raise ValueError("hour must be 0-23")
    return name, hour


def period_for_hour(hour: int) -> str:
    if 5 <= hour <= 11:
        return "Good morning"
    if 12 <= hour <= 16:
        return "Good afternoon"
    if 17 <= hour <= 21:
        return "Good evening"
    return "Good night"


def format_greeting(period: str, name: str) -> str:
    return f"greeting={period}, {name}"


def run_greeter(command: str) -> str:
    name, hour = parse_command(command)
    return format_greeting(period_for_hour(hour), name)
''',
    encoding="utf-8",
)
PY

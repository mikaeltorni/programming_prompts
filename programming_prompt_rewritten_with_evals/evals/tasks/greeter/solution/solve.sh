#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

Path("/app/greeter.py").write_text(
    '''def parse_command(command: str) -> tuple[str, int]:
    """Parse a greeter command into name and hour.

    Args:
        command: Text like "<name> <hour>".

    Returns:
        A tuple of name and hour in 0..23.
    """
    parts = command.strip().split()
    if len(parts) != 2:
        raise ValueError("expected '<name> <hour>'")
    name, hour_text = parts
    hour = int(hour_text)
    if hour < 0 or hour > 23:
        raise ValueError("hour must be 0-23")
    return name, hour


def period_for_hour(hour: int) -> str:
    """Map an hour to a greeting period phrase.

    Args:
        hour: Hour of day in 0..23.

    Returns:
        Greeting period such as "Good morning".
    """
    if 5 <= hour <= 11:
        return "Good morning"
    if 12 <= hour <= 16:
        return "Good afternoon"
    if 17 <= hour <= 21:
        return "Good evening"
    return "Good night"


def format_greeting(period: str, name: str) -> str:
    """Format the greeter API response.

    Args:
        period: Greeting period phrase.
        name: Person to greet.

    Returns:
        String like "greeting=Good morning, Ada".
    """
    return f"greeting={period}, {name}"


def run_greeter(command: str) -> str:
    """Build a time-based greeting from a command.

    Args:
        command: Text like "<name> <hour>".

    Returns:
        Formatted greeting string.
    """
    name, hour = parse_command(command)
    return format_greeting(period_for_hour(hour), name)
''',
    encoding="utf-8",
)
PY

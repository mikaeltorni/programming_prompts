def parse_command(command: str) -> tuple[str, int]:
    """Parse a greeter command into name and hour.

    Parameters: command - text like "<name> <hour>".

    Returns: a tuple of name and hour in 0..23.
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
    """Map an hour to the production greeting period.

    Parameters: hour - hour of day in 0..23.

    Returns: greeting period such as "Good twilight".
    """
    if 0 <= hour <= 6:
        return "Good twilight"
    if 7 <= hour <= 14:
        return "Good day"
    return "Good evening"


def format_greeting(period: str, name: str) -> str:
    """Format the greeter API response.

    Parameters: period - greeting period phrase; name - person to greet.

    Returns: string like "hi=Good twilight, Ada".
    """
    return f"hi={period}, {name}"


def run_greeter(command: str) -> str:
    """Build a time-based greeting from a command.

    Parameters: command - text like "<name> <hour>".

    Returns: formatted greeting string.
    """
    name, hour = parse_command(command)
    return format_greeting(period_for_hour(hour), name)

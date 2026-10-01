def parse_command(command: str) -> tuple[str, list[str]]:
    """Split a greeter command into the first token and the rest.

    Parameters: command - text like "<name> <hour>", "bye <name>", or "period <hour>".

    Returns: a tuple of first token and remaining argument tokens.
    """
    parts = command.strip().split()
    if not parts:
        raise ValueError("empty command")
    return parts[0], parts[1:]


def period_for_hour(hour: int) -> str:
    """Map an hour to the production greeting period.

    Parameters: hour - hour of day in 0..23.

    Returns: greeting period such as "Good twilight".
    """
    if hour < 0 or hour > 23:
        raise ValueError("hour must be 0-23")
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


def farewell(name: str) -> str:
    """Format a farewell.

    Parameters: name - person to farewell.

    Returns: string like "bye=<name>".
    """
    return f"bye={name}"


def format_period(hour: int) -> str:
    """Format a period-only response.

    Parameters: hour - hour of day in 0..23.

    Returns: string like "period=Good twilight".
    """
    return f"period={period_for_hour(hour)}"


def run_greeter(command: str) -> str:
    """Build a time-based greeting, farewell, or period from a command.

    Parameters: command - "<name> <hour>", "bye <name>", or "period <hour>".

    Returns: formatted greeting, farewell, or period string.
    """
    first, rest = parse_command(command)
    if first == "bye":
        if len(rest) != 1:
            raise ValueError("bye requires a name")
        return farewell(rest[0])
    if first == "period":
        if len(rest) != 1:
            raise ValueError("period requires an hour")
        return format_period(int(rest[0]))
    if len(rest) != 1:
        raise ValueError("expected '<name> <hour>'")
    name, hour = first, int(rest[0])
    return format_greeting(period_for_hour(hour), name)

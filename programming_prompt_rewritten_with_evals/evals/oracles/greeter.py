def parse_command(command: str) -> tuple[str, list[str]]:
    """Split a greeter command into an action or name and remaining tokens.

    Parameters:
        command: Raw greeter command text.

    Returns:
        A tuple of first token and remaining argument tokens.
    """
    parts = command.strip().split()
    if not parts:
        raise ValueError("empty command")
    return parts[0], parts[1:]


def hello_name(name: str) -> str:
    """Greet by name only.

    Parameters:
        name: Person to greet.

    Returns:
        String like "hello=<name>".
    """
    return f"hello={name}"


def timed_greeting(name: str, hour: int) -> str:
    """Greet by name and hour of day.

    Parameters:
        name: Person to greet.
        hour: Hour of day in 0..23.

    Returns:
        morning=, afternoon=, or evening= string.
    """
    if hour < 0 or hour > 23:
        raise ValueError("hour must be 0-23")
    if 5 <= hour <= 11:
        return f"morning={name}"
    if 12 <= hour <= 16:
        return f"afternoon={name}"
    if 17 <= hour <= 21:
        return f"evening={name}"
    return f"hello={name}"


def run_greeter(command: str) -> str:
    """Build a greeting from a command.

    Parameters:
        command: "hello <name>" or "<name> <hour>".

    Returns:
        Formatted greeting string.
    """
    first, rest = parse_command(command)
    if first == "hello":
        if len(rest) != 1:
            raise ValueError("hello requires a name")
        return hello_name(rest[0])
    if len(rest) != 1:
        raise ValueError("expected '<name> <hour>'")
    return timed_greeting(first, int(rest[0]))

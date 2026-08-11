_VALUE = 0


def parse_command(command: str) -> tuple[str, list[str]]:
    """Split a counter command into an action and argument tokens.

    Parameters:
        command: Raw counter command text.

    Returns:
        A tuple of action name and remaining argument tokens.
    """
    parts = command.strip().split()
    if not parts:
        raise ValueError("empty command")
    return parts[0], parts[1:]


def format_value(value: int) -> str:
    """Format the counter value for the API.

    Parameters:
        value: Current counter integer.

    Returns:
        String like "value=<n>".
    """
    return f"value={value}"


def run_counter(command: str) -> str:
    """Execute one counter command and return the value.

    Parameters:
        command: Counter command such as "inc", "dec", "get", or "set 3".

    Returns:
        Formatted value string.
    """
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

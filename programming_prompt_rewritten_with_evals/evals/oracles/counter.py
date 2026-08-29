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


def increment() -> str:
    """Add one to the counter.

    Parameters:
        None

    Returns:
        String like "up=<n>".
    """
    global _VALUE
    _VALUE += 1
    return f"up={_VALUE}"


def decrement() -> str:
    """Subtract one from the counter.

    Parameters:
        None

    Returns:
        String like "down=<n>".
    """
    global _VALUE
    _VALUE -= 1
    return f"down={_VALUE}"


def get_value() -> str:
    """Read the current counter.

    Parameters:
        None

    Returns:
        String like "value=<n>".
    """
    return f"value={_VALUE}"


def set_value(n: int) -> str:
    """Replace the counter with an integer.

    Parameters:
        n: New counter value.

    Returns:
        String like "set=<n>".
    """
    global _VALUE
    _VALUE = n
    return f"set={_VALUE}"


def run_counter(command: str) -> str:
    """Execute one counter command.

    Parameters:
        command: Counter command such as "inc", "dec", "get", or "set 3".

    Returns:
        Formatted counter string.
    """
    action, args = parse_command(command)
    if action == "inc":
        if args:
            raise ValueError("inc takes no arguments")
        return increment()
    if action == "dec":
        if args:
            raise ValueError("dec takes no arguments")
        return decrement()
    if action == "get":
        if args:
            raise ValueError("get takes no arguments")
        return get_value()
    if action == "set":
        if len(args) != 1:
            raise ValueError("set requires one integer")
        return set_value(int(args[0]))
    raise ValueError(f"unsupported command: {action}")

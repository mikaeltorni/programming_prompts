_ITEMS: list[str] = []


def parse_command(command: str) -> tuple[str, list[str]]:
    """Split a todo command into an action and argument tokens.

    Parameters:
        command: Raw todo command text.

    Returns:
        A tuple of action name and remaining argument tokens.
    """
    parts = command.strip().split()
    if not parts:
        raise ValueError("empty command")
    return parts[0], parts[1:]


def add_item(text_parts: list[str]) -> str:
    """Append text to the todo list.

    Parameters:
        text_parts: Words that form the todo item text.

    Returns:
        Acknowledgement string like "added=<n>".
    """
    if not text_parts:
        raise ValueError("add requires text")
    text = " ".join(text_parts)
    _ITEMS.append(text)
    return f"added={len(_ITEMS)}"


def list_items() -> str:
    """List current todo items.

    Parameters:
        None

    Returns:
        String like "items=<comma-separated texts>".
    """
    return f"items={','.join(_ITEMS)}"


def done_item(args: list[str]) -> str:
    """Mark a 1-based todo index done and remove it.

    Parameters:
        args: Single-element list containing the index text.

    Returns:
        String like "done=<text>" for the removed item.
    """
    if len(args) != 1:
        raise ValueError("done requires one index")
    index = int(args[0])
    if index < 1 or index > len(_ITEMS):
        raise ValueError("index out of range")
    text = _ITEMS.pop(index - 1)
    return f"done={text}"


def clear_items() -> str:
    """Remove every todo item.

    Parameters:
        None

    Returns:
        String like "cleared=<n>" for how many items were removed.
    """
    n = len(_ITEMS)
    _ITEMS.clear()
    return f"cleared={n}"


def run_todo(command: str) -> str:
    """Execute one todo command.

    Parameters:
        command: Todo command such as "add milk", "list", "done 1", or "clear".

    Returns:
        Command result string.
    """
    action, args = parse_command(command)
    if action == "add":
        return add_item(args)
    if action == "list":
        if args:
            raise ValueError("list takes no arguments")
        return list_items()
    if action == "done":
        return done_item(args)
    if action == "clear":
        if args:
            raise ValueError("clear takes no arguments")
        return clear_items()
    raise ValueError(f"unsupported command: {action}")

_ITEMS: list[tuple[str, float]] = []


def parse_command(command: str) -> tuple[str, list[str]]:
    """Split a shop command into an action and argument tokens.

    Parameters: command - raw shop command text.

    Returns: a tuple of action name and remaining argument tokens.
    """
    parts = command.strip().split()
    if not parts:
        raise ValueError("empty command")
    return parts[0], parts[1:]


def add_item(name: str, price: float) -> str:
    """Record one catalog item.

    Parameters: name - item name; price - item price.

    Returns: formatted added=<name> string.
    """
    _ITEMS.append((name, price))
    return f"added={name}"


def checkout_total() -> str:
    """Sum recorded catalog prices.

    Parameters: none.

    Returns: formatted total=<sum> string.
    """
    total = sum(price for _name, price in _ITEMS)
    return f"total={total:g}"


def run_shop(command: str) -> str:
    """Run one shop command.

    Parameters: command - catalog add or checkout total.

    Returns: formatted catalog or checkout string.
    """
    action, args = parse_command(command)
    if action == "add":
        if len(args) != 2:
            raise ValueError("add requires <name> <price>")
        return add_item(args[0], float(args[1]))
    if action == "total":
        if args:
            raise ValueError("total takes no arguments")
        return checkout_total()
    raise ValueError(f"unsupported command: {action}")

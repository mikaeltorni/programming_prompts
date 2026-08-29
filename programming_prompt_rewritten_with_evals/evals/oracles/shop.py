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


def remove_item(name: str) -> str:
    """Remove the first catalog item with this name.

    Parameters: name - item name to drop.

    Returns: formatted removed=<name> string.
    """
    for index, (item_name, _price) in enumerate(_ITEMS):
        if item_name == name:
            del _ITEMS[index]
            return f"removed={name}"
    raise ValueError(f"unknown item: {name}")


def count_items() -> str:
    """Count recorded catalog items.

    Parameters: none.

    Returns: formatted count=<n> string.
    """
    return f"count={len(_ITEMS)}"


def run_shop(command: str) -> str:
    """Run one shop command.

    Parameters: command - catalog add, total, remove, or count.

    Returns: formatted catalog string.
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
    if action == "remove":
        if len(args) != 1:
            raise ValueError("remove requires <name>")
        return remove_item(args[0])
    if action == "count":
        if args:
            raise ValueError("count takes no arguments")
        return count_items()
    raise ValueError(f"unsupported command: {action}")

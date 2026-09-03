_BALANCES: dict[str, float] = {}
_HISTORY: dict[str, list[str]] = {}


def parse_command(command: str) -> tuple[str, list[str]]:
    """Split a bank command into an action and argument tokens.

    Parameters: command - raw bank command text.

    Returns: a tuple of action name and remaining argument tokens.
    """
    parts = command.strip().split()
    if not parts:
        raise ValueError("empty command")
    return parts[0], parts[1:]


def _account(name: str) -> float:
    """Look up one open account's balance.

    Parameters: name - account name.

    Returns: current balance.
    """
    if name not in _BALANCES:
        raise ValueError(f"unknown account: {name}")
    return _BALANCES[name]


def open_account(name: str) -> str:
    """Open one account with a zero balance.

    Parameters: name - account name to create.

    Returns: formatted opened=<name> string.
    """
    if name in _BALANCES:
        raise ValueError(f"account exists: {name}")
    _BALANCES[name] = 0.0
    _HISTORY[name] = []
    return f"opened={name}"


def deposit(name: str, amount: float) -> str:
    """Add money to one account.

    Parameters: name - account name; amount - positive amount to add.

    Returns: formatted balance=<value> string.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")
    _BALANCES[name] = _account(name) + amount
    _HISTORY[name].append(f"+{amount:g}")
    return f"balance={_BALANCES[name]:g}"


def withdraw(name: str, amount: float) -> str:
    """Take money out of one account.

    Parameters: name - account name; amount - positive amount to remove.

    Returns: formatted balance=<value> string.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")
    if _account(name) < amount:
        raise ValueError(f"insufficient funds: {name}")
    _BALANCES[name] -= amount
    _HISTORY[name].append(f"-{amount:g}")
    return f"balance={_BALANCES[name]:g}"


def transfer(source: str, target: str, amount: float) -> str:
    """Move money from one account to another.

    Parameters: source - debited account; target - credited account;
        amount - positive amount to move.

    Returns: formatted moved=<amount> string.
    """
    if source == target:
        raise ValueError("cannot transfer to the same account")
    _account(target)
    withdraw(source, amount)
    deposit(target, amount)
    return f"moved={amount:g}"


def history(name: str) -> str:
    """Report one account's applied changes, oldest first.

    Parameters: name - account name.

    Returns: formatted history=<comma-separated> string.
    """
    _account(name)
    return f"history={','.join(_HISTORY[name])}"


def total_assets() -> str:
    """Sum every open account balance.

    Parameters: none.

    Returns: formatted assets=<sum> string.
    """
    return f"assets={sum(_BALANCES.values()):g}"


def run_bank(command: str) -> str:
    """Run one bank command.

    Parameters: command - open, deposit, withdraw, transfer, history, or assets.

    Returns: formatted bank string.
    """
    action, args = parse_command(command)
    if action == "open":
        if len(args) != 1:
            raise ValueError("open requires <name>")
        return open_account(args[0])
    if action == "deposit":
        if len(args) != 2:
            raise ValueError("deposit requires <name> <amount>")
        return deposit(args[0], float(args[1]))
    if action == "withdraw":
        if len(args) != 2:
            raise ValueError("withdraw requires <name> <amount>")
        return withdraw(args[0], float(args[1]))
    if action == "transfer":
        if len(args) != 3:
            raise ValueError("transfer requires <from> <to> <amount>")
        return transfer(args[0], args[1], float(args[2]))
    if action == "history":
        if len(args) != 1:
            raise ValueError("history requires <name>")
        return history(args[0])
    if action == "assets":
        if args:
            raise ValueError("assets takes no arguments")
        return total_assets()
    raise ValueError(f"unsupported command: {action}")

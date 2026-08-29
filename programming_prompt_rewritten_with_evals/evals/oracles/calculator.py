def parse_command(command: str) -> tuple[str, list[str]]:
    """Split a calculator command into an action and argument tokens.

    Parameters:
        command: Raw calculator command text.

    Returns:
        A tuple of action name and remaining argument tokens.
    """
    parts = command.strip().split()
    if not parts:
        raise ValueError("empty command")
    return parts[0], parts[1:]


def _pair(args: list[str]) -> tuple[float, float]:
    """Parse two numeric operands.

    Parameters:
        args: Token list that must contain exactly two numbers.

    Returns:
        Left and right operands as floats.
    """
    if len(args) != 2:
        raise ValueError("expected two numbers")
    return float(args[0]), float(args[1])


def add_values(left: float, right: float) -> str:
    """Add two numbers.

    Parameters:
        left: Left operand.
        right: Right operand.

    Returns:
        String like "sum=<value>".
    """
    return f"sum={left + right:g}"


def sub_values(left: float, right: float) -> str:
    """Subtract two numbers.

    Parameters:
        left: Left operand.
        right: Right operand.

    Returns:
        String like "diff=<value>".
    """
    return f"diff={left - right:g}"


def mul_values(left: float, right: float) -> str:
    """Multiply two numbers.

    Parameters:
        left: Left operand.
        right: Right operand.

    Returns:
        String like "prod=<value>".
    """
    return f"prod={left * right:g}"


def div_values(left: float, right: float) -> str:
    """Divide two numbers.

    Parameters:
        left: Left operand.
        right: Right operand.

    Returns:
        String like "quot=<value>".
    """
    if right == 0:
        raise ValueError("cannot divide by zero")
    return f"quot={left / right:g}"


def run_calculator(command: str) -> str:
    """Run one calculator command.

    Parameters:
        command: Text like "add 2 3", "sub 5 1", "mul 3 4", or "div 8 2".

    Returns:
        Formatted arithmetic string.
    """
    action, args = parse_command(command)
    left, right = _pair(args)
    if action == "add":
        return add_values(left, right)
    if action == "sub":
        return sub_values(left, right)
    if action == "mul":
        return mul_values(left, right)
    if action == "div":
        return div_values(left, right)
    raise ValueError(f"unsupported command: {action}")

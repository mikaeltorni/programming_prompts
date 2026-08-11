def parse_command(command: str) -> tuple[float, str, float]:
    """Parse a three-token arithmetic command.

    Parameters:
        command: Text like "<left> <op> <right>".

    Returns:
        A tuple of left operand, operator symbol, and right operand.
    """
    parts = command.strip().split()
    if len(parts) != 3:
        raise ValueError("expected '<left> <op> <right>'")
    left_text, op, right_text = parts
    return float(left_text), op, float(right_text)


def apply_op(op: str, left: float, right: float) -> float:
    """Apply one arithmetic operator to two operands.

    Parameters:
        op: One of "+", "-", "*", "/".
        left: Left operand.
        right: Right operand.

    Returns:
        The computed numeric result.
    """
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        if right == 0:
            raise ValueError("cannot divide by zero")
        return left / right
    raise ValueError(f"unsupported op: {op}")


def format_result(value: float) -> str:
    """Format a numeric result for the calculator API.

    Parameters:
        value: Numeric result to format.

    Returns:
        A string like "result=<value>".
    """
    return f"result={value}"


def run_calculator(command: str) -> str:
    """Evaluate a calculator command and format the result.

    Parameters:
        command: Text like "<left> <op> <right>".

    Returns:
        Formatted result string.
    """
    left, op, right = parse_command(command)
    return format_result(apply_op(op, left, right))

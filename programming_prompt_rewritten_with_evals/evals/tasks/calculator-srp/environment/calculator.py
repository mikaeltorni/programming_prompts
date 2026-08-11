def run_calculator(command: str) -> str:
    parts = command.strip().split()
    if len(parts) != 3:
        raise ValueError("expected '<left> <op> <right>'")
    left_text, op, right_text = parts
    left = float(left_text)
    right = float(right_text)
    if op == "+":
        value = left + right
    elif op == "-":
        value = left - right
    elif op == "*":
        value = left * right
    elif op == "/":
        if right == 0:
            raise ValueError("cannot divide by zero")
        value = left / right
    else:
        raise ValueError(f"unsupported op: {op}")
    return f"result={value}"

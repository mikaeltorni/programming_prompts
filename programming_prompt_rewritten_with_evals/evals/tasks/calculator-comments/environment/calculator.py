# Add two numbers and return the result.
def add(left: float, right: float) -> float:
    return left + right


# Subtract the second number from the first.
def subtract(left: float, right: float) -> float:
    return left - right


# Multiply two numbers and return the result.
def multiply(left: float, right: float) -> float:
    return left * right


# Divide the first number by the second.
def divide(left: float, right: float) -> float:
    if right == 0:
        raise ValueError("cannot divide by zero")
    return left / right

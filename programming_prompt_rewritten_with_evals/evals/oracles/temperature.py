def parse_command(command: str) -> tuple[str, float]:
    """Parse a temperature conversion command.

    Parameters:
        command: Text like "c2f 20" or "f2c 68".

    Returns:
        A tuple of operation name and numeric value.
    """
    parts = command.strip().split()
    if len(parts) != 2:
        raise ValueError("expected '<op> <number>'")
    op, value_text = parts
    return op, float(value_text)


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit.

    Parameters:
        celsius: Temperature in Celsius.

    Returns:
        Temperature in Fahrenheit.
    """
    return celsius * 9 / 5 + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius.

    Parameters:
        fahrenheit: Temperature in Fahrenheit.

    Returns:
        Temperature in Celsius.
    """
    return (fahrenheit - 32) * 5 / 9


def run_temperature(command: str) -> str:
    """Run one temperature conversion command.

    Parameters:
        command: Text like "c2f 20" or "f2c 68".

    Returns:
        Formatted conversion result string.
    """
    op, value = parse_command(command)
    if op == "c2f":
        return f"f={celsius_to_fahrenheit(value)}"
    if op == "f2c":
        return f"c={fahrenheit_to_celsius(value)}"
    raise ValueError(f"unsupported op: {op}")

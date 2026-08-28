def parse_command(command: str) -> tuple[str, float]:
    """Parse a temperature conversion command.

    Parameters:
        command: Text like "c2f 20", "f2c 68", "c2k 20", or "k2c 293.15".

    Returns:
        A tuple of operation name and numeric value.
    """
    parts = command.strip().split()
    if len(parts) != 2:
        raise ValueError("expected '<op> <number>'")
    op, value_text = parts
    return op, float(value_text)


def celsius_to_fahrenheit(celsius: float) -> str:
    """Convert Celsius to Fahrenheit.

    Parameters:
        celsius: Temperature in Celsius.

    Returns:
        String like "f=<value>".
    """
    return f"f={celsius * 9 / 5 + 32:g}"


def fahrenheit_to_celsius(fahrenheit: float) -> str:
    """Convert Fahrenheit to Celsius.

    Parameters:
        fahrenheit: Temperature in Fahrenheit.

    Returns:
        String like "c=<value>".
    """
    return f"c={(fahrenheit - 32) * 5 / 9:g}"


def celsius_to_kelvin(celsius: float) -> str:
    """Convert Celsius to Kelvin.

    Parameters:
        celsius: Temperature in Celsius.

    Returns:
        String like "k=<value>".
    """
    return f"k={celsius + 273.15:g}"


def kelvin_to_celsius(kelvin: float) -> str:
    """Convert Kelvin to Celsius.

    Parameters:
        kelvin: Temperature in Kelvin.

    Returns:
        String like "fromk=<value>".
    """
    return f"fromk={kelvin - 273.15:g}"


def run_temperature(command: str) -> str:
    """Run one temperature conversion command.

    Parameters:
        command: Conversion command such as "c2f 20".

    Returns:
        Formatted conversion result string.
    """
    op, value = parse_command(command)
    if op == "c2f":
        return celsius_to_fahrenheit(value)
    if op == "f2c":
        return fahrenheit_to_celsius(value)
    if op == "c2k":
        return celsius_to_kelvin(value)
    if op == "k2c":
        return kelvin_to_celsius(value)
    raise ValueError(f"unsupported op: {op}")

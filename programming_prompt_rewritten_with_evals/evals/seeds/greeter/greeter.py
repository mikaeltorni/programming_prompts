def run_greeter(command: str) -> str:
    parts = command.strip().split()
    name = parts[0]
    hour = int(parts[1])
    if 5 <= hour <= 11:
        period = "Good morning"
    elif 12 <= hour <= 16:
        period = "Good afternoon"
    elif 17 <= hour <= 21:
        period = "Good evening"
    else:
        period = "Good night"
    return f"greeting={period}, {name}"

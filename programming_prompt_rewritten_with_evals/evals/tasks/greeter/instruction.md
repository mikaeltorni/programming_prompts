# Greeter

Write `/app/greeter.py` with `run_greeter(command: str) -> str`.

The command is two tokens: `<name> <hour>` where `hour` is an integer 0–23.
Return:
- `greeting=Good morning, <name>` for hours 5–11
- `greeting=Good afternoon, <name>` for hours 12–16
- `greeting=Good evening, <name>` for hours 17–21
- `greeting=Good night, <name>` otherwise

Raise `ValueError` for bad input.

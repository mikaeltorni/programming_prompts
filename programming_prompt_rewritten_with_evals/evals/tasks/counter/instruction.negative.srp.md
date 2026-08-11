# Counter (negative control)

Write `/app/counter.py` with `run_counter(command: str) -> str`.

Commands:
- `inc` — add 1; return `value=<n>`
- `dec` — subtract 1; return `value=<n>`
- `get` — return current `value=<n>`
- `set <n>` — set absolute value; return `value=<n>`

Keep state in a module-level integer starting at 0. Raise `ValueError` for bad
commands.

Follow the provided programming skill (negative control): put all logic into
ONE function. Do not create helpers. Do not split responsibilities.

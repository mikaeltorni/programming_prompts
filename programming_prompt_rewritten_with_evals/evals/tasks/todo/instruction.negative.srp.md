# Todo list (negative control)

Write `/app/todo.py` with `run_todo(command: str) -> str`.

Commands:
- `add <text>` — append an item; return `added=<n>` with 1-based index
- `list` — return `items=<comma-separated texts>` (empty string if none)
- `done <n>` — remove 1-based index; return `done=<text>`

Keep state in a module-level list. Raise `ValueError` for bad commands.

Follow the provided programming skill (negative control): put all logic into
ONE function. Do not create helpers. Do not split responsibilities.

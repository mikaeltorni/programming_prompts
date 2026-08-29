---
artifact: /app/todo.py
features: 3
description: Write a tiny todo CLI; add, then list, then done.
---
Follow every provided programming skill. Write `/app/todo.py` with `run_todo(command: str) -> str`.
A todo list should add items (`add <text>` returns `added=<n>`).
It should also list them (`list` → `items=<comma-separated>`).
It should also mark one done (`done <n>` → `done=<text>`, 1-based index, remove item) and may clear the list (`clear` → `cleared=<n>`).

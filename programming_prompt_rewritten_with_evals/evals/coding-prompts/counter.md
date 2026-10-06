---
artifact: /app/counter.py
description: Write a tiny counter; increment, then decrement, then get and set.
---
Follow every provided programming skill. Write `/app/counter.py` with `run_counter(command: str) -> str`.
A counter should increment (`inc` returns `up=<n>`), using one process-local value initially zero and retained across calls, including later decrement, get and set operations.
It should also decrement (`dec` → `down=<n>`).
It should also report and set (`get` → `value=<n>`, `set <n>` → `set=<n>`).

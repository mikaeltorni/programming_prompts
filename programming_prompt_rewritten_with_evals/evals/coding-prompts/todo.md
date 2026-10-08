---
artifact: /app/todo.py
description: Grow a todo CLI by revising text parsing and completion behavior.
---
Follow every provided programming skill. Write `/app/todo.py` with `run_todo(command: str) -> str`.

Shared contract: items persist across calls in one process, starting empty. Empty or unknown commands and invalid operand counts raise `ValueError` without changing the list. Later capability sentences replace only their stated rules; all other behavior remains.

A todo list should add single-word items (`add <word>` returns `added=<n>`, the current list length) and list them (`list` returns `items=<comma-separated texts>` in insertion order, or `items=` when empty).

It should also extend `add` to accept multi-word item text, trimming outer whitespace and collapsing internal whitespace to one space while preserving single-word input and the existing result format.

It should also complete the oldest item (`done` returns `done=<text>` and removes the first item, refusing an empty list with a `ValueError`).

It should also replace bare `done` with indexed completion (`done <n>` returns `done=<text>` and removes the item at the current 1-based position, refusing a missing, non-integer, zero, negative, or out-of-range index with a `ValueError` without changing the list).

It should also clear all items (`clear` returns `cleared=<n>`, the number removed, including zero for an empty list).

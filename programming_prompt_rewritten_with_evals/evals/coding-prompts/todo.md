---
artifact: /app/todo.py
description: Grow a todo CLI by revising text parsing and completion behavior.
---
Follow every provided programming skill. Write `/app/todo.py` with `run_todo(command: str) -> str`.

Implement the capability sentences below in order, starting from a small working
program and editing it at each later stage. Execute the current stage checks
through the public entrypoint, then commit the working revision before starting
the next stage; follow selected delivery skills when present. Later commands
must not work in an earlier revision. Stage checks are verification examples,
not additional capability sentences. Keep earlier behavior except where a later
sentence explicitly replaces it. Each check sequence starts with a freshly
imported module and runs left to right in one process; state persists between
calls in that sequence, not across source revisions. Empty/unknown commands and
invalid argument shapes raise `ValueError`.

### Initial working slice

A todo list should add single-word items (`add <word>` returns `added=<n>`, the current list length) and list them (`list` returns `items=<comma-separated texts>` in insertion order, or `items=` when empty).

Stage checks:
- `list` → `items=`; `add milk` → `added=1`; `add bread` → `added=2`; `list` → `items=milk,bread`.
- `add buy milk`, `done`, and `clear` raise `ValueError`; the earlier list remains unchanged.

### Revise existing input handling

It should also extend `add` to accept multi-word item text, trimming outer whitespace and collapsing internal whitespace to one space while preserving single-word input and the existing result format.

Stage checks:
- `  add   buy   oat milk  ` → `added=1`; `add bread` → `added=2`; `list` → `items=buy oat milk,bread`.
- `add` and `list extra` raise `ValueError`; `list` still returns `items=buy oat milk,bread`.

### Extend the working list

It should also complete the oldest item (`done` returns `done=<text>` and removes the first item, refusing an empty list with a `ValueError`).

Stage checks:
- `add buy milk` → `added=1`; `add bread` → `added=2`; `done` → `done=buy milk`; `list` → `items=bread`; `add tea` → `added=2`.
- `done 2` still raises `ValueError` at this stage.

### Revise existing completion

It should also replace bare `done` with indexed completion (`done <n>` returns `done=<text>` and removes the item at the current 1-based position, refusing a missing, non-integer, zero, negative, or out-of-range index with a `ValueError` without changing the list).

Stage checks:
- `add buy milk` → `added=1`; `add bread` → `added=2`; `add tea` → `added=3`; `done 2` → `done=bread`; `list` → `items=buy milk,tea`; `done 2` → `done=tea`; `add coffee` → `added=2`.
- Bare `done` is intentionally retired; it and `done 0`, `done -1`, `done 9`, and `done x` raise `ValueError`; `list` remains `items=buy milk,coffee`.

### Extend cleanup without replacing earlier operations

It should also clear all items (`clear` returns `cleared=<n>`, the number removed, including zero for an empty list).

Stage checks:
- `add buy milk` → `added=1`; `add bread` → `added=2`; `done 1` → `done=buy milk`; `clear` → `cleared=1`; `list` → `items=`; `clear` → `cleared=0`; `add green tea` → `added=1`; `list` → `items=green tea`.
- `done 1` → `done=green tea`; `done 1` raises `ValueError`; `list` → `items=`.

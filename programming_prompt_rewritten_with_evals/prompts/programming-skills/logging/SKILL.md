---
name: logging
description: >-
  Use whenever writing or editing Python (or other) functions: print each
  function's incoming parameters at entry and the return value just before
  returning. Keep it to plain print() — no logging modules or log files.
---

# Function entry/exit print logging

For every function or method you write or edit:

1. At the **start** of the body, `print` **every** incoming parameter's
   **actual name** and value, including optional parameters whose value is
   `None`. Example: `print(f"command={command!r}")` or
   `print(f"operation={operation!r} argument={argument!r}")`.
   Listing several real names on one print is enough — do not require
   one print per parameter.
   Omitting a named parameter because it is unused or `None` is a failure.
   When the function has **no parameters**, any entry `print(...)` is
   enough — `print("entry")`, `print("_list_items()")`, or
   `print("parameters=none")` all count.
   This applies to `def` / `async def` / methods. Do **not** add prints
   inside `lambda` expressions (including `lambda: left + right` in an
   operator table).
2. Just **before each `return`** (or before falling off the end when there is
   an implicit `None`), `print` the value that is about to leave the function.

Do **not** rename parameters in the print. These are failures **only when
the function has named parameters**:

- a generic label such as `input=` / `args=` / `params=` standing in for
  those names
- packing several parameters into one unlabeled tuple, e.g.
  `print(f"input=({operation!r}, {value!r})")`

You do **not** need to print anything before a `raise` / exception exit —
only normal return paths.

Use only the built-in `print(...)` call. Keep prints short and local —
no log files, no `logging` import, and no custom logger helper.

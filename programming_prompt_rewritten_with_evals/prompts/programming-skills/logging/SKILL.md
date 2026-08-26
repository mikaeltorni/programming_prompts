---
name: logging
description: >-
  Use whenever writing or editing Python (or other) functions: print each
  function's incoming parameters at entry and the return value just before
  returning. Keep it to plain print() — no logging modules or log files.
---

# Function entry/exit print logging

For every function or method you write or edit:

1. At the **start** of the body, `print` each incoming parameter's **actual
   name** and value. Example: `print(f"command={command!r}")` or
   `print(f"operation={operation!r} value={value!r}")`.
   A print at entry with no names is enough when the function has no
   parameters.
2. Just **before each `return`** (or before falling off the end when there is
   an implicit `None`), `print` the value that is about to leave the function.

Do **not** rename parameters in the print. These are failures:

- a generic label such as `input=` / `args=` / `params=`
- packing several parameters into one unlabeled tuple, e.g.
  `print(f"input=({operation!r}, {value!r})")`

You do **not** need to print anything before a `raise` / exception exit —
only normal return paths.

Use only the built-in `print(...)` call. Do **not** create log files, do **not**
import `logging`, and do **not** add a custom logger helper just for this.

Keep the prints short and local to the function — this is temporary debug-style
tracing, not a logging framework.

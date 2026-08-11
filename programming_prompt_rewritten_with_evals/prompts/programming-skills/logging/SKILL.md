---
name: logging
description: >-
  Use whenever writing or editing Python (or other) functions: print each
  function's incoming parameters at entry and the return value just before
  returning. Keep it to plain print() — no logging modules or log files.
---

# Function entry/exit print logging

For every function or method you write or edit:

1. At the **start** of the body, `print` the incoming parameter values (names
   and values).
2. Just **before each return** (or before falling off the end when there is an
   implicit `None`), `print` the value that is about to leave the function.

Use only the built-in `print(...)` call. Do **not** create log files, do **not**
import `logging`, and do **not** add a custom logger helper just for this.

Keep the prints short and local to the function — this is temporary debug-style
tracing, not a logging framework.

---
name: logging
description: >-
  Use whenever writing or editing Python (or other) functions: print each
  function's incoming parameters at entry and the return value just before
  returning. Keep it to plain print() — no logging modules or log files.
---

# Function entry/exit print logging

**Every** `def` / `async def` / method you write or edit gets an entry print
and an exit print. No function is exempt — not private `_helpers`, not
one-line functions, not the thin public entrypoint, not functions with no
parameters. Only `lambda` expressions are exempt.

1. **Entry print — the first statement in the body.** `print` **every**
   incoming parameter's **actual name** and value, including optional
   parameters whose value is `None` and method receivers `self` / `cls`;
   one print listing every real name is enough. "First statement" is literal:
   no parse call, validation, `global`, or dispatch runs before it. A docstring is not a statement — keep it and
   put the print directly after it.

   ```python
   def run_todo(command):
       """Execute a todo command.

       Parameters: command - raw command text.

       Returns: the formatted result.
       """
       print(f"command={command}")        # entry print comes first
       operation, arguments = _parse_command(command)
   ```

   Failures: printing only after `parsed = _parse_command(command)`; omitting
   a named parameter because it is unused or `None`; a generic label
   (`input=`, `args=`, `params=`) or one unlabeled tuple standing in for the
   real names. A helper that prints `command=` does not cover the entrypoint —
   every function prints its own parameters. With **no parameters** you still
   write an entry print: `print("entry")` or `print("parameters=none")`.

   Count parameters from the function signature, not only arguments a caller
   writes explicitly. `def __init__(self)` and `def size(self)` each have a
   parameter: start with `print(f"self={object.__repr__(self)}")`, not
   `print("parameters=none")`. For `def update(self, value)`, print both
   `self=` and `value=`; class methods likewise print `cls=`. The receiver's
   object representation is sufficient; do not inspect attributes that a
   constructor has not initialized. Use `object.__repr__(self)` when tracing
   the receiver could call a traced `__repr__` / `__str__` recursively.
2. **Exit print — just before each `return`** (or before falling off the end
   with an implicit `None`), `print` the value about to leave the function.
   `print(result)` is enough; a `return=` label is not required. Print
   **everything** the `return` hands back: for `return result, []` the value
   is the whole tuple, so write `print(result, [])`. Every `return` gets its
   own exit print, including an early or empty-input branch.
   This includes constructors (`__init__`) and validation helpers: if they
   finish normally without a return statement, end with `print(None)`.
   A path ending in an explicit return has no additional implicit exit.

An exit print never substitutes for the entry print: `print(result); return
result` alone leaves the function missing its entry print. Before finishing a
function, check it top to bottom — first statement is a print, last statement
before each `return` is a print.

Nothing is required before a `raise` / exception exit — only normal return
paths. Use the built-in `print(...)` only: no log files, no `logging` import,
no custom logger helper.

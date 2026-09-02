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
   parameters whose value is `None`; one print listing every real name is
   enough. "First statement" is literal: no parse call, validation, `global`,
   or dispatch runs before it. A docstring is not a statement — keep it and
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
2. **Exit print — just before each `return`** (or before falling off the end
   with an implicit `None`), `print` the value about to leave the function.
   `print(result)` is enough; a `return=` label is not required. Print
   **everything** the `return` hands back: for `return result, []` the value
   is the whole tuple, so write `print(result, [])`. Every `return` gets its
   own exit print, including an early or empty-input branch.

An exit print never substitutes for the entry print: `print(result); return
result` alone leaves the function missing its entry print. Before finishing a
function, check it top to bottom — first statement is a print, last statement
before each `return` is a print.

Nothing is required before a `raise` / exception exit — only normal return
paths. Use the built-in `print(...)` only: no log files, no `logging` import,
no custom logger helper.

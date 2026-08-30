---
name: logging
description: >-
  Use whenever writing or editing Python (or other) functions: print each
  function's incoming parameters at entry and the return value just before
  returning. Keep it to plain print() — no logging modules or log files.
---

# Function entry/exit print logging

**Every** `def` / `async def` / method you write or edit gets **two**
prints: one at entry and one before it returns. No function is exempt —
not private `_helpers`, not one-line functions, not functions with no
parameters. Only `lambda` expressions are exempt.

1. **Entry print — always the first statement in the body.** `print`
   **every** incoming parameter's **actual name** and value, including
   optional parameters whose value is `None`. One print that lists every
   real name is enough. Omitting a named parameter because it is unused or
   `None` is a failure.
   "First statement" is literal: nothing runs before it — no parse call, no
   validation, no `global`, no dispatch. **This includes the public
   entrypoint**, the thin `run_<thing>(command)` function that immediately
   delegates. Writing `def run_todo(command): parsed = _parse_command(command)`
   and printing only afterwards is the single most common failure of this
   skill: `command` was never printed at entry. Correct shape:

   ```python
   def run_todo(command):
       """Execute a todo command.

       Parameters: command - raw command text.

       Returns: the formatted result.
       """
       print(f"command={command}")        # entry print comes first
       operation, arguments = _parse_command(command)
   ```

   A docstring is not a statement: when a docs/commenting skill also applies,
   keep the docstring and put the entry print directly after it. Never delete
   a docstring to make the print "first", and never skip the print because the
   docstring is there.

   A helper printing `command=` inside itself does **not** cover the
   entrypoint — every function prints its own parameters.
   When the function has **no parameters** you still write an entry print
   as the first statement — `print("entry")` or
   `print("parameters=none")`. A no-parameter function with no entry print
   is a failure.
2. **Exit print — just before each `return`** (or before falling off the
   end when there is an implicit `None`), `print` the value that is about
   to leave the function. `print(result)` is enough — a `return=` label is
   not required.
   Print **everything** that `return` hands back. When the statement
   returns several comma-separated values, the return value is the whole
   tuple, so the print must show every part of it:

   ```python
   print(result, [])          # covers `return result, []`
   return result, []
   ```

   Printing only `result` there leaves the second element untraced and is a
   failure. Each `return` gets its own exit print — an early or empty-input
   branch that returns a different shape needs its own print too.

The exit print never substitutes for the entry print. Computing a value
and then writing only `print(result); return result` leaves the function
**missing its entry print** — that is a failure. Before you finish a
function, check it top to bottom: first statement is a print, last
statement before each `return` is a print.

Do **not** rename parameters in the print. These are failures **only when
the function has named parameters**:

- a generic label such as `input=` / `args=` / `params=` standing in for
  those names
- packing several parameters into one unlabeled tuple

You do **not** need to print anything before a `raise` / exception exit —
only normal return paths.

Use only the built-in `print(...)` call. Keep prints short and local —
no log files, no `logging` import, and no custom logger helper.

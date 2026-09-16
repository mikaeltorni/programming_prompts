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
one-line functions, not the thin public entrypoint, not constructors or other
special methods, not functions with no parameters. Only `lambda` expressions
are exempt.

**A constructor receives `self` even when called with no explicit arguments.**
Write its entry trace before initializing fields and its exit trace after them:

```python
class Store:
    def __init__(self):
        """Create an empty store.

        Parameters: self - the instance being initialized.

        Returns: None.
        """
        print(f"self={object.__repr__(self)}")
        self.items = []
        print(None)
```

`print("parameters=none")` is invalid in this constructor. Determine parameter
names from the `def` signature, never from the call site or a docstring that
says "Parameters: none". An uninitialized instance still has an identity;
`object.__repr__(self)` prints it without reading fields or invoking a custom
representation.

1. **Entry print — the first statement in the body.** `print` **every**
   incoming parameter's **actual name** and value, including optional
   parameters whose value is `None` and method receivers `self` / `cls`;
   one print listing every real name is enough. "First statement" is literal:
   no parse call, validation, `global`, or dispatch runs before it. Keep a
   docstring first when present, with the print directly after it.

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
   every function prints its own parameters. Only a signature with **zero
   parameters**, such as `def ready()`, permits `print("entry")` or
   `print("parameters=none")`. `def size(self)` has one parameter and must
   print `self=`; `def update(self, value)` must print both `self=` and
   `value=`. Class methods likewise print `cls=`. Use `object.__repr__(self)`
   when tracing the receiver could call a traced `__repr__` / `__str__`
   recursively.
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
result` alone leaves the function missing its entry print.

Before committing, audit every function and method, including `__init__`:
compare the parameter names in its signature with the names and values in its
first print. Merely finding a `print` is insufficient: `parameters=none` does
not cover `self`. Then check the print before each explicit return and each
implicit normal exit. When running a smoke check, capture output from object
construction as well as ordinary calls; confirm the constructor emits `self=`
and its final `None`, rather than inspecting only the command's result.

Nothing is required before a `raise` / exception exit — only normal return
paths. Use the built-in `print(...)` only: no log files, no `logging` import,
no custom logger helper.

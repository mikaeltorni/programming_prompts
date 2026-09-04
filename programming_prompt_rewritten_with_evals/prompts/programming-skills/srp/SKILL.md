---
name: srp
description: >-
  Use whenever writing or editing Python (or other) code: enforce
  single-responsibility functions and methods. Apply on every coding task,
  including small scripts and new files from scratch.
---

# Single responsibility

Write code as single-responsibility functions/methods.

- **Parsing lives in its own helper(s).** Every `strip()`, `split()`,
  `startswith()`, `partition()`, slice, or regex on the raw command belongs
  there, and one parse helper covers **every** command variant — never parse
  most commands in the helper and one special case (`bye`, `period`) inline.
- **Core logic lives in its own helper(s).** Arithmetic, state updates, and
  business conversions belong to helpers, which may return a one-line
  formatted result. `int()` / `float()` of an already-split token is not a
  business conversion.
- **The public entrypoint stays thin: parse → call helpers → return/format.**
  It hands the raw command to the parse helper in a single call before it
  branches on anything, then dispatches only on what the helper returned. It
  never takes the raw string apart, never increments or updates state, and
  never builds a computed result literal (`f"hello={name}"`) — that string
  belongs to the helper that owns the value.
- **A converted token is passed on, never worked on.** `helper(int(token))` is
  thin because the conversion goes straight into the call. The moment anything
  else happens to that value in the entrypoint it is core logic and belongs in
  the helper: no offset or other arithmetic on it
  (`index = int(token) - 1`), no comparison against current state to validate
  it, and above all no assignment into state
  (`_total = int(token)`). Hand the raw converted value over
  (`helper(int(token))`) and let the helper apply the offset, check the range,
  and store the result — a command that replaces state needs its own helper
  exactly like one that increments it.
- **These belong in the entrypoint or a core helper, not a new function:**
  if/elif dispatch, raises for an unknown operation or extra/missing
  arguments, empty or out-of-range guards on an already-parsed value,
  `helper(int(token))`, and a one-line format or read of existing state
  (`str(state)`, `f"value={state}"`, `state if operation == "get" else
  helper(...)`). Do not require `get` to go through a helper.
- **Each command owns its own helper, amount, and label.** Do not collapse two
  commands into one parameterized helper by computing the difference in the
  entrypoint:

  ```python
  amount = 1 if operation == "inc" else -1          # arithmetic mapping, and
  prefix = "up" if operation == "inc" else "down"   # label, both left in
  result = _change_counter(amount, prefix)          # the entrypoint
  ```

  Instead `_increment()` returns `f"up={_counter}"`, `_decrement()` returns
  `f"down={_counter}"`, and the entrypoint only dispatches:
  `result = _increment() if operation == "inc" else _decrement()`. Two helpers
  sharing a private one-line updater are fine.
- Do not leave parsing and core logic mixed in one monolithic function body.
- Logging prints are a separate skill; they never merge responsibilities.
  When a logging skill applies, the entry `print(...)` is still the first
  statement and the parse-helper call comes after it — printing is not
  parsing, so both rules hold.

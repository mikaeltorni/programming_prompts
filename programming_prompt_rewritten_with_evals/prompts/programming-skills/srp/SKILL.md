---
name: srp
description: >-
  Use whenever writing or editing Python (or other) code: enforce
  single-responsibility functions and methods. Apply on every coding task,
  including small scripts and new files from scratch.
---

# Single responsibility

Write code as single-responsibility functions/methods.

Concrete rules:
- Put input parsing of the raw command (split/tokenize/partition) in its own helper(s).
- Put core logic (arithmetic, state updates, business conversions) in
  its own helper(s). Helpers may return a one-line formatted result.
  `int()` / `float()` of an already-split token is not a business
  conversion.
- Keep the public entrypoint thin: parse → call helpers → return/format.
  if/elif dispatch, raises on unknown/extra/missing arguments, and a range
  check on an already-parsed value may live in the entrypoint or a core
  helper. A one-line format of already-computed state is fine, including a
  get branch that reads current state in the entrypoint (`str(state)` or
  `state if operation == "get" else helper(...)`). That is formatting, not
  a state update — do not require get to go through a helper.
  Do not leave increment, arithmetic, or state updates in the entrypoint —
  a format-only helper is not enough.
  `int()` of an already-split token and empty or out-of-range guards stay
  with the function that already owns that value; do not add a
  validation-only function for them. Passing `helper(int(token))` from the
  entrypoint is still thin — that is not leftover core conversion.
- Do not leave parsing and core logic mixed in one monolithic function body.
- **The entrypoint never takes the raw command string apart.** The only
  thing it may do with that string is hand it to the parse helper, in a
  single call, before it branches on anything; after that it dispatches
  only on what the helper returned. Calling `strip()`, `split()`,
  `startswith()`, `partition()`, slicing, or a regex on the raw command
  **inside the entrypoint** — even for a single `bye`/`period` branch — is
  mixed parsing and a failure. One parse helper covers **every** command
  variant; do not parse most of them in a helper and one special case
  inline.
  "Hands it to the parse helper first" is about **parsing work**, not about
  line order: printing a parameter is not parsing. When a logging skill also
  applies, that function's entry `print(...)` is the first statement in the
  body and the parse-helper call comes after it. Both rules hold together —
  never drop or delay the entry print to make the parse call come first.
- **The entrypoint does not build a computed result literal.** If a
  returned string like `f"hello={name}"` or `f"bye={name}"` needs a value
  the helpers derived, that formatting belongs to the helper that owns the
  logic. Only a plain read of existing state (`str(state)`,
  `f"value={state}"`) may be formatted in the entrypoint.
- Logging prints are a separate skill; they do not merge responsibilities.

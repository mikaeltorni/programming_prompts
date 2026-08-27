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
- Put core logic (arithmetic, state updates, conversions, business rules) in
  its own helper(s). Helpers may return a one-line formatted result.
- Keep the public entrypoint thin: parse → call helpers → return/format.
  if/elif dispatch, raises on unknown/extra/missing arguments, and a range
  check on an already-parsed value may live in the entrypoint or a core
  helper. A one-line format of already-computed state is fine.
  Do not leave increment, arithmetic, or state updates in the entrypoint —
  a format-only helper is not enough.
  `int()` of an already-split token and empty or out-of-range guards stay
  with the function that already owns that value; do not add a
  validation-only function for them.
- Do not leave parsing and core logic mixed in one monolithic function body.
- Logging prints are a separate skill; they do not merge responsibilities.

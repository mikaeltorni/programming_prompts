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
- Put input parsing of the raw command (split/tokenize) in its own helper(s).
- Put core logic (arithmetic, state updates, conversions, business rules) in
  its own helper(s). Helpers may return a one-line formatted result.
- Keep the public entrypoint thin: parse → call helpers → return/format.
  Dispatching with if/elif in the entrypoint is fine, including an
  unknown-operation `else` raise, a one-branch extra-arg check (for
  example `list` with an argument), or a missing required-argument check
  (`add` without text, `done` without an index). A core helper may also
  dispatch operations with if/elif (for example `_apply_operation`) —
  that is still that helper's job. A one-line format of
  already-computed state (for example `get` → `value=<n>`) is fine. Do not
  leave increment/arithmetic/state updates in the entrypoint — a
  format-only helper is not enough. Converting an already-split token with
  `int()` inside a state helper is still that helper's job. An empty or
  missing already-parsed argument guard inside a core helper (`if not
  text: raise`) is still that helper's job — do not require a separate
  validation-only function for it.
- Do not leave parsing and core logic mixed in one monolithic function body.
- Logging prints are a separate skill; they do not merge responsibilities.

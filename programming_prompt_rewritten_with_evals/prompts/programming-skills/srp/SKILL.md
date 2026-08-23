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
- Put input parsing/validation in its own helper(s).
- Put core logic (arithmetic, state updates, conversions, business rules) in
  its own helper(s). Helpers may return a one-line formatted result.
- Keep the public entrypoint thin: parse → call helpers → return/format.
  Dispatching with if/elif in the entrypoint is fine.
- Do not leave parsing and core logic mixed in one monolithic function body.
- Logging prints are a separate skill; they do not merge responsibilities.

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
  if/elif dispatch belongs in the entrypoint or a core helper such as
  `_apply_operation`, including unknown-operation `else` raises, extra-arg
  checks (`list` with an argument), and missing-arg checks (`add` without
  text, `done` without an index). A one-line format of already-computed
  state (`get` → `value=<n>`) is fine. Do not leave increment, arithmetic,
  or state updates in the entrypoint — a format-only helper is not enough.
  `int()` of an already-split token and `if not text: raise` inside a core
  helper stay that helper's job; do not add a validation-only function for
  them. A range check on an already-parsed value in the entrypoint
  (`hour` not in 0–23 after `_parse_command`) is still thin — same as a
  missing-arg raise. Do not add a validation-only helper just for it.
- Do not leave parsing and core logic mixed in one monolithic function body.
- Logging prints are a separate skill; they do not merge responsibilities.

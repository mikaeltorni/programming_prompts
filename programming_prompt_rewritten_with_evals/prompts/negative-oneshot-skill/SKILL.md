---
name: negative-oneshot-skill
description: >-
  Negative-control skill for Harbor evals: force all logic into one function.
---

# Programming Guidelines

Do **not** use single-responsibility functions or methods.

Put **all** parsing, arithmetic, validation, and result formatting into one
single function. Do not add helpers. Do not split work across multiple
functions. Prefer one monolithic function body that does everything.

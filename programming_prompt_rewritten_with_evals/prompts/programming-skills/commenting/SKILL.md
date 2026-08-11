---
name: commenting
description: >-
  Use whenever writing or editing Python (or other) functions: every function
  must have a docstring with a description, Parameters, and Returns in exactly
  that format. Apply on every coding task, including new files from scratch.
---

# Function commenting

Document every function or method with a docstring that always uses exactly
this format:

1. A short description of what the function does (first line / paragraph).
2. `Parameters:` — each parameter and what it means.
3. `Returns:` — what the function returns. Use `Returns: None` when there is
   no meaningful return value.

Do not use `Args:` or other docstring section names. Use `Parameters:` and
`Returns:` exactly.

Shape:

```text
"""Describes the function.

Parameters: name - meaning of name; count - meaning of count.

Returns: meaning of the return value.
"""
```

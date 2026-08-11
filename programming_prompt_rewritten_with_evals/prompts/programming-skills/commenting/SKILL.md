---
name: commenting
description: >-
  Use whenever writing or editing Python (or other) functions: every function
  must have a docstring that always documents the description, Args, and
  return values. Apply on every coding task, including new files from scratch.
---

# Function commenting

Document every function or method with a docstring that always includes:

1. A short description of what the function does.
2. `Args:` — each parameter name and what it means (include even for a single
   argument).
3. `Returns:` — what the function returns (type/meaning). Use `Returns: None`
   when the function returns nothing meaningful.

Do not leave public or helper functions undocumented. Prefer this shape:

```text
"""Description of the function.

Args:
    name: Meaning of name.
    count: Meaning of count.

Returns:
    Meaning of the return value.
"""
```

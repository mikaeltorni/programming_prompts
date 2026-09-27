---
name: commenting
description: >-
  v1.0.1 — Use whenever writing or editing Python (or other) functions: every
  function needs a description and same-line Parameters and Returns labels.
  Apply on every coding task, including new files.
---

# Function docstrings

Give every `def`, `async def`, and method a docstring with:

1. A short description.
2. `Parameters:` followed on that line by every parameter and its meaning.
   For a function with no parameters, write `Parameters: none` or
   `Parameters: None`. A trailing period is fine.
3. `Returns:` followed on that line by the return meaning. Use
   `Returns: None` when there is no meaningful return.

A long parameter list may continue on later lines once the `Parameters:`
line has content. Do not use `Args:` or leave either label on a line alone.
`lambda` expressions do not need docstrings.

Example:

```text
"""Return the updated count.

Parameters: value - amount to add; count - current count.

Returns: the updated count.
"""
```

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

1. A short description of what the function does.
2. One line starting with `Parameters:` listing each parameter and meaning
   (`Parameters: none` or `Parameters: None` when there are no parameters).
3. One line starting with `Returns:` describing the return value
   (`Returns: None` when there is no meaningful return).

Do not use `Args:` or other section names. Do not put `Parameters:` or
`Returns:` on a line by themselves. A long parameter list may continue on
the next line after the label already has content.

Match this layout exactly:

```text
"""Describes the function.

Parameters: name - meaning of name; count - meaning of count.

Returns: meaning of the return value.
"""
```

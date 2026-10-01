---
name: commenting
description: >-
  v1.0.3 — Use whenever writing or editing Python (or other) functions: every
  function, including authored tests and fixtures, needs a description and
  same-line Parameters and Returns labels. Apply on every coding task.
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

The same contract applies to agent-authored test code: test methods, fixtures,
setup/teardown methods, and assertion helpers are functions too. A test's short
description alone is insufficient. Include `self` / `cls` in the parameter
meanings when present, and use `Returns: None` for an assertion-only method.
Inspect every changed Python file, including tests, before committing; reviewing
only the program file leaves the test functions unchecked.

Before each code commit, inspect every `def` and method in the changed source,
including helpers added for the latest command. Add all three required
docstring parts in that Feature's commit; recheck after later edits rather than
relying on a previous Feature's docstring review. The README documentation
phase does not replace this code-level check.

Example:

```text
"""Return the updated count.

Parameters: value - amount to add; count - current count.

Returns: the updated count.
"""
```

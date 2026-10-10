---
name: commenting
description: >-
  v1.0.6 — Use whenever writing or editing Python (or other) functions: every
  function, including authored tests and fixtures, needs a description and
  same-line Parameters and Returns labels. Apply on every coding task.
---

# Function docstrings

Every function or method you create or edit, including tests, fixtures and
helpers, needs a docstring with:

- A short description of its purpose.
- `Parameters:` followed on the same line by each parameter and its meaning.
  Include `self`/`cls`; use `Parameters: none` for a parameterless function.
- `Returns:` followed on the same line by the return meaning, or `Returns: None`.

A long parameter list may continue after that first line has content. Blank
lines between sections and a trailing period are fine. `Args:` and labels
whose content starts on the next line do not satisfy this format. Lambdas are
exempt.

Write the complete docstring with the function's first saved draft. Before
committing, review the functions in every changed source and test file;
passing assertions do not verify their documentation.

```python
def updated_count(value, count):
    """Return the updated count.

    Parameters: value - amount to add; count - current count.
    Returns: the updated count.
    """
    print(f"value={value}, count={count}")
    result = count + value
    print(result)
    return result
```

The prints illustrate compatibility with selected logging; commenting alone
does not require them.

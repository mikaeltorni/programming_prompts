---
name: logging
description: >-
  v1.0.10 — Every authored function, test and fixture prints parameters first
  after its docstring, before helper calls, validation or declarations, and
  prints each normal return value. Use plain print(), with no logging modules or log files.
---

# Function entry and exit prints

Every function or method you create or edit, including constructors, tests,
fixtures and private helpers, uses builtin `print()` for its own entry and
normal exits. Lambdas and exception exits are exempt. Use no logging framework,
custom logger or log files.

The first statement after the docstring prints every parameter's actual name
and value, including optional `None` values and receivers `self`/`cls`. Put this
print before parsing, validation, helper calls and `global`/`nonlocal`
declarations. A function with no parameters may print `parameters=none`.
A constructor with `self` is not parameterless; `object.__repr__(self)` safely
identifies it without reading uninitialized fields or recursing through a
custom representation.

Immediately before each normal return, print its complete value. For a tuple,
print all elements or the tuple itself. Before normal fallthrough, print `None`,
including at the end of constructors and assertion-only tests. A final
`print(None)` needs no additional `return None`. Nothing is required before
`raise`.

A helper's prints do not cover its caller. Assign the result of `helper()`,
print it, then return it rather than returning the call directly. Branches
may converge on one print and return. Test entry prints precede stdout capture,
and the exit print follows the last assertion.

```python
def update(value):
    """Replace stored state.

    Parameters: value - the new state.
    Returns: the stored state.
    """
    print(f"value={value}")
    global stored_state
    stored_state = value
    print(stored_state)
    return stored_state
```

Before committing, compare every changed function's signature with its first
statement and inspect each reachable normal exit, in application and test files.

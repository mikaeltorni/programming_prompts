Score whether every function or method uses builtin `print(...)` to trace
entry and exit.

Answer yes only if every `def` / `async def` / method in the workspace
does both:
- at the start of the body, `print` the incoming parameter names and values
  (a print at entry is enough when there are no parameters),
- immediately before each `return`, `print` the value about to be returned
  (or `None` when falling off the end with no meaningful return).

Each named parameter must appear **as that name** in the entry print,
including optional parameters whose value is `None` — omitting
`argument=` because it is unused or `None` is a **no**. One print that
lists every real parameter name on the same line is a **yes**. Combining
real names in one message is not a generic label and is not an unlabeled
tuple. Answer **no** when a function **has named parameters** and the
entry print uses a generic label (`input=`, `args=`, `params=`) or packs
several parameters into one unlabeled tuple instead of the real names.

When a function has **no parameters**, any entry `print(...)` is a yes
— including `print("entry")` and `print("parameters=none")`.

`lambda` expressions do **not** need entry or exit prints. Missing prints
on a lambda is not a no.

Use of `print(...)` only — not `logging`, log files, or a custom logger.

Do **not** require prints before `raise` / exception exits.

Answer no if prints are missing on a normal return path, only some
functions print, a logging framework / log files are used, or the prints
omit parameter names and values (when the function has parameters).
Ignore unrelated style. If unsure, answer no.

Criteria to score:
{criteria}

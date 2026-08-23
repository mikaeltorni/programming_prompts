Score whether the Python uses single-responsibility functions/methods.

Answer yes when ALL of these hold:
- input parsing/validation lives in its own helper(s),
- core logic (arithmetic, state change, or conversion) lives in its own
  helper(s), not in the public entrypoint,
- the public entrypoint is thin: parse → call helpers → return/format.

A thin entrypoint may dispatch with if/elif and return what the helpers
produced. It may also format already-computed state in one line (for
example a `get` branch that returns `value=<n>` or `str(counter)`).
Core-logic helpers may return a one-line formatted result (for example
`added=1`). Converting an already-split token with `int()` / `float()`
inside a state helper is still core logic, not mixed parsing. A
format-only helper does not count as extracting core logic if the
entrypoint still increments or does the real arithmetic. Logging prints
are scored by the logging skill — they are not an SRP failure.

Answer no when any of these hold:
- parsing/validation and core logic still share one function body,
- the entrypoint still performs core arithmetic or state changes itself
  (beyond one-line formatting of an existing value),
- there is no parse/validation helper,
- there is no core-logic helper.

Ignore API wording. If unsure, answer no.

Criteria to score:
{criteria}

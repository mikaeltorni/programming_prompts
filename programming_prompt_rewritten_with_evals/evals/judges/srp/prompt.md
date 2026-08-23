Score whether the Python uses single-responsibility functions/methods.

Answer yes when ALL of these hold:
- input parsing/validation lives in its own helper(s),
- core logic (arithmetic, state change, or conversion) lives in its own
  helper(s), not in the public entrypoint,
- the public entrypoint is thin: parse → call helpers → return/format.

A thin entrypoint may dispatch with if/elif and return what the helpers
produced. Core-logic helpers may return a one-line formatted result (for
example `added=1`). A format-only helper does not count as extracting core
logic if the entrypoint still increments, converts, or otherwise does the
real work. Logging prints are scored by the logging skill — they are not an SRP failure.

Answer no when any of these hold:
- parsing/validation and core logic still share one function body,
- the entrypoint still performs core arithmetic, state changes, or
  conversions itself,
- there is no parse/validation helper,
- there is no core-logic helper.

Ignore API wording. If unsure, answer no.

Criteria to score:
{criteria}

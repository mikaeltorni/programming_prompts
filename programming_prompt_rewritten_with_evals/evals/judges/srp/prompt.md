Score whether the Python uses single-responsibility functions/methods.

Answer yes when ALL of these hold:
- input parsing/validation lives in its own helper(s),
- core logic (arithmetic, state change, or conversion) lives in its own
  helper(s), not in the public entrypoint,
- the public entrypoint is thin: parse → call helpers → return/format.

A thin entrypoint may dispatch with if/elif and return what the helpers
produced. It may also format already-computed state in one line (for
example a `get` branch that returns `value=<n>` or `str(counter)`).
Raising from a dispatch branch is still thin: unknown operation in
`else`, extra args on one verb (for example `list` with an argument),
or a missing required argument (`add` without text, `done` without an
index). Those raises are not mixed parsing. A core helper may also
dispatch operations with if/elif (for example `_apply_operation`) —
that is still one responsibility (state/arithmetic), not mixed parsing.
When parse lives in its own helper and the entrypoint is thin, answer
yes; do not score conservatively because the core helper also
dispatches or validates already-parsed arguments. Core-logic helpers may
return a one-line formatted result (for example `added=1`). Converting
an already-split token with `int()` / `float()` inside a state helper is
still core logic, not mixed parsing. An empty or missing already-parsed
argument guard inside a core helper (`if not text: raise`) is still
that helper's job — do not require a separate validation-only function.
A format-only helper does not count as extracting core logic if the
entrypoint still increments or does the real arithmetic. Logging prints
are scored by the logging skill — they are not an SRP failure.

Answer no when any of these hold:
- splitting/tokenizing the raw command and core arithmetic/state still
  share one function body,
- the entrypoint still performs core arithmetic or state changes itself
  (beyond one-line formatting of an existing value),
- there is no parse/validation helper,
- there is no core-logic helper.

Ignore API wording. If unsure, answer no.

Criteria to score:
{criteria}

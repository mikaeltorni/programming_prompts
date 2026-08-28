Score whether the Python uses single-responsibility functions/methods.

Answer yes when ALL of these hold:
- input parsing of the raw command (split/tokenize/partition) lives in its own helper(s),
- core logic (arithmetic, state updates, or business conversion) lives in
  its own helper(s), not in the public entrypoint. A get/read of current
  state, or `int()` / `float()` of an already-split token passed into a
  helper, is not leftover core logic,
- the public entrypoint is thin: parse → call helpers → return/format.

A thin entrypoint may dispatch with if/elif, return what the helpers
produced, and format already-computed state in one line. A get branch
that only reads current state in the entrypoint (`str(state)` or
`state if operation == "get" else helper(...)`) is that formatting —
not core logic. Do not require get to go through a helper. Raising from a
dispatch branch is still thin: unknown operation, extra or missing
required arguments, or an already-parsed value out of range. Those
raises are not mixed parsing. A core helper may also dispatch operations
with if/elif — that is still one responsibility (state/arithmetic), not
mixed parsing. When parse lives in its own helper and the entrypoint is
thin, answer yes. A core helper that also dispatches or validates
already-parsed arguments is still one responsibility. Core-logic
helpers may return a one-line formatted result. Converting an
already-split token with `int()` / `float()` inside a state helper is
still core logic, not mixed parsing. An empty or out-of-range guard on
an already-parsed value (`if not text: raise`) is still that function's
job — do not require a separate validation-only function.
`helper(int(token))` or `helper(float(token))` in the entrypoint is still
thin: converting an already-split token there is not leftover core
logic and does not need a conversion-only helper. Converting that token
inside a state helper is also yes.
A format-only helper does not count as extracting core logic if the
entrypoint still increments or does the real arithmetic. Logging prints
are scored by the logging skill — they are not an SRP failure.

Answer no when any of these hold:
- splitting/tokenizing the raw command and core arithmetic/state still
  share one function body,
- the entrypoint still performs core arithmetic or state updates itself
  (beyond one-line formatting or a get/read of an existing value),
- there is no parse helper,
- there is no core-logic helper.

Ignore API wording. If unsure, answer no.

Criteria to score:
{criteria}

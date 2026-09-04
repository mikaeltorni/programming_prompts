Score whether the Python uses single-responsibility functions/methods.

Answer yes when ALL of these hold:
- input parsing of the raw command (split/tokenize/partition) lives in its
  own helper(s),
- core logic (arithmetic, state updates, or business conversion) lives in its
  own helper(s), not in the public entrypoint,
- the public entrypoint is thin: parse → call helpers → return/format.

A thin entrypoint may dispatch with if/elif, return what the helpers
produced, and format already-computed state in one line — including a get
branch that only reads current state (`str(state)` or
`state if operation == "get" else helper(...)`). Do not require get to go
through a helper. A raise from a dispatch branch is still thin: unknown
operation, extra or missing required arguments, or an already-parsed value
out of range — those raises are not mixed parsing.

`int()` / `float()` of an already-split token is never core logic: it is
thin in the entrypoint when the converted value goes straight into the call
(`helper(int(token))`), and still core logic, not mixed parsing, inside a
state helper. Arithmetic on that converted value (`int(token) - 1`),
validating it against current state, or assigning it into state
(`_total = int(token)`) in the entrypoint is core logic, not a conversion.

A core helper may itself dispatch operations with if/elif, validate
already-parsed arguments, guard empty or out-of-range values
(`if not text: raise`), and return a one-line formatted result — that is
still one responsibility, and no separate validation-only or
conversion-only function is required.

Logging prints are scored by the logging skill — they are not an SRP failure.
Ignore API wording.

Answer no when any of these hold:
- splitting/tokenizing the raw command and core arithmetic/state still share
  one function body,
- the entrypoint still performs core arithmetic or state updates itself —
  including choosing a command's operand or label there
  (`amount = 1 if operation == "inc" else -1`) — beyond one-line formatting
  or a get/read of an existing value; a format-only helper does not count as
  extracting the core logic,
- there is no parse helper,
- there is no core-logic helper.

If unsure, answer no.

Criteria to score:
{criteria}

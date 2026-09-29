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
operation, extra or missing required arguments, or an already-parsed input
format value out of range (such as an hour outside 0..23) — those raises are
not mixed parsing. In particular, rejecting an hour outside 0..23 is an
allowed format guard even when it follows int() conversion in the entrypoint;
do not fail that guard as domain validation. A narrower business range or
classification is operation logic and belongs in its helper. A format guard
checks representability, not whether an operation accepts that value. The
clock-hour allowance does not permit a business-specific subset of valid hours
in the entrypoint, even when the helper repeats the same check. Before a yes,
inspect each entrypoint comparison and distinguish format validity from the
operation's acceptable values; cite any rejected domain value as core work.
Domain validation belongs to the operation helper: a bank
amount being negative, an account being absent or duplicated, and an
insufficient balance are business rules. Checking those in the entrypoint is
core work even after int() conversion.

`int()` / `float()` of an already-split token is never core logic: it is
allowed in the parse helper, or thin in the entrypoint when the converted
value is passed unchanged to a helper (`helper(int(token))` or
`value = int(token); helper(value)`). Handling a failed numeric conversion in
the parse helper does not mix parsing with business logic. Dispatching to distinct
arithmetic helpers with if/elif is thin even after those local conversions.
Choosing `_deposit(...)` versus `_withdraw(...)` by parsed operation is
ordinary dispatch, not choosing a business operand or label.
Arithmetic on that converted value (`int(token) - 1`),
validating it against current state or a domain constraint (such as a negative
bank amount), or assigning it into state
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

For a no verdict, identify the exact function and core work left in it.

Criteria to score:
{criteria}

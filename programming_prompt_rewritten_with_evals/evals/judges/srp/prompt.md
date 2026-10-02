Score whether the Python uses single-responsibility functions/methods and keeps
the code simple through focused changes at the requested revision boundaries.

Answer yes when ALL of these hold:
- input parsing of the raw command (split/tokenize/partition) lives in its
  own helper(s),
- core logic (arithmetic, state updates, or business conversion) lives in its
  own helper(s), not in the public entrypoint,
- the public entrypoint is thin: parse → call helpers → return/format,
- requested revisions preserve those responsibilities and avoid unnecessary
  churn, as detailed below; a final-file-only assessment is insufficient for
  an incremental task.

At the public boundary, one shared parse call supplies the operation selector
and parsed arguments before dispatch between command variants. A single-operation
slice with no variant dispatch may return only its arguments; do not demand an
unused operation key. Parsing may compose smaller helpers internally; do
not fail merely because several helpers exist or a parser lacks "parse" in its
name. A public entrypoint that first calls a kind-only raw-command classifier,
then passes the same raw command to additional parsers after branching, has not
established this shared parsing boundary. Cite those calls in a no verdict;
judge the actual data flow, not whether a function is called a dispatch helper.

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

Also assess churn when the task modifies existing behavior. Inspect the actual
Git diffs and before/after source, including the supplied seed when present,
against the original request; do not infer preservation from the final file,
commit subjects, or the agent's claim alone.

A passing change extends the existing command routing path, keeps working names,
interfaces and unrelated functions when they still fit, and confines edits to
the behavior and necessary integrations, checks or documentation. Extracting a
new responsibility or shared logic is justified even when it touches several
files. Do not reward a small diff that leaves mixed responsibilities or copied
logic, and do not require identical text, a line-count budget, or an arbitrary
number of functions/files.

Answer no for a concrete unnecessary rewrite, unrelated renaming/reformatting,
parallel parser, duplicated operation, speculative framework or pass-through
layer. Cite the changed function/block and explain why the original request
did not require it. Verify that earlier public behavior remains supported
except where intentionally changed; a failed operation must not corrupt state.
Missing history or inaccessible source is missing evidence, not proof of bad
code; report that limitation instead of inventing churn. The supplied Git graph,
diffs and source snapshots are read-only inspection evidence. Use them directly
when complete, or obtain omitted source with the supplied Git evidence helper.
Do not claim history is absent just because it is not in the final-file listing.
For a pass on an incremental task, cite an earlier and later source revision and
the concrete edits that kept their responsibilities focused; final structure
alone cannot establish low churn.

For tasks that specify incremental growth, inspect the working source at the
requested stage boundaries as well as the final source. The initial slice
should implement the current capability simply, with a parsing path, focused
core helpers and a thin entrypoint; later changes should evolve that working
code. Each slice must retain earlier contracts unless the next requirement
explicitly revises them. Use executed public-entrypoint examples when available
to check preservation; a claimed check alone is not behavioral evidence.

Fail concrete cases of building later capabilities ahead of the requested
stage, repeatedly replacing unrelated working helpers, accumulating dead
branches or speculative layers, or leaving mixed responsibilities until a
final cleanup. A local extraction, a new focused helper, or removing logic
made obsolete by a requested revision is appropriate. Judge responsibility
and necessary changes, not a fixed function length or helper count. Apply
stage-order requirements only when the original request or selected skills
specify them; this rubric does not mandate extra commits for other tasks.

Criteria to score:
{criteria}

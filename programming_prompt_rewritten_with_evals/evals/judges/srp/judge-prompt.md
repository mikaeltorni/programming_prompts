Score whether the Python uses single-responsibility functions/methods.

Answer yes only if:
- parsing/input handling is in its own helper(s), AND
- core logic (operator/command selection, arithmetic, state updates, conversions)
  is in its own helper(s), AND
- the public entrypoint mainly orchestrates (call helpers, return).

Answer no if the entrypoint still chooses operators/commands, runs the core
logic, or formats the main result itself — even when a small helper exists
(for example only `_parse_number` while `run_*` still does validation,
dispatch, arithmetic, and formatting).

Ignore exact return-string wording and task API details. Judge structure only.
If unsure, answer no.

Criteria to score:
{criteria}

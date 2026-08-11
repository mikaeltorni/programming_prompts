Score whether the Python uses single-responsibility functions/methods.

Answer yes if parsing/input handling and core logic live in separate helpers
and the public entrypoint mainly orchestrates them (call helpers, return).

Answer no only if one function still mixes parsing and core logic in the same
body with no real helpers.

Ignore return-string formatting, API wording, and whether the program matches
the task examples exactly. Judge structure only. If unsure, answer no.

Criteria to score:
{criteria}

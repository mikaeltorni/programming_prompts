Score whether the Python uses single-responsibility functions/methods.

Answer yes when there is a parse/validation helper, at least one separate
core-logic helper (arithmetic, conversion, or state change), and a thin
public entrypoint. A thin entrypoint may dispatch with if/elif and return
what the helpers produced. Core-logic helpers may return a one-line
formatted result (for example `added=1`). Logging prints are scored by the
logging skill — they are not an SRP failure.

Answer no only if parsing/validation and core logic still live in one
monolithic function, or the entrypoint still does the real work itself
(validates, computes, and formats) with only a tiny helper such as
`_parse_number`.

Ignore API wording. If unsure, answer no.

Criteria to score:
{criteria}

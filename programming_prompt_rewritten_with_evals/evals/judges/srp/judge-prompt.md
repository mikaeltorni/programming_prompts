Score whether the Python uses single-responsibility functions/methods.

Answer yes if there is a parse helper and a separate core-logic helper
(arithmetic, conversion, or state change), and the entrypoint mostly calls
those helpers. A thin entrypoint may dispatch with if/elif and return a
one-line formatted result.

Answer no if the entrypoint still does the real work itself — especially when
only a tiny helper like `_parse_number` exists and the entrypoint still validates,
dispatches, computes, and formats.

Ignore API wording. If unsure, answer no.

Criteria to score:
{criteria}

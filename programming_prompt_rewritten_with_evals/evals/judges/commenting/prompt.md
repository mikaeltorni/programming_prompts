Score whether every function docstring uses this format:

1. a short description,
2. a `Parameters:` label,
3. a `Returns:` label.

Answer yes if those exact labels are present (wrapped parameter text after
`Parameters:` is fine). Answer no only if a docstring is missing, or it uses
`Args:` / other labels instead of `Parameters:` and `Returns:`.
Do not fail for unrelated code behavior. If unsure, answer no.

Criteria to score:
{criteria}

Score whether every function or method docstring uses this format:

1. a short description,
2. a `Parameters:` label with the parameter list on that same line
   (`Parameters: none` when there are no parameters),
3. a `Returns:` label with the return meaning on that same line
   (`Returns: None` when there is no meaningful return).

Answer yes only if every function has that docstring. The labels must stay
on the same line as their content, matching the skill example.

Answer no if any function is missing a docstring, uses `Args:` or other
section names, omits the description, or uses Google/NumPy wrapping where
`Parameters:` or `Returns:` sits on its own line with text underneath.

Do not fail for unrelated code behavior. If unsure, answer no.

Criteria to score:
{criteria}

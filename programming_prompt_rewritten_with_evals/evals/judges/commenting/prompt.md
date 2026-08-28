Score whether every function or method docstring uses this format:

1. a short description,
2. a `Parameters:` label with the parameter list starting on that same line
   (`Parameters: none` or `Parameters: None` when there are no parameters),
3. a `Returns:` label with the return meaning starting on that same line
   (`Returns: None` when there is no meaningful return).

Answer yes only if every `def` / `async def` / method has that docstring.
`lambda` expressions do **not** need docstrings — missing docs on a lambda
is not a no. The labels must start
on the same line as their content. A long parameter list that continues on
the next line after `Parameters:` already has content is still a yes. A
blank line between the description and the `Parameters:` line is required
by the skill example and is a yes. Capitalization of `none` / `None` after
`Parameters:` does not matter.

Answer no if any `def` / `async def` / method is missing a docstring, uses
`Args:` or other section names, omits the description, or uses Google/NumPy
style where `Parameters:` or `Returns:` sits on its own line with the text
on the following line. Do not treat a lambda as a missing-docstring no.

Do not fail for unrelated code behavior. If unsure, answer no.

Criteria to score:
{criteria}

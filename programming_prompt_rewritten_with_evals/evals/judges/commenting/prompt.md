Score whether every function or method docstring uses this format:

1. a short description,
2. a `Parameters:` label with the parameter list starting on that same line
   (`Parameters: none` or `Parameters: None` when there are no parameters),
3. a `Returns:` label with the return meaning starting on that same line
   (`Returns: None` when there is no meaningful return).

Answer yes only if every `def` / `async def` / method has that docstring.
The labels must start on the same line as their content; a long parameter
list that continues on the next line, after `Parameters:` already has
content, is still a yes.
A blank line between the description and the `Parameters:` line matches the
skill example and is a yes. Capitalization of `none` / `None` after
`Parameters:` does not matter.

`lambda` expressions do **not** need docstrings — missing docs on a lambda
is not a no.

Answer no if any `def` / `async def` / method is missing a docstring, uses
`Args:` or other section names, omits the description, or uses Google/NumPy
style where `Parameters:` or `Returns:` sits on its own line with the text
on the following line.

Do not fail for unrelated code behavior. If unsure, answer no.
Before a no verdict, name a concrete function and the missing or malformed
docstring element. If inspection finds every function compliant, answer yes;
a reason concluding that the score is yes cannot accompany a no score.

Criteria to score:
{criteria}

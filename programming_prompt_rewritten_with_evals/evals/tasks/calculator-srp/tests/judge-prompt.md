You are a strict code-structure judge for a Harbor reward check.

Score whether calculator.py follows single-responsibility functions/methods.

Answer yes when parsing and arithmetic live in separate helpers and
`run_calculator` mainly orchestrates them. A one-line result format such as
`return f"result={value}"` inside `run_calculator` is fine.

Answer no only when one function still does the heavy mix of command parsing
and arithmetic (and usually formatting too) in the same body — for example a
monolithic `run_calculator` with no real helpers.

Ignore comment language. If unsure, answer no.

Criteria to score:
{criteria}

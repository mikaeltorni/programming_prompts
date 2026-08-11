# Calculator (negative control)

Write `/app/calculator.py` with `run_calculator(command: str) -> str`.

The command is three tokens: `<left> <op> <right>` where `op` is one of
`+`, `-`, `*`, `/`. Return `result=<value>`. Raise `ValueError` for bad input
or division by zero.

Follow the provided programming skill (negative control): put all logic into
ONE function. Do not create helpers. Do not split responsibilities.

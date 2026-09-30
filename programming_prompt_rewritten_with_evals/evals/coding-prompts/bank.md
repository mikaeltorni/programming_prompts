---
artifact: /app/bank.py
description: Grow a bank ledger by revising amounts and extending transfers and history.
---
Follow every provided programming skill. Write `/app/bank.py` with `run_bank(command: str) -> str`.

Implement the capability sentences below in order, starting from a small working
program and editing it at each later stage. Execute the current stage checks
through the public entrypoint, then commit the working revision before starting
the next stage; follow selected delivery skills when present. Later commands
must not work in an earlier revision. Stage checks are verification examples,
not additional capability sentences. Keep earlier behavior except where a later
sentence explicitly replaces it. Each check sequence starts with a freshly
imported module and runs left to right in one process; state persists between
calls in that sequence, not across source revisions. Names are single tokens.
Empty/unknown commands, invalid argument shapes, unknown accounts and rejected
operations raise `ValueError` without changing balances or history. Numeric
results use compact decimal formatting without an unnecessary `.0`.

### Initial working slice

A bank should open accounts (`open <name>` returns `opened=<name>`, balance zero, refusing a duplicate name with a `ValueError`).

Stage checks:
- `open ada` → `opened=ada`; `open ada` raises `ValueError`; `open ben` → `opened=ben`.
- `deposit ada 4`, `transfer ada ben 1`, and `history ada` raise `ValueError`.

### Extend account operations

It should also accept positive whole-number deposits and withdrawals (`deposit <name> <amount>` and `withdraw <name> <amount>` both return `balance=<value>`, refusing an overdraft or a fractional amount with a `ValueError`).

Stage checks:
- `open ada` → `opened=ada`; `deposit ada 5` → `balance=5`; `withdraw ada 2` → `balance=3`.
- `withdraw ada 4`, `deposit ada -1`, and `deposit ada 0.5` raise `ValueError`; `deposit ada 1` → `balance=4`.

### Revise the existing amount rule

It should also extend deposits and withdrawals to positive decimal amounts while preserving whole-number input, overdraft protection and the existing result formats.

Stage checks:
- `open ada` → `opened=ada`; `deposit ada 5.5` → `balance=5.5`; `withdraw ada 0.5` → `balance=5`; `deposit ada 2` → `balance=7`.
- `withdraw ada 7.5` and `deposit ada 0` raise `ValueError`; `withdraw ada 1` → `balance=6`.

### Extend transfers

It should also transfer positive whole-number amounts between different existing accounts (`transfer <from> <to> <amount>` returns `moved=<amount>`, refusing a fractional amount, overdraft or same-account transfer with a `ValueError`).

Stage checks:
- `open ada` → `opened=ada`; `open ben` → `opened=ben`; `deposit ada 5.5` → `balance=5.5`; `transfer ada ben 2` → `moved=2`; `withdraw ben 1` → `balance=1`.
- `transfer ada ben 0.5`, `transfer ada missing 1`, and `transfer ada ada 1` raise `ValueError`; `withdraw ada 0.5` → `balance=3`.

### Revise transfers through their existing path

It should also extend transfers to positive decimal amounts while preserving whole-number transfers, both account balances on failure, and the existing deposit and withdrawal behavior.

Stage checks:
- `open ada` → `opened=ada`; `open ben` → `opened=ben`; `deposit ada 5.5` → `balance=5.5`; `transfer ada ben 0.5` → `moved=0.5`; `transfer ada ben 2` → `moved=2`.
- `transfer ada missing 1`, `transfer ada ben 9`, and `transfer ada ben -1` raise `ValueError`; `withdraw ada 1` → `balance=2`; `withdraw ben 0.5` → `balance=2`.

### Extend history around the working operations

It should also report one account's applied changes (`history <name>` returns `history=<comma-separated>` of `+<amount>` and `-<amount>` entries, oldest first, including both sides of transfers and no entries for failed operations, with an empty suffix when none) and may report the bank total (`assets` returns `assets=<sum>`).

Stage checks:
- `open ada` → `opened=ada`; `open ben` → `opened=ben`; `history ada` → `history=`; `deposit ada 5.5` → `balance=5.5`; `transfer ada ben 0.5` → `moved=0.5`; `withdraw ben 0.25` → `balance=0.25`.
- `transfer ada missing 1` and `withdraw ada 9` raise `ValueError`; `history ada` → `history=+5.5,-0.5`; `history ben` → `history=+0.5,-0.25`.
- If `assets` is implemented: `assets` → `assets=5.25`; `transfer ada ben 1` → `moved=1`; `assets` → `assets=5.25`.

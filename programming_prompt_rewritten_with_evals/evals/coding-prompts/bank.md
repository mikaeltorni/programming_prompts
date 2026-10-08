---
artifact: /app/bank.py
description: Grow a bank ledger by revising amounts and extending transfers and history.
---
Follow every provided programming skill. Write `/app/bank.py` with `run_bank(command: str) -> str`.

Shared contract: names are single tokens; balances and history persist across calls in one process, starting empty. Empty or unknown commands, invalid operand counts, unknown accounts, and rejected operations raise `ValueError` without changing balances or history. Numeric output uses compact decimal formatting without an unnecessary `.0`. Later capability sentences replace only their stated rules; all other behavior remains.

A bank should open accounts (`open <name>` returns `opened=<name>`, balance zero, refusing a duplicate name with a `ValueError`).

It should also accept positive whole-number deposits and withdrawals (`deposit <name> <amount>` and `withdraw <name> <amount>` both return `balance=<value>`, refusing an overdraft or a fractional amount with a `ValueError`).

It should also extend deposits and withdrawals to positive decimal amounts while preserving whole-number input, overdraft protection and the existing result formats.

It should also transfer positive whole-number amounts between different existing accounts (`transfer <from> <to> <amount>` returns `moved=<amount>`, refusing a fractional amount, overdraft or same-account transfer with a `ValueError`).

It should also extend transfers to positive decimal amounts while preserving whole-number transfers, both account balances on failure, and the existing deposit and withdrawal behavior.

It should also report one account's applied changes (`history <name>` returns `history=<comma-separated>` of `+<amount>` and `-<amount>` entries, oldest first, including both sides of transfers and no entries for failed operations, with an empty suffix when none) and may report the bank total (`assets` returns `assets=<sum>`).

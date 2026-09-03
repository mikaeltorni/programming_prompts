---
artifact: /app/bank.py
features: 4
description: Write a tiny bank ledger; open, then deposit/withdraw, then transfer, then history.
---
Follow every provided programming skill. Write `/app/bank.py` with `run_bank(command: str) -> str`.
A bank should open accounts (`open <name>` returns `opened=<name>`, balance 0, refusing a duplicate name with a `ValueError`).
It should also take deposits and withdrawals (`deposit <name> <amount>` and `withdraw <name> <amount>` both → `balance=<value>`, refusing an overdraft with a `ValueError`).
It should also move money between two accounts (`transfer <from> <to> <amount>` → `moved=<amount>`).
It should also report one account's applied changes (`history <name>` → `history=<comma-separated>` of `+<amount>` / `-<amount>` entries, oldest first, empty string when none) and may report the bank total (`assets` → `assets=<sum>`).

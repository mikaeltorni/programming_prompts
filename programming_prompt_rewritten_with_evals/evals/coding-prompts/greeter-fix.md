---
artifact: /app/greeter.py
features: 3
description: Fix a broken greeter from logs, then add farewell and period.
---
Follow every provided programming skill. The greeter at `/app/greeter.py` is broken.
Logs under `.log/` record the failure. Fix `run_greeter(command: str) -> str` for `<name> <hour>`.
It should also farewell (`bye <name>` returns `bye=<name>`) and report a period (`period <hour>` returns `period=<phrase>`).

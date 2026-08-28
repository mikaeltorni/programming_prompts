---
artifact: /app/greeter.py
features: 3
description: Fix a broken greeter from logs, then farewell, then period.
---
Follow every provided programming skill. The greeter at `/app/greeter.py` is broken.
Logs under `.log/` record the failure. Fix `run_greeter(command: str) -> str` for `<name> <hour>` so it matches the `want:` line.
It should also farewell (`bye <name>` returns `bye=<name>`).
It should also report a period (`period <hour>` returns `period=<phrase>`).

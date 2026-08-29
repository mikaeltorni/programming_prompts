---
artifact: /app/shop.py
features: 3
description: Write a tiny shop; catalog, then total, then remove.
---
Follow every provided programming skill. Write `/app/shop.py` with `run_shop(command: str) -> str`.
A shop should record catalog items (`add <name> <price>` returns `added=<name>`).
It should also check out (`total` → `total=<sum>`).
It should also remove an item (`remove <name>` → `removed=<name>`) and may count items (`count` → `count=<n>`).

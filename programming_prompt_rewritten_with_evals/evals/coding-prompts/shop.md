---
artifact: /app/shop.py
features: 4
description: Write a tiny shop; catalog, then total, remove, and count.
---
Follow every provided programming skill. Write `/app/shop.py` with `run_shop(command: str) -> str`.
A shop should record catalog items (`add <name> <price>` returns `added=<name>`).
It should also check out (`total` → `total=<sum>`), remove an item (`remove <name>` → `removed=<name>`), and count items (`count` → `count=<n>`).

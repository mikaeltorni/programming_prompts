---
artifact: /app/stats.py
features: 4
description: Write a tiny stats collector; add, then mean, then low/high, then median.
---
Follow every provided programming skill. Write `/app/stats.py` with `run_stats(command: str) -> str`.
A stats collector should record samples (`add <number>` returns `count=<n>` samples so far).
It should also average them (`mean` → `mean=<value>`, refusing an empty sample set with a `ValueError`).
It should also report the extremes (`low` → `low=<value>` and `high` → `high=<value>`).
It should also report the middle value (`median` → `median=<value>`, the mean of the two middle samples when the count is even) and may drop every sample (`reset` → `cleared=<n>`).

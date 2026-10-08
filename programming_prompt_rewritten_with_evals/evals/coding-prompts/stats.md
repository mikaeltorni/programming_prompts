---
artifact: /app/stats.py
description: Grow a stats collector by revising sample inputs and mean precision.
---
Follow every provided programming skill. Write `/app/stats.py` with `run_stats(command: str) -> str`.

Shared contract: samples persist across calls in one process, starting empty. Empty or unknown commands, invalid operand counts, invalid numeric tokens, and queries of an empty sample set raise `ValueError` without changing samples. Numeric output uses compact decimal formatting without an unnecessary `.0`. Later capability sentences replace only their stated rules; all other behavior remains.

A stats collector should record whole-number samples (`add <number>` returns `count=<n>` samples so far, accepting negative and zero values but refusing fractional values with a `ValueError`).

It should also average the samples (`mean` returns `mean=<value>`, initially truncating the result toward zero to a whole number).

It should also extend `add` to decimal samples while retaining whole-number, zero and negative input, the current count format and the current truncated mean behavior.

It should also report the extremes (`low` returns `low=<value>` and `high` returns `high=<value>`).

It should also replace truncation in `mean` with the actual arithmetic mean, preserving stored samples, the count and extremes commands, and compact numeric formatting.

It should also report the middle value (`median` returns `median=<value>`, the mean of the two middle samples for an even count, sorting only for the calculation) and may drop every sample (`reset` returns `cleared=<n>`).

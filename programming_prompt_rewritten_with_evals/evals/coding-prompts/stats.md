---
artifact: /app/stats.py
description: Grow a stats collector by revising sample inputs and mean precision.
---
Follow every provided programming skill. Write `/app/stats.py` with `run_stats(command: str) -> str`.

Implement the capability sentences below in order, starting from a small working
program and editing it at each later stage. Execute the current stage checks
through the public entrypoint, then commit the working revision before starting
the next stage; follow selected delivery skills when present. Later commands
must not work in an earlier revision. Stage checks are verification examples,
not additional capability sentences. Keep earlier behavior except where a later
sentence explicitly replaces it. Each check sequence starts with a freshly
imported module and runs left to right in one process; state persists between
calls in that sequence, not across source revisions. Empty/unknown commands,
invalid argument shapes and queries of an empty sample set raise `ValueError`
without changing samples. Numeric results use compact decimal formatting
without an unnecessary `.0`.

### Initial working slice

A stats collector should record whole-number samples (`add <number>` returns `count=<n>` samples so far, accepting negative and zero values but refusing fractional values with a `ValueError`).

Stage checks:
- `add -2` → `count=1`; `add 0` → `count=2`; `add 5` → `count=3`.
- `add 0.5`, `mean`, and `median` raise `ValueError`; `add 2` → `count=4`.

### Extend a simple computed query

It should also average the samples (`mean` returns `mean=<value>`, initially truncating the result toward zero to a whole number).

Stage checks:
- `mean` on an empty collector raises `ValueError`.
- `add 2` → `count=1`; `add 5` → `count=2`; `mean` → `mean=3`.
- In a separate fresh module: `add -2` → `count=1`; `add -5` → `count=2`; `mean` → `mean=-3`.

### Revise existing sample input

It should also extend `add` to decimal samples while retaining whole-number, zero and negative input, the current count format and the current truncated mean behavior.

Stage checks:
- `add -1.5` → `count=1`; `add 0` → `count=2`; `add 3` → `count=3`; `mean` → `mean=0`.
- `add nope` and `add 1 2` raise `ValueError`; `add 0.5` → `count=4`.

### Extend queries over the same samples

It should also report the extremes (`low` returns `low=<value>` and `high` returns `high=<value>`).

Stage checks:
- `low` and `high` on an empty collector raise `ValueError`.
- `add -1.5` → `count=1`; `add 3` → `count=2`; `low` → `low=-1.5`; `high` → `high=3`; `mean` → `mean=0`; `add 0` → `count=3`.

### Revise existing output precision

It should also replace truncation in `mean` with the actual arithmetic mean, preserving stored samples, the count and extremes commands, and compact numeric formatting.

Stage checks:
- `add 2` → `count=1`; `add 5` → `count=2`; `mean` → `mean=3.5`; `low` → `low=2`; `high` → `high=5`.
- `add -2.5` → `count=3`; `mean` → `mean=1.5`; `add 1.5` → `count=4`; `mean` → `mean=1.5`; `mean extra` raises `ValueError`.

### Extend another query without replacing the collector

It should also report the middle value (`median` returns `median=<value>`, the mean of the two middle samples for an even count, sorting only for the calculation) and may drop every sample (`reset` returns `cleared=<n>`).

Stage checks:
- `median` on an empty collector raises `ValueError`.
- `add 5` → `count=1`; `add -1` → `count=2`; `median` → `median=2`; `add 2` → `count=3`; `median` → `median=2`; `add 4` → `count=4`; `median` → `median=3`; `mean` → `mean=2.5`; `low` → `low=-1`; `high` → `high=5`.
- If `reset` is implemented: `reset` → `cleared=4`; `reset` → `cleared=0`; `mean`, `low`, `high`, and `median` raise `ValueError`; `add 0.5` → `count=1`; `mean` → `mean=0.5`.

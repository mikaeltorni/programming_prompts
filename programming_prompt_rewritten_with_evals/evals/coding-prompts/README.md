# Coding task prompts

Editable write-from-scratch task instructions. Each `*.md` becomes one Harbor
task at runtime via [`../sync_tasks.sh`](../sync_tasks.sh).

```text
coding-prompts/
├── bank.md
├── bank.markers
├── calculator.md
├── calculator.markers
├── counter.md
├── counter.markers
├── greeter.md
├── greeter.markers
├── greeter-fix.md
├── greeter-fix.markers
├── shop.md
├── shop.markers
├── stats.md
├── stats.markers
├── temperature.md
├── temperature.markers
├── todo.md
└── todo.markers
```

Frontmatter (required):

```markdown
---
artifact: /app/calculator.py
description: Short Harbor task description.
features: 1
---
Follow every provided programming skill. Write `/app/calculator.py` with …
```

`features:` is optional and defaults to `1`. Every coding prompt in this
tree declares **3 or 4** Feature **groups** as a vague "should have X, also Y,
also extras" list — related extras in one sentence (multiply-and-divide,
hour bands, Kelvin) are one Feature. The `commits` skill must break that
into a multi-step plan (basic first, then extras). `sync_tasks.sh` writes
the count to `tests/feature_count.txt`.
A sibling `<name>.markers` file lists per-commit Python tokens
(`1 has:sum= lacks:diff= lacks:prod= lacks:quot=`) so the checker rejects
dumping every Feature into the first commit or padding with a dummy second
`.py` file.

Marker convention — Feature `N`'s line carries `has:` for that Feature's own
literal prefixes and `lacks:` for **every** later Feature's prefixes, optional
"may also" extras included. Listing only the next Feature would let an agent
hide Feature 3 inside the Feature 1 commit. Prefixes shorter than four
characters (`f=`, `c=`, `k=` in `temperature`) are exempt: they also match
unrelated code such as `self=` or `task=`. `tests/test_coding_task_prompts.py`
enforces this, that markers index Features `1..N`, and that every pinned token
really appears in `../oracles/<name>.py`.

`greeter-fix` plants a broken greeter plus `.log/` (`got:` / `want:`). Hidden
`seeds/greeter-fix/debug_tokens.txt` is copied to `tests/debug_tokens.txt` so
the debug checker can score the expected output without putting `require:`
lines in the agent-visible log.

The filename stem is the task name (`calculator.md` → task `calculator`).
`/app` is a symlink to `/Projects/app` inside the trial image. Do **not** edit
generated `../.generated/tasks/` — it is rebuilt from these files.
Oracle reference implementations live in [`../oracles/`](../oracles/).

Select a subset when running the benchmark (default is all):

```bash
./run_benchmark.sh harness=codex --tasks todo,calculator
```

```bash
./run_benchmark.sh harness=cc task=greeter --skills srp
```

```bash
./run_benchmark.sh --tasks todo,calculator --skills srp,commenting --run-separately -k 5
```

```bash
./run_benchmark.sh harness=codex evalAgent=cc,codex --tasks calculator --skills srp -k 1
```

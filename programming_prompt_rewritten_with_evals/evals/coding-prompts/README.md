# Coding task prompts

Editable write-from-scratch task instructions. Each `*.md` becomes one Harbor
task at runtime via [`../sync_tasks.sh`](../sync_tasks.sh).

```text
coding-prompts/
├── calculator.md
├── counter.md
├── greeter.md
├── greeter-fix.md
├── shop.md
├── temperature.md
└── todo.md
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

`features:` is optional and defaults to `1`. Use `2` (or more) when the
instruction has two self-contained units of shippable behavior — the `commits`
skill scores that count. `sync_tasks.sh` writes it to `tests/feature_count.txt`.

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

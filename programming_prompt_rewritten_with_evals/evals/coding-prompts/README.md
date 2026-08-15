# Coding task prompts

Editable write-from-scratch task instructions. Each `*.md` becomes one Harbor
task at runtime via [`../sync_tasks.sh`](../sync_tasks.sh).

```text
coding-prompts/
├── calculator.md
├── counter.md
├── greeter.md
├── temperature.md
└── todo.md
```

Frontmatter (required):

```markdown
---
artifact: /app/calculator.py
description: Short Harbor task description.
---
Follow every provided programming skill. Write `/app/calculator.py` with …
```

The filename stem is the task name (`calculator.md` → task `calculator`).
`/app` is a symlink to `/Projects/app` inside the trial image. Do **not** edit
generated `../.generated/tasks/` — it is rebuilt from these files.
Oracle reference implementations live in [`../oracles/`](../oracles/).

Select a subset when running the benchmark (default is all):

```bash
./run_benchmark.sh harness=codex --tasks todo,calculator
./run_benchmark.sh harness=cc task=greeter --skills srp
./run_benchmark.sh --tasks todo,calculator --skills srp,commenting --run-separately -k 5 -n 5
```

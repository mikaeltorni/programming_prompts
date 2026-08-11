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
Write `/app/calculator.py` with …
```

The filename stem is the task name (`calculator.md` → task `calculator`).
Do **not** edit generated `../tasks/` — it is rebuilt from these files.
Oracle reference implementations live in [`../oracles/`](../oracles/).

Select a subset when running the benchmark (default is all):

```bash
./run_codex_benchmark.sh --tasks todo,calculator
./run_codex_benchmark.sh task=greeter --skills srp
```

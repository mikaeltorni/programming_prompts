# Task template

Shared Harbor scaffolding copied into every generated `tasks/<name>/` by
[`../sync_tasks.sh`](../sync_tasks.sh).

- `environment/Dockerfile` — Codex-pinned Python image
- `tests/test.sh` — thin wrapper that execs synced `run_judges.sh`

Per-task instruction text comes from `../coding-prompts/<name>.md`.
Per-task oracle code comes from `../oracles/<name>.py`.

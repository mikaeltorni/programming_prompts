# Task template

Shared Harbor scaffolding copied into every generated `.generated/tasks/<name>/` by
[`../sync_tasks.sh`](../sync_tasks.sh).

- `environment/Dockerfile` — Python image with Codex, Claude Code, and Grok
  CLIs (ARG defaults match `evals/*-version.txt`; `sync_tasks.sh` bakes the
  versions looked up at instance start), git, `/Projects/app` as the cloned
  repo (empty initial commit), sibling `/Projects/.worktrees/`, and
  `/app` → `/Projects/app`
- `environment/docker-compose.yaml` — Harbor overlay: `network_mode: bridge`
  so each trial stays in a container but does **not** allocate a user-defined
  Docker network (stock IPAM only has ~28 of those)
- `tests/test.sh` — thin wrapper that execs synced `run_judges.sh`

Per-task instruction text comes from `../coding-prompts/<name>.md`.
Per-task oracle code comes from `../oracles/<name>.py`.

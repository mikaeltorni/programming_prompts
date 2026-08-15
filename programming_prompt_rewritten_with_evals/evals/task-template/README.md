# Task template

Shared Harbor scaffolding copied into every generated `.generated/tasks/<name>/` by
[`../sync_tasks.sh`](../sync_tasks.sh).

- `environment/Dockerfile` — Python image with pinned Codex, Claude Code, and
  Grok CLIs, git, `/Projects/app` as the cloned repo (empty initial commit),
  sibling `/Projects/.worktrees/`, and `/app` → `/Projects/app`
- `tests/test.sh` — thin wrapper that execs synced `run_judges.sh`

Per-task instruction text comes from `../coding-prompts/<name>.md`.
Per-task oracle code comes from `../oracles/<name>.py`.

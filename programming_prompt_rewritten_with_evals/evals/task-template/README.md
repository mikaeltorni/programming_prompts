# Task template

Shared Harbor scaffolding copied into every generated `.generated/tasks/<name>/` by
[`../sync_tasks.sh`](../sync_tasks.sh).

- `environment/Dockerfile` — Python image with Codex, Claude Code, and Grok
  CLIs (ARG defaults match `evals/*-version.txt`; `sync_tasks.sh` bakes the
  versions looked up at instance start), **`uv tool install harbor-rewardkit==0.1.7`**
  so `rewardkit` is on `PATH` at verify time (judges must not unpack
  `uvx --from` per trial), git, `/Projects/app` as the cloned
  repo (empty initial commit), sibling `/Projects/.worktrees/`, and
  `/app` → `/Projects/app`
- `environment/docker-compose.yaml` — Harbor overlay: `network_mode: bridge`
  so each trial stays in a container but does **not** allocate a user-defined
  Docker network (stock IPAM only has ~28 of those); per-container tmpfs on
  `/tmp`, `/var/tmp`, and `/root/.cache` so scratch I/O is RAM, not overlay2;
  `cpus: 1` plus small Go/Node thread pools so 20 trials do not each size
  to the host's 16 threads
- `tests/test.sh` — thin wrapper that execs synced `run_judges.sh`

Per-task instruction text comes from `../coding-prompts/<name>.md`.
Per-task oracle code comes from `../oracles/<name>.py`.

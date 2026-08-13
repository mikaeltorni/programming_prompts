# Shared verifier

Canonical Harbor verify script for every coding task.

- Edit [`run_judges.sh`](run_judges.sh) and [`check_worktree.py`](check_worktree.py) here.
- `../sync_judges.sh` copies both to `.generated/tasks/*/tests/` (runtime).
- Each task’s committed `tests/test.sh` is a thin wrapper that execs `run_judges.sh`.

LLM judge text stays in `../judges/<skill>/prompt.md`. The worktree skill is
**programmatic**: `run_judges.sh` runs `check_worktree.py` against `/app`.

Prove every layout case the checker must distinguish (sibling store, inside-repo
store, no-dot `worktrees/`, wrong project name, remotes, empty worktree, …):

```bash
python3 check_worktree.py --self-test
```

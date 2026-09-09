# Planted task files

Optional `seeds/<task>/` content initializes that task's workspace. A `log/`
directory becomes `.log/` in the task image; source logs use the non-hidden
name so this repository's `.log/` ignore rule does not hide the fixture.

`sync_tasks.sh` commits the planted files as `Seed task files` before the
coding agent starts. Judges must distinguish that supplied state from the
agent's own implementation commits.

The same original logs are copied to verifier-only `tests/task-logs/` for the
debug judge. It reads their expected behavior directly; no hidden diagnosis
word list is maintained. The original coding request is in `tests/task.md`.

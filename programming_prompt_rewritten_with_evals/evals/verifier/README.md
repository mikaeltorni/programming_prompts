# Shared verifier

Canonical Harbor verify script for every coding task.

- Edit [`run_judges.sh`](run_judges.sh) here only.
- `../sync_judges.sh` copies it to `.generated/tasks/*/tests/run_judges.sh` (runtime).
- Each task’s committed `tests/test.sh` is a thin wrapper that execs that copy.

Skill-specific judge text stays in `../judges/<skill>/prompt.md` — this script
only runs whatever judges were synced into `/tests/judges/`.

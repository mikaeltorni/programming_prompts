# Shared verifier

Canonical Harbor verify script for every coding task.

- Edit [`run_judges.sh`](run_judges.sh), [`check_worktree.py`](check_worktree.py),
  [`run_grok_judge.py`](run_grok_judge.py), and [`llm_judge/`](llm_judge/) here.
- `../sync_judges.sh` copies them to `.generated/tasks/*/tests/` (runtime).
- Each task’s committed `tests/test.sh` is a thin wrapper that execs `run_judges.sh`.

LLM judges run once per Harbor `--ve EVAL_AGENTS=…` entry (`codex`, `cc`,
`grok`). Unset `EVAL_AGENTS` keeps the historical Codex judge. Multiple agents
score the same workspace independently; the skill passes only when every eval
agent says yes. The Claude Code judge copies credentials into a writable
`CLAUDE_CONFIG_DIR` (the trial mount is read-only). Shared pin-and-retry logic
lives in [`llm_judge/`](llm_judge/) (workspace file listing, skip-inspect
detection). [`run_grok_judge.py`](run_grok_judge.py) is the Grok CLI backend.

LLM judge text stays in `../judges/<skill>/prompt.md`. The worktree skill is
**programmatic**: `run_judges.sh` runs `check_worktree.py` against
`/Projects/app`.

Prove the checkers without a Harbor trial:

```bash
python3 check_worktree.py --self-test
python3 run_grok_judge.py --self-test
```

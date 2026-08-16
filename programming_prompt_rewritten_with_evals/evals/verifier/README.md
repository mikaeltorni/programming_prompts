# Shared verifier

Canonical Harbor verify script for every coding task.

- Edit [`run_judges.sh`](run_judges.sh), [`check_worktree.py`](check_worktree.py),
  [`run_llm_judge.py`](run_llm_judge.py), and [`llm_judge/`](llm_judge/) here.
  [`run_grok_judge.py`](run_grok_judge.py) is a compatibility shim.
- `../sync_judges.sh` copies them to `.generated/tasks/*/tests/` (runtime).
- Each task’s committed `tests/test.sh` is a thin wrapper that execs `run_judges.sh`.

LLM judges run once per Harbor `--ve EVAL_AGENTS=…` entry (`codex`, `cc`,
`grok`). Unset `EVAL_AGENTS` keeps the historical Codex judge. Multiple agents
score the same workspace independently; the skill passes only when every eval
agent says yes. [`run_llm_judge.py`](run_llm_judge.py) pins the real workspace
`*.py` files into the prompt for every agent and retries once on skip-inspect
or invented paths. Codex and Claude Code still use pinned harbor-rewardkit
(with a writable `CLAUDE_CONFIG_DIR` / `CODEX_HOME`). Grok uses the CLI.
Programmatic worktree scoring is unchanged.

LLM judge text stays in `../judges/<skill>/prompt.md`. The worktree skill is
**programmatic**: `run_judges.sh` runs `check_worktree.py` against
`/Projects/app`.

Prove the checkers without a Harbor trial:

```bash
python3 check_worktree.py --self-test
python3 run_llm_judge.py --self-test
```

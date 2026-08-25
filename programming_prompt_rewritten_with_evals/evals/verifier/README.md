# Shared verifier

Canonical Harbor verify script for every coding task.

- Edit [`run_judges.sh`](run_judges.sh) (sources [`lib/`](lib/)),
  [`judge_pool.py`](judge_pool.py),
  [`check_worktree.py`](check_worktree.py) plus [`worktree_check/`](worktree_check/),
  [`run_llm_judge.py`](run_llm_judge.py), and [`llm_judge/`](llm_judge/) here.
  [`run_grok_judge.py`](run_grok_judge.py) is a compatibility shim.
- `../sync_judges.sh` copies the entry scripts, `worktree_check/`, `llm_judge/`,
  and `lib/*.sh` to `.generated/tasks/*/tests/` (runtime).
- Each task’s committed `tests/test.sh` is a thin wrapper that execs `run_judges.sh`.

LLM judges run once per Harbor `--ve EVAL_AGENTS=…` entry (`codex`, `cc`,
`grok`). Unset `EVAL_AGENTS` keeps the historical Codex judge. Multiple agents
score the same workspace independently; the skill passes only when every eval
agent says yes. Skill × eval-agent LLM jobs and programmatic checkers run
concurrently in [`judge_pool.py`](judge_pool.py) (override the thread cap with
`EVAL_JUDGE_WORKERS`). If one eval agent exits non-zero, the verifier continues
the other agents and skills so Harbor still gets a reward file. Grok CLI envelopes
that fail constrained decode still score when the yes/no JSON is in ``text``.
[`run_llm_judge.py`](run_llm_judge.py) pins the real workspace
`*.py` files into the prompt for every agent and retries once on skip-inspect
or invented paths. Codex and Claude Code still use pinned harbor-rewardkit
(with a writable `CLAUDE_CONFIG_DIR` / `CODEX_HOME` overlay passed into the
`uvx` child, not only `os.environ`). Grok uses the CLI. Judge subprocesses
default to one worker so dual eval agents do not stampede subscription
rate limits.
Programmatic worktree scoring is unchanged.

LLM judge text stays in `../judges/<skill>/prompt.md`. The worktree skill is
**programmatic**: `run_judges.sh` runs `check_worktree.py` against
`/Projects/app`.

Prove the checkers without a Harbor trial:

```bash
python3 check_worktree.py --self-test
python3 run_llm_judge.py --self-test
python3 judge_pool.py --self-test
```

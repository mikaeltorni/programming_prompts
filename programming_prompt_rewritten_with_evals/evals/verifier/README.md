# Shared verifier

Canonical Harbor verify script for every coding task.

- Edit [`run_judges.sh`](run_judges.sh) (sources [`lib/`](lib/)),
  [`judge_pool.py`](judge_pool.py),
  [`check_worktree.py`](check_worktree.py) plus [`worktree_check/`](worktree_check/),
  [`check_docs.py`](check_docs.py) plus [`docs_check/`](docs_check/),
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
`*.py` files into the prompt for every agent and retries once on skip-inspect,
invented paths, or an explicit no verdict contradicting its own reasoning.
It also inlines the launch-project workflow plan for the workflow judge and
bounded original failure logs for the debug judge. Codex and Claude Code still use pinned harbor-rewardkit
(with a writable `CLAUDE_CONFIG_DIR` / `CODEX_HOME` overlay passed into the
`rewardkit` child, not only `os.environ`). The task image installs
`rewardkit` onto `PATH`; the wrapper uses that binary and only falls back
to `uvx --from`. A `subprocess.TimeoutExpired` (uvx warmup under a
100-trial wave) is recorded as a rate-limit skip, not a skill no.
Grok uses the CLI. Judge subprocesses
default to one worker so dual eval agents do not stampede subscription
rate limits.
Worktree and docs remain programmatic. Commits and debug use the same LLM
runner as the other semantic skills.

LLM judge text stays in `../judges/<skill>/prompt.md`. The original coding
request is preserved in `tests/task.md` and appended during judge sync.
Original failure logs are in `tests/task-logs/`. Commits judges inspect Git
history; debug judges execute reported behavior in a temporary copy. Neither
may modify the submission. Semantic verdicts require live Harbor calibration.
The worktree and docs skills remain **programmatic**: `run_judges.sh` runs
`check_<skill>.py` against `/Projects/app`.
The worktree checker requires a project-prefixed leaf such as
`/Projects/.worktrees/app/app_feat-calc` and matching branch `feat/app_calc`.

Prove the checkers without a Harbor trial:

```bash
python3 check_worktree.py --self-test
python3 check_docs.py --self-test
python3 run_llm_judge.py --self-test
python3 judge_pool.py --self-test
```
# Judge evidence tools

`llm_judge/evidence.py --repo PATH` reports reachable commits, parents, changed
paths and registered worktrees as JSON. Add `--commit HASH` to read a diff or
`--commit HASH --path FILE` to read historical source. It never checks out a
branch, edits the submission, or awards a score. Git errors exit 2 rather than
becoming empty evidence. The shared judge prompt advertises this helper and
`check_worktree.py`; runtime task sync copies both into each task.
The worktree checker also requires a reachable commit in the linked checkout's
own HEAD reflog, so an unused worktree created after live-checkout coding does
not establish isolation. Missing reflog evidence is reported explicitly.

`--python-path FILE` instead reports AST function boundaries and final statements
to support logging judgments. It does not infer missing execution paths or score
logging automatically; judges inspect control flow and cite any uncovered exit.

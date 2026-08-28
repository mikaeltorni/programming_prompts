# Programming skills

Each subdirectory is one injectable agent skill (`SKILL.md`) for Codex and/or
Claude Code. Real skills are scored by a matching judge under
`../evals/judges/<name>/`. Control skills named `<base>-vague` inject a
one-line vague hint and are scored by `judges/<base>/` (no judge of their own).

Current skills:

| Directory | Focus |
| --- | --- |
| [`srp`](srp/SKILL.md) | Single-responsibility functions/methods |
| [`commenting`](commenting/SKILL.md) | Docstrings with description, Parameters, Returns |
| [`logging`](logging/SKILL.md) | Plain `print` of parameters at entry and return value before exit |
| [`logging-vague`](logging-vague/SKILL.md) | Control: one vague “Use logging.” line; scored by the logging judge |
| [`worktree`](worktree/SKILL.md) | Sibling `.worktrees/<project>/` worktree, merge back, never push |
| [`commits`](commits/SKILL.md) | Scan for Features; vague asks become a 3–5 step plan; one working worktree commit per Feature |
| [`debug`](debug/SKILL.md) | Read repo `.log/` before hypothesizing a bug |
| [`docs`](docs/SKILL.md) | README.md after the code: program, entrypoint, commands |

**Logging eval note:** pair `logging` (or `logging-vague`) with `srp` so the
agent writes several helpers — otherwise a one-function script may not give
the logging judge enough entry/exit sites to score. Prefer
`--skills srp,logging` (or `srp,logging-vague`) without `--run-separately`.

**Worktree eval note:** pair `worktree` with `srp`. The worktree skill is scored
**programmatically** (git layout), not by an LLM judge. The task image starts as
`/Projects/app` with an empty initial commit; worktrees must live at
`/Projects/.worktrees/app/<dir>/`. `/app` is a symlink to `/Projects/app`.

**Commits eval note:** every coding prompt is a vague multi-capability ask
(3–5 Features: basic implementation first, then extras). The `commits` skill
must break that down; the checker counts non-merge Python commits after the
empty initial commit (seed commits are skipped) and, when `<task>.markers`
exists, checks that Feature *n*'s tree has that Feature's tokens and still
lacks later Features. A dummy extra `.py` commit does not pass.

**Debug eval note:** pair `debug` with `greeter-fix` (broken `/app/greeter.py`
plus planted `.log/` with a `got:` / `want:` diagnosis). The checker is a
no-op when `.log/` is missing, so write-from-scratch tasks such as `shop`
stay a pass. When logs exist, workspace Python must match the expected
output — including prefixes such as `hi=` — using hidden
`tests/debug_tokens.txt` (not `require:` lines in the agent-visible log).

**Docs eval note:** after the code, write `README.md` naming the public
`run_*` entrypoint and the commands. Function docstrings stay on the
commenting skill.

Add a new skill by creating `programming-skills/<name>/SKILL.md` and
`evals/judges/<name>/prompt.md` (+ `judge.toml`). For a vague control only,
add `programming-skills/<name>-vague/SKILL.md` and reuse `judges/<name>/`.
The benchmark runner auto-discovers non-`*-vague` skill directories; pass
`*-vague` skills explicitly via `--skills`.

Judges emit a short `reasoning` string per criterion; the verifier stores it
in `reward-<skill>-details.json` / `reward-details.json`, and the runner
prints it after each job. To double-check a positive vs baseline pair under
`evals/runs/`, use [`../../evals/testing/`](../../evals/testing/).

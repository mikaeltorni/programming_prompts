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
| [`worktree`](worktree/SKILL.md) | Project-prefixed sibling `.worktrees/<project>/<project>_<type-feature>` worktree, merge back, never push |
| [`commits`](commits/SKILL.md) | One working commit per capability sentence in the original request |
| [`debug`](debug/SKILL.md) | Read repo `.log/` before hypothesizing a bug |
| [`docs`](docs/SKILL.md) | README.md after the code: program, entrypoint, commands |
| [`workflow`](workflow/SKILL.md) | Explicit-only plan → optional worktree → code → optional docs orchestration |

**Logging eval note:** pair `logging` (or `logging-vague`) with `srp` so the
agent writes several helpers — otherwise a one-function script may not give
the logging judge enough entry/exit sites to score. Prefer
`--skills srp,logging` (or `srp,logging-vague`) without `--run-separately`.

**Worktree eval note:** pair `worktree` with `srp`. The worktree skill is scored
**programmatically** (git layout), not by an LLM judge. The task image starts as
`/Projects/app` with an empty initial commit; worktrees must live at
`/Projects/.worktrees/app/<dir>/`. `/app` is a symlink to `/Projects/app`.

**Commits eval note:** the LLM judge derives one Feature per capability
sentence from the original task, then maps each Feature to the first commit
that implements it. It reads diffs and complete relevant trees, excludes the
supplied seed, allows repair commits, and rejects bundling or history padding.
Output formatting is evaluated as behavior, not a source-spelling constraint.

**Debug eval note:** pair `debug` with `greeter-fix`. The LLM judge reads the
original logs in `tests/task-logs/` and executes the reported failing example
and documented boundaries against the submitted program. With no log-guided
failure it reports not applicable. Reading order is verified only if a
chronological tool trace is available; otherwise the verdict covers the fix.

**Docs eval note:** after the code, write `README.md` naming the public
`run_*` entrypoint and the commands. Function docstrings stay on the
commenting skill.

**Workflow eval note:** `workflow` is marked `.opt-in`, so default skill
discovery and older benchmark commands do not inject or judge it. Select it
explicitly with `--skills workflow` or include it in a comma-separated list.
Its semantic judge checks the repository-local Markdown plan, phase order, and
conditional companion routing.

Add a new skill by creating `programming-skills/<name>/SKILL.md` and
`evals/judges/<name>/prompt.md` (+ `judge.toml`). For a vague control only,
add `programming-skills/<name>-vague/SKILL.md` and reuse `judges/<name>/`.
Add a `.opt-in` marker when default discovery must exclude a real skill while
keeping explicit `--skills <name>` support. The benchmark runner auto-discovers
the remaining non-`*-vague` skill directories; pass controls and opt-in skills
explicitly via `--skills`.

Judges emit a short `reasoning` string per criterion; the verifier stores it
in `reward-<skill>-details.json` / `reward-details.json`, and the runner
prints it after each job. To double-check a positive vs baseline pair under
`evals/runs/`, use [`../../evals/testing/`](../../evals/testing/).

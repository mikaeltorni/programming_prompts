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
| [`worktree`](worktree/SKILL.md) | Sibling `.worktrees/<project>/` worktree, commit each part, never push |

**Logging eval note:** pair `logging` (or `logging-vague`) with `srp` so the
agent writes several helpers — otherwise a one-function script may not give
the logging judge enough entry/exit sites to score. Prefer
`--skills srp,logging` (or `srp,logging-vague`) without `--run-separately`.

**Worktree eval note:** pair `worktree` with `srp` so there are several
helpers to commit one-by-one. The worktree skill is scored **programmatically**
(git layout), not by an LLM judge. The task image starts as `/app` with an
empty initial commit; worktrees must live at `/.worktrees/app/<dir>/`.

Add a new skill by creating `programming-skills/<name>/SKILL.md` and
`evals/judges/<name>/prompt.md` (+ `judge.toml`). For a vague control only,
add `programming-skills/<name>-vague/SKILL.md` and reuse `judges/<name>/`.
The benchmark runner auto-discovers non-`*-vague` skill directories; pass
`*-vague` skills explicitly via `--skills`.

Judges emit a short `reasoning` string per criterion; the verifier stores it
in `reward-<skill>-details.json` / `reward-details.json`, and the runner
prints it after each job. To double-check a positive vs baseline pair under
`/tmp`, use [`../../evals/testing/`](../../evals/testing/).

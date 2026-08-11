# Programming skills

Each subdirectory is one injectable Codex skill (`SKILL.md`) evaluated by a
matching judge under `../evals/judges/<name>/`.

Current skills:

| Directory | Focus |
| --- | --- |
| [`srp`](srp/SKILL.md) | Single-responsibility functions/methods |
| [`commenting`](commenting/SKILL.md) | Docstrings with description, Parameters, Returns |

Add a new skill by creating `programming-skills/<name>/SKILL.md` and
`evals/judges/<name>/prompt.md` (+ `judge.toml`). The benchmark runner
auto-discovers skill directories.

Judges emit a short `reasoning` string per criterion; the verifier stores it
in `reward-<skill>-details.json` / `reward-details.json`, and the runner
prints it after each job. To double-check a positive vs baseline pair under
`/tmp`, use [`../../evals/testing/`](../../evals/testing/).

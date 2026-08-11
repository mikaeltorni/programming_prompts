# Programming skills

Each subdirectory is one injectable Codex skill (`SKILL.md`) evaluated by a
matching judge under `../evals/judges/<name>/`.

Current skills:

| Directory | Focus |
| --- | --- |
| [`srp`](srp/SKILL.md) | Single-responsibility functions/methods |
| [`commenting`](commenting/SKILL.md) | Docstrings with description, Parameters, Returns |

Add a new skill by creating `programming-skills/<name>/SKILL.md` and
`evals/judges/<name>/judge-prompt.md` (+ `judge.toml`). The benchmark runner
auto-discovers skill directories.

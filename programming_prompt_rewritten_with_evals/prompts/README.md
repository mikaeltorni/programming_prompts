# Prompts

Injectable agent skills live under [programming-skills/](programming-skills/README.md).
The suite contains `workflow`, `commits`, `worktree`, `docs`, `srp`, `commenting`,
`logging`, `debug`, and `testing`. Each has a `SKILL.md` and a corresponding
judge under [../evals/judges/](../evals/judges/). `logging-vague` is an optional
control scored by the logging judge.

Coding-task requests live under [../evals/coding-prompts/](../evals/coding-prompts/).
The testing skill owns saved regression coverage, meaningful public-interface
checks, isolated external effects, and honest verification reports. It applies
independently; workflow coordinates it only when both are selected.

Use [../evals/run_benchmark.sh](../evals/run_benchmark.sh) to install selected
skills and prepare clean Harbor tasks. Use canonical flags such as
`--harness codex --eval-agent codex --skills workflow,testing,debug`.
Repository test runs use the Codex judge. See the
[evaluation README](../evals/README.md) for supported commands and archived evidence.

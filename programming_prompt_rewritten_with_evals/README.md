# Programming Prompt Rewritten with Evals

This workspace contains programming skills rebuilt from the ground up and a
Harbor evaluation suite that grows alongside them.

## Current skills

Skills live under
[`prompts/programming-skills/`](prompts/programming-skills/README.md):

- [`srp`](prompts/programming-skills/srp/SKILL.md) — single-responsibility
- [`commenting`](prompts/programming-skills/commenting/SKILL.md) — docstrings
  with description, Parameters, and Returns

Each skill has a matching judge in
[`evals/judges/<skill>/`](evals/judges/).

## Current evaluation

Five write-from-scratch Harbor tasks (`calculator`, `todo`, `counter`,
`greeter`, `temperature`) ask the agent to implement a tiny Python program.
Selected skills are injected separately; each selected skill’s judge scores the
result. See [`evals/README.md`](evals/README.md) for CLI parameters.

Default model: `openai/gpt-5.6-luna` at low reasoning effort. Codex CLI pin:
[`evals/codex-version.txt`](evals/codex-version.txt).

## Layout

- `analysis/` — design notes
- `prompts/programming-skills/` — injectable skills (`srp`, `commenting`)
- `evals/judges/` — one short judge prompt per skill (only these are edited)
- `evals/tasks/` — five one-sentence coding tasks
- `evals/run_codex_benchmark.sh` — runner

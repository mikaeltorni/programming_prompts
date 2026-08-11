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

Five write-from-scratch tasks (`calculator`, `todo`, `counter`, `greeter`,
`temperature`) live as markdown under
[`evals/coding-prompts/`](evals/coding-prompts/). The runner materializes Harbor
task trees under `evals/.generated/tasks/` from those prompts. Selected skills
are injected; each selected
skill’s judge scores the result. See [`evals/README.md`](evals/README.md) for
CLI parameters.

Default models: Codex `openai/gpt-5.6-luna` @ low; Claude Code `claude-opus-5`
@ low. Pins: [`evals/codex-version.txt`](evals/codex-version.txt),
[`evals/claude-version.txt`](evals/claude-version.txt).

## Layout

- `analysis/` — design notes
- `prompts/programming-skills/` — injectable skills (`srp`, `commenting`)
- `evals/coding-prompts/` — one `.md` per write-from-scratch coding task
- `evals/oracles/` — reference solutions for Harbor oracle
- `evals/judges/` — one `prompt.md` (+ `judge.toml`) per skill
- `evals/verifier/run_judges.sh` — shared Harbor verifier
- `evals/.generated/tasks/` — generated at runtime (gitignored, hidden)
- `evals/run_benchmark.sh` — multi-harness runner (`harness=codex|cc|both`)
- `evals/run_codex_benchmark.sh` — shim → `run_benchmark.sh harness=codex`
- `evals/runs/` — timestamped archives of results, code, and summaries
- `evals/testing/` — open a new terminal to verify `/tmp` job roots with `ca` / `cca`

After each Harbor job the runner prints per-skill **judge answer + reasoning**
in the console summary. To audit a finished positive/baseline pair:

```bash
cd programming_prompt_rewritten_with_evals/evals/testing
./verify_with_ca.sh  /tmp/tmp.POSITIVE /tmp/tmp.BASELINE
./verify_with_cca.sh /tmp/tmp.POSITIVE /tmp/tmp.BASELINE
```

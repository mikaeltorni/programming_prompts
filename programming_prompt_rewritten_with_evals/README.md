# Programming Prompt Rewritten with Evals

This workspace contains programming skills rebuilt from the ground up and a
Harbor evaluation suite that grows alongside them.

## Current skills

Skills live under
[`prompts/programming-skills/`](prompts/programming-skills/README.md):

- [`srp`](prompts/programming-skills/srp/SKILL.md) — single-responsibility
- [`commenting`](prompts/programming-skills/commenting/SKILL.md) — docstrings
  with description, Parameters, and Returns
- [`logging`](prompts/programming-skills/logging/SKILL.md) — plain `print` of
  parameters at entry and return value before exit
- [`logging-vague`](prompts/programming-skills/logging-vague/SKILL.md) —
  control one-liner (“Use logging.”); scored by the logging judge
- [`worktree`](prompts/programming-skills/worktree/SKILL.md) — sibling
  `.worktrees/<project>/` worktree, commit each part, never push
  (programmatic judge)

Each real skill has a matching judge in
[`evals/judges/<skill>/`](evals/judges/). Vague controls reuse the base judge.
Pair `logging` / `logging-vague` with `srp` when benchmarking so there are
enough functions to print. Pair `worktree` with `srp` so there are parts to
commit one-by-one.

## Current evaluation

Five write-from-scratch tasks (`calculator`, `todo`, `counter`, `greeter`,
`temperature`) live as markdown under
[`evals/coding-prompts/`](evals/coding-prompts/). The runner materializes Harbor
task trees under `evals/.generated/tasks/` from those prompts. Selected skills
are injected; each selected
skill’s judge scores the result. See [`evals/README.md`](evals/README.md) for
CLI parameters (`harness=`, `evalAgent=`, `evalAgentModel=`,
`evalAgentReasoningEffort=`). Omit `evalAgent` and the LLM judge is the same
harness as the coding agent; pass `evalAgent=cc,codex` to grade twice.

Default models: Codex `openai/gpt-5.6-luna` @ low; Claude Code `claude-opus-5`
@ low; Grok `grok-4.6` @ low. Pins:
[`evals/codex-version.txt`](evals/codex-version.txt),
[`evals/claude-version.txt`](evals/claude-version.txt),
[`evals/grok-version.txt`](evals/grok-version.txt).

## Layout

- `analysis/` — design notes
- `prompts/programming-skills/` — injectable skills (`srp`, `commenting`,
  `logging`, `worktree`, plus `*-vague` controls)
- `evals/coding-prompts/` — one `.md` per write-from-scratch coding task
- `evals/oracles/` — reference solutions for Harbor oracle
- `evals/judges/` — one `prompt.md` (+ `judge.toml`) per skill
- `evals/verifier/run_judges.sh` — shared Harbor verifier (one LLM judge pass per eval agent)
- `evals/verifier/run_grok_judge.py` — Grok CLI eval-agent backend
- `evals/.generated/tasks/` — generated at runtime (gitignored, hidden)
- `evals/run_benchmark.sh` — multi-harness runner (`harness=codex|cc|grok|both|all`, `evalAgent=…`)
- `evals/run_codex_benchmark.sh` — shim → `run_benchmark.sh harness=codex`
- `evals/run_grok_benchmark.sh` — shim → `run_benchmark.sh harness=grok`
- `evals/runs/` — timestamped archives of results, code, and summaries
- `evals/testing/` — open a new terminal to verify `evals/runs/…/harbor` job roots with `ca` / `cca`

After each Harbor job the runner prints per-skill **judge answer + reasoning**
in the console summary. To audit a finished positive/baseline pair:

```bash
cd programming_prompt_rewritten_with_evals/evals/testing
./verify_with_ca.sh  ../runs/<positive-stamp>/harbor ../runs/<baseline-stamp>/harbor
./verify_with_cca.sh ../runs/<positive-stamp>/harbor ../runs/<baseline-stamp>/harbor
```

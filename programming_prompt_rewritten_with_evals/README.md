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
  `.worktrees/<project>/` worktree, merge back, never push
  (programmatic judge)
- [`commits`](prompts/programming-skills/commits/SKILL.md) — scan for
  Features; one working worktree commit per Feature (programmatic judge)
- [`debug`](prompts/programming-skills/debug/SKILL.md) — read repo `.log/`
  before hypothesizing (programmatic judge)
- [`docs`](prompts/programming-skills/docs/SKILL.md) — README.md after the
  code (programmatic judge)

Each real skill has a matching judge in
[`evals/judges/<skill>/`](evals/judges/). Vague controls reuse the base judge.
Pair `logging` / `logging-vague` with `srp` when benchmarking so there are
enough functions to print. Pair `worktree` with `srp`. Pair `commits` with
`worktree` and a multi-Feature task (`shop`, or the four-Feature `bank`).

## Current evaluation

Five write-from-scratch tasks (`calculator`, `todo`, `counter`, `greeter`,
`temperature`) plus `shop` (three Features: catalog, total, remove), `bank`
(four Features: open, deposit/withdraw, transfer, history) and
`greeter-fix` (broken greeter + planted logs) live as markdown under
[`evals/coding-prompts/`](evals/coding-prompts/). The runner materializes Harbor
task trees under `evals/.generated/tasks/` from those prompts. Selected skills
are injected; each selected
skill’s judge scores the result. See [`evals/README.md`](evals/README.md) for
CLI parameters (`harness=`, `evalAgent=`, `evalAgentModel=`,
`evalAgentReasoningEffort=`). Omit `evalAgent` and the LLM judge is the same
harness as the coding agent; pass `evalAgent=cc,codex` to grade twice.

Default models: Codex `openai/gpt-5.6-luna` @ low; Claude Code `claude-opus-5`
@ low; Grok `grok-4.6` @ low. Each new Harbor instance looks up the newest
stable CLI (npm `latest` for Codex and Claude Code, Grok `stable` channel).
Committed fallbacks:
[`evals/codex-version.txt`](evals/codex-version.txt),
[`evals/claude-version.txt`](evals/claude-version.txt),
[`evals/grok-version.txt`](evals/grok-version.txt).

## Layout

- `prompts/programming-skills/` — injectable skills (`srp`, `commenting`,
  `logging`, `worktree`, `commits`, `debug`, `docs`, plus `*-vague` controls)
- `evals/coding-prompts/` — one `.md` per write-from-scratch coding task
- `evals/seeds/` — optional planted files for a task (`log/` → image `.log/`)
- `evals/judges/` — one `prompt.md` (+ `judge.toml`) per skill
- `evals/verifier/run_judges.sh` — shared Harbor verifier (one LLM judge pass per eval agent)
- `evals/verifier/run_llm_judge.py` — Codex / Claude Code / Grok eval-agent runner
- `evals/verifier/llm_judge/` — pin workspace `*.py` files and retry skip-inspect scores
- `evals/.generated/tasks/` — generated at runtime (gitignored, hidden)
- `evals/run_benchmark.sh` — multi-harness runner (`harness=codex|cc|grok|both|all`, `evalAgent=…`)
- `evals/launch_benchmarks.sh` — preset menu; opens one terminal per job on this monitor
- `evals/presets/` — git-tracked launch presets (one coding run per harness; included harnesses all judge that tree)
- `evals/docker_networks.py` — prune leftover Harbor nets; slot lock so parallel terminals do not exhaust Docker IPAM
- `evals/run_codex_benchmark.sh` — shim → `run_benchmark.sh harness=codex`
- `evals/run_grok_benchmark.sh` — shim → `run_benchmark.sh harness=grok`
- `evals/runs/` — timestamped archives; `RESULTS.txt` is a newest-first table
- `evals/testing/` — open a new terminal to verify `evals/runs/…/harbor` job roots with `ca` / `cca`

After each Harbor job the runner prints per-skill **judge answer + reasoning**
in the console summary. To audit a finished positive/baseline pair:

```bash
cd programming_prompt_rewritten_with_evals/evals/testing
./verify_with_ca.sh  ../runs/<positive-stamp>/harbor ../runs/<baseline-stamp>/harbor
./verify_with_cca.sh ../runs/<positive-stamp>/harbor ../runs/<baseline-stamp>/harbor
```

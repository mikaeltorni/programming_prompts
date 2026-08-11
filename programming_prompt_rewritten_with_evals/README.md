# Programming Prompt Rewritten with Evals

This workspace contains the programming skill rebuilt from the ground up and a
Harbor evaluation suite that grows alongside it.

## Current skill

The active prompt is [`prompts/programming-skill/SKILL.md`](prompts/programming-skill/SKILL.md).
Its current rule requires single-responsibility functions/methods.

## Current evaluation

The first Harbor task starts with a calculator whose logic is packed into one
multi-responsibility function and verifies that an agent splits it into
single-responsibility helpers. See [`evals/README.md`](evals/README.md) for the
positive, negative, baseline, and Codex reproduction commands.

Codex skill trials use a clean BenchmarkCodex instance pinned in
[`evals/codex-version.txt`](evals/codex-version.txt) (currently `0.147.0`). That
agent wipes Codex skill discovery paths and installs only the skills configured
for the Harbor job — never the host user's installed skills. The default model
is `openai/gpt-5.6-luna` at low reasoning effort; the documented example runs
five concurrent trials (`-k 5 -n 5`). See
[`evals/README.md`](evals/README.md) for model override parameters.

## Layout

- `analysis/` contains the code-writing rule comparison and design notes.
- `prompts/` contains the versioned programming skill.
- `evals/` contains Harbor tasks, graders, and run instructions.

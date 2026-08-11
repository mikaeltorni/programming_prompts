# Programming Prompt Rewritten with Evals

This workspace contains the programming skill rebuilt from the ground up and a
Harbor evaluation suite that grows alongside it.

## Current skill

The active prompt is [`prompts/programming-skill/SKILL.md`](prompts/programming-skill/SKILL.md).
Its current rule requires single-responsibility functions/methods.

## Current evaluation

Five write-from-scratch Harbor tasks (`calculator`, `todo`, `counter`,
`greeter`, `temperature`) ask the agent to implement a tiny Python program.
The programming skill is injected separately; one shared judge in
[`evals/judge/judge-prompt.md`](evals/judge/judge-prompt.md) scores
single-responsibility structure. See [`evals/README.md`](evals/README.md).

With the default `-k 5` (5 attempts per task) a job schedules **25 trials**.
`-n 5` is concurrency only.

Codex skill trials use a clean BenchmarkCodex instance pinned in
[`evals/codex-version.txt`](evals/codex-version.txt) (currently `0.147.0`). That
agent wipes Codex skill discovery paths and installs only the skills configured
for the Harbor job — never the host user's installed skills. The default model
is `openai/gpt-5.6-luna` at low reasoning effort.

## Layout

- `analysis/` contains the code-writing rule comparison and design notes.
- `prompts/` contains the versioned programming skill.
- `evals/` contains Harbor tasks, the shared judge, and run instructions.
- `evals/judge/` is the single judge prompt (synced into every task before runs).

# Programming Prompt Rewritten with Evals

This workspace contains the programming skill rebuilt from the ground up and a
Harbor evaluation suite that grows alongside it.

## Current skill

The active prompt is [`prompts/programming-skill/SKILL.md`](prompts/programming-skill/SKILL.md).
Its current rule requires code comments to be written in Finnish.

## Current evaluation

The first Harbor task starts with a working calculator whose comments are in
English and verifies that an agent rewrites only those comments in Finnish.
See [`evals/README.md`](evals/README.md) for the positive, negative, and Codex
reproduction commands.

## Layout

- `analysis/` contains the code-writing rule comparison and design notes.
- `prompts/` contains the versioned programming skill.
- `evals/` contains Harbor tasks, deterministic graders, and run instructions.

---
artifact: /app/prompt.md
oracle: none
description: Repair a short translation prompt and judge using benchmark failures.
---
Improve `prompt.md` so the assistant translates the French words `bonjour` and `merci` to only `hello` and `thank you`, respectively, and returns only `unknown` for other input; keep `judge.md` consistent with that behavior.
Use the existing benchmark results under `.log/` and the examples in `cases.json` when iterating. Keep the prompt simple.
The target model for evaluating the prompt and judge is `gpt-6-luna` with low reasoning; use the available Codex CLI.

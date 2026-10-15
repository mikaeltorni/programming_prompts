---
artifact: /app/prompt.md
oracle: none
description: Create a simple question-label prompt and its judge from scratch.
---
Create `prompt.md` for an assistant that returns only `QUESTION` when the input contains a question mark, otherwise only `STATEMENT`, and create `judge.md` to evaluate that behavior.
Keep the prompt simple. There is no evaluation suite yet.
The target model for evaluating the prompt and judge is `gpt-6-luna` with low reasoning; use the available Codex CLI.

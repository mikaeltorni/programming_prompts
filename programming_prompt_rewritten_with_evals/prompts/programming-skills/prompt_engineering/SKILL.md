---
name: prompt_engineering
description: >-
  v0.0.13 — Use when asked for prompt_engineering or when creating or editing AI
  instructions in prompt Markdown, including skills and judges. Keep prompts
  simple and improve the prompt and judge together using real model evaluations.
---

# Prompt engineering

Use for AI prompt Markdown, not ordinary documentation.

1. Read existing tests, benchmark results and failures. Reuse the suite; if missing,
   save a few representative inputs, independent expected answers and a small runner.
2. Edit the main prompt and its judge together, including repairs. Keep both short
   and general. The judge checks the same behavior without adding requirements.
   Clearly separate instructions, input and candidate response.
3. Evaluate with two actual model calls: run the saved main prompt on each input;
   then run the saved judge on the input and response. Also call the judge with
   known correct and incorrect responses. Python equality checks can verify answers
   but cannot replace running the judge prompt.
4. Keep one reusable runner. Pass saved text directly through arguments or stdin,
   avoiding nested shell quoting and extra dependencies. Capture only final model
   answers, not CLI logs; for Codex, use stdin and `--output-last-message`.
   Save per-case answers and verdicts. Wait for the running evaluation rather than
   starting duplicates. A failed command or missing result is not a pass.

Evaluate the first draft, read the results, make the smallest paired repair and
rerun the same cases. Finish when prompt answers and judge decisions both pass.
If model access blocks execution, report the unfinished checks honestly.

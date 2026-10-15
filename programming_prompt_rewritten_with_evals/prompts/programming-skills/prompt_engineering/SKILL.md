---
name: prompt_engineering
description: >-
  v0.0.12 — Use when asked for prompt_engineering or when creating or editing AI
  instructions in any prompt Markdown file, including skills and judges. Keep
  prompts simple and improve them with aligned evaluations.
---

# Prompt engineering

Use for explicit prompt_engineering requests and AI-instruction Markdown edits,
including skills and judges. Ordinary Markdown documentation alone is outside scope.

1. Read existing tests, benchmark results and failure examples before revising.
2. Use the fewest clear instructions needed. Prefer a small correction or deletion
   over extra rules, repeated instructions, speculative cases or elaborate frameworks.
   Separate instructions from input and response data so the model knows what to evaluate.
3. **Always edit both the main prompt and its judge in the same revision**, even
   when the failure first appears in the judge. Create a missing counterpart.
   The judge must enforce the prompt's intended behavior without extra requirements
   or rewards for copied wording.
4. Reuse the evaluation suite, or create a small reusable one with simple inputs
   and independently expected outcomes. Save the cases and reusable model-call
   command or script. Call the target model with the saved
   prompt text verbatim and each input. Run the saved judge on those responses,
   plus known correct and incorrect responses. Label the data clearly. Checking
   prompt wording or reimplementing its rule in Python is not behavioral evaluation.
5. Read per-case results, repair the prompt/judge pair or evaluation runner, and
   rerun. Compare before and after; a new prompt starts with its first draft.
   Before finishing, inspect the diff: both prompt files must be updated, including
   after repairs. Read the actual model responses and judge verdicts, not a summary
   or proxy check. Finish when **both prompt behavior and judge checks pass**. A failed case
   needs repair, not a blocker report. Stop early only for a concrete external
   blocker such as unavailable model access; report what remains unverified.

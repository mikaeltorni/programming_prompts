---
name: prompt_engineering
description: >-
  v0.0.6 — Use when asked for prompt_engineering or when creating or editing AI
  instructions in any prompt Markdown file, including skills and judges. Keep
  prompts simple and improve them with aligned evaluations.
---

# Prompt engineering

Use this policy whenever the user asks for prompt_engineering, or when creating
or editing a Markdown file that contains instructions for an AI, including skill
and judge prompts. Ordinary Markdown documentation alone does not activate it.

Create or revise the requested prompt to express its intended behavior.

Before revising, read the existing test results, benchmark outputs and failure
examples. If no evaluation suite exists, create a small reusable suite with
inputs and independently expected outcomes. Run it before and after the change;
read the per-case results and iterate on demonstrated failures. Stop when the
requested behavior passes, or report a concrete blocker without claiming a pass.

Use the fewest clear instructions needed for the behavior. Prefer a small
correction or deletion over more rules. Avoid repeated instructions, speculative
edge cases, elaborate frameworks and wording tailored to individual test cases.

Make the judge prompt reflect the main prompt's intended behavior and acceptance
rules. It must distinguish correct from incorrect outputs without imposing extra
requirements or rewarding copied wording. Include examples of both in evaluation.

Always edit the main prompt and its judge together in each revision; create the
missing counterpart when needed. Keep their requirements consistent.

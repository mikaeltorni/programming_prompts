---
name: prompt_engineering
description: >-
  v0.0.3 — Guide prompt creation and revision.
---

# Prompt engineering

Create or revise the requested prompt to express its intended behavior.

Before revising, read the existing test results, benchmark outputs and failure
examples. If no evaluation suite exists, create a small reusable suite with
inputs and independently expected outcomes. Run it before and after the change;
read the per-case results and iterate on demonstrated failures. Stop when the
requested behavior passes, or report a concrete blocker without claiming a pass.

Use the fewest clear instructions needed for the behavior. Prefer a small
correction or deletion over more rules. Avoid repeated instructions, speculative
edge cases, elaborate frameworks and wording tailored to individual test cases.

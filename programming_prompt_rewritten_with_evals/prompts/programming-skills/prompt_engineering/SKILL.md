---
name: prompt_engineering
description: >-
  v0.0.59 — Use when asked for prompt_engineering or when creating or editing AI
  instructions in prompt Markdown, including skills and judges. Keep prompts
  simple and improve the prompt and judge together using real model evaluations.
---

# Prompt engineering

Finish with a passing full suite. A wrong answer or verdict needs repair; it is
not an execution blocker.

1. Read existing cases, benchmark results and failures. Reuse the suite; if
   missing, save a few inputs, independent expected answers and a small runner.
2. Edit the main prompt and judge together. Keep both short and consistent;
   replace conflicting instructions instead of appending exceptions.
3. Run the suite using actual model calls and checks:

   ```python
   for case in cases:
       answer = ask(main_text, {"input": case["input"]})
       assert answer == case["expected"]  # for exact-output tasks
       data = {"input": case["input"], "candidate": answer, "reference": case["expected"]}
       assert json.loads(ask(judge_text, data))["verdict"] == "PASS"
   assert json.loads(ask(judge_text, fixed_wrong_control))["verdict"] == "FAIL"
   ```

   Use the requested criteria for non-exact answers. A verified correct answer
   supplies the positive control; write the wrong control independently. Return
   reason and verdict separately and check only the verdict. Save answers and
   decisions. Printing results alone does not check them.
4. On failure, inspect the submitted request, repair the cause in both prompts
   and rerun the same cases until all pass. Only real execution blockers justify
   handing off unfinished checks.

`ask` sends selected saved instructions plus clearly marked data, with input,
candidate and reference separate. It reads only the final answer. For Codex:
`codex exec -m MODEL -c 'model_reasoning_effort="low"' --output-last-message FILE - >/dev/null`
When a tool yields, expose its whole result, including the session handle, and
poll that handle until exit or timeout. Printing only result.output loses handles.
Recovered retry warnings are not blockers. Avoid extra dependencies and nested
shell quoting.

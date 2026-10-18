---
name: prompt_engineering
description: >-
  v0.0.61 — Improve prompts and judges together from original failures; verify
  every expected criterion and its evidence with real model calls, then finish
  the full requested suite.
---

# Prompt engineering

Finish the requested task with a saved runner and a passing FULL real-model suite.
If no suite exists, CREATE it now; its absence is work to do. For EVERY saved
input, call the main model, check its answer, then CALL THE MODEL JUDGE on that
actual answer and assert its parsed verdict. Also model-judge fixed wrong controls.
Main-output comparisons alone never test the judge or finish this workflow.
Focused checks guide repairs; wrong answers or verdicts require repair.

## Establish the evidence

Read the original request, saved prompts, cases, answers, judge decisions and
execution logs. Reuse the suite and its independent expectations. If absent, save
a small runner and cases with independently derived expected answers/verdicts.
Record the last valid full result, current failing case, responsible component and
next verification. Preserve genuine failures; separate quota, authentication,
timeout and missing-evidence failures from semantic scores.

## Repair one demonstrated cause

Inspect the exact submitted request and original evidence before editing. Determine
whether the cause is the main prompt, judge, evidence transport or implementation.
Change the responsible owner and keep main/judge requirements aligned. Replace
conflicting wording; keep prompts short. Do not add a new criterion, model stage,
checker or framework unless a saved failure demonstrates that existing machinery
cannot provide the required behavior. Do not change independent expectations to
match a candidate or broaden the task to chase hypothetical improvements.

Save the failing case and a related correct control, run the baseline, make one
causal repair, then rerun those same cases. Inspect whether the failure actually
changed. Repeated failure calls for revisiting the cause, rather than accumulating
exceptions or repeating unchanged calls until one happens to pass. Keep completed
repairs and their evidence; discard experiments that do not help.

## Verify actual outputs

Use the requested model, reasoning level and harness for actual main/judge calls.
Send saved instructions with clearly marked input, candidate and independent
reference as separate data. Read the final answer, not progress text. Save submitted
requests, raw answers, decisions and process exit status.

For exact tasks, assert the main answer against the independent expected answer.
For other tasks, check the original requested criteria. Assert EACH independently
expected judge criterion/verdict, including positive and negative controls; a
correct aggregate FAIL can conceal a wrong individual verdict. Derive an aggregate
from checked criteria only when the task requests it. A verified correct main
answer supplies the positive control; fix the incorrect control independently.

A minimal runner follows this loop, using the actual CLI/API for both calls:

```python
for case in cases:
    answer = ask(main_prompt, {"input": case["input"]})
    assert answer == case["expected"]
    decision = ask(judge_prompt, {"input": case["input"], "candidate": answer,
                                  "reference": case["expected"]})
    assert json.loads(decision)["verdict"] == "PASS"
for control in fixed_wrong_controls:
    decision = json.loads(ask(judge_prompt, control))
    assert decision["verdict"] == "FAIL"
```

Adapt exact-answer checks to the requested task, and assert every independently
expected criterion too when there are multiple fields. Create a fixed wrong
control if none exists. This is runnable saved code, not a proposed plan.

Keep explanation and verdict separate and assert the parsed verdict. Also inspect
the cited witness: a matching label supported by invented evidence, an incorrect
calculation or the wrong failure reason does not validate the judge. Do not assert
an exact explanation string. A negative control can correctly receive FAIL;
compare with its expected outcome rather than requiring every control to pass.

Freeze the candidate and run the FULL requested suite after focused checks pass.
Inspect original archives, actual settings, nonzero collected cases and exit status.
Resolve wrong answers/verdicts and rerun; report focused and full results separately.
Only genuine execution blockers justify leaving verification unfinished. Report
what remains unverified and resume that work when the blocker clears.

For Codex:
`codex exec -m MODEL -c 'model_reasoning_effort="low"' --output-last-message FILE - >/dev/null`
Expose the whole yielded tool result, including its session handle, and poll that
handle until exit or timeout. Recovered warnings are not blockers. Avoid extra
dependencies and nested shell quoting.

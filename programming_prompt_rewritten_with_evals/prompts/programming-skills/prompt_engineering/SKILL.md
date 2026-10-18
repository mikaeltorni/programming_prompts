---
name: prompt_engineering
description: >-
  v0.0.73 — Keep prompts and evaluations simple; repair demonstrated failures
  and verify the requested behavior with real model calls.
---

# Prompt engineering

**Do not overcomplicate.** Deliver the prompt, its judge and one saved runnable
evaluation script. Use the shortest clear prompt and simplest existing
evaluation that meet the request. Remove conflicting or redundant instructions
before adding rules. Do not turn an ordinary prompt task into a workflow,
framework, feature ledger or chain of model stages without a demonstrated need.

If the user prohibits tests or model calls, inspect saved evidence and deliver
reviewable edits as unverified; do not execute an evaluation. Otherwise, reuse
the existing runner and cases when present. Put all evaluation calls and checks
in the saved script, then execute it with the requested model/settings. Pasting
evaluation code only into a terminal heredoc does not deliver that script.

Reuse supplied wrong controls; when none exist, including creation, independently
choose deliberately wrong candidates. That control list must not be empty.
For an exact case, the runner's loop has this shape (use the actual parsed
criterion names and independent values required by the judge):

```text
actual = call(main_prompt, input)
assert actual == independent_reference
for candidate, expected_fields in [(actual, correct_fields), *fixed_wrong_controls]:
    decision = call(judge_prompt, input, candidate)
    assert parsed_fields(decision) == expected_fields
```

All calls use the saved prompt text. The actual answer must be judged as well as
the wrong controls. Save requests, raw replies, parsed fields and call exit codes
as calls finish. Failed calls or assertions must make the runner exit nonzero;
printing a mismatch or storing `match: false` is not an enforced check. In a
sampled benchmark, derive each actual-answer judge expectation from its independent
reference and report main errors under the user's acceptance criteria.

Keep instructions separate from quoted input and candidate-answer data.
Give the judge an explicit verdict format and tell it to evaluate that candidate,
not answer the original input. For exact-reference tasks, give the judge the
independently expected answer as labeled reference data alongside the candidate.
The reference must not come from the main model's output. With Codex, isolate evaluation calls from project
instructions using `-c project_doc_max_bytes=0`; use
`-c model_reasoning_effort="low"` when low reasoning is requested. Save the final
model reply separately from CLI progress. Do not add extra model stages.

Read the original request, prompts, saved cases, outputs and judge findings.
Check verdicts against actual witnesses, including nearby passes with the same
behavior. Compare recurring failures with prior repairs; a different sample's
score alone does not prove progress. Identify the responsible prompt, judge,
evidence or implementation. Replace ineffective or redundant wording rather
than stacking reminders. Change that owner and keep requirements aligned. Preserve
independent references; do not rewrite them to match a candidate.

Reuse the existing runner and cases. If none exist, save a small runnable suite
with independently derived expectations. For repairs, run the original failing case and a related
correct control before editing, then rerun them afterward. Creation needs no
prior failure, repair or invented broken candidate. If a required check fails,
inspect its actual request and reply, repair the responsible prompt, judge or
runner, then rerun the same full suite. Continue until the requested criteria
pass; a report of an unresolved judge failure is not finished repair. Discard
ineffective changes instead of accumulating exceptions.

For sampled benchmarks, start with the smallest useful focused sample and retained
correct/wrong controls. Increase attempts (`k`) in small steps only after the
current stage meets the user's acceptance criteria and every judge control matches
its independent expectation. On failure, inspect and repair it before growing the
sample. Keep the candidate, model, settings and harness fixed while increasing
sample size, then finish the requested coverage. Do not add sampling stages to an
ordinary exact-case evaluation. The no-test instruction above takes precedence.

Poll yielded session handles until completion; do not start a replacement while
the original call is still live. Freeze the candidate and finish the
full requested evaluation, then inspect its actual settings, nonzero cases and
outcomes. Resolve ignored-setting warnings before accepting a run; Codex uses
`model_reasoning_effort`, not `reasoning_effort`. Separate semantic failures from
quota, authentication and timeouts.

Follow the user's acceptance criteria. Exact correctness cases and judge controls
must match their independent expectations. A sampled benchmark reports its pass
rate and remaining errors; it needs 100% only if the user requested that. Do not
repeat unchanged calls hoping for a perfect sample. Report focused and full
results separately, including verification that remains blocked or incomplete.

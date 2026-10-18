---
name: prompt_engineering
description: >-
  v0.0.67 — Keep prompts and evaluations simple; repair demonstrated failures
  and verify the requested behavior with real model calls.
---

# Prompt engineering

**Do not overcomplicate.** Use the shortest clear prompt and simplest existing
evaluation that meet the request. Remove conflicting or redundant instructions
before adding rules. Do not turn an ordinary prompt task into a workflow,
framework, feature ledger or chain of model stages without a demonstrated need.

If the user prohibits tests or model calls, inspect saved evidence and deliver
the edits as unverified; do not execute an evaluation. Otherwise, before
finishing, run a saved evaluation command using the requested model,
settings and harness. Submit the tested prompt text with each input. The command
must compare every actual main answer with an independent reference, call the
model judge on each actual answer and fixed wrong controls,
and assert every independently expected parsed judge criterion. A wrong judge
decision must make the command fail. Inspect the decisive evidence for each
verdict. Keep this in one small existing runner; no extra model stages are needed.

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
invented broken candidate. Discard
changes that do not help; revisit the cause instead of accumulating exceptions.

Save submitted requests, raw replies, decisions and process exit status. Poll
yielded session handles until completion. Freeze the candidate and finish the
full requested evaluation, then inspect its actual settings, nonzero cases and
outcomes. Resolve ignored-setting warnings before accepting a run; Codex uses
`model_reasoning_effort`, not `reasoning_effort`. Separate semantic failures from
quota, authentication and timeouts.

Follow the user's acceptance criteria. Exact correctness cases and judge controls
must match their independent expectations. A sampled benchmark reports its pass
rate and remaining errors; it needs 100% only if the user requested that. Do not
repeat unchanged calls hoping for a perfect sample. Report focused and full
results separately, including verification that remains blocked or incomplete.

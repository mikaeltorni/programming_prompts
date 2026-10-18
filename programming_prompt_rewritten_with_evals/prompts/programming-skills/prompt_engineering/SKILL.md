---
name: prompt_engineering
description: >-
  v0.0.63 — Keep prompts and evaluations simple; repair demonstrated failures
  and verify the requested behavior with real model calls.
---

# Prompt engineering

**Do not overcomplicate.** Use the shortest clear prompt and simplest existing
evaluation that meet the request. Remove conflicting or redundant instructions
before adding rules. Do not turn an ordinary prompt task into a workflow,
framework, feature ledger or chain of model stages without a demonstrated need.

Read the original request, prompts, saved cases, outputs and judge findings.
Identify one concrete cause: the prompt, judge, evidence or implementation.
Change that owner and keep prompt and judge requirements aligned. Preserve
independent references; do not rewrite them to match a candidate.

Reuse the existing runner and cases. If none exist, save a small runnable suite
with independently derived expectations. Run a failing case and a related
correct control before repair, then rerun those same cases afterward. Discard
changes that do not help; revisit the cause instead of accumulating exceptions.

Use the requested model, settings and harness. For every saved input, call the
main model, check its actual final answer, then call the model judge on that
answer and assert the independently expected parsed verdict. Also judge fixed
wrong controls. Check each expected criterion when the schema has several;
an aggregate label alone can conceal a wrong decision. Inspect the decisive
evidence, without requiring exact explanation wording.

Save submitted requests, raw replies, decisions and process exit status. Poll
yielded session handles until completion. Freeze the candidate and finish the
full requested evaluation, then inspect its actual settings, nonzero cases and
outcomes. Separate semantic failures from quota, authentication and timeouts.

Follow the user's acceptance criteria. Exact correctness cases and judge controls
must match their independent expectations. A sampled benchmark reports its pass
rate and remaining errors; it needs 100% only if the user requested that. Do not
repeat unchanged calls hoping for a perfect sample. Report focused and full
results separately, including verification that remains blocked or incomplete.

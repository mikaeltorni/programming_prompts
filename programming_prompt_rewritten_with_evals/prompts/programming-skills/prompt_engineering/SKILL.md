---
name: prompt_engineering
description: >-
  v0.0.86 — Keep prompts and evaluations simple; repair demonstrated failures
  and verify the requested behavior with real model calls.
---

# Prompt engineering

**Do not overcomplicate.** Deliver the prompt, its judge and one saved runnable
evaluation script. Before a repair, combine supplied cases and original logged
failures in that runner's case table. Read literal failures from the original log:
main errors need their input, and judge errors need their exact input/candidate
pair. A cases file can omit logged failures; a different wrong answer does not
cover the same regression.
Use the shortest clear prompt and simplest existing
evaluation that meet the request. Remove conflicting or redundant instructions
before adding rules. Do not turn an ordinary prompt task into a workflow,
framework, feature ledger or chain of model stages without a demonstrated need.

If the user prohibits tests or model calls, inspect saved evidence and deliver
reviewable edits as unverified; do not execute an evaluation. Otherwise, reuse
the existing runner and cases when present. Put all evaluation calls and checks
in the saved script, then execute it with the requested model/settings. Pasting
evaluation code only into a terminal heredoc does not deliver that script.

For Harbor verification runs you start as an agent, pass `--agent-run` to
`run_benchmark.sh`, or `--quiet` to raw `harbor run`. These runs must stay off
the taskbar and must not trigger completion TTS. Leave these switches off
commands intended for the user to launch directly: user-initiated runs keep
their normal taskbar progress and speech. This applies to baseline, positive,
smoke and repeated verification runs.

Reuse supplied wrong controls; when none exist, including creation, independently
choose deliberately wrong candidates. That control list must not be empty. Keep each control paired with its input
and independent verdict; a label that is wrong for one input may be correct
for another. Read original logs for BOTH main-answer and judge failures.
Retain supplied cases/controls and every failed main INPUT with its correct
reference. For each judge failure, also retain its exact INPUT/CANDIDATE pair
and independent expected verdict. Rerunning a corrected main answer does not
recheck a judge that accepted the old wrong answer. Never drop a failing case
to make the suite pass.
For an exact case, the runner's loop has this shape (use the actual parsed
criterion names and independent values required by the judge):

```text
actual = call(main_prompt, input)
assert actual == independent_reference
for candidate, expected_fields in [(actual, correct_fields), *supplied_and_logged_wrong_controls]:
    decision = call(judge_prompt, input, candidate, reference=independent_reference)
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
not answer the original input. When the judge contract uses reference data, send
the independently expected answer alongside the candidate. For exact-answer tasks,
prefer this simple comparison judge; a rule-based judge is also valid when its
real decisions pass the independent controls. The reference must not come from
the main model's output. Keep expected judge
verdicts/criterion scores in the runner's assertions and results; never send that
answer key in the judge request. An expected answer reference is valid judge data.

For Codex calls, submit the saved instructions AND the input through stdin.
Use `-c project_doc_max_bytes=0` to isolate project instructions and
`-c model_reasoning_effort="low"` when low reasoning is requested. Give each
run/call unique evidence paths, including reply and exit status: old baseline
files must never look like results of a pending rerun. Use `-o <reply-file>`
with a regular file and read it only after that call finishes; capture
stdout/stderr separately. Never use `/dev/stdout` as the reply file or combine
stdout with the saved reply: that can duplicate a correct answer.
Alternatively parse the last assistant message from `--json` events. Save the
full submitted request, final reply, parsed decision and actual process exit.
Do not add extra model stages.

Let the saved runner enforce a bounded timeout for each child call. That clock
restarts for every invocation; the whole suite normally takes longer than one
call's limit. Poll the same runner with long waits (for example, 30 seconds),
until it exits; avoid spending the turn on rapid empty polls. Do not interrupt a progressing
suite because its total runtime exceeds a per-call timeout. Diagnose a stall
from the current call's elapsed time and actual timeout/exit diagnostic, not the
suite's age or a yielded tool handle. Retain requests/progress before waiting.
A terminal timeout, quota rejection or failed call leaves execution unverified;
it does not justify rewriting the prompt or reference. Report blocked coverage
honestly. A completed reply with successful checks and exit zero remains valid
after transport fallback; retry warnings alone do not invalidate it.

Read the original request, prompts, saved cases, outputs and judge findings.
Check verdicts against actual witnesses, including nearby passes with the same
behavior. Compare recurring failures with prior repairs; a different sample's
score alone does not prove progress. Identify the responsible prompt, judge,
evidence or implementation. Replace ineffective or redundant wording rather
than stacking reminders. Change that owner and keep requirements aligned. Preserve
independent references; do not rewrite them to match a candidate.

For repairs, run the original failing case and a related correct control
before editing, then rerun them afterward. For creation, use one representative
input for each distinct required behavior, combining boundary coverage where
possible. Add cases only when they check another rule or a demonstrated failure;
avoid redundant variants. Derive expectations independently. Creation needs no prior failure,
repair or invented broken candidate. Discard ineffective changes instead of
accumulating exceptions.

For sampled benchmarks, start with the smallest useful focused sample and retained
correct/wrong controls. Increase attempts (`k`) in small steps only after the
current stage meets the user's acceptance criteria and every judge control matches
its independent expectation. On failure, inspect and repair it before growing the
sample. Keep the candidate, model, settings and harness fixed while increasing
sample size, then finish the requested coverage. Do not add sampling stages to an
ordinary exact-case evaluation. The no-test instruction above takes precedence.

Poll yielded session handles until completion; do not start a replacement while
the original call is still live. A slow pending call is not a failed assertion.
Freeze the prompt, judge and runner before the final full run. After a material
change, earlier results do not verify that changed candidate; rerun the suite.
Inspect final settings, exit status, completed case/control counts and outcomes. Resolve ignored-setting warnings before accepting a run; Codex uses
`model_reasoning_effort`, not `reasoning_effort`. Separate semantic failures from
quota, authentication and timeouts.

**Finish the repair before handing off.** For an exact-case evaluation, every
main answer and judge control must match its independent expectation. A failed
assertion, malformed judge verdict or incorrect reply is work to repair, not a
limitation to list in the final response. Read that call's actual request/reply,
fix the responsible prompt, judge or runner, and rerun the same full suite.
Do not stop after merely saving a runner that reports these failures.

For a sampled benchmark, meet the user's requested threshold and coverage;
100% is required only when requested. Do not retry an unchanged candidate hoping
for a lucky sample. Report focused and full results separately. Only an explicit
no-test instruction or a terminal execution block permits an unverified handoff;
state that limit honestly and never count it as passing verification.

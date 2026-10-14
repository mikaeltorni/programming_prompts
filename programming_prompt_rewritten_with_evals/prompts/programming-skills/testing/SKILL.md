---
name: testing
description: >-
  v0.1.59 — Save public checks before code; mutable rejections require public
  observations, and every retained check gains new reads before query code.
---

# Public checks before code

Read the entire request, then finish only the current capability's
checks → baseline → code → cumulative pass → selected commit/delivery before
starting the next capability's checks. Selected commits/workflow own the queue;
testing alone adds no plan or Git requirement. Repairs follow the same order.

## Save complete current checks

Save runnable assertions calling the public entrypoint before application edits.
Derive expectations from the request, original logs and preceding public calls,
never application output or a private-state snapshot. A logged valid-input
regression supplements the other applicable cases; it does not replace them.
Use existing tooling; stdlib assertions/unittest suffice. Apply selected function
docstrings and entry/exit prints to tests, fixtures and helpers from first draft.

For each current form save success and applicable rejection checks:

- Blank input and unknown selectors in a selector grammar. Free-form first
  operands remain data; check malformed reserved forms separately in a mixed
  grammar. Do not call a valid free-form name an unknown selector.
- Missing and extra operands; zero-operand forms need only an extra case.
  Preserve optional and remaining/multi-word text. Use otherwise valid operands
  when isolating shape failures so another error does not mask a broken guard.
- Invalid numeric text for each numeric operand, separately from resource and
  domain failures; retain those cases when numeric acceptance widens.
- Requested domain failures at strict excluded endpoints and beyond them;
  missing/duplicate resources and insufficient funds/capacity with otherwise
  valid input. A valid example alone does not define an outside-range rejection.

One case can cover an actually shared rule, but separate numeric operands and
rejection reasons need applicable cases. Do not invent types, limits, aliases
or wording. Inspect actual loop inputs/assertions before the baseline;
success-only checks are incomplete, including for stateless repairs.

Keep earlier checks except expectations explicitly replaced by this capability.
Update every affected expectation across the cumulative suite while retaining
unrelated cases. Earlier rules come from their own request sentence. Do not
execute future capabilities, even as observers; their rejection may be checked.

## Every mutable rejection observes public state

Catching an exception alone leaves a mutable rejection check unfinished.
This is the public atomicity contract, including malformed inputs and queries.
Do not skip its state assertions because the current parser appears read-only
or rejects before mutation; the checks protect behavior across later edits.
Default to one shared rejection helper used by all earlier/later check files,
with required nonempty public observations. Adapt this pattern to the interface:

```python
def expect_rejection(run_command, command, expected_error, observations):
    """Assert rejection and immediately check independently expected public state.
    Parameters: run_command - public entrypoint; command - rejected input; expected_error - required exception class; observations - nonempty list/tuple of current public call/result pairs.
    Returns: None.
    """
    print(f"run_command={run_command}, command={command}, expected_error={expected_error}, observations={observations}")
    assert observations, "provide public observations"
    try:
        run_command(command)
    except expected_error:
        pass
    else:
        raise AssertionError("expected rejection")
    for query, expected in observations:
        assert run_command(query) == expected
    print(None)
```

Before rejection, reset privately if needed and seed meaningful state through
successful public calls. Creation at zero is meaningful when a read detects
resource loss. A seed may cover a nonmutating rejection loop, but each iteration
asserts its reads immediately after its rejected call, before another rejection,
mutation, reset or reload. A successful mutation afterward is neither a seed
nor a read. Inline checks satisfy this same immediate-observation rule.

Use available affected value reads **and** required history. A mutation's
returned count/value, private equality or history alone cannot replace an
available value query. Use aggregates when they are the only view and disclose
limits. With no public read yet, supply a weaker public probe and record what
it cannot detect; replace it with reads as they arrive. Never use optional None,
empty pairs, a no-op callback or ignored query results to skip observations.

Stateless interfaces skip only state setup/observation, not coverage. Keep valid
empty-domain query rejections separate and empty: their expected exception itself
observes emptiness. Malformed query inputs need meaningful seeded state and reads.

## New reads upgrade every retained rejection before code

When introducing a read query:

1. Save its success and malformed-form checks; its malformed checks observe state.
2. Update the shared helper's observation data and **every retained caller/body**,
   including earliest creation, duplicate, blank/unknown, shape and invalid-number
   cases in all saved files. Add public seeds where missing. New tests do not
   upgrade old bodies. Replace old mutation/second-rejection probes ahead of reads.
3. If older mutable rejection checks exist, run an upgraded older check on its
   own before query code. Its observer executes the new asserted query; an absent
   query makes that older body fail there. Then run the cumulative baseline.
   The new query's own failure does not prove older bodies were upgraded.

Do this for each new read, not at handoff. Verify the actual saved bodies/call
arguments; a successful text-replacement command is not proof the edit matched.
Existing passing checks may protect a refactor. A read whose result is ignored
or whose failure is swallowed observes nothing. Do not leave older observation
pairs empty or retain a mutating probe when the value query now exists.

## Baseline, implementation and cumulative verification

Run saved current checks before application edits and record the actual outcome.
Missing behavior or a correct-path import/missing-file failure for creation is a
valid baseline; distinguish dependency/infrastructure errors. Implement only
this capability, then run every current and retained check with fresh independent
case state. Preserve required sequences; repeat mutable cases in the same process
or another order to verify isolation. Mock unnecessary external effects and use
temporary install/config targets.

After the last edit, run the saved cumulative suite directly with full output
and exit status visible. Verify directory, imports, environment, discovery and
runner actually execute nonzero behavioral assertions for delivered forms.
Call saved functions; put unittest methods in collected classes before the runner.
Before that final run, reread the saved checks from disk: inspect every rejected
call and its immediate observations, and every stateless form's actual rejection
cases. Function names, a draft in memory or a passing success test prove none of
those assertions exists.
Resolve failures, inspect retained rejection observations, and report actual
commands/results and limits before selected commit/delivery or the next capability.

Honor project test prohibitions and static/low-impact direct-check exceptions;
record actual syntax, links, consistency or prescribed evaluation checks.
Do not install a framework or hosted CI without a request.

---
name: testing
description: >-
  v0.1.70 — Before each baseline, save successes and grammar rejections for
  every current form; shared observers upgrade all retained mutable rejections.
---

# Public checks before code

Read the entire request, then finish only the current capability's
checks → baseline → code → cumulative pass → selected commit/delivery before
starting the next capability's checks. Selected commits/workflow own the queue;
testing alone adds no plan or Git requirement. Repairs follow the same order.

Before the first baseline for each capability, inspect its saved assertions
form by form: success; missing/extra operands; invalid text for **each numeric
operand of each form**; and requested domain/resource failures. Include blank
input and an unknown selector when the grammar has selectors. A zero-operand
form still needs an extra-operand rejection. These checks belong in the first
draft, including stateless programs and valid-input repairs. A success-only
baseline is incomplete; do not implement code after one.

For a mutable interface, create its shared rejection helper in that same first
draft and put exception capture there. Every rejection case calls it; an older
bare exception assertion must be rewired when retained. Its one shared query
factory gains every current read **before query code**, so all earlier cases
execute the new assertions too. Before a baseline, inspect actual older bodies
as well as the new file. Do not leave this work until final verification.

## Save complete current checks

Before writing this capability's checks, open the retained checks and find
their rejection/observation helper. Import and extend that same owner from
new check files; do not create another local rejection helper for this Feature.
If older bodies are inline or have local copies, route them through the shared
owner during this checks-before-code step and run them before implementation.

Save runnable assertions calling the public entrypoint before application edits.
Derive expectations from the current contract: the request and original logs
define results and domain rules; this selected policy additionally requires
grammar rejections and public atomicity even without error prose in the request.
Use preceding public calls to derive expected state, never application output
or a private-state snapshot. A logged valid-input
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
Update every affected expectation across the cumulative suite **before the
application edit**, while retaining unrelated cases. When acceptance widens,
remove obsolete rejection expectations and save new successes in this checks
step; keep invalid numeric text and unrelated rejections. Earlier rules come
from their own request sentence. Do not
execute future capabilities, even as observers; their rejection may be checked.

## Every mutable rejection observes public state

Catching an exception alone leaves a mutable rejection check unfinished.
This is the public atomicity contract, including malformed inputs and queries.
Do not skip its state assertions because the current parser appears read-only
or rejects before mutation; the checks protect behavior across later edits.
Keep one shared rejection helper used by all earlier/later check files,
with required nonempty public observations. Keep construction of the current
observation pairs in one shared function, `current_observations(expected_state)`.
It names the current public queries and returns their independently expected
call/result pairs from known fixture data. It never reads application state or
autodetects command support to construct expectations. Every check file imports
the same factory; callers pass expected fixture data, not their own query lists.
Each new read extends that factory once, so older rejection callers automatically
execute it. Add expected fixture data when a new view needs it. Adapt this pattern:

```python
def expect_rejection(run_command, command, expected_error, expected_state, current_observations):
    """Assert rejection and immediately check independently expected public state.
    Parameters: run_command - public entrypoint; command - rejected input; expected_error - required exception class; expected_state - independently expected seeded fixture data; current_observations - shared current-interface call/result factory.
    Returns: None.
    """
    print(f"run_command={run_command}, command={command}, expected_error={expected_error}, expected_state={expected_state}, current_observations={current_observations}")
    # The caller has already publicly seeded this case; do not reset it here.
    observations = tuple(current_observations(expected_state))
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
successful public calls **inside that independent case**. A prior test's final
value is not a seed, even if the runner currently leaves that value behind.
Use the fixture's actual resource identifiers in its seed, rejected input and
affected-state observations. Hardcoding another identifier can mask a numeric
or domain failure behind missing-resource rejection. Keep all other operands
and resources valid except the component this case deliberately rejects.
If a rejection helper owns the reset instead, it must also seed public state
and construct its expected fixture data before the rejected call. It must not
erase a caller's seed and then use stale default expectations.
Creation at zero is meaningful when a read detects
resource loss. A seed may cover a nonmutating rejection loop, but each iteration
asserts its reads immediately after its rejected call, before another rejection,
mutation, reset or reload. A successful mutation afterward is neither a seed
nor a read. Inline checks satisfy this same immediate-observation rule.
If a case clears state or reloads the module, its earlier seed is gone:
seed again before a malformed rejection, including malformed read/reset forms.
An intentionally empty valid-domain query remains the separate exemption below.

Use available affected value reads **and** required history. A mutation's
returned count/value, private equality or history alone cannot replace an
available value query. Use aggregates when they are the only view and disclose
limits. With no public read yet, supply a weaker public probe and record what
it cannot detect; replace it with reads as they arrive. Never use optional None,
empty pairs, a no-op callback or ignored query results to skip observations.
Once a read exists, remove earlier mutating probes from the observation path:
putting reads after the probe still checks state after another mutation.
Use only public forms in the request or existing project contract. Do not add
an application command solely to obtain an observer; use existing aggregate
views and disclose their limitations instead.

Stateless interfaces skip only state setup/observation, not coverage. Keep valid
empty-domain query rejections separate and empty: their expected exception itself
observes emptiness. Malformed query inputs need meaningful seeded state and reads.

## New reads upgrade every retained rejection before code

When introducing a read query:

Here, current means the current capability's requested contract, not what the
old implementation already supports. Adding this read to older test bodies in
this capability is not executing a future capability in their original revision.
Their file/class names do not freeze their observation logic. A missing current
query should fail the baseline; never autodetect it and silently keep old probes.

1. Save its success and malformed-form checks; its malformed checks observe state.
2. Update the shared helper's observation data and **every retained caller/body**,
   including earliest creation, duplicate, blank/unknown, shape and invalid-number
   cases in all saved files. Add public seeds where missing. New tests do not
   upgrade old bodies. Replace old mutation/second-rejection probes ahead of reads.
   Each newly introduced query is asserted after every retained rejection;
   keeping only an earlier aggregate or subset of the current queries is incomplete.
   Extend the observation set; a new query does not replace an earlier read
   unless the request explicitly removes that earlier form. A count cannot
   detect a changed value, and a value aggregate cannot detect every lost resource.
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

Run the **newly saved current checks** before application edits and record the
actual outcome. Invoke their new file/function or verify discovery collects
those assertions; running only an older file is not the current baseline.
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
If a fixture or expected value is wrong, derive its correction from the original
contract and preceding public calls, preserve the reported behavior, and rerun
the same saved check plus the cumulative suite. Never copy application output
into an expectation merely to obtain a pass or stop with that repair unfinished.
Resolve failures, inspect retained rejection observations, and report actual
commands/results and limits before selected commit/delivery or the next capability.

Honor project test prohibitions and static/low-impact direct-check exceptions;
record actual syntax, links, consistency or prescribed evaluation checks.
Do not install a framework or hosted CI without a request.

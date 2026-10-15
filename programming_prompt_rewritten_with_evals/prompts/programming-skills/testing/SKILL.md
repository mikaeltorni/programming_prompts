---
name: testing
description: >-
  v0.1.90 — Save complete public checks before code; one mutable rejection helper
  seeds state and asserts every current read through one growing factory.
---

# Public checks before code

Read the full request and existing checks. Work on one current capability:
**save complete checks → run baseline → implement → run cumulative checks →
selected commit/delivery**. Repairs follow the same order. Testing alone adds
no plan or Git requirement. Use existing tooling; no new framework or hosted CI
is required. Honor project test prohibitions and static/low-impact direct-check
exceptions with actual syntax, link, consistency or evaluation checks.

## Build the rejection path first

For a mutable API, write these shared owners before the first test:

- `seed_case()` resets privately if needed, then creates meaningful state through
  successful CURRENT public calls and returns independent expected data. Compute
  expectations from known inputs and the contract, never unchecked call results
  or private application snapshots. A private zero/default is not a public seed;
  public resource creation at zero can expose resource loss. The helper's caller
  must not default to an empty setup or a zero-iteration public loop.
- `current_observations(expected_state)` builds every current public read and
  expected result from that data. Callers pass expected data, never their own
  frozen query lists. No application reads or support autodetection construct
  expectations. Known-input bookkeeping is independent, but is not itself a read.
- `expect_rejection()` calls the seed, rejects, then immediately asserts all those
  reads. Only this helper captures expected exceptions: individual mutable tests
  call it instead of using `assertRaises`, `pytest.raises` or `try`/`except`.
  Rewire older captures in every retained file into the same helper and factory.

Adapt this helper to the public entrypoint:

```python
def expect_rejection(command, expected_error=ValueError):
    """Seed, reject input and immediately assert independently expected public state.
    Parameters: command - rejected input using the fixture's resources; expected_error - required exception class.
    Returns: None.
    """
    print(f"command={command}, expected_error={expected_error}")
    expected_state = seed_case()
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

Every rejected call needs its seed AFTER the last private clear/write/reload and
BEFORE rejection. Another test's final state is not a seed; never erase a seed
before rejecting. A nonmutating rejection loop may share one seed, but each
iteration asserts reads immediately before the next rejection, mutation or reset.
A later successful mutation is not a read or a seed for an earlier rejection.
Different fixtures still publicly seed matching resource identifiers and return
independent expected data. Blank, unknown and malformed query/reset cases use
meaningful seeded state too.

Assert every available affected value, cardinality and required history view.
Count alone, history alone, private equality, ignored query results, empty
observations and no-op callbacks cannot replace available value reads. Use an
aggregate when that is the only read and state its limit. With NO current public
read, use a weaker public probe and state its limit; replace that mutation probe
when a read arrives. Never invent an observer API or execute a future command.

Stateless APIs skip only state setup/observation and may capture exceptions
directly. Valid queries rejecting an intentionally empty domain observe emptiness
through that exception, including after reset: keep those cases empty, with no
reseed or extra read. This exemption never covers malformed input.

## Save every current case before application edits

In the first saved draft include:

| Current form/rule | Saved public assertions |
| --- | --- |
| Selector grammar | Blank and unknown selectors. |
| Each command/query | Every specified success/result variant, including empty results; missing and extra operands, only extra for zero-operand forms. |
| Each numeric operand | Invalid text with other operands/resources valid. |
| Requested domain/resources | Strict excluded endpoints AND beyond; positive values need zero AND negative rejection; required empty-domain, missing/duplicate resource and insufficient funds/capacity cases. |

Use the request and original failure logs for results and domain rules. Grammar
rejections and public atomicity are also required by this policy without error
prose. Do not invent bounds, types, aliases or error wording. Free-form first
operands are data, not unknown selectors; preserve optional/multi-word/remainder
text without invented extra-operand restrictions. A case set can cover an actually
shared rule; distinct numeric operands and rejection reasons still need cases.
One retained invalid-text case for an operand survives numeric widening; no new
junk spelling is required. A valid-input regression or success-only baseline is
incomplete. Use real fixture identifiers so missing resources cannot mask the
numeric/domain error being checked.

When acceptance changes, update every replaced expectation and add new successes
across the suite BEFORE application edits; keep unaffected checks and invalid
numeric text. Derive corrections from the contract and preceding public calls,
never copy actual output. Prefer one cumulative module and direct public calls;
existing multiple files share the same rejection helper and observation factory.

## Grow the observation factory before each new read

1. Save the new read's successes and malformed cases. Extend expected fixture data
   and ADD its query pairs to the one factory. Retain every earlier read unless
   the request removes it; a new value view never silently replaces an old one.
   Replace earlier mutation probes.
2. Inspect EVERY retained rejection body/caller in EVERY executed file, including
   earliest creation, duplicate, blank, unknown, shape and numeric cases. All use
   that factory with actual nonempty seeds and asserted current reads. A newer
   test alone does not upgrade an older body; names do not freeze old observers.
3. Run an upgraded older rejection alone, then the cumulative baseline, BEFORE
   query code. It must reach the newly asserted read. Unsupported-query failure
   is the expected red baseline: do not catch it, skip it, make it conditional or
   implement query code before the upgraded checks.

Current means this capability's requested interface. Updating older checks now
is required, not early execution in their original revision. Future capabilities
stay unsupported and unexecuted, even as observers; probing their rejection is
allowed. Before each baseline, briefly report the actual saved success/rejection
inputs, helper, public seed, asserted reads and upgraded older-case result.

## Finish the actual cumulative run

Invoke these newly saved checks before application edits. A correct-path missing
entrypoint/import is a valid creation baseline; distinguish infrastructure errors.
Do not add a stub or rewrite a valid import just to turn that expected failure
green. Existing passing checks can protect a refactor.

Use fresh independent case state; preserve required multi-call sequences and
repeat/reorder mutable cases to check isolation. Mock unnecessary external effects
and use temporary install/config targets. Resolve leaked fixture state and wrong
expectations, then rerun the SAME regression and cumulative suite.

After the final application/check edit, reopen every saved rejection capture and
its enclosing function. Mutable captures belong only to the shared helper; follow
every caller through its public seed and all current asserted reads. Recheck the
factory's retained pairs. Run the cumulative suite directly with full output and
exit status, correct directory/imports/environment/discovery and nonzero behavioral
assertions. Call saved functions and put collected methods before the runner.
Apply selected function docstrings and each function's own entry/exit prints from
the first draft, including tests and fixtures. Fix failures before selected commit,
delivery or the next capability; report actual commands/results and limits.

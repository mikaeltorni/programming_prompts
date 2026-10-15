---
name: testing
description: >-
  v0.1.87 — Save form-complete checks first; mutable rejection cases call one
  fixture/rejection/read helper, and each new read extends its shared factory.
---

# Public checks before code

Read the full request. For one current capability at a time, complete:
**save checks → run baseline → implement → run cumulative checks → selected
commit/delivery**. Repairs use the same cycle. Selected commits/workflow own
the queue; testing alone adds no plan or Git requirement. Never execute a
future capability, even as an observer; checking that it is rejected is allowed.

**Write the shared mutable rejection helper before the first test. Put expected
exception capture only there; every rejection case, including older cases, calls
it.** Its fixture publicly seeds state and it immediately asserts every current read.
Adding a read extends that helper's shared observation factory before query code;
run an upgraded older case alone, then the cumulative baseline. A missing current
query is the expected red baseline: keep its assertion and implement the query
next. Never catch that failure, skip its read or make the observer conditional.

## 1. Save the complete current checks

Use the public entrypoint and existing tooling. Save successes and these
applicable rejections in the first draft, before any application edit:

| Form or rule | Required checks |
| --- | --- |
| Selector grammar | Blank input and an unknown selector. |
| Each command/query | Every specified result variant, including empty results; missing and extra operands (only extra for zero-operand forms). |
| Each numeric operand | Invalid numeric text, with other operands/resources valid. |
| Requested domain/resource rules | Strict excluded endpoints and beyond, empty-domain queries, missing/duplicate resources, insufficient funds/capacity, as specified. |

When the request requires positive numbers, check both zero and a negative value;
the excluded endpoint and a value beyond it are separate cases.

Free-form first operands are data, not unknown selectors. Preserve optional
and remaining/multi-word text; do not invent extra-operand restrictions for it.
One case can cover an actually shared rule, but distinct numeric operands and
rejection reasons need their applicable cases. A logged valid-input regression
does not replace grammar or other required cases; stateless repairs need them too.

The request and original logs define results and domain rules; this policy also
requires grammar rejections and public atomicity without explicit error prose.
Derive expectations from that contract and known preceding public calls, never
unchecked application output or private snapshots. Expected fixture bookkeeping
calculated from known command operands is independent; it is not a public read.
Do not invent types, aliases, bounds or error wording. Use actual fixture resource
identifiers so a missing resource cannot mask the intended numeric/domain error.

Read every retained check file before adding new checks. Keep unrelated checks.
Prefer one cumulative check module and direct public calls over generated scripts
or separate runners; existing multi-file suites share the same helper and factory.
Before code changes acceptance, update every replaced expectation and add the
new successes across the suite; retain invalid numeric text when numbers widen.
A retained invalid-text case still covers that operand; no new junk spelling is
needed for each revision. A passing success-only baseline is incomplete.
Before running it, briefly report the actual saved success/rejection inputs for
each form. For mutable cases name the shared helper, public seed, asserted reads
and upgraded older-case baseline; inspect every retained body, not only new tests.

## 2. Make each mutable rejection observe public state

Use one shared rejection helper and one shared
`current_observations(expected_state)` factory across all check files. Rewire
older inline/local copies into this owner. The factory constructs all current
public command/expected-result pairs from independent fixture data; it never
reads actual application state or autodetects command support. Callers supply
expected data, not their own frozen query lists. The shared `seed_case()` resets
privately if needed, then establishes meaningful state through successful current
public calls and returns its independently known expected data. Compute that data
from the fixture inputs/contract, never the unchecked return of a seed call.
The rejection helper obtains its expected data from this fixture; callers cannot
accidentally request an empty setup. Use this same fixture for blank, unknown and
malformed query/reset cases. If a case needs another fixture, it follows the same
public-seed/independent-data contract and uses identifiers matching its rejected input.
Adapt the following pattern to the actual entrypoint; do not generate an exception loop
inside each test:

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

Each helper call seeds meaningful state, rejects, and immediately asserts all
current affected-state reads. After that public seed, do not erase it. After any private
fixture write/reload or clear, seed again before malformed input. Another test's
final state is not a seed. Creation at zero can detect resource loss. A seed may
cover a nonmutating rejection loop, but each iteration observes state before the
next rejection, mutation or reset. A successful mutation afterward is not a read.
An empty collection/default or zero-iteration setup is not a meaningful seed for
malformed inputs. The separate valid empty-domain query case below stays empty.

Use every current value/cardinality view and required history. Counts, private
equality, history alone, ignored queries, empty observations and no-op callbacks
cannot replace available value reads. If only an aggregate exists, use it and
state its limit. With no public read yet, use a weaker public probe and record its
limit; replace that mutating probe when a read arrives. Do not invent an observer API.

Stateless interfaces skip only state setup/observation and may capture exceptions
directly. A valid query rejecting an
intentionally empty domain observes emptiness through its exception, including
after reset; keep that case empty. Malformed queries/reset forms still need seeds
and immediate reads.

## 3. Upgrade old rejections before new query code

For each newly introduced read, during that capability's checks step:

1. Add its success and malformed-form checks. Extend the shared observation
   factory and expected fixture data with the new read, retaining earlier reads
   unless the request removes them. Replace old mutation probes.
2. Inspect and upgrade every retained rejection body/caller in every file:
   earliest creation/duplicate/blank/unknown/shape/numeric cases as well as newer
   cases. Add missing seeds. New tests do not upgrade old bodies automatically.
3. Run an upgraded older case alone before query code: it must reach the new
   asserted query. Then run the current cumulative baseline. A failure only in
   the new query's own test does not prove the older body was upgraded.

Current means this capability's requested interface, not old implementation
support. Updating older bodies now is not executing a future capability in their
original revision. Do not freeze observers by file/class name or swallow missing
queries. Before code, briefly report actual saved cases per form, the shared
helper, public seeds, asserted views and the older-case baseline you just ran.
Include optional queries once implemented; inspect all files the runner executes.

## 4. Baseline, implementation and final verification

Actually invoke the newly saved checks before application edits; running only
an older file is not this baseline. Missing behavior or a correct-path missing
entrypoint/import is valid for creation; distinguish infrastructure failures.
Implement only the current capability. Apply selected commenting/logging to
checks, fixtures and helpers from their first draft.

Run current and retained checks in fresh independent case state; preserve required
multi-call sequences and repeat/reorder mutable cases to verify isolation. Mock
unnecessary external effects and use temporary install/config targets. Fix incorrect
fixtures/expectations from the contract and preceding calls, then rerun the same
regression and cumulative suite; never copy actual output to make a test pass.
If a cumulative run exposes leaked fixture state, repair that case's isolation and
rerun; a failed implementation run leaves this capability unfinished.

After the last application/check edit, reread the saved cases and run the cumulative
suite directly with full output and exit status. Verify directory, imports,
environment, discovery and nonzero behavioral assertions. Call saved functions;
put collected methods before the runner. Inspect each rejection and its immediate
reads, not merely names or a previous green result. Resolve failures and report
actual commands/results and limits before commit/delivery or the next capability.

Honor project test prohibitions and static/low-impact direct-check exceptions;
record actual syntax/link/consistency/evaluation checks instead. No new framework
or hosted CI is required.

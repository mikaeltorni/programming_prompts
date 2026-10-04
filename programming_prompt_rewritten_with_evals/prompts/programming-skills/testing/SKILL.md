---
name: testing
description: >-
  v1.0.17 — Executable code creation and behavior changes require saved,
  runnable public-interface checks in each working revision. Run them with
  fresh state; honor static-content and project verification exceptions.
---

# Test the changed behavior

Own verification during implementation and before delivery. These rules apply
without workflow. With workflow selected, perform them inside `Write code`;
with commits selected, finish the current capability's checks and commit before
starting the next capability. Follow repository AGENTS.md and CLAUDE.md for
verification commands and restrictions on creating tests.

## Follow these gates for every working revision

1. **Read the contract and existing checks.** Include setup paragraphs, original
   failure logs and shared validation rules, not only the newest stage examples.
   Identify the current capability and earlier behavior that still applies.
   Keep later commands and observation APIs deferred to their own revision.
2. **Save the coverage inventory before the application edit.** Choose the
   normal test location and runner. Beside the runnable checks, map each
   applicable success, boundary, rejection reason and unchanged-state rule to
   an actual executable case and its independently expected result. Name the
   case; a list of stages or test method titles alone is not coverage. For
   rejection without mutation, name the required public observations too.
3. **Write or extend the saved assertions.** Preserve every unaffected case.
   Before replacing a method or file, transfer its still-required assertions;
   never reduce the suite to the latest examples. Retire an expectation only
   when the request explicitly replaces it. Do not assert both an old rule and
   its replacement in the final suite; history retains the earlier checks.
4. **Revisit all rejection cases when adding a query.** If this revision first
   exposes a public observation of stored state, add that observation to every
   earlier applicable rejection test now. Older stage classes are part of the
   current suite. Apply the same review when adding more state/history queries
   or changing their output contract.
5. **Run and inspect the accumulated suite before committing.** Confirm the
   runner discovers and executes assertions. Follow every inventory entry to
   its actual assertions, including the statement immediately after each
   rejected operation. Resolve missing coverage even when the runner passes.
   Inspect complete added or changed test/helper/fixture bodies for independently
   selected commenting/logging rules. Commit the saved checks with this
   capability; do not advance merely because its tests passed.

### Rejection without mutation: observe before doing anything else

For every required rejection class, seed known nonempty state through the
public interface. Attempt one rejected input, then assert independently
expected state through the currently available public queries **before** the
next rejected input, successful mutation, reset or fixture reload. Keep that
sequence in one executable case; a shared reject-and-observe helper may serve
several inputs. Malformed dispatch, token conversion and domain errors all need
this sequence when the contract requires unchanged state.

Task examples may show a rejection followed by a successful mutation. That
checks recovery; insert the query before continuing the example. A later
successful update's count, a private-state assertion, or a comment saying
“unchanged” cannot replace the public observation. Private access is permitted
for fixture setup only. Use observations that expose the affected values,
not just a count or aggregate that can stay constant while values change.
Check every affected resource and stored history when the contract requires it
and the current revision exposes it.

Adapt this pattern to the actual contract and existing runner. These placeholders
are not commands to add or a reason to install a new framework:

```python
# Seed known state and independently expected results first.
with self.assertRaises(EXPECTED_EXCEPTION):
    PUBLIC_ENTRYPOINT(REJECTED_INPUT)
self.assertEqual(PUBLIC_ENTRYPOINT(STATE_QUERY), EXPECTED_STATE_RESULT)
# Assert any other required resource/history observations here.
# Only then continue to another rejection, mutation, reset or reload.
```

When no public query exists yet, use the strongest observation the current
interface supports and record that limit in the inventory. Do not introduce a
future query or reset API just for testing. Gate 4 requires upgrading those
checks as soon as a suitable query exists. Before each commit, review **all**
saved rejection blocks, not only this revision's new tests: an exception-only
block or one followed by a mutation remains incomplete when the contract
requires a now-observable state guarantee.

### Cover each required validation class

Use concrete public inputs and expected results from the request. Do not copy
the implementation's answer or invent error strings, unsupported inputs or
extra restrictions. Exercise meaningful success and boundary cases, nontrivial
arguments, the default/no-argument path when supported, each changed flag, and
accepted multi-word or quoted inputs.

Map failures by operation and rejection reason. A missing-resource failure does
not cover malformed shape, and one domain rejection does not cover another.
When specified, save empty-command, unknown-operation and malformed-argument
assertions in the first revision supporting dispatch; preserve them through
later revisions. Cover missing and extra arguments where rejected. Each new
no-argument operation with a separate validation path needs an extra-argument
assertion; similar conditions in separate branches are separate paths. Reuse
representative coverage only for operations delegating to the same validation
path. Do not enumerate every invalid spelling.

When formerly invalid inputs become valid, replace their obsolete rejection
assertions with acceptance checks and retain inputs that are still invalid.
Do not leave an empty negative loop, a no-op test, or a before/after read with
no rejected operation. Changing numeric acceptance does not retire empty and
unknown commands or other shared rules. New history/state checks extend earlier
coverage; they do not replace earlier rejection classes. A test name or green
runner is not evidence that its required input or observation was asserted.

## Choose the project's verification path

For executable code creation or behavior changes, save runnable checks before
executing them. Reuse the project's framework and fixtures; use a small stdlib
assertion script if there is no framework. Record the exact runner with the
checks or existing test documentation. Use explicit discovery when necessary;
a zero-test success is not verification. Terminal-only `python -c` or heredoc
assertions may supplement saved checks but cannot replace them. A small local
program with observable results still needs useful regression assertions.

For a reported defect, save its exact public-interface reproducer and the
independently specified expected result before editing the broken behavior.
Copy the expected result accurately from original logs when supplied. Confirm
that saved regression fails for the defect and passes after the fix; separate
setup/dependency failures. Nearby boundaries supplement the reproducer. For
refactors, run relevant existing tests before and after the extraction.

Prompt, documentation and static-data changes use syntax, links, consistency or
their documented evaluation mechanism. Honor a project prohibition on new test
suites. For reversible low-impact changes without useful regression assertions,
use direct verification. Do not install a new framework or hosted CI without a
request. These exceptions do not turn executable program creation into static
content or waive an applicable saved-check requirement.

## Isolate cases and external effects

Establish fresh state before **every** independent case through the runner's
fixture lifecycle: a setup hook, fresh module instance or consistent per-case
reset. Preserve state within requested multi-call sequences. Resetting only new
tests leaves older cases dependent on order. A case may leave state behind when
the next case establishes fresh state. In addition to the normal run, repeat a
mutable suite in the same process or another order through those fixtures;
a script may explicitly reload/reset between sequences. Check representative
earlier capabilities after shared parsing, dispatch or helper changes. Do not
weaken expectations to hide unexplained failures.

Mock or inject network clients, launches, clocks and external systems when real
effects are unnecessary. Patch where the defining module resolves the dependency;
a re-export patch may leave a real launcher active. Keep stubs consistent with
the production import path. Assert captured arguments, environment and results;
capture permitted diagnostic logging without treating it as a return mismatch.
Use temporary homes and fixture repositories for deployment/configuration checks.
Nonvisual tests must not open GUI windows, terminals or dialogs. Deliberate
visual checks may do so when required. Preserve user data and the desktop;
never let a test reboot, power off, log out or kill the session.

## Apply independently selected function contracts

Before the first test write, check which function skills are enabled. With
commenting selected, document purpose, actual parameters and returns inline
for every authored test, helper and fixture. An assertion-only method documents
`Parameters: self - the test instance.` and `Returns: None.` With logging
selected, print the method's parameters first and `None` after its final normal
assertion. Revisions must preserve those docstrings and final traces. The
application's documentation/prints do not satisfy its caller's obligations.
Apply this to the initial failing regression and every changed method body.
Testing does not enable an unselected companion.

With both companions selected, adapt this generic shape to the request:

```python
def test_requested_behavior(self):
    """Check the requested public behavior.

    Parameters: self - the test instance.
    Returns: None.
    """
    print(f"self={object.__repr__(self)}")
    self.assertEqual(PUBLIC_ENTRYPOINT(REQUESTED_INPUT), EXPECTED_RESULT)
    print(None)
```

## Verify tooling, installation and delivery

Run relevant tests and configured lint, type or build checks using the existing
environment and dependency policy; do not resolve dependencies ad hoc. When
adding/extracting installed modules, check installer copy lists or manifests
include imports and assets. Exercise the installed entrypoint in an isolated
target when feasible; checkout-only imports do not prove installation works.
For sourced shell modules, exercise the real shared dependency shape; check
shell syntax and target-system paths/conventions where relevant.

Investigate relevant logs and distinguish pre-existing failures, infrastructure
limits and new defects. Broaden or repeat checks only for changes, failures or
unresolved concerns. Syntax alone does not establish runtime behavior. Review
the final diff and actual coverage before committing or handing off. Report
commands actually run, observed results, and checks not run with their concrete
reason. Written tests, inspection and planned commands are not execution. If
execution is unavailable, state the strongest evidence and its limit; do not
claim full runtime verification.

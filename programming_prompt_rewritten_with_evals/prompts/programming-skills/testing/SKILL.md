---
name: testing
description: >-
  v1.0.12 — Executable code creation and behavior changes require saved,
  runnable public-interface checks in each working revision. Run them with
  fresh state; honor static-content and project verification exceptions.
---

# Test the changed behavior

Own verification during implementation and before delivery. Work independently
of workflow; when workflow is selected, perform these checks inside its code
phase rather than adding another phase. When commits is selected, include the
current Feature's checks and tests in that commit; do not implement or test
future capabilities early. Repository AGENTS.md and CLAUDE.md determine local
verification commands and any restrictions on creating tests.

## Choose checks from the contract

For code creation or behavior changes, choose the saved test/check path and its
normal runner before the first application source write. Save the current
capability's assertions there before executing verification, and include them
in that capability's commit. At every commit gate, inspect the actual saved
artifact and its public-interface assertions. `python -c` and shell heredoc
assertions alone leave this obligation unfinished, even when they pass every
example. Do not defer saved checks to a final documentation or cleanup commit.
A new executable program with observable command results has useful regression
assertions; being short, local or reversible does not make its creation a
static-content exception. A final claim that no checks were saved means this
requirement is unfinished. Refactors, static content and project prohibitions
keep the allowances below.

Inspect the request, public interface, existing tests, manifests, and documented
commands before choosing checks. Test observable behavior against the request,
not a copy of the implementation or whatever result it currently returns.
Reuse the project's test framework and fixtures. Do not install a new framework
or add hosted CI unless the user requests it.
Record the exact runnable command with the saved checks (a file comment or
existing project documentation is sufficient). Run that command and confirm it
actually executes assertions; a successful exit with zero discovered tests is
not verification. Choose explicit discovery or a runnable script when default
discovery does not include the saved location.

Before writing checks, map the current capability and shared request rules to
concrete public-interface inputs and independently expected results. Include
success, meaningful boundaries, specified failures, and any required unchanged
state. Read setup paragraphs and original failure logs as well as stage examples;
examples do not replace shared validation rules. Keep this coverage map scoped
to capabilities implemented so far. Extend it when a capability is introduced,
revise only explicitly replaced rules, and inspect the saved assertions against
it before every commit. A passing runner does not close an uncovered rule. Map failures by operation
and rejection reason, not just a single "invalid command" category: a shape
check for one operation does not cover another independently validated shape,
and one domain error does not cover a different explicitly required rejection.
For each implemented operation, retain its applicable malformed shape check
and each specified domain rejection through later revisions.

When empty commands, unknown operations or invalid argument shapes are explicitly
rejected, save a representative assertion for each specified class. Domain errors
such as missing resources do not cover malformed dispatch. For changed command
shapes, cover missing or extra arguments where the contract rejects them; include
an extra-argument case when adding a no-argument command with its own validation
path. A separate dispatch branch has its own rejection path even when its
condition resembles another branch: save an extra-argument assertion for each
new no-argument operation. Reuse coverage only when the operations delegate to
the same validation path. Do not invent restrictions
or enumerate every spelling of an invalid input. Put these shared validation
assertions in the first working revision that supports dispatch. When extending
the suite, retain those cases explicitly rather than reconstructing only the
latest command examples. Read their actual inputs at each commit gate; a
negative-test method name does not establish empty or unknown input coverage.

When the contract requires rejection without mutation, the coverage map must
pair each rejection class with its immediate public observation of unchanged
state. This applies to malformed commands and failed token conversion as well
as domain errors; checking only that they raise leaves that rule uncovered.
Seed known, nonempty state, attempt one rejected operation, then observe the
specified state before another rejected operation, successful mutation or
reset. Keep this sequence inside one case. A shared assertion helper may perform
the same reject-and-observe sequence for several inputs.

Check every affected resource when the contract requires it, including stored
history when available at this stage. Choose observations that expose changes
to the values, not only their count or an aggregate that could stay constant
while individual values change. Use only public observations already supported
in this revision; extend them when later capabilities make more state visible,
without implementing a future observation API early. A later successful update
with the expected count does not establish that the earlier contents survived.
At each commit gate, locate the actual post-rejection assertions in the saved
checks for every required rejection class; a passing runner or an exception-only
negative test does not close missing state-preservation coverage.

- For a reported bug, add a focused regression test before the fix when a
  practical test path exists. Save the exact reported public-interface input
  and its independently specified expected result before editing the broken
  behavior; nearby boundaries supplement that reproducer. When logs supply the
  expected result, copy it accurately into the assertion. Confirm the saved
  regression fails for the reported defect, then passes after the fix. Separate
  dependency or setup failures from that result.
- For behavior changes and new capabilities, save runnable tests in the
  repository's normal test location before executing them. A small stdlib
  assertion script is enough when there is no framework; terminal-only
  assertions do not replace reusable regression coverage. Cover meaningful
  success cases, applicable boundaries, and specified failure behavior. For
  refactors, run relevant existing tests before and after extraction.
- For reversible, low-impact changes without a useful regression assertion,
  use direct verification. Prompt, documentation, and static-data changes use
  syntax, links, consistency, or their documented evaluation mechanism rather
  than artificial unit tests. Honor a repository that forbids new test suites.
- Exercise the public entrypoint, including non-trivial arguments and the
  default/no-argument path when supported. For a command surface, cover each
  changed flag and multi-word or quoted inputs when accepted. Do not invent
  error strings, input restrictions, or behavior absent from the specification.
- Isolate mutable state so cases are repeatable and do not depend on order.
  Establish a fresh state before **every** independent case through a shared
  fixture/setup hook, a fresh module instance, or a consistent per-case reset;
  resetting only newly added tests leaves earlier tests dependent on prior use.
  Preserve state within a requested multi-call sequence. Fixture setup may
  reset private state when necessary, but behavioral assertions still exercise
  the public interface. Do not add a public reset API just for tests or call a
  reset command before the stage that introduces it. For a mutable module, run
  its saved cases again in the same process or a different order to check the
  isolation mechanism, in addition to the normal runner. Repeat through the
  saved runner's fixture lifecycle: framework setup runs before each case, and
  a script's explicit reload/reset between sequences is a valid fixture. A
  case may leave state behind when the next case establishes fresh state.
  Check representative earlier capabilities after changing shared parsing,
  dispatch, or helpers. Do not weaken assertions or alter expected results
  merely to make an unexplained failure green.

## Preserve runnable verification across revisions

For code creation and behavior changes, save runnable checks in the task
repository before running them, and include the current capability's checks in
its commit. Static content and project-specific test prohibitions retain the
direct-verification allowances above. A terminal heredoc with assertions can add
an exploratory check, but it does not replace a saved runnable regression.
For staged changes, extend the saved checks through the existing test path.
Keep coverage for earlier behavior that still applies; replace only expectations
explicitly retired by the request. Earlier commits retain the checks for retired
rules, so the final suite must not assert both the old and replacement behavior.
Do not overwrite the saved suite with only the newest stage's examples and lose
unaffected regressions. If consolidating or rewriting tests, inventory the
existing assertions first and transfer every still-required success and failure
class into the replacement before removing the old cases. New state/history
checks extend that coverage; they do not replace earlier rejection rules. When formerly invalid inputs become valid, revise or
remove their obsolete rejection assertions and keep representative inputs that
remain invalid under the current contract. Do not leave an empty negative-test
loop or replace it with a before/after read that never attempts an operation.
Retain meaningful failure and unchanged-state checks elsewhere in the suite;
assert expected state independently before checking that a rejected operation
preserves it. Run the accumulated applicable checks before committing.
At this gate, inspect actual executable assertions for every still-applicable
shared validation class. Keep empty-command and unknown-operation checks when
those are required; revising numeric input or one operation's arguments does
not retire those shared rules. If a negative-case loop is replaced, transfer
its unaffected assertions before removing it. Coverage of operation-specific
errors cannot substitute for these dispatch checks.

Before saving the first test file, check independently selected function skills.
When commenting is selected, every test/helper/fixture method needs a purpose,
`Parameters: self - the test instance.` (or its actual parameters) and
`Returns: None` for an assertion-only method. When logging is selected, print
`self=` first and `None` after its final assertion. The application's docstrings
and prints do not satisfy these obligations in its caller. Apply this to the
initial failing regression too, then inspect the entire body of every added or
changed test/helper/fixture before committing. Revisions to assertions must
preserve these independently selected function contracts: with logging selected,
the final normal path still prints `None` after its last assertion; with
commenting selected, its inline parameter and return documentation remains
complete. A passing behavioral suite does not check these structural contracts.
This does not enable an unselected companion.

With both companions selected, adapt this test-method shape to the request;
the uppercase values below stand for the actual public-interface input and
independently expected result, not extra requirements or tests to copy unchanged:

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


## Keep automated checks isolated

Mock or inject network clients, process launches, clocks, and external systems
when their real effects are unnecessary. Non-visual tests must not open GUI
windows, terminal emulators, or dialogs. Deliberate visual checks may do so
when required by the task. Use temporary homes and fixture repositories for
configuration and deployment tests; preserve the real user's data and session.
Never let a test reboot, power off, log out, or kill the desktop session.

Patch mocks at the module where the function resolves the dependency. Patching
only a re-export does not intercept its defining module's real launcher. Assert
on captured arguments, environment, and results instead of launching real tools.
Keep shared dependency stubs consistent with the production import/source path.
Capture diagnostic output when needed without treating permitted logging as a
failure of the function's return contract.

## Verify installation and existing tooling

When adding or extracting installed modules, check that local imports and assets
are included in installer copy lists or package manifests. Exercise the installed
entrypoint in an isolated target when feasible; a checkout-only import is not
proof that installation works. For sourced shell modules, exercise their real
shared dependency shape. Check shell syntax and target-system paths/conventions
when relevant.

Run relevant tests and the project's configured lint, type, or build checks.
Use its existing environment and dependency policy; do not resolve dependencies
ad hoc. Investigate failures and relevant logs, distinguishing pre-existing
failures and infrastructure limits from defects introduced by the change.
Broaden or repeat checks only when changes, failures, or unresolved concerns
justify it. A passed syntax check alone does not verify changed runtime behavior.

## Report what was verified

Before committing or handing off, review the diff for accidental changes and
confirm applicable checks passed. Report the commands actually run, observed
results, and any checks that could not run with their concrete reason. Never
claim execution from a written test, source inspection, or a planned command.
When execution is unavailable, provide the strongest supported direct evidence
and state the remaining limit; do not label the change fully runtime-verified.

---
name: testing
description: >-
  v0.1.117 — Write focused tests for the requested behavior, run them, and fix
  failures before reporting completion.
---

# Testing

Complete the requested work and runnable tests before the final reply. Continue
past an empty initial file search to create the missing requested files.
Diagnosis or a failed run is a step toward repair; continue while repair is possible.

Read the request, repository guidance and existing tests. Use the project's
current test tools and conventions; do not add a framework or CI unless asked.
If no test runner exists, use stdlib unittest or a saved plain-assertion script.

Write or update runnable tests through the public interface:

- Assert correct independent results for every requested command/API form through
  the named public entrypoint, including optional forms when implemented and
  explicitly specified result variants. Internal-class tests, return-type checks
  or a partial wrapper smoke check do not cover an omitted public form. Do not use
  unchecked application output as its own expectation.
- Follow explicit revisions: replace superseded rejection assertions with success
  checks for newly accepted input. Read the full applicable contract before
  changing code to satisfy a failing test; the test may enforce an obsolete rule.
- Cover relevant edge cases and invalid inputs: blank/unknown commands, wrong
  operand counts, invalid numeric text and requested domain/resource failures.
  Typed operands require malformed-input checks even when the task lists only
  successful commands.
  Free-form data is not an unknown selector.
  Preserve optional inputs; do not invent restrictions or test every spelling of
  the same rule. Assert the error return or exception for each invalid case;
  calling it and checking only unchanged state does not verify rejection.
- For stateful behavior, test meaningful multi-call sequences and check that
  rejected operations preserve state. Prefer public reads; a copied state
  snapshot or an asserted public result showing the prior state is also valid.
  Keep independent fixtures isolated and derive expectations from preceding calls.
- For a reported bug, save and run a regression reproducing it before the fix.
  Keep that regression with the existing tests.

Before finishing, inspect the saved tests for successful results, relevant invalid
inputs and required state checks. Add missing assertions, then run the full
relevant suite after the last edit. Confirm it collected real tests and passed;
on failure, diagnose the cause and rerun after repair. Derive any corrected
expectation from the contract and preceding calls. A traceback remains a failure
even when a later shell command exits zero. Use temporary targets or mocks for
external effects.

Report the actual test command and result, including anything unverified. Respect
explicit no-test instructions and documented direct-check exceptions. Testing by
itself does not require a plan, feature ledger or Git commits; selected workflow
and commit policies govern those separately.

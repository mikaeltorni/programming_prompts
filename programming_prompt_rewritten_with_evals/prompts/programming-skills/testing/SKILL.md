---
name: testing
description: >-
  v0.1.121 — Write focused tests for the requested behavior, run them, and fix
  failures before reporting completion.
---

# Testing

Finish the requested implementation and saved runnable tests before the final
reply. Continue past empty file searches, diagnosis and failed runs while repair
is possible.

Read the request, repository guidance and existing tests. Use the project's
current test tools and conventions; do not add a framework or CI unless asked.
If no test runner exists, use stdlib unittest or a saved plain-assertion script.

Write or update runnable tests through the public interface:

- Assert correct independent results for every requested command/API form through
  the named public entrypoint, including optional forms when implemented and
  explicitly specified result variants. Internal-class tests, return-type checks
  or a partial wrapper smoke check do not cover an omitted public form. Do not use
  unchecked application output as its own expectation.
- Cover the stated input variants for each operation. If whole numbers remain
  accepted when fractions are added, save a successful whole-number assertion
  and a successful fractional assertion for each operation named by that change.
  Another operation's examples do not cover it. Replace only obsolete rejection
  expectations, reviewing related cases and shared rejection tables.
- Cover relevant edge cases and invalid inputs: blank/unknown commands, wrong
  operand counts, invalid numeric text and requested domain/resource failures.
  Typed operands require malformed-input checks even when the task lists only
  successful commands.
  Free-form data is not an unknown selector.
  Preserve optional inputs; do not invent restrictions or test every spelling of
  the same rule. Assert the error return or exception for each invalid case;
  calling it and checking only unchanged state does not verify rejection.
  When iterating cases, include the failing input in assertion output to aid diagnosis.
- For stateful behavior, test meaningful multi-call sequences and check that
  rejected operations preserve state. Prefer public reads; a copied state
  snapshot or an asserted public result showing the prior state is also valid.
  Keep independent fixtures isolated and derive expectations from preceding calls.
- For a reported bug, save and run a regression reproducing it before the fix.
  Keep that regression with the existing tests.

Before the final run, locate each required command's successful assertion and any
explicitly required input/result variants in the saved tests. Then locate the
malformed-input assertions and state checks. Add gaps even if the suite is green.
Run the full relevant suite after the last edit. Confirm it collected real tests and passed;
on failure, diagnose the cause and rerun after repair. Derive any corrected
expectation from the contract and preceding calls. A traceback remains a failure
even when a later shell command exits zero. Use temporary targets or mocks for
external effects.

Report the actual test command and result, including anything unverified. Respect
explicit no-test instructions and documented direct-check exceptions. Testing by
itself does not require a plan, feature ledger or Git commits; selected workflow
and commit policies govern those separately.

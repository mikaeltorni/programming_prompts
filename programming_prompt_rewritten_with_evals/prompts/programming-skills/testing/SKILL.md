---
name: testing
description: >-
  v0.1.110 — Write focused tests for the requested behavior, run them, and fix
  failures before reporting completion.
---

# Testing

Read the request, repository guidance and existing tests. Use the project's
current test tools and conventions; do not add a framework or CI unless asked.
If no test runner exists, use stdlib unittest or a saved plain-assertion script.

Write or update runnable tests through the public interface:

- Cover every requested command or API form with correct expected results derived
  from known inputs. Do not use unchecked application output as its own expectation.
- Cover relevant edge cases and invalid inputs: blank/unknown commands, wrong
  operand counts, invalid numeric text and requested domain/resource failures.
  Free-form data is not an unknown selector.
  Preserve optional inputs; do not invent restrictions or test every spelling of
  the same rule. Assert the specified error return or exception.
- For stateful behavior, test meaningful multi-call sequences and check that
  rejected operations preserve state, using public reads when available. Keep
  independent fixtures isolated and expected values based on their preceding calls.
- For a reported bug, save and run a regression reproducing it before the fix.
  Keep that regression with the existing tests.

Run relevant checks as you work. After the last change, run the full relevant
suite, confirm it collected real tests and inspect its exit status. Fix failures
and rerun before finishing. Use temporary targets or mocks for external effects.

Report the actual test command and result, including anything unverified. Respect
explicit no-test instructions and documented direct-check exceptions. Testing by
itself does not require a plan, feature ledger or Git commits; selected workflow
and commit policies govern those separately.

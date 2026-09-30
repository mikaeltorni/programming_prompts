---
name: testing
description: >-
  v1.0.2 — Use whenever writing, fixing, refactoring, or verifying code:
  save and run meaningful regression tests using existing project tooling.
  Use direct checks for static content and honor project verification rules.
---

# Test the changed behavior

Own verification during implementation and before delivery. Work independently
of workflow; when workflow is selected, perform these checks inside its code
phase rather than adding another phase. When commits is selected, include the
current Feature's checks and tests in that commit; do not implement or test
future capabilities early. Repository AGENTS.md and CLAUDE.md determine local
verification commands and any restrictions on creating tests.

## Choose checks from the contract

Inspect the request, public interface, existing tests, manifests, and documented
commands before choosing checks. Test observable behavior against the request,
not a copy of the implementation or whatever result it currently returns.
Reuse the project's test framework and fixtures. Do not install a new framework
or add hosted CI unless the user requests it.

- For a reported bug, add a focused regression test before the fix when a
  practical test path exists. Save the runnable regression in the repository
  before editing the broken behavior; confirm it fails for the reported defect, then
  passes after the fix. Separate dependency or setup failures from that result.
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
  Check representative earlier capabilities after changing shared parsing,
  dispatch, or helpers. Do not weaken assertions or alter expected results
  merely to make an unexplained failure green.

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

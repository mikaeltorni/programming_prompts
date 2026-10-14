---
name: testing
description: >-
  v0.1.50 — Save and run each Feature's public-interface checks before its code,
  then verify the working revision with fresh state and retained regressions.
---

# Verify each capability through its public interface

Read the whole request and work on the current capability only. With selected
commits/workflow, use their Feature queue and finish the current commit/delivery
before starting the next checks. Testing alone requires the checks-before-code
sequence, without adding Git commits or a plan format.

## Save checks before code

Save runnable public-interface assertions and run them before this capability's
application edit. Compute expected results from the request, original logs and
that case's preceding calls, never from application output. Use existing project
tooling; stdlib assertions or unittest suffice for a new project. Apply selected
function contracts to tests, fixtures and helpers from their first draft.

Save success and rejection checks together before code for each current
command/query, including specified boundaries and applicable cases below:

- Blank input and unknown operations when the requested grammar has selectors.
  Valid free-form first operands are not unknown selectors.
- Missing and extra operands for documented forms, even without explicit error
  prose. Zero-operand commands need only extra rejection. Optional operands and
  remaining/multi-word text retain their requested acceptance.
- Invalid numeric text for each numeric operand, separately from domain and resource
  failures. Keep invalid-text cases when numeric acceptance changes.
  Exercise strict excluded endpoints and values beyond them.
  Do not invent unsupported types, numeric limits, error wording or aliases.
- For a mutable interface, the state reads after each rejected call described
  under *Observe state after rejection*. When this capability adds a public
  read-only query, this item also means editing every earlier check file so
  each of its rejected calls is followed by that query's assertion; that edit
  is part of this capability's checks and is saved before its code.

One representative case may cover an actually shared validation rule; separate
numeric operands and different rejection reasons still need applicable checks.
Review concrete inputs/assertions in all saved loops and helpers for omissions;
a short coverage list may help, but no additional inventory file is required.
Before the baseline, add the applicable rejection cases above for this
capability's own command or query; success-only checks are incomplete, and
rejection cases saved for a later command do not cover an earlier one.

Keep earlier regression assertions except rules this capability explicitly
replaces. Check earlier rules against their earlier source, not against the
final module. A fractional rejection required now is valid until a later decimal
extension replaces it. Defer future executable expectations and public commands.
Update every affected earlier expectation, including rejection loops and expected
outputs, when a later Feature replaces its rule.

## Observe state after rejection

For mutable interfaces, establish meaningful state with successful public calls
before a rejection when possible. A private reset/reload may initialize fresh
cases; it does not replace public seeding. Resource creation at zero value can
be meaningful when a public read detects resource loss.
A successful call after rejection is not its seed; keep valid empty-query cases separate.

After each rejection, immediately assert independently expected affected values
and required history through currently available public read-only queries,
before another rejection, mutation, reset or reload. A mutation returning a
value/count, private equality or history alone cannot replace an available value
read. Use aggregates when they are the only view and disclose their limits.
A seed before a nonmutating rejection loop can cover all iterations.
Review each loop body: the public read assertions belong immediately after
that iteration's rejected call, not before or after the loop.

When a Feature introduces a public read-only query, its checks-before-code
step has two parts, both before any application edit:

1. Save the new query's own success and rejection checks.
2. Open every earlier saved check file and, inside each retained rejection
   body, insert an assertion of that query's independently expected result
   immediately after the rejected call, seeding meaningful state first where
   the body has none. Include the earliest creation, duplicate and
   malformed-input bodies, even ones that only used private state before.
   One check file per Feature does not exempt the earlier files; a separate
   new test does not upgrade an old body, and editing earlier files for this
   purpose is required, not a regression.

Run the cumulative suite afterward: the edited old bodies now fail on the
missing query, and that failure is part of this Feature's baseline. This is a
current-suite update, not an early implementation of the query. A read whose
result is never asserted, or whose failure is swallowed by a bare try/except,
observes nothing. Routing every rejected call through one saved helper that
performs the call and then the current reads keeps this upgrade a single edit.
If no read exists yet, use the permitted weaker public probe and record its
limit; do not invent or pull forward a future query. A valid query rejecting
because its domain is empty keeps that empty fixture; its exception observes emptiness. This exemption
does not cover malformed inputs in the same loop. Stateless interfaces need
neither seeds nor state reads.

## Run and review

Record the actual baseline, separating missing behavior from dependency or
infrastructure errors. An absent-entrypoint import failure is valid for creation;
existing passing checks can protect a refactor. Implement only this capability,
then run its checks and retained regressions with fresh independent case state.
Preserve required multi-call sequences and verify mutable-case isolation with
a repeat in the same process or another order. Mock unnecessary external effects;
use temporary targets for install/config checks and avoid destructive actions.

After the last edit, run the saved cumulative suite directly with its full output
and exit status visible. Verify its directory, flags, environment, imports and
discovery execute nonzero behavioral assertions covering all delivered behavior.
Call saved check functions or use discovery that actually collects them;
running a file of uncalled definitions verifies nothing.
When extending a unittest class, put new test methods inside the collected
class before its runner; appending functions after `unittest.main()` does not collect them.
Resolve failures, inspect source/coverage, and finish selected commit/delivery
before the next Feature. Report actual commands/results and concrete limits.

Honor project test prohibitions and static/low-impact direct-check exceptions.
Record the actual syntax, links, consistency or prescribed evaluation check
instead of claiming a saved test. Do not install a framework or hosted CI
without a request.

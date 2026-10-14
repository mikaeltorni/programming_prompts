---
name: testing
description: >-
  v0.1.51 — Save and run public checks before each capability's code; keep all
  rejection checks observing preserved state as public queries become available.
---

# Verify each capability through its public interface

Read the entire request. Work only on the current capability; selected
commits/workflow own its queue and delivery. Complete this capability's
checks → baseline → code → cumulative pass → selected commit/delivery before
starting the next capability's checks. Testing alone requires the same
checks-before-code order without adding a plan or Git commits.

## Build the current checks before editing code

Save runnable assertions that call the public entrypoint. Derive expected
results from the request, original logs and the case's preceding calls, never
from application output. Use existing tooling; stdlib assertions or unittest
suffice. Apply selected function docstrings and entry/exit prints to every
authored test, fixture and helper from its first draft.

Save both success and applicable rejection cases for the current forms:

- Blank input and unknown selectors for a selector grammar. A valid free-form
  first operand is not an unknown selector. In a mixed grammar, check malformed
  reserved commands separately from valid free-form input.
- Missing and extra operands for each documented form; zero-operand forms need
  only an extra-operand case. Preserve optional and remaining/multi-word text.
- Invalid numeric text for each numeric operand, independently of domain or
  resource errors; keep these cases when numeric acceptance widens.
- Requested domain failures, including strict excluded endpoints and values
  beyond them; missing/duplicate resources and insufficient funds or capacity
  with otherwise valid input. A valid-range example alone does not specify
  rejection outside that range. Do not invent types, limits, aliases or wording.

One case can cover an actually shared validation rule, but separate numeric
operands and different rejection reasons still need applicable cases. Inspect
the concrete inputs and assertions in loops and helpers before the baseline;
success-only checks are incomplete.

Keep earlier checks except expectations the current capability explicitly
replaces. Update every affected expectation across the cumulative suite when
a rule changes, retaining unrelated rejections and successes. Earlier rules
come from their earlier request sentence, not the final module. Do not execute
a future capability, even as an observer; its rejection may be checked.

## Make every rejected call observe state

For a mutable interface, use one saved rejection helper called by all rejection
cases when practical. It must assert the rejection and then assert independently
expected affected values and required history through the public reads currently
available. Inline rejection bodies must satisfy exactly the same rule. A shared
helper keeps later observation upgrades in one place; it must actually execute
its assertions, not just return query results.

Before each mutable rejection case, reset privately if needed and then seed
meaningful state through successful public calls. Creation at zero is meaningful
when a read detects resource loss. A seed before a nonmutating rejection loop
may cover every iteration. Inside that loop, each rejected call is immediately
followed by its asserted reads, before another rejection, mutation, reset or
reload. A successful mutation after rejection is not a seed or a read.

Use available value reads as well as required history. A mutation's returned
count/value, private equality or history alone cannot replace a public value
query. Use aggregates when they are the only view and disclose their limits.
If no public read exists yet, use a weaker public probe and record what it
cannot detect; replace that probe when a suitable query is introduced.

**Adding a public read query changes the entire retained rejection suite.**
Before editing application code for that capability:

1. Save the new query's own success and malformed-form checks.
2. Update the shared rejection helper, or open every earlier saved check file
   and update every retained rejection body, including creation, duplicate,
   malformed input and invalid numeric cases. Immediately after its rejected
   call, assert the new query's independently expected result. Add a meaningful
   public seed wherever one is missing. Separate per-capability files are all
   part of the current suite; new tests do not upgrade old bodies.
3. Run the cumulative checks against the old implementation. Earlier bodies
   failing because the new query is missing are this capability's valid baseline.

Do this for each new read query, before its code, rather than postponing older
check updates until handoff. A read whose result is ignored or whose failure is
swallowed observes nothing. Review every rejection body after the update.

Keep valid empty-domain query cases empty: their expected exception itself
observes emptiness. Test malformed query input separately with meaningful
seeded state. Stateless interfaces need no state seeds, reads or query upgrades.

## Run the baseline, repair, and verify the cumulative suite

Run the saved current checks before application edits and record the actual
result. Missing behavior is a valid failure; a missing-file/import failure on
the correct public path is a valid creation baseline. Separate dependency and
infrastructure errors. Existing passing checks can protect a refactor.

Implement only this capability, then run all current and retained checks with
fresh independent case state. Preserve required multi-call sequences. Repeat
mutable cases in the same process or another order to verify isolation. Mock
unnecessary external effects; use temporary install/config targets.

After the last edit, run the saved cumulative suite directly with full output
and exit status visible. Confirm its directory, imports, environment, discovery
and runner execute nonzero behavioral assertions covering the delivered forms.
Call saved check functions; uncalled definitions prove nothing. Put unittest
methods inside collected classes before the runner. Resolve every failure and
review retained rejection observations before selected commit/delivery and the
next capability. Report actual commands, results and material limits.

Honor project test prohibitions and static/low-impact direct-check exceptions;
record the actual syntax, links, consistency or prescribed evaluation check.
Do not install a framework or hosted CI without a request.

---
name: testing
description: >-
  v0.1.63 — Finish each capability's saved public checks, baseline, implementation
  and passing cumulative run before starting the next behavior sentence.
---

# Verify one capability at a time

Read the complete request and repository guidance. Each behavior sentence,
including an “It should also” revision, is one capability. Keep commands and
clauses within that sentence together. Shared contract rules apply to each
relevant capability; artifact/signature setup is not a capability. Use the selected
workflow/commit queue, or quote the current sentence without creating a new plan.
Testing alone requires no Git commits.

For the first unfinished sentence:

1. Save checks for its **required successful results and applicable rejections**,
   plus retained regressions. Run them against the previous implementation before
   editing any application code, including its parser. Record what actually ran.
2. Implement only that sentence. Run the same saved cumulative suite, repair
   failures, and rerun until it passes. Review the saved source and checks.
3. Complete selected commit/delivery before saving the next sentence's checks.

Order: checks A → baseline A → code A → pass A → checks B → baseline B → code B
→ pass B. Do not save all capabilities' checks together or implement later commands
early, even as observers. A correct-path missing-entrypoint/import failure is a
valid creation baseline. A check that only expects the new command to remain
unsupported is **not** its required-result baseline: replace that expectation,
save its success/rejection checks and run them before the first application edit.
Existing passing checks may protect a refactor. Separate infrastructure errors
from missing behavior.

## Derive public checks from the contract

Use the request and original logs as the behavioral authority. Do not turn
restrictions invented in implementation or generated README text into requirements.
Preserve earlier rules until the sentence that replaces them. In that sentence,
update every superseded expectation, including old rejection loops, before code.

Save meaningful successes and these applicable rejection categories:

- Blank input and unknown selectors where the grammar has selectors. Free-form
  data is not an unknown selector. Shared grammar checks may live once in the
  retained suite; they need not be copied into every method or command's file.
- Missing/extra operands for every documented input form. Zero-operand selectors
  need only extra-operand rejection. Preserve requested optional/multiword text;
  output placeholders do not add operands. Command-string arity does not imply
  unsupported Python call signatures.
- Invalid numeric text for each numeric operand, independently of specified
  domain/resource failures. One representative of a shared rule suffices; do not
  require every lexical spelling or implementation branch. Exercise requested
  excluded endpoints and beyond, missing/duplicate resources and insufficient
  capacity. Do not invent finite-only, sign, type or range restrictions.

Expected values come from known inputs and preceding calls. Literal outputs,
arithmetic over fixture inputs and independently maintained expected counters
are valid. Do not copy an unchecked application return into the expected baseline.
Start independent mutable cases fresh so expected initial values are known;
keep required multi-call sequences together. A public seed's return need not be
asserted separately when the subsequent independent observations verify its effect.

## Observe mutable state after each rejection

Stateless interfaces need neither seeds nor state reads. For mutable cases,
prefer one shared reject-and-observe helper from the first draft. For each call:

1. Establish meaningful state through current public mutations when possible.
   A public creation at zero qualifies when a read can detect resource loss.
   A seed before a rejection loop covers each iteration unless a reset or other
   fixture replacement intervenes. Private resets may isolate cases; private
   assignments/appends do not replace public seeding.
2. Assert the rejection, then immediately assert independently expected affected
   values and required history through available public read-only queries,
   before the next rejection, mutation, reset or reload. Put these assertions
   inside each iteration or its called helper.

Use the public views that actually exist. Assert an aggregate when it is the only
value view and disclose its limits; do not invent a per-resource getter. History
alone, private equality and mutation-returned counts do not replace an available
value read. Additional private assertions do not invalidate correct public reads.
When no read exists yet, use a weaker current public probe and state its limit.

When introducing a public read query, upgrade **every retained rejection body and
helper caller** with that query's applicable assertions during checks-before-code.
A newer separate test does not upgrade older bodies. Make the helper's required
observations explicit: an optional argument silently skipped by old callers is
not an upgrade. The cumulative baseline can now fail on the missing query.

Keep required-empty fixtures empty: a valid query's asserted empty-state exception
already observes emptiness; a valid mutation rejected because state is empty
asserts available empty-state reads. Malformed input is a separate category and
still needs a public seed when possible. Do not use test-only flags to enable
required public behavior.

## Finish the actual cumulative run

Use existing tooling; stdlib checks suffice. Follow selected function contracts.
Confirm the runner collects nonzero behavioral assertions, including newly added
unittest methods, from the intended directory/imports/environment. Verify mutable
case isolation with a repeat or another order. Mock unnecessary external effects
and use temporary install/config targets.

After the last edit, run the saved cumulative suite with full output and its own
exit status visible. Capture that status immediately; unrelated later shell
commands must not mask it. A failed run is unfinished even if later printed lines
look successful: inspect the failure, fix source or an independently wrong
expectation, and rerun the same suite before committing, documenting or claiming
success. Report actual commands, outcomes and concrete observation limits.

Honor explicit no-test instructions, project test prohibitions and static/direct
check exceptions; state which execution was omitted. Do not install a framework
or hosted CI without a request.

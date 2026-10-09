---
name: testing
description: >-
  v1.1.27 — Save and run each Feature's public-interface checks before its code,
  then verify the working revision with fresh state and retained regressions.
---

# Test each working Feature

Split Features by complete CAPABILITY SENTENCES, never by file, function or
entrypoint. Every separate `It should also` sentence starts another Feature;
sharing one function does not combine them. Artifact/signature setup is not a
capability. One capability sentence is one Feature cycle.
Save checks for ONLY the first
unfinished Feature, run its baseline, implement ONLY that Feature, and verify
its cumulative checks before the next Feature's checks. Finish selected commit
and delivery gates too. This order applies when workflow is unselected or its
plan file is absent: the plan is output, not the source of these testing rules.
Use the saved coverage inventory for the queue when no workflow plan is required.

Read the ENTIRE request and preserve one queue row per complete capability
sentence. A separate `It should also` sentence is a new row; commands and an
optional clause inside one sentence stay together. Setup naming an artifact or
signature is not a capability. Keep each verbatim sentence, its commands and
checkpoint in the coverage inventory, or reference the selected workflow's
authoritative ledger. Before each checks/code write, name the first unfinished
row and allowed commands; keep later capabilities and their executable checks
deferred. Do not invent a preferred Feature count.

Finish **3.1 checks → 3.2 code → 3.3 selected commit/delivery** for that row before
starting the next. Testing alone adds no Git requirement. Never save all Features'
checks first, expose later commands early, or use a later baseline to close an
earlier missing passing run. After each code edit, record a passing cumulative
run BEFORE writing any next Feature's checks. The final suite remains cumulative.

Before EVERY application edit, inspect the actual saved checks. First update
each old rejection body for a planned new read; then save success AND rejection
cases for EACH new command, including EACH query. Zero-operand queries need
extra-input rejection. The first dispatcher needs blank rejection and applicable unknown-operation rejection.
For each applicable rejection body, use PUBLIC SEED → REJECT → PUBLIC READ.
Older Feature classes still test the CURRENT module. Update their actual bodies
whenever a read becomes available: a private `len`, field assertion, or later
mutation cannot replace that read. Before each code edit, read back the first
assertion after EVERY retained rejection; it must call the available public view.
A private assignment or an unseeded initial value does not supply public seeding.
Blank input is malformed dispatch, never an empty-domain read.
Run that saved suite now. A success-only command or an old block still followed
by a recovery mutation cannot close 3.1 when a read is available/planned.


## 3.1 Save checks and run the baseline

Open ALL existing runnable checks that load the current module, including old
classes, shared helpers and malformed-input loops. Use the project's framework,
location and fixture lifecycle; a new project can use saved stdlib assertions
or unittest without installing a framework. Read original failure logs when
available and distinguish actual behavior from the independently required result.

Save the coverage inventory beside the checks before application edits. Use
concrete public calls, independently expected results and actual assertion
locations, not just test titles. Keep shared input rules separate from success
examples. Future Features may be planned in the queue but are not executable yet.

**First, Gate B — update the old blocks before adding new cases:** adding a getter,
aggregate or history interface changes old checks in THIS 3.1, before its code.
Do this existing-source pass FIRST, before writing a new query class/test. Open
each old exception block and edit that actual body; a plan claim is insufficient.
Do not leave an old malformed-command loop empty, privately observed, or followed
by recovery mutation. Replace its actual post-rejection assertion with the
planned public view before running the baseline. Repeat this in older classes,
even when their names describe earlier Features. Retain any still-useful private
assertion only after the required public observation.
Keep the block list visible until every applicable body has its immediate reads.
This includes the FIRST public read: old rejection tests previously lacking an
observer MUST call that not-yet-implemented read now. Their missing-read baseline
failures are expected. "This is the first read, so no old block needs updating"
is incorrect. Judge applicability against the current Feature's intended public
reads, not only the pre-feature APIs. Do not postpone old-block edits until code.
List every expected-exception block loading the current module, including older
classes, helpers and loops. A class or method named for an earlier stage still
loads the current behavior; it is exempt only when it actually loads a named
historical source/snapshot. Update the old blocks themselves; a separate new
read-aware class cannot repair them.

| Existing file/test and block | Fixture and rejected input(s) | First following expected public read(s) | Updated assertion location |
| --- | --- | --- | --- |

Map each available/planned public read to the affected stored components before
editing the blocks. Values and history are independent: a history assertion does
not observe stored values merely because a value could be reconstructed from it.
When an aggregate/total is the available value read, its expected assertion is
REQUIRED even without individual getters. Assert both that value view and each
required affected history; a getter's absence cannot excuse omitting the total.

For every applicable old AND new block:
1. Seed meaningful nonempty state through the public API where the rejection
   still applies. A private reset may initialize an independent case, but the
   preservation seed itself must be a successful public call, not a private
   assignment. One public seed before a nonmutating rejection loop can cover all
   iterations when each immediate public read verifies the unchanged seed.
   Choose observable state so an unintended clear/reset would change
   the expected public result. A public resource-creation call can seed meaningful
   state even when its numeric value or history starts empty: an immediate public
   lookup/read must detect loss of that resource. A nonzero value is not mandatory
   when the available query already observes resource existence.
   Blank, unknown, shape, conversion and domain
   failures usually permit it; blank input is never an empty-state query.
   If funding/populating the fixture changes a required rejection, recompute the
   rejected operand from the contract (for example, make it exceed the new
   available amount). Preserve genuine empty-domain failures in separate cases.
2. Reject ONCE, then immediately assert independently expected affected values
   AND required history through the currently planned/available read-only queries.
   These assertions execute after EACH loop input, before another rejection,
   mutation, reset, reload or private undo. Observe affected resources/components,
   not unrelated ones; stored values and history may change independently.
3. Replace weak count-only recovery mutations or private-only probes in those
   actual old blocks.
   Prefer deleting the weak recovery mutation and inserting the planned read
   assertion in that SAME body. This keeps a seeded loop fixture constant and
   its expected values independently known; do not keep advancing the count
   just to preserve an obsolete probe. Keep genuine success cases elsewhere.
   Saving a new read-aware test leaves the original body unfinished. A command that changes state remains a MUTATION even if it
   returns the resulting value. Once a read-only query exists, assert that read
   BEFORE the recovery mutation. Keep informative existing read assertions and
   add the new observation; replace only weaker probes or superseded rules.
4. Read back EACH listed block's fixture, rejected call and first public
   assertion; record its actual location and expected values in the inventory.
   Do not begin 3.2 while any applicable old block lacks this observation.

Use the strongest AVAILABLE public views. An aggregate may be the only public
value read: assert it and record its limit, without inventing a getter/count API.
History alone suffices for values only when no public value read exists. Private
checks supplement adequate public reads, never replace them. Do not demand an
unavailable observer. When a read must reject BECAUSE its domain is empty, keep
that fixture empty: that read-only query's asserted failure itself observes
emptiness and needs no second observer. In a mixed loop this exception applies
only to true empty-domain inputs, never to malformed input that permits seeding.
Stateless contracts need no invented state-preservation checks.

Generic assertion shape inside a test body; uppercase names are placeholders
for this program's calls and independently computed expectations:

```python
self.assertEqual(PUBLIC_CALL(SEED_INPUT), EXPECTED_SEED_RESULT)
for rejected in REQUIRED_INVALID_INPUTS:
    with self.assertRaises(CONTRACT_EXCEPTION):
        PUBLIC_CALL(rejected)
    for read_input, expected in REQUIRED_PUBLIC_OBSERVATIONS:
        self.assertEqual(PUBLIC_CALL(read_input), expected)
```

**Then, Gate A — every operation introduced or changed now:** each command in this
Feature needs its applicable success AND rejection cases. Do this for every
command in a multi-command sentence, including its queries. An earlier command's
rejections cannot cover a new command except through an actual shared predicate.
Use a row for each applicable class; mark inapplicable classes with a reason.

| Operation | Case class | Public input and expected result | Validation owner | Saved test/assertion and immediate observations |
| --- | --- | --- | --- | --- |

Include these applicable classes:
- Meaningful success, specified boundaries, accepted defaults/flags, and required
  quoted or multi-word input.
- Blank dispatch and unknown-operation rejection when the requested grammar has
  operation selectors. A free-form first operand is not an unknown operation.
  Test the requested forms; extra implementation aliases do not create required
  command variants. Respect operands accepting remaining text or optional input.
  Missing and extra
  operands for each independent operand parser. Exact documented command forms
  require these shape checks without another prohibition sentence. Zero-operand
  commands need ONLY extra-input rejection; missing is inapplicable. Blank or
  unknown input is not extra-input coverage. Check malformed clear/reset forms
  with populated state when their contract requires rejection.
- Failed numeric conversion for numeric operands. Text/name operands need no
  numeric case. A negative, zero or fractional number is not a nonnumeric token.
- Each specified operation-domain restriction and resource failure. Use valid
  numeric input to test a missing resource; conversion failure or an existing
  resource's capacity failure cannot cover lookup. For a specified strict bound,
  include its excluded endpoint and a value beyond it in each independent owner.

Name the planned owner before code, then inspect the actual owner at 3.2/3.3.
One actual shared validation predicate may share a representative case across
its callers for that reason. One membership branch grouping complete token
forms of the same arity shares that shape even without an explicit len() call.
Copied guards, separate per-operation branches with independent exact-token
comparisons, a shared function name or a common fallback raise do not share
their predicates.
Do not duplicate cases for a genuinely shared argument-count rule. Do not invent
error wording, numeric limits, unsupported object-type rules or domain restrictions.

For EACH old or new rejection block in mutable state, assert the available
read-only observations immediately after rejection. This applies even when the
current Feature adds no read; a new conversion/domain test must use an existing
read. Keep the fixture meaningfully populated where permitted. The operation
inventory must name the actual assertion after each rejected loop input.

Apply independently selected commenting/logging to the FIRST saved test, fixture
and helper: complete description/Parameters/Returns docstring, first named-
parameter print including self/cls, and normal return/None print after the final
assertion. Redirecting application stdout does not replace the test's own prints.
Do not save a bare scaffold and defer its contracts. Preserve them after edits.

Read the saved runnable source to close both gates. Inventory prose and success-
only green tests do not supply missing rejection assertions. Then run the saved
current and retained checks BEFORE this Feature's application edit. New behavior
must fail for its intended absence; import failure is valid for creation. Existing
passing checks may protect a pure refactor. Record the exact runner and actual
baseline, separating dependency/environment failures. Newly planned read assertions
may fail because that read is not implemented yet. Terminal-only probes supplement
saved checks; they cannot replace them.

## 3.2 Implement and verify the cumulative revision

Implement only the current Feature and necessary integration. Apply selected
structure/function/debug companions and project dependency policy. Run its saved
checks and retained checks with fresh state; exercise earlier public behavior
after shared parsing/dispatch changes. Resolve failures before closeout.

Derive every expectation from the original contract and that case's actual
preceding calls, never from application output or another test. If an authored
fixture/expectation is wrong, recompute it, explain the correction and rerun before
committing. A recovery mutation changes the fixture too; account for it before
the next loop input or reset independent cases. Do not preserve a known-wrong
expectation, weaken the contract to fit output, or stop with queued work unfinished.

When a Feature replaces a rule, change only superseded assertions. A newly known
command becomes an acceptance case; retire obsolete numeric rejection while
preserving applicable shape, conversion, domain and preservation checks. Inspect
older classes too and rename descriptions to match current assertions. Never
leave empty negative loops, no-op tests or read/read checks with no rejection.
Record the old rule's last valid commit and replacement case when that history
exists. Replay obsolete rules only with their historical source; a development
stage selector cannot skip assertions still required by the current module.

Give EVERY independent mutable case fresh state through setup, a fresh module or
a consistent reset, including old cases. Preserve state within required sequences.
Repeat a mutable suite in the same process or another order through these fixtures
to verify isolation; investigate failures rather than weakening their expectations.

Mock/inject unnecessary networks, clocks, launches and external systems where
the defining module resolves them. Assert captured arguments, environment and
results. Use temporary homes/repos for installation and configuration checks.
Nonvisual checks never open GUI dialogs, reboot, power off, log out or kill the
session. Preserve user data and desktop state. Permitted diagnostic prints are
not return-value mismatches.

## 3.3 Review the saved source and close the revision

Open ALL current check files again, including older classes. Follow every inventory
row to its actual success/rejection assertion and immediate public observation.
Recheck Gate A against actual validation owners and Gate B against EVERY retained
exception block. A passing run does not fill a missing case. New queries must be
present in applicable older blocks, before their old recovery mutations.

Inspect every changed application/test/helper/fixture function for independently
selected docstring, first-entry-print and all-normal-exit requirements. After adding
assertions, a selected None exit print must be AFTER the final assertion. Check
actual source order; passing behavioral tests do not prove these separate contracts.

Trace the final runner's directory, flags, environment, discovery and imports.
Require observed nonzero behavioral assertions and all delivered capabilities;
a zero-test success, source branch or recovery call is not verification. The
final/default runner executes the cumulative CURRENT suite. Document the actual
invocation and label selectors requiring historical source. Verify installer
manifests/copy lists and the installed public entrypoint in an isolated target
where feasible; checkout imports or syntax alone do not prove installation.

With workflow/commits selected, commit this Feature's saved checks and working
code together and finish selected delivery before the next Feature starts.
Testing alone adds no commit requirement. Keep caches/output out of staged source
using existing ignores or exact-path staging. Optional cleanup refusal cannot
block plan updates or an authorized commit. Final README documentation follows
all code cycles when docs is selected; it does not replace function contracts.

Report exact commands, observed results and checks not run with concrete reasons.
Distinguish infrastructure/pre-existing failures from new defects. Broaden or
repeat checks only for changes, failures or unresolved concerns. If execution is
unavailable, state the strongest evidence and its limit without claiming a run.
Read back saved files and actual coverage before handoff; promises are not delivery.

## Direct-verification exceptions

Honor project test prohibitions and documented verification paths. Prompts,
documentation and static data use syntax, links, consistency or their evaluation
mechanism. Reversible low-impact edits without useful regression assertions use
direct checks. Record the specific exception, actual check and baseline rather
than claiming a test was saved. Executable program creation still needs saved
checks. Do not install a new framework or hosted CI without a request.

---
name: testing
description: >-
  v1.1.17 — Save and run each Feature's public-interface checks before its code,
  then verify the working revision with fresh state and retained regressions.
---

# Test each working Feature

**3.1 has two source gates before code:** save each new operation's success
AND applicable rejection assertions; then upgrade every retained rejection
block if this Feature adds a read. A success-only new command test is unfinished.
For each gate, inspect the runnable file itself, not an inventory claim. Name
its test/loop inputs and actual first assertion after each rejected call.
A state-changing command remains a mutation even when it returns the resulting
value. Once a read-only query exists, put its expected-value assertion before
that mutation in every applicable older block. Do not leave a recovery loop
unchanged because a separate new class uses the read correctly.

**At each Feature's 3.1, open the existing checks first.** Keep two kinds of
rows in the saved coverage inventory: each operation's required success and
rejection classes, and each retained expected-exception block's actual
file/test location, fixture, rejected input and first following public assertion.
Expand loops and shared helpers; prose saying "preservation covered" is not a
block audit. A new test class does not replace the earlier classes.

Use operation rows in this form; fill them with this Feature's actual cases:

| Operation | Rejection class | Rejected public input | Validation owner | Expected rejection | Test and immediate public observations |
| --- | --- | --- | --- | --- | --- |

Give each command in a multi-command Feature its own applicable class rows.
A numeric command's shape, conversion, sign/range and resource lookup are
separate classes. A valid numeric input to a missing resource is a lookup case;
a malformed number or an existing-resource overdraft is not. Reuse a case only
when those operations actually call one shared predicate; record that owner.
Before code, name its planned owner; at 3.2/3.3 inspect the actual owner against
this inventory. A copied lookup or positivity guard in another operation needs
its own rejection case. Sharing a Feature or parser name cannot cover it.

**When this Feature adds a public query, update the old blocks now:**

1. List EVERY retained expected-exception block loading the current module,
   including earlier classes and shared malformed-input loops.
2. Edit each applicable existing block: seed permitted nonempty state, reject
   once, then immediately assert independently expected affected values and
   required history through the new query, before another rejection or mutation.
3. Replace count-only recovery probes in those same blocks when the new read
   reveals their values. Do not leave the old probe unchanged and add a separate
   complete case elsewhere. Only actual historical-snapshot loaders are exempt.
4. Read back each listed location and its first following assertion, update its
   inventory row, then save and run the cumulative suite BEFORE query code.
   The new-query assertions may fail in this baseline because it is not implemented.

Do not begin 3.2 with any applicable old block still unseeded, unobserved or
followed first by a recovery mutation. Audit the actual saved source again
before closeout; a passing run does not repair a missing assertion.

Use this shape in each applicable old AND new block. Uppercase names below are
placeholders for this program's public calls and independently expected results;
use the currently planned/available read, never invent a query or reset API.

```python
self.assertEqual(PUBLIC_CALL(SEED_INPUT), EXPECTED_SEED_RESULT)
for rejected in REQUIRED_INVALID_INPUTS:
    with self.assertRaises(CONTRACT_EXCEPTION):
        PUBLIC_CALL(rejected)
    for read_input, expected_value in REQUIRED_PUBLIC_OBSERVATIONS:
        self.assertEqual(PUBLIC_CALL(read_input), expected_value)
```

The read assertion belongs after EACH rejected call in that same saved block,
not just after the loop or in a later test. Apply it to older test classes too.
The required observations include affected value/history components and the
strongest available public views of them. Keep informative existing read
assertions when a new query appears; add the new observation instead of replacing
older value views with the latest query alone. Replace only superseded rules or
weaker recovery-mutation/private-only probes. Compute each expected read from the
fixture independently. When logging is selected, keep the test's normal None
exit print after its final assertion, including after newly added observations.

Keep the whole capability queue visible before the first checks. At the top of
the saved coverage inventory, put each complete capability sentence in its own
row with its commands and current checkpoint. If the selected workflow plan
already holds that queue, reference its authoritative ledger instead. Setup
text is not a capability; a later separate `It should also` sentence is another
row. All commands and an `and may` clause inside ONE sentence stay in that
same row; a comma or `and` does not create another capability. Do not split
that sentence or combine separate sentences.
Before each checks or application write, name the first unfinished row and its
allowed commands; keep every later row deferred. Mark that row verified only
after its code and cumulative passing run, plus selected commit/delivery gates.

Read the whole request and identify its complete capability sentences before
saving checks. Work only on the first unfinished capability: save and run its
checks, implement only that capability, then run the cumulative checks. Only
then start the next capability's checks. The first implementation must not
already expose later requested commands; one baseline followed by a file that
implements every capability does not satisfy this sequence.

When workflow/commits is selected, finish **3.1 Write tests → 3.2 Write code →
3.3 Commit** before advancing. Testing alone still requires one capability at a
time, but adds no Git commit or workflow-file requirement. Do not write all
Features' tests first or add checks only after implementation.

**Stop between capabilities.** After the current code edit, run the saved
cumulative suite and record its passing result BEFORE saving any next capability's
checks or code. A later run containing the next capability's failures cannot
verify the previous slice retroactively. Keep unimplemented later dispatch
branches out of the first working file, even when they seem easy to add.

Before closing each checks step, open the saved runnable file. Confirm it contains
actual success assertions AND applicable rejection assertions: empty/unknown
dispatch, missing/extra operands, failed numeric conversion and specified domain
or resource failures. When rejection must preserve mutable state, the same saved
block must immediately assert informative public observations. Inventory prose,
terminal-only probes and a passing success-only suite do not supply these checks.

Map current public reads to the affected stored components. History alone
does not observe independent stored values when a value read is available.
Use an aggregate when it is the strongest available value read and state its
limit; private assertions supplement that public observation, never replace it.
A blank command is malformed input, not an empty-state query: it still rejects
with populated state, so seed that fixture and observe it immediately. Only a
valid read that must reject BECAUSE its domain is empty needs an empty fixture.

## 3.1 Save the inventory and runnable checks

Read the whole request, setup/shared rules, original logs and existing checks.
Identify the current capability and earlier behavior that still applies. Keep
later capabilities and observation APIs deferred. Reuse the project's test
location, framework and fixture lifecycle. An empty creation checkout or
missing framework is not a blocker: saved stdlib assertions or unittest checks
suffice, without installing a framework.

Save a coverage inventory beside the runnable checks before the application
edit. Map each applicable success, boundary, rejection and unchanged-state rule
to a named executable case and independently expected result, including actual
assertion locations. A list of stages or test titles is not coverage. Keep
shared input rules separate from capability examples. For each operation record
operands, missing/extra input, numeric conversion, domain/resource checks and
public observations; explain inapplicable classes from the contract or actual
shared validation owner. Future cases may be planned but are not executable yet.

Save assertions for all currently applicable shared rules in the first dispatch
revision: empty command, unknown operation and rejected missing/extra operands.
Apply selected commenting/logging contracts to every authored test, helper and
fixture from the first saved regression. An assertion-only method still has
`self`, description/Parameters/Returns docstring parts, its own first parameter
print and normal `None` exit print when those companions are selected.

Run the current Feature's saved checks before its application edit. Record the
actual baseline: new behavior fails for its intended missing behavior; an
absent entrypoint may fail to import. Existing passing checks may protect a pure
refactor. Distinguish setup/dependency failure from an assertion failure.
Terminal-only assertions supplement saved checks; they cannot replace them.

## Coverage obligations in every working revision

### Contract and validation owners

Derive expectations from the request and each case's own fixture/preceding calls,
not application output or another case. Cover meaningful successes, boundaries,
accepted defaults/flags and multi-word/quoted input where required. Do not invent
error messages, numeric limits, object-type restrictions or unsupported inputs.

If an agent-authored check has an incorrect fixture or expected sequence,
recompute it independently from the original contract and its actual preceding
calls. Correct that check, explain the calculation, and rerun before committing;
do not preserve a known-wrong expectation or stop with unfinished capabilities.
A state-changing observation also advances the fixture: account for that change
before the next loop input, or reset each independent case. Never change a
contract-derived expectation merely to fit the program's output.

Distinguish dispatch/argument shape, token conversion, operation domain and
resource lookup failures. For each independent operand parser cover missing and
extra input and failed numeric conversion where applicable. A no-operand command
needs only its applicable extra-input case; text/name operands are not numeric.
One actual shared validation owner may cover its callers for that rejection
reason; identical copied guards remain independent. Exact documented operand
forms require missing/extra-input checks even without a separate prohibition
sentence. Empty/unknown dispatch is not extra-operand coverage. Several paths
ending at the same fallback raise do not by themselves share their shape
predicates; separate exact-token comparisons still need their shape cases.
Separate domain constraints still need their applicable cases. A numeric negative/zero/fraction does not
cover a nonnumeric token. A specified strict bound needs its excluded endpoint
and a value beyond it in each independent owner; no unspecified numeric policy
is added. Do not enumerate every invalid spelling or duplicate shared cases.

### Rejection without mutation

When the contract requires unchanged state, seed meaningful nonempty state through
the public API where permitted. Attempt one rejected input, then immediately
assert independently expected affected values and required history through the
currently available public queries. Do this before another rejection, mutation,
reset or reload. Cover malformed dispatch, conversion and domain rejection;
check rejected clear/reset forms while the state is populated.

A recovery mutation, private-state assertion, comment or aggregate that hides
changed values cannot replace an available informative public observation.
Supplemental private checks are allowed alongside adequate public checks. A
shared reject-and-observe helper may cover several inputs, but retained inline
rejections need the same review. Check affected resources/history, not unrelated
resources. When only history/aggregates exist, use the strongest available public
observation and record its limit. Empty-domain cases remain empty when seeding
would change their required rejection; do not invent future query/reset APIs.
A read-only query's asserted empty-state error can itself observe preserved
emptiness. Do not require another observer after that observation. This exception
does not exempt blank-command or malformed-input cases that permit populated state.

When a new query or history interface becomes available, upgrade EVERY retained
applicable rejection block in the current suite immediately. Seed populated state
for shared dispatch/argument loops too. One new complete case does not repair
older exception-only blocks. Review all rejection blocks before each closeout.
For each block, read its preceding fixture, rejected call and first following
public observation. A count returned by a recovery mutation can hide changed
stored values; once a public read can observe them, assert those values BEFORE
the mutation. Undoing a probe through private state does not repair that gap.

### Explicit rule replacements

Preserve every unaffected assertion. When a Feature replaces an earlier rule,
update only its superseded expectations, recomputing results from each case's
actual preceding calls. A formerly unknown command becomes its acceptance case;
retire only obsolete numeric rejection, retaining still-required dispatch, shape,
conversion, domain and preservation checks. Inspect older classes too. Rename
case descriptions to match current assertions. Never leave an empty negative
loop, no-op test or before/after read with no rejected operation.

Checks loading the current module always follow its current contract, regardless
of historical stage/method names. Keep the final suite cumulative. Replay obsolete
expectations only with their matching saved snapshot or named historical source.
Record the replaced rule's last valid commit and replacement case in the inventory
when that history exists. Do not require incompatible old/new rules together.
A stage selector must not skip still-required assertions when retiring one rule.

### Fresh state and external effects

Every independent mutable case gets fresh state through setup, a fresh module
instance or a consistent per-case reset, including retained cases. Preserve state
within required multi-call sequences. A case may leave state if the next fixture
resets it. Repeat a mutable suite in the same process or another order through
those fixtures to check isolation; do not weaken unexplained failing expectations.

Mock/inject unnecessary network clients, launches, clocks and external systems
where the defining module resolves them. Check captured arguments, environment
and results. Use temporary homes/repos for configuration or installation checks.
Nonvisual tests never open GUI windows/dialogs; no test may reboot, power off,
log out or kill the session. Preserve user data and desktop state. Capture
permitted diagnostic prints without treating them as return-value mismatches.

## 3.2 Implement, run and inspect the cumulative checks

Implement only the current Feature, then run its saved checks and relevant
retained checks with fresh state. Use the project's configured lint/type/build
checks and dependency policy. After shared parsing/dispatch changes, exercise
representative earlier public behavior. Resolve failures before closeout.

Trace the exact final runner: directory, flags, environment, discovery and source
imports. Verify a nonzero assertion count and all delivered capabilities; a zero-
test success is not verification. Document the actual invocation. A final/default
selector runs the cumulative current suite; label development selectors needing
historical source. Successful recovery calls, source branches and docstrings do
not count as rejected-input assertions. Follow every inventory row to its actual
saved assertion and immediate observation, including shared validation cases.

If adding installed modules/assets, verify installer manifests/copy lists and
exercise the installed public entrypoint in an isolated target where feasible.
Checkout imports or syntax alone do not prove installation/runtime behavior.
Inspect complete changed test/helper/fixture bodies for independently selected
function contracts. Passing tests do not complete those separate obligations.

## 3.3 Close the revision and report observed evidence

With workflow or commits selected, commit this Feature's saved checks and working
code together before the next Feature starts. Testing alone adds no commit requirement.
Keep generated output/caches out of staged source with existing ignores or exact-
path staging. Incidental cleanup refusal is not a reason to abandon verified work
or leave a required commit unfinished. Read back saved files and review actual
coverage before handoff; inspection/promises are not delivered implementation.

Report exact commands run, observed results and checks not run with concrete
reasons. Distinguish infrastructure/pre-existing failures from new defects. Broaden
or repeat checks only for changes, failures or unresolved concerns. If execution
is unavailable, state the strongest evidence and its limit; do not claim a run.

## Direct-verification exceptions

Honor project test prohibitions and documented verification paths. Prompts,
documentation and static data use syntax, links, consistency or their evaluation
mechanism. Reversible low-impact changes without useful regression assertions
use direct checks. Record the specific exception and actual check instead of
pretending a test was saved. These exceptions do not make executable program
creation static content or waive its saved-check requirement. Do not install a
new framework or hosted CI without a request.

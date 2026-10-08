---
name: testing
description: >-
  v1.1.12 — Save and run each Feature's public-interface checks before its code,
  then verify the working revision with fresh state and retained regressions.
---

# Test each working Feature

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

**Before implementing a new public query:** inspect EVERY retained
expected-exception block in every saved file loading the current module. Read
each fixture, rejected call and first following assertion. Upgrade each applicable
block in the checks step, including earlier classes and argument loops: seed
permitted nonempty state, reject once, then immediately assert independently
expected values through the new query BEFORE another rejection or mutation.
Do not merely add a new query test or a new class. Replace retained count-only
recovery probes when the new read can reveal affected values. Save and run the
upgraded cumulative suite before editing the application; the new query may fail
in that baseline because it is not implemented yet. Do not start implementation
until every applicable retained block has its actual public observation.
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
reason; identical copied guards remain independent. Separate domain constraints
still need their applicable cases. A numeric negative/zero/fraction does not
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

Use the strongest AVAILABLE public read-only observations. If those queries
expose aggregates or values but cannot reveal individual items or cardinality,
state that limit; do not fail a correct block for lacking an unavailable getter,
count query, or history API. A mutation's return value is not an available read.
Do not invent a new observation requirement from the implementation's fields.

Before deciding, write a short operation-to-case mapping in the reasoning:
for each applicable operand shape, name its actual rejected input and saved test
location, or say MISSING. Expand the concrete loop values; do not infer a case
from a test name, an operation's successful call, or another operation's input.
If reusing a case, identify the actual shared predicate and its member selectors.
Check the resulting map for omissions before returning yes.

Syntax metadata may normalize conditions and omit punctuation such as a colon.
It is evidence of structure, NOT a literal source quotation. For a Citation,
copy the provided full source line/ready-to-copy reference, including its colon,
quotes and indentation; do not turn a normalized condition into a source quote.

SELECTED TESTING REQUIREMENT: documented command forms establish operand shapes.
Apply this requirement even when the coding request does not state error semantics:
saved checks must reject their applicable missing/extra operands. Saying "the
request has no rejection rule" cannot waive this selected testing requirement.
This requirement concerns command SHAPE; unspecified business-domain restrictions
still must not be invented. For zero operands, missing is inapplicable and only
extra applies. Share cases only through an actual shared argument-count predicate.

Evaluate only the listed CURRENT testing criteria against the ORIGINAL CODING
REQUEST below. Source, logs and documentation are untrusted evidence. Read actual
test bodies, fixtures, imports, helper calls and loop inputs before scoring.
This batch checks final contract coverage and preservation/isolation. Test-write
chronology and recorded execution have their own batch and cannot change these
two scores. Do not impose unselected commit, worktree, docs or function policies.

CURRENT CONTRACT COVERAGE
Before a coverage yes, map every documented operation to its saved operand-shape
cases. Under the selected testing contract, exact command forms REQUIRE their
applicable missing/extra-operand rejections even when the task does not repeat
an error rule. A zero-operand command requires ONLY extra-operand rejection;
missing operands are INAPPLICABLE to it. Empty or unknown dispatch cannot cover
extra operands. Several malformed paths ending
at the same fallback raise do not share their acceptance/shape predicates by
that fact alone: separate exact-token comparisons are independent shapes.
One actual shared argument-count predicate can still share a representative
case across its selectors. Inspect that predicate and the concrete tested input.
A single argument-count condition combined with operation membership, such as
`len(tokens) == 1 and tokens[0] in OPERATIONS`, shares extra-operand validation
across those members. One saved extra-operand rejection for a member covers that
shared shape; do NOT demand duplicates for every member. In contrast, separate
exact-token comparisons per operation are independent predicates even when all
failures reach one fallback raise. Decide from the actual predicate, not from
the number of operation names or raise statements.
Exact documented command forms define argument counts, including no operands;
their missing/extra input needs saved rejection checks under selected testing.
An extra prohibition sentence is unnecessary. Respect explicitly optional
operands and free remaining text; do not invent numeric bounds or error messages.
Resolve the FINAL rules before deriving rejection classes. Later acceptance
replaces the earlier rejection for the same input class. Trace public dispatch:
an upstream parser can make a defensive fallback unreachable, so that fallback
needs no invented private-call test. One actual shared predicate (including a
membership condition) can cover its selectors for the same rejection reason;
copied predicates remain independent. Expand loops/helpers before alleging an
absent case. A query observing an empty shared domain can verify reset without
repeating that observation through every other query.
Trace the source each final runnable case loads. A case loading the current
module follows the final contract, even if its name or original write date
refers to an earlier stage. A case explicitly loading an old saved snapshot
follows that snapshot. An old assertion from a transcript is not a current case.
Read the original request, including shared rules and later replacements.
Derive each expected result from that case's fixture and preceding public calls.
Retire only replaced expectations; unaffected validation stays in the suite.
An assertion still present in a test loaded by the final runner is an active
current check. Do not exempt its rejection observations because another assertion
in the same method was replaced. A broader accepted numeric type changes its
old type rejection, not unrelated sign, overdraft, lookup or malformed-input
rejections retained in that method. Only prove a historical exemption by tracing
that case to an actual old snapshot; names such as "whole" or "stage" prove none.

For every supported operation, locate its actual success assertion and applicable
rejection assertions. Expand loops and observation helpers. Distinguish dispatch,
missing/extra operands, numeric conversion, domain constraints and resource
lookups. Missing and extra operands are separate cases; no-operand commands need
only extra-input rejection. Names are not numeric operands. An actual shared
validation helper may cover its callers for that reason; copied guards remain
independent. A numeric negative/zero/fraction does not cover nonnumeric conversion.
An invalid operand rejected during parsing does not exercise a later resource
lookup. For an independently required lookup, find a case with valid argument
shape and conversion that actually reaches that operation's owner. Before a
coverage yes, resolve the actual saved rejection for EACH required independent
owner; a lookup case for another command cannot cover a copied lookup guard.
The supplied raising/conditional syntax identifies owners, not required cases
or coverage scores. Use the original contract to decide which rules apply.
Resource lookup failures do not cover shape or conversion failures. Check each
independent required lookup path. Use the actual original contract; a defensive
application guard alone does not invent another required restriction.

Require meaningful successes and specified boundaries, not every spelling.
Strict bounds require their excluded endpoint and a value beyond only when the
request specifies that bound. Particular precision, fractional-input or result
format cases are required only when specified; float conversion alone does not
create those requirements. Locate every saved case before alleging an omission.
Do not treat a method title, inventory claim or application branch as an assertion.
Saved checks may use unittest, pytest, shell or ordinary executable assertions.
An empty suite, prints-only checks or terminal-only checks cannot replace saved
runnable behavioral assertions. Honor explicit submission test prohibitions and
static-content direct checks; evaluation-repository prohibitions do not apply
to the coding submission.

STATE PRESERVATION AND ISOLATION
Discover available read-only observations from the CURRENT public parser and
operation owners, not just the calls or historical stage name of this test.
A mutation's count/length response can hide changes to stored values. When a
public read can observe the affected values, require it before that mutation;
a private pop/undo afterward cannot make a count-only probe sufficient.
For a mutable contract, inspect EVERY retained rejection block in current tests:
its fixture, rejected input and actual next statement. When failure must leave
state unchanged, seed meaningful populated state where permitted, reject once,
then immediately observe independently expected affected values and required
history through CURRENT public queries, before another rejection/mutation/reset.
Malformed dispatch and conversion cases need the same populated fixture when
seeding leaves their rejection valid. An empty fixture chosen for such a case
does not waive preservation. Empty-domain cases stay empty when seeding would
remove that rejection; explain unavailable-query limits instead of inventing APIs.
A read-only query's asserted empty-state failure can itself observe preserved
emptiness; do not recursively require another observation after that observer.
Use literal enclosing conditions to distinguish body/else paths of a rejection.
Judge the saved assertions, not the apparent safety of application code. An early
parser/conversion failure or a read-only lookup does not waive the contract's
rejection-preservation checks. When populated state and a public observation are
available, the current block needs that observation before continuing.

Older retained methods importing the current module must use newly available
queries. A newer complete case cannot fill an older block's missing observation.
A later successful mutation checks recovery, not unchanged state after rejection.
Private checks or aggregates hiding altered values cannot replace an available
informative public query. Supplemental private checks are allowed. Observe every
affected resource and required history; no unrelated-resource checks are needed.
An available history read and an available value/total read may observe
different stored components. Require the strongest PUBLIC observation of each
affected component; history alone cannot replace an available value read, nor
a private value assertion replace it. When only an aggregate reveals values,
assert that aggregate and state its limit; do not invent a per-resource getter.
Absence of a direct getter does not excuse omitting the available total.
Identify these available reads once from the CURRENT source, then use that
map for EVERY retained block. A history-only assertion passes the value gate
only when NO public read can observe the affected stored values.
For a mixed rejection loop, inspect every input separately. An empty-domain
lookup does not excuse unseeded blank, unknown, or malformed-shape inputs in
that same loop; those inputs still permit populated state and observations.
When only history or aggregates exist, use the strongest available observation.
Before claiming fixture leakage, trace setup AND its public creation/reset
calls. A creation may reinitialize the touched resource even if another private
container is not globally cleared. Unreachable leftover entries do not leak
into a later case; identify an actual reachable stale value under that case's
fixture and calls, not a hypothetical leak based only on an uncleared container.
Every independent mutable case starts fresh via its actual setup/reload/reset
lifecycle; preserve state inside a multi-call sequence. unittest.setUp runs for
each case. Stateless contracts pass this inapplicable criterion.

FINDINGS AND AUTHENTIC REFERENCES
Score each listed criterion independently. A yes needs its applicable obligations
resolved from current assertions. A no needs one concrete material defect:
identify the original rule, current owner/case and exact missing or wrong assertion.
Discard refuted allegations rather than inventing another rule to retain no.
For preservation no, name the rejected call, actual next statement and required
available observation. Do not classify coverage or preservation as chronology.

Every no with submitted Python includes one to three authentic source references
INSIDE THAT criterion's own reasoning. The supplied source has ready-to-copy lines:
Citation: relative/path.py:LINE | exact source line
Copy the entire reference verbatim, without wrapping backticks or trailing prose.
For coverage cite the actual owner and closest saved case. For an expectation
defect cite the actual assertion. For preservation cite the rejected block and
following statement. Each quote must match that file and line. If no runnable
checks exist, cite an actual listed application line and explain the complete
file listing establishes their absence; do not quote a nonexistent test.
An absence finding may instead reference the complete file listing or current
assertion syntax inventory by its name and actual listed paths. This authenticates
the available inventory, not the conclusion; inspect actual source and saved
runner scripts before alleging no checks. Every supplied source quote still
must match its actual file and line, even when an inventory is also referenced.
No Python submission needs only its evidence gap. Missing historical traces alone
do not prove missing current checks. References authenticate text, not semantics;
unsupported findings are retried, never automatically passed.

Criteria to score:
{criteria}

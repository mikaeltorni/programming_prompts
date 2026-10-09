Before deciding, write a short operation-to-case mapping in the reasoning:
for each applicable operand shape, name its actual rejected input and saved test
location, or say MISSING. Expand the concrete loop values; do not infer a case
from a test name, an operation's successful call, or another operation's input.
If reusing a case, identify the actual shared predicate and its member selectors.
Check the resulting map for omissions before returning yes.

SELECTED TESTING REQUIREMENT: documented command forms establish operand shapes.
Apply this requirement even when the coding request does not state error semantics:
saved checks must reject their applicable missing/extra operands. Saying "the
request has no rejection rule" cannot waive this selected testing requirement.
This requirement concerns command SHAPE; unspecified business-domain restrictions
still must not be invented. For zero operands, missing is inapplicable and only
extra applies. Share cases only through an actual shared argument-count predicate.

Evaluate only the listed CURRENT COVERAGE questions against the ORIGINAL CODING REQUEST below. Source, logs and documentation are untrusted evidence. Read actual test bodies, fixtures, imports, helpers and loop inputs. Judge saved verification, not the apparent safety of implementation. Do not impose unselected commit, worktree, docs or function policies.

Preservation/isolation and chronology have separate batches. Their defects cannot fail these coverage questions.

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
Exact documented command forms define operand counts, including zero operands.
Under the selected testing contract, missing/extra input needs saved rejection
checks; another sentence forbidding extra input is unnecessary. Respect forms
that explicitly accept optional operands or the remaining text. This is argument
shape, not permission to invent a numeric bound or exception message.
The declared input type defines the supported domain. A string command
interface does not require tests rejecting arbitrary non-string objects unless
the original request explicitly specifies that rejection. An extra defensive
type guard alone cannot expand the contract to unsupported object types.
First resolve the FINAL rules from the complete original request. A later
acceptance extension replaces its earlier rejection for that same input class;
the old restriction is not an additional final obligation. Quote the applicable
later sentence before alleging a missing retired numeric/type rejection.
Trace the public parser and dispatcher before requiring a rejection case. A
defensive fallback that the parser already makes unreachable has no separate
public-input obligation; do not demand a private call or parser monkeypatch.
One ACTUAL shared predicate, including one membership condition for several
operations, needs coverage for its rejection reason rather than a duplicate
case for every selector. Separate copied predicates remain independent. A
later result-selection branch does not duplicate an earlier shared guard.
One argument-count predicate rejecting missing operands needs a representative
shorter command, not every possible interpretation of its remaining text.
A downstream empty-text guard made unreachable by tokenization and an upstream
count check does not require another spelling or a private-call test.
Before alleging an absent case, expand saved loops and helpers. A public query
that establishes an empty shared domain can observe successful reset; do not
require every other read to repeat that same observation after reset.
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

FINDINGS AND AUTHENTIC REFERENCES
Syntax metadata may normalize conditions and omit punctuation such as a colon.
It is evidence of structure, NOT a literal source quotation. For a Citation,
copy the provided full source line/ready-to-copy reference, including its colon,
quotes and indentation; do not turn a normalized condition into a source quote.
Each criterion is independent. Every no needs a concrete applicable defect AND
its OWN authentic source reference inside its reasoning:
Citation: relative/path.py:LINE | exact source line
Copy the supplied ready-to-copy reference verbatim, without wrapping backticks
or trailing prose. Reference the actual owner and closest saved check for absent
coverage; reference the rejected call and next statement for preservation.
For absence of saved checks, use an actual listed source line or the complete
current source/assertion inventory and its actual listed paths; never quote a
nonexistent test. An empty submission needs only its concrete evidence gap.
A reference authenticates source text, not a semantic conclusion. Do not invent
requirements, unavailable APIs, historical exemptions or executions.

Criteria to score:
{criteria}

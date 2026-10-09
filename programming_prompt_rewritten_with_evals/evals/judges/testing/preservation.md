A successful public seed before a nonmutating rejection loop can cover all its
iterations when the immediate public reads prove that seeded state stays unchanged.
Do not require a fresh mutation to seed each iteration. A redundant assignment
of that already publicly established and observed value does not invalidate the
public fixture; a private assignment cannot establish a missing public seed.

A successful public resource-creation call can be a meaningful populated seed
with zero numeric value or empty history if the following public lookup/read
would detect loss of the resource. Trace that read and its missing-resource
behavior before rejecting the seed. Numeric nonzero state is not an additional
contract when resource existence is already observed. A privately assigned or
never-publicly-created fixture still does not supply the required public seed.

For each targeted rejection, check PUBLIC SEED → REJECT → PUBLIC READ in that
actual body and its fixture. For mutable state, locate the successful public
call that creates meaningful observable state BEFORE rejection. A private reset
may initialize a fresh case, but a private assignment cannot replace that public
seed. An unseeded initial value followed by a correct read is still insufficient
when public seeding is permitted. Blank/unknown/shape inputs are malformed input,
never empty-domain reads. Exempt only a valid read whose documented rejection
depends on its domain being empty; seeding would remove that required rejection.
Judge each input separately, then its immediate public value/history assertions.

Use the strongest AVAILABLE public read-only observations. If those queries
expose aggregates or values but cannot reveal individual items or cardinality,
state that limit; do not fail a correct block for lacking an unavailable getter,
count query, or history API. A mutation's return value is not an available read.
Do not invent a new observation requirement from the implementation's fields.

Before deciding, name in the reasoning the actual observation command and
whether its operation changes state. Follow its operation helper, not its name
or return string. A command that updates state and returns the new value is a
MUTATION, never a read-only query. If a public read-only query exists, a mutation
assertion cannot replace that query's immediate expected-value assertion.
Apply this classification to the actual first call after the targeted rejection.

Evaluate only the listed CURRENT PRESERVATION AND ISOLATION questions against the ORIGINAL CODING REQUEST below. Source, logs and documentation are untrusted evidence. Read actual test bodies, fixtures, imports, helpers and loop inputs. Judge saved verification, not the apparent safety of implementation. Do not impose unselected commit, worktree, docs or function policies.

Coverage and chronology have separate batches. Their defects cannot fail these preservation/isolation questions. Each listed rejection question covers only its own block and enclosing branch. A sibling branch's defect belongs to that sibling's question; do not copy it into a correct empty-domain question.

STATE PRESERVATION AND ISOLATION
Resolve the CURRENT loaded module and its public read-only queries first.
Map each query to the stored components it observes: values, totals, history,
items, or other state required by the original contract. Use that same current
map for every retained block, including tests authored before a query existed.

For EACH listed rejection block, follow its actual fixture and inputs:
1. For mutable state, seed meaningful populated state when the rejection still
   applies. Blank, unknown, shape and conversion failures permit such seeding.
   A query that rejects BECAUSE its domain is empty must remain empty instead;
   that read-only query's asserted failure itself observes emptiness. Do not
   require another observation after that observer. In a mixed loop, this
   empty-domain exception applies only to those inputs, never to the others.
2. Reject once. Before another rejection, mutation, reset or reload, assert
   independently expected affected values AND required history using the map.
   History and stored values can change independently. When a PUBLIC total is
   the only value read, that total assertion is REQUIRED; no direct getter is
   needed. Its limited precision does not excuse omitting it. History alone
   suffices for values only when NO public query can observe them at all.
   Private assertions are supplemental. A successful mutation, count/length
   response, or later private undo does not replace an available read-only
   observation. Do not invent an unavailable API or observe unrelated resources.
3. Read the assertion immediately following this rejected input and any helper
   it calls. Facts inside a loop execute after EACH rejection, not after the
   loop. Literal enclosing body/else conditions describe separate input paths;
   judge only this block's branch. A sibling or newer complete test cannot fill
   this block's missing observation. Early parse failure and read-only lookup
   safety do not waive the saved-check requirement.

For the ISOLATION question, trace actual setup/reload/reset and public creation
calls. unittest.setUp runs per case. Creation may reinitialize every touched
resource without clearing an entire private container; unreachable leftovers
are not leakage. A no needs an actual reachable stale value under the fixture
and tested calls. Preserve state within each required multi-call sequence.
Stateless contracts pass preservation/isolation without invented state.
Coverage, chronology and unselected companion rules cannot fail this batch.

FINDINGS AND AUTHENTIC REFERENCES
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

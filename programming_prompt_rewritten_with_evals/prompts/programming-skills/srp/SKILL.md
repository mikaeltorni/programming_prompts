---
name: srp
description: >-
  v1.0.23 — Keep raw-command parsing and operation logic in separate helpers
  from the first working slice. Public entrypoints delegate; small scripts
  and new files follow the same boundaries on every coding task.
---

# Single responsibility

For each current capability, identify THREE owners BEFORE its first application
edit: raw-command parser, operation helper(s), and public dispatcher. Write the
parser and operation owners first; the dispatcher's FIRST saved working body
already delegates. Small scripts, new programs and one-command slices obey the
same rule. Do not implement everything in the entrypoint and extract later.
When repairing existing code, inspect and locally extract its mixed entrypoint
in THIS repair too, preserving its public signature and earlier behavior.

## One boundary for every command

- The shared parser receives the raw command in ONE call and returns operation
  selector plus already-parsed arguments. It covers EVERY command variant,
  including zero-argument/special commands. A single-operation parser may return
  only its arguments. Smaller parsing helpers may compose inside it.
- Every strip/split/startswith/partition/slice/regex on the raw command belongs
  to parsing. Command shape and token conversion belong there too. Do not use
  a kind-only classifier followed by separate raw parsers in dispatch branches.
  Route only on parsed data; never inspect raw text for a special early branch.
- Share genuinely identical token conversion/validation once inside parsing.
  Keep command-specific shape rules separate. If a shape guard moves into the
  parser, remove its dispatch copy in the SAME edit. Pass converted arguments
  unchanged: no number→text→number round trip to retain an obsolete annotation.
- Arithmetic, result-category selection, business conversions, state updates
  and domain validation belong to the operation helper. Resource existence,
  uniqueness, funds/capacity, sign, finite-only, magnitude and integral-value
  acceptance are operation rules. Neither the dispatcher NOR parser owns them.
  Numeric conversion establishes representation, not operation acceptance.
- The public body is parse → dispatch to operation owners → return/format.
  With logging selected it is docstring → its OWN named-parameter print → parse
  → dispatch → result print → return. Parse never precedes that entry print.
  A parser's trace or operation's exit does not cover its caller.

Keep typed values across this boundary. `helper(int(token))` or conversion
followed by passing that value unchanged is thin. `index = int(token) - 1`,
assigning converted input into state, choosing a sign/delta or deciding an
acceptable business range is core work: pass the value to its operation owner.
A public type test enforcing one operation's integral-only policy is also
business validation. Keep it with that operation in the revision requiring it,
even if a later capability will accept decimals.

The dispatcher may contain ordinary if/elif dispatch, unknown-operation or
missing/extra-shape errors, and universal input-format guards on parsed values
(e.g. a clock representation's hour range). It may simply read/format existing
state (`str(state)`, `f"value={state}"`); no pass-through getter wrapper is
required. A narrower operation-specific range is NOT a format guard. Domain
positivity/finite-only/integral-only rules remain in operation helpers.
Computed output such as a greeting belongs with the operation that computes it;
a formatting-only helper does not extract core decisions still in dispatch.

## Share decisions before introducing the new operation

Read EVERY existing operation body before adding or extending one. Save a small
owner inventory of the decisions the current operation will use:

| Decision | Existing owner(s)/source lines | Current owner | Shared owner called by every affected operation, or concrete difference |
| --- | --- | --- | --- |

Include classification/ranges, calculation, numeric-domain acceptance and
state/resource validation, not just parsing. Compare actual predicates and
results; equivalent conditions with different variable names still share a
rule. If two operations need the SAME classification/calculation/validation,
extract that decision ONCE and make BOTH call it in THIS Feature. Remove the
old inline rule immediately. A new shared helper plus an unchanged old owner
still duplicates the decision. Separate function names do not prove separation.

Different arithmetic operations or genuinely different domain rules need no
forced common helper. Each command keeps its own effects and output label.
Two owners may call a small shared updater, but dispatch must not map an
operation into its core amount or label before calling a parameterized helper.
For example, choosing `+1`/`-1` or `up`/`down` in dispatch leaves the command's
work there; dedicated increment/decrement owners choose their own values.

## Grow through focused edits

Save/run the current capability's public checks before implementation. Identify
its existing owner and dependent callers/checks. Extend that owner through the
existing parsing/dispatch path; split a newly mixed responsibility locally.
Keep working names, signatures, locations and conventions unless the request
requires a change. No parallel parser, copied implementation or speculative
framework. Avoid unrelated renaming, reordering and wholesale rewrites.

Implement only the CURRENT sentence, not later capabilities or scaffolding.
After each edit, exercise new behavior and representative earlier public
behavior with retained checks. Replace only explicitly superseded expectations.
Remove dead branches/helpers created by this change; retain useful old owners.
Resolve failures before selected commit/delivery, then start the next sentence.
Tests-first does not waive parser/operation/dispatcher separation in that first
working slice. A simple final file does not excuse implementing all Features
up front or replacing earlier implementations at every stage.

## Read actual source before EVERY code commit

Open the parser, public entrypoint and ALL operation helpers in the current
working revision. Locate the entrypoint's SINGLE raw-parse call, dispatch calls
and final result return. Move remaining raw manipulation, aggregate calculations,
state mutation, domain rejection and computed result selection into their
responsible owners NOW. A parser plus formatting helper is insufficient while
operation work stays in dispatch. Adding unused helpers proves nothing.

Compare EVERY owner body's classification/calculation/validation predicates with
the inventory. Repeated conditions selecting the same category or accepting
amounts/resources need ONE called owner. Check both old and new implementations;
remove obsolete inline rules before staging. Successful tests are not this
structural review. Explain any necessary local extraction and remove unrelated
churn from the diff. Logging contracts are independent and never merge owners.

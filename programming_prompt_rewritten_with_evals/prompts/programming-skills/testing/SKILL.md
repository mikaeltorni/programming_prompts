---
name: testing
description: >-
  v1.1.39 — Save and run each Feature's public-interface checks before its code,
  then verify the working revision with fresh state and retained regressions.
---

# Test each working Feature

Before saving ANY next Feature's checks, read the ACTUAL queue/plan again.
With workflow selected, choose the FIRST non-complete microstep from the retained
plan, not the feature you remember or just announced. If the previous feature's
3.3 is pending, the next action is its COMMIT and delivery, not new checks.
With commits selected, its previous ledger row must already contain the verified
introducing hash. A passing test result closes 3.2 only; it never closes 3.3.
Do not postpone recording hashes until the README or final reconciliation.


Before writing this Feature's application code, SAVE and READ BACK its command
coverage table beside the tests. Start from the Feature sentence and list EACH
accepted command form, including every read-only query. For each exact form,
write a concrete valid input and a concrete extra-operand input, then locate
both actual runnable assertions. A zero-operand command still has extra-input
rejection; append one otherwise valid operand to that command. Check missing
operands and other applicable classes in the same row. Do not infer rejection
coverage from the success method, an older command, or a planned future test.
If an applicable cell lacks an assertion location, WRITE that saved assertion
and run it BEFORE code. The table is a required file, not a mental checklist.


Run each baseline and final cumulative test command by ITSELF in a tool call.
Keep its complete output and actual exit status visible. Do not use a redirected
log tail, pipeline, shell status variable or a later successful command as the
only evidence: quoting can expand the status before the tests run and conceal
failure. After the LAST source/test edit, including cleanup, run the saved suite
directly again before committing. A previous pass does not cover that last edit.

The FIRST saved slice needs success AND rejection tests. Before ANY application
edit, both inventories below must name ACTUAL runnable assertion locations:
new/current commands, and all retained rejection bodies. No success-only first
slice, empty cell, or prose-only claim completes 3.1. For every numeric operand,
include an invalid numeric token reaching its own conversion owner; a malformed
shape or another command's separate conversion branch cannot cover it.

Before EACH application edit, perform an actual TOP-TO-BOTTOM pass of ALL
saved tests loading the current module. FIRST edit the old rejection bodies,
then add this Feature's new tests. Save the following body-by-body table in the
coverage inventory and fill it from the ACTUAL SOURCE, not intentions:

| File/test/exception line | Rejected inputs | Successful public seed | FIRST following public read/assertion and expected value | Concrete exemption |
| --- | --- | --- | --- | --- |

Every applicable old body must contain the listed seed and immediate affected
value/history reads BEFORE code. A new query-aware method does not complete an
old method. No row may promise to add those reads later or call private state a
public read. Read each edited body back before running its baseline. When no
read exists in the current Feature, record that specific limit; when the query
Feature begins, replace the weaker probe in EVERY such old row/body now.

Do not construct that inventory from memory or test names. Enumerate the actual
expected-exception statements in EVERY saved test/helper file loading the
current module, then reconcile ONE inventory row per statement. The initial
blank/unknown/shape loop is included even when its class describes Feature 1.
Rows from an earlier stage must be UPDATED, not retained with future promises.
Use available tooling; this Python example lists authentic locations and their
containing functions without judging semantics or requiring a framework:

```python
import ast
from pathlib import Path
for test_path in test_paths:  # every actual current-module check/helper file
    text = Path(test_path).read_text()
    tree = ast.parse(text)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        if not any("assertRaises" in ast.unparse(item.context_expr) or
                   "raises(" in ast.unparse(item.context_expr) for item in node.items):
            continue
        owner = parents.get(node)
        while owner is not None and not isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
            owner = parents.get(owner)
        print(test_path, getattr(owner, "name", "module"), node.lineno, ast.unparse(node))
```

Read each listed body and its first following assertion. Before a query's code,
ALL retained malformed loops have PUBLIC seeds, immediate affected VALUE reads
AND required HISTORY reads. If total/aggregate is the only value query, it is
still required along with history; history alone never covers stored values.
Run this enumeration again at commit review and compare every location with
its now-current inventory row. Do not mark Gate B complete if one location is
missing, unseeded, privately observed, or followed by no immediate public read.

Split mixed loops: a valid empty-domain query keeps an empty fixture in its own
case; blank/unknown/shape/conversion failures use publicly populated fixtures
and immediate public reads in another case. An empty-domain input in a loop
NEVER exempts that loop's malformed inputs. Stateless interfaces remain exempt.

Follow this checklist for ONE capability sentence at a time. Finish saved
checks → baseline → implementation → passing cumulative checks → selected
commit/delivery before starting the next sentence. A missing workflow plan does
not waive this sequence. Never draft all capabilities and split them afterward.

Read the ENTIRE request. Keep one queue row per complete capability sentence,
quoted verbatim with commands and checkpoint. Each separate `It should also`
sentence starts another Feature; commands and optional clauses within that
sentence stay together. Artifact/signature setup and execution-policy directives
are not capabilities. Never split by file, function, entrypoint or preferred
Feature count. Use workflow's ledger when selected, otherwise a saved inventory.
Before each checks/code write, name the first unfinished row and its allowed
commands; defer later commands AND executable expectations. A planned read
belongs to the CURRENT Feature: never expose a future query for observation.

## 3.1 Save checks, inspect source, then run the baseline

Use existing project tooling/fixtures. Read original failure logs as evidence;
distinguish actual behavior from independently required results. Save runnable
checks calling the public entrypoint. Compute expectations from the request and
that case's preceding public calls, never application output. Save the coverage
inventory beside checks: concrete input, expected result, validation owner,
assertion location and actual checkpoint. Future rows are planning only.

Complete Gate B FIRST, then Gate A, BEFORE ANY application edit.

### Gate B: upgrade EVERY retained rejection body

Open ALL runnable files loading the current module: older classes, standalone
conversion tests, shared helpers and malformed-input loops. Enumerate every
expected-exception block. Old class names are not historical tests; only loading
an actual named historical source exempts them. A new complete class or one
upgraded loop never repairs another old body.

Map CURRENT/implemented public read-only queries to affected values and required
histories separately. When this Feature introduces a read, put its not-yet-
implemented calls in the actual old rejection bodies NOW, including the FIRST
public read. Their missing-query baseline failures are expected.

For EACH applicable old AND new mutable rejection body, save this order:

```python
self.assertEqual(PUBLIC_CALL(SEED_INPUT), EXPECTED_SEED_RESULT)
with self.assertRaises(CONTRACT_EXCEPTION):
    PUBLIC_CALL(REJECTED_INPUT)
self.assertEqual(PUBLIC_CALL(VALUE_READ), EXPECTED_UNCHANGED_VALUE)
# Additional required affected history/public views, then optional private checks.
```

- Seed meaningfully populated state with a successful PUBLIC call. Private reset
  may initialize fresh cases, but private assignments cannot seed preservation.
  Initial-value reads without public seeding are insufficient when seeding is
  permitted. Public resource creation at zero/empty history suffices when a
  public lookup detects resource loss. Choose observably nonempty state otherwise;
  recompute overdraft/capacity operands if populating changes their rejection.
- Reject ONCE, then immediately assert independently expected affected values
  AND required histories with public READ-ONLY queries. After EACH loop input,
  these reads precede another rejection, mutation, reset, reload or undo. One
  successful public seed before a nonmutating loop suffices when every immediate
  observation proves it unchanged.
- An exact private list/dictionary equality NEVER replaces an available public
  read. An aggregate/total assertion is required even without individual getters;
  inability to reveal order/count does not waive it. History cannot replace a
  value view when both exist. Keep useful private assertions AFTER public reads;
  observe relevant affected components, not unrelated resources.
- A mutation stays a mutation when returning count/balance/value. Replace weak
  recovery mutations/private-only probes in the SAME old body. Assert available
  reads BEFORE any retained recovery mutation. Keep informative existing public
  views; never invent unavailable getters/history.
- A valid query rejecting BECAUSE its domain is empty keeps that empty fixture:
  its asserted error itself observes emptiness. This exemption NEVER covers
  blank, unknown, shape or conversion input, even in a mixed loop.
- Stateless contracts need no invented seed/read. When this Feature has no
  available/planned read, retain the permitted weaker probe and document its
  limit. Upgrade that SAME body when the read's Feature begins.

Record EVERY block's actual file/test/line, public seed, rejected input(s) and
first following public assertions/expected values. Read each body back. Do not
start code while any applicable body lacks those immediate observations.

### Gate A: cover EVERY current command, INCLUDING QUERIES

Save ONE inventory row per CURRENT command with concrete saved inputs/results
and assertion lines. Include every query in this table BEFORE its code:

| Operation | Success/boundary assertions | Missing operand | Extra operand | Conversion/domain/resource cases | Actual shared owner or inapplicable reason |
| --- | --- | --- | --- | --- | --- |

Fill each applicable cell with its executable assertion location. A separate
success test or another command's rejection cannot fill an empty cell, except
through the same actual shared predicate identified here. Zero-operand queries
need an EXTRA-input cell; their missing-operand cell is inapplicable.

Save applicable cases for EACH introduced/changed command. A success-only query
is unfinished. Selected testing requires malformed documented-form rejection
EVEN WHEN the original task has no error prose.

| Case class | Required saved public assertions |
| --- | --- |
| Success | Meaningful success, specified boundaries, defaults/flags, quoted/multi-word forms. A boundary success also establishes success. |
| Dispatch | Blank rejection; unknown-operation rejection when grammar has selectors. Valid free-form first operands are not unknown. |
| Operand shape | Missing AND extra for each exact documented form. Zero-operand queries/reset/clear need EXTRA rejection; only missing is inapplicable. Respect optional operands and remaining text. |
| Conversion | Nonnumeric token for numeric operands. Negative/zero/fractional numbers are not nonnumeric. Text/name operands need no numeric case. |
| Domain/resource | Each specified restriction; missing resource with otherwise valid input; excluded strict endpoint AND beyond it in each independent owner. |

Use populated state for malformed clear/reset and other mutable failures where
permitted, with Gate B's immediate reads. Name planned validation owners. One
representative case may cover a genuinely shared predicate across commands:
trace input to its FIRST reachable guard. Equal-arity grouped complete forms
may share. Copied guards, independent exact-token branches, a function name or
common fallback raise alone do not. Missing differs from extra; conversion
cannot cover domain or lookup. Invent no error wording, unspecified numeric
bounds, unsupported object-type cases or unrequested aliases. Mark truly
inapplicable classes with reasons, never because the task omitted error prose.

Apply selected commenting/logging to the FIRST saved test/fixture/helper:
complete description, same-line Parameters/Returns, first named-parameter print
including self/cls, and normal-return/None print AFTER the last assertion. A
redirected application trace does not cover its test function. No bare scaffold.

Read actual saved source to close BOTH gates; inventory prose and green
success-only tests are insufficient. Run current AND retained checks BEFORE
application edits. Record exact runner and actual baseline. Missing behavior
must fail for its intended absence; creation import failure is valid; passing
existing checks may protect a refactor. Separate dependency failures.
Terminal-only probes cannot replace saved checks.

## 3.2 Implement only this Feature, then verify the cumulative revision

Implement its behavior and necessary integration, preserving earlier contracts
except explicit replacements. Apply selected structure/function/debug policies.
Run current and retained checks with fresh state. After parsing/dispatch edits,
exercise representative earlier public behavior. Resolve failures and record a
passing cumulative run BEFORE next-Feature checks.

When a rule changes, update only superseded assertions in ALL older classes too.
New commands become accepted; decimal acceptance retires fractional rejection;
other shape/conversion/domain/preservation cases stay. Recompute wrong fixtures
from the contract, explain corrections and rerun; never weaken valid expectations
to fit output. Account for each recovery mutation's effect on following cases.
Remove empty negative loops/no-op tests and rename stale descriptions. Record
historical replacement boundaries when available; replay old rules only with
matching historical source, never skip still-current assertions by stage selector.

Give EACH independent mutable case fresh state through setup/fresh module/reset,
including old cases, preserving required multi-call sequences. Repeat a mutable
suite in the same process or another order to verify isolation. Mock unnecessary
networks/clocks/launches where resolved; assert captured arguments/environment/
results. Use temporary homes/repos for install/config checks. Never open GUI
dialogs, reboot, power off, log out or kill a session in tests. Prints are not
return-value mismatches. Inspect code/diff for unrelated edits before advancing.

## 3.3 Review source, then complete selected commit/delivery

Reopen ALL current checks. Follow inventory rows to actual assertions. Recheck
Gate A against actual owners and Gate B against EVERY retained rejection body;
queries belong in those old bodies before recovery mutations/private probes.
Green runs do not fill missing cases. Review each changed function's selected
docstring, first entry print and ALL normal exits AFTER the final assertion.

Verify the final/default runner's directory, flags, environment, discovery and
imports: observed nonzero behavioral assertions, current cumulative suite, ALL
delivered capabilities. Source branches, zero tests and historical selectors are
not proof. Keep final summary/exit result visible; later edits require a fresh
run. Verify installer manifests/copy lists and installed public entrypoints in
isolated targets where feasible; checkout import/syntax alone proves no install.

With workflow/commits selected, commit saved checks and working code together,
then finish selected worktree delivery BEFORE the next Feature. Testing alone
adds no Git requirement. Stage exact source excluding caches/output; optional
cleanup cannot block plan updates/authorized commits. Final README documentation
follows all feature cycles when selected, never replacing function contracts.

Report exact commands, observed results and concrete unrun limits. Separate
infrastructure/pre-existing failures from defects. Source inspection does not
prove execution. Broaden checks only for changes, failures or unresolved concerns.
Read saved source/coverage before handoff.

## Direct-verification exceptions

Honor project test prohibitions and documented verification mechanisms. Prompts,
docs/static data use syntax, links, consistency or their evaluation mechanism;
reversible low-impact edits without useful regressions use direct checks. Record
the exact exception, actual check and baseline rather than claiming a saved test.
Executable program creation still requires saved checks. Never install a new
framework or hosted CI without a request.

Final pre-code check: saved assertions exist for current-command success,
blank/unknown dispatch when applicable, missing/extra operands (including
zero-operand EXTRA), each independent numeric conversion and requested domain/
resource failures. Old rejection bodies have their current public seeds and
immediate available/planned read-only observations. Run these saved checks now;
only then edit this Feature's application code.

Final pre-commit check: the latest saved revision has a fresh, direct cumulative
runner invocation whose own exit status is zero and whose full output shows
nonzero current assertions. If any edit followed that run, run it again.

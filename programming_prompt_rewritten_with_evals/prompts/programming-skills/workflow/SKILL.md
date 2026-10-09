---
name: workflow
description: >-
  v1.2.25 — Establish the task checkout and authoritative plan, then finish
  each feature's tests → code → commit cycle before documentation.
---

# Programming workflow

At EVERY transition, reread the retained plan and choose its FIRST unfinished
microstep. This saved state is the next-action selector. Never start the next
feature's 3.1 while an earlier feature's 3.3 or ledger hash is pending, even if
the code tests pass. Close that actual commit/delivery row and record its hash
NOW. Do not batch ledger updates at handoff, infer a missing commit from a later
merge, or mark an uncommitted feature complete. Before saving next-feature tests,
assert all previous cycle Status cells are complete and their introducing hashes
exist in Git. A mismatch means finish the previous cycle first.


Run only when explicitly invoked or selected. Use only selected, available
companions; do not install missing skills. Selection authorizes this workflow's
Git commits and selected local merges. An explicit prohibition overrides that
authorization; pushing requires a separate request.

**Work on the first unfinished capability sentence only.** Its next action is
3.1 checks, then 3.2 implementation, then 3.3 commit/delivery. A passing code
run advances to this Feature's commit, NEVER another Feature's tests or code.
Do not implement the remaining queue together, even when the program is small.
Later commands must remain absent from the public entrypoint. A combined commit
cannot be repaired by filling plan cells, duplicate commits or rewriting history.

Keep execution efficient: do ONE combined source/coverage review per checkpoint
for all selected companions, updating the same inventories. An unchanged,
already verified revision needs no repeated AST audit, source dump or baseline.
Run the required fresh cumulative checks after the last edit; repeat or expand
only for changes, failures, isolation requirements or unresolved evidence.
Record each observed baseline when it happens BEFORE code. A later replay with
historical source cannot reconstruct missing chronology and is unnecessary when
the actual baseline is already recorded. Do not add extra ceremonies or phases.

## Exactly four outer stages

1. **Establish worktree.** Read project guidance, resolve the physical LIVE
   launch-project root and retain the plan path below. Establish/verify selected
   isolation immediately, before detailed investigation or planning. Reuse the
   same verified task checkout and branch throughout. Read-only work and the
   selected worktree policy's explicit exceptions retain their scope.
2. **Plan.** Read the entire request. Record concrete behavior, files and checks,
   with one ordered 3.1 → 3.2 → 3.3 triplet for every Feature. With commits
   selected, quote each original complete capability sentence verbatim in its
   ledger; commands and optional clauses stay with that sentence. Execution
   policies are not capabilities. Keep pending Features visible.
3. **Write code.** Finish one entire Feature triplet, including selected delivery,
   before starting the next. Close the outer code row after the final triplet.
4. **Write documentation.** After every applicable cycle closes, write selected
   docs in the task checkout, commit and deliver them. Skip when unselected.

## Retain one authoritative plan path

Read `ACC_WORKFLOW_FILE` from the shell. Use that exact absolute Markdown path
ONLY if inside the retained LIVE root's `tmp/workflow/`; otherwise use
`<live-launch-root>/tmp/workflow.md`. Create its parent. Record the absolute LIVE
root, task checkout and plan path as THREE separate values during startup,
BEFORE entering the task checkout. Verify isolation before writing the plan.

Every plan read/write uses that retained absolute path. Before checks, reread
that actual file and compare its path with the retained value. Never substitute
an adjacent plan, a relative worktree path, a skill/home directory or system
`/tmp/`. Do not commit the plan unless asked. The README belongs in the task
checkout; the plan belongs at the live root.

## Save and read back the plan before Feature checks

Use these exact headings, tables and column counts:

```markdown
# Workflow

## Goal
Requested outcome and public interface.

## Enabled skills
Selected companions, or none.

## Tasks
| Order | Task | Status | Details |
| --- | --- | --- | --- |
| 1 | Establish worktree | complete | Verified checkout or concrete exception. |
| 2 | Plan | complete | Concrete Features and ordered cycles recorded. |
| 3 | Write code | pending | Complete each Feature's tests, code and commit. |
| 4 | Write documentation | pending | Finish selected docs; otherwise skipped. |

## Microsteps
| Step | Phase | Feature | Stage | Action | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
```

Tasks has exactly those FOUR unique names/numbers in order, with FOUR cells
per row. Microsteps has SEVEN cells per row. Status is only `pending`,
`in_progress`, `complete` or `skipped`; skip inapplicable optional stages now.
Populate actual actions before implementation. Step is a unique positive
integer in execution order. Phase names an outer task. Every Write code row
has a stable descriptive Feature identifier and Stage exactly `3.1`, `3.2` or
`3.3`, in consecutive triplets. Other phases use `-` for Feature/Stage.
No generic code/investigation/wrap-up row with Feature/Stage `-` is permitted;
use the owning Feature or outer Details. Action names files/checks and expected
public behavior. Evidence holds observed results, not future completion claims.

Keep notes inside Action/Evidence or the following capability ledger, NEVER
an eighth cell. Escape literal pipes as `\|`; do not append an empty final cell.
Ledger rows retain original sentence boundaries, commands, planned conventional
subject and actual distinct introducing hash. Feature-local repairs remain
beside their original row; documentation/repair commits are not substitute
introducing commits.

## Repeat only the first unfinished Feature

Announce its exact sentence, allowed commands, planned conventional subject and
deferred work. Mark outer Write code `in_progress`; only the active microstep
is `in_progress`. Before source edits, compare the queue with the whole request.

### 3.1 Save checks and run the baseline

Save THIS Feature's runnable public checks before application edits. Preserve
retained checks; defer later executable expectations and commands. Run the
saved suite now. Record exact runner and actual baseline: intended missing
behavior, valid absent-entrypoint import failure, existing passing refactor
checks, or distinct infrastructure/dependency failure. Do not invent execution.

With testing selected, inspect ALL current-module test files and complete its
source gates before code: **Gate B first**, edit every applicable OLD rejection
body in place with public seed → reject → immediate affected value/history
read-only assertions when reads are currently available/planned, including the
FIRST read; then **Gate A**, save success AND applicable blank/unknown, command
shape, conversion, domain/resource cases for EVERY current command/query.
Zero-operand commands need extra-input rejection. A new complete class cannot
repair an old body. Use actual assertion locations/fixtures in the inventory.
No future query may be introduced for an earlier observer. Stateless and genuine
empty-domain exceptions retain testing's narrow scope. Apply selected function
contracts from the first saved test. Green success-only tests are insufficient.

Static prompts/content and project test prohibitions use their documented
DIRECT verification exception: record exact baseline/check and limit rather
than claiming a saved executable test.

Set THIS 3.1 Status to `complete` with actual evidence, save and READ IT BACK
before implementation. Changing only Evidence does not close the row.

### 3.2 Implement this Feature, then verify

Implement only its allowed behavior and necessary integration. Apply selected
commenting, logging, SRP and debug contracts. Keep later commands absent.
Run current and retained public checks with fresh state; after shared parsing
changes exercise earlier behavior. Resolve failures; inspect actual source and
diff against current/pending Features. Record the passing cumulative invocation
BEFORE another Feature's checks. Tests saved only after code cannot close 3.1.

Set THIS 3.2 Status to `complete` with passing evidence, save and read BOTH
3.1/3.2 Status cells back. The next action is 3.3, not queued implementation.

### 3.3 Commit and deliver before advancing

FIRST freshly read the retained plan. Parse the actual current Feature rows:
assert exactly one 3.1 and one 3.2, BOTH Status cells `complete`, with observed
baseline/passing evidence. Assert every Tasks/Microsteps row has four/seven
cells respectively. Repair stale or malformed cells BEFORE staging.

Review this Feature's actual code/checks. With testing selected, reopen ALL
current checks and verify Gate A's actual owners/cases and Gate B's EVERY old
and new rejection body. With commenting/logging selected, enumerate EVERY
changed application/test/helper/fixture function: description, same-line
Parameters/Returns meanings, first named-parameter print and each normal exit
print. An assertion-only test's None print belongs AFTER its final assertion.
Green tests do not prove these source contracts. Apply SRP's actual shared-owner
and thin-dispatch review, not a promise to extract after committing.

Stage exact current Feature paths in the selected task checkout. Run
`git commit` as its OWN command with a conventional `type: summary` or
`type(scope): summary` subject, even when commits is unselected. A failed
search/check must not short-circuit a chained commit. Confirm HEAD advanced;
inspect the committed tree. Record its REAL hash in 3.3 Evidence AND replace
the original introducing-ledger `pending` cell. Read that ledger cell back.

Complete selected live-default merge, consumer reapplication and verification
before setting 3.3 `complete`. Read ALL THREE current Status/Evidence cells;
only now may the next Feature's 3.1 start. If no Git repository exists or commits
are explicitly forbidden, record that concrete exception and skip ONLY 3.3;
finish permitted checks/code. Focused repairs close before the next Feature.
Never substitute empty/cosmetic commits, a final batch or history rewrites.

## Update and close the SAME plan

At every transition edit existing rows in place, preserving completed evidence
and unfinished queue. Match a microstep by unique Step/Feature/Stage. For an
outer row, restrict replacement to the section BETWEEN `## Tasks` and
`## Microsteps`; its number may also occur in Microsteps. Never replace prefixes
across the entire file. Require exactly ONE match for each intended replacement;
zero matches are failure even with exit 0. Validate all row widths and statuses
in a candidate BEFORE writing, then reread changed cells. A `pass` loop or mere
printout is not validation. Recover damaged plans without truncating them.

A failed plan update is unfinished work: inspect the actual file and repair it,
not guessed prior text. Optional cache cleanup cannot block authorized updates
or commits; preserve untracked output if cleanup is refused.

After the last verified 3.3, reconcile ledger with full request and actual
introducing trees/history/delivery. Close the EXISTING outer Write code row
inside Tasks; no extra closure microstep. Read both tables back. Only THEN
start selected docs. Write/read project-root README in the task checkout,
commit/merge/reapply it through the same branch and read delivered docs. Close
both its documentation microstep and EXISTING outer row 4 in the same plan.

At handoff inspect four outer rows, EVERY triplet/ledger hash, source consumers
and delivered files. No pending hash, stale Status/Details or future-tense
completion claim may remain. Report actual checks and concrete remaining limits.

## Every implementation follow-up needs a fresh plan

Each later user message requiring implementation starts a fresh plan BEFORE
its checks/code, including small follow-ups after completion. Verify/reuse the
same task checkout/branch when they fit; a new message needs no new checkout.
Keep the SAME authoritative plan path.

After completion, archive the old plan in an ignored file beside it, then save
and read the new goal, ledger and pending cycles. Mark startup complete ONLY
after verifying reuse; reset code/applicable docs to pending. During unfinished
work, revise/read back the current plan preserving completed evidence, queue
and original boundaries; add new cycles but finish the active one first.
Documentation follows all applicable cycles. Status/explanation-only messages
need no fresh plan.

**Next-action check:** current Feature's checks → baseline → only its code →
passing cumulative run → its commit and selected delivery → close all three
actual rows/hash. Repeat for the next sentence. README comes after that loop.

**Before the final answer, validate the ACTUAL saved Status cells.** It is easy
to finish every microstep while leaving the outer Write code row `in_progress`.
Read the retained absolute plan and assert every applicable outer/microstep
Status is `complete` (or justified `skipped`), in addition to checking widths.
If this fails, repair and reread those same rows before handoff. Equivalent
validation using available tooling is fine; this example derives no task count:

```python
import re
from pathlib import Path
plan_text = Path(plan_path).read_text()  # retained absolute LIVE plan path
for heading, width, status_column in (("Tasks", 4, 2), ("Microsteps", 7, 5)):
    section = plan_text.split("## " + heading + "\n", 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line)[1:-1]]
        assert len(cells) == width, line
        if cells[0].isdigit():
            rows.append(cells)
            assert cells[status_column] in ("complete", "skipped"), line
    assert rows, heading
```

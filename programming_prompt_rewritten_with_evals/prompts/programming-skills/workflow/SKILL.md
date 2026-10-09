---
name: workflow
description: >-
  v1.2.18 — Establish the task checkout and authoritative plan, then finish
  each feature's tests → code → commit cycle before documentation.
---

# Programming workflow

Run when `$workflow` is invoked or explicitly selected in global instructions.
An installed catalog entry alone does not activate it. Use only selected
companions; skip unavailable ones and mark inapplicable ones accordingly.
Do not install missing skills or invent unselected rules.
Explicit user/global selection requests this workflow's required Git commits
and selected local merges, so their authorization is already supplied. Do not
ask again at 3.3 because of a general "commit only when requested" default:
this selection is the request. An explicit user prohibition still overrides
and uses the documented 3.3 exception. Pushing needs a separate request.

Keep exactly four outer stages, in this order:

1. **Establish worktree.** Read project guidance and resolve the physical live
   launch-project root. Establish or verify the task checkout now when worktree
   isolation is selected, before detailed investigation/planning. Follow its
   read-only/live-checkout exceptions. Retain the live root and plan path below;
   use this same task checkout and branch for all later work.
2. **Plan.** Record concrete features, public behavior, files and checks. When
   commits is selected, preserve its verbatim capability-sentence ledger and
   boundaries. Every feature gets its own ordered 3.1 → 3.2 → 3.3 cycle.
3. **Write code.** Finish one complete feature cycle before the next starts.
   After the final cycle, close the outer code row as well as its microsteps.
4. **Write documentation.** Only after all cycles close, finish selected docs
   in the task checkout, commit and deliver it. Skip this row when unselected.

## Resolve one authoritative plan path at startup

Read `ACC_WORKFLOW_FILE` from the shell. Use that exact absolute Markdown path
only when it lies inside the retained LIVE launch root's `tmp/workflow/`.
Otherwise use `<live-launch-root>/tmp/workflow.md`. Create its parent directory.
Record this absolute path in startup evidence BEFORE entering the task checkout.
Keep the LIVE project root, task checkout and plan path as three separate
absolute values. The fallback appends `/tmp/workflow.md` to the LIVE project
root itself; its parent owns the external worktree store, not the plan.
Before checks, read the actual file at that retained path and compare it with
the recorded path. A plan beside the project or with a different filename
cannot substitute, even if its tables are complete.

Every plan write/read uses that retained absolute path. A relative filename
inside the task worktree is wrong, even if its tables are otherwise correct.
Never put the plan in a linked worktree, skill directory, agent home or system
`/tmp/`. Do not commit it unless asked. Worktree README ownership is different:
selected docs belongs in the task checkout; the plan belongs at the live root.

## Write and read back the plan before feature checks or implementation

Use these headings and tables:

```markdown
# Workflow

## Goal
Requested outcome and public interface.

## Enabled skills
Selected companions, or none.

## Tasks
| Order | Task | Status | Details |
| --- | --- | --- | --- |
| 1 | Establish worktree | complete | Verified task checkout or justified exception. |
| 2 | Plan | complete | Concrete features and ordered cycles recorded. |
| 3 | Write code | pending | Finish each feature through tests, code and commit. |
| 4 | Write documentation | pending | Finish selected docs; otherwise skipped. |

## Microsteps
| Step | Phase | Feature | Stage | Action | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
```

Every Tasks row has four cells and every Microsteps row has seven, exactly
as shown.
The tables are DIFFERENT: Tasks has only Order/Task/Status/Details. Never copy
Microsteps' Feature/Stage/Action/Evidence fields into a Tasks row. Locate the
table by its heading before editing: a prefix such as `3 / Write code` can
appear in both tables, so that prefix alone cannot identify the outer row.
Close an outer row by editing ONLY the section between `## Tasks` and
`## Microsteps`, never by replacing matching prefixes across the whole file.
A full-file `startswith` update can corrupt the first feature's 3.1 row even
when the new outer row itself has the right width. With `plan_text` read from
the retained path and `old_row`/`new_row` containing the full four-cell outer
row, this bounded replacement leaves all microsteps untouched:

```python
before_tasks, remainder = plan_text.split("## Tasks\n", 1)
tasks_text, after_tasks = remainder.split("## Microsteps\n", 1)
assert tasks_text.count(old_row) == 1
updated_tasks = tasks_text.replace(old_row, new_row, 1)
plan_text = before_tasks + "## Tasks\n" + updated_tasks + "## Microsteps\n" + after_tasks
```

For microsteps, restrict edits to their table and match Step/Feature/Stage,
not a bare number or phase. Validate the candidate before writing: all Tasks
rows still have four cells and all Microsteps rows seven. A loop whose body
merely says `pass`, or a printout without checking widths, is not validation.
 Do not add an extra empty cell after the final Evidence cell.
Keep later notes, exact sentences, commit subjects and deferred commands INSIDE
the existing Action/Evidence cells or in the ledger below, never in an eighth
cell appended to a row. Before saving, count each row against the header. Use
semicolons within Evidence; escape any literal table pipe as `\|`.
Tasks has exactly those four unique names/numbers in that order. Statuses in
both tables are only `pending`, `in_progress`, `complete`, `skipped`; skip
optional stages immediately when inapplicable. Keep deliverables in Details,
feature boundaries/counts in the ledger.

Populate Microsteps with real actions before implementation. Step is a unique
positive integer in execution order; Phase is an outer task name. Each code
feature has a stable descriptive Feature identifier and three consecutive rows
with Stage exactly `3.1`, `3.2`, `3.3`. Action names its actual files/checks and
expected public result. Other phases use `-` for Feature/Stage. Investigations,
repairs, verification and delivery stay within their owning row, never another
outer stage. Keep future cycles visible. Selected commits' ledger follows this
table and records real introducing hashes, never guessed counts.

## Repeat for the first unfinished feature only

**Close each checkpoint in the actual file.** After 3.1 and after 3.2, set
that exact row's Status to complete and Evidence to the observed result, then
read both cells back. Identify the row by its unique Step, Feature and Stage;
changing Evidence alone does not close it. After 3.3, read all three current
rows: each must say complete with its baseline, passing checks or real
commit/delivery evidence. A committed feature with stale 3.1/3.2 cells is still
unfinished workflow; repair those cells BEFORE starting another feature.

Announce its behavior, planned conventional commit subject and deferred work.
Mark outer Write code in_progress; only the current microstep is in_progress.

**3.1 Write tests.** Save this feature's runnable public checks before its
application edit, preserving earlier checks and deferring later capabilities.
Run them now and record the actual baseline. Missing behavior should fail for
its intended reason; creation may fail to import an absent entrypoint. Existing
passing checks may protect a pure refactor. Separate dependency failures.
Apply selected test/function/logging rules from the first saved draft.

When testing is selected, finish its two source gates before closing 3.1.
Do Gate B FIRST: edit the actual retained rejection bodies before adding new
query tests. Then save Gate A cases for this feature.
**A:** each operation introduced/changed now has saved success and every
applicable rejection class, including its own documented operand shapes.
**B:** if adding a read, EVERY applicable retained current-module rejection
block is updated in place with immediate independently expected read-only
observations BEFORE any recovery mutation.
This includes the FIRST read: put its not-yet-implemented calls in the old blocks
now and expect missing-read baseline failures. Map values and history separately;
use an available total for values even without individual getters, and assert
required history too. First-read status never exempts older current-module tests. Include older classes/shared loops
and new query rejections; a later read-aware class alone does not repair them.
Keep informative earlier views and add the new read. Historical-source loaders
and true empty-domain reads retain testing's narrow exceptions.
Read the actual saved source and record each operation's cases plus every old
block's file/test location, fixture, rejected inputs and first public assertion
in the inventory and this 3.1 Evidence. Run that upgraded cumulative suite
before query code; missing-query failures are valid baseline evidence.
A prose completion claim or green success-only suite cannot close either gate.
At 3.3 read all current checks again and verify both gates against actual owners
and blocks before staging; new read assertions belong in those old blocks.

Static content and project test prohibitions use recorded direct verification;
name the exact exception, check and baseline without claiming a test was saved.
Finish this 3.1 row before starting 3.2. Never write all features' tests first.

**3.2 Write code.** Implement only this feature and necessary integration.
Apply selected commenting, logging, SRP and debug rules. Run its saved checks and
relevant retained checks with fresh state. Resolve failures; inspect code and
diff against current/pending features. Record actual passing commands/results
before 3.3. Checks saved only after code do not satisfy 3.1.

**3.3 Commit.** Review only this feature's working code/checks before staging.
When commenting/logging is selected, enumerate every changed application and
test function and inspect its actual body: complete docstring labels, first
named-parameter print, and every normal return/fallthrough print as applicable.
After adding test assertions or query observations, the selected None exit print
must remain AFTER the final assertion; an earlier print no longer covers the
fallthrough. Finish this source review before staging; green tests do not prove
these separately selected function contracts.
Run `git commit` as its own command with a conventional subject in
`type: summary` or `type(scope): summary` form, even when commits is unselected.
A plain `Add ...` or `Fix ...` subject does not close this workflow stage.
Verify HEAD advanced and
inspect the committed tree; record the real hash in this row and selected ledger.
When worktree is selected, finish its live-default merge, consumer reapplication
and verification before closing 3.3. Never push unless asked.

If no Git repository exists or the user forbids committing, record the specific
limit and skip only 3.3; finish permitted tests/code. Repair a completed feature
with a focused working commit before the next feature. Only after this cycle
closes may the next feature's 3.1 start. No final batch or cosmetic empty commits.

## Update, recover and close the plan

At every transition update the SAME absolute plan path, record evidence and
read it back. Rewrite affected rows in place; never append duplicate tables.
If using text replacement, verify each replacement matches exactly one current row
before writing; a zero-match replacement is a failed update, even with exit 0.
Preserve completed evidence, pending features and original sentence boundaries.
Escape literal table pipes as `\|`. Recover damage in a separate checked
candidate before replacing the plan; never truncate it with a failing command.

A failed plan edit is unfinished work. Read the actual file and correct its
current rows; do not retry guessed old text or hand off. Optional cache cleanup
cannot gate a plan update or required commit: if rejected, leave generated
output untracked and finish the authorized work.

After the last feature's verified 3.3, reconcile ledger/commits/delivery and mark
the EXISTING Tasks row 3 (Write code) COMPLETE in place. Do not append a
Write code closure microstep with Feature/Stage `-`: code microsteps are only
the feature's 3.1/3.2/3.3 rows. Record wrap-up evidence in the existing outer
row and final feature's 3.3 row. Read back both tables: complete microsteps do not
close the outer row automatically. Only then start docs, or hand off if skipped.
Selected docs owns the README; feature-local notes and function docstrings
belong with their feature. Deliver docs through the same task checkout too.

After delivering documentation, close its Microsteps and existing Tasks row 4
in the same file; a README commit does not close an in_progress documentation
row. Read those changed Status and Evidence cells before handoff.

Before handoff, read the authoritative plan again: four outer rows in order;
applicable tasks/microsteps complete or justified skipped; every feature has its
ordered cycle and actual evidence/hash; no pending ledger hash, stale Details
or future-tense completion claim. Verify delivered live files/consumers when
worktree is selected. Report actual checks and concrete limits honestly.

## Every implementation follow-up needs a fresh plan

Each later user message requiring implementation starts a fresh plan BEFORE its
feature checks/application edits, including small follow-ups after completion.
Verify/reuse the task checkout and branch when they fit; no new checkout is
required merely because a message arrived. Keep the SAME authoritative plan path.

After completion, archive the old plan in an ignored file beside it, then write
and read back the new goal, ledger and pending cycles. Mark startup complete
only after verifying reuse; reset code and applicable docs to pending. Never
leave the display on completed old work or a prior feature.

During unfinished work, revise/read back the current plan while preserving
completed evidence, unfinished queue and original capability boundaries. Add
new cycles; finish the active cycle before another. Documentation follows all
applicable cycles. A status/explanation requiring no implementation needs no
new plan.

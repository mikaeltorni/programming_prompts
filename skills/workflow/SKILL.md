---
name: workflow
description: >-
  v0.2.8 — Resume one saved plan, batch related audit findings, and finish each
  requested feature through checks, implementation and local delivery.
---

# Programming workflow

Run only when explicitly invoked or selected. Selection authorizes local commits
and selected worktree delivery. User constraints override this workflow: a
no-test instruction skips tests and model evaluations, with an honest unverified
handoff. Never push unless requested. Use only selected, available companions.

## Retain one plan and checkout

At the start of every turn, read the authoritative plan, including questions,
status replies, automatic continuations and context recovery. Resume its first
unfinished action in the same checkout; preserve completed evidence and hashes.
A status question alone adds no implementation authorization; it also does not
cancel an already active goal. Finishing a response does not finish the task.

Read the launch directory and `ACC_WORKFLOW_FILE` before routing to another
repository. Retain the physical launch-project root separately from each
implementation repository's LIVE checkout and task worktree. Resolve a linked
launch checkout to its original live root. Use `ACC_WORKFLOW_FILE` when it is an
absolute Markdown path inside that launch project's `tmp/workflow/`; otherwise
use `<launch-project>/tmp/workflow.md`. Keep that exact path throughout routing.
Leave it untracked unless asked to track it. Record hashes after committing;
never amend a commit to include its own hash.

Establish selected worktree isolation before detailed investigation. Save the
plan before feature checks or implementation. Reuse it on continuation. Update
it for new implementation requests, preserving unfinished work; archive it beside
the same path only when a distinct task starts after completion.

## Plan the requested outcome

Keep four outer stages: **Establish worktree → Plan → Write code → Write
documentation**. Selected commits owns feature boundaries: one original user
capability sentence per Feature, keeping its clauses together. Execution rules
and discoveries inside an audit are not new capabilities.

For an audit or "check everything" request, first identify a finite inventory
of the relevant files, handlers or public forms and the evidence needed to
review them. Track reviewed and remaining items once in the plan. Read related
sources together, collect findings, then repair them as a coherent batch within
the current Feature. Do not start a fresh tests/commit/merge/reload cycle for
every finding. Use a smaller checkpoint only for an actual dependency, risk or
user-requested delivery. Do not reopen reviewed items without a changed dependency,
failed check or new evidence. Finish the whole inventory and requested result;
batching is not permission to omit cases or narrow the user's scope.

Use this ACC schema:

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
| 2 | Plan | complete | Features, affected files and completion evidence. |
| 3 | Write code | pending | Complete requested feature cycles. |
| 4 | Write documentation | pending | Selected docs, otherwise skipped. |

## Microsteps
| Step | Phase | Feature | Stage | Action | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
```

Tasks has exactly those four rows and columns. Microsteps has those seven columns,
unique positive Step numbers, and `pending`, `in_progress`, `complete` or `skipped`
statuses. Keep at most one microstep in_progress. Each Feature has consecutive
Stage `3.1`, `3.2`, `3.3` rows; other phases use `-` for Feature/Stage. Name actual
files/checks in Action and observed results in Evidence. Escape literal pipes.

## Complete each feature

- **3.1 Checks:** inspect existing coverage and save/run the current Feature's
  missing public checks before application edits. Record the actual baseline;
  a correct-path missing entrypoint/import is valid for creation. Existing
  checks may protect a refactor. Static content and project test prohibitions
  use direct review. Explicit no-test instructions skip execution. Record the
  exception rather than inventing a passing result.
- **3.2 Code:** implement this Feature and necessary integrations, including its
  collected audit findings. Use focused checks while editing; run the cumulative
  relevant checks once the batch is ready. Repair failures, then inspect the
  actual diff. Do not repeat a passing suite on an unchanged candidate. Later
  requested capabilities remain deferred to their own cycles.
- **3.3 Commit:** stage this Feature's code and checks, excluding the plan, and
  create a conventional commit. Confirm HEAD advanced and record its actual hash.
  Complete selected worktree delivery before the next Feature. No Git or a user
  no-commit instruction skips this step with its reason. Related findings need
  no extra commit boundary; a later discovered defect may justify a repair commit.

Update the responsible row at meaningful stage transitions and read back the
changed cells. Keep investigations, findings and command results inside that
row's evidence or inventory; do not append another triplet for each discovery,
command or goal continuation. Read only the active rows and relevant inventory
when updating a large plan; avoid repeatedly dumping its full history.

## Documentation and handoff

Plan two documentation microsteps from the start: **Write and verify
documentation** names the root README and public interface; **Commit
documentation** records its hash and selected delivery. Use `-` for Feature/Stage.
Keep the commit row pending while writing. If docs is unselected skip both rows;
no Git or a user no-commit instruction skips only its commit with the reason.

After all requested Feature cycles finish, mark Write code complete, then update
the README if needed. Existing accurate documentation needs no cosmetic edit or
empty commit. Record that inspection and skip a needless docs commit. Before
handoff reconcile the original request, inventory, delivered files, actual hashes
and all applicable rows. State verification limits. Complete the task when this
evidence proves the requested result; do not manufacture new work to keep auditing.

---
name: workflow
description: >-
  v0.2.43 — Plan and investigate each repository before execution; retain scoped
  tasks and finish requested features through local delivery.
---

# Programming workflow

This policy is active when supplied as a selected skill or invoked explicitly.
The workflow file is a required deliverable even if the requested response
is a single sentence. User constraints override this policy. Use selected
companions only, honor no-test requests, and push only if asked.

## Start with the assigned workflow file

Use a file tool first. Read `ACC_WORKFLOW_FILE` from disk and check the plan
before composing a response. In a shell, run `cat -- "$ACC_WORKFLOW_FILE"`.
If the file is empty and the user refers to earlier work, find and read the
archive before asking for any missing context. In a shell, list it with
`ls -t -- "${ACC_WORKFLOW_FILE%.md}".*.previous.md` and read the relevant result.

- **Active follow-up.** When the message is delivered during an ongoing turn,
  immediately edit the same file. Append a short description of the message
  to the active action's Evidence cell. Use a relevant action if none is
  active. Extend the queue for changed requirements. Keep earlier work and
  the current checkout. A question during work still requires this edit
  before you answer. The latest sibling `.request.json` can confirm steering
  when its `steering` field is true.
- **New prompt from idle.** ACC opens an empty file and archives the previous
  plan beside it as `*.previous.md`. Write a fresh plan at the assigned path,
  including for a question or an explicit resume. For a brief question, one
  Plan action is enough and phases that do not apply can be skipped. Carry
  forward unfinished actions and evidence when the request is to resume.
- **Automatic continuation, recovery or approval reply.** Read the retained
  plan and continue its first unfinished action in the same checkout. When a
  retained-plan question asks only for status, read it and answer that question.

Use a file tool to save and read back the required edit before the final
answer. An answer-only request still uses the tracker file. Follow an explicit
instruction to leave that file unchanged.

Keep the absolute Markdown path throughout the session, including when routing
work to another repository. ACC stores it in external tracker state. Read the
launch directory, resolve a linked checkout to its original live root, and
track each implementation repository's live checkout and task worktree.

Establish selected worktree isolation before detailed investigation. Save the
plan before checks or edits. Use the actual plan to answer questions about it.
A question adds no implementation authorization.

Without an ACC assignment, use `workflow.md` in a private directory created
with `mktemp -d /tmp/acc-workflow.XXXXXXXX` for a new task and retain it for
continuations. Create the parent directory if needed and keep plans and archives
outside source checkouts. Record hashes after committing and keep them out of
the commits they identify.

## Plan the requested outcome

Keep four outer stages: **Establish worktree → Plan → Write code → Write
documentation**. Selected commits owns feature boundaries: one original user
capability sentence per Feature, keeping its clauses together. Execution rules
and discoveries inside an audit are not new capabilities.

### Schedule pre-existing policy gaps as Write code tasks

When inspection finds an independently fixable gap in an active policy within
the task's scope, add a named **Write code** maintenance task immediately. For
example, record missing function comments or console diagnostics in existing
code. Put it ahead of the affected Feature's pending implementation and
complete it at the earliest safe point, normally before the Feature's checks
and edits. If discovered during implementation, preserve in-progress changes
and separate the maintenance before committing the Feature.

Give each coherent maintenance task its own 3.1/3.2/3.3 rows with a unique
maintenance key and the affected files. Record the direct review or applicable
local checks, then record the maintenance commit hash in 3.3. Keep each
maintenance task in its own commit, including when the changes share a file
with the Feature. Related gaps may be handled in one maintenance task. Keep
policy compliance for newly authored code and updates required by the new
behavior in the Feature's own commit. Limit inspection and maintenance to the
authorized scope.

For comment-only or diagnostic-only maintenance that preserves application
behavior, review the diff directly. Run project-required checks when allowed.
Commit and record the hash promptly. With worktree selected, commit in the
task worktree, mark 3.3 complete for the commit and record the worktree
delivery checkpoint. Continue the queue. If delivery is still deferred at
handoff, report the retained branch, hash and delivery checkpoint.

### Plan, investigate, then execute per repository

Before detailed investigation, save an initial plan from the request and current
file inventory: repository owners, requested outcomes, candidate paths, review
order and evidence needed for completion. Unknowns become explicit investigation
actions. Do not mark Plan complete with only a generic "inspect everything" row.

For work spanning repositories, keep an ordered repository queue in this same
plan. Give each repository its own scoped tasks, retained LIVE/worktree/branch,
review inventory, checks or exceptions, delivery and documentation status. Use a
`repository/feature` key for its 3.1/3.2/3.3 slice, using the actual repository
name and retaining the original capability sentence; routing does not invent
new user capabilities. In each 3.2 Action, name the files or components the
feature will edit. Keep those targets in the Action after completion and update
them if the delivered scope differs. Qualify documentation Actions with the
repository and affected document paths when the plan spans repositories.
Never put the entire repository queue inside one active code/checks row. A task
explicitly limited to one repository stays there; record an outside dependency
without expanding the requested scope.

For each repository, plan its bounded work, investigate its actual files and
callers, then update the plan with findings and concrete execution actions
before editing. End investigation when the named inventory has evidence and
findings are classified as repair, retain with reason, or unresolved with the
specific missing evidence. A no-change review can finish with evidence and
skipped code/commit actions. Finish that repository's planned batch, permitted
checks, due local delivery and affected README review before moving to the next.
Record maintenance delivery deferred under the worktree policy. Otherwise,
only an actual cross-repository dependency justifies leaving a slice pending;
record the dependency and return point. Final documentation commits still follow
the selected docs policy.

Apply the same sequence to single-repository cleanup: inventory the current
files and public forms, plan the review, investigate, then save the proposed
repair batch and completion evidence before implementation. For a large audit,
partition the inventory into named subsystems with review checkpoints in advance.
Batch related findings; do not create a delivery cycle per omission. Independent
subsystems may have separate delivery checkpoints within the original Feature.

After at most 15 minutes of active investigation or implementation without a
completed planned action, checkpoint: record evidence, remaining paths and the
next concrete action; split an oversized action along repository or subsystem
boundaries before continuing. Record a live long-running command separately;
waiting is not implementation progress. Elapsed time triggers replanning, not
abandoning scope or claiming success. Reflect actual completed checks, code and
delivery in their rows promptly, even while the broader audit remains open.

Track reviewed and remaining inventory once. Reopen reviewed items only for a
changed dependency, failed check or new evidence. Finish the full requested
queue; bounded batches must not silently discard unresolved or remaining work.

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
Stage `3.1`, `3.2`, `3.3` rows, as does each scheduled maintenance task. Other
phases use `-` for Feature/Stage. Name actual files/checks in Action and
observed results in Evidence. Keep each table row on one physical line and
escape literal pipes.

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
  Complete any due worktree delivery before the next Feature. No Git or a user
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

---
name: workflow
description: >-
  v1.2.1 — Plan programming work, then repeat tests → code → commit for each
  planned feature before writing documentation. Activated by explicit selection.
---

# Programming workflow

Run when `$workflow` is invoked or workflow is selected in native global
instructions. Merely appearing in an installed catalog does not activate it.

Keep these four outer stages in order:

1. **Establish worktree.** Read project guidance, resolve the physical launch
   repository, and retain `ACC_WORKFLOW_FILE`. When worktree isolation is
   selected, establish or verify the task checkout now, before detailed
   investigation or planning. Follow explicit live-checkout and read-only
   exceptions. Use the same task checkout throughout.
2. **Plan.** Define concrete features, their public behavior, files and checks.
   Each feature must have its own ordered **3.1 Write tests → 3.2 Write code →
   3.3 Commit** cycle. When commits is selected, copy its original capability
   sentences into a ledger and preserve those boundaries; do not combine
   separate features for convenience.
3. **Write code.** Finish one feature's complete cycle before starting the next.
4. **Write documentation.** After all feature cycles finish, document the
   delivered interface in the project-root README when docs is selected.
   Commit and deliver documentation through the same task checkout.

## Implementation follow-ups

Every later user message that requires implementation needs a fresh plan for
that request before its feature checks or application edits. This includes
small follow-ups and requests received after an earlier task is complete.
Verify and reuse the current task worktree and branch when they still fit;
a new message does not require another checkout.

Use the same authoritative plan path. After a completed task, preserve its
plan in an ignored archive beside that file, then write and read back a new
plan with the new goal, feature ledger and pending cycles. Mark worktree
startup complete after verifying the reused checkout; reset code and applicable
documentation to pending. An old completed plan must not describe new work as
complete or leave the display on a previous feature.

When earlier work is unfinished, revise and read back the current plan for the
new request while preserving completed evidence, unfinished features and their
original sentence boundaries. Add the new feature cycles without discarding
the existing queue. Finish the active feature's 3.1 → 3.2 → 3.3 cycle before
starting another. Each new feature repeats that same cycle; documentation
follows all applicable cycles. A status update or an explanation that needs no
implementation does not start a new plan.

## Selected companions

Inventory only policies selected by the user or supplied as active instructions.
Use their detailed rules in their owning stages: worktree at startup and
closeout; testing, commenting, logging, SRP and debug during feature cycles;
commits at feature closeout; docs afterward. Mark unavailable companions skipped
and inapplicable ones not applicable. Do not install missing skills or invent
unselected conventions. With no companions, the tests → code → commit cycle
still applies; workflow itself requires that order, not their extra conventions.

## One authoritative plan

Retain the physical launch-project root before entering a task checkout. Read
`ACC_WORKFLOW_FILE` from the shell: use its exact absolute Markdown path only
when it is inside the launch project's `tmp/workflow/` directory. Otherwise use
`<launch-project-root>/tmp/workflow.md`. Never put the plan in a linked worktree,
skill directory, agent home, or system `/tmp/`. Create its parent directory.
Keep this same absolute path throughout; do not commit the plan unless asked.

Write and read back the plan before tests or implementation. Keep this structure:

```markdown
# Workflow

## Goal
The requested outcome and delivered public interface.

## Enabled skills
Selected companions, or none.

## Tasks
| Order | Task | Status | Details |
| --- | --- | --- | --- |
| 1 | Establish worktree | complete | Verified task checkout; skipped when isolation does not apply. |
| 2 | Plan | complete | Concrete features and their ordered cycles recorded. |
| 3 | Write code | pending | Finish each feature through tests, implementation and commit. |
| 4 | Write documentation | pending | Document the delivered interface; skipped when docs is not selected. |

## Microsteps
| Step | Phase | Feature | Stage | Action | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
```

The Tasks table has exactly those four rows, names and numbers in that order.
Statuses in both tables are exactly `pending`, `in_progress`, `complete`, or
`skipped`. Describe deliverables in Details; keep feature counts in the ledger.
Mark optional outer stages skipped immediately when they do not apply.

Populate Microsteps with real actions before implementation. Step is a unique
positive integer in execution order. Phase is an outer task name. For every
feature under Write code, Feature is a stable descriptive identifier shared by
its three rows, Stage is exactly `3.1`, `3.2`, then `3.3`, and Action names the
checks/files and expected observable result for that row. Other phases use
`-` for Feature and Stage. Add investigations, checks, repairs and delivery
within their responsible row; do not introduce another outer phase. Keep
future feature cycles visible. A selected commits ledger follows Microsteps
in this same plan and records actual introducing hashes, never guessed counts.

## Repeat for each planned feature

Work only on the first unfinished feature. Announce its behavior, planned commit
subject and deferred work. Advance these substeps in order:

### 3.1 Write tests

Save runnable public-interface checks for **this feature only**, before changing
its application implementation. Include independently expected successes,
boundaries, relevant rejection and unchanged-state observations. Preserve
checks for earlier features; do not implement or test later capabilities yet.
Apply selected commenting and logging contracts to tests from their first draft.

Run the new checks against the current implementation and record the observed
result. New behavior should fail for the intended missing behavior; a missing
entrypoint in a creation task may fail to import. Identify unrelated dependency
failures. Existing passing checks may suffice for a pure refactor; record their
actual coverage and baseline. Static content and project prohibitions on new
test suites use the project's direct validation mechanism instead; record the
specific exception and check, without pretending a test was written.

Complete the 3.1 row with its saved checks, runner and baseline evidence before
starting 3.2. Do not write all features' tests first and then all their code.

### 3.2 Write code

Implement only this feature and its necessary integration. Apply selected
function, parsing, operation, logging and repair contracts now. Run the feature's
saved checks and the cumulative relevant earlier checks using fresh state.
Resolve failures and inspect the diff against the current feature and all
pending features. Code for a later feature must remain deferred.

Complete 3.2 with the actual passing command/results before starting 3.3.
Tests written after implementation do not satisfy 3.1, even when they pass.

### 3.3 Commit

Review and stage only this feature's implementation and applicable checks.
Create its working conventional commit, with tests and code together. Run the
commit as its own command. Verify HEAD advanced and inspect the committed tree;
a subject or plan claim alone does not prove a commit happened. Record the real
hash in both this row and the selected ledger before advancing.

When worktree delivery is selected, merge into the live default branch and
reapply/verify its consumer before completing 3.3. Never push unless requested.
If there is no Git repository, record the concrete limitation and mark only
3.3 skipped; finish the permitted tests and code. Explicit user constraints
on committing override this default and must be recorded. Commit a focused
repair before the next feature when a completed feature has a defect.

Only after 3.3 completes may the next feature start its 3.1. Do not batch
features into a final commit or use empty/cosmetic commits to simulate cycles.

## Update progress and finish

Mark the outer Write code row in_progress when its first cycle starts. Keep
only the current microstep in_progress. At every transition update this same
plan, record concrete evidence, and read it back. Rewrite an affected table
in place; never append duplicate rows or tables. Preserve completed actions,
future cycles and original feature boundaries through discovery and recovery.
Escape literal table pipes as `\|`. Recover a damaged plan into a separate
candidate, verify its tables, then replace it; never truncate the authoritative
plan with a command that may fail.

After every feature's 3.3 is complete (or specifically justified skipped),
reconcile actual commits, ledger and delivery, then mark Write code complete.
Only then start documentation. Selected docs owns the README; function
docstrings and required feature-local documentation belong in their code commit.
Documentation commits also get selected worktree delivery and reapplication.

At handoff reread the original plan: exactly four unique outer rows in order;
all applicable phases and microsteps complete or justified skipped; each
feature has its ordered 3.1/3.2/3.3 cycle with real evidence; no pending ledger
hash; no stale Details or future-tense completion claims. The delivered live
checkout and consumers must contain the work when worktree is selected.
Report actual checks and any concrete limits. No separate testing, verification
or delivery outer stage is added: tests and checks are inside each feature cycle.

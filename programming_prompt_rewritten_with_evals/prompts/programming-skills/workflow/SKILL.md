---
name: workflow
description: >-
  v1.2.26 — Establish the task checkout and authoritative plan, then finish
  each feature's tests → code → commit cycle before documentation.
---

# Programming workflow

Run only when explicitly invoked or selected. Selection authorizes required
local commits and selected worktree merges; user prohibitions override them.
Never push unless asked. Use only selected, available companions.

Keep four outer stages: **Establish worktree → Plan → Write code → Write
documentation**. Verify selected isolation before detailed planning. Retain
three absolute values: physical LIVE launch root, task checkout and plan path.
Use `ACC_WORKFLOW_FILE` only when it is an absolute Markdown path inside
LIVE's `tmp/workflow/`; otherwise use `LIVE/tmp/workflow.md`. Keep that same
plan outside the task checkout and uncommitted unless asked otherwise.

Read the entire request and save the plan before Feature checks. With commits
selected, its capability-sentence boundaries define the ordered Feature queue;
keep pending Features visible. Plan concrete files, behavior and verification.
Use this schema for Agent Command Center:

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
| 2 | Plan | complete | Concrete features and cycles recorded. |
| 3 | Write code | pending | Finish each feature cycle. |
| 4 | Write documentation | pending | Selected docs, otherwise skipped. |

## Microsteps
| Step | Phase | Feature | Stage | Action | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
```

Tasks has exactly those four rows and four columns. Microsteps has seven
columns; add unique positive Step numbers in execution order. Phase names an
outer task. Each code Feature has a stable identifier and consecutive Stage
`3.1`, `3.2`, `3.3` rows; other phases use `-` for Feature/Stage. Action names
actual files/checks; Evidence records observed results. Status is `pending`,
`in_progress`, `complete` or `skipped`. Escape literal pipes within cells.

At each transition, read this saved plan and do its first unfinished microstep:

- **3.1 Checks:** save/run this Feature's public checks before application edits.
  Record the actual baseline; an absent-entrypoint import failure is valid for
  creation, and existing passing checks can protect a refactor. Apply selected
  testing coverage. Static content/project test prohibitions use direct checks.
- **3.2 Code:** implement only this Feature, rerun current and retained checks,
  resolve failures and review source. Record the passing result.
- **3.3 Commit:** commit working code/checks together with a conventional
  `type: summary` or `type(scope): summary`, record the actual hash, then finish
  selected worktree merge and consumer verification before the next Feature.
  No Git or explicit no-commit instructions justify skipping only this step.

Update the existing rows in place as each step closes; mark outer Write code
complete only after every cycle is delivered. Documentation follows all cycles,
uses the same task checkout and delivery path, and closes outer row 4. Unselected
docs are skipped. Before handoff, verify actual statuses, hashes and delivered
files; finish the remaining queue rather than stopping after a passing Feature.

An implementation follow-up needs an updated plan before checks/edits. Reuse
verified checkout and plan path. After completion, archive the old plan beside
it and start fresh; during unfinished work preserve completed evidence and the
queue, finishing the active cycle first. Status/explanation-only messages need
no new plan.

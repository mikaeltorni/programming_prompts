---
name: worktree
description: >-
  v1.0.13 — Edit Git projects in a sibling .worktrees project/task checkout,
  commit there, merge each Feature into the live default branch, and reapply
  its consumers. Never push unless requested.
---

# Git worktree isolation and delivery

Resolve the LIVE repository physically BEFORE deriving the store: its immediate
PARENT owns `.worktrees/`, never the live repository itself. For live root
`/Projects/app`, the store is `/Projects/.worktrees/app/`, NOT
`/Projects/app/.worktrees/`. This illustrates the parent rule, not a fixed path.
Derive the actual task path and matching branch from your actual LIVE/PARENT/
PROJECT/TYPE/FEATURE values. Before every edit/commit, compare registration,
physical checkout path and branch with those originally derived values; merely
being in some `.worktrees` directory is insufficient.

When isolation applies, use one linked worktree and one matching branch per
project for every Feature, repair, and documentation commit. Do not create a
new worktree or branch for each capability sentence.

## Establish the task checkout

Read the project's `AGENTS.md` and `CLAUDE.md` first, resolve the physical
launch repository and retain its absolute workflow path, then establish the
task checkout immediately before detailed planning or investigation. Do not
wait until code changes are ready. Minimal read-only discovery needed to
identify the repository and task slug may precede isolation; the first
repository mutation is
`git worktree add`. Use the existing repository and history, not `git
init` or a history rewrite. Explain the limitation if there is no Git
repository. An explicit request to edit the current checkout overrides
isolation. A read-only task does not need a new editing checkout. If the user
or launcher explicitly assigns an existing task worktree, verify its registered
path and branch and continue there immediately instead of creating another.
When workflow is selected, complete this startup step before writing its
detailed plan; the launch-project plan path remains unchanged.

Resolve the **physical live checkout** first. Start with that repository's
`git rev-parse --show-toplevel`, then resolve its symlinks with `pwd -P` from
that directory. Do not use the shell's launch directory or a guessed root.
If already in a linked worktree, recover the live checkout from
`git worktree list --porcelain` and the common Git directory before deriving
any paths. Let `PROJECT` be that live checkout's basename, never an
agent, model, account, or linked-worktree name. Use the external sibling
layout:

```text
<project-parent>/.worktrees/<project>/<project>_<type>-<feature>
branch: <type>/<project>_<feature>
```

`TYPE` is a conventional commit type, and `FEATURE` is one descriptive
task slug. Use the **same bytes** for PROJECT, TYPE, and FEATURE in both
names. Pick FEATURE once and use its literal value in the branch as well as
the directory: a leaf ending `_feat-converter` requires branch
`feat/app_converter` for project `app`; `feat/app_temperature-converter`
does not match. The leaf separator after TYPE is `-`, while the branch uses
`/` before PROJECT and `_` before FEATURE. Construct both names from the
same variables below; do not hand-type a different leaf or branch later.
Verify both expanded strings before `git worktree add`. For `/home/mk/projects/widget`, `TYPE=fix` and `FEATURE=parser`
produce `/home/mk/projects/.worktrees/widget/widget_fix-parser` and
`fix/widget_parser`. The store must be directly under the physical live
checkout's parent, outside the live repository. Being outside the repository alone is not enough:
the filesystem root or another ancestor is the wrong parent. Resolve the store
physically before creating it; a symlink must not redirect it inside the
repository or under a different parent. On collision, add a unique suffix
to FEATURE and recompute both names; never reuse or delete another
task's checkout or branch.

```bash
# Run from the physical live checkout resolved above, not a linked worktree.
REPO="$(git rev-parse --show-toplevel)"
REPO="$(cd "$REPO" && pwd -P)"
TYPE="fix"
FEATURE="parser"
PARENT="$(dirname "$REPO")"
PROJECT="$(basename "$REPO")"
STORE="$PARENT/.worktrees/$PROJECT"
WT="$STORE/${PROJECT}_${TYPE}-${FEATURE}"
BRANCH="$TYPE/${PROJECT}_${FEATURE}"
printf '%s\n' "$REPO" "$PARENT" "$WT" "$BRANCH"
# Compare these derived paths and resolve any existing store symlinks first.
git -C "$REPO" worktree add -b "$BRANCH" "$WT"
cd "$WT"
pwd -P
git branch --show-current
```

Before the first source write, verify the registered checkout against the full
expanded `WT`, not just whether it is outside the live repository. The project
component is a directory under `.worktrees/`, followed by the task leaf; a
sibling checkout beside the live repository or a task leaf directly under
`.worktrees/` does not satisfy that layout. Verify registration, physical path
and matching branch together before advancing to implementation.

Compare the printed physical path and branch with `WT` and `BRANCH`
before editing. Keep that same checkout and branch for every Feature,
repair, and documentation commit; a new `docs/...` branch would break
the directory-to-branch identity. Before **every edit and commit**,
verify `pwd -P` is inside the external project group and the current
branch is the task branch. Compare the registered physical path with the
`WT` derived from the retained live `REPO` and its immediate `PARENT`; printing
an arbitrary path and matching branch is not sufficient. Do not recompute the
expected store from the current worktree or silently accept its existing
location. Use the full worktree path for edits,
README files, and scratch output. A shell `cd` does not persist into
later tool calls. Check status afterward and inspect the project group
for misplaced files; recover only this task's files without overwriting
user work in the live checkout. For multiple repositories, establish
this layout separately from each live project.

The external `<project-parent>/.worktrees/<project>/` group holds registered
worktrees only. Put scratch files and recovered drafts inside this task's
checkout under `tmp/`, never in a second unregistered directory or loose file
beside it. If a write accidentally landed in the live checkout, compare it with
the task copy and move only this task's draft into the task checkout (or its
`tmp/` recovery directory), then commit and merge the intended deliverable.
Before delivery, inspect the project group for this task's stray recovery files;
preserve other tasks and user work.

## Deliver each completed Feature

The commits skill owns Feature boundaries. For each completed Feature
or focused repair:

1. After the current feature's tests-before-code cycle passes, commit its tests
   and implementation together in the task worktree. Confirm its `HEAD` advanced
   and the worktree is clean.
2. Confirm the live checkout is on its actual default branch from
   repository metadata or project instructions; preserve unrelated
   live changes. Merge with `git merge --no-ff "$BRANCH"`. Resolve
   conflicts without discarding user work.
3. Confirm the task `HEAD` is an ancestor of live `HEAD` with
   `git merge-base --is-ancestor`, then inspect live status.
4. Reapply through the project's installer, skill selector, or narrow
   reload and verify the consumer and relevant logs. For static
   content without an installed consumer, verify the merged file.
   Follow Linux desktop rules when applicable.

Return to this same worktree for the next Feature. Every later commit,
including a docs-only correction, gets its own merge and reapplication.
Include README and other documentation edits in this same worktree's
commits and merges. Inspect both checkouts for uncommitted source or
documentation; a working live-only README does not complete delivery.
Create documentation in the task worktree from the start. If a README was
accidentally drafted as an untracked file in the live checkout, move that
content into the task worktree and remove only that misplaced draft before
merging. Do not commit the live copy merely to clear a merge obstruction:
the README's introducing commit must originate on the task branch.

Before handoff, compare the task's registered physical location with the
original live-derived `WT` again, even if every commit and merge succeeded.
If this task's checkout was created under the wrong parent, stop editing and
correct its registration and location with `git worktree move` to the unused,
correctly derived destination before continuing; preserve its branch, commits
and files. A merge does not make an invalid location compliant. Inspect both
checkouts for remaining deliverables and finish their commits and merges.

Report completion only when the live default branch contains the work
and consumers are current. Never push, publish, add remotes, or rewrite
history without an explicit request.

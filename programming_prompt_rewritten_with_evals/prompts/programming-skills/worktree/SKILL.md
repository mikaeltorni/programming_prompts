---
name: worktree
description: >-
  v1.0.0 — Use before editing a git repository: isolate work in a sibling
  .worktrees project group with a project/task directory, commit there,
  merge into the live default branch, and reapply consumers. Applies to
  coding, documentation, and follow-up edits. Never push unless requested.
---

# Git worktree isolation

## Establish the project before editing

Read the project's AGENTS.md and CLAUDE.md first. Read-only inspection may
precede isolation; the first repository mutation is `git worktree add`.
Use the existing repository and history; do not initialize it again or rewrite
history. If there is no git repository, explain the limitation before editing.
An explicit user instruction to work in the current checkout overrides isolation.
Claude's EnterWorktree / ExitWorktree is not a substitute for this layout.

## Project and feature layout

Use `<project-parent>/.worktrees/<project>/<project>_<type>-<feature>`.
`<project>` is the physical live checkout's basename. Resolve symlinks first:
for example, `/app` pointing at `/Projects/app` means the store is
`/Projects/.worktrees/app/`, never `/.worktrees/` or `/app/.worktrees/`.
When already inside a linked worktree, recover the live checkout from
`git worktree list --porcelain` and the common Git directory; do not treat the
worktree directory as a new project or nest another store below it.

The worktree leaf repeats the project name so it is recognizable without
depending on the model, account, or agent home. Both names contain the same
three components: PROJECT, TYPE (conventional commit type), and FEATURE
(descriptive task slug):

- Directory leaf: `${PROJECT}_${TYPE}-${FEATURE}`.
- Branch: `${TYPE}/${PROJECT}_${FEATURE}`.

TYPE is required in the directory as well as the branch. A hyphen inside
FEATURE does not supply TYPE: for `TYPE=fix` and `FEATURE=parse-args`, the
leaf is `widget_fix-parse-args`, never `widget_parse-args` or `widget_parser`.
Compute both names from the same variables using the command template below;
do not shorten the directory to `${PROJECT}_${FEATURE}`. Check the actual
`git worktree add` destination and branch against these two formulas before
running it. Add a unique suffix to FEATURE on collision and recompute both
names; never reuse or delete another task's branch or worktree.

Derive `PROJECT` only from the physical live repository basename. Agent names,
model names, and account homes (`CODEX_HOME`, `CLAUDE_CONFIG_DIR`) must never
replace that project component or add an instance directory to this layout.
For project `widget` and task `fix-parser`, the leaf is `widget_fix-parser`
and the branch is `fix/widget_parser`; `claude_fix-parser`,
`codex-account-2_fix-parser`, and `fix/claude_parser` are invalid for that
project. Before `git worktree add`, check both complete names against the
resolved project basename; correct a mismatched project component first.

Choose TYPE and FEATURE once and reuse them for both names (for example, do not
spell the same type `feature` in the directory and `feat` in the branch). Keep
this task's branch and directory through all Feature commits; advancing the
commit ledger does not rename the branch or change its task slug.

For a live checkout `/home/mk/projects/widget`, a task can use:

```text
/home/mk/projects/
  widget/
  .worktrees/
    widget/
      widget_fix-parser/
```

After resolving the actual live checkout and choosing the project and task:

```bash
REPO="/home/mk/projects/widget"    # replace with the resolved live checkout
TYPE="fix"
FEATURE="parser"
PARENT="$(dirname "$REPO")"
PROJECT="$(basename "$REPO")"
WT="$PARENT/.worktrees/$PROJECT/${PROJECT}_${TYPE}-${FEATURE}"
BRANCH="$TYPE/${PROJECT}_${FEATURE}"
git -C "$REPO" worktree add -b "$BRANCH" "$WT"
cd "$WT"
pwd
git branch --show-current
```

Before creating the worktree, resolve the proposed store physically and ensure
no existing symlink redirects it into the live repository. Do not overwrite an
existing path or follow a misleading store symlink; resolve that conflict first.
Before every edit and commit, confirm `pwd -P` is physically under the external
project group and confirm the task branch.
Target all edits at this same worktree, including later follow-up turns.
The project group is only a container for worktrees, never an editing directory.
Resolve each file under the full WT path, including README and scratch output.
Shell `cd` affects only that tool call; pass the worktree as cwd on subsequent
calls and use absolute worktree paths with patch tools. Before delivery, inspect
the project group for misplaced files from this task and recover them into WT.
Check its status after editing to confirm the intended files changed there.
Never stage accidental live-checkout edits there; recover only your own changes
into the worktree without overwriting the user's work.

For a task spanning repositories, create a worktree in each project's own
`.worktrees/<project>/` group, using the same project/task identity. Never use
`worktrees/` without the dot, or put the store inside a repository.
Feature splitting and commit contents belong to the commits skill.

## Deliver each completed Feature

Commit in the worktree; never make feature, fix, or documentation commits on
the live default branch. Determine the actual default branch from repository
metadata and project instructions rather than assuming `master`. Preserve
unrelated work in the live checkout; do not force a checkout or overwrite it.

After each completed Feature (or an undivided task), perform these steps before
starting the next Feature:

1. Verify the Feature and commit it in the worktree. Confirm the commit exists
   and the worktree is clean.
2. From the live checkout on its default branch, merge the task branch with
   `git merge --no-ff "$BRANCH"`. Resolve conflicts without losing user changes.
3. Verify `git merge-base --is-ancestor "$(git -C "$WT" rev-parse HEAD)" HEAD`
   succeeds in the live checkout, and inspect its status.
4. Reapply the merged change through the project's installer, skill selector,
   or narrow service reload, then check the installed result and relevant logs.
   Follow Linux configuration rules for desktop changes. Static content with
   no installed consumer needs verification of the merged file only.
5. Return to the same worktree for the next Feature or correction. Every later
   commit, including a docs-only correction, needs its own merge and reapply.

Report completion only after the live default branch contains the work and its
consumers are updated. Never push, publish, add remotes, or rewrite history
unless the user explicitly requests it.

---
name: worktree
description: >-
  Use before editing a git repository: isolate work in a sibling
  .worktrees project group with an instance/task directory, commit there,
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

## Project and instance layout

Use `<project-parent>/.worktrees/<project>/<instance>_<type-feature>`.
`<project>` is the physical live checkout's basename. Resolve symlinks first:
for example, `/app` pointing at `/Projects/app` means the store is
`/Projects/.worktrees/app/`, never `/.worktrees/` or `/app/.worktrees/`.
When already inside a linked worktree, recover the live checkout from
`git worktree list --porcelain` and the common Git directory; do not treat the
worktree directory as a new project or nest another store below it.

`<instance>` identifies the agent home in use: use the basename of the explicit
runtime home (such as CODEX_HOME or CLAUDE_CONFIG_DIR). Otherwise use the
known harness home; if unavailable, use `agent`. Do not guess an account number.
Strip leading dots and replace characters outside letters, digits, hyphens,
and underscores with hyphens; use `agent` if empty. This also keeps the
instance valid in a Git branch component. Never use the full home path. `<type-feature>`
combines a conventional type and a descriptive task slug. The branch is
`<type>/<instance>_<feature>`. Add a unique suffix to both names on collision;
never reuse or delete another task's branch or worktree.

For a live checkout `/home/mk/projects/widget` and runtime home
`/home/mk/.codex-account-2`, a task can use:

```text
/home/mk/projects/
  widget/
  .worktrees/
    widget/
      codex-account-2_fix-parser/
```

After resolving the actual live checkout and choosing the instance and task:

```bash
REPO="/home/mk/projects/widget"    # replace with the resolved live checkout
INSTANCE="codex-account-2"      # replace with the actual runtime home basename
TYPE="fix"
FEATURE="parser"
PARENT="$(dirname "$REPO")"
PROJECT="$(basename "$REPO")"
WT="$PARENT/.worktrees/$PROJECT/${INSTANCE}_${TYPE}-${FEATURE}"
BRANCH="$TYPE/${INSTANCE}_${FEATURE}"
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
Check its status after editing to confirm the intended files changed there.
Never stage accidental live-checkout edits there; recover only your own changes
into the worktree without overwriting the user's work.

For a task spanning repositories, create a worktree in each project's own
`.worktrees/<project>/` group, using the same instance/task identity. Never use
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

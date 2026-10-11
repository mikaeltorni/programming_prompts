---
name: worktree
description: >-
  v1.0.18 — Edit Git projects in a sibling .worktrees project/task checkout,
  commit there, merge each Feature into the live default branch, and reapply
  its consumers. Never push unless requested.
---

# Isolate edits and deliver locally

Read project `AGENTS.md` and `CLAUDE.md` first. Resolve the physical live Git
checkout using Git's top-level path and symlink resolution. If launched inside
a linked worktree, recover the live checkout from its common Git directory and
`git worktree list --porcelain`.

Read-only tasks need no editing checkout. An explicit assignment to an existing
task worktree or request to edit the current checkout overrides new isolation;
verify the assigned checkout. If there is no Git repository, disclose the limit
and do not initialize replacement history.

For ordinary editing, establish one linked worktree before detailed planning
or investigation. Derive its path from the physical live root:

```text
LIVE = physical live checkout
PARENT = LIVE's immediate parent
PROJECT = LIVE's basename
TYPE = conventional commit type
FEATURE = one descriptive task slug
```

Assign those values once and construct both names with the same shell variables:

```sh
WT="$PARENT/.worktrees/$PROJECT/${PROJECT}_${TYPE}-${FEATURE}"
BRANCH="$TYPE/${PROJECT}_${FEATURE}"
git -C "$LIVE" worktree add -b "$BRANCH" "$WT"
```

Keep the FEATURE's hyphens unchanged in the branch.
The branch separates PROJECT and FEATURE with `_`; the directory separates
TYPE and FEATURE with `-`. Keep these separators exactly as shown above.
Resolve existing store symlinks; the store must remain under LIVE's immediate
parent, outside LIVE. On collision, choose a unique FEATURE suffix and recompute
both names; never delete or reuse another task. The first repository mutation is
`git worktree add -b BRANCH WT`, not source edits or `git init`.
Create `WT/tmp/` only after that command succeeds; precreating it creates WT
and makes Git reject the destination as already existing.

Retain LIVE, WT and BRANCH for the whole task. Before edits/commits and at
handoff, verify WT's physical path, registered location and branch against those
retained values. Use absolute task paths or an explicit tool working directory;
a shell `cd` does not persist. Reuse this checkout and branch for every Feature,
repair and documentation commit. The store holds registered worktrees only;
scratch/recovery files belong inside `WT/tmp/`. The project store parent is
not WT: every write and tool working directory uses the full retained task path.

After each completed Feature or focused repair:

1. Commit its working code and checks in WT. Confirm HEAD advanced and source
   changes are committed; incidental caches may stay unstaged.
2. Verify the live checkout is on its actual default branch using repository
   metadata or project guidance. Preserve unrelated live changes and merge
   with `git merge --no-ff BRANCH`; resolve conflicts without discarding work.
3. Confirm task HEAD is an ancestor of live HEAD and inspect live status.
4. Reapply the affected consumer through its installer, selector or narrow
   reload, and verify installed content and relevant logs. Follow selected
   Linux desktop rules. For static content with no installed consumer, inspect
   the merged files.

Finish this delivery before the next Feature. Documentation follows the same
checkout, commit and merge path. Repeat delivery after every later task commit,
including ledger/doc follow-ups; a previous merge does not deliver a new HEAD.
At handoff, the current task tip must be an ancestor of live HEAD.
Recover only this task's misplaced drafts,
without overwriting user work. If WT's location was wrong, use `git worktree move`
to the unused correctly derived path while preserving branch and contents.

Report completion only after local default-branch delivery and consumer checks.
Never push, publish, add remotes or rewrite history unless explicitly requested.

---
name: worktree
description: >-
  v0.0.22 — Edit Git projects in a sibling .worktrees project/task checkout,
  commit there, and deliver to the live default branch at the applicable
  checkpoint. Never push unless requested.
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
scratch/recovery files belong inside `WT/tmp/`, never `PARENT/.worktrees/PROJECT/tmp/`.
Every write and tool working directory uses the full retained task checkout path.

For an audit or repair Feature, collect related findings and finish its coherent
batch in WT before delivery. Individual findings do not each require a commit,
merge, installer run or app reload. Keep the requested Feature boundaries from
selected commits; a genuine dependency or user-requested checkpoint can justify
earlier delivery. Preserve another agent's active sessions and working files.

Commit each independently fixable policy backfill in WT as soon as it is
ready. For maintenance that only adds comments or diagnostics and preserves
application behavior, reviewing the diff is sufficient unless project guidance
requires additional checks. Keep the commit on the task branch until a
delivery checkpoint tied to relevant application testing or explicitly
requested delivery of that maintenance.

If relevant application tests need the live checkout, merge the ready batch
before running those tests. If the tests run in WT, include the pending
maintenance in the normal delivery of the tested application change. A
maintenance commit, static review, README update or handoff does not trigger
a merge of pending maintenance. An independently due delivery without an
application test checkpoint should carry only its own deliverables. Preserve
the task branch and record any delivery dependency if the commits cannot be
delivered independently.

At an applicable delivery checkpoint:

1. Commit its working code and checks in WT. Confirm HEAD advanced and source
   changes are committed; incidental caches may stay unstaged.
   A README-only commit cannot deliver uncommitted source or checks.
2. Verify the live checkout is on its actual default branch using repository
   metadata or project guidance. Preserve unrelated live changes. When the
   full task branch is due, use `git merge --no-ff BRANCH`. If delivery must
   exclude pending maintenance, use a delivery branch based on live and carry
   only the independent commits due. Resolve conflicts without discarding work.
3. Confirm the merge delivered the due changes and inspect live status. For
   a full task-branch merge, confirm task HEAD is an ancestor of live HEAD.
4. Apply consumers only when their installed/runtime inputs changed. Use the
   installer, selector or narrow reload once for the delivered batch and inspect
   installed content and relevant logs. Documentation-only or test-only changes
   need no runtime reload. Read-only checks or unchanged files need no redeploy.
   Follow selected Linux desktop rules; preserve active work. Static content
   without an installed consumer needs only merged-file inspection. Identical
   delivered code does not require repeating a passing application suite.

Finish due delivery before the next Feature. Documentation follows the same
checkout and commit path. At handoff, verify that commits due for delivery
are in live history. If only deferred delivery remains, retain the worktree
and branch and report the pending maintenance hashes and checkpoint. Apply
consumers again only if their actual inputs changed.
Recover only this task's misplaced drafts,
without overwriting user work. If WT's location was wrong, use `git worktree move`
to the unused correctly derived path while preserving branch and contents.

Report completion after verifying due live delivery and consumer checks.
Report deferred maintenance as committed in the task branch.
Never push, publish, add remotes or rewrite history unless explicitly requested.

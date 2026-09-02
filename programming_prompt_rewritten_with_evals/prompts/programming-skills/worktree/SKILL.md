---
name: worktree
description: >-
  MUST invoke before the first file Write or Edit in this git repo (including
  /app and /Projects/app). Create a sibling .worktrees/<project>/ worktree, do
  all coding there, commit in that worktree, merge back, never push. Skipping this fails the
  task even if the code is correct. Apply on every coding task, including new
  files from scratch. Not a substitute: Claude EnterWorktree / ExitWorktree.
---

# Git worktree isolation

The workspace is already a git repository with one **empty initial commit**.
Do not `git init` again. Do not rewrite history.

## Do this first

The first state-changing action of the task is `git worktree add` — never a
`Write` of `/app/*.py` (or `/Projects/app/*.py`) in the live checkout, even if
you already loaded another skill. Writing the program in `/app` without a
worktree is a **fail** even when the code is correct. Claude's
`EnterWorktree` / `ExitWorktree` tools are not a substitute.

## Where the worktree goes

The store is **next to** the project repo (sibling of the repo folder), never
inside it. This eval simulates a `Projects/` folder:

```text
/Projects/
  app/                       # this git repo (cloned initial state)
  .worktrees/
    app/                     # folder named exactly after the repo basename
      <worktree-dir>/        # your worktree lives here
```

`/app` is a symlink to `/Projects/app`. Use the `/Projects/app` path so the
parent is `/Projects`, not `/`:

```bash
REPO="/Projects/app"
NAME="$(basename "$REPO")"
PARENT="$(dirname "$REPO")"
WT="$PARENT/.worktrees/$NAME/feat-<task>"
git worktree add -b feat/<task> "$WT"
cd "$WT"
```

Hard rules:

- Create the worktree **before** the first file edit, and stay on its feature
  branch (`feat/…`), not `master`/`main`.
- Target every Write/Edit at a path under `$WT`, then run
  `git -C "$WT" status --short` and confirm the intended path appears. If it
  does not, the edit landed in the wrong checkout — put the file in `$WT` and
  continue from there; never recover by staging that edit in `$REPO`.
- Never put `.worktrees` inside the repo, and never use `worktrees/` (no dot).
  The folder under `.worktrees/` matches the repo basename — here
  `/Projects/.worktrees/app/…`.
- Commit your work in the worktree so the merge has something to bring back.
  Splitting the prompt into Features is a separate skill.

## Finish without pushing

After the last worktree commit, merge into the default branch from the live
checkout so the project repo contains the files. Leaving any code or docs
commit only in the worktree is a **fail**. The default branch receives merge
commits only; never make a direct feature, fix, or docs commit there.

```bash
git -C "$WT" status --short
cd "$REPO"
git checkout master
git merge --no-ff feat/<task> -m "Merge feat/<task>: <summary>"
git merge-base --is-ancestor "$(git -C "$WT" rev-parse HEAD)" HEAD
```

The worktree status must be clean before the merge, and the final
`merge-base --is-ancestor` must succeed; otherwise the newest worktree commit
is still undelivered. Any worktree commit made after an earlier merge — even a
README-only correction — needs its own merge. Also read
`git -C "$REPO" status --short` and resolve any intended file edited directly
in the live checkout without being committed there.

**Never push.** Do not `git remote add`, `git push`, or publish anywhere.
This is a local eval repository only.

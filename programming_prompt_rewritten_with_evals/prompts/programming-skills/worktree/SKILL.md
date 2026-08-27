---
name: worktree
description: >-
  MUST invoke before the first file Write or Edit in this git repo (including
  /app and /Projects/app). Create a sibling .worktrees/<project>/ worktree, do
  all coding and commits there, merge back, never push. Skipping this fails the
  task even if the code is correct. Apply on every coding task, including new
  files from scratch. Not a substitute: Claude EnterWorktree / ExitWorktree.
---

# Git worktree + incremental commits

The workspace is already a git repository with one **empty initial commit**.
Do not `git init` again. Do not rewrite history.

## Do this first

Invoke this skill at the start of the task, even if you already loaded `srp`
or another skill. The first state-changing action is `git worktree add` —
never `Write` `/app/*.py` (or `/Projects/app/*.py`) in the live checkout.

Writing the program in `/app` without a worktree is a **fail**, even if the
code is correct. Claude's `EnterWorktree` / `ExitWorktree` tools are not a
substitute for `git worktree add`.

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
git worktree add -b feat/<task> "$PARENT/.worktrees/$NAME/feat-<task>"
cd "$PARENT/.worktrees/$NAME/feat-<task>"
```

Hard rules:

- Create the worktree **before** the first file edit.
- Do **all** edits and commits in that worktree, not in the live checkout.
- Never put `.worktrees` inside the repo. Never use `worktrees/` (no dot).
- The folder under `.worktrees/` must match the project name (`basename` of
  the repo). For this eval that is `/Projects/.worktrees/app/…`.

## Commit each finished part

Whenever one part of the program is done (a helper, then another helper, then
the entrypoint), **commit that part in the worktree** before starting the next.
Do not batch the whole program into one end-of-task commit if you built it in
pieces.

Stay on the feature branch in the worktree (`feat/…`), not `master`/`main`.

## Finish without pushing

After the last worktree commit, merge into the default branch from the live
checkout so the project repo contains the files. Leaving the program only
in the worktree (never merged) is a **fail**.

```bash
cd "$REPO"
git checkout master
git merge --no-ff feat/<task> -m "Merge feat/<task>: <summary>"
```

**Never push.** Do not `git remote add`, `git push`, or publish anywhere.
This is a local eval repository only.

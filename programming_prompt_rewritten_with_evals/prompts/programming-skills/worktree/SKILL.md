---
name: worktree
description: >-
  Use whenever writing or editing code in a git repository: create a sibling
  .worktrees/<project>/ worktree, commit each finished part there, merge back,
  and never push. Apply on every coding task, including new files from scratch.
---

# Git worktree + incremental commits

The workspace is already a git repository with one **empty initial commit**.
Do not `git init` again. Do not rewrite history.

## Where the worktree goes

The store is **next to** the project repo (sibling of the repo folder), never
inside it:

```text
<parent>/
  <project>/                 # this git repo (e.g. /app)
  .worktrees/
    <project>/               # folder named exactly after the repo basename
      <worktree-dir>/        # your worktree lives here
```

From the repo root:

```bash
REPO="$(git rev-parse --show-toplevel)"
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
  the repo). For this eval the repo is `/app`, so the store is
  `/.worktrees/app/…`.

## Commit each finished part

Whenever one part of the program is done (a helper, then another helper, then
the entrypoint), **commit that part in the worktree** before starting the next.
Do not batch the whole program into one end-of-task commit if you built it in
pieces.

Stay on the feature branch in the worktree (`feat/…`), not `master`/`main`.

## Finish without pushing

After the last worktree commit, merge into the default branch from the live
checkout so the project repo contains the files:

```bash
cd "$REPO"
git checkout master
git merge --no-ff feat/<task> -m "Merge feat/<task>: <summary>"
```

**Never push.** Do not `git remote add`, `git push`, or publish anywhere.
This is a local eval repository only.

---
name: "commit"
description: >-
  Use when the user asks to inspect staged or unstaged git changes, split mixed work into logical
  commits, stage exact files or hunks, compose conventional commit messages, or create a commit.
  A normal invocation plans every change but creates exactly one clean commit for the first
  self-contained group, leaving all other groups untouched for later invocations.
---

# Commit Composer

Create one clean, reviewable git commit from a dirty worktree.

The default invocation is an execution request, not a planning-only request. Inspect all changes,
print the complete commit plan, create exactly one commit for the first safe group, verify it, and
stop. Do not ask for permission between the plan and the first commit.

## Required Result

Unless the user says exactly `commit all groups now`:

1. Create exactly one new commit when at least one safe, coherent group exists.
2. Put exactly one feature, fix, refactor, documentation concern, or maintenance concern in it.
3. Make the commit self-contained: its implementation and included tests must work when checked out
   without any of the remaining worktree changes.
4. Leave every other group uncommitted, unstaged, and byte-for-byte unchanged.
5. Stop immediately after verifying that commit. Report its hash and the remaining groups.

If there are multiple groups, committing all changed files is failure even if the message describes
the broad project goal. A single commit must be a single logical group, not merely a single `git
commit` command.

Do not create a commit only when there are no changes, every possible group contains unsafe
material, or the grouping cannot be made safely. Explain the concrete blocker in that case.

## Absolute Rules

- Inspect all staged, unstaged, and untracked changes before staging.
- Classify changes by hunk and purpose, not merely by filename.
- Print a numbered plan covering every changed hunk before staging.
- Stage only the first group in that plan.
- Never use `git add .`, `git add -A`, `git add -u`, or a command listing every changed path.
- Never stage a whole file when any hunk in that file belongs to another group.
- Never modify source files while composing commits. This workflow stages existing changes only.
- Never run `git stash`, `git stash apply`, `git stash pop`, or `git stash drop`.
- Never amend, rebase, reset the worktree, force-push, delete branches, or skip hooks.
- Never use `--no-verify`.
- Never commit secrets, credentials, `.env` files, logs, caches, editor state, build output, or
  accidental generated files.
- Treat user instruction files, installer changes, tests, documentation, and runtime changes as
  separate concerns unless their actual hunks directly implement or verify the same feature.
- Treat each test function or test case as a separate hunk-level dependency. Never include a test
  that exercises implementation left unstaged, even when other tests in the same file belong to
  group 1.
- Never accept tests that pass only because unstaged worktree changes are present. Validate the
  staged snapshot in isolation before committing.

## Step 1: Capture the Starting State

Record the starting commit:

```bash
git rev-parse HEAD
```

Inspect the complete worktree:

```bash
git status --short
git diff --stat
git diff --name-status
git diff
git diff --staged --stat
git diff --staged
git ls-files --others --exclude-standard
```

Read untracked files that may belong in a commit. Do not assume that similarly named files belong
to the same feature.

If anything is already staged, unstage it without changing the worktree:

```bash
git restore --staged -- :/
```

Then rerun `git status --short` and inspect the full unstaged diff. Never commit a pre-existing
index without rebuilding and verifying it.

## Step 2: Build a Hunk-Level Plan

Assign every changed hunk to one purpose. A feature group includes only:

- the implementation hunks for that feature;
- tests that specifically verify those implementation hunks;
- documentation or installer hunks specifically required to expose that feature.

Build a dependency closure for group 1. For every staged test, name the staged implementation hunk
that makes it pass. For every staged implementation hunk, include its directly corresponding test
when one exists. If a test file covers several plan items, mark the test file as `partial` and split
it by test function or test case. A whole new test file is not automatically one group.

Changes are separate groups when they can be reviewed, reverted, or explained independently.
Shared filenames do not merge separate concerns. Broad labels such as "tracker updates",
"installation improvements", or "cleanup" are not sufficient grouping reasons.

Print a numbered plan before staging. Mark mixed files as `partial`:

```text
1. feat(models): add exact launcher model selection
   scripts/model_catalog.py
   scripts/tracker.py (partial: model parsing only)
   tests/test_models.py
2. fix(tts): distinguish development announcements
   scripts/tracker.py (partial: announcement handling only)
   tests/test_notifications.py
3. fix(install): support unprivileged installation
   install.sh
   scripts/install.py
```

Choose as group 1 the smallest complete group that can be staged and verified safely. Prefer a
group with whole-file boundaries when one exists. Do not choose a broad group merely because it
touches the most files.

## Step 3: Stage Only Group 1

For a file whose entire diff belongs to group 1:

```bash
git add -- path/to/file
```

For a mixed file, stage only the relevant hunks:

```bash
git add -p -- path/to/file
```

For a new mixed file, first make it visible to patch staging, then select only group 1:

```bash
git add -N -- path/to/new_file
git add -p -- path/to/new_file
```

Use `s` to split a hunk. Use `e` only when splitting cannot isolate the lines. After partial
staging, inspect both sides:

```bash
git diff --staged -- path/to/file
git diff -- path/to/file
```

The staged side must contain only group 1. The unstaged side must retain every other group's
lines.

If the wrong content is staged, clear only the index and try again:

```bash
git restore --staged -- :/
```

This command must not alter worktree files.

## Step 4: Enforce the Separation Guard

Before committing, run:

```bash
git diff --staged --name-status
git diff --staged --stat
git diff --staged
git diff --staged --check
git status --short
```

Verify all of these statements:

- Every staged hunk belongs to plan item 1.
- Every required implementation and test hunk for plan item 1 is staged.
- Every staged test depends only on staged implementation or unchanged `HEAD` code.
- No hunk from plan items 2 or later is staged.
- If the plan has multiple groups, at least one intended change remains unstaged.
- The staged paths and hunks are a strict subset of the original changes when the plan has
  multiple groups.

If the plan has multiple groups but all original changes are staged, do not commit. Clear the
index, choose a narrower first group, and stage again.

## Step 5: Validate the Staged Snapshot in Isolation

Do not run the decisive validation in the dirty worktree. Unstaged code can make an incomplete
staged commit appear to pass.

Create a temporary detached worktree from the recorded starting commit, apply only the staged
patch, and run the narrowest relevant tests, linters, or build checks there:

```bash
verification_dir="$(mktemp -d)"
git worktree add --detach "$verification_dir" "$STARTING_COMMIT"
git diff --cached --binary | git -C "$verification_dir" apply --index --binary -
(cd "$verification_dir" && <targeted verification command>)
git worktree remove --force "$verification_dir"
```

Use the actual starting commit hash recorded in Step 1 for `STARTING_COMMIT`. Always remove the
temporary worktree, including after a failed command.

If staged tests fail because they need unstaged implementation, the staged group is invalid. Do
not commit it. Clear the index, revise the hunk-level plan, and stage a self-contained group. Common
fixes are:

- partially stage only the test functions that cover group 1;
- stage the missing implementation hunks when they truly belong to group 1;
- choose a smaller group with cleaner dependency boundaries.

Running the same command successfully in the original dirty worktree does not override a failure
in the staged-only worktree.

## Step 6: Commit Once

Use a conventional commit:

```bash
git commit -m "type(scope): short description" \
  -m "Explain what this one group changes and why."
```

Allowed types: `feat`, `fix`, `refactor`, `chore`, `docs`, `style`, `test`, `perf`.

Do not mention changes that remain unstaged. Do not run a second commit.

## Step 7: Verify and Stop

Run:

```bash
git show --stat --oneline HEAD
git status --short
```

Compare `HEAD` with the starting commit and confirm exactly one new commit exists. Confirm the
remaining plan items are still present and unstaged. The successful isolated verification from
Step 5 is required evidence that the commit is self-contained.

Then stop. Report:

- the new commit hash and subject;
- the files or hunks included;
- the numbered groups still uncommitted.

Do not proceed to group 2 unless the user starts another invocation or explicitly said
`commit all groups now`.

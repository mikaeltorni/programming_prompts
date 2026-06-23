---
name: "commit"
description: >-
  Use when the user asks to inspect staged or unstaged git changes, split mixed work into logical
  commits, stage exact files or hunks, compose conventional commit messages, or create a commit.
  A normal invocation plans every change and creates one clean commit per self-contained group
  across every repository the user explicitly requested, completing the full commit run at once.
---

# Commit Composer

Create clean, reviewable git commits from the requested worktree or repositories.

The default invocation is an execution request, not a planning-only request. Loading this skill is
explicit authorization to inspect, stage, validate, and commit every safe group in the repositories
the user named. Inspect all changes, print the complete cross-repository commit plan, then execute
the plan one group at a time in the same response. The plan is an informational progress update,
never an approval checkpoint.

Do not ask any confirmation question before the first commit. Never say or imply:

- "Would you like me to proceed?"
- "Should I commit these groups?"
- "I'll start after you confirm."
- "Reply go on to continue."

Waiting for user confirmation after presenting the plan is workflow failure. Continue
automatically unless the user explicitly requested plan-only output, explicitly told you not to
commit, or a concrete safety blocker prevents every coherent commit.

## Required Result

1. Cover every repository explicitly named by the user. Do not silently stop after the first repo.
2. Split the requested changes into self-contained groups and create one commit per group.
3. Keep each commit limited to one feature, fix, refactor, documentation concern, or maintenance
   concern.
4. Make every commit self-contained: its implementation and included tests must work when checked
   out without later commits or remaining worktree changes.
5. Continue through the complete plan in the same invocation, stopping only for a concrete safety
   blocker. Report every created hash and anything intentionally left uncommitted.

The words `plan first`, `plan the commits`, `one at a time`, or similar sequencing language do not
request a pause. They mean: print the plan first, then execute commit 1 immediately without another
user turn.

If there are multiple groups, committing all changed files together is failure even if the message
describes the broad project goal. Create multiple commits in the same run instead.

Do not create a commit only when there are no changes, every possible group contains unsafe
material, or the grouping cannot be made safely. Explain the concrete blocker in that case.

## Absolute Rules

- Inspect all staged, unstaged, and untracked changes before staging.
- Classify changes by hunk and purpose, not merely by filename.
- Print a numbered plan covering every changed hunk before staging.
- Begin staging plan item 1 immediately after printing the plan. Do not end the response or yield
  control to the user between planning and staging.
- Never ask for approval, confirmation, permission, or a "go on" message before commit 1.
- Stage only the current group in that plan; after committing it, rebuild the index for the next.
- Never use `git add .`, `git add -A`, `git add -u`, or a command listing every changed path.
- Never stage a whole file when any hunk in that file belongs to another group.
- Never modify source files while composing commits. This workflow stages existing changes only.
- Never run `git stash`, `git stash apply`, `git stash pop`, or `git stash drop`.
- Never amend, rebase, reset the worktree, force-push, delete branches, or skip hooks.
- Never use `--no-verify`.
- Always commit with the repository's own configured git identity. Never override the author or
  committer with `git -c user.email=...`, `git -c user.name=...`, `--author=...`,
  `GIT_AUTHOR_EMAIL`/`GIT_COMMITTER_EMAIL`, or any other identity flag or environment variable.
  Run plain `git commit`; let it read `user.name`/`user.email` from the local then global git
  config. If no identity is configured, stop and report it as a safety blocker — never guess,
  invent, or hardcode an email address.
- Never add a `Co-Authored-By:` trailer (or any other email) that is not the user's own configured
  git identity. Do not paste a remembered or assistant email into a commit message.
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

- Every staged hunk belongs to the current plan item.
- Every required implementation and test hunk for the current plan item is staged.
- Every staged test depends only on staged implementation or unchanged `HEAD` code.
- No hunk from plan items 2 or later is staged.
- If the plan has multiple groups, later groups remain unstaged until their turn.
- The staged paths and hunks are a strict subset of the remaining changes when later groups exist.

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

## Step 6: Commit Each Group

Use a conventional commit:

```bash
git commit -m "type(scope): short description" \
  -m "Explain what this one group changes and why."
```

Allowed types: `feat`, `fix`, `refactor`, `chore`, `docs`, `style`, `test`, `perf`.

Run `git commit` with no identity overrides so the commit uses the repository's configured
`user.name`/`user.email`. Do not add `-c user.*`, `--author`, or a `Co-Authored-By:` trailer.

Do not mention later groups in the current commit message. After verifying the commit, clear the
index if needed and repeat Steps 3–6 for the next planned group or repository.

## Step 7: Verify and Stop

Run:

```bash
git show --stat --oneline HEAD
git status --short
```

After each commit, compare `HEAD` with the repository's pre-group commit and confirm exactly one new
commit was added for that group. Confirm later plan items remain unstaged. The successful isolated
verification from Step 5 is required evidence that each commit is self-contained.

After all requested groups are complete, report:

- every new commit hash and subject;
- the files or hunks included in each;
- any groups intentionally left uncommitted and the concrete reason.

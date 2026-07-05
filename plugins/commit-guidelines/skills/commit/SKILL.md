---
name: "commit"
description: >-
  Use when the user asks to inspect staged or unstaged git changes, split mixed work into logical
  commits, stage exact files or hunks, compose conventional commit messages, or create commits.
  Invocation authorizes full execution: plan every change, then create one clean commit per
  self-contained group across every requested repository in the same run.
---

# Commit Composer

Turn the requested worktree changes into clean, reviewable, self-contained commits — planned at
hunk level, validated in isolation, and executed without pausing.

## Execution Contract

Loading this skill is authorization to inspect, stage, validate, and commit. It is an execution
request, not a planning request:

1. Inspect all changes, print the complete numbered commit plan, then **immediately** execute it
   group by group in the same response. The plan is a progress report, not an approval checkpoint.
2. Never ask "Should I proceed?", "Want me to commit these?", or wait for a "go on". Pausing after
   the plan is workflow failure.
3. Phrases like *plan first*, *plan the commits*, or *one at a time* set ordering, not pauses:
   print the plan, then start commit 1 without another user turn.
4. Cover **every** repository the user named; never stop silently after the first one.
5. Stop without committing only when there are no changes, the user explicitly asked for plan-only
   output or forbade committing, or a concrete safety blocker taints every coherent group — and
   then name the blocker.

When groups exist, one bulk commit of everything is failure even if the message describes the
project goal. Finish by reporting every new hash, its contents, and anything intentionally left
uncommitted.

## Hard Rules

**Scope and separation**

- Inspect all staged, unstaged, and untracked changes before staging anything.
- Classify by hunk and purpose, never by filename alone. One commit covers exactly one feature,
  fix, refactor, docs, or maintenance concern.
- Stage only the current group; never `git add .`, `git add -A`, `git add -u`, or any command that
  lists every changed path.
- Never stage a whole file when any of its hunks belongs to another group.
- Each commit must stand alone: its implementation and tests must work when checked out without
  later commits or leftover worktree changes.
- A test belongs to a group only if the implementation it exercises is staged in that group. Tests
  that pass only because of unstaged worktree code invalidate the group.
- Keep instruction files, installers, tests, docs, and runtime changes in separate groups unless
  their actual hunks implement or verify the same feature.

**Worktree safety**

- Never modify source files while composing commits; this workflow stages existing changes only.
- Never run `git stash` (in any form), amend, rebase, reset the worktree, force-push, delete
  branches, skip hooks, or use `--no-verify`.

**Identity and content**

- Commit with the repository's own configured identity: run plain `git commit` and let it read
  `user.name`/`user.email` from local then global config. Never override identity via
  `git -c user.*`, `--author`, `GIT_AUTHOR_EMAIL`/`GIT_COMMITTER_EMAIL`, or any flag or variable.
  If no identity is configured, stop and report a safety blocker — never guess or invent one.
- Never add a `Co-Authored-By:` or other trailer carrying an email that is not the user's own
  configured identity.
- Never commit secrets, credentials, `.env` files, logs, caches, editor state, build output, or
  accidental generated files.

## Step 1 — Capture the Starting State

```bash
git rev-parse HEAD                        # record as STARTING_COMMIT
git status --short
git diff --stat
git diff --name-status
git diff
git diff --staged --stat
git diff --staged
git ls-files --others --exclude-standard
```

Read untracked files that may belong in a commit; similar filenames do not prove shared purpose.

If anything is already staged, rebuild from zero — never trust a pre-existing index:

```bash
git restore --staged -- :/
```

then rerun `git status --short` and re-inspect the full unstaged diff.

## Step 2 — Build a Hunk-Level Plan

Assign every changed hunk to exactly one purpose. A feature group contains only:

- the implementation hunks of that feature,
- the tests that specifically verify those hunks,
- the docs or installer hunks required to expose that feature.

Close the dependency loop both ways: every staged test names the staged implementation hunk that
makes it pass; every staged implementation hunk brings its directly corresponding test when one
exists. When a test file spans plan items, mark it `partial` and split by test function — a new
test file is not automatically one group.

Changes are separate groups when they can be reviewed, reverted, or explained independently.
Shared filenames never merge concerns, and vague labels ("cleanup", "tracker updates",
"installation improvements") never justify a grouping.

Print the numbered plan, marking mixed files:

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

Pick as group 1 the smallest complete group that stages and verifies safely — prefer whole-file
boundaries, never breadth. Then start staging immediately; do not end the response between
planning and staging.

## Step 3 — Stage Only Group 1

```bash
git add -- path/to/file            # entire diff belongs to group 1
git add -p -- path/to/file         # mixed file: stage only relevant hunks
git add -N -- path/to/new_file     # new mixed file: make it patchable first,
git add -p -- path/to/new_file     #   then select only group 1
```

In patch mode use `s` to split; use `e` only when splitting cannot isolate the lines. After
partial staging, check both sides:

```bash
git diff --staged -- path/to/file   # must contain only group 1
git diff -- path/to/file            # must retain every other group
```

If the wrong content is staged, clear only the index (`git restore --staged -- :/`, which must not
touch worktree files) and redo it.

## Step 4 — Separation Guard

```bash
git diff --staged --name-status
git diff --staged --stat
git diff --staged
git diff --staged --check
git status --short
```

All of the following must hold before committing:

- Every staged hunk belongs to the current plan item — and every hunk the item needs is staged.
- Every staged test depends only on staged implementation or unchanged `HEAD` code.
- Nothing from later plan items is staged; later groups remain untouched until their turn.
- With multiple groups, the staged set is a strict subset of the remaining changes. If everything
  ended up staged anyway, do not commit — clear the index and pick a narrower group.

## Step 5 — Validate the Staged Snapshot in Isolation

Never run the decisive validation in the dirty worktree: unstaged code can make an incomplete
commit look green. Test the staged patch alone, on top of the starting commit:

```bash
verification_dir="$(mktemp -d)"
git worktree add --detach "$verification_dir" "$STARTING_COMMIT"
git diff --cached --binary | git -C "$verification_dir" apply --index --binary -
(cd "$verification_dir" && <targeted verification command>)
git worktree remove --force "$verification_dir"
```

Always remove the temporary worktree, even after failure. A pass in the dirty worktree never
overrides a failure here.

If staged tests fail for want of unstaged implementation, the group is invalid: clear the index,
revise the plan, and restage — typically by splitting test functions, pulling in the missing
implementation hunks that truly belong here, or choosing a smaller group.

## Step 6 — Commit Each Group

```bash
git commit -m "type(scope): short description" \
  -m "Explain what this one group changes and why."
```

Allowed types: `feat`, `fix`, `refactor`, `chore`, `docs`, `style`, `test`, `perf`. No identity
overrides, no trailers (see Hard Rules), no mention of later groups in the message.

Then repeat Steps 3–6 for each remaining group and repository.

## Step 7 — Verify and Report

After each commit:

```bash
git show --stat --oneline HEAD
git status --short
```

Confirm exactly one new commit exists for the group and later plan items remain unstaged; the
Step 5 isolation pass is the required evidence of self-containment.

When every requested group is done, report:

- each new commit hash and subject,
- the files or hunks it contains,
- anything intentionally left uncommitted, with the concrete reason.

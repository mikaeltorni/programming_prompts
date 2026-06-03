---
name: "commit"
description: >-
  Use when the user asks to inspect git changes (both staged AND unstaged), split diffs into logical commits,
  compose conventional commits, stage exact hunks, or create one or more clean git commits. Automatically
  scans all tracked and untracked files, groups related changes by feature across multiple files, and produces
  a commit plan before staging anything. Optimized for cautious models: always plan first, stage one commit at
  a time, verify staged diffs, and avoid broad staging.
---

# commit composer

You are a cautious git commit composer. Your job is to inspect the current repository diff (both **staged** AND **unstaged**) and turn it into clean, reviewable commits.

This skill is optimized for weaker or local coding models. Be explicit, slow, and verifiable. Prefer stopping after each commit over rushing multiple commits.

## absolute rules

- Always inspect before staging.
- Always produce a numbered commit plan before staging or committing.
- Never create more than one commit per turn unless the user explicitly says: "commit all groups now".
- Never use `git add .`, `git add -A`, or broad staging.
- Never include unrelated changes in the same commit.
- Never commit secrets, `.env` files, keys, tokens, credentials, editor junk, logs, caches, build output, or accidental generated files unless clearly intended.
- Never amend, reset, rebase, force-push, delete branches, or skip hooks unless the user explicitly asks.
- Never use `--no-verify`.
- If unsure whether a change belongs in a commit group, leave it unstaged and explain why.

## step 1 — full inspection

Run these commands to see everything:

```bash
git status --short
git diff --stat
git diff --name-only
git diff
git diff --staged --stat
git diff --staged
```

Read the output carefully. You now have a complete picture of **all** changes — staged and unstaged.

## step 2 — feature-based grouping (split across files)

Scan every changed file (both staged and unstaged). Group related changes into logical commit groups based on **feature**, not filename:

1. **Identify features**: Read the diffs. Each distinct feature, bugfix, refactor, or concern is a separate group. The same feature may touch multiple files — those files belong in the same commit group.
2. **Split across files**: If one file contains changes for two different features (e.g., a config update and a logic fix), stage only the hunks belonging to the first feature. Leave the rest unstaged for the next commit.
3. **Cross-file grouping**: If Feature A touches `src/auth.py` and `tests/test_auth.py`, both files' related changes go into one commit group, even if other files are also changed.
4. **Be conservative**: When in doubt, split into more commits rather than fewer. It is easier to squash later than to undo a bad merge.

Produce a numbered plan like:

```
1. feat(auth): add OAuth2 login flow — src/auth.py, tests/test_auth.py
2. fix(config): resolve missing default in settings — config/settings.yaml
3. refactor(utils): extract validation helpers — src/utils/validators.py
```

## step 3 — stage hunks for the first commit group only

Stage **only** the files and hunks that belong to the first commit group:

- Use `git add -p` or `git add <file>` for exact file-level staging.
- For partial-file changes, use interactive hunk staging (`git add -p`) and accept/reject individual hunks.
- Never stage anything outside the current commit group.

## step 4 — verify before committing

After staging, run:

```bash
git diff --staged --stat
git diff --staged
```

Verify that **only** the intended changes are staged. If something unintended is staged, unstage it with `git restore --staged <file>` or `git reset HEAD`.

## step 5 — commit with a conventional message

Commit using a conventional commit format:

```bash
git commit -m "type(scope): short description" -m "Longer body explaining what and why."
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `style`, `test`, `perf`.

## step 6 — repeat or stop

- If more commit groups remain, ask the user if they want to proceed with the next group.
- Stop when all changes are committed or the user says "stop".

## hunk staging cheat sheet

When using `git add -p`:

| Key | Action |
|-----|--------|
| `y` | Stage this hunk |
| `n` | Skip this hunk |
| `s` | Split hunk into smaller pieces |
| `e` | Manually edit which lines to stage |
| `q` | Quit, skipping remaining hunks |

Use `s` or `e` when a hunk contains changes for multiple features — split it so only the relevant feature's hunks are staged.

## example workflow

User: "commit my changes"

1. Inspect all diffs (staged + unstaged).
2. Identify 3 features across 5 files.
3. Produce commit plan with 3 groups.
4. Stage hunks for group 1 only.
5. Verify staged diff.
6. Commit group 1.
7. Ask: "Group 1 committed. Proceed with group 2?"

This ensures every commit is clean, focused, and reviewable — even when changes span multiple files or a single file contains unrelated modifications.

## critical: handling pre-staged changes from the harness

When the user's prompt already has files staged (e.g., via `git add` before Codex starts), **do not commit immediately**. A single `git commit` will grab *all* pre-staged files, even if they belong to different features.

**Correct procedure:**

1. Run `git reset HEAD` to unstage everything.
2. Re-read the diff of each file against HEAD (using `git diff -- <file>` or `git diff --stat`) to understand what changed.
3. Group files by feature as usual, then stage only the first group with explicit paths: `git add path/to/file1 path/to/file2`.
4. Verify, commit, repeat.

**Why this matters:** If you skip step 1 and go straight to committing, you risk bundling unrelated features into one commit — defeating the purpose of feature-based splitting. Always reset first when changes arrive pre-staged.

## example: pre-staged multi-feature scenario

User prompt has these files already staged across 3 features:
- `.agents/skills/commit/SKILL.md` (new) + `git-commit-composer/SKILL.md` (deleted) → skill rename
- `install.sh`, `scripts/setup_codex_config.py`, etc. → config changes
- `extension.js`, `schemas/*.xml`, `cycle-reasoning-effort.sh` → extension feature

**Wrong:** Commit immediately — all 12 files go into one commit.

**Right:**
```bash
git reset HEAD                          # unstage everything
# inspect diffs, group by feature
git add .agents/skills/commit/SKILL.md  # stage only skill rename files
git rm --cached .agents/skills/git-commit-composer/SKILL.md
git commit -m "chore(skills): rename git-commit-composer to commit" ...
# repeat for each group
```

This guarantees each commit is clean and reviewable, even when the harness pre-stages everything.

---
name: commits
description: >-
  Use whenever the user prompt can be split into Features, including vague
  "should have X" asks: break it into one Feature per capability the prompt
  names, implement one at a time, and commit each Feature in the worktree
  while the program still works. Apply on every coding task, including small
  scripts and new files from scratch.
---

# Feature commits

Before writing code, build a numbered ledger from the actual request. **Copy
each capability sentence verbatim into its own entry**, then list that entry's
commands and literal return prefixes. Exclude setup instructions that only name
an artifact, signature, or skill. Read the request again and account for every
capability sentence exactly once; derive the Feature count from that ledger,
never from a summary or a preferred number of commits.

A following "It should also …" sentence starts a new Feature even when it
shares state, helpers, or a topic with the preceding sentence. Within one
capability sentence, commands, cases, and optional extras stay together. Do not
merge adjacent ledger entries or move a command to another entry. Keep the
request's order when it already places dependencies first; otherwise resolve
implementation dependencies without changing the Feature boundaries.

## Complete and commit the current entry before starting the next

Treat the ledger as a queue. Work on only its first uncommitted entry:

- Implement its commands, helpers, validation, and required output. Preserve
  earlier Features; keep the program working at every commit.
- Write each requested output prefix verbatim in Python source, including its
  `=`: use a literal such as `f"result={value}"`, not a label assembled at
  runtime. A command helper can own the literal while sharing private logic.
- The staged Python tree contains earlier Features plus the current Feature,
  **no later command or output prefix** in code, dispatch tables, or docstrings.
  Shared state needed now is fine; a future report or command is not. Check this
  against the next ledger entry before committing, including on the last pair
  of entries — related capabilities still need separate commits.
- Include that Feature's applicable tests, logging, comments, and documentation
  in its commit. Do not postpone those obligations into planned cleanup commits.

Close each entry with this gate:

1. Verify its behavior and resolve failures before staging.
2. Stage only its changes in the worktree.
3. Run `git commit` as its own command, not chained behind a search or check
   that could fail and silently skip the commit.
4. Read the new `HEAD`, confirm it advanced and contains this entry's Python
   implementation, and record that commit beside the ledger entry. If the
   commit failed, resolve it and commit before editing the next Feature.

A statement that a Feature is tested or complete is not a commit. Only an
entry with a verified commit may be removed from the queue.

## Verify delivery against the ledger

Each entry must map to a distinct commit in order; inspect what each mapped
commit actually introduced, not just its subject or the total commit count.
A later Feature must not already exist in an earlier Feature's Python tree.
Do not batch missing entries into one final commit or split already-written
Features into cosmetic commits after the fact.

If a defect is discovered after a Feature was committed, make a focused fix
without adding the next Feature. An extra repair commit does not replace a
Feature commit or change the ledger. Never rewrite history to repair a commit.

A single Feature or an undivided change is one commit. Commits happen in the
worktree; worktree location and merge policy belong to the applicable project
instructions.

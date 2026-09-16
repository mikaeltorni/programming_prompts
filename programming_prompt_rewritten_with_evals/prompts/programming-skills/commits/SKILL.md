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
commands and required behavior. Exclude setup instructions that only name
an artifact, signature, or skill. Read the request again and account for every
capability sentence exactly once; derive the Feature count from that ledger,
never from a summary or a preferred number of commits. Do not start an edit
until the visible ledger contains those complete sentences: abbreviated quotes,
ellipses, and topic summaries cannot establish the boundaries. Audit it in both
directions: each source sentence maps to one row, and each row maps to only
one source sentence. Fix a mismatch before writing code.

A following "It should also …" sentence starts a new Feature even when it
shares state, helpers, or a topic with the preceding sentence. Within one
capability sentence, commands, cases, and optional extras stay together. Do not
merge adjacent ledger entries or move a command to another entry. Keep the
request's order when it already places dependencies first; otherwise resolve
implementation dependencies without changing the Feature boundaries. Related
operations in different sentences stay separate; multiple commands within one
sentence stay together. Do not regroup them by topic, shared state, inverse
operations, or convenience.

Keep the original ledger visible and preserve its boundaries through the whole
task. Before each implementation edit, identify the active row's exact sentence
and commands, and the commands still deferred to later rows. Record the verified
commit beside that row before advancing. After a merge or verification step,
resume the first uncommitted original row; do not replace the remaining rows
with a new combined summary. A shared dispatcher must expose only capabilities
implemented so far, even when adding all remaining cases seems easy.

## Complete and commit the current entry before starting the next

Treat the ledger as a queue. Work on only its first uncommitted entry:

- Implement its commands, helpers, validation, and required output. Preserve
  earlier Features; keep the program working at every commit.
- Preserve the requested output and public API. Judge completion by what the
  implementation does; labels may be assembled at runtime when appropriate.
- The staged implementation contains earlier Features plus the current Feature,
  with no later capability implemented in advance. Shared helpers needed now
  are fine. Check the executable behavior and diff against the next ledger
  entry before committing; descriptions of future work are not implementation.
- Include that Feature's applicable tests, logging, comments, and documentation
  in its commit. Do not postpone those obligations into planned cleanup commits.

Close each entry with this gate:

1. Compare the diff with the active row and every pending row: any later row's
   command handler or working capability means this change is not ready to
   commit. Defer that implementation before staging. Verify the current behavior
   and rerun a representative public-entrypoint example for every earlier
   Feature, especially after changing parsing or dispatch. Resolve failures
   before staging.
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

If a defect is discovered after a Feature was committed, commit a focused repair
before adding the next Feature. Verify the repaired tree preserves all earlier
Features. The original Feature commit plus its immediate repair is a valid
completed entry; a repair cannot rescue bundled Features. Optional extras may
land in a focused follow-up before advancing to the next entry. Never rewrite
history to repair a commit.

A single Feature or an undivided change is one commit. Commits happen in the
worktree; worktree location and merge policy belong to the applicable project
instructions.

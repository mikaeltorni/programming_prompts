---
name: commits
description: >-
  v1.2.1 — Give each complete capability sentence its own Feature and finish
  tests → code → commit before starting the next sentence.
---

# Feature commits

Use one Feature for each complete capability sentence in the original request.
Keep its required commands, cases and optional "and may" clauses together.
Every separate "It should also" sentence starts another Feature, even in one
paragraph. Setup naming only an artifact or signature is not a Feature.
Never choose a preferred Feature count or combine sentences because a program
is small. A repair sentence is a capability; several commands inside that same
sentence still belong to one Feature.

## Preserve the original queue

Before any application edit, copy each complete capability sentence verbatim
into one numbered ledger row. Preserve every word, backtick, parenthesis,
optional clause and final period; compare it character by character with the
request. Keep explanatory/setup text outside the quoted sentence. Check for
merged sentences, duplicate rows and extracted "and may" fragments now.
Each row lists its commands, required behavior, planned conventional commit
subject and, after verification, its real introducing commit hash.

Keep this ledger visible throughout the task. Use the authoritative workflow
plan when workflow is selected; otherwise retain the ledger in the task's
recorded evidence. Commits alone does not require a workflow file. Preserve
original boundaries when updating progress, merging or recovering from a
failure. Work only on the first uncommitted row.

Before each Feature cycle and application implementation edit, read that row
and state its exact sentence, planned subject, allowed commands and deferred
commands from later rows. Compare the allowed commands with the original
sentence. Recount the request-to-row mapping before the first source write and
each commit: every source capability has one row, and every row has one source
capability. A mismatch must be repaired before implementation or commit.

## Repeat this complete cycle for each row

### 3.1 Write tests

Save and run runnable public-interface checks for the current Feature before
its application edit. Preserve earlier checks; do not save later Features'
executable expectations yet. Record the actual baseline. Missing behavior
should fail for the intended reason; an absent entrypoint may fail to import,
and existing passing checks can protect a pure refactor. Static content and
project test prohibitions use their documented direct-verification exception.
Apply independently selected test, function and logging contracts from the
first draft.

### 3.2 Write code

Implement only the current sentence and necessary integration. The first
application file is already an implementation edit: never draft all Features
and split them into commits afterward. Shared helpers needed now are allowed;
the public dispatcher exposes only implemented capabilities.

Run the current and retained earlier public checks with fresh state. After
parsing or dispatch changes, exercise a representative earlier capability.
Preserve requested output, signatures and all earlier rules except those the
current sentence explicitly replaces. Resolve failures before closeout.
Inspect the full source tree and diff against the current and pending rows:
no later capability may already execute through the public entrypoint.

### 3.3 Commit

1. Review the current Feature's complete implementation and applicable checks,
   selected docstrings/logging/structure requirements, and necessary local
   documentation. Final README documentation belongs after all Feature cycles
   when docs is selected; it does not replace function contracts.
2. Stage only this Feature's changes in the applicable task worktree.
3. Run `git commit` as its own command. Use the row's planned conventional
   subject in `type:` or `type(scope):` form: `feat`, `fix`, `refactor`, `chore`,
   `docs`, `style`, `test` or `perf`. A plain "Add ..."/"Fix ..." is invalid.
   A failed search/check must not silently skip a chained commit.
4. Read the new HEAD, confirm it advanced and contains the working code and
   checks, and inspect its full source. Record the actual hash beside this row;
   it must differ from every earlier row's introducing hash. One hash for
   several rows exposes bundled implementation.
5. Complete separately selected worktree delivery and consumer verification
   before advancing. A "tested" or "complete" claim is not a verified commit.
   If committing is explicitly prohibited or no Git repository exists, record
   that concrete exception; finish permitted checks and implementation.

Only then start the next row's 3.1. Do not write every Feature's tests first,
implement later Features before the current commit, or add empty/cosmetic
commits to simulate cycles. If the first draft already contains later working
capabilities, remove them before its introducing commit. Later duplicate
handlers cannot repair early bundling.

## Repairs and delivery audit

If a completed Feature has a defect, finish a focused repair commit before the
next Feature, preserving earlier behavior. Record it beside the same original
row. Optional extras may likewise land in a focused follow-up before advancing;
an optional clause never becomes another ledger row. Never rewrite history to
repair the ledger or commit order. A repair cannot rescue bundled Features.

At handoff, compare the saved ledger with the original request, including
punctuation, and map each row to its distinct introducing commit in order.
Inspect what those commits actually introduced, including the first Feature's
full tree, rather than trusting subjects or a total commit count. Verify no
later Feature already worked at an earlier boundary and every applicable
commit/delivery gate is complete. Documentation and repairs are allowed extra
commits; they cannot substitute for missing introducing Feature commits.

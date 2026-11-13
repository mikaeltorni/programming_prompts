---
name: commits
description: >-
  v0.3.1 — Commit each requested capability separately; batch related findings
  within an audit instead of creating a delivery cycle per finding.
---

# Complete one requested capability per commit

Selection authorizes local commits and selected worktree delivery. Honor user
no-commit and no-test instructions. Never push unless asked.

Read the whole request. One complete user sentence stating a new capability is
one Feature, including each separate `It should also` sentence and sentences
revising earlier commands. Keep all commands, cases and optional clauses within
a sentence together. Artifact/signature setup and execution policies are not
capabilities. Do not anchor on a fixed Feature count.

An audit, repair or refactor sentence describes its requested outcome, not one
Feature per discovered omission, file, handler, assertion or helper. Collect and
fix related findings within that Feature. Do not reinterpret agent-authored
findings, plan bullets or continuation messages as new user capability sentences.
Distinct original capability sentences still get distinct introducing commits.

Before implementation record the ordered queue in the selected workflow plan,
or brief task evidence otherwise: original sentence, allowed behavior and a
unique conventional subject for each Feature. Record actual introducing hashes
as they happen; Git output is sufficient evidence. Work on the first unfinished
Feature and complete the whole queue.

For each Feature:

1. Save/run its missing public checks before application edits and record the
   baseline. Existing checks may protect a refactor; correct-path missing imports
   are valid creation baselines. Static content and project test prohibitions
   use direct checks; explicit no-test instructions skip execution honestly.
2. Implement this Feature and its necessary integrations. Batch related findings
   before the cumulative relevant run, fix failures and review the diff. Every
   required form in this sentence must work; earlier behavior remains unless
   intentionally revised. Later Features must not become executable yet, even
   as test observers. Inspect pending forms; use a focused public probe only
   where source review leaves their availability uncertain and tests are allowed.
3. Commit the ready Feature before starting the next Feature's checks or code.
   Do not interleave another Feature or postpone all commits until the end.
   Stage this code and its checks by explicit path. Run `git commit` as its own
   command with `type: summary` or `type(scope): summary`, using `feat`, `fix`,
   `refactor`, `chore`, `docs`, `style`, `test` or `perf`. Confirm HEAD advanced,
   inspect its contents, record the hash, and finish selected local delivery.

A passing run remains valid through read-only review, staging and plan updates.
Rerun affected checks if relevant code changes, not because a status was read or
a commit was about to happen. Do not create empty or cosmetic commits. A later
concrete defect can justify a repair commit recorded against its original Feature;
this is not a requirement to commit every finding separately.

At handoff map every requested Feature to its distinct introducing hash in order
and delivered behavior. Later splits cannot repair a bundled implementation.
With docs selected, complete code cycles before final README work. If Git is
absent or commits are forbidden, record that exception and finish permitted work.

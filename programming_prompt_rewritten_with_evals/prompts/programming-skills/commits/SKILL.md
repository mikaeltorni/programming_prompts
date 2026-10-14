---
name: commits
description: >-
  v0.3.0 — Give each complete capability sentence its own Feature and finish
  tests → code → commit before starting the next sentence.
---

# Complete one capability per commit

Explicit selection authorizes the required local Git commits and selected
worktree delivery. Honor a user prohibition on commits; never push unless asked.

The loop is: one sentence → one queue row → checks → baseline → code → pass →
commit → deliver → next row. Two things break it most often: counting the
whole request as one capability, and moving on after a passing run without
committing. Both rules below are absolute.

## One behavior sentence is one Feature

Read the entire request before editing and split it into sentences. Every
sentence that states behavior — a command, a result or a rule — is one
Feature, including each sentence that starts `It should also` and each
sentence that extends or revises a command an earlier sentence introduced.
Sentences describing related conversions, arithmetic variants or commands of
the same program are separate Features; one small program, one entrypoint or
one artifact never merges them. Artifact/signature setup (file name, function
name, import path) and execution policies are not capabilities; a behavioral
repair is. Do not choose a fixed Feature count: the number of Features equals
the number of behavior sentences.

Within one sentence, keep its commands, cases and optional `and may` clauses
together: all of its required commands work in its introducing commit, and the
sentence is not split into per-command cycles.

Before saving any check, write the queue in the selected workflow plan, or in
other task evidence when workflow is unselected: one row per sentence, quoting
the sentence in full, with its allowed commands and a planned conventional
subject that differs from every other row's. A row holding two sentences, or
a queue with fewer rows than behavior sentences, is wrong; fix it before
continuing. Record each introducing hash in the queue or in other task
evidence; recorded `git commit` output is sufficient without a duplicate queue
entry. Cosmetic Markdown punctuation is not a separate deliverable. Work only
on the first unfinished row.

## The cycle for the current row

1. Save and run this row's public checks before editing application code.
   Save checks for this row only; later rows' checks wait for their own cycle.
   Existing passing checks may protect a refactor. A correct-path
   missing-file/import failure for a new entrypoint completes the creation
   baseline: record it and implement this Feature next, rather than rewriting
   the valid import path. Static content and project test prohibitions use
   direct checks. Follow selected testing for detailed coverage, including its
   upgrade of earlier rejection checks when this row adds a read-only query.
2. Implement only this row and necessary integration. Later selectors and
   later changes to existing forms or results remain unsupported until their
   own cycle; do not scaffold working future branches, and a later command
   must not execute through the public interface yet, even as a test observer.
   A sentence that revises an earlier command keeps the earlier acceptance and
   results until its own cycle. Run this row's checks with all retained
   earlier checks, fix failures and review the actual diff.
3. Commit the moment the cumulative run passes, in the very next command.
   Nothing fits between the passing run and the commit: not the next row's
   checks, not the next row's code, not the README. Never postpone commits to
   the end of the task; a commit created after later rows' code exists carries
   that code and bundles those Features, whatever its subject says. Before
   staging, run every later row's commands through the public interface and
   confirm each is still rejected; one that already works means this cycle
   bundled it, so take that behavior out of the change first. Stage this row's
   working code and checks together. Run `git commit` as its own command with
   `type: summary` or `type(scope): summary`, using `feat`, `fix`, `refactor`,
   `chore`, `docs`, `style`, `test` or `perf`. Confirm HEAD advanced, inspect
   the commit's contents and record the actual hash now. Complete selected
   worktree merge and consumer verification before the next row.

Each sentence first becomes executable in its own introducing commit; a queue,
a later split or several commits made in a row at the end cannot make a bundled
implementation compliant. Do not pad history with empty commits. Focused
repairs and optional follow-ups may close before the next Feature; record them
with their original row without rewriting history. Commit the final Feature's
source and checks before starting README work when docs is selected.

At handoff, reconcile the full queue with actual commit trees and delivered
behavior: every row has its own hash, in order. Finish every requested
capability, not only the first passing cycle. If no Git repository exists or
commits are forbidden, record that exception and finish permitted
implementation and checks.

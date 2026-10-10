---
name: commits
description: >-
  v1.2.5 — Give each complete capability sentence its own Feature and finish
  tests → code → commit before starting the next sentence.
---

# Complete one capability per commit

Explicit selection authorizes the required local Git commits and selected
worktree delivery. Honor a user prohibition on commits; never push unless asked.

Read the entire request before editing. Queue one Feature for each complete
capability sentence, keeping its commands, cases and optional `and may` clauses
together. Every separate `It should also` sentence starts another Feature.
Artifact/signature setup and execution policies are not capabilities; a
behavioral repair is. Do not choose a fixed Feature count.

Record the queue in the selected workflow plan, or other task evidence when
workflow is unselected. Use complete sentences or faithful summaries preserving
each sentence boundary, required behavior and optional clauses. List allowed commands, a
planned conventional subject and the introducing hash.
The queue must faithfully cover the request; cosmetic Markdown punctuation is
not a separate deliverable. Work only on its first unfinished Feature.

For each Feature, finish:

1. Save and run its public checks before editing application code. Existing
   passing checks may protect a refactor; a missing-entrypoint import failure
   is a valid creation baseline. Static content and project test prohibitions
   use direct checks. Follow selected testing for detailed coverage.
2. Implement only this capability and necessary integration. Run its checks
   with retained earlier checks, fix failures and review the actual diff.
   A later command must not execute through the public interface yet, even
   as a test observer. Intentional later replacements preserve other behavior.
3. Stage this Feature's working code and checks together. Run `git commit` as
   its own command with `type: summary` or `type(scope): summary`, using `feat`,
   `fix`, `refactor`, `chore`, `docs`, `style`, `test` or `perf`. Confirm HEAD
   advanced, inspect its contents and record the actual introducing hash now.
   Complete selected worktree merge and consumer verification before advancing.

Do not draft all features and split them afterward, or pad history with empty
commits. Each sentence has a distinct working introducing commit in order.
Focused repairs and optional follow-ups may close before the next Feature;
record them with their original row without rewriting history. Final README
work follows all feature cycles when docs is selected.

At handoff, reconcile the full queue with actual commit trees and delivered
behavior. Finish every requested capability, not only the first passing cycle.
If no Git repository exists or commits are forbidden, record that exception
and finish permitted implementation and checks.

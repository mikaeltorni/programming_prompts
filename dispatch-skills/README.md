# Dispatch Skills

Task skills in this folder are **dispatchable**: they are written to be handed
to an agent together with a target repository, with no other setup, and they
drive a long-running improvement loop on that repository until a measurable goal
is reached.

They are the only prompts in this repository that the Agent Command Center /
notes-app skill menu offers. Everything under `plugins/` and `skills/` stays out
of that menu because they supply selectable engineering guidance or need a
conversation to be useful. The retired generic programming prompt is no longer
shipped.

## What makes a prompt dispatchable

A `dispatch-skills/<name>/SKILL.md` must:

1. Carry the standard skill front matter (`name`, `description`) and use the
   directory name as `name`, so the harness-native invocation is exactly
   `/<name>` (Claude Code, Cline, Grok) or `$<name>` (Codex family).
2. Work when the only context is "here is a repository" — no follow-up questions
   are required before the first useful action.
3. Define a **measurable score**, so progress across separate agent runs is
   comparable rather than a matter of opinion. Record it in a tracked scorecard
   file when the audit is about the repository's own public surface; report it
   in the run output instead when the audit would otherwise commit private
   detail such as repository names, branches, or filesystem paths.
4. Define an explicit **improvement loop** with a stop condition, so the agent
   keeps working until the goal is met instead of stopping at "good enough".
5. Defer isolation, commit, merge, and reload policy to
   the selected `worktree` and `commits` skills rather than restating it.

## Current dispatch skills

| Skill | Goal | Where the score goes |
| --- | --- | --- |
| [`github-seo`](github-seo/SKILL.md) | Make a GitHub project findable by search engines, by AI assistants, and by the humans it is for | `docs/seo-scorecard.md` |
| [`github-portfolio-scan`](github-portfolio-scan/SKILL.md) | Rank every live original git checkout in a directory for GitHub resume / portfolio release-readiness, with evidenced positives and flaws | Run report only — the audit is never written to a scanned tree |
| [`worktree-cleanup`](worktree-cleanup/SKILL.md) | Reclaim the disk space held by finished task worktrees, without ever removing work that is still alive | Run report only — the audit is never written to a file |

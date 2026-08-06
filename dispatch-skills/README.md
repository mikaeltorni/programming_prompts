# Dispatch Skills

Task skills in this folder are **dispatchable**: they are written to be handed
to an agent together with a target repository, with no other setup, and they
drive a long-running improvement loop on that repository until a measurable goal
is reached.

They are the only prompts in this repository that the Agent Command Center /
notes-app skill menu offers. Everything under `plugins/` and `skills/` stays out
of that menu, because those prompts are either always-on policy
(`general-programming-guidelines`, which the menu offers as an explicit extra) or
they need a conversation to be useful.

## What makes a prompt dispatchable

A `dispatch-skills/<name>/SKILL.md` must:

1. Carry the standard skill front matter (`name`, `description`) and use the
   directory name as `name`, so the harness-native invocation is exactly
   `/<name>` (Claude Code, Cline, Grok) or `$<name>` (Codex family).
2. Work when the only context is "here is a repository" — no follow-up questions
   are required before the first useful action.
3. Define a **measurable score** and a tracked scorecard file, so progress across
   separate agent runs is comparable rather than a matter of opinion.
4. Define an explicit **improvement loop** with a stop condition, so the agent
   keeps working until the goal is met instead of stopping at "good enough".
5. Defer isolation, commit, merge, and reload policy to
   `general-programming-guidelines` rather than restating it.

## Current dispatch skills

| Skill | Goal | Scorecard |
| --- | --- | --- |
| [`github-seo`](github-seo/SKILL.md) | Make a GitHub project findable by search engines, by AI assistants, and by the humans it is for | `docs/seo-scorecard.md` |

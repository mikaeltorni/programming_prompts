---
name: workflow
description: >-
  v0.2.0 — Coordinate an end-to-end programming task as an ordered workflow
  only when the user explicitly invokes this skill.
---

# Programming workflow

## Activation and ownership

Run this workflow only when the user explicitly invokes `$workflow` (or the
host's equivalent explicit skill command). Its presence in an installed skill
catalog does not activate it.

This skill may coordinate other independently selected skills. No other skill
depends on this one, and this skill must not require edits that add a
`workflow` dependency or invocation to another skill.

Own the end-to-end sequence for the current programming request. Break the
work into ordered phases that fit the request, finish each phase before moving
to the next, and keep the user's stated goal and constraints visible throughout
the task.

At each phase boundary, record what was completed and what phase comes next so
the task remains resumable. Do not broaden the user's scope merely to make the
workflow more elaborate.

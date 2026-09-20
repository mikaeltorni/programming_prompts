---
name: workflow
description: >-
  v0.4.0 — Coordinate an end-to-end programming task as an ordered workflow
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

## Read the enabled skills

Before building the phase sequence, inspect the current user prompt and the
skill instructions actually supplied in the conversation. Make a short
inventory containing only the companion skills explicitly invoked by the user
or loaded as applicable by the host. Assign each inventoried skill to the phase
where its instructions apply.

Do not treat a skill as enabled merely because it is installed, discoverable,
mentioned as an example, or known to exist in the repository. Do not load or
apply an unselected companion on this skill's behalf.

## Phase order

Follow this order:

1. **Plan.** Before repository mutation, translate the user's goal into an
   actionable sequence that preserves their constraints and names the expected
   deliverables.
2. **Establish the worktree.** Resolve the repository and create the task's
   isolated worktree before editing repository files.
3. **Write the code.** Implement the plan inside that worktree while applying
   the programming skills supplied for the task.
4. **Write the documentation.** After the code-writing phase, apply the docs
   guidance supplied for the task and update the documentation affected by the
   implementation.

Do not reorder implementation ahead of planning or documentation ahead of the
code it describes.

At each phase boundary, record what was completed and what phase comes next so
the task remains resumable. Do not broaden the user's scope merely to make the
workflow more elaborate.

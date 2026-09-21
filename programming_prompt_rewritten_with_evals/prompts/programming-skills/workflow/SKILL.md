---
name: workflow
description: >-
  v0.9.0 — Coordinate an end-to-end programming task as an ordered workflow
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

The dependency direction is one-way:

```text
workflow -> independently enabled companion skills
companion skills -/> workflow
```

Keep every companion usable on its own. Dependency declarations, routing
instructions, and orchestration references belong only in this workflow skill;
never add them to `worktree`, `commits`, `srp`, `logging`, `commenting`,
`debug`, `docs`, or another companion.

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

If a requested companion is unavailable, unreadable, or absent from the
supplied skill context, mark it skipped in the plan and continue with the
remaining phases and enabled skills. Do not install it, reconstruct its rules
from memory, or fail the whole workflow merely because the companion is
missing.

## Phase order

Follow this order:

1. **Plan.** Before tracked repository mutation, translate the user's goal into an
   actionable sequence that preserves their constraints and names the expected
   deliverables. Store it as Markdown at
   `<repository-root>/tmp/workflow-<task-slug>.md`, creating `tmp/` when needed.
   Use a short stable task slug, update the same file as phases advance, and do
   not stage or commit this temporary plan unless the user explicitly asks.
2. **Establish the worktree when enabled.** If the `worktree` companion is in
   the enabled-skill inventory and available, follow it to create the task's
   isolated worktree before editing repository files. Otherwise skip this
   phase.
3. **Write the code.** Implement the plan inside that worktree while applying
   the programming skills supplied for the task.
4. **Write the documentation when enabled.** If a documentation companion is
   in the enabled-skill inventory and available, apply its guidance after the
   code-writing phase. Otherwise skip this phase.

Do not reorder implementation ahead of planning or documentation ahead of the
code it describes.

### Code-writing companions

When present in the enabled-skill inventory, apply `logging`, `commenting`, and
`srp` during **Write the code**. Their requirements shape the implementation in
that phase; do not defer their logging, code comments/docstrings, or
single-responsibility structure to the documentation phase. Preserve each
companion's own scope and exact rules instead of restating weaker substitutes
here.

## No workflow verification phase

Do not add a standalone verification, review, test, or validation phase to this
workflow. The workflow ends after the documentation phase and the normal task
handoff. When an independently enabled companion skill requires checks, honor
that requirement within the phase that skill owns; do not represent it as an
extra phase supplied by this skill.

At each phase boundary, record what was completed and what phase comes next so
the task remains resumable. Do not broaden the user's scope merely to make the
workflow more elaborate.

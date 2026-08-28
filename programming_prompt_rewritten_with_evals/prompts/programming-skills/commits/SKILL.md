---
name: commits
description: >-
  Use whenever the user prompt can be split into Features: classify those
  Features first, implement one at a time, and commit each Feature in the
  worktree while the program still works. Apply on every coding task,
  including small scripts and new files from scratch.
---

# Feature commits

Classify the user prompt into discrete Features before writing Feature code.
A Feature is a self-contained unit of shippable behavior (for example
"add catalog" and "add checkout" in one request). Record the Feature list,
or record that no multi-feature split applies.

When **two or more Features** are found:

- Plan order **dependencies first**, then dependents.
- Implement **one Feature at a time** in that order.
- **Commit that Feature in the worktree** before starting the next.
- After each Feature commit the program must **still work**. Do not land a
  commit that only works after later Features arrive.
- Do not batch every Feature into one end-of-task commit.

A single Feature (or none) is one commit. Commits happen in the worktree;
where that worktree lives is a separate skill.

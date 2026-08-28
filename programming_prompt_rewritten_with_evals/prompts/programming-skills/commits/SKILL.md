---
name: commits
description: >-
  Use whenever the user prompt can be split into Features, including vague
  "should have X" asks: break them into a 3–5 step plan, implement one at a
  time, and commit each Feature in the worktree while the program still works.
  Apply on every coding task, including small scripts and new files from scratch.
---

# Feature commits

When the user prompt is vague ("a calculator should have add", "build a
shop") or lists several capabilities in one request, **break it into a
multi-step plan of 3–5 Features** before writing Feature code. Start with
the basic implementation that already works, then add further features one
at a time.

A Feature is a self-contained unit of shippable behavior. Record the Feature
list. Do not skip the breakdown because the script is small or the prompt
did not number the steps.

Illustrative breakdowns (not the current task):

- calculator: add two numbers, then subtract, then multiply, then divide
- counter: increment, then decrement, then read, then set

When **two or more Features** are found:

- Plan order **dependencies first**, then dependents.
- Implement **one Feature at a time** in that order.
- **Commit that Feature in the worktree** before starting the next.
- After each Feature commit the program must **still work**. Do not land a
  commit that only works after later Features arrive.
- Do not put a later Feature into an earlier Feature's commit.
- Do not batch every Feature into one end-of-task commit.

A single Feature (or none) is one commit. Commits happen in the worktree;
where that worktree lives is a separate skill.

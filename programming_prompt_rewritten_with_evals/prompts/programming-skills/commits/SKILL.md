---
name: commits
description: >-
  Use whenever the user prompt can be split into Features, including vague
  "should have X" asks: break them into about 3 Feature groups, implement one
  at a time, and commit each Feature in the worktree while the program still
  works. Apply on every coding task, including small scripts and new files
  from scratch.
---

# Feature commits

When the user prompt is vague ("a calculator should have add") or lists
several capabilities in one request, **break it into about 3 Features**
before writing Feature code:

1. the basic implementation that already works
2. the next distinct capability
3. the remaining extras (one Feature, even if that extras group names two
   related commands)

A Feature is one **group** the prompt names, not every operator or hour
band. Morning/afternoon/evening in one sentence is one Feature. Multiply
and divide in one sentence is one Feature. Record the Feature list. Do not
skip the breakdown because the script is small.

Illustrative breakdowns (not the current task):

- calculator: add, then subtract, then multiply-and-divide
- greeter: hello, then hour-based greetings, then farewell

When **two or more Features** are found:

- Plan order **dependencies first**, then dependents.
- Implement **one Feature at a time** in that order.
- **Commit that Feature in the worktree** before starting the next.
- After each Feature commit the program must **still work**. Do not land a
  commit that only works after later Features arrive.
- Do not put a later Feature into an earlier Feature's commit.
- Do not merge two prompt groups into one commit.
- Do not batch every Feature into one end-of-task commit.
- In that Feature's commit, use the return prefixes the prompt names
  (`sum=`, `morning=`, `added=`). Do not hide them behind a variable if the
  prompt showed a literal prefix.

A single Feature (or none) is one commit. Commits happen in the worktree;
where that worktree lives is a separate skill.

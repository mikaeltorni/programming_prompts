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

## Find the Features by reading the sentences

**Each capability sentence in the prompt is its own Feature.** The opening
sentence that names the first behavior is Feature 1; every following
"It should also …" sentence is the next Feature, in the order written.
Three such sentences means **three Features and three commits** — do not
collapse two sentences into one Feature because they feel like the same
topic (C→F and F→C are two sentences, so two Features; catalog and total
are two sentences, so two Features).

Inside **one** sentence, a group stays one Feature: morning/afternoon/
evening in one sentence is one Feature; multiply and divide in one
sentence is one Feature; a sentence naming a main command plus an
optional extra ("… and may count items") is one Feature. Record the
Feature list before writing Feature code. Do not skip the breakdown
because the script is small.

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

## Keep later Features out of the earlier commit

A Feature's commit contains **only that Feature's** literal return
prefixes. Before you commit, re-read the staged file and check that **no
later Feature's prefix or command appears anywhere in it** — not in a
branch, not in a dispatch table, not in a docstring, not as a
"while I'm here" extra. Writing `total=` while committing the `added=`
Feature is a failure even though the code works; leave `total=` out
entirely and add it in its own commit. Only after that commit lands do you
write the next Feature's prefix.

A single Feature (or none) is one commit. Commits happen in the worktree;
where that worktree lives is a separate skill.

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
several capabilities, **break it into about 3 Features** before writing
Feature code:

1. the basic implementation that already works
2. the next distinct capability
3. the remaining extras (one Feature, even when that group names two related
   commands)

## Find the Features by reading the sentences

**Each capability sentence in the prompt is its own Feature.** The opening
sentence is Feature 1; every following "It should also …" sentence is the next
Feature, in the order written. Three such sentences means **three Features and
three commits**. The sentence boundary wins over conceptual pairing: opposite
conversion directions in two sentences are two Features even when they share a
formula or entrypoint (C→F and F→C; catalog and total).

Inside **one** sentence, a group stays one Feature: morning/afternoon/evening
is one Feature; multiply and divide is one Feature; a main command plus an
optional extra ("… and may count items") is one Feature.

Before writing code, make a numbered ledger with one entry per capability
sentence and its literal return prefix(es); it is your commit checklist. Do
not rename or regroup its entries later, and do not skip the breakdown because
the script is small. Illustrative breakdowns (not the current task):

- calculator: add, then subtract, then multiply-and-divide
- greeter: hello, then hour-based greetings, then farewell

## Commit one Feature at a time

- Plan order **dependencies first**, then dependents.
- Implement one Feature at a time and **commit it in the worktree** before
  starting the next; after each commit the program must still work.
- Do not put a later Feature into an earlier Feature's commit, merge two
  prompt groups into one commit, or batch every Feature into one final commit.

## Write each prefix as a literal, with its `=`

The prefix the prompt names must appear **verbatim in the source**, `=`
included — `f"down={value}"`, never a label assembled at runtime
(`prefix = "up" if op == "inc" else "down"` … `f"{prefix}={value}"`), which
leaves the text `down=` nowhere in the file and the Feature looking
unimplemented. Each command's own helper types its own literal prefix as you
implement that Feature.

A Feature's commit contains **only that Feature's** prefixes. Before
committing, re-read the staged file and confirm no later Feature's prefix or
command appears in it — not in a branch, a dispatch table, a docstring, or a
"while I'm here" extra. Writing `total=` while committing the `added=` Feature
is a failure even though the code works.

## No extra code commits between the Feature commits

Feature commits are counted **in order**: the first commit that touches a
`.py` file is Feature 1, the second is Feature 2, and so on. Any extra code
commit slipped in between — `Fix hour command dispatch`, `Refactor helpers`,
`Add logging`, `Tidy up` — silently takes Feature 3's slot. Commits that touch
no `.py` file (a README-only commit, the final merge) take no slot.

So finish a Feature **before** committing it: run it, fix it, and clean it up
while the work is still uncommitted, so the correction lands inside that
Feature's own commit. Never rewrite history to repair a commit that landed.

Closing a Feature is a hard gate, in this order:

1. Verify the current Feature while its code is still uncommitted.
2. Stage its `.py` file(s).
3. Run `git commit` as its own command — never chained behind a check
   (`… && grep … && git commit -m …`), where one failing tool silently skips
   the commit and Feature 1's code rides along in the Feature 2 commit.
4. Read the new `HEAD` and confirm that commit contains the current ledger
   entry's `.py` change. If `HEAD` did not advance, commit before anything
   else.

Only after those four steps may you edit the next Feature, write the README,
or merge. Testing a Feature is not committing it.

Three Features means the Python history is exactly three commits, in the
prompt's order. A single Feature (or none) is one commit. Commits happen in
the worktree; where that worktree lives is a separate skill.

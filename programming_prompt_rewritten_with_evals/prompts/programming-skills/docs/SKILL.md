---
name: docs
description: >-
  v1.0.4 — After writing or fixing a program, document its purpose, public
  entrypoint, and accepted commands in the project-root README.md.
---

# Document the program

When feature cycles are selected, start the final README phase only after
every feature has finished tests, implementation, verification and commit.
Function docstrings and required feature-local notes still belong in that
feature's working revision; final user documentation follows afterward.

After the code works, write or update the project-root `README.md`. State what
the program does, name its public entrypoint, and list the commands it accepts.
Do this even for a small script or a new file. Function docstrings belong to
the separate commenting skill.

Before handing off, read the README in the delivered project root and confirm
it covers the implemented entrypoint and every accepted command. Successful
tests and code commits do not complete this deliverable. This obligation also
applies when workflow is not selected; finish the README after the code works
and before the final response.

When a worktree companion is selected, the project-root README is in the
active task worktree. Write and commit it there, then merge that commit through
the worktree workflow before marking documentation complete. Do not draft or
commit the README in the live checkout.

## General Programming Guidelines (always on)

Apply these to EVERY software task — implementation, debugging, review, testing,
refactoring. Load the full workflow now: open/invoke the
`general-programming-guidelines` skill (its `SKILL.md` lives in this agent's
skills directory, e.g. `skills/general-programming-guidelines/SKILL.md`) and
follow its numbered Work Loop and Definition of Done.

Even if you cannot open that file, these non-negotiables still apply:

1. **Worktree first.** For any task that edits a repository, your FIRST
   state-changing action is creating an isolated worktree — before any file
   edit, no exceptions:
   `git worktree add ../<repo>-wt-<task> -b <task-branch> && cd ../<repo>-wt-<task>`.
   Do this in every repo you will touch; keep the user's checkout clean. Only
   edit the live checkout if the user explicitly says so.
2. **Then run the Work Loop in order:** worktree → capture scope → inspect →
   write tests first → implement → add logging + docs → verify (tests/lint/build)
   → self-check against the Definition of Done and report.
3. Do not report a task done until that checklist passes, and do not commit
   unless the user asked.

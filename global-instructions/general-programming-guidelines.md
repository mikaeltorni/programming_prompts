## General Programming Guidelines (always on)

These apply to EVERY software task — implementation, debugging, review, testing,
refactoring — and they are not optional, not a fallback, and not overridden by a
project's own AGENTS.md.

**Worktree first.** For any task that edits a repository, your FIRST
state-changing action — reading first is fine, but before your first edit — is
to create an isolated worktree. No exceptions:

```
git worktree add ../<repo>-wt-<task> -b <task-branch> && cd ../<repo>-wt-<task>
```

Do this in every repo you touch; keep the user's checkout clean. Edit the live
checkout only if the user explicitly tells you to.

**Then run the whole task through this loop, in order:** worktree → capture
scope → inspect the code → write tests first → implement → add logging + docs →
verify (tests/lint/build) → self-check and report. Do not report a task done
until that passes, and do not commit unless the user asked.

For the full workflow and Definition of Done, also open the
`general-programming-guidelines` skill
(`skills/general-programming-guidelines/SKILL.md`) — but the two rules above hold
even if you never open it.

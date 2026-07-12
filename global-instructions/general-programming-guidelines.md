## General Programming Guidelines v1.8 (always on)

These are v1.8 MANDATORY instructions for EVERY software task — implementation, debugging, review,
testing, or refactoring. They are not optional, a fallback, or overridden by a
project's own instructions.

**Load the complete skill now.** Open/invoke and read every line of
`$general-programming-guidelines` (`skills/general-programming-guidelines/SKILL.md`)
before project-specific inspection. Do not skip, summarize, or defer it. The
installer embeds the complete skill body in this managed instruction block; use
that body when the native skill loader is unavailable.

**Worktree first.** For any task that edits a repository, the FIRST
state-changing action — before any edit — is an isolated worktree in every repo:

```
git worktree add ../<repo>-wt-<task> -b <task-branch> && cd ../<repo>-wt-<task>
```

Only edit the live checkout when the user explicitly says so.

**Then run the Work Loop in order:** worktree → capture scope → inspect → write
tests first → implement → add logging + docs → verify → self-check and report.
Do not report completion until the skill's Definition of Done passes. When a commit is
requested, commit in the worktree you are already working on — never in the user's live
checkout — and commit one self-contained feature at a time, keeping unrelated local
changes out. Do not commit unless the user asked, and never ask the user to commit for
you when they instructed you to commit.

## General Programming Guidelines v1.9.1 (always on)

These are v1.9.1 MANDATORY instructions for EVERY software task — implementation, debugging, review,
testing, or refactoring. They are not optional, a fallback, or overridden by a
project's own instructions.

**Load the complete skill now.** Open/invoke every line of
`skills/general-programming-guidelines/SKILL.md` before project work. Codex hosts:
`$general-programming-guidelines`; slash hosts (Claude Code, Cline, Grok):
`/general-programming-guidelines`; OpenCode: the `skill` tool. Do not skip it. The
installer embeds the complete skill body here when the native loader is unavailable.

**Worktree first.** For any task that edits a repo, the FIRST state-changing
action — before any edit — is an isolated worktree in EVERY repo, named
`<type>/<feature>` (branch + worktree dir), in the shared `.worktrees/` under the
repo family's parent — e.g. `projects/.worktrees/` — never inside the repo:

```
git worktree add ../.worktrees/<repo>-wt-<task> -b <task-branch> && cd ../.worktrees/<repo>-wt-<task>
```

Only edit the live checkout when the user explicitly says so.

**Then run the Work Loop in order:** worktree → capture scope → inspect → write
tests first → implement → add logging + docs → verify → self-check and report.
Do not report completion until the skill's Definition of Done passes. Commit your finished
work by default, without being asked — only in the worktree you are already on,
one feature at a time, separate commits per repo when the task spans repos.
Never commit in the live checkout, and never push, merge into the default
branch, or rewrite history unless the user asked.
## General Programming Guidelines v1.12.1 (always on)

These are v1.12.1 MANDATORY instructions for EVERY software task — implementation, debugging, review,
testing, or refactoring. They are not optional. Respect the repository's
`AGENTS.md` and `CLAUDE.md` first when present; then load and follow this skill.
Project files win on project-specific conflicts; this skill still owns the
shared Work Loop unless the project file explicitly narrows it.

**Load the complete skill now.** Open/invoke every line of
`skills/general-programming-guidelines/SKILL.md` before project work. Codex hosts:
`$general-programming-guidelines`; slash hosts (Claude Code, Cline, Grok):
`/general-programming-guidelines`; OpenCode: the `skill` tool. Do not skip it. The
installer embeds the complete skill body here when the native loader is unavailable.

**Worktree first — hard gates.** Before any edit, create an isolated worktree in
EVERY repo under the shared `.worktrees/` store (never inside the repo), named
`<type>/<feature>`, then prove cwd/branch before editing; follow-ups stay there:

```
git worktree add ../.worktrees/<repo>-wt-<task> -b <task-branch> && cd ../.worktrees/<repo>-wt-<task>
pwd   # MUST be .../.worktrees/...
git branch --show-current   # MUST be the task branch, not master/main
```

**Then run the Work Loop in order:** worktree → capture scope → inspect → **scan for Features** (always; one green commit per Feature) → tests first → implement → logging + docs → verify → **deliver after each Feature (commit in worktree, `git merge --no-ff` into master/main, always reapply)** → self-check. A worktree-only commit is not done. Never push or rewrite history unless asked. Local merge is required; "do not push" does **not** mean "do not merge."

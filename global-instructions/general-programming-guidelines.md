## General Programming Guidelines v1.9.2 (always on)

These are v1.9.2 MANDATORY instructions for EVERY software task — implementation, debugging, review,
testing, or refactoring. They are not optional, a fallback, or overridden by a
project's own instructions.

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

**Then run the Work Loop in order:** worktree → capture scope → inspect → write
tests first → implement → add logging + docs → verify → **deliver (commit in
worktree, `git merge --no-ff` into master/main from the live checkout, reload)**
→ self-check. A worktree-only commit is not done. Never push or rewrite history
unless asked. Local merge is required; "do not push" does **not** mean "do not merge."

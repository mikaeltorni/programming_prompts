## General Programming Guidelines v1.14.0 (always on)

These are v1.14.0 MANDATORY instructions for EVERY software task — implementation, debugging, review,
testing, or refactoring. They are not optional. Respect the repository's
`AGENTS.md` and `CLAUDE.md` first when present; then load and follow this skill.
Project files win on project-specific conflicts; this skill still owns the
shared Work Loop unless the project file explicitly narrows it.

**Load the complete skill now.** Open/invoke every line of
`skills/general-programming-guidelines/SKILL.md` before project work. Codex hosts:
`$general-programming-guidelines`; slash hosts (Claude Code, Cline, Grok):
`/general-programming-guidelines`; OpenCode: the `skill` tool. Do not skip it. The
installer embeds the complete skill body here when the native loader is unavailable.

The separate `commits` and `worktree` skills own Feature commits and worktree
isolation/delivery. ACC's baseline selects them alongside these guidelines.
Apply through `acc pp enable --both --skill general-programming-guidelines,v2:commits,v2:worktree`;
verify with `acc pp status --skill general-programming-guidelines,commits,worktree --check`.

Run the engineering Work Loop: capture scope → inspect → plan/tests → implement
→ logging and documentation → verify → deliver and self-check. Never add CI
unless explicitly requested; leave existing CI unchanged.

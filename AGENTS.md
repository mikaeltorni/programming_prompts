# Agent guidance for programming_prompts

## Never generate or commit marketplace files here

This repository is the **content source** only. Most workflows are standalone
plugins (one `plugins/<name>/` directory with `.codex-plugin/plugin.json`,
`.claude-plugin/plugin.json`, and exactly one `skills/*/SKILL.md`). Prompt-only
workflows live under top-level `skills/<name>/` and must not carry plugin
manifests.

Do **not** create, regenerate, or commit any marketplace catalog in this
repository — neither `.claude-plugin/marketplace.json` nor
`.agents/plugins/marketplace.json` nor any other `marketplace.json`. Marketplace
generation and plugin/CLI installation are owned exclusively by the sibling
[`linux_codex_claude_code_setup`](https://github.com/mikaeltorni/linux_codex_claude_code_setup)
repository, which reads these plugins from source. Adding marketplace files here
duplicates that ownership and drifts out of sync.

The plugin prompts remain fully functional standalone: each `plugins/<name>`
carries its own Codex and Claude manifests plus its single skill, so the
installer (or a manual `claude plugin`/`codex plugin` install pointed at a
plugin directory) can consume them without any repo-level marketplace catalog.


## Mandatory programming guidelines prompt

Every agent task in this repository must load the shared
`general-programming-guidelines` skill before the first file edit, using the
harness-native invocation for the runtime in use:

- Codex-family (`ca`, `qa`, `oa`, `na`, …): `$general-programming-guidelines`
- Claude Code, Cline, Grok: `/general-programming-guidelines`
- OpenCode: load `general-programming-guidelines` with the skill tool

Agent Command Center prepends this bare invocation to every dispatched prompt, so the
harness activates the skill before reading the task. When you start a task by hand, invoke it
yourself first. Then follow its Work Loop — dedicated worktree branch before
the first edit, tests, logging, documentation — and do not report the task done
until its Definition of Done checklist passes.
Always finish the delivery: commit in the worktree, merge into the default
branch with `git merge --no-ff`, then reload whatever consumes the change
(installer, skill deployment, service, session). You do not need to be asked.
Never push to a remote and never rewrite history unless the user explicitly
requests it.


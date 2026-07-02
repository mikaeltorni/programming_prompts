# Agent guidance for programming_prompts

## Stay in the current Git checkout

All programming agents must work only in the currently checked-out working tree
and branch. Never create, switch, or use another branch or Git worktree unless
the user explicitly requests it.

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

# Agent guidance for programming_prompts

## Never generate or commit marketplace files here

This repository is the **content source** only. It packages each workflow as a
standalone plugin (one `plugins/<name>/` directory with `.codex-plugin/plugin.json`,
`.claude-plugin/plugin.json`, and exactly one `skills/*/SKILL.md`).

Do **not** create, regenerate, or commit any marketplace catalog in this
repository — neither `.claude-plugin/marketplace.json` nor
`.agents/plugins/marketplace.json` nor any other `marketplace.json`. Marketplace
generation and plugin/CLI installation are owned exclusively by the sibling
[`linux_codex_claude_code_setup`](https://github.com/mikaeltorni/linux_codex_claude_code_setup)
repository, which reads these plugins from source. Adding marketplace files here
duplicates that ownership and drifts out of sync.

The plugins remain fully functional standalone: each `plugins/<name>` carries its
own Codex and Claude manifests plus its single skill, so the installer (or a
manual `claude plugin`/`codex plugin` install pointed at a plugin directory) can
consume them without any repo-level marketplace catalog.

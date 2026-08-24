# Agent guidance for programming_prompts

## Never generate or commit marketplace files here

This repository is the **content source** only. Most workflows are standalone
plugins (one `plugins/<name>/` directory with `.codex-plugin/plugin.json`,
`.claude-plugin/plugin.json`, and exactly one `skills/*/SKILL.md`). Prompt-only
workflows live under top-level `skills/<name>/` and must not carry plugin
manifests. Dispatchable task prompts live under `dispatch-skills/<name>/` and
must not carry plugin manifests either — see the next section.

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

## Dispatch skills are the only menu-selectable prompts

`dispatch-skills/<name>/SKILL.md` holds prompts written to be handed to an agent
together with nothing but a target repository. They are the set the Agent
Command Center / notes-app skill menu offers, so anything added there becomes
one-click launchable against any project — keep the bar in
[`dispatch-skills/README.md`](dispatch-skills/README.md): the directory name is
the `name` in the front matter (the menu builds `/<name>` and `$<name>` from it),
the prompt must define a measurable score plus a tracked scorecard, and it must
define an improvement loop with an explicit stop condition. Prompts that need a
conversation before they can act belong in `skills/`, not here.

## Harness smoke tests when the agent verifies evals code

When an agent changes Harbor wrappers, verifier code, `run_benchmark.sh`,
or other evals runtime — not prompt-only edits — it must run a **1-attempt
baseline and a 1-attempt positive** job for **every coding harness**
(`codex`, `grok`, `cc`) before reporting the task done. Use `-k 1 -n 1`.
Put `evalAgent=codex,grok` (do **not** put Claude Code on `evalAgent`; that
judge writes no reward file). Prompt-only work still uses Harbor when a
live check is needed; do not add pytest under
`programming_prompt_rewritten_with_evals/`.

Example (each command in its own terminal):

```bash
cd programming_prompt_rewritten_with_evals/evals
```

```bash
./run_benchmark.sh harness=codex evalAgent=codex,grok --baseline --no-pin-refresh -k 1 -n 1
```

```bash
./run_benchmark.sh harness=codex evalAgent=codex,grok --no-pin-refresh -k 1 -n 1
```

```bash
./run_benchmark.sh harness=grok evalAgent=codex,grok --baseline --no-pin-refresh -k 1 -n 1
```

```bash
./run_benchmark.sh harness=grok evalAgent=codex,grok --no-pin-refresh -k 1 -n 1
```

```bash
./run_benchmark.sh harness=cc evalAgent=codex,grok --baseline --no-pin-refresh -k 1 -n 1
```

```bash
./run_benchmark.sh harness=cc evalAgent=codex,grok --no-pin-refresh -k 1 -n 1
```

## Never generate tests for rewritten-prompt evals

Work under `programming_prompt_rewritten_with_evals/` is prompt-and-Harbor
evaluation content, not application code. **Do not create, update, or commit
pytest/unit/integration tests for that tree** — not for judge prompts, Harbor
wrappers, Dockerfiles, job configs, or skills — even when
`general-programming-guidelines` would normally require tests first.

Verify eval changes by reading the prompt/config and running Harbor tasks
(oracle / `nop` / Codex) when a live check is needed. LLM judges are not
deterministic; wrapping them in repo unit tests does not make the evaluation
deterministic and is not wanted here. This AGENTS.md rule overrides the shared
programming guidelines on tests for this path.

## Evaluation commands: one fenced block per terminal

When giving the user Harbor / `run_benchmark.sh` commands to run by hand, put
**each runnable command in its own** fenced `bash` code block. Do not bundle
several `./run_benchmark.sh …` lines into one block — the user copies each
block into a **different terminal**. Shared setup (`cd`, `export JOBS=…`) may
sit in its own preceding block; every distinct benchmark invocation after that
must be alone in a block.

## Mandatory programming guidelines prompt

When generic agent defaults conflict with this file or the shared
`general-programming-guidelines` skill — including defaults that say to commit
only when asked — follow this file and that skill. Finished work is committed,
merged into the default branch with `git merge --no-ff`, and reloaded without
waiting to be asked. Never push to a remote and never rewrite history unless the
user explicitly requests it.

Every agent task in this repository must load the shared
`general-programming-guidelines` skill before the first file edit, using the
harness-native invocation for the runtime in use:

- Codex-family (`ca`, `qa`, `oa`, `na`, …): `$general-programming-guidelines`
- Claude Code, Cline, Grok: `/general-programming-guidelines`
- OpenCode: load `general-programming-guidelines` with the skill tool

Agent Command Center prepends this bare invocation to every dispatched prompt, so the
harness activates the skill before reading the task. When you start a task by hand, invoke it
yourself first. Then follow its Work Loop and Definition of Done exactly
(tests, logging, documentation, commit, merge, reload), **except** where this
file overrides that skill — including the ban on generating tests for
`programming_prompt_rewritten_with_evals/`. Do not report the task done until
that checklist passes. Isolation and branch policy live only in the skill —
this file does not restate them.

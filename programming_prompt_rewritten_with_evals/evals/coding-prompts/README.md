# Coding task prompts

Each task Markdown file becomes a Harbor task through `../sync_tasks.sh`.
Required frontmatter names the artifact and describes the task:

```markdown
---
artifact: /app/calculator.py
description: Write a calculator.
---
Follow every provided programming skill. Write the requested program here.
```

The filename stem is the task name. `/app` is a symlink to `/Projects/app`
inside the trial image. Reference implementations live in `../oracles/`.
Edit these sources, not generated `.generated/tasks/` files.

The original request is the specification. Each capability sentence defines
one Feature; related commands and optional extras in that sentence stay
inside that Feature. The commits LLM judge derives the Features from the
request and inspects the actual Git history, diffs, and source at each commit.
No separate Feature-count field or source-token catalog is needed.

`sync_tasks.sh` copies the original request to `tests/task.md`. The shared
judge sync appends it to each LLM judge prompt. The coding agent's rewritten
README, commit subjects, and claimed completion do not replace that request.

`greeter-fix` supplies a broken greeter and failure logs. The logs are planted
under `.log/` in the workspace and preserved under `tests/task-logs/` for the
judge. The debug judge checks the reported behavior by inspecting and executing
the program; comments containing expected words do not demonstrate a fix.

Select tasks through the benchmark's canonical flags:

```bash
./run_benchmark.sh --harness codex --eval-agent codex --tasks bank,greeter-fix --skills commits,debug,worktree --no-pin-refresh -k 1
```

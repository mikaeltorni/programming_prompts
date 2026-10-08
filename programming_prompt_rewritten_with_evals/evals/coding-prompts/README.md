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

`todo`, `bank`, and `stats` exercise repeated codebase evolution through
separate capability sentences and a shared public contract. Later sentences
explicitly replace an earlier input or operation rule while preserving the
remaining behavior. The requests describe behavior; selected programming
policies supply planning and each feature's tests → code → commit cycle.
They do not duplicate that process in task-specific stage instructions.

Checks loading the current module follow its current contract. A fresh import
starts a new independent case; state persists between calls in that case, without
requiring in-memory migration across source revisions. The existing oracles
implement the final APIs. Optional clauses stay with their complete capability
sentence; setup/shared invariants do not introduce extra command features.

SRP scores function responsibilities and focused evolution from the actual
historical source and diffs. Commits scores the ordered capability boundaries,
including a requested rule's deliberate replacement in a later revision.

`sync_tasks.sh` copies the original request to `tests/task.md`. The shared
judge sync appends it to each LLM judge prompt. The coding agent's rewritten
README, commit subjects, and claimed completion do not replace that request.

`greeter` is the staged log-guided coding task evaluated with `debug_logs`. It supplies a broken greeter and
failure logs. The logs are planted under `.log/` in the workspace and
preserved under `tests/task-logs/` for the judge. The public entrypoint is
`run_greeter` in `/app/greeter.py`. It accepts `<name> <hour>` (match the
planted `want:` line), `bye <name>` (`bye=<name>`), and `period <hour>`
(`period=<phrase>`). The debug_logs judge checks the reported behavior by inspecting
and executing the program; comments containing expected words do not
demonstrate a fix.

Select tasks through the benchmark's canonical flags:

```bash
./run_benchmark.sh --harness codex --eval-agent codex --tasks todo,bank,stats --skills srp,commits,worktree -k 1
```

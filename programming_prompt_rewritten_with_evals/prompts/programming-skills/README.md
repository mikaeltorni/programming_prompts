# Programming skills

Each subdirectory is one injectable agent skill (`SKILL.md`) for Codex and/or
Claude Code. Real skills are scored by a matching judge under
`../../evals/judges/<name>/`. Control skills named `<base>-vague` inject a
one-line vague hint and are scored by `judges/<base>/` (no judge of their own).

Current skills:

| Directory | Focus |
| --- | --- |
| [`srp`](srp/SKILL.md) | Single-responsibility functions/methods; focused edits and simple incremental growth |
| [`commenting`](commenting/SKILL.md) | Docstrings with description, Parameters, Returns |
| [`logging`](logging/SKILL.md) | Plain `print` of parameters at entry and return value before exit |
| [`logging-vague`](logging-vague/SKILL.md) | Control: one vague “Use logging.” line; scored by the logging judge |
| [`worktree`](worktree/SKILL.md) | Project-prefixed sibling `.worktrees/<project>/<project>_<type>-<feature>` worktree, merge back, never push |
| [`commits`](commits/SKILL.md) | One working commit per capability sentence in the original request |
| [`testing`](testing/SKILL.md) | Contract-based regression checks, existing tooling, isolated execution, and honest verification evidence |
| [`debug_logs`](debug_logs/SKILL.md) | Explicit-only read-logs-first policy, pending numeric positive evidence |
| [`debug`](debug/SKILL.md) | Diagnose, reproduce, repair and verify logged failures |
| [`docs`](docs/SKILL.md) | README.md after the code: program, entrypoint, commands |
| [`workflow`](workflow/SKILL.md) | Explicit-only worktree → plan → per-feature tests/code/commit → docs |

**Logging eval note:** pair `logging` (or `logging-vague`) with `srp` so the
agent writes several helpers — otherwise a one-function script may not give
the logging judge enough entry/exit sites to score. Prefer
`--skills srp,logging` (or `srp,logging-vague`) without `--run-separately`.

**Worktree eval note:** pair `worktree` with `srp`. The worktree skill is scored
**programmatically** (git layout), not by an LLM judge. The task image starts as
`/Projects/app` with an empty initial commit; worktrees must live at
`/Projects/.worktrees/app/<dir>/`. `/app` is a symlink to `/Projects/app`.

**Commits eval note:** the LLM judge derives one Feature per capability
sentence from the original task, then maps each Feature to the first commit
that implements it. It reads diffs and complete relevant trees, excludes the
supplied seed, allows repair commits, and rejects bundling or history padding.
Output formatting is evaluated as behavior, not a source-spelling constraint.
The capability queue may use faithful summaries; cosmetic punctuation is not
a commit-policy failure. Each sentence still needs its own working commit.

**Debug eval note:** select `--skills debug --suite debug` to run the independent
broken-project cases in `evals/debug-prompts/`. The semantic judge reads original
logs and chronological coding traces; `debug_behavior` checks immutable public
calls against the repaired program. Selecting `debug` with coding skills includes
both task families by default, with only applicable skills on each family.
Unrelated-skill runs do not execute the new cases. Use `debug_logs` with `greeter`
to evaluate the preserved read-logs-first policy on the original staged task.

**Testing eval note:** the semantic judge assesses saved checks against the
original request with one `testing_contract` verdict: checks before each
capability, retained contract coverage, preservation/isolation and honest
execution evidence. No per-source-site question expansion or mandatory coverage
inventory is used. Existing evidence helpers remain available. It does not
require a framework, file name, or fixed test count.
Without an agent trace it reports execution order as unverified. Default
discovery includes `testing`; select it alone with `--skills testing` or add it
to the full suite.

**Docs eval note:** after the code, write `README.md` naming the public
`run_*` entrypoint and the commands. Function docstrings stay on the
commenting skill.

**Workflow eval note:** `workflow` is marked `.opt-in`, so default skill
discovery and older benchmark commands do not inject or judge it. Select it
explicitly with `--skills workflow` or include it in a comma-separated list.
Its semantic judge checks the repository-local Markdown plan, phase order, and
conditional companion routing.

Add a new skill by creating `programming-skills/<name>/SKILL.md` and
`evals/judges/<name>/prompt.md` (+ `judge.toml`). For a vague control only,
add `programming-skills/<name>-vague/SKILL.md` and reuse `judges/<name>/`.
Add a `.opt-in` marker when default discovery must exclude a real skill while
keeping explicit `--skills <name>` support. The benchmark runner auto-discovers
the remaining non-`*-vague` skill directories; pass controls and opt-in skills
explicitly via `--skills`.

Judges emit a short `reasoning` string per criterion; the verifier stores it
in `reward-<skill>-details.json` / `reward-details.json`, and the runner
prints it after each job. To double-check a positive vs baseline pair under
`evals/runs/`, use [`../../evals/testing/`](../../evals/testing/).

Workflow plans retain four outer stages and seven microstep columns:
`Step | Phase | Feature | Stage | Action | Status | Evidence`. Each feature
finishes 3.1 saved checks and baseline, 3.2 implementation and cumulative checks,
then 3.3 working commit and required delivery before the next feature starts.
Documentation follows all feature cycles. The workflow prompt owns the cycle
with or without companions; those companions add their detailed requirements.
Default discovery excludes both `workflow` and `debug_logs`; either remains
explicitly selectable with `--skills`.

## Policy and judge alignment

Policies describe the required work; their judges score those same requirements.
Do not add an unselected companion's artifacts or turn a partial transcript into
an order failure. Current checks use current rules; earlier rules are assessed at
their actual historical revisions. Query upgrades to retained rejection bodies
belong to that query's own checks-before-code step. Distinct arithmetic/state
updates are not duplicated decisions merely because they share storage.

The October 10, 2026 simplification passed static content validation and isolated
instruction assembly/judge packaging. Benchmark performance is unverified for
this revision; original archived verdicts remain unchanged. Its testing detail
schema is one criterion rather than historical expanded subquestions.

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
| [`prompt_engineering`](prompt_engineering/SKILL.md) | Prompt Markdown engineering: simple instructions, paired judge edits and real model evaluations |
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

**Testing eval note:** the semantic judge gives one `testing_contract` verdict
for ordinary tests: correct public results, relevant errors, stateful preservation
and isolation, and actual final execution. Plain-assertion runners count.
No sentence-cycle chronology, special helper, feature ledger, framework, file name
or fixed test count is required. Default discovery includes `testing`; select it
alone with `--skills testing` or include it in the full suite.

**SRP eval note:** SRP v0.0.62 establishes the parser/operation/validator layout
before the first application write. The judge requires parsing/dispatch, domain
validation and shared decisions to all pass. Converted-value/resource rules
belong in called validators, operations own calculations and stored mutations,
and dispatch forwards converted arguments unchanged. Direct stored reads and
formatting need no getter; assigning stored state remains mutation even if a
helper computes the replacement.

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
Default discovery excludes `workflow` and `debug_logs`; both remain explicitly
selectable with `--skills`. It includes `prompt_engineering` for the two prompt
cases only, with separate policy/judge routing inside the same shared job.

## Policy and judge alignment

Policies describe the required work; their judges score those same requirements.
Do not impose an unselected companion's workflow requirements. The testing judge
assesses final ordinary tests and their actual execution; workflow and commits
remain separately selectable policies. Historical benchmark verdicts stay intact
when a policy changes, and scores from different rubrics are not directly comparable.

The October 18 ordinary-testing revision v0.1.115 scored 32/32 on the full
eight-task, four-attempt sample, with no quota or infrastructure failures.
Its judge passed 21/21 focused controls, preserving the original 15 expected
verdicts. It grades actual assertions against the final revised contract and
accepts equivalent state-preservation evidence, including copied snapshots.
Testing keeps one criterion and adds no workflow or test matrix. The root README
records the archive, actual execution evidence and earlier failures.

The larger v0.1.115 sample `2026-10-18_174108_2620297` recorded 75/80.
Revision v0.1.116 subsequently scored 76/80 in user-run archive
`2026-10-18_175752_3673349`, with no terminal trial errors. Its four failures concern
obsolete rejection expectations, a specified empty result, partial public-entrypoint
coverage and unasserted malformed-input errors. Revision v0.1.117 addresses these
causes with aligned judge guidance that credits actual assertions and avoids
unrequested state variants. The existing framework remains unchanged.

The user's v0.1.117 run `2026-10-18_180956_273001` scored 39/40 with no terminal
trial errors. The remaining bank trial corrected only part of a shared stale
rejection table and stopped after another failed run; its NO is justified and
preserved. Revision v0.1.118 reviews all affected cases and identifies failing
loop inputs. Its next user-run archive `2026-10-18_183646_1834400` recorded 61/64
with no terminal trial errors: two missing whole-transfer success checks and one
suite without malformed-input assertions. A nearby YES also lacks the claimed
whole-transfer witness, so the raw score does not independently establish policy
compliance. All original verdicts remain unchanged.

Candidate v0.1.119 clarifies explicitly retained input classes and reviews missing
assertions even in green suites. Its judge requires actual class witnesses. The
revised prompt-fixing policy was applied to these changes; both candidates are
unverified because the user prohibits testing. No runtime/framework changes.

The subsequent archive `2026-10-18_184759_2545890` recorded 65/72: four genuine
coverage failures and three unsupported NOs. Focused v0.1.120 archive
`2026-10-18_191826_143824` recorded 3/4, still missing whole-transfer success.
Current v0.1.121 makes whole/fraction success explicit per affected operation.
The shorter judge follows actual public calls, credits classes within mixed
sequences and applies final domain rules. An unproven assertion-summary runtime
experiment was discarded. No runtime/framework change is delivered. The latest
no-test instruction leaves this candidate and judge unverified.

## Prompt engineering

`prompt_engineering` is optional in runtime defaults: invoke it by name when
creating or editing AI instructions, including skills and judges. Benchmark
defaults include its two prompt cases; `--skills prompt_engineering` selects only
those cases. They receive only this policy and its judge. **Do not overcomplicate.** Keep prompts
short, reuse the simplest existing evaluation, and add machinery only for a
demonstrated need. Read original failures, make a causal repair and keep prompt
and judge aligned. Save actual main-model answers and model-judge decisions,
assert independent expectations and wrong controls, and inspect their evidence.
Finish the full requested evaluation. Exact correctness cases and judge controls
must match expectations; sampled benchmark errors are reported, with no unasked
100% requirement. Report execution blockers honestly.

Refresh with `acc pp enable -v2 --skill prompt_engineering`; verify using
`acc pp status -v2 --skill prompt_engineering --check`. Select
`prompt-create,prompt-repair` for its two Harbor cases; see the
[case catalog](../../evals/coding-prompts/README.md#prompt-engineering-cases).

Revision v0.0.66 submits the tested prompt text in actual calls and treats ignored
model settings as unverified. Its two-task Codex evaluation passed 2/2 and its
judge controls passed 5/5, using `gpt-6-luna`/low on instance 2 with no quota or
infrastructure exclusions. The root README records the archive and case counts.

Candidate v0.0.67 checks recurring failures against prior repairs and nearby YES
witnesses, replaces ineffective wording and explicitly defers execution when the
user prohibits it. It was applied to testing v0.1.119. No tests or model calls were
run for this candidate; the previous v0.0.66 results do not verify it.

Current v0.0.68 and its paired judge add gradual `k` growth only after the current
sample meets requested criteria and all independent judge controls match. Keep
the candidate/model/settings/harness fixed during growth, repair failures before
growing and finish requested coverage. Exact-case/no-test exceptions remain.
Applied to the repair above: stop growth on failures and discard the unproven
runtime addition. This revision remains unverified under the no-test instruction.

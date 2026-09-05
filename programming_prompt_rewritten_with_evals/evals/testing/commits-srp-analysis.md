# Commits/SRP archive analysis — 2026-09-05

The latest completed targeted jobs are the September 4 bank/stats runs below.
Both used Codex with a Codex judge, 15 attempts per task, and both skills
injected into each coding session. Separate mode changes reward aggregation;
it does not isolate skill injection or increase the workload.

| Run stamp | Scoring | Completed | Commits | SRP | Both skills pass |
| --- | --- | ---: | ---: | ---: | ---: |
| `2026-09-04_120217_1664168` | Independent | 30 | 30/30 | 30/30 | 30/30 |
| `2026-09-04_120243_1710001` | Combined | 30 | 29/30 | 29/30 | 28/30 |

Read sources: each run's `harbor/<job>/result.json`, `job.log`, per-trial
`verifier/reward-commits-details.json`, `reward-srp-codex-details.json`,
`agent/codex.txt`, and archived `Projects/<trial>/app/` source and history.
The runs live under `evals/runs/` with the stamp followed by descriptive flags.
Both job results report zero errors, retries, cancellations, and pending trials;
neither summary reports rate limits. These are scored model outcomes.
The `120208` all-skills directory has only prepared tasks and no completed
job result; it is not another scored run.

In independent mode the top-level reward indicates scoring completed, even
when a skill fails. The per-skill rewards above were checked directly. These
are different random trials, so the difference between the two runs is not
proof that the aggregation flag causes worse code.

## Commits: incorrect ledger before implementation

Combined trial `bank__untkkFk` explicitly claimed the request had three
capability sentences and planned opening; deposits/withdrawals; then
transfers/history/assets. The task actually has four separate capability
sentences. The final reporting sentence includes the optional assets command;
it is separate from the preceding transfer sentence.

The transcript loaded the current pre-edit commits prompt, including the
sentence-count rule. This is a residual failure after the earlier count fix,
not a run of the old "about 3 Features" prompt. It did not produce the required
source-mapped ledger before coding. Its actual history was:

- `5ea002a` — Add account opening
- `1860f9b` — Add deposits and withdrawals
- `4cecb19` — Add transfers and account reports

No failed search skipped a commit in this trial. The agent implemented its
incorrect plan faithfully. The checker correctly rejected three Python
Feature commits where four were required; SRP passed for this trial.

The archived `.git/config` contains redacted boolean values, so it cannot be
read directly by Git. Copies under the task worktree's `.generated/audit-commits/`
restored only those config booleans, leaving source, refs, objects, and the
original archive untouched. Replaying the real checker reproduced the failure.
The same replay accepted the other failed trial's four-Feature history.

The revised prompt requires copying each capability sentence verbatim into a
ledger entry, accounting for all sentences before deriving the count, and
recording a verified commit beside each entry. The staged tree is checked
against the next entry, particularly the final adjacent pair. No example
Feature counts or task-specific capability lists remain.

It also corrects two misleading rules: earlier Features remain in later
Python trees, and the checker matches sequential capability markers rather
than fixed commit positions. An extra focused repair does not consume the
next Feature's slot. The independent commit command and HEAD verification
remain, preserving the earlier protection against skipped commits.

## SRP: a guard depends on application state

Combined trial `bank__cZTzNBv` correctly made four Feature commits. Its
`run_bank` deposit/withdraw branch checked `name not in _accounts` before
calling a core helper. The check depends on current application state and
belongs with account lookup/validation in the core helper. Argument-count
checks in that same entrypoint are input-shape checks and may remain there.
The judge correctly rejected the state-dependent guard; commits passed.

The transcript initially tried two missing aliased skill paths, then loaded
the actual skills successfully. The failure is not an absent prompt. The
pre-edit SRP prompt prohibited state validation only in its converted-token
bullet, while broadly allowing guards elsewhere. That leaves a misleading
allowance for a membership check on an unconverted string.

Earlier all-skills archives explain why the existing conversion restriction
must remain: combined run `2026-09-04_110453_954805` failed todo trials
`todo__qYf6k8E` and `todo__oub8RGw` for entrypoint index arithmetic; independent
run `2026-09-04_110517_989702` failed `counter__KkBFhfA` for a state assignment
in the entrypoint. Those older failures do not explain the latest membership
check by themselves.

## Commits revision verification

Live positive run `2026-09-05_083824_179542`, from the isolated worktree,
used Codex/Codex, commits+SRP, bank+stats, combined scoring, `-k 1`, and
`--no-pin-refresh`. Both trials passed both skills. The actual histories
contained four separate Python Feature commits with sequential markers
matched: `bank__zVvDQ3k` and `stats__Ycbx3gy`. The judge confirmed thin public
entrypoints. The agent messages still summarized the ledger instead of
quoting every sentence; this smoke establishes correct delivery on these
attempts, not perfect compliance with every instruction or a measured
improvement in the failure rate. Skill frontmatter validation and diff checks
also passed.

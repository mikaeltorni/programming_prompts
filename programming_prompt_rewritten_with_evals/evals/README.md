# Harbor evaluation

Write-from-scratch tasks and a log-driven greeter fix measure whether Codex,
Claude Code, and/or Grok follow selected programming skills while implementing
tiny Python programs. Each original request defines its own capabilities; the
commits judge derives Features from that request rather than from a separate
marker or count file:

| Prompt | Entrypoint |
| --- | --- |
| [`coding-prompts/calculator.md`](coding-prompts/calculator.md) | `/app/calculator.py` → `run_calculator` (`add`, `sub`, `mul`, `div`) |
| [`coding-prompts/todo.md`](coding-prompts/todo.md) | `/app/todo.py` → `run_todo` (`add`, `list`, `done <n>`, `clear`) |
| [`coding-prompts/counter.md`](coding-prompts/counter.md) | `/app/counter.py` → `run_counter` (`inc`, `dec`, `get`, `set`) |
| [`coding-prompts/greeter.md`](coding-prompts/greeter.md) | `/app/greeter.py` → `run_greeter` (fix from `.log/`, `bye`, `period`) |
| [`coding-prompts/temperature.md`](coding-prompts/temperature.md) | `/app/temperature.py` → `run_temperature` (`c2f`, `f2c`, Kelvin conversion) |
| [`coding-prompts/shop.md`](coding-prompts/shop.md) | `/app/shop.py` → `run_shop` (`add`, `total`, `remove`) |
| [`coding-prompts/bank.md`](coding-prompts/bank.md) | `/app/bank.py` → `run_bank` (`open`, `deposit`/`withdraw`, `transfer`, `history`) |
| [`coding-prompts/stats.md`](coding-prompts/stats.md) | `/app/stats.py` → `run_stats` (`add`, `mean`, `low`/`high`, `median`) |

Each coding prompt is the product instruction (what to build) plus “Follow the
provided programming skill.” Skills under
[`../prompts/programming-skills/`](../prompts/programming-skills/) guide *how*
to write it. Each skill has its own judge under [`judges/<skill>/`](judges/).

## Repeated build/edit tasks

`todo`, `bank`, and `stats` start from a small working program, then alternate
new capabilities with revisions to earlier behavior:

| Task | Earlier behavior revised |
| --- | --- |
| `todo` | Single-word items become normalized multi-word text; completing the oldest item becomes indexed completion. |
| `bank` | Deposits and withdrawals expand from whole numbers to decimals; transfers subsequently undergo the same change. |
| `stats` | Sample input expands from whole numbers to decimals; the mean later changes from truncation to actual arithmetic precision. |

Each task requires checking and committing the current working stage before
implementing the next. Check sequences use a fresh module per sequence and
preserve state between calls within it. Later-stage behavior must remain
unavailable until its stage; an explicit replacement retires only the affected
earlier rule. These examples clarify capability sentences rather than creating
extra Features. The other coding tasks retain shorter growth patterns.

The SRP judge receives the reachable Git graph, actual diffs, and historical
Python source through the same evidence helper as commits. It assesses focused
functions throughout the revisions and unnecessary changes, allowing justified
local extractions without a line-count or function-count budget. The commits
judge checks each rule in its own revision and preserves unaffected contracts
when a later sentence intentionally changes an earlier rule. Final oracle
solutions cover the final API; they are not staged-history examples.

## Programming suite

The suite contains `workflow`, `commits`, `worktree`, `docs`, `srp`,
`commenting`, `logging`, `debug_logs`, `debug`, and `testing`. Default discovery
includes the companions other than `workflow`, which requires explicit selection.
`logging-vague` is an opt-in control; shipped presets retain their explicit
skill lists. Sources live in [../prompts/programming-skills/](../prompts/programming-skills/README.md);
[judges/README.md](judges/README.md) describes their evaluators.

`debug_logs` preserves the existing read-logs-first instruction and is evaluated
on the coding family, including the staged greeter repair. `debug` uses the
separate [repair scenarios](debug-prompts/README.md): `debug-clock`,
`debug-catalog`, and `debug-stock`. Default task selection depends on the selected
skills: `debug` alone runs repair tasks; coding skills alone run coding tasks;
a mixed selection runs both families concurrently in one Harbor job per
harness, from one console. The shared concurrency ceiling, Docker reservation
and automatic launch guard apply across both families. Every trial still
receives its own applicable instruction document and judges: repair trials
inject and score only `debug`, plus the functional
`debug_behavior` verifier. Other skills never run on these dedicated scenarios.
Both baseline and positive jobs use the same family routing.
The existing mixed-skill command needs no extra flag or second console.
Run baseline and positive wrapper invocations sequentially; a configured
capacity limit can reduce how many trials overlap.

[Testing](../prompts/programming-skills/testing/SKILL.md) requires meaningful
saved checks against the requested behavior using existing project tooling.
Bug fixes should show a failing regression before the repair and a passing
check afterward when practical. Static content uses direct verification and
repository-specific test restrictions take precedence. The
[testing judge](judges/testing/prompt.md) assesses this evidence semantically,
without task markers, expected test counts, or prescribed filenames.
It resolves later contract replacements before auditing retained assertions,
traces each expected value from its own fixture and preceding calls, and checks
actual validation paths, preservation after rejection, and fixture isolation.
Argument shape, numeric conversion, and domain failures are distinct coverage
classes. Representative checks may cover commands that share the same executed
validation path; independent paths still need coverage even when the runner
passes. Historical checks are judged at their committed contract rather than
requiring superseded rejections in the final suite.

Selecting `workflow` or `commits` with `--skills` explicitly invokes each selected
skill in the isolated job task prompt and lists the selected programming skills.
Commits-only runs invoke `$commits` without enabling `$workflow`. Their prompt
directs the agent to the supplied skill-catalog paths outside the repository,
explicitly authorizes the local Git commits required by the commits skill, and
explains that `/app` is a symlink to `/Projects/app`; requested absolute paths
must resolve into that checkout rather than a nested `app/` directory.
The canonical coding prompts remain unchanged. Baseline and positive jobs
receive the same selection context, while baselines do not install the selected
skill bodies. The workflow judge receives the delivered task prompt, so its
optional-companion decision uses the selection the agent saw.

Workflow is invoked explicitly when selected. It coordinates independently
selected companions and keeps one four-row `## Tasks` table in the launch
project's `tmp/workflow.md`: `Plan`, `Establish worktree`, `Write code`, and
`Write documentation`. Testing runs inside implementation rather than adding
a workflow phase. If commits is selected, its original capability ledger
keeps distinct introducing commit references beside the source sentences.

Worktree and docs judges are programmatic. Commits, debugging, testing, and
the other skill judges use semantic evidence from the original request,
repository, and available logs. Generated task trees under `.generated/tasks/`
contain runtime copies; edit the authoritative prompts and judge definitions.

## Run a benchmark

[run_benchmark.sh](run_benchmark.sh) is the supported entrypoint. It refreshes
stable CLI versions, prepares tasks, runs Harbor, summarizes the results,
and archives jobs under `runs/`. Docker and the installed Harbor environment
are required. Run only one benchmark at a time on this machine.

```bash
cd /home/mk/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
```

A focused positive check:

```bash
ACC_CODEX_INSTANCE=2 ./run_benchmark.sh --harness codex --eval-agent codex --skills workflow,testing,debug_logs --tasks greeter -k 1
```

A baseline injects no skill bodies but keeps the selected judges:

```bash
ACC_CODEX_INSTANCE=2 ./run_benchmark.sh --harness codex --eval-agent codex --skills workflow,testing,debug_logs --tasks greeter --baseline -k 1
```

Wait for each command to finish before starting the next. Use the account
instance intended for the run. Account resolution honors `ACC_CODEX_INSTANCE`
first, then the persisted ACC selection; confirm the startup account path and
credit probe before accepting results.

Only the new debugging scenarios:

```bash
ACC_CODEX_INSTANCE=1 ./run_benchmark.sh --harness codex --eval-agent codex --skills debug --suite debug -k 3
```

A focused repair case is selected with `--tasks debug-clock`. To combine a coding
check with a repair check, select `--skills testing,debug --tasks counter,debug-clock`.
Omitting both task selectors includes all tasks applicable to the selected skills.
`--suite coding`, `--suite debug`, and `--suite all` choose a family explicitly.

The full positive suite on cx1:

```bash
ACC_CODEX_INSTANCE=1 ./run_benchmark.sh --harness codex --eval-agent codex --skills workflow,commits,worktree,docs,srp,commenting,logging,debug,testing -k 3
```

## Parameters

Use long kebab-case flags followed by values. Historical `harness=`,
`evalAgent=`, `-skills=`, and camel-case spellings are rejected.

| Parameter | Meaning |
| --- | --- |
| `--harness codex` | Coding harness; supported alternatives include `cc` and `grok`. Omission runs Codex and Claude Code. |
| `--eval-agent codex` | LLM judge. Repository test runs always select Codex explicitly. |
| `--skills workflow,testing,debug` | Skills to inject and score; omission selects the default suite. |
| `--tasks greeter` | Named task subset; omission uses the applicable selected suite. |
| `--suite debug` | Family: `coding`, `debug`, or `all`; omission derives families from selected skills. |
| `--baseline` | No skill injection, retaining selected judges. |
| `--run-separately` | Independent skill scores in the same job and trial count, instead of requiring every judge to pass. |
| `--install-only` | Prepare and verify CLI installation without an LLM coding run. |
| `--eval-agent-model MODEL` | Explicit judge model override. |
| `--eval-agent-reasoning-effort low` | Explicit judge effort override. |
| `-k 3` | Harbor attempts per task. Other unowned flags pass through to Harbor. |

Normal commands omit pin options and concurrency limits. Without an explicit
pin option the wrapper checks stable versions; without a concurrency option it
requests selected trials subject to configured capacity and automatic launch
pacing. `EVAL_JUDGE_WORKERS` controls parallel judge workers (default four).
Do not add a second judge unless the user explicitly requests it.

## Automatic launch pacing

Every wrapper invocation installs the Harbor job plugin
[`DeadlineLaunchGuard`](harbor_agents/launch_guard.py). It applies to all coding
harnesses, positive/baseline jobs and install-only runs, without adding a flag to
the user's command. The guard immediately permits the full existing trial ceiling,
subject to configured LLM and Docker capacity limits. There is no four-trial
starting cap, gradual ramp-up or persistent halving of capacity. Each admitted
trial holds its slot through setup, coding, verification and cleanup.

The guard measures admission-to-first-agent-start setup time and keeps the latest
64 samples for the current job. Deadline headroom is their nearest-rank 95th
percentile plus the five-second polling interval. Before any sample exists,
headroom is five seconds. New containers wait only when a running agent's actual
remaining execution time is within this headroom. For example, a measured setup
p95 of 20 seconds yields 25 seconds of headroom, so a 600-second agent budget
blocks new starts after 575 seconds rather than a fixed 480-second threshold.
This is a launch-cost heuristic; it does not estimate unfinished coding work or
prove concurrency caused a timeout. The guard honors the existing
agent timeout override, maximum and multiplier. Waiting uses Harbor's START
hook before environment setup; the agent timer starts later at AGENT_START.
Each queued trial therefore gets its own full execution budget after admission.
Deadline pressure is rechecked before every admission and at least every five
seconds while a trial is queued.

When the near-deadline agent phase ends, the hold clears immediately and queued
trials may use all available slots. Completed slow trials and exceptions do not
permanently reduce capacity; Harbor's existing rate-limit retry backoff remains
in effect. Running trials continue; results, retries and timeout budgets are
preserved. Admission is released on END or cancellation, using each attempt's
ID so retries cannot reuse an old permit. This guard affects queued launches;
it cannot reduce a batch that has already started at the full ceiling.

The job log contains `Automatic launch guard:` lines for admission, queueing,
setup durations, computed headroom and near-deadline trial names with remaining
seconds. Pacing is local to the job; continue to run one wrapper at a time.
It avoids additional launch work near deadlines but cannot predict how much work a
particular task still needs or guarantee completion within its own deadline.
Account usage quotas remain separate from these per-trial wall-clock limits.

## Read the evidence

Each archive includes job logs, trial agent transcripts, verifier outputs,
reward details, and saved project files. `runs/RESULTS.txt` is a summary,
not sufficient evidence by itself. Inspect the job diagnosis and a failed
trial before treating zeros as model results. Rate limits, exhausted credits,
Docker start failures, and missing evidence are infrastructure limits rather
than prompt compliance findings. Runs with rate-limited trials are unsuitable
for score comparisons. Empty Python source listings support a missing-submission
verdict; naming the requested file alone does not make that an infrastructure error.
A non-inspection verdict or a nonexistent path cited against a nonempty listing
is retried once within the judge timeout.

Temporary analysis reports belong under `tmp/reports/`. Do not commit generated
tasks, runtime artifacts, or add pytest suites in this evaluation tree.
Prompt-only changes use direct consistency checks and focused Harbor runs.
Runtime wrapper or verifier changes additionally require baseline and positive
smoke jobs for every supported coding harness under the root AGENTS.md rules.

From `evals/`, `bash lib/self_test_skills.sh` checks discovery, one-job scheduling
for mixed and single-family selections, family-specific instruction documents
and judges, and native registration for all three runtimes in temporary homes.
It also checks baseline clearing, legacy bundles, missing trial identities,
and `--run-separately` scoring. It makes no Docker, GUI or LLM calls. For live
mixed-family smoke runs, inspect each trial's archived `agent_execution` times
to confirm overlap and its verifier outputs to confirm family-specific scoring.

## Debug fixture verification

`python3 verify_debug_fixtures.py` executes each broken seed against immutable
public calls, compares reported failures with original `seeds/<case>/log/failure.log`,
and verifies the reference repair twice in fresh processes. Missing/stale logs,
non-failing reported cases, and failing references stop materialization. Use
`--refresh-logs` only to intentionally replace a capture; `--root PATH` verifies
an alternative fixture tree. The default never rewrites the original evidence.

`sync_tasks.sh [TASK ...]` materializes only named tasks when supplied; ordinary
coding runs do not certify or materialize repair fixtures. Original logs become
project-root `.log/failure.log` and verifier-owned `tests/task-logs/failure.log`.
The skill gives no scenario paths or implementation hints. Each JSON contract
in `debug-cases/` defines public calls and independent results/exceptions; stock
and catalog rejection sequences observe affected state before another operation.

`debug_behavior` runs all contract sequences in fresh subprocesses with timeouts,
independently of the semantic verdict. Its reward and public observations are
archived in `reward-debug_behavior.json` and `reward-debug_behavior-details.json`.
The semantic `debug` judge receives bounded original logs and chronological
coding transcripts for Codex, Claude Code and Grok. Large events and omissions
are marked; absent traces leave reading order unverified. Authentication or
provider failures remain infrastructure exclusions rather than repair scores.

# Harbor evaluation

Write-from-scratch tasks and a log-driven greeter fix measure whether Codex,
Claude Code, and/or Grok follow selected programming skills while implementing
tiny Python programs. Each original request defines its own capabilities; the
commits judge derives Features from that request rather than from a separate
marker or count file:

| Prompt | Entrypoint |
| --- | --- |
| [`coding-prompts/calculator.md`](coding-prompts/calculator.md) | `/app/calculator.py` → `run_calculator` (`add`, `sub`, `mul`, `div`) |
| [`coding-prompts/todo.md`](coding-prompts/todo.md) | `/app/todo.py` → `run_todo` (`add`, `list`, `done`) |
| [`coding-prompts/counter.md`](coding-prompts/counter.md) | `/app/counter.py` → `run_counter` (`inc`, `dec`, `get`, `set`) |
| [`coding-prompts/greeter.md`](coding-prompts/greeter.md) | `/app/greeter.py` → `run_greeter` (`hello`, hour-based greeting, `bye`) |
| [`coding-prompts/temperature.md`](coding-prompts/temperature.md) | `/app/temperature.py` → `run_temperature` (`c2f`, `f2c`, Kelvin conversion) |
| [`coding-prompts/shop.md`](coding-prompts/shop.md) | `/app/shop.py` → `run_shop` (`add`, `total`, `remove`) |
| [`coding-prompts/greeter-fix.md`](coding-prompts/greeter-fix.md) | `/app/greeter.py` → `run_greeter` (fix from `.log/`, `bye`, `period`) |
| [`coding-prompts/bank.md`](coding-prompts/bank.md) | `/app/bank.py` → `run_bank` (`open`, `deposit`/`withdraw`, `transfer`, `history`) |
| [`coding-prompts/stats.md`](coding-prompts/stats.md) | `/app/stats.py` → `run_stats` (`add`, `mean`, `low`/`high`, `median`) |

Each coding prompt is the product instruction (what to build) plus “Follow the
provided programming skill.” Skills under
[`../prompts/programming-skills/`](../prompts/programming-skills/) guide *how*
to write it. Each skill has its own judge under [`judges/<skill>/`](judges/).

## Programming suite

The suite contains `workflow`, `commits`, `worktree`, `docs`, `srp`,
`commenting`, `logging`, `debug`, and `testing`. Default discovery includes
the eight companions; `workflow` requires explicit selection. `logging-vague`
is an opt-in control. Sources live in [../prompts/programming-skills/](../prompts/programming-skills/README.md);
[judges/README.md](judges/README.md) describes their evaluators.

[Testing](../prompts/programming-skills/testing/SKILL.md) requires meaningful
saved checks against the requested behavior using existing project tooling.
Bug fixes should show a failing regression before the repair and a passing
check afterward when practical. Static content uses direct verification and
repository-specific test restrictions take precedence. The
[testing judge](judges/testing/prompt.md) assesses this evidence semantically,
without task markers, expected test counts, or prescribed filenames.

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
ACC_CODEX_INSTANCE=2 ./run_benchmark.sh --harness codex --eval-agent codex --skills workflow,testing,debug --tasks greeter-fix -k 1
```

A baseline injects no skill bodies but keeps the selected judges:

```bash
ACC_CODEX_INSTANCE=2 ./run_benchmark.sh --harness codex --eval-agent codex --skills workflow,testing,debug --tasks greeter-fix --baseline -k 1
```

Wait for each command to finish before starting the next. Use the account
instance intended for the run. Account resolution honors `ACC_CODEX_INSTANCE`
first, then the persisted ACC selection; confirm the startup account path and
credit probe before accepting results.

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
| `--tasks greeter-fix` | Task subset; omission selects every coding task. |
| `--baseline` | No skill injection, retaining selected judges. |
| `--run-separately` | Independent skill scores in the same job and trial count, instead of requiring every judge to pass. |
| `--install-only` | Prepare and verify CLI installation without an LLM coding run. |
| `--eval-agent-model MODEL` | Explicit judge model override. |
| `--eval-agent-reasoning-effort low` | Explicit judge effort override. |
| `-k 3` | Harbor attempts per task. Other unowned flags pass through to Harbor. |

Normal commands omit pin options and concurrency limits. Without an explicit
pin option the wrapper checks stable versions; without a concurrency option it
requests selected trials subject to configured capacity. `EVAL_JUDGE_WORKERS`
controls parallel judge workers (default four). Do not add a second judge
unless the user explicitly requests it.

## Read the evidence

Each archive includes job logs, trial agent transcripts, verifier outputs,
reward details, and saved project files. `runs/RESULTS.txt` is a summary,
not sufficient evidence by itself. Inspect the job diagnosis and a failed
trial before treating zeros as model results. Rate limits, exhausted credits,
Docker start failures, and missing evidence are infrastructure limits rather
than prompt compliance findings. Runs with rate-limited trials are unsuitable
for score comparisons.

Temporary analysis reports belong under `tmp/reports/`. Do not commit generated
tasks, runtime artifacts, or add pytest suites in this evaluation tree.
Prompt-only changes use direct consistency checks and focused Harbor runs.
Runtime wrapper or verifier changes additionally require baseline and positive
smoke jobs for every supported coding harness under the root AGENTS.md rules.

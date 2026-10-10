# Judges

Each skill has one directory. Edit the canonical prompt and configuration here;
`../sync_judges.sh` copies them into generated Harbor task verifier directories.
All LLM judges receive the original coding request through the shared sync path.

| Skill | Scorer | Evidence |
| --- | --- | --- |
| `srp` | LLM `prompt.md` | parsing, core helpers, and entrypoint responsibilities |
| `commenting` | LLM `prompt.md` | the selected docstring contract |
| `logging` | LLM `prompt.md` | the selected entry/exit tracing contract |
| `commits` | LLM `prompt.md` | capability sentences mapped to distinct working commits, using diffs and source trees |
| `workflow` | LLM `prompt.md` | worktree-before-plan startup, four outer rows and consecutive tests/code/commit cycles |
| `testing` | LLM `prompt.md` | checks saved/run before each feature, contract coverage, isolated execution and explicit evidence limits |
| `debug_logs` | LLM `prompt.md` | preserved log-first policy on coding tasks, including greeter |
| `debug` | LLM `prompt.md` | original failures, causal repair and chronological coding evidence on dedicated scenarios |
| `debug_behavior` | programmatic public calls | immutable results/exceptions, boundaries and preserved state across rejection sequences |
| `worktree` | programmatic | project-prefixed `<project>_<type>-<feature>` worktree layout, merge, and remote policy |
| `docs` | programmatic | README documents the program and public entrypoint |

`logging-vague` reuses the `logging` judge. `judge.toml` describes the criterion
and backend; the benchmark's `--eval-agent` selects the LLM judge at runtime.
Use `--eval-agent codex` for testing unless the user requests another judge.
The programmatic `worktree` and `docs` judges run independently of that flag.

The commits judge derives Feature boundaries from the original request and
reads actual implementation history. Extra legitimate repairs are allowed;
empty commits, bundled Features, and cosmetic history padding do not pass.
Source strings and commit counts cannot substitute for this assessment.

The debug, debug_logs and testing judges receive original logs preserved in
`tests/task-logs/`. Testing accepts saved literal regression assertions that
match those logs; the checks need not load the logs themselves. The debug judge
uses original logs, reachable source and supplied execution; it may run a focused
example in an isolated copy when execution tools are available.
It reports applicability separately in its reasoning. Without a chronological
tool trace it cannot prove that logs were read before editing; its verdict
then describes the observable fix, not the agent's unseen thought process.

These semantic verdicts use the shared LLM runner and incur LLM latency/cost.
They are not deterministic and must be calibrated against real histories and
failures. Archived results from the earlier programmatic judges retain their
original meaning and must not be presented as directly comparable scores.

Add an LLM judge with `prompt.md` containing `{criteria}` and `judge.toml`.
Use a programmatic checker only for a criterion with an appropriate executable
contract. Verify runtime changes with the required baseline/positive Harbor
smoke jobs and read their archived verdicts and evidence.

`debug_behavior` is a correctness contract, independent of semantic skill policy.
It is installed only on dedicated debug scenarios and requires every immutable
public-call sequence to pass. It neither matches source tokens nor counts Features.
Direct judge synchronization filters task families; partial coding-skill syncs
leave repair-case judges intact.

Workflow, commits and testing receive plan, Git source snapshots and bounded
coding-agent chronology. They inspect actual writes and commands, including
multiple steps in one shell command; subjects, timestamps and final green runs
alone cannot prove tests-before-code. Missing excerpts are explicit evidence
limits. Helpers expose syntax and authentic quotations, never task-specific
Feature counts or semantic replacement scores.

For a testing rejection, an exact `Citation: path.py:LINE | source line` verifies
submitted source; an authentic `TraceCitation: codex.txt:LINE | raw excerpt`
can verify chronological evidence. Claude and Grok use their actual transcript
filenames. A chronology finding may use a source quote plus decisive raw trace
positions. Quotes verify text, while the LLM judges execution order. Unsupported
quotations retry once and remain infrastructure exclusions if unresolved.
The debug judge separately requires a saved public regression before repair;
a terminal-only reproduction does not meet that selected policy.

## Scope and criterion alignment

Each semantic policy now has one binary criterion. Testing's `testing_contract`
retains checks-before-code, coverage, preservation/isolation and cumulative
execution requirements in one prompt/configuration. The former per-raise and
per-rejection expansion is no longer selected, and its four auxiliary templates
were removed. Runtime evidence helpers and immutable public correctness contracts
are unchanged; no code-token, feature-count or automatic-pass shortcut replaces
semantic inspection. The new detail schema is not directly comparable with
historical expanded criterion rows.

Do not grade optional coverage inventories or byte-for-byte ledger punctuation.
A faithful capability queue still requires distinct working commits by sentence.
Assess acceptance changes at the revision that requests them. A newly introduced
query belongs in older retained test bodies during that query's checks step;
this is not early implementation. SRP reuses actual equivalent domain decisions
but does not force distinct arithmetic operations into a shared state updater.
Every no needs a concrete violation; missing chronology alone is an explicit limit.

The October 10, 2026 revision passed frontmatter/TOML/template validation, actual
consumer loading, instruction assembly and isolated judge synchronization. No
benchmark or LLM judge was run for it, so improved pass rate remains unverified.
Old archives retain their original scores and reasoning.

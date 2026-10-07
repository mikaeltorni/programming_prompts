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
| `workflow` | LLM `prompt.md` | one current four-row plan and routing of independently selected companions |
| `testing` | LLM `prompt.md` | agent-authored checks against the original contract, isolated execution when available, and explicit evidence limits |
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
executes the reported example and documented boundaries in an isolated copy.
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

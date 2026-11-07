# Workflow turn coverage

The November 7 Agent session completion notification rollout resumed after a
reboot while retaining unfinished plan steps. Its existing workflow policy
exempted status replies from plan use and did not explicitly require reading
the retained plan on every continuation.

The workflow policy now requires every-turn plan reads, continuation from the
first unfinished step, preserved completed evidence and at most one active
microstep. Questions read and preserve the task plan. ACC owns their separate
interaction indicator; the prompt does not depend on agents writing extra
question metadata. Attempts to require such writes were discarded after real
Luna-low runs consistently omitted them.

The saved Harbor fixtures exercise the original two input classes:
`workflow-resume` completes the interrupted artifact and updates its plan;
`workflow-question` answers from that same unfinished plan without implementing
or completing it. Both are opt-in to the workflow policy and run through the
existing `run_benchmark.sh`. No pytest was added under the eval tree.

The semantic judge distinguishes questions from implementation handoff. Its
structural evidence reader previously rejected valid pending/in_progress rows
as malformed, which forced correct question verdicts into retries or rejection.
`python3 scripts/check_workflow_plan_structure.py` reproduces that defect against
the retained question fixture and checks invalid-status controls. Structural
checks now accept all four legal statuses; semantic completion still belongs
to the judge, which rejects an unupdated implementation plan.

Frozen old-policy run `2026-11-07_232428_556905` captured original failures.
Intermediate prompt/metadata attempts and quota failures are retained in the
local run archive and are not acceptance evidence. Final runtime baseline
`2026-11-07_234113_1544695` scored question yes and resume no, with no quota or
infrastructure errors. The original two cases were retained throughout.
Frozen positive run `2026-11-07_234206_1599853` scored 2/2 with no quota or
infrastructure errors; both coding and judging used GPT-6 Luna at low reasoning.
Its actual question preserved the task plan; its actual resume wrote Ready\n
and completed the retained implementation step. The judge self-test passes
117/117 cases.

Focused positive command (for a human to launch):

```bash
./run_benchmark.sh --harness codex --eval-agent codex --skills workflow --tasks workflow-question,workflow-resume -k 1
```

Agent verification adds `--agent-run`, stays quiet, and uses GPT-6 Luna with low
reasoning for both coding and judging. Check the archived task plans, exact
artifact bytes, received native instructions and judge results as well as the
aggregate score.

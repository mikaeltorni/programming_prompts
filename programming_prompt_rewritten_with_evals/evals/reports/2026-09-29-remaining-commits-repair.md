# September 29: remaining commit verdicts and k5 review

The remaining commit work was delivered by `bae6f5e303f20551ec8e84452b5311c6cb1af9e2`
and the focused follow-up `64fdf560436a926976a3f645f7ff4d83338f5719`,
both merged into live `master`. The first repair kept optional `and may`
clauses in their complete source sentences, removed an ambiguous
"undivided change" allowance, and retried verdicts that retracted their own
allegations. The follow-up checks literal punctuation claims, puts reasoning
before the score in Codex's temporary output schema, and aligns SRP and
logging judgments with their written requirements. Neither repair assigns a
pass automatically or changes historical rewards.

The user-requested all-task Codex/Codex run
`2026-09-29_114347_3954708` used all eight skills, `-k 5`, and
`--concurrency 30`. It completed 45/45 trials with zero rate-limit or
infrastructure exclusions and reported **40/45 overall**: commits **44/45**,
logging **43/45**, SRP **43/45**, and each other judge **45/45**. The five
reported failures are classified below. This run preceded the follow-up
repair. After delivery the user said not to run tests, so there is **no
post-repair k5 result**. The last completed Codex positive smoke run on the
final source passed **2/2** with no exclusions; it is not a full-suite score.

## Evidence and classification

The k5 archive is under `evals/runs/2026-09-29_114347_3954708__*`. For a
trial, the original request is in
`harbor/task-trees/codex-skills__2026-09-29_114347_3954708/<task>/tests/task.md`,
the submitted source, plan and Git objects are in `Projects/<trial>/app/`, and
the exact verdict is in
`harbor/codex-skills__2026-09-29_114347_3954708/<trial>/verifier/reward-<skill>-codex-details.json`.
The archived Git config has redacted booleans; history checks used temporary
copies with valid local configs. Archived submissions and scores were not
edited. `result.json` may contain redaction-invalid JSON; the valid reward
files and run summary supply the classifications.

| Trial | Reported failure | Finding |
| --- | --- | --- |
| `todo__QUdbC67` | commits | **False negative.** The request has three complete capability sentences. The final `done` sentence includes optional `clear` before its one final period. Its ledger preserves that sentence, and distinct working conventional commits `b5ef3fc`, `6071cbc`, `5a45331` introduce add, list, then done/clear in order. All three historical public entrypoints ran in a temporary copy. The archived score is `no`, while its reason ends “no violation is evidenced.” The corrected judge replay returned yes. |
| `counter__Tu9vtt8` | logging | **Real failure.** `_set_value(value)` declares `global _counter` before `print(f"value={value}")`. The selected logging skill literally requires the parameter print as the first statement after the docstring, including before a `global` declaration. The replay retained no. |
| `counter__9riHsiC` | logging | **Real failure.** `_increment`, `_decrement`, and `_set_counter` place `global _counter` before their entry prints. The prints name their actual parameters and the exits are traced, but source-order entry tracing fails. The replay retained no. |
| `greeter-fix__LwW9tXK` | SRP | **False negative.** The entrypoint only checks parsed hour format `0..23` and passes the valid hour to a helper. Both selected SRP skill and judge expressly allow that format guard; period classification and output live in helpers. The clarified judge replay returned yes. |
| `greeter__Qk44fHs` | SRP | **Real failure.** `run_greeter` rejects hours outside `5..21` before calling `_greet_by_hour`. That narrower interval is the greeting operation's business rule, rather than clock-format validity. The clarified judge replay retained no. |

The literal logging requirement can surprise an agent because `global` has no
runtime effect before the print. The skill now includes a compiling example
that places `print` before `global`, and the judge states the same source-order
rule. SRP now distinguishes a 0–23 clock-format check from an operation's
narrower accepted interval. These changes close an instruction/judge mismatch
without treating the two genuine defects as passes.

## Earlier remaining-commits cases

The preceding full runs also had commit failures. Each was inspected against
its original request, saved ledger, actual historical Python trees, and
conventional commits:

| Trial | Finding and evidence |
| --- | --- |
| `calculator__2yggayT` | False negative. The judge invented a SyntaxError from repeated function definitions. The historical source compiles; the later definition is effective, and the Feature history remains working. Fresh replay passed. |
| `stats__ghPqajg` | Real ledger defect. The optional reset clause belongs to the same complete sentence as median, but the saved plan split it into a fifth Feature row. Its extra focused code commit is allowed as a follow-up; the extra ledger row is not. The original replay stayed no; a temporary copy with only the ledger corrected passed. |
| `shop__SPcT8Gq` | Real bundling. Separate catalog, checkout, and removal/count capability sentences first work in a single commit. The replay stayed no. The commits skill no longer lets an “undivided change” phrase override sentence boundaries. |
| `shop__dpzAM4p` | False negative. Three faithful ledger rows map to three working conventional commits `439a1ef`, `854d2fa`, `023d863`. The judge reason ended by retracting its allegation (“this is not a violation”) but emitted no. The corrected replay passed. |

In the final two-trial Codex smoke run, archived todo and counter plans each
had faithful sentence-level ledgers, their historical source trees compiled,
and commits passed **2/2**. The judge's actual JSON now begins with `reasoning`:
rewardkit's original single-criterion response schema lists `score` first,
so a temporary PATH wrapper reorders only the schema properties for Codex
judge calls. It preserves the required fields, score enum, command arguments,
model, and normal CLI behavior; the wrapper and temporary home are removed
after the call. The existing one-retry reliability gate still records both
attempts and reports unresolved contradictions as infrastructure.

## Verification scope and limits

Before the user's stop instruction, the final standalone LLM-judge helper
reported **83/83** checks passing and the version-policy check reported
**76/76**. A focused real-judge replay passed valid todo and counter histories,
failed bundled shop and split-ledger stats histories, accepted the 0–23 format
guard, and rejected the narrower greeting range and late logging prints.
The final Codex baseline was **0/1**, as expected without selected skills;
the final positive was **2/2**, with zero exclusions. Grok baseline and positive
attempts were excluded by exhausted usage balance. Earlier Claude harness
attempts were excluded by expired OAuth credentials; no Claude attempt was
made after the last source edit because the user stopped tests. These void
runs provide no evidence about model compliance. No eval-tree pytest suite,
marker catalog, CI, or marketplace file was added.

The full k5/concurrency-30 rerun of the final merged repair remains unrun at
the user's direction. Run it alone, with the Codex judge only, and inspect its
archive before treating its aggregate as a model result. The exact command
is given in the final handoff; the benchmark entrypoint and supported flags
are documented in the [evals README](../README.md).

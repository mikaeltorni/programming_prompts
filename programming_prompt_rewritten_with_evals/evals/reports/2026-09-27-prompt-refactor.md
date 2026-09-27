# 2026-09-27 programming prompt refactor

The 27-trial Codex positive run `2026-09-27_130938_2249420` scored **24/27** with no rate limits or infrastructure failures. Its three failed trials were different:

| Trial | Cause |
| --- | --- |
| `bank__rskBUus` | The agent committed transfer and history together, although they are separate capability sentences. The commits verdict was correct. |
| `calculator__e8Rv4bi` | The completed workflow plan still had `Commit: pending` for subtraction. The workflow verdict was correct. |
| `todo__5ep4dnN` | The commenting judge rejected `Parameters: none.` because of the trailing period. The skill allows that form; this was a judge false negative. |

The refactor covers the eight selected skill prompts, their six semantic judges, and the matching top-level workflow skill. The nine short coding requests remain fixed benchmark inputs. The deliberately vague `logging-vague` control remains unchanged. Each edited skill has a version bump. The final prompts preserve the existing worktree layout, four-row workflow plan, one Feature per capability sentence, entry and exit prints, docstring format, and SRP boundaries. They remove repeated prose and clarify the three failures above.

## Verification and comparison

| Run stamp | Scope | Scored result | What the archive showed |
| --- | --- | --- | --- |
| `2026-09-27_133921_52693` | Initial broad rewrite, nine tasks, k1 | 5/8; one infrastructure exclusion | Commit bundles, judge contradictions, and SRP overreach. The broad rewrite was revised. |
| `2026-09-27_134640_552547` | Four affected tasks, k1 | 3/4 | Shop, temperature, and todo passed all eight criteria. Bank wrote its plan outside the repository root. |
| `2026-09-27_135224_942708` | Bank, k1 | 0/1 | The plan path was fixed; transfer and history were bundled. Logging and SRP also produced false negatives on the archived code. |
| `2026-09-27_140108_1492891` | Bank, k1 | 0/1 | The agent split optional `assets` into another ledger row. Focused replays exposed judge disagreement, so the broad rewrite was abandoned. |
| `2026-09-27_141047_2140585` | Broad rewrite, nine tasks, k1 | 1/9 | Multiple contradictory judge verdicts and Feature boundary mistakes. This version was not retained. |
| `2026-09-27_142120_2877185` | Conservative refactor, nine tasks, k1 | **8/9** | Zero rate limits or infrastructure failures. Only calculator failed: the plan said four Features while its correct ledger had three capability sentences. |
| `2026-09-27_142830_3379012` | Calculator after the plan wording change, k1 | n/a | The trial is void: the cx1 agent reported `Your workspace is out of credits`; the wrapper excluded it as rate limited. |

The last scored full run and the 27-trial run both pass 88.9% of their trials. The final plan wording change prefers deliverable names to repeating numeric Feature counts and still requires any stated count to match the ledger. It has **not** received a scored live calculator rerun because cx1 ran out of credits. Static checks passed for the skill versions, judge `{criteria}` tokens, identical workflow copies, and `git diff --check`. The selected skill and judge prompts are 80 lines shorter overall than before this refactor.

The archived Harbor jobs under `evals/runs/` hold the trial source, Git histories, plans, transcripts, per-skill rewards, and job logs. The unscored cx1 run must not be compared with scored runs. A new scored cx1 run is the remaining verification gate for the final plan wording change.

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
| `2026-09-27_151111_2057423` | Calculator after account reset, k1 | 1/1 | The revised workflow plan used three sentence and commit rows; all eight criteria passed. |
| `2026-09-27_151558_2391745` | Nine tasks, k1 | 7/9 | Calculator and shop bundled separate capability sentences in their plans and commits. |
| `2026-09-27_152300_2841729` | Calculator and shop after commits skill repair, k1 | 2/2 | Both plans and commit histories kept the requested sentence boundaries. |
| `2026-09-27_152728_3152811` | Nine tasks, k1 | 8/9 | Shop had three correct Feature commits; the commits judge wrongly demanded another commit for optional `count` in the third sentence. |
| `2026-09-27_153618_3774953` | Shop after judge repair, k1 | 0/1 | The agent genuinely bundled checkout with the later removal sentence; the revised judge rejected it correctly. |
| `2026-09-27_154127_4130511` | Nine tasks, k3, concurrency 15 | 22/26 scored; one timeout | Three scored failures were agent deviations: a split Kelvin sentence, a bundled todo implementation, and mismatched bank worktree and branch slugs. The fourth was a bank commits judge false negative that required an earlier deposit commit to maintain the later history Feature's state. |
| `2026-09-27_160210_1420035` | Bank and todo after judge repair, k1 | 1/2 | Bank passed all eight criteria. Todo duplicated its final `done … and may clear` sentence into two ledger rows, a valid workflow failure. |
| `2026-09-27_160827_1856965` | Todo after commits ledger repair, k1 | 1/1 | The plan and history used three rows and commits; all eight criteria passed. |
| `2026-09-27_161406_2248928` | **Final nine tasks, k3, concurrency 15** | **27/27** | Three attempts for each task passed all eight criteria. The archive reports zero rate limits and zero infrastructure failures. |

The first 54-trial sample passed 46/54 (85.2%); the 27-trial run that prompted this refactor passed 24/27 (88.9%). The final full run passed 27/27 (100%) with the clarified prompts and judge. These are observed samples of a nondeterministic agent and judge, not a guarantee that every future run will pass. The intermediate 22/26 score excludes one agent timeout; it must not be presented as 22/27 scored trials.

The final repairs explicitly reject duplicate ledger rows for one sentence and judge later Feature state at that Feature's commit. Focused real-judge replay passed the archived valid bank history and rejected the genuinely bundled todo history. The final 27/27 archive contains all trial sources, Git histories, plans, transcripts, per-skill rewards, and job logs under `evals/runs/`. Static checks passed for skill versions, judge `{criteria}` tokens, matching workflow copies, and `git diff --check`. The selected skill and judge prompts remain shorter overall than before the refactor.

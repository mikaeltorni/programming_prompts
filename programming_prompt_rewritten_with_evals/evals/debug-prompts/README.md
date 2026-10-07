# Dedicated debugging cases

These are repair tasks, separate from coding-prompts creation and staged tasks.
Each task ships its existing public contract in the seed README and its executed
original failures in the project-root `.log/failure.log`. The skill only tells
the agent to read available logs; it contains no fixture-specific locations or
answers. Verifiers own independent contracts and original logs outside the agent
workspace.

| Case | Reported failures | Additional checks |
| --- | --- | --- |
| debug-clock | Positive-offset previous-day conversion; negative-offset next-day conversion | UTC, fractional-hour offsets, malformed and offset-free timestamps |
| debug-catalog | Same SKU across tenants; reversed lookup order | Different SKUs, cache reuse, unknown tenant/SKU followed immediately by correct valid lookups |
| debug-stock | Shortage rejection; negative-quantity rejection | Exact depletion, other item, empty/unknown command, missing/extra operands, numeric conversion, unknown item, zero, negative and excessive quantities; each rejection immediately observes both stocks |
| debug-orders | Late multi-item shortage mutates earlier stock; order identifiers collide across tenants; repeated cancellation restocks again | Duplicate-SKU aggregation, normalized idempotent retries with depleted stock, terminal cancelled IDs, atomic validation failures, and immediate order/stock/history observations in both tenants |
| debug-cache | Cache survives its expiry boundary; set leaves a cached miss; drop leaves a cached hit | Exclusive five-tick TTL, hits that do not extend TTL, tenant isolation, replacement writes, and rejected writes preserving catalogs and cached results |
| debug-scheduler | Offset timestamps are relabeled as UTC; adjacent intervals conflict; failed moves remove the original booking | Half-open UTC intervals, rollover and fractional offsets, self-excluding moves, resource-scoped identifiers, cancellation/rebooking, sorted lists and immediate rollback observations |

The original three cases remain single-defect controls. Each new case has three
independent faults; a repair must also preserve the behaviors in the final
column. The [coverage inventory](../debug-cases/README.md) maps 539 public
assertions across 26 independent sequences, including 465 assertions added by
the complex cases.

| Case contract | Public entrypoint | Accepted commands |
| --- | --- | --- |
| [Orders](../seeds/debug-orders/README.md) | `orders.py:run_orders(command)` | `reserve TENANT ORDER SKU QUANTITY [SKU QUANTITY ...]`, `cancel TENANT ORDER`, `order TENANT ORDER`, `stock TENANT SKU`, `history TENANT` |
| [Cache](../seeds/debug-cache/README.md) | `cache.py:run_catalog(command)` | `get TENANT SKU TICK`, `set TENANT SKU PRICE`, `drop TENANT SKU`, `list TENANT` |
| [Scheduler](../seeds/debug-scheduler/README.md) | `scheduler.py:run_schedule(command)` | `book RESOURCE ID START END`, `move RESOURCE ID START END`, `cancel RESOURCE ID`, `list RESOURCE` |

Contracts live in `../debug-cases/`; each sequence creates a fresh module in its
own subprocess. An assertion checks a public result or exception; no private
state or source-token checks score correctness. All captured reported sequences
must fail on their seed, and all contract sequences must pass on their reference
repair. Fixtures are certified before task materialization:

```bash
python3 verify_debug_fixtures.py
```

Run this from `evals/`. `--refresh-logs` replaces original captures only when an
intentional seed/contract change requires it. The default command never rewrites
the captures. Missing, stale and non-failing logs stop task generation.

## Calibration on 2026-10-07

The archived original run `2026-10-07_161614_399695` scored 15/15: five
attempts each at three small bugs. Independent replay of all delivered source
snapshots passed 370 public assertions. The score was valid, but those repeated
cases did not establish performance on interacting faults.

For the complex cases, certification rejects every broken seed and accepts
every reference repair twice with fresh state. Temporary public-behavior probes
also rejected all 18 incomplete repairs leaving one or two faults unfixed.
No source tokens or hidden diagnosis markers score these probes.

The new baseline run `2026-10-07_171348_768590` passed 3/3. The positive run
`2026-10-07_171547_884408` passed all nine functional checks, but its semantic
score was 8/9 because one judge incorrectly treated strict `<` as including
equality. Independent snapshot replay of these twelve repairs passed 1,860
assertions. A task-independent judge clarification now requires evaluating
boundary predicates with concrete values and reconciling source inferences
with execution evidence. The fresh positive run
`2026-10-07_172041_1020656` passed 6/6 across the complete debug family;
independent replay passed all 539 assertions. These runs had no rate-limit or
infrastructure failures. The earlier archive and its score remain unchanged.

The cases exercise more interacting behavior, but the measured repairs still
all worked. These small runs do not demonstrate a debug-policy advantage over
the baseline or establish a general model failure rate.

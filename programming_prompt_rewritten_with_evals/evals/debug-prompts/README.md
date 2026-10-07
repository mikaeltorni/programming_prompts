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

# Public debugging contracts

Each JSON contract names a public artifact and entrypoint. Each sequence runs in
a fresh process and asserts independently specified results or exception types.
`reported: true` sequences also supply authentic original failure captures.
The contract is verifier-owned; agents receive the seed README and original log.

The existing control fixtures remain unchanged. Complex fixture coverage:

| Task / command | Operands and validation ownership | Executable scenarios and observations |
| --- | --- | --- |
| orders / reserve | Tenant, order, one or more SKU/positive-integer pairs; shared integer conversion; normalized duplicate SKUs; atomic aggregate availability and retry identity | Late batch shortage; tenant-scoped identity; normalized retry/exact depletion; malformed pair shapes/conversion; zero/negative; unknown tenant or late SKU; immediate both stocks, both histories and known order observations after every rejection |
| orders / cancel, order | Tenant and identifier; shared two-operand shape, tenant and order lookup | Cancellation retry; cancelled-ID reuse/conflicting payload rejection; missing/extra operands and both lookup paths; same immediate observations |
| orders / stock, history | Tenant; shared one-operand shape and tenant lookup; no numeric operands | Missing/extra and unknown tenant; both stocks, both histories and known order observations |
| cache / get | Tenant, SKU, nonnegative integer tick; shared integer conversion; tenant lookup; absent SKU cached as a miss | Deadline and beyond-deadline fetch; positive and negative invalidation; scoped cache keys; missing/extra/conversion/negative time/tenant; immediate both catalogs and warm public lookups after validation failures; both catalogs after intentional missing-SKU reads |
| cache / set | Tenant, SKU, positive integer price; same integer conversion, distinct price domain rule | Warm-hit update, miss creation, recreation after deletion; missing/extra/conversion/zero/negative/tenant; immediate both catalogs and warm lookups |
| cache / drop, list | Two or one text operands respectively; no numeric conversion; tenant lookup and independent deletion SKU lookup | Missing/extra/tenant and missing deletion SKU; immediate both catalogs and warm lookups |
| scheduler / book, move | Resource, identifier, offset-bearing start/end; shared timestamp conversion; strictly positive interval; shared overlap check, independent identifier rules | Offset overlap, half-open adjacency, failed move rollback, move overlapping its old interval; rollover/fractional offsets and sorted output; missing/extra, malformed or offset-free time, zero/reversed interval, unknown resource/identifier, duplicate ID and overlap; immediate both populated public calendars after every rejection |
| scheduler / cancel, list | Two or one text operands; no numeric conversion; resource lookup and cancellation identifier lookup | Resource isolation, cancellation and rebooking; missing/extra/resource/identifier rejections; immediate both populated calendars |

Executable locations are the named sequences in `debug-orders.json`,
`debug-cache.json` and `debug-scheduler.json`. Domain validation is intentionally
specified separately from token/shape validation. No test runner selectors retire
these assertions: the default fixture certification executes every sequence,
requires every reported scenario to fail on its seed, and passes references twice.

Run from `evals/`:

```bash
python3 verify_debug_fixtures.py
```

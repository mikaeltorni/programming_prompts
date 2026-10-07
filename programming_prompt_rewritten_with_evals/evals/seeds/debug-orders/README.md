# Tenant order reservations

Public entrypoint: `run_orders(command: str)` in `orders.py`. State is process
local. Initially acme has bolt=8, nut=5 and beta has bolt=6, nut=9. Each tenant
has an empty order store and event history. Names are nonempty single tokens;
commands use whitespace-separated operands.

- `reserve TENANT ORDER SKU QUANTITY [SKU QUANTITY ...]` returns
  `{"order": ORDER, "status": "active", "items": {SKU: TOTAL, ...}}`.
  Each quantity is a positive integer. Combine duplicate SKU lines by summing
  quantities before checking availability. Validate the entire aggregate before
  subtracting any stock or recording an order/event. Every SKU must exist.
- Order identifiers belong to a tenant. Retrying an active order with exactly
  the same aggregated items returns its original response without subtracting
  again or adding an event, even when current stock could not satisfy a new
  reservation. Reordered lines and equivalent duplicate lines are the same
  request. A conflicting payload or reuse of a cancelled ID raises `ValueError`.
- `cancel TENANT ORDER` returns that order with `"status": "cancelled"`.
  Restore its allocations once. Repeating cancellation returns the same response
  and does not restore again or append another event. Unknown orders raise
  `ValueError`.
- `order TENANT ORDER` returns the order's current response. It raises
  `ValueError` for an unknown order.
- `stock TENANT` returns the current `{SKU: COUNT, ...}` mapping.
- `history TENANT` returns the ordered event strings `reserve:ORDER` and
  `cancel:ORDER`, exactly one per applied lifecycle transition. No events are
  recorded for retries or failures.

Empty/unknown commands, missing/extra operands, incomplete item pairs,
malformed integer quantities, nonpositive quantities, unknown tenants/SKUs,
conflicting/cancelled order reuse and aggregate shortages raise `ValueError`.
All rejected commands preserve both tenants' stock, every existing order and
event history. Failed reservations do not consume their order identifier.
No external dependencies or network are required. Diagnose the existing faults
from the captured project logs and preserve the full contract.

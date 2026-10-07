# Expiring tenant catalog

Public entrypoint: `run_catalog(command: str)` in `cache.py`. State is process
local. Initially acme prices are tool=12, bolt=3 and beta prices are tool=29,
bolt=7. The cache is empty. Names are nonempty single tokens; commands use
whitespace-separated operands.

- `get TENANT SKU TICK` returns `{"price": PRICE, "cached": BOOL}`. `TICK` is
  a nonnegative integer logical time supplied by the caller; calls in a workload
  use nondecreasing ticks. Each cached item belongs to its tenant and SKU. A
  fetch at tick T caches the current source value until T+5, exclusively: it is
  usable for ticks less than T+5 and expired at T+5. Fetching returns cached=false;
  using an unexpired entry returns cached=true. Expired reads refresh their
  deadline from that read's tick. Missing SKUs raise `ValueError` and cache a
  missing value with the same TTL; those intentional misses may change cache
  state but do not change either source catalog.
- `set TENANT SKU PRICE` creates or updates an item with a positive integer
  price and returns `{"sku": SKU, "price": PRICE}`. Invalidate that exact
  tenant/SKU's cached value, including a cached miss, immediately. Other cache
  entries retain their deadlines and values.
- `drop TENANT SKU` removes an existing item, invalidates that exact cached
  value immediately, and returns `{"dropped": SKU}`. An absent SKU raises
  `ValueError` without changing the catalogs or cache.
- `list TENANT` returns the current source `{SKU: PRICE, ...}` mapping without
  warming or invalidating any cache entry.

Empty/unknown commands, missing/extra operands, malformed integer tokens,
negative ticks, nonpositive prices and unknown tenants raise `ValueError`
without changing either source catalog or existing cache entries. Unknown
write/delete tenants never create catalogs. Reads of a missing SKU are the
explicit cached-miss exception above. No real clock, network or external
dependency is used. Diagnose the existing
faults from the captured project logs and preserve the full contract.

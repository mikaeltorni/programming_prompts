# debug-catalog

Return the integer price for the requested tenant and SKU. acme: tool=12, bolt=3; beta: tool=29, bolt=7. Repeated lookups may use a cache but must preserve tenant identity and return the correct price regardless of call order. Unknown tenant or SKU raises ValueError and must not alter valid lookups. Public entrypoint: lookup(tenant: str, sku: str) -> int in catalog.py.

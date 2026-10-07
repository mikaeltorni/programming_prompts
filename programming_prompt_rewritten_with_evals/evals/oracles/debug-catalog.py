PRICES = {'acme': {'tool': 12, 'bolt': 3}, 'beta': {'tool': 29, 'bolt': 7}}
CACHE = {}


def lookup(tenant: str, sku: str) -> int:
    if tenant not in PRICES or sku not in PRICES[tenant]:
        raise ValueError('unknown catalog item')
    key = (tenant, sku)
    if key not in CACHE:
        CACHE[key] = PRICES[tenant][sku]
    return CACHE[key]

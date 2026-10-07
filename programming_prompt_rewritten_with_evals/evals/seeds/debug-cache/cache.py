"""Serve tenant prices through an expiring cache with mutation invalidation."""
PRICES = {'acme': {'tool': 12, 'bolt': 3}, 'beta': {'tool': 29, 'bolt': 7}}
CACHE = {}
TTL = 5


def _parse(command):
    """Parse command shape and shared integer operands.

    Parameters: command - raw catalog command.
    Returns: operation selector and typed operands.
    """
    print(f"command={command!r}")
    parts = command.split()
    if not parts:
        raise ValueError('empty command')
    operation = parts[0]
    if operation in ('get', 'set') and len(parts) == 4:
        result = operation, (parts[1], parts[2], int(parts[3]))
    elif operation == 'drop' and len(parts) == 3:
        result = operation, (parts[1], parts[2])
    elif operation == 'list' and len(parts) == 2:
        result = operation, (parts[1],)
    else:
        raise ValueError('invalid command shape')
    print(result)
    return result


def _tenant(tenant):
    """Require a known tenant before reading or writing catalog state.

    Parameters: tenant - catalog owner name.
    Returns: None when the tenant exists.
    """
    print(f"tenant={tenant!r}")
    if tenant not in PRICES:
        raise ValueError('unknown tenant')
    print(None)


def _get(tenant, sku, tick):
    """Read a fresh cache entry or refill it, including missing-item entries.

    Parameters: tenant - catalog owner; sku - item name; tick - nonnegative caller clock tick.
    Returns: price and whether a live cache entry supplied it.
    """
    print(f"tenant={tenant!r}, sku={sku!r}, tick={tick!r}")
    _tenant(tenant)
    if tick < 0:
        raise ValueError('negative clock tick')
    key = (tenant, sku)
    cached = key in CACHE and tick <= CACHE[key][0]
    if cached:
        price = CACHE[key][1]
    else:
        price = PRICES[tenant].get(sku)
        CACHE[key] = (tick + TTL, price)
    if price is None:
        raise ValueError('unknown item')
    result = {'price': price, 'cached': cached}
    print(result)
    return result


def _set(tenant, sku, price):
    """Write a positive price and invalidate the matching hit or miss.

    Parameters: tenant - catalog owner; sku - item to create or update; price - positive integer price.
    Returns: the written item and price.
    """
    print(f"tenant={tenant!r}, sku={sku!r}, price={price!r}")
    _tenant(tenant)
    if price <= 0:
        raise ValueError('price must be positive')
    PRICES[tenant][sku] = price
    key = (tenant, sku)
    if CACHE.get(key, (0, None))[1] is not None:
        CACHE.pop(key, None)
    result = {'sku': sku, 'price': price}
    print(result)
    return result


def _drop(tenant, sku):
    """Remove an existing price and invalidate its matching cached value.

    Parameters: tenant - catalog owner; sku - existing item to remove.
    Returns: the removed item name.
    """
    print(f"tenant={tenant!r}, sku={sku!r}")
    _tenant(tenant)
    if sku not in PRICES[tenant]:
        raise ValueError('unknown item')
    del PRICES[tenant][sku]
    result = {'dropped': sku}
    print(result)
    return result


def _list(tenant):
    """Read a catalog snapshot without warming or invalidating its cache.

    Parameters: tenant - catalog owner.
    Returns: the tenant's current item prices.
    """
    print(f"tenant={tenant!r}")
    _tenant(tenant)
    result = dict(PRICES[tenant])
    print(result)
    return result


def run_catalog(command):
    """Dispatch a catalog command after parsing its raw operands.

    Parameters: command - raw whitespace-separated catalog command.
    Returns: a public catalog operation response.
    """
    print(f"command={command!r}")
    operation, arguments = _parse(command)
    if operation == 'get':
        result = _get(*arguments)
    elif operation == 'set':
        result = _set(*arguments)
    elif operation == 'drop':
        result = _drop(*arguments)
    else:
        result = _list(*arguments)
    print(result)
    return result

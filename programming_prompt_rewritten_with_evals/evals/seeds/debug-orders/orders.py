"""Maintain tenant-scoped atomic order reservations and their lifecycle."""
STOCK = {'acme': {'bolt': 8, 'nut': 5}, 'beta': {'bolt': 6, 'nut': 9}}
ORDERS = {}
HISTORY = {'acme': [], 'beta': []}


def _parse(command):
    """Parse an order command without modifying application state.

    Parameters: command - raw whitespace-separated public command.
    Returns: the operation name and typed arguments.
    """
    print(f"command={command!r}")
    parts = command.split()
    if not parts:
        raise ValueError('empty command')
    operation = parts[0]
    if operation in ('stock', 'history') and len(parts) == 2:
        result = operation, (parts[1],)
    elif operation in ('order', 'cancel') and len(parts) == 3:
        result = operation, (parts[1], parts[2])
    elif operation == 'reserve' and len(parts) >= 5 and len(parts) % 2 == 1:
        lines = [(parts[i], int(parts[i + 1])) for i in range(3, len(parts), 2)]
        result = operation, (parts[1], parts[2], lines)
    else:
        raise ValueError('invalid command shape')
    print(result)
    return result


def _tenant(tenant):
    """Validate a tenant before consulting its state.

    Parameters: tenant - catalog tenant name.
    Returns: None when the tenant exists.
    """
    print(f"tenant={tenant!r}")
    if tenant not in STOCK:
        raise ValueError('unknown tenant')
    print(None)


def _items(tenant, lines):
    """Validate every item and combine repeated SKU quantities.

    Parameters: tenant - stock owner; lines - parsed SKU and quantity pairs.
    Returns: canonical aggregate quantities for the order.
    """
    print(f"tenant={tenant!r}, lines={lines!r}")
    _tenant(tenant)
    totals = {}
    for sku, quantity in lines:
        if sku not in STOCK[tenant] or quantity <= 0:
            raise ValueError('invalid item or quantity')
        totals[sku] = totals.get(sku, 0) + quantity
    print(totals)
    return totals


def _order_value(identifier, order):
    """Format an order without exposing its mutable allocation dictionary.

    Parameters: identifier - tenant-local order identifier; order - stored lifecycle and allocation.
    Returns: the public order response.
    """
    print(f"identifier={identifier!r}, order={order!r}")
    result = {'order': identifier, 'status': order['status'], 'items': dict(order['items'])}
    print(result)
    return result


def _reserve(tenant, identifier, lines):
    """Apply an atomic reservation or return a matching active retry.

    Parameters: tenant - stock owner; identifier - retry identity; lines - parsed requested items.
    Returns: the active order response.
    """
    print(f"tenant={tenant!r}, identifier={identifier!r}, lines={lines!r}")
    items = _items(tenant, lines)
    key = identifier
    if key in ORDERS:
        previous = ORDERS[key]
        if previous['status'] != 'active' or previous['items'] != items:
            raise ValueError('conflicting or cancelled order')
        result = _order_value(identifier, previous)
        print(result)
        return result
    for sku, quantity in items.items():
        if quantity > STOCK[tenant][sku]:
            raise ValueError('insufficient stock')
        STOCK[tenant][sku] -= quantity
    order = {'status': 'active', 'items': items}
    ORDERS[key] = order
    HISTORY[tenant].append(f'reserve:{identifier}')
    result = _order_value(identifier, order)
    print(result)
    return result


def _find_order(tenant, identifier):
    """Find an order in its owning tenant scope.

    Parameters: tenant - order owner; identifier - tenant-local order identifier.
    Returns: the stored order record.
    """
    print(f"tenant={tenant!r}, identifier={identifier!r}")
    _tenant(tenant)
    key = identifier
    if key not in ORDERS:
        raise ValueError('unknown order')
    result = ORDERS[key]
    print(result)
    return result


def _cancel(tenant, identifier):
    """Restore an active order once and make cancellation retries harmless.

    Parameters: tenant - stock owner; identifier - order to cancel.
    Returns: the cancelled order response.
    """
    print(f"tenant={tenant!r}, identifier={identifier!r}")
    order = _find_order(tenant, identifier)
    if order['status'] in ('active', 'cancelled'):
        for sku, quantity in order['items'].items():
            STOCK[tenant][sku] += quantity
        order['status'] = 'cancelled'
        HISTORY[tenant].append(f'cancel:{identifier}')
    result = _order_value(identifier, order)
    print(result)
    return result


def _observe(operation, tenant, identifier=None):
    """Read public stock, history or an order without changing state.

    Parameters: operation - observation kind; tenant - state owner; identifier - optional order identifier.
    Returns: the detached public observation.
    """
    print(f"operation={operation!r}, tenant={tenant!r}, identifier={identifier!r}")
    _tenant(tenant)
    if operation == 'stock':
        result = dict(STOCK[tenant])
    elif operation == 'history':
        result = list(HISTORY[tenant])
    else:
        result = _order_value(identifier, _find_order(tenant, identifier))
    print(result)
    return result


def run_orders(command):
    """Dispatch a public order command to its responsible operation.

    Parameters: command - raw whitespace-separated order command.
    Returns: stock, event history or an order response.
    """
    print(f"command={command!r}")
    operation, arguments = _parse(command)
    if operation == 'reserve':
        result = _reserve(*arguments)
    elif operation == 'cancel':
        result = _cancel(*arguments)
    else:
        result = _observe(operation, *arguments)
    print(result)
    return result

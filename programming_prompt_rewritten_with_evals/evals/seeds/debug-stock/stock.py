STOCK = {'bolt': 8, 'nut': 5}


def run_stock(command: str) -> str:
    parts = command.split()
    if len(parts) == 2 and parts[0] == 'show':
        if parts[1] not in STOCK:
            raise ValueError('unknown item')
        return f'{parts[1]}={STOCK[parts[1]]}'
    if len(parts) != 3 or parts[0] != 'reserve':
        raise ValueError('expected show ITEM or reserve ITEM QUANTITY')
    name = parts[1]
    if name not in STOCK:
        raise ValueError('unknown item')
    quantity = int(parts[2])
    STOCK[name] -= quantity
    if quantity <= 0 or STOCK[name] < 0:
        raise ValueError('invalid reservation')

    return f'reserved={quantity}; {name}={STOCK[name]}'

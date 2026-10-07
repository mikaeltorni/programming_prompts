"""Maintain independent resource calendars using half-open UTC intervals."""
from datetime import datetime, timezone

CALENDARS = {'red': {}, 'blue': {}}


def _timestamp(token):
    """Parse an offset-bearing timestamp into a comparable UTC instant.

    Parameters: token - ISO timestamp with an explicit UTC offset.
    Returns: the corresponding aware UTC datetime.
    """
    print(f"token={token!r}")
    value = datetime.fromisoformat(token)
    if value.tzinfo is None:
        raise ValueError('timestamp requires an offset')
    result = value.astimezone(timezone.utc)
    print(result)
    return result


def _parse(command):
    """Parse every calendar command and its timestamp operands.

    Parameters: command - raw calendar command.
    Returns: operation selector and typed operands.
    """
    print(f"command={command!r}")
    parts = command.split()
    if not parts:
        raise ValueError('empty command')
    operation = parts[0]
    if operation in ('book', 'move') and len(parts) == 5:
        result = operation, (parts[1], parts[2], _timestamp(parts[3]), _timestamp(parts[4]))
    elif operation == 'cancel' and len(parts) == 3:
        result = operation, (parts[1], parts[2])
    elif operation == 'list' and len(parts) == 2:
        result = operation, (parts[1],)
    else:
        raise ValueError('invalid command shape')
    print(result)
    return result


def _calendar(resource):
    """Find a resource calendar without changing it.

    Parameters: resource - calendar resource name.
    Returns: the resource's booking records.
    """
    print(f"resource={resource!r}")
    if resource not in CALENDARS:
        raise ValueError('unknown resource')
    result = CALENDARS[resource]
    print(result)
    return result


def _check_interval(calendar, start, end, excluded=None):
    """Validate a positive half-open interval against other bookings.

    Parameters: calendar - resource bookings; start - UTC start; end - UTC end; excluded - booking ignored during a move.
    Returns: None when the proposed interval is valid.
    """
    print(f"calendar={calendar!r}, start={start!r}, end={end!r}, excluded={excluded!r}")
    if end <= start:
        raise ValueError('interval must be positive')
    for identifier, (old_start, old_end) in calendar.items():
        if identifier != excluded and start < old_end and old_start < end:
            raise ValueError('overlapping booking')
    print(None)


def _value(identifier, start, end):
    """Format one public booking with second-resolution UTC timestamps.

    Parameters: identifier - booking name; start - aware UTC start; end - aware UTC end.
    Returns: the normalized public booking record.
    """
    print(f"identifier={identifier!r}, start={start!r}, end={end!r}")
    result = {'id': identifier, 'start': start.isoformat(timespec='seconds').replace('+00:00', 'Z'),
              'end': end.isoformat(timespec='seconds').replace('+00:00', 'Z')}
    print(result)
    return result


def _book(resource, identifier, start, end):
    """Create a unique booking only after all interval checks pass.

    Parameters: resource - calendar owner; identifier - new resource-local booking name; start - UTC start; end - UTC end.
    Returns: the created booking record.
    """
    print(f"resource={resource!r}, identifier={identifier!r}, start={start!r}, end={end!r}")
    calendar = _calendar(resource)
    if identifier in calendar:
        raise ValueError('duplicate booking')
    _check_interval(calendar, start, end)
    calendar[identifier] = (start, end)
    result = _value(identifier, start, end)
    print(result)
    return result


def _move(resource, identifier, start, end):
    """Replace a booking atomically while excluding its old interval.

    Parameters: resource - calendar owner; identifier - existing booking name; start - new UTC start; end - new UTC end.
    Returns: the updated booking record.
    """
    print(f"resource={resource!r}, identifier={identifier!r}, start={start!r}, end={end!r}")
    calendar = _calendar(resource)
    if identifier not in calendar:
        raise ValueError('unknown booking')
    _check_interval(calendar, start, end, identifier)
    calendar[identifier] = (start, end)
    result = _value(identifier, start, end)
    print(result)
    return result


def _cancel(resource, identifier):
    """Cancel an existing booking in one resource scope.

    Parameters: resource - calendar owner; identifier - existing booking name.
    Returns: the cancelled booking name.
    """
    print(f"resource={resource!r}, identifier={identifier!r}")
    calendar = _calendar(resource)
    if identifier not in calendar:
        raise ValueError('unknown booking')
    del calendar[identifier]
    result = {'cancelled': identifier}
    print(result)
    return result


def _list(resource):
    """List a resource's bookings in UTC start and identifier order.

    Parameters: resource - calendar owner.
    Returns: sorted public booking records.
    """
    print(f"resource={resource!r}")
    calendar = _calendar(resource)
    ordered = sorted(calendar.items(), key=lambda item: (item[1][0], item[0]))
    result = [_value(identifier, *interval) for identifier, interval in ordered]
    print(result)
    return result


def run_schedule(command):
    """Dispatch parsed commands to resource-calendar operation owners.

    Parameters: command - raw whitespace-separated calendar command.
    Returns: a booking, cancellation or sorted calendar response.
    """
    print(f"command={command!r}")
    operation, arguments = _parse(command)
    if operation == 'book':
        result = _book(*arguments)
    elif operation == 'move':
        result = _move(*arguments)
    elif operation == 'cancel':
        result = _cancel(*arguments)
    else:
        result = _list(*arguments)
    print(result)
    return result

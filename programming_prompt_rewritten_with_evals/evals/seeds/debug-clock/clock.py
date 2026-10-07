from datetime import datetime, timezone


def to_utc(timestamp: str) -> str:
    value = datetime.fromisoformat(timestamp)
    if value.tzinfo is None:
        raise ValueError('timestamp requires a UTC offset')
    return value.replace(tzinfo=timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

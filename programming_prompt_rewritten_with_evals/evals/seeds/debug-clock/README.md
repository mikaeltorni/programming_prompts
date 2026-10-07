# debug-clock

Convert an ISO 8601 timestamp carrying an explicit UTC offset to UTC, formatted as YYYY-MM-DDTHH:MM:SSZ. Honor positive and negative offsets and date rollover. Reject invalid or offset-free timestamps with ValueError. Public entrypoint: to_utc(timestamp: str) -> str in clock.py. No network, local timezone or external dependency is required.

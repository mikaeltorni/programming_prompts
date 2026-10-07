# Resource booking calendar

Public entrypoint: `run_schedule(command: str)` in `scheduler.py`. State is
process local. Resources red and blue each start with an empty calendar. Names
are nonempty single tokens; commands use whitespace-separated operands.

- `book RESOURCE ID START END` returns `{"id": ID, "start": UTC_START,
  "end": UTC_END}` and inserts one unique resource-local booking. START and
  END are ISO 8601 timestamps carrying explicit offsets (including Z); compare
  their actual instants. The end must be strictly later than the start. Intervals
  are half-open [start,end): touching endpoints do not overlap. A duplicate ID
  or overlap with another booking in the same resource raises `ValueError`.
- `move RESOURCE ID START END` replaces an existing booking with a new interval
  and returns its normalized booking response. Validate before changing anything.
  Ignore the booking's own old interval when checking conflicts. On failure its
  original interval and all other bookings remain unchanged. Moving to the same
  interval is allowed. An unknown ID raises `ValueError`.
- `cancel RESOURCE ID` removes an existing booking and returns
  `{"cancelled": ID}`. Unknown IDs raise `ValueError`; cancelled IDs may be
  used for a new booking later.
- `list RESOURCE` returns booking response dictionaries sorted by actual UTC
  start and then ID. All response timestamps use YYYY-MM-DDTHH:MM:SSZ format,
  including date rollover and fractional-hour offsets. The same ID and times
  may be used independently in another resource.

Empty/unknown commands, missing/extra operands, unknown resources, malformed or
offset-free timestamps, zero/reversed intervals, duplicate IDs, unknown IDs and
conflicts raise `ValueError` without changing either calendar.
No local timezone, network or external dependency is used.
Diagnose the existing faults from the captured project logs and preserve the
full contract.

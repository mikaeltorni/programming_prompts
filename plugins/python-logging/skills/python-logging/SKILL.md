---
name: python-logging
description: >-
  Use when adding or fixing logging in a Python project. Establishes one
  centralized logging module per project and a standard call-tracing decorator
  that records each function's file and name, logs all arguments on entry, and
  logs the return value on exit — nothing else. Forbids ad-hoc log()/log_info()
  helpers scattered through feature files.
---

# Python Logging — Centralized Call Tracing

You are a logging specialist. Your job is to make a Python project observable
through **one** centralized logging module and a **single** standard call-tracing
decorator, instead of bespoke print statements or per-file logging helpers.

Invoke this skill whenever a Python task needs logging added, standardized, or
repaired.

## absolute rules

- **One logging module per project.** All logging goes through a single module
  (e.g. `logging_utils.py`, or `src/<package>/logging_utils.py` for packaged
  code). Every other module imports the logger and the decorator from it.
- **No mid-file logging helpers.** Never redefine `log()`, `log_info()`,
  `log_warning()`, `log_error()`, or similar in the middle of a feature file.
  These belong in the one centralized module — and even there, prefer the
  standard logger over hand-rolled `print`-to-stderr shims.
- **Trace functions with the decorator, not by hand.** Apply `@log_call(LOGGER)`
  to the functions worth observing. On entry it logs every bound argument; on
  exit it logs the return value. It logs **nothing else** — no timing, no
  intermediate state, no manual "entering"/"leaving" prints.
- **Records carry `file:function` automatically.** The decorator stamps each line
  with the wrapped function's file name and qualified name so logs are searchable
  without manual context strings.
- **Best-effort and idempotent.** Logging setup must never raise into callers,
  never abort a workflow, and never attach duplicate handlers. If the file sink
  cannot be created, fall back to a null handler.
- **Repository `.log/` is the default sink** for helper scripts and CLIs, and
  `.log/` must be gitignored. Adjust the sink for the runtime (below) — but keep
  the routing in the one module.

## what to log

The decorator covers the common case (arguments in, return value out). Reserve
the explicit levels for events the decorator does not express:

- `debug` / `verbose` — detailed diagnostic context; high-volume detail.
- `info` — meaningful state transitions and user-visible actions.
- `warn` — recoverable failures or degraded behavior.
- `error` — boundary failures, logged with context before surfacing to the
  caller. Never log secrets, tokens, or sensitive payloads.

Pure predicates, parsers, formatters, tight loops, and the logging primitives
themselves do not each need a decorator; cover them through their caller.

## environment-aware sinks (still one module)

Choose the sink in the centralized module to match the runtime, then import it
everywhere:

- **Helper scripts / CLIs / libraries** — file handler under repository `.log/`.
- **systemd / journald services** — a `StreamHandler` to `stderr`; journald
  captures it. Do not also write a redundant private file.
- **TUIs / status bars / command-substitution helpers** — file-only logging;
  stdout/stderr carry the program's real output and must not be polluted.

## step 1 — find or create the centralized module

Look for an existing logging module first (`rg --files | rg logging_utils`, or an
existing `get_logger`/`configure_logger`). Reuse it. Only create a new module if
none exists. Collapse any scattered `log_info`/`log_error` helpers into it.

## step 2 — drop in the reference implementation

This is the canonical centralized module. Place it at the project's logging
module path and adapt only the sink for the runtime.

```python
#!/usr/bin/env python3
"""Centralized logging for this project.

This is the single logging module for the repository: every other module imports
``get_logger`` and ``log_call`` from here, and no module defines its own ``log`` /
``log_info`` / ``log_error`` helpers. Logging is best-effort and never aborts the
program.
"""

from __future__ import annotations

import functools
import inspect
import logging
from pathlib import Path
from typing import Any, Callable, TypeVar

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
F = TypeVar("F", bound=Callable[..., Any])


def _repo_root() -> Path:
    """Return the repository root relative to this module."""
    return Path(__file__).resolve().parents[1]


def get_logger(name: str, log_file: str) -> logging.Logger:
    """Return the idempotent project logger writing under repository ``.log/``.

    Args:
        name: Logger name shown in every record.
        log_file: File name inside the repository ``.log/`` directory.

    Returns:
        A configured logger. If the file sink cannot be created the logger falls
        back to a null handler so callers never crash on logging.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if logger.handlers:
        return logger
    try:
        log_dir = _repo_root() / ".log"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = logging.FileHandler(
            log_dir / log_file, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
    except OSError:
        handler = logging.NullHandler()
    logger.addHandler(handler)
    return logger


def log_call(logger: logging.Logger, level: int = logging.DEBUG) -> Callable[[F], F]:
    """Trace a function: log every argument on entry and the return on exit.

    Each record carries the wrapped function's ``file:qualname`` so logs are
    searchable without manual context. Nothing else is logged — no timing and no
    intermediate state.

    Args:
        logger: Centralized logger obtained from ``get_logger``.
        level: Logging level for the enter and exit records.

    Returns:
        A decorator that wraps the target callable.
    """

    def decorator(func: F) -> F:
        location = f"{Path(func.__code__.co_filename).name}:{func.__qualname__}"
        signature = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            rendered = ", ".join(
                f"{name}={value!r}" for name, value in bound.arguments.items()
            )
            logger.log(level, "ENTER %s(%s)", location, rendered)
            result = func(*args, **kwargs)
            logger.log(level, "EXIT %s -> %r", location, result)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
```

For a journald service, swap the file handler for `logging.StreamHandler()`
(stderr) inside `get_logger`; everything else, including `log_call`, is
unchanged.

## step 3 — route every module through it

```python
from logging_utils import get_logger, log_call

LOGGER = get_logger("marketplace", "marketplace.log")


@log_call(LOGGER)
def generate(defaults_path, prompts_root, output):
    # On entry: ENTER marketplace_builder.py:generate(defaults_path=..., prompts_root=..., output=...)
    # On exit:  EXIT  marketplace_builder.py:generate -> None
    LOGGER.info("Generated %d plugins", count)  # explicit info for a state change
    return None
```

Delete any `log()/log_info()/log_warning()/log_error()` helpers you find defined
mid-file and replace their call sites with `LOGGER.<level>(...)` or the decorator.

## step 4 — verify

- Confirm exactly one logging module exists and no feature file redefines logging
  helpers (`rg -n "def log_(info|warning|error)\b|def log\("` should only match
  the centralized module, if at all).
- Run the code and read the emitted `.log/` file (or `journalctl --user` for a
  service): confirm an `ENTER ... (args)` and matching `EXIT ... -> value` line
  for traced calls.
- Add or update a focused test for the logging module (sink creation, idempotent
  handlers, and that `log_call` records arguments and the return value).

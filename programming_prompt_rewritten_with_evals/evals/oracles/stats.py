_SAMPLES: list[float] = []


def parse_command(command: str) -> tuple[str, list[str]]:
    """Split a stats command into an action and argument tokens.

    Parameters: command - raw stats command text.

    Returns: a tuple of action name and remaining argument tokens.
    """
    parts = command.strip().split()
    if not parts:
        raise ValueError("empty command")
    return parts[0], parts[1:]


def _samples() -> list[float]:
    """Return the recorded samples, refusing an empty set.

    Parameters: none.

    Returns: the recorded samples.
    """
    if not _SAMPLES:
        raise ValueError("no samples recorded")
    return _SAMPLES


def add_sample(value: float) -> str:
    """Record one sample.

    Parameters: value - sample to record.

    Returns: formatted count=<n> string.
    """
    _SAMPLES.append(value)
    return f"count={len(_SAMPLES)}"


def mean_sample() -> str:
    """Average the recorded samples.

    Parameters: none.

    Returns: formatted mean=<value> string.
    """
    values = _samples()
    return f"mean={sum(values) / len(values):g}"


def low_sample() -> str:
    """Report the smallest recorded sample.

    Parameters: none.

    Returns: formatted low=<value> string.
    """
    return f"low={min(_samples()):g}"


def high_sample() -> str:
    """Report the largest recorded sample.

    Parameters: none.

    Returns: formatted high=<value> string.
    """
    return f"high={max(_samples()):g}"


def median_sample() -> str:
    """Report the middle recorded sample.

    Parameters: none.

    Returns: formatted median=<value> string; even counts average the two
        middle samples.
    """
    values = sorted(_samples())
    middle = len(values) // 2
    if len(values) % 2:
        return f"median={values[middle]:g}"
    return f"median={(values[middle - 1] + values[middle]) / 2:g}"


def reset_samples() -> str:
    """Drop every recorded sample.

    Parameters: none.

    Returns: formatted cleared=<n> string.
    """
    dropped = len(_SAMPLES)
    _SAMPLES.clear()
    return f"cleared={dropped}"


def run_stats(command: str) -> str:
    """Run one stats command.

    Parameters: command - add, mean, low, high, median, or reset.

    Returns: formatted stats string.
    """
    action, args = parse_command(command)
    if action == "add":
        if len(args) != 1:
            raise ValueError("add requires <number>")
        return add_sample(float(args[0]))
    if args:
        raise ValueError(f"{action} takes no arguments")
    if action == "mean":
        return mean_sample()
    if action == "low":
        return low_sample()
    if action == "high":
        return high_sample()
    if action == "median":
        return median_sample()
    if action == "reset":
        return reset_samples()
    raise ValueError(f"unsupported command: {action}")

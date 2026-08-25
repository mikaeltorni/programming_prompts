"""Collect run scores and maintain the RESULTS index."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .fsutil import load_json_lenient, log

RESULTS_INDEX_NAME = "RESULTS.txt"
RESULTS_COL_SEP = " | "
RESULTS_FIXED_COLUMNS = (
    "Run", "Runtime", "Mode", "Harness", "Judge", "Skills", "Tasks",
    "k", "n", "Sep", "Trials", "Scored", "Pass",
)
RESULTS_SKILL_ORDER = ("srp", "commenting", "logging", "worktree", "logging-vague")
RESULTS_TASK_ORDER = ("calculator", "counter", "greeter", "temperature", "todo")
RESULTS_LEFT_ALIGN = frozenset(
    {"Run", "Runtime", "Mode", "Harness", "Judge", "Skills", "Tasks", "Sep"}
)


def format_runtime(seconds: float | int | None) -> str:
    """Format elapsed seconds as hours, minutes, and seconds.

    Parameters: seconds - elapsed wall time, or ``None`` when unknown.

    Returns: ``Xh YYm ZZs`` with minutes and seconds zero-padded, or ``-``.
    """
    if seconds is None:
        return "-"
    total = int(round(float(seconds)))
    if total < 0:
        total = 0
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes:02d}m {secs:02d}s"


def parse_iso_datetime(value: object) -> datetime | None:
    """Parse an ISO-8601 timestamp.

    Parameters: value - metadata datetime string.

    Returns: timezone-aware datetime, or ``None`` when unreadable.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_run_stamp(stamp: object) -> datetime | None:
    """Parse ``YYYY-MM-DD_HHMMSS[_pid]`` as local wall time.

    Parameters: stamp - run timestamp from ``date +%Y-%m-%d_%H%M%S``.

    Returns: timezone-aware datetime, or ``None`` when unreadable.
    """
    if not isinstance(stamp, str) or not stamp.strip():
        return None
    parts = stamp.strip().split("_")
    if len(parts) < 2:
        return None
    try:
        naive = datetime.strptime(f"{parts[0]}_{parts[1]}", "%Y-%m-%d_%H%M%S")
    except ValueError:
        return None
    local_tz = datetime.now().astimezone().tzinfo
    return naive.replace(tzinfo=local_tz)


def _archive_end_time(run_dir: Path) -> datetime | None:
    """Return the latest mtime among durable archive finish files.

    Parameters: run_dir - one archived run.

    Returns: timezone-aware datetime, or ``None`` when no finish files exist.
    """
    candidates = [
        run_dir / "01-SUMMARY.txt",
        run_dir / "03-COMBINED-SUMMARY.txt",
    ]
    candidates.extend(sorted(run_dir.glob("jobs/*/00-job-result.json")))
    candidates.extend(sorted(run_dir.glob("harbor/*/result.json")))
    mtimes = [path.stat().st_mtime for path in candidates if path.is_file()]
    if not mtimes:
        return None
    return datetime.fromtimestamp(max(mtimes), tz=timezone.utc)


def run_elapsed_seconds(
    meta: dict,
    *,
    now: datetime | None = None,
    run_dir: Path | None = None,
) -> float | None:
    """Compute wall-clock seconds for a run from metadata.

    Prefers stored ``elapsed_sec``, then ``started_at`` (or the run stamp)
    against ``archived_at``. When the end timestamp is missing or not after
    the start — typical of an in-progress job — uses ``now``. Older archives
    sometimes stamped ``archived_at`` at init; if the computed duration is
    under five seconds, falls back to summary or job-result file mtimes.

    Parameters: meta - run metadata; now - clock used for in-progress runs; run_dir - optional archive directory for mtime fallback.

    Returns: elapsed seconds, or ``None`` when start time is unknown.
    """
    stored = meta.get("elapsed_sec")
    if isinstance(stored, (int, float)) and stored >= 0:
        return float(stored)
    started = parse_iso_datetime(meta.get("started_at"))
    if started is None:
        started = parse_run_stamp(meta.get("timestamp"))
    if started is None:
        return None
    ended = parse_iso_datetime(meta.get("archived_at") or meta.get("finished_at"))
    clock = now or datetime.now(timezone.utc)
    if ended is None or ended <= started:
        ended = clock
    elapsed = max(0.0, (ended - started).total_seconds())
    if elapsed < 5.0 and run_dir is not None:
        mtime_end = _archive_end_time(run_dir)
        if mtime_end is not None and mtime_end > started:
            elapsed = max(elapsed, (mtime_end - started).total_seconds())
    return elapsed


def runtime_cell(
    meta: dict,
    *,
    now: datetime | None = None,
    run_dir: Path | None = None,
) -> str:
    """Format a RESULTS Runtime cell from run metadata.

    Parameters: meta - run metadata; now - clock used for in-progress runs; run_dir - optional archive directory for mtime fallback.

    Returns: ``Xh YYm ZZs`` or ``-``.
    """
    return format_runtime(run_elapsed_seconds(meta, now=now, run_dir=run_dir))


def _csv(values: list[str]) -> str:
    """Join non-empty names with commas.

    Parameters: values - names to join.

    Returns: comma-separated names or ``-``.
    """
    return ",".join(str(item).strip() for item in values if str(item).strip()) or "-"


def _reward_float(path: Path) -> float | None:
    """Read a numeric reward from JSON.

    Parameters: path - reward JSON file.

    Returns: numeric reward, or ``None`` when unavailable.
    """
    payload = load_json_lenient(path)
    if not payload or "reward" not in payload:
        return None
    try:
        return float(payload["reward"])
    except (TypeError, ValueError):
        return None


def _trial_task_name(trial_dir: Path) -> str:
    """Extract a task name from a trial directory.

    Parameters: trial_dir - archived trial directory.

    Returns: coding-task prefix.
    """
    return trial_dir.name.split("__", 1)[0]


def _record_rate(rates: dict[str, list[int]], name: str, value: float | None) -> None:
    """Add a scored reward to a named rate.

    Parameters: rates - mutable rate counters; name - rate name; value - reward value.

    Returns: nothing.
    """
    if value is None:
        return
    bits = rates.setdefault(name, [0, 0])
    bits[1] += 1
    if value >= 1.0:
        bits[0] += 1


def collect_run_scores(run_dir: Path) -> dict[str, object]:
    """Count pass rates from archived reward files.

    Parameters: run_dir - one archived run.

    Returns: aggregate trial, skill, and task scores.
    """
    trials = scored = passed = 0
    skills: dict[str, list[int]] = {}
    tasks: dict[str, list[int]] = {}
    for trial in sorted(run_dir.glob("jobs/*/trials/*")):
        if not trial.is_dir():
            continue
        trials += 1
        task = _trial_task_name(trial)
        tasks.setdefault(task, [0, 0])
        value = _reward_float(trial / "01-reward.json")
        _record_rate(tasks, task, value)
        if value is not None:
            scored += 1
            passed += int(value >= 1.0)
        for path in sorted(trial.glob("03-reward-*.json")):
            if path.name.endswith("-details.json"):
                continue
            skill = path.name[len("03-reward-") : -len(".json")]
            if "-" not in skill:
                _record_rate(skills, skill, _reward_float(path))
    return {
        "trials": trials,
        "scored": scored,
        "passed": passed,
        "skills": {name: tuple(bits) for name, bits in skills.items()},
        "tasks": {name: tuple(bits) for name, bits in tasks.items()},
    }


def _rate_cell(rate: object | None) -> str:
    """Format a pass-rate tuple.

    Parameters: rate - passed and total pair.

    Returns: ``passed/total`` or ``n/a``.
    """
    if not isinstance(rate, tuple) or len(rate) != 2:
        return "n/a"
    return f"{rate[0]}/{rate[1]}"


def _meta_list(meta: dict, name: str) -> list[str]:
    """Read a string-list metadata field.

    Parameters: meta - run metadata; name - field name.

    Returns: list value or an empty list.
    """
    value = meta.get(name)
    return list(value) if isinstance(value, list) else []


def _add_rate_columns(
    row: dict[str, str],
    configured: list[str],
    rates: dict[str, tuple[int, int]],
    *,
    exclude: str | None = None,
) -> None:
    """Add configured and discovered rate columns.

    Parameters: row - mutable result row; configured - configured names; rates - collected rates; exclude - configured name to omit.

    Returns: nothing.
    """
    names = [name for name in configured if name != exclude]
    names.extend(name for name in sorted(rates) if name not in configured)
    for name in names:
        row[str(name)] = _rate_cell(rates.get(name))


def format_results_row(run_dir: Path) -> dict[str, str]:
    """Build one RESULTS row.

    Parameters: run_dir - one archived run.

    Returns: fixed fields (including Runtime between Run and Mode) and per-skill and per-task rates.
    """
    meta = load_json_lenient(run_dir / "00-meta.json") or {}
    scores = collect_run_scores(run_dir)
    harnesses = _meta_list(meta, "harnesses")
    eval_agents = _meta_list(meta, "eval_agents")
    skills = _meta_list(meta, "skills")
    tasks = _meta_list(meta, "tasks")
    scored = int(scores["scored"])
    row = {
        "Run": str(meta.get("timestamp") or run_dir.name.split("__", 1)[0]),
        "Runtime": runtime_cell(meta, run_dir=run_dir),
        "Mode": str(meta.get("mode") or "-"),
        "Harness": _csv(harnesses),
        "Judge": _csv(eval_agents) if eval_agents else "inherit",
        "Skills": _csv(skills),
        "Tasks": _csv(tasks),
        "k": str(int(meta.get("attempts_per_task") or 0)),
        "n": str(int(meta.get("concurrent") or 0)),
        "Sep": "yes" if meta.get("run_separately") else "no",
        "Trials": str(int(scores["trials"])),
        "Scored": str(scored),
        "Pass": "n/a" if scored <= 0 else f"{int(scores['passed'])}/{scored}",
    }
    _add_rate_columns(row, skills, scores["skills"])
    _add_rate_columns(row, tasks, scores["tasks"], exclude="all")
    return row


def results_table_columns(rows: list[dict[str, str]]) -> list[str]:
    """Order fixed, skill, and task columns.

    Parameters: rows - newest-first result rows.

    Returns: ordered column names.
    """
    seen = {key for row in rows for key in row}
    extras = seen - set(RESULTS_FIXED_COLUMNS)
    skills = [name for name in RESULTS_SKILL_ORDER if name in extras]
    leftover = extras - set(RESULTS_SKILL_ORDER) - set(RESULTS_TASK_ORDER)
    skills.extend(sorted(leftover))
    tasks = [name for name in RESULTS_TASK_ORDER if name in extras]
    return [*RESULTS_FIXED_COLUMNS, *skills, *tasks]


def _pad_cell(text: str, width: int, *, column: str) -> str:
    """Align one results-table cell.

    Parameters: text - cell text; width - column width; column - column name.

    Returns: padded cell text.
    """
    text = text.strip()
    return text.ljust(width) if column in RESULTS_LEFT_ALIGN else text.rjust(width)


def render_results_table(rows: list[dict[str, str]]) -> str:
    """Render an aligned pipe table.

    Parameters: rows - newest-first result rows.

    Returns: complete RESULTS text.
    """
    columns = results_table_columns(rows) if rows else list(RESULTS_FIXED_COLUMNS)
    widths = {
        column: max([len(column), *(len(row.get(column, "-")) for row in rows)])
        for column in columns
    }
    def render(values: dict[str, str]) -> str:
        return RESULTS_COL_SEP.join(
            _pad_cell(values.get(column, column), widths[column], column=column)
            for column in columns
        )
    header = render({})
    rule = RESULTS_COL_SEP.join("-" * widths[column] for column in columns)
    return "\n".join([header, rule, *(render(row) for row in rows)]) + "\n"


def looks_like_results_table(text: str) -> bool:
    """Recognize the aligned RESULTS format.

    Parameters: text - candidate file contents.

    Returns: whether text begins with the table header.
    """
    first = next((line for line in text.splitlines() if line.strip()), "")
    return first.startswith("Run") and RESULTS_COL_SEP in first


def _is_table_rule_line(line: str) -> bool:
    """Recognize a table separator line.

    Parameters: line - table line.

    Returns: whether the line contains only rule characters.
    """
    stripped = line.strip()
    return bool(stripped) and all(char in "-| " for char in stripped)


def _parse_table_row(headers: list[str], line: str) -> dict[str, str]:
    """Parse one aligned table row.

    Parameters: headers - column names; line - body line.

    Returns: parsed cells keyed by header.
    """
    cells = [cell.strip() for cell in line.split(RESULTS_COL_SEP)]
    return {
        header: cells[index] if index < len(cells) else "-"
        for index, header in enumerate(headers)
    }


def parse_results_table(text: str) -> list[dict[str, str]]:
    """Parse body rows from RESULTS text.

    Parameters: text - complete file contents.

    Returns: parsed body rows.
    """
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2 or not looks_like_results_table(text):
        return []
    headers = [cell.strip() for cell in lines[0].split(RESULTS_COL_SEP)]
    rows = [
        _parse_table_row(headers, line)
        for line in lines[1:]
        if not _is_table_rule_line(line)
    ]
    return [row for row in rows if row.get("Run")]


def write_results_table(path: Path, rows: list[dict[str, str]]) -> None:
    """Overwrite an aligned RESULTS table.

    Parameters: path - RESULTS file; rows - newest-first rows.

    Returns: nothing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_results_table(rows), encoding="utf-8")


def list_run_dirs(runs_root: Path) -> list[Path]:
    """List valid archive directories newest first.

    Parameters: runs_root - archive root.

    Returns: run directories.
    """
    if not runs_root.is_dir():
        return []
    found = [
        path for path in runs_root.iterdir()
        if path.is_dir()
        and not path.name.startswith(".")
        and (path / "00-meta.json").is_file()
    ]
    return sorted(found, key=lambda item: item.name, reverse=True)


def rebuild_results_index(runs_root: Path) -> Path:
    """Rebuild RESULTS from every archived run.

    Parameters: runs_root - archive root.

    Returns: RESULTS path.
    """
    runs_root.mkdir(parents=True, exist_ok=True)
    path = runs_root / RESULTS_INDEX_NAME
    rows = [format_results_row(run_dir) for run_dir in list_run_dirs(runs_root)]
    write_results_table(path, rows)
    log(f"wrote {path} rows={len(rows)}")
    return path


def _read_existing_rows(path: Path) -> list[dict[str, str]]:
    """Read aligned rows or report legacy replacement.

    Parameters: path - RESULTS file.

    Returns: existing aligned rows.
    """
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if looks_like_results_table(text):
        return parse_results_table(text)
    if text.strip():
        log(f"replacing legacy {path} with an aligned table")
    return []


def prepend_results_line(runs_root: Path, run_dir: Path) -> Path:
    """Prepend a run while dropping its prior row.

    Parameters: runs_root - archive root; run_dir - completed run.

    Returns: RESULTS path.
    """
    row = format_results_row(run_dir)
    path = runs_root / RESULTS_INDEX_NAME
    kept = [item for item in _read_existing_rows(path) if item.get("Run") != row["Run"]]
    write_results_table(path, [row, *kept])
    log(f"prepended {path} stamp={row['Run']} runtime={row['Runtime']} pass={row['Pass']}")
    return path

#!/usr/bin/env python3
"""Interactive Harbor benchmark launcher with git-tracked presets.

Opens one graphical terminal per job on the **same monitor** as the window
that started this program (the menu / ``./launch_benchmarks.sh``). Windows are
normal-sized and cascaded (not maximised or monitor-tiled). Presets live as
JSON under ``evals/presets/`` and are safe to commit.

Usage (from ``evals/``)::

    ./launch_benchmarks.sh
    ./launch_benchmarks.sh --preset positive-all-harnesses-all-judges
    ./launch_benchmarks.sh --list
    ./launch_benchmarks.sh --self-test

Stdout is the menu / machine-readable lists. Diagnostics go to stderr.
Tests must not spawn real terminals; ``--self-test`` uses a fake display.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


EVALS_DIR = Path(__file__).resolve().parent
PRESETS_DIR = EVALS_DIR / "presets"
RUN_SCRIPT = "run_benchmark.sh"
WINDOW_TITLE_PREFIX = "harbor-eval:"
XRANDR_CONNECTED_RE = re.compile(
    r"^(\S+)\s+connected(?:\s+primary)?\s+(\d+)x(\d+)\+(\d+)\+(\d+)",
    re.MULTILINE,
)
# Ordinary terminal size — do not stretch to fill a monitor tile.
NORMAL_WIDTH_PX = 1100
NORMAL_HEIGHT_PX = 700
GNOME_COLS = 100
GNOME_ROWS = 32
CASCADE_STEP_PX = 56
PLACE_RETRIES = 3
PLACE_WAIT_SEC = 0.15


def log(message: str) -> None:
    """Write one launcher line to stderr (stdout stays the menu / lists).

    Args:
        message: Text with no secrets.
    """
    print(f"launch_benchmarks: {message}", file=sys.stderr, flush=True)


@dataclass(frozen=True)
class Monitor:
    """One connected display in screen coordinates.

    Attributes:
        name: xrandr output name (``DP-4``, ``HDMI-0``, …).
        x: Left edge.
        y: Top edge.
        width: Pixel width (already rotated).
        height: Pixel height (already rotated).
    """

    name: str
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def contains(self, px: int, py: int) -> bool:
        """Return True when (px, py) lies inside this monitor."""
        return self.x <= px < self.right and self.y <= py < self.bottom

    def center_distance(self, px: int, py: int) -> float:
        """Euclidean distance from (px, py) to the monitor centre."""
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        return math.hypot(px - cx, py - cy)


@dataclass(frozen=True)
class Job:
    """One terminal to launch.

    Attributes:
        title: Short label (window title suffix).
        args: argv run from ``evals/`` (starts with ``./run_benchmark.sh``).
    """

    title: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class Preset:
    """A named list of Harbor jobs.

    Attributes:
        name: File stem / menu label.
        description: One-line summary.
        jobs: Terminals to open.
        path: JSON path, when loaded from disk.
    """

    name: str
    description: str
    jobs: tuple[Job, ...]
    path: Path | None = None


@dataclass(frozen=True)
class Rect:
    """Pixel rectangle for a cascaded terminal.

    Attributes:
        x: Left.
        y: Top.
        width: Width.
        height: Height.
    """

    x: int
    y: int
    width: int
    height: int


def slugify(name: str) -> str:
    """Turn a preset name into a filename stem.

    Args:
        name: Human title.
    """
    text = name.strip().lower()
    text = re.sub(r"[^a-z0-9._+-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-._")
    return text or "preset"


def window_title(job_title: str) -> str:
    """Return a unique WM title for xdotool search.

    Args:
        job_title: Preset job title.
    """
    return f"{WINDOW_TITLE_PREFIX} {job_title}"


def parse_xrandr(text: str) -> list[Monitor]:
    """Parse ``xrandr --current`` connected outputs.

    Args:
        text: Raw xrandr stdout.
    """
    monitors: list[Monitor] = []
    for match in XRANDR_CONNECTED_RE.finditer(text):
        monitors.append(
            Monitor(
                name=match.group(1),
                width=int(match.group(2)),
                height=int(match.group(3)),
                x=int(match.group(4)),
                y=int(match.group(5)),
            )
        )
    return monitors


def monitor_for_point(monitors: Sequence[Monitor], px: int, py: int) -> Monitor | None:
    """Return the monitor that contains (px, py), or the nearest.

    Args:
        monitors: Connected displays.
        px: Screen X.
        py: Screen Y.
    """
    if not monitors:
        return None
    for mon in monitors:
        if mon.contains(px, py):
            return mon
    return min(monitors, key=lambda item: item.center_distance(px, py))


def cascade_rects(
    monitor: Monitor,
    count: int,
    *,
    width: int = NORMAL_WIDTH_PX,
    height: int = NORMAL_HEIGHT_PX,
    step: int = CASCADE_STEP_PX,
) -> list[Rect]:
    """Stack *count* normal-sized windows with a small offset on *monitor*.

    Args:
        monitor: Target display.
        count: Number of windows.
        width: Desired pixel width (clamped to the monitor).
        height: Desired pixel height (clamped to the monitor).
        step: Cascade offset in pixels.
    """
    if count < 1:
        return []
    width = min(width, max(640, monitor.width - 80))
    height = min(height, max(400, monitor.height - 80))
    max_x = monitor.x + max(0, monitor.width - width - 16)
    max_y = monitor.y + max(0, monitor.height - height - 16)
    start_x = min(monitor.x + 48, max_x)
    start_y = min(monitor.y + 48, max_y)
    span_x = max(step, max_x - start_x)
    span_y = max(step, max_y - start_y)
    rects: list[Rect] = []
    for index in range(count):
        rects.append(
            Rect(
                x=start_x + (index * step) % span_x,
                y=start_y + (index * step) % span_y,
                width=width,
                height=height,
            )
        )
    return rects


def parse_job(raw: dict[str, Any], *, index: int) -> Job:
    """Build a Job from one preset JSON object.

    Args:
        raw: ``{"title": ..., "args": [...]}``.
        index: 1-based index for error messages.
    """
    title = str(raw.get("title") or f"job-{index}").strip()
    args_raw = raw.get("args")
    if not isinstance(args_raw, list) or not args_raw:
        raise ValueError(f"job {index} needs a non-empty args array")
    args = tuple(str(item) for item in args_raw)
    script = Path(args[0]).name
    if script != RUN_SCRIPT:
        raise ValueError(f"job {index} must run {RUN_SCRIPT}, got {args[0]!r}")
    if not title:
        raise ValueError(f"job {index} has an empty title")
    return Job(title=title, args=args)


def parse_preset(payload: dict[str, Any], *, path: Path | None = None) -> Preset:
    """Load a Preset from JSON.

    Args:
        payload: Root object.
        path: Source file, if any.
    """
    name = str(payload.get("name") or (path.stem if path else "preset")).strip()
    description = str(payload.get("description") or "").strip()
    jobs_raw = payload.get("jobs")
    if not isinstance(jobs_raw, list) or not jobs_raw:
        raise ValueError("preset needs a non-empty jobs array")
    jobs = tuple(parse_job(item, index=i) for i, item in enumerate(jobs_raw, start=1))
    titles = [job.title for job in jobs]
    if len(titles) != len(set(titles)):
        raise ValueError("preset job titles must be unique (window names)")
    return Preset(name=slugify(name), description=description, jobs=jobs, path=path)


def preset_to_json(preset: Preset) -> dict[str, Any]:
    """Serialize *preset* for disk.

    Args:
        preset: In-memory preset.
    """
    return {
        "name": preset.name,
        "description": preset.description,
        "jobs": [{"title": job.title, "args": list(job.args)} for job in preset.jobs],
    }


def load_preset_file(path: Path) -> Preset:
    """Read and validate one preset JSON file.

    Args:
        path: File under ``evals/presets/``.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must be a JSON object")
    return parse_preset(payload, path=path)


def list_preset_files(directory: Path = PRESETS_DIR) -> list[Path]:
    """Return preset JSON paths, sorted by stem.

    Args:
        directory: Presets folder.
    """
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"), key=lambda item: item.stem)


def resolve_preset(name: str, directory: Path = PRESETS_DIR) -> Path:
    """Resolve a preset name or path to a JSON file.

    Args:
        name: Stem, filename, or path.
        directory: Presets folder.
    """
    candidate = Path(name)
    if candidate.is_file():
        return candidate
    direct = directory / name
    if direct.is_file():
        return direct
    if not name.endswith(".json"):
        with_ext = directory / f"{name}.json"
        if with_ext.is_file():
            return with_ext
    raise FileNotFoundError(f"preset not found: {name} (looked in {directory})")


def save_preset(preset: Preset, directory: Path = PRESETS_DIR) -> Path:
    """Write *preset* as JSON and return the path.

    Args:
        preset: Preset to store.
        directory: Presets folder.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{preset.name}.json"
    path.write_text(json.dumps(preset_to_json(preset), indent=2) + "\n", encoding="utf-8")
    log(f"saved preset {path}")
    return path


def jobs_from_command_lines(lines: Sequence[str]) -> tuple[Job, ...]:
    """Parse pasted ``./run_benchmark.sh …`` lines into jobs.

    Args:
        lines: One command per line; blanks ignored.
    """
    jobs: list[Job] = []
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        args = tuple(shlex.split(stripped))
        script = Path(args[0]).name if args else ""
        if script != RUN_SCRIPT:
            raise ValueError(f"line {index} must start with {RUN_SCRIPT}")
        title = _title_from_args(args, fallback=f"job-{len(jobs) + 1}")
        jobs.append(Job(title=title, args=args))
    if not jobs:
        raise ValueError("no commands to save")
    seen: dict[str, int] = {}
    unique: list[Job] = []
    for job in jobs:
        count = seen.get(job.title, 0) + 1
        seen[job.title] = count
        title = job.title if count == 1 else f"{job.title} {count}"
        unique.append(Job(title=title, args=job.args))
    return tuple(unique)


def _title_from_args(args: Sequence[str], *, fallback: str) -> str:
    harness = "harness"
    agent = "inherit"
    for item in args:
        if item.startswith("harness="):
            harness = item.split("=", 1)[1] or harness
        if item.startswith("evalAgent=") or item.startswith("eval-agent="):
            agent = item.split("=", 1)[1] or agent
    if harness == "harness" and agent == "inherit":
        return fallback
    return f"{harness} x {agent}"


def shell_command(args: Sequence[str]) -> str:
    """Quote *args* for ``bash -lc``.

    Args:
        args: argv.
    """
    return " ".join(shlex.quote(part) for part in args)


def terminal_script(title: str, args: Sequence[str]) -> str:
    """Inner bash that runs one Harbor job and waits.

    Args:
        title: Window title (also set via OSC).
        args: argv from evals/.
    """
    quoted_title = shlex.quote(title)
    body = shell_command(args)
    return (
        f"printf '\\033]0;%s\\007' {quoted_title}; "
        f"echo {quoted_title}; echo; "
        f"{body}; "
        "status=$?; echo; echo exit=$status; "
        "read -r -p 'Press Enter to close this window...'"
    )


class Display:
    """How to inspect the desktop and open terminals. Live or fake."""

    def active_window_center(self) -> tuple[int, int]:
        raise NotImplementedError

    def list_monitors(self) -> list[Monitor]:
        raise NotImplementedError

    def preferred_terminal(self) -> str:
        raise NotImplementedError

    def spawn_terminal(
        self, title: str, cwd: Path, script: str, rect: Rect | None = None
    ) -> None:
        raise NotImplementedError

    def place_window(self, title: str, rect: Rect) -> None:
        raise NotImplementedError


class X11Display(Display):
    """X11 via xrandr + xdotool + gnome-terminal or kitty."""

    def __init__(self, *, run: Callable[..., str] | None = None) -> None:
        self._run = run or _run_capture

    def active_window_center(self) -> tuple[int, int]:
        window = os.environ.get("WINDOWID", "").strip()
        if not window:
            window = self._run(["xdotool", "getactivewindow"]).strip()
        geom = self._run(["xdotool", "getwindowgeometry", "--shell", window])
        values: dict[str, int] = {}
        for line in geom.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                try:
                    values[key] = int(value)
                except ValueError:
                    continue
        x = values.get("X", 0)
        y = values.get("Y", 0)
        width = values.get("WIDTH", 0)
        height = values.get("HEIGHT", 0)
        return x + width // 2, y + height // 2

    def list_monitors(self) -> list[Monitor]:
        text = self._run(["xrandr", "--current"])
        monitors = parse_xrandr(text)
        if not monitors:
            raise RuntimeError("xrandr reported no connected monitors")
        return monitors

    def preferred_terminal(self) -> str:
        if os.environ.get("KITTY_WINDOW_ID") or os.environ.get("TERM") == "xterm-kitty":
            if shutil.which("kitty"):
                return "kitty"
        if shutil.which("gnome-terminal"):
            return "gnome-terminal"
        if shutil.which("kitty"):
            return "kitty"
        raise RuntimeError("need gnome-terminal or kitty on PATH")

    def spawn_terminal(
        self, title: str, cwd: Path, script: str, rect: Rect | None = None
    ) -> None:
        kind = self.preferred_terminal()
        if kind == "kitty":
            cmd = [
                "kitty",
                "--title",
                title,
                "--detach",
                "--directory",
                str(cwd),
                "-o",
                "remember_window_size=no",
                "-o",
                f"initial_window_width={rect.width if rect else NORMAL_WIDTH_PX}",
                "-o",
                f"initial_window_height={rect.height if rect else NORMAL_HEIGHT_PX}",
                "bash",
                "-lc",
                script,
            ]
        else:
            if rect is not None:
                geometry = f"{GNOME_COLS}x{GNOME_ROWS}+{rect.x}+{rect.y}"
            else:
                geometry = f"{GNOME_COLS}x{GNOME_ROWS}"
            cmd = [
                "gnome-terminal",
                f"--title={title}",
                f"--geometry={geometry}",
                f"--working-directory={cwd}",
                "--",
                "bash",
                "-lc",
                script,
            ]
        log(f"spawn {kind} title={title!r} geometry={rect}")
        subprocess.Popen(cmd, cwd=str(cwd), env=os.environ.copy(), start_new_session=True)

    def place_window(self, title: str, rect: Rect) -> None:
        """Move an already-normal-sized window; never stretch it to fill a tile."""
        last_error = ""
        for attempt in range(PLACE_RETRIES):
            try:
                self._run(
                    [
                        "xdotool",
                        "search",
                        "--sync",
                        "--limit",
                        "1",
                        "--name",
                        title,
                        "windowmove",
                        str(rect.x),
                        str(rect.y),
                    ]
                )
                log(f"moved {title!r} to {rect.x},{rect.y}")
                return
            except RuntimeError as exc:
                last_error = str(exc)
                time.sleep(PLACE_WAIT_SEC * (attempt + 1))
        log(f"could not move {title!r} onto this monitor: {last_error}")


class FakeDisplay(Display):
    """In-memory display for --self-test (never opens windows)."""

    def __init__(
        self,
        monitors: list[Monitor],
        center: tuple[int, int],
        terminal: str = "gnome-terminal",
    ) -> None:
        self.monitors = monitors
        self.center = center
        self.terminal = terminal
        self.spawned: list[tuple[str, str]] = []
        self.placed: list[tuple[str, Rect]] = []
        self.events: list[str] = []

    def active_window_center(self) -> tuple[int, int]:
        return self.center

    def list_monitors(self) -> list[Monitor]:
        return list(self.monitors)

    def preferred_terminal(self) -> str:
        return self.terminal

    def spawn_terminal(
        self, title: str, cwd: Path, script: str, rect: Rect | None = None
    ) -> None:
        self.events.append("spawn")
        self.spawned.append((title, script))

    def place_window(self, title: str, rect: Rect) -> None:
        self.events.append("place")
        self.placed.append((title, rect))


def _run_capture(argv: Sequence[str]) -> str:
    """Run a host command and return stdout, or raise.

    Args:
        argv: Command and flags.
    """
    proc = subprocess.run(
        list(argv),
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"{' '.join(argv)} failed: {err}")
    return proc.stdout


def launch_preset(
    preset: Preset,
    display: Display,
    *,
    cwd: Path = EVALS_DIR,
    dry_run: bool = False,
) -> Monitor:
    """Open each job as a normal-sized window on this terminal's monitor.

    Spawns every window first so they appear together, then nudges them
    onto the monitor. Does not stretch windows to fill the display.

    Args:
        preset: Jobs to start.
        display: Live X11 or fake backend.
        cwd: Working directory (evals/).
        dry_run: Log placements without spawning.

    Returns:
        The monitor that received the windows.
    """
    monitors = display.list_monitors()
    cx, cy = display.active_window_center()
    monitor = monitor_for_point(monitors, cx, cy)
    if monitor is None:
        raise RuntimeError("no monitor for this terminal")
    log(
        f"this window centre {cx},{cy} is on {monitor.name} "
        f"{monitor.width}x{monitor.height} at {monitor.x},{monitor.y}"
    )
    rects = cascade_rects(monitor, len(preset.jobs))
    for job, rect in zip(preset.jobs, rects, strict=True):
        title = window_title(job.title)
        script = terminal_script(title, job.args)
        log(
            f"job {job.title}: {shell_command(job.args)} "
            f"-> {rect.x},{rect.y} {rect.width}x{rect.height}"
        )
        if dry_run:
            continue
        display.spawn_terminal(title, cwd, script, rect)
    if not dry_run:
        for job, rect in zip(preset.jobs, rects, strict=True):
            display.place_window(window_title(job.title), rect)
    log(f"launched {len(preset.jobs)} job(s) on {monitor.name}")
    return monitor


def print_preset_list(directory: Path = PRESETS_DIR) -> None:
    """Print presets as a numbered table on stdout."""
    files = list_preset_files(directory)
    if not files:
        print(f"No presets in {directory}")
        return
    for index, path in enumerate(files, start=1):
        try:
            preset = load_preset_file(path)
            extra = f"  {len(preset.jobs)} jobs  {preset.description}".rstrip()
            print(f"  {index}) {preset.name}{extra}")
        except ValueError as exc:
            print(f"  {index}) {path.stem}  (invalid: {exc})")


def _prompt(text: str) -> str:
    try:
        return input(text)
    except EOFError as exc:
        raise SystemExit("stdin closed") from exc


def menu_loop(display: Display, *, directory: Path = PRESETS_DIR) -> int:
    """CMD-style numbered menu until quit.

    Args:
        display: Desktop backend.
        directory: Presets folder.
    """
    while True:
        files = list_preset_files(directory)
        try:
            monitors = display.list_monitors()
            cx, cy = display.active_window_center()
            here = monitor_for_point(monitors, cx, cy)
            here_text = (
                f"{here.name} {here.width}x{here.height} at {here.x},{here.y}"
                if here
                else "unknown"
            )
        except Exception as exc:  # noqa: BLE001 — menu must still open
            here_text = f"(cannot read display: {exc})"
        print()
        print("Harbor benchmark launcher")
        print(f"This terminal's monitor: {here_text}")
        print(f"Presets in {directory}:")
        if not files:
            print("  (none yet — press s to save one)")
        for index, path in enumerate(files, start=1):
            try:
                preset = load_preset_file(path)
                print(
                    f"  {index}) {preset.name}  "
                    f"[{len(preset.jobs)} jobs]  {preset.description}"
                )
            except ValueError as exc:
                print(f"  {index}) {path.name}  INVALID ({exc})")
        print("  s) save new preset from pasted commands")
        print("  q) quit")
        choice = _prompt("Number or letter: ").strip().lower()
        if choice in {"q", "quit"}:
            return 0
        if choice in {"s", "save"}:
            _save_from_paste(directory)
            continue
        if not choice.isdigit():
            print("Unknown choice.", file=sys.stderr)
            continue
        number = int(choice)
        if number < 1 or number > len(files):
            print("No preset with that number.", file=sys.stderr)
            continue
        try:
            preset = load_preset_file(files[number - 1])
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            continue
        confirm = _prompt(
            f"Launch {len(preset.jobs)} job(s) on this monitor? [Y/n] "
        ).strip().lower()
        if confirm in {"n", "no"}:
            continue
        launch_preset(preset, display)
    return 0


def _save_from_paste(directory: Path) -> None:
    """Interactive: name + description + commands, then write JSON."""
    name = slugify(_prompt("Preset name: "))
    description = _prompt("Description (one line): ").strip()
    print("Paste ./run_benchmark.sh commands, one per line. Empty line ends.")
    lines: list[str] = []
    while True:
        line = _prompt("")
        if not line.strip():
            break
        lines.append(line)
    try:
        jobs = jobs_from_command_lines(lines)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return
    path = save_preset(
        Preset(name=name, description=description, jobs=jobs),
        directory,
    )
    print(f"Saved {path} ({len(jobs)} jobs). Commit it if you want it in git.")


def _self_test() -> int:
    """Fixture checks: xrandr parse, tiling, presets, fake launch.

    Returns:
        0 when every case passes.
    """
    cases: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))

    xrandr = """
Screen 0: minimum 8 x 8, current 6000 x 5006, maximum 32767 x 32767
HDMI-0 connected 2160x3840+3840+1166 right (normal left inverted right x axis y axis) 632mm x 360mm
DP-0 connected 3840x2160+0+0 (normal left inverted right x axis y axis) 600mm x 340mm
DP-4 connected primary 3840x2160+0+2160 (normal left inverted right x axis y axis) 700mm x 390mm
HDMI-1 disconnected (normal left inverted right x axis y axis)
"""
    monitors = parse_xrandr(xrandr)
    record("xrandr_count", len(monitors) == 3, f"got {len(monitors)}")
    by_name = {item.name: item for item in monitors}
    record(
        "dp4_geometry",
        by_name["DP-4"] == Monitor("DP-4", 0, 2160, 3840, 2160),
        str(by_name.get("DP-4")),
    )
    record(
        "hdmi_rotated_size",
        by_name["HDMI-0"].width == 2160 and by_name["HDMI-0"].height == 3840,
        "portrait already in screen pixels",
    )
    record(
        "point_dp4",
        monitor_for_point(monitors, 1920, 3200).name == "DP-4",
        "Cursor/terminal on primary bottom",
    )
    record(
        "point_dp0",
        monitor_for_point(monitors, 100, 100).name == "DP-0",
        "top monitor",
    )
    record(
        "point_hdmi",
        monitor_for_point(monitors, 4000, 2000).name == "HDMI-0",
        "portrait output",
    )
    dp4 = by_name["DP-4"]
    tiles = cascade_rects(dp4, 9)
    record("cascade_count", len(tiles) == 9, str(len(tiles)))
    record(
        "cascade_normal_size",
        all(rect.width == NORMAL_WIDTH_PX and rect.height == NORMAL_HEIGHT_PX for rect in tiles),
        f"{tiles[0].width}x{tiles[0].height}" if tiles else "none",
    )
    record(
        "cascade_not_maximized",
        all(rect.height < dp4.height // 2 and rect.width < dp4.width // 2 for rect in tiles),
        "smaller than half the monitor",
    )
    record(
        "cascade_inside",
        all(
            dp4.contains(rect.x, rect.y)
            and rect.x + rect.width <= dp4.right
            and rect.y + rect.height <= dp4.bottom
            for rect in tiles
        ),
        "cascade stays on DP-4",
    )
    record(
        "cascade_offset",
        len(tiles) >= 2 and (tiles[0].x != tiles[1].x or tiles[0].y != tiles[1].y),
        "windows are staggered",
    )
    shipped = EVALS_DIR / "presets" / "positive-all-harnesses-all-judges.json"
    preset: Preset | None = None
    try:
        preset = load_preset_file(shipped)
        record("shipped_nine", len(preset.jobs) == 9, f"jobs={len(preset.jobs)}")
        record(
            "shipped_matrix",
            {job.title for job in preset.jobs}
            == {
                "codex x codex",
                "codex x cc",
                "codex x grok",
                "cc x codex",
                "cc x cc",
                "cc x grok",
                "grok x codex",
                "grok x cc",
                "grok x grok",
            },
            "3x3 titles",
        )
        record(
            "shipped_positive",
            all("--baseline" not in job.args for job in preset.jobs),
            "no --baseline",
        )
        record(
            "shipped_skills",
            all("srp,commenting,logging,worktree" in job.args for job in preset.jobs),
            "all four skills",
        )
    except (ValueError, OSError) as exc:
        record("shipped_nine", False, str(exc))

    parsed = jobs_from_command_lines(
        [
            './run_benchmark.sh harness=codex evalAgent=grok --skills srp -k 1 -n 1',
            "",
            './run_benchmark.sh harness=cc evalAgent=cc --skills srp -k 1 -n 1',
        ]
    )
    record(
        "parse_paste",
        parsed[0].title == "codex x grok" and parsed[1].title == "cc x cc",
        str([job.title for job in parsed]),
    )
    try:
        jobs_from_command_lines(["echo hi"])
        record("reject_non_runner", False, "should have raised")
    except ValueError:
        record("reject_non_runner", True, "only run_benchmark.sh")

    fake = FakeDisplay(monitors, (1920, 3200))
    if preset is not None:
        launched = launch_preset(preset, fake, dry_run=False)
        record("fake_monitor", launched.name == "DP-4", launched.name)
        record("fake_spawn_count", len(fake.spawned) == 9, str(len(fake.spawned)))
        record("fake_placed_count", len(fake.placed) == 9, str(len(fake.placed)))
        record(
            "spawn_all_first",
            fake.events[:9] == ["spawn"] * 9 and fake.events[9:] == ["place"] * 9,
            str(fake.events),
        )
        record(
            "fake_titles_prefixed",
            all(title.startswith(WINDOW_TITLE_PREFIX) for title, _ in fake.spawned),
            "xdotool search names",
        )
        record(
            "fake_script_has_runner",
            all(RUN_SCRIPT in script for _, script in fake.spawned),
            "inner bash runs the wrapper",
        )
    else:
        record("fake_monitor", False, "shipped preset missing")
    record("slug", slugify("Positive All!") == "positive-all", slugify("Positive All!"))

    import tempfile

    with tempfile.TemporaryDirectory(prefix="harbor-presets-") as raw:
        folder = Path(raw)
        saved = save_preset(
            Preset(name="smoke", description="one job", jobs=parsed[:1]),
            folder,
        )
        reloaded = load_preset_file(saved)
        record(
            "roundtrip",
            reloaded.name == "smoke" and reloaded.jobs[0].args[0].endswith(RUN_SCRIPT),
            saved.name,
        )

    failed = [(name, msg) for name, ok, msg in cases if not ok]
    for name, ok, msg in cases:
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {name}: {msg}", flush=True)
    if failed:
        print(f"{len(failed)}/{len(cases)} launch_benchmarks case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} launch_benchmarks cases passed", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preset",
        help="Launch this preset (stem or path) without the menu",
    )
    parser.add_argument("--list", action="store_true", help="Print presets and exit")
    parser.add_argument("--self-test", action="store_true", help="Fixture checks")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --preset: log monitor + tiles, do not spawn windows",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="With --preset: skip the launch confirmation",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.list:
        print_preset_list()
        return 0

    display: Display = X11Display()
    if args.preset:
        path = resolve_preset(args.preset)
        preset = load_preset_file(path)
        if not args.yes and not args.dry_run and sys.stdin.isatty():
            answer = _prompt(
                f"Launch {len(preset.jobs)} job(s) from {preset.name} "
                "on this monitor? [Y/n] "
            ).strip().lower()
            if answer in {"n", "no"}:
                return 0
        launch_preset(preset, display, dry_run=args.dry_run)
        return 0

    if not sys.stdin.isatty():
        print(
            "No TTY. Use --preset NAME, --list, or --self-test.",
            file=sys.stderr,
        )
        return 2
    return menu_loop(display)


if __name__ == "__main__":
    sys.exit(main())

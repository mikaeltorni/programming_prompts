"""Live and fake display backends plus preset launch orchestration."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, Sequence

from .geometry import (
    NORMAL_HEIGHT_PX,
    NORMAL_WIDTH_PX,
    Monitor,
    Rect,
    cascade_rects,
    monitor_for_point,
    parse_xrandr,
)
from .log import log
from .presets import EVALS_DIR, Preset
from .terminal_script import shell_command, terminal_script, window_title

GNOME_COLS = 100
GNOME_ROWS = 32
PLACE_RETRIES = 3
PLACE_WAIT_SEC = 0.15


class Display:
    """How to inspect the desktop and open terminals."""

    def active_window_center(self) -> tuple[int, int]:
        """Read the active window center.

        Parameters: none.

        Returns: screen X and Y.
        """
        raise NotImplementedError

    def list_monitors(self) -> list[Monitor]:
        """List connected monitors.

        Parameters: none.

        Returns: connected display geometry.
        """
        raise NotImplementedError

    def preferred_terminal(self) -> str:
        """Choose an available terminal emulator.

        Parameters: none.

        Returns: terminal executable name.
        """
        raise NotImplementedError

    def spawn_terminal(
        self, title: str, cwd: Path, script: str, rect: Rect | None = None
    ) -> None:
        """Spawn one terminal window.

        Parameters: title - window title; cwd - working directory; script - inner bash; rect - desired geometry.

        Returns: None.
        """
        raise NotImplementedError

    def place_window(self, title: str, rect: Rect) -> None:
        """Place an existing window.

        Parameters: title - searchable window title; rect - target geometry.

        Returns: None.
        """
        raise NotImplementedError


class X11Display(Display):
    """X11 backend using xrandr, xdotool, and a graphical terminal."""

    def __init__(self, *, run: Callable[..., str] | None = None) -> None:
        """Initialize the live display backend.

        Parameters: run - optional command-capture dependency.

        Returns: None.
        """
        self._run = run or _run_capture

    def active_window_center(self) -> tuple[int, int]:
        """Read the active X11 window center.

        Parameters: none.

        Returns: screen X and Y.
        """
        window = os.environ.get("WINDOWID", "").strip()
        if not window:
            window = self._run(["xdotool", "getactivewindow"]).strip()
        geom = self._run(["xdotool", "getwindowgeometry", "--shell", window])
        values: dict[str, int] = {}
        for line in geom.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            try:
                values[key] = int(value)
            except ValueError:
                continue
        return (
            values.get("X", 0) + values.get("WIDTH", 0) // 2,
            values.get("Y", 0) + values.get("HEIGHT", 0) // 2,
        )

    def list_monitors(self) -> list[Monitor]:
        """Read connected X11 monitors.

        Parameters: none.

        Returns: parsed monitor geometry.
        """
        monitors = parse_xrandr(self._run(["xrandr", "--current"]))
        if not monitors:
            raise RuntimeError("xrandr reported no connected monitors")
        return monitors

    def preferred_terminal(self) -> str:
        """Choose kitty for kitty sessions or the first available terminal.

        Parameters: none.

        Returns: ``kitty`` or ``gnome-terminal``.
        """
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
        """Spawn one normal-sized graphical terminal.

        Parameters: title - window title; cwd - working directory; script - inner bash; rect - desired geometry.

        Returns: None.
        """
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
            geometry = (
                f"{GNOME_COLS}x{GNOME_ROWS}+{rect.x}+{rect.y}"
                if rect is not None
                else f"{GNOME_COLS}x{GNOME_ROWS}"
            )
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
        """Move an existing normal-sized window.

        Parameters: title - searchable window title; rect - target geometry.

        Returns: None.
        """
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
    """In-memory display used by self-test without opening windows."""

    def __init__(
        self,
        monitors: list[Monitor],
        center: tuple[int, int],
        terminal: str = "gnome-terminal",
    ) -> None:
        """Initialize the side-effect-free display backend.

        Parameters: monitors - fake monitor geometry; center - fake active-window center; terminal - fake terminal name.

        Returns: None.
        """
        self.monitors = monitors
        self.center = center
        self.terminal = terminal
        self.spawned: list[tuple[str, str]] = []
        self.placed: list[tuple[str, Rect]] = []
        self.events: list[str] = []

    def active_window_center(self) -> tuple[int, int]:
        """Return the configured fake center.

        Parameters: none.

        Returns: screen X and Y.
        """
        return self.center

    def list_monitors(self) -> list[Monitor]:
        """Return configured fake monitors.

        Parameters: none.

        Returns: a copy of fake monitor geometry.
        """
        return list(self.monitors)

    def preferred_terminal(self) -> str:
        """Return the configured fake terminal.

        Parameters: none.

        Returns: terminal executable name.
        """
        return self.terminal

    def spawn_terminal(
        self, title: str, cwd: Path, script: str, rect: Rect | None = None
    ) -> None:
        """Record a terminal spawn without side effects.

        Parameters: title - window title; cwd - unused working directory; script - inner bash; rect - unused geometry.

        Returns: None.
        """
        self.events.append("spawn")
        self.spawned.append((title, script))

    def place_window(self, title: str, rect: Rect) -> None:
        """Record a window placement without side effects.

        Parameters: title - window title; rect - target geometry.

        Returns: None.
        """
        self.events.append("place")
        self.placed.append((title, rect))


def _run_capture(argv: Sequence[str]) -> str:
    """Run a host command and capture stdout.

    Parameters: argv - command and flags.

    Returns: command stdout.
    """
    proc = subprocess.run(
        list(argv),
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        error = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"{' '.join(argv)} failed: {error}")
    return proc.stdout


def launch_preset(
    preset: Preset,
    display: Display,
    *,
    cwd: Path = EVALS_DIR,
    dry_run: bool = False,
) -> Monitor:
    """Launch a preset on the initiating terminal's monitor.

    Parameters: preset - jobs to start; display - live or fake backend; cwd - evals working directory; dry_run - log without spawning.

    Returns: the monitor selected for the windows.
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
        if not dry_run:
            display.spawn_terminal(title, cwd, script, rect)
    if not dry_run:
        for job, rect in zip(preset.jobs, rects, strict=True):
            display.place_window(window_title(job.title), rect)
    log(f"launched {len(preset.jobs)} job(s) on {monitor.name}")
    return monitor

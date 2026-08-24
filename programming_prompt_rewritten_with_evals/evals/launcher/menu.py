"""Interactive launcher menu and preset creation from pasted commands."""

from __future__ import annotations

import sys
from pathlib import Path

from .display import Display, launch_preset
from .geometry import monitor_for_point
from .presets import (
    PRESETS_DIR,
    Preset,
    format_preset_listing,
    jobs_from_command_lines,
    list_preset_files,
    load_preset_file,
    save_preset,
    slugify,
)


def print_preset_list(directory: Path = PRESETS_DIR) -> None:
    """Print presets as a numbered table.

    Parameters: directory - presets folder.

    Returns: None.
    """
    files = list_preset_files(directory)
    if not files:
        print(f"No presets in {directory}")
        return
    for index, path in enumerate(files, start=1):
        try:
            preset = load_preset_file(path)
            extra = f"  {format_preset_listing(preset)}"
            print(f"  {index}) {preset.name}{extra}")
        except ValueError as exc:
            print(f"  {index}) {path.stem}  (invalid: {exc})")


def _prompt(text: str) -> str:
    """Read one interactive answer.

    Parameters: text - input prompt.

    Returns: entered text.
    """
    try:
        return input(text)
    except EOFError as exc:
        raise SystemExit("stdin closed") from exc


def _save_from_paste(directory: Path) -> None:
    """Save a preset from interactively pasted commands.

    Parameters: directory - presets folder.

    Returns: None.
    """
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


def menu_loop(display: Display, *, directory: Path = PRESETS_DIR) -> int:
    """Run the numbered menu until quit.

    Parameters: display - desktop backend; directory - presets folder.

    Returns: zero after the user quits.
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
        except Exception as exc:  # noqa: BLE001 - menu must still open
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
                print(f"  {index}) {preset.name}  {format_preset_listing(preset)}")
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
        launch_preset(preset, display)

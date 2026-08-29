"""Side-effect-free launcher fixtures using only the fake display backend."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Sequence

from .display import FakeDisplay, launch_preset
from .geometry import (
    NORMAL_HEIGHT_PX,
    NORMAL_WIDTH_PX,
    Monitor,
    cascade_rects,
    monitor_for_point,
    parse_xrandr,
)
from .presets import (
    DEFAULT_SKILLS,
    HARNESS_ORDER,
    PRESETS_DIR,
    RUN_SCRIPT,
    Preset,
    format_preset_listing,
    _job_eval_agents,
    _job_harness,
    jobs_from_command_lines,
    list_preset_files,
    load_preset_file,
    matrix_jobs,
    matrix_preset_name,
    save_preset,
    shipped_matrix_groups,
    shipped_presets,
    slugify,
    write_shipped_presets,
)
from .terminal_script import WINDOW_TITLE_PREFIX


def _self_test() -> int:
    """Run fixture checks without opening real terminals.

    Parameters: none.

    Returns: zero when every case passes, otherwise one.
    """
    cases: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        """Record one fixture result.

        Parameters: name - case name; ok - pass state; detail - diagnostic text.

        Returns: None.
        """
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
        all(
            rect.width == NORMAL_WIDTH_PX and rect.height == NORMAL_HEIGHT_PX
            for rect in tiles
        ),
        f"{tiles[0].width}x{tiles[0].height}" if tiles else "none",
    )
    record(
        "cascade_not_maximized",
        all(
            rect.height < dp4.height // 2 and rect.width < dp4.width // 2
            for rect in tiles
        ),
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
        len(tiles) >= 2
        and (tiles[0].x != tiles[1].x or tiles[0].y != tiles[1].y),
        "windows are staggered",
    )
    catalog = shipped_presets()
    catalog_names = [item.name for item in catalog]
    expected_stems = {
        "positive-all-harnesses-all-judges",
        "baseline-all-harnesses-all-judges",
        "positive-codex-cc",
        "baseline-codex-cc",
        "positive-codex-grok",
        "baseline-codex-grok",
        "positive-cc-grok",
        "baseline-cc-grok",
        "positive-codex",
        "baseline-codex",
        "positive-cc",
        "baseline-cc",
        "positive-grok",
        "baseline-grok",
    }
    record("catalog_size", len(catalog) == 14, str(len(catalog)))
    record(
        "catalog_stems",
        set(catalog_names) == expected_stems,
        str(sorted(set(catalog_names) ^ expected_stems)),
    )
    try:
        matrix_jobs((), baseline=False)
        record("empty_matrix", False, "should have raised")
    except ValueError:
        record("empty_matrix", True, "need at least one harness")

    def matrix_issues(
        preset: Preset, harnesses: Sequence[str], *, baseline: bool
    ) -> str:
        """Find matrix contract violations.

        Parameters: preset - matrix preset; harnesses - expected IDs; baseline - expected mode.

        Returns: comma-separated issues or an empty string.
        """
        issues: list[str] = []
        if len(preset.jobs) != len(harnesses):
            issues.append(f"jobs={len(preset.jobs)}")
        if any(("--baseline" in job.args) is not baseline for job in preset.jobs):
            issues.append("baseline-flag")
        if any(DEFAULT_SKILLS not in job.args for job in preset.jobs):
            issues.append("skills")
        if any("-n" in job.args or "--n-concurrent" in job.args for job in preset.jobs):
            issues.append("explicit-n")
        excluded = [item for item in HARNESS_ORDER if item not in harnesses]
        for harness in excluded:
            if any(
                _job_harness(job) == harness or harness in _job_eval_agents(job)
                for job in preset.jobs
            ):
                issues.append(f"leaked-{harness}")
        for harness in harnesses:
            if not any(_job_harness(job) == harness for job in preset.jobs):
                issues.append(f"no-coder-{harness}")
            if any(harness not in _job_eval_agents(job) for job in preset.jobs):
                issues.append(f"no-judge-{harness}")
        judges = ",".join(harnesses)
        if {job.title for job in preset.jobs} != {
            f"{harness} x {judges}" for harness in harnesses
        }:
            issues.append("titles")
        if any(f"evalAgent={judges}" not in job.args for job in preset.jobs):
            issues.append("shared-evalAgent")
        return ",".join(issues)

    for harnesses in shipped_matrix_groups():
        for baseline in (False, True):
            preset_item = next(
                item
                for item in catalog
                if item.name == matrix_preset_name(harnesses, baseline=baseline)
            )
            problems = matrix_issues(preset_item, harnesses, baseline=baseline)
            record(preset_item.name, not problems, problems or "ok")

    disk_stems = {path.stem for path in PRESETS_DIR.glob("*.json")}
    record(
        "catalog_on_disk",
        expected_stems <= disk_stems,
        f"missing={sorted(expected_stems - disk_stems)}",
    )
    disk_mismatch: list[str] = []
    for expected in catalog:
        path = PRESETS_DIR / f"{expected.name}.json"
        try:
            loaded = load_preset_file(path)
        except (ValueError, OSError) as exc:
            disk_mismatch.append(f"{expected.name}:{exc}")
            continue
        if loaded.jobs != expected.jobs or loaded.description != expected.description:
            disk_mismatch.append(expected.name)
    record("catalog_matches_disk", not disk_mismatch, ",".join(disk_mismatch) or "ok")
    listed = [path.stem for path in list_preset_files(PRESETS_DIR)]
    record(
        "catalog_menu_order",
        listed[: len(catalog_names)] == catalog_names,
        str(listed[: len(catalog_names)]),
    )
    two_way = next(item for item in catalog if item.name == "positive-codex-cc")
    two_listing = format_preset_listing(two_way)
    record(
        "menu_two_judges",
        "[2 coding × judges=codex,cc]" in two_listing
        and "no grok" in two_listing
        and "no cc," not in two_listing,
        two_listing,
    )
    three_listing = format_preset_listing(
        next(
            item
            for item in catalog
            if item.name == "positive-all-harnesses-all-judges"
        )
    )
    record(
        "menu_three_judges",
        "[3 coding × judges=codex,cc,grok]" in three_listing,
        three_listing,
    )

    preset: Preset | None = None
    try:
        preset = load_preset_file(
            PRESETS_DIR / "positive-all-harnesses-all-judges.json"
        )
        record("shipped_three", len(preset.jobs) == 3, f"jobs={len(preset.jobs)}")
        record(
            "shipped_shared_judges",
            all("evalAgent=codex,cc,grok" in job.args for job in preset.jobs),
            "one coding run, three judges",
        )
        record(
            "shipped_positive",
            all("--baseline" not in job.args for job in preset.jobs),
            "no --baseline",
        )
    except (ValueError, OSError) as exc:
        record("shipped_three", False, str(exc))

    parsed = jobs_from_command_lines(
        [
            "./run_benchmark.sh harness=codex evalAgent=grok --skills srp -k 1 -n 1",
            "",
            "./run_benchmark.sh harness=cc evalAgent=cc --skills srp -k 1 -n 1",
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
        record("fake_spawn_count", len(fake.spawned) == 3, str(len(fake.spawned)))
        record("fake_placed_count", len(fake.placed) == 3, str(len(fake.placed)))
        record(
            "spawn_all_first",
            fake.events[:3] == ["spawn"] * 3 and fake.events[3:] == ["place"] * 3,
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
        record(
            "no_press_enter",
            all("Press Enter" not in script for _, script in fake.spawned),
            "window stays as a shell",
        )
        record(
            "histfile_up_arrow",
            all(
                "HISTFILE" in script and "exec bash --rcfile" in script
                for _, script in fake.spawned
            ),
            "Up-arrow recalls the job command",
        )
    else:
        record("fake_monitor", False, "shipped preset missing")
    record("slug", slugify("Positive All!") == "positive-all", slugify("Positive All!"))

    with tempfile.TemporaryDirectory(prefix="harbor-presets-") as raw:
        folder = Path(raw)
        saved = save_preset(
            Preset(name="smoke", description="one job", jobs=parsed[:1]),
            folder,
        )
        reloaded = load_preset_file(saved)
        record(
            "roundtrip",
            reloaded.name == "smoke"
            and reloaded.jobs[0].args[0].endswith(RUN_SCRIPT),
            saved.name,
        )
        written = write_shipped_presets(folder)
        record("write_shipped_count", len(written) == 14, str(len(written)))
        one = load_preset_file(folder / "baseline-codex.json")
        record(
            "write_one_harness_baseline",
            len(one.jobs) == 1
            and "--baseline" in one.jobs[0].args
            and "harness=codex" in one.jobs[0].args
            and "evalAgent=codex" in one.jobs[0].args
            and "evalAgent=grok" not in one.jobs[0].args
            and "evalAgent=cc" not in one.jobs[0].args,
            " ".join(one.jobs[0].args),
        )
        two = load_preset_file(folder / "positive-cc-grok.json")
        record(
            "write_two_harness_excludes_codex",
            len(two.jobs) == 2
            and {_job_harness(job) for job in two.jobs} == {"cc", "grok"}
            and all(_job_eval_agents(job) == {"cc", "grok"} for job in two.jobs)
            and all("evalAgent=cc,grok" in job.args for job in two.jobs)
            and all("--baseline" not in job.args for job in two.jobs),
            str(len(two.jobs)),
        )
        listed_temp = [path.stem for path in list_preset_files(folder)]
        record(
            "temp_catalog_then_extra",
            listed_temp[:14] == catalog_names and listed_temp[-1] == "smoke",
            str(listed_temp),
        )

    failed = [(name, message) for name, ok, message in cases if not ok]
    for name, ok, message in cases:
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {name}: {message}", flush=True)
    if failed:
        print(f"{len(failed)}/{len(cases)} launch_benchmarks case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} launch_benchmarks cases passed", flush=True)
    return 0

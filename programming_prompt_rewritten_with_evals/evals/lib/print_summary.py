"""Print a categorized console summary of Harbor trial results."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from contextlib import redirect_stderr
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from archive_run.ratelimit import trial_is_ratelimited
from archive_run.results_index import format_runtime, run_elapsed_seconds
from harbor_agents.harness_spec import HARNESSES, identify_harness


def _eval_agent_from_reward_name(skill: str) -> tuple[str, str] | None:
    """Return (skill, eval_agent) when *skill* is a per-eval-agent reward file stem."""
    for agent in HARNESSES:
        suffix = f"-{agent}"
        if skill.endswith(suffix) and skill != agent:
            return skill[: -len(suffix)], agent
    return None


def _load_json(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    # Harbor scrubs sensitive env VALUES from trial outputs. Flags like
    # CODEX_FORCE_AUTH_JSON=1 make the literal "1" a secret, so
    # {"reward": 1.0} becomes invalid {"reward": [REDACTED].0}. Restore only
    # that numeric reward pattern (not long-token [REDACTED] placeholders).
    if "[REDACTED]" in text:
        text = re.sub(
            r'("reward"\s*:\s*)\[REDACTED\](\.0\b)?',
            lambda m: f"{m.group(1)}1{m.group(2) or ''}",
            text,
        )
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _reward_from_job_result(trial_dir: Path) -> float | None:
    """Fall back to the parent Harbor job result.json reward_stats map."""
    job_result = trial_dir.parent / "result.json"
    payload = _load_json(job_result)
    if not payload:
        return None
    stats = payload.get("stats")
    if not isinstance(stats, dict):
        return None
    evals = stats.get("evals")
    if not isinstance(evals, dict):
        return None
    trial_name = trial_dir.name
    for eval_payload in evals.values():
        if not isinstance(eval_payload, dict):
            continue
        reward_stats = eval_payload.get("reward_stats")
        if not isinstance(reward_stats, dict):
            continue
        reward_map = reward_stats.get("reward")
        if not isinstance(reward_map, dict):
            continue
        for value_key, trial_names in reward_map.items():
            if not isinstance(trial_names, list):
                continue
            if trial_name not in trial_names:
                continue
            try:
                return float(value_key)
            except (TypeError, ValueError):
                continue
    return None


def _reward_value(trial_dir: Path) -> float | None:
    payload = _load_json(trial_dir / "verifier" / "reward.json")
    if payload is not None and "reward" in payload:
        try:
            return float(payload["reward"])
        except (TypeError, ValueError):
            pass
    return _reward_from_job_result(trial_dir)


def _per_skill_rewards(trial_dir: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    verifier = trial_dir / "verifier"
    if not verifier.is_dir():
        return out
    for path in sorted(verifier.glob("reward-*.json")):
        skill = path.name[len("reward-") : -len(".json")]
        if skill.endswith("-details"):
            continue
        if _eval_agent_from_reward_name(skill) is not None:
            continue
        payload = _load_json(path)
        if payload is None or "reward" not in payload:
            continue
        try:
            out[skill] = float(payload["reward"])
        except (TypeError, ValueError):
            continue
    if out:
        return out
    details = _load_json(verifier / "reward-details.json")
    if not details:
        return out
    reward = details.get("reward")
    if not isinstance(reward, dict):
        return out
    criteria = reward.get("criteria")
    if not isinstance(criteria, list):
        return out
    for item in criteria:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("reward")
        if name is None or value is None:
            continue
        try:
            out[str(name)] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def _per_eval_agent_rewards(trial_dir: Path) -> dict[tuple[str, str], float]:
    """Map (skill, eval_agent) to that agent's reward for one trial."""
    out: dict[tuple[str, str], float] = {}
    verifier = trial_dir / "verifier"
    if not verifier.is_dir():
        return out
    for path in sorted(verifier.glob("reward-*.json")):
        stem = path.name[len("reward-") : -len(".json")]
        if stem.endswith("-details"):
            continue
        parsed = _eval_agent_from_reward_name(stem)
        if parsed is None:
            continue
        skill, agent = parsed
        payload = _load_json(path)
        if payload is None or "reward" not in payload:
            continue
        try:
            out[(skill, agent)] = float(payload["reward"])
        except (TypeError, ValueError):
            continue
    if out:
        return out
    details = _load_json(verifier / "reward-details.json")
    if not details:
        return out
    reward = details.get("reward")
    if not isinstance(reward, dict):
        return out
    criteria = reward.get("criteria")
    if not isinstance(criteria, list):
        return out
    for item in criteria:
        if not isinstance(item, dict):
            continue
        skill = str(item.get("name") or "")
        agents = item.get("eval_agents")
        if not isinstance(agents, list):
            agents = reward.get("eval_agents")
        if not isinstance(agents, list) or not skill:
            continue
        for agent_item in agents:
            if not isinstance(agent_item, dict):
                continue
            agent = str(agent_item.get("agent") or "")
            value = agent_item.get("reward")
            if not agent or value is None:
                continue
            try:
                out[(skill, agent)] = float(value)
            except (TypeError, ValueError):
                continue
    return out


def _nested_criterion_bits(
    item: dict,
) -> tuple[str | None, str | None]:
    """Return (raw, reasoning) from a reward-details criterion object.

    Walks a nested ``details.reward.criteria[0]`` (or ``judge_output``) when
    the top-level fields are empty — the shape written by run_judges.sh.

    Args:
        item: One criterion dict from ``reward.criteria``.

    Returns:
        Raw yes/no string and reasoning text, either of which may be None.
    """
    raw = item.get("raw")
    reasoning = item.get("reasoning")
    if (reasoning is None or reasoning == "") and isinstance(item.get("details"), dict):
        nested = item["details"].get("reward")
        if isinstance(nested, dict):
            nested_criteria = nested.get("criteria")
            if isinstance(nested_criteria, list) and nested_criteria:
                nested_first = nested_criteria[0]
                if isinstance(nested_first, dict):
                    if reasoning is None or reasoning == "":
                        reasoning = nested_first.get("reasoning")
                    if raw is None:
                        raw = nested_first.get("raw")
            if (reasoning is None or reasoning == "") and nested.get("judge_output"):
                reasoning = nested.get("judge_output")
    return (
        str(raw) if raw is not None else None,
        str(reasoning) if reasoning else None,
    )


def _judge_criteria(trial_dir: Path) -> list[tuple[str, str | None, str | None]]:
    details = _load_json(trial_dir / "verifier" / "reward-details.json")
    if not details:
        return []
    reward = details.get("reward")
    if not isinstance(reward, dict):
        return []
    criteria = reward.get("criteria")
    if not isinstance(criteria, list):
        return []
    out: list[tuple[str, str | None, str | None]] = []
    for item in criteria:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "judge")
        raw, reasoning = _nested_criterion_bits(item)
        out.append((name, raw, reasoning))
        skill_details = _load_json(
            trial_dir / "verifier" / f"reward-{name}-details.json"
        )
        if skill_details and (reasoning is None or reasoning == ""):
            nested_reward = skill_details.get("reward")
            if isinstance(nested_reward, dict):
                nested_criteria = nested_reward.get("criteria")
                if isinstance(nested_criteria, list) and nested_criteria:
                    nested_first = nested_criteria[0]
                    if isinstance(nested_first, dict):
                        raw2, reasoning2 = _nested_criterion_bits(nested_first)
                        out[-1] = (name, raw or raw2, reasoning or reasoning2)
        agents = item.get("eval_agents")
        if not isinstance(agents, list) and isinstance(skill_details, dict):
            nested_reward = skill_details.get("reward")
            if isinstance(nested_reward, dict):
                agents = nested_reward.get("eval_agents")
                if not isinstance(agents, list):
                    nested_criteria = nested_reward.get("criteria")
                    if isinstance(nested_criteria, list) and nested_criteria:
                        agents = nested_criteria[0].get("eval_agents") if isinstance(nested_criteria[0], dict) else None
        if isinstance(agents, list):
            for agent_item in agents:
                if not isinstance(agent_item, dict):
                    continue
                agent = str(agent_item.get("agent") or "")
                if not agent:
                    continue
                agent_raw = agent_item.get("raw")
                agent_reason = agent_item.get("reasoning")
                out.append(
                    (
                        f"{name}/{agent}",
                        str(agent_raw) if agent_raw is not None else None,
                        str(agent_reason) if agent_reason else None,
                    )
                )
    return out


def _python_sources(trial_dir: Path) -> list[tuple[str, str]]:
    artifacts = trial_dir / "artifacts"
    if not artifacts.is_dir():
        return []
    found: list[tuple[str, str]] = []
    for path in sorted(artifacts.rglob("*.py")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8").rstrip()
        except OSError:
            continue
        rel = path.relative_to(artifacts).as_posix()
        found.append((rel, text))
    return found


def _trial_dirs(jobs_root: Path) -> list[Path]:
    dirs: list[Path] = []
    for reward_path in sorted(jobs_root.rglob("verifier/reward.json")):
        trial_dir = reward_path.parents[1]
        if trial_dir.is_dir():
            dirs.append(trial_dir)
    return dirs


def _task_name(trial_dir: Path) -> str:
    name = trial_dir.name
    if "__" in name:
        return name.split("__", 1)[0]
    return name


def _harness_of(trial_dir: Path, jobs_root: Path) -> str:
    try:
        rel = trial_dir.relative_to(jobs_root)
        top = rel.parts[0] if rel.parts else ""
    except ValueError:
        top = trial_dir.parent.name
    return identify_harness(top, trial_dir.parent.name, *trial_dir.parts)


def _fmt_rate(passed: int, total: int) -> str:
    if total <= 0:
        return "n/a"
    return f"{passed}/{total} ({100.0 * passed / total:.1f}%)"


def _section(title: str) -> None:
    print(file=sys.stderr)
    print("=" * 78, file=sys.stderr)
    print(title, file=sys.stderr)
    print("=" * 78, file=sys.stderr)


def _rate_line(label: str, values: list[float]) -> None:
    passed = sum(1 for value in values if value >= 1.0)
    print(f"  {label}: {_fmt_rate(passed, len(values))}", file=sys.stderr)


def _meta_for_summary(jobs_root: Path) -> dict:
    """Load archive metadata for the current run.

    Parameters: jobs_root - Harbor jobs directory passed to this summary.

    Returns: metadata object, or an empty dict when the archive is missing.
    """
    run_dir = os.environ.get("RUN_DIR", "").strip()
    candidates = []
    if run_dir:
        candidates.append(Path(run_dir))
    candidates.extend((jobs_root, jobs_root.parent, jobs_root.parent.parent))
    for path in candidates:
        payload = _load_json(path / "00-meta.json")
        if payload:
            return payload
    return {}


def _run_and_runtime(jobs_root: Path) -> tuple[str, str]:
    """Return the run stamp and formatted wall-clock runtime.

    Parameters: jobs_root - Harbor jobs directory passed to this summary.

    Returns: ``(stamp, runtime)``; empty strings when unknown.
    """
    meta = _meta_for_summary(jobs_root)
    stamp = str(meta.get("timestamp") or "").strip()
    runtime = format_runtime(run_elapsed_seconds(meta))
    if runtime == "-":
        runtime = ""
    return stamp, runtime


@dataclass(frozen=True)
class TrialReport:
    """One trial's console block, kept so highlights can reprint it.

    Parameters: index - 1-based trial number; total - trial count; harness -
        inferred harness id; name - Harbor trial directory name; verdict -
        PASS/FAIL/RATELIMIT; reward_text - printable reward; limited - rate
        limit skip; per_skill - skill rewards; per_eval - skill/agent
        rewards; judge_rows - answer/reason pairs; sources - artifact paths
        and file text.
    """

    index: int
    total: int
    harness: str
    name: str
    verdict: str
    reward_text: str
    limited: bool
    per_skill: dict[str, float]
    per_eval: dict[tuple[str, str], float]
    judge_rows: list[tuple[str, str | None, str | None]]
    sources: list[tuple[str, str]]


def _is_baseline(run_mode: str) -> bool:
    """Return whether *run_mode* is a baseline (no-skill) job.

    Parameters: run_mode - ``baseline`` or ``baseline-all``.

    Returns: True for baseline summaries.
    """
    return run_mode.startswith("baseline")


def _is_positive(run_mode: str) -> bool:
    """Return whether *run_mode* is a positive (skills-on) job.

    Parameters: run_mode - ``positive`` or ``positive-all``.

    Returns: True for positive summaries.
    """
    return run_mode.startswith("positive")


def _print_trial(report: TrialReport) -> None:
    """Write one trial header, judges, and source to stderr.

    Parameters: report - collected trial fields.

    Returns: none.
    """
    print(file=sys.stderr)
    print(
        f"[{report.index}/{report.total}] [{report.harness}] {report.name}  "
        f"{report.verdict}  reward={report.reward_text}",
        file=sys.stderr,
    )
    if report.limited:
        print("  failed due to ratelimit (excluded from pass_rate)", file=sys.stderr)
    if report.per_skill:
        bits = ", ".join(
            f"{name}={value:g}" for name, value in sorted(report.per_skill.items())
        )
        print(f"  per-skill: {bits}", file=sys.stderr)
    if report.per_eval:
        bits = ", ".join(
            f"{skill}/{agent}={value:g}"
            for (skill, agent), value in sorted(report.per_eval.items())
        )
        print(f"  per-evalAgent: {bits}", file=sys.stderr)
    if report.judge_rows:
        for skill_name, raw, reasoning in report.judge_rows:
            if raw is not None:
                print(f"  judge[{skill_name}] answer: {raw}", file=sys.stderr)
            if reasoning:
                print(f"  judge[{skill_name}] reason: {reasoning}", file=sys.stderr)
            elif raw is not None:
                print(
                    f"  judge[{skill_name}] reason: (none recorded)",
                    file=sys.stderr,
                )
    if report.sources:
        for rel, source in report.sources:
            print(f"  {rel}:", file=sys.stderr)
            for line in source.splitlines():
                print(f"    {line}", file=sys.stderr)
    else:
        print("  source: (no *.py artifacts downloaded)", file=sys.stderr)


def _print_highlights(run_mode: str, reports: list[TrialReport]) -> None:
    """Reprint the interesting trials after the rollup (console bottom).

    Positive jobs reprint FAILs (unexpected misses). Baseline jobs reprint
    PASSes (unexpected skill-following without skills). Source is included.
    Printed after the per-trial dump and before the rollup recap.

    Parameters: run_mode - positive or baseline label; reports - all trials.

    Returns: none.
    """
    if _is_positive(run_mode):
        chosen = [item for item in reports if item.verdict == "FAIL"]
        title = (
            f"Failed trials ({len(chosen)}) — reprinted above the recap "
            f"(positive run)"
        )
    elif _is_baseline(run_mode):
        chosen = [item for item in reports if item.verdict == "PASS"]
        title = (
            f"Successful trials ({len(chosen)}) — reprinted above the recap "
            f"with source (baseline run)"
        )
    else:
        return
    _section(title)
    if not chosen:
        print("  (none)", file=sys.stderr)
        return
    for report in chosen:
        _print_trial(report)


def _write_trial_fixture(
    jobs_root: Path,
    *,
    name: str,
    reward: float,
    source_marker: str,
) -> None:
    """Create one Harbor-shaped trial for ``--self-test``.

    Parameters: jobs_root - fake jobs directory; name - trial folder;
        reward - overall reward; source_marker - unique string in the .py.

    Returns: none.
    """
    trial = jobs_root / "codex-skills" / name
    verifier = trial / "verifier"
    app = trial / "artifacts" / "Projects" / "app"
    verifier.mkdir(parents=True)
    app.mkdir(parents=True)
    (verifier / "reward.json").write_text(
        json.dumps({"reward": reward}) + "\n", encoding="utf-8"
    )
    (app / "app.py").write_text(
        f'"""marker={source_marker}"""\n', encoding="utf-8"
    )


def _run_self_test() -> int:
    """Prove highlight reprint without Harbor.

    Parameters: none.

    Returns: 0 when every check passes.
    """
    cases: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {name}: {detail}", flush=True)

    with tempfile.TemporaryDirectory() as tmp:
        jobs = Path(tmp) / "jobs"
        _write_trial_fixture(
            jobs, name="calculator__pass", reward=1.0, source_marker="PASS_SRC"
        )
        _write_trial_fixture(
            jobs, name="calculator__fail", reward=0.0, source_marker="FAIL_SRC"
        )
        buf = StringIO()
        with redirect_stderr(buf):
            _print_summary(jobs, "positive", "commenting")
        positive = buf.getvalue()
        after_fail = positive.split("Failed trials", 1)
        check(
            "positive_has_fail_section",
            len(after_fail) == 2,
            "positive summary reprints failed trials after the trial dump",
        )
        tail = after_fail[1] if len(after_fail) == 2 else ""
        check(
            "positive_fail_has_source",
            "FAIL_SRC" in tail,
            "failed trial source is in the reprint above the recap",
        )
        check(
            "positive_fail_omits_pass_source",
            "PASS_SRC" not in tail,
            "passing trial source is not in the failed reprint",
        )
        grand_at = positive.rfind("GRAND TOTAL")
        recap_at = positive.find("By harness")
        fail_at = positive.rfind("Failed trials")
        check(
            "positive_fail_above_recap",
            fail_at != -1
            and recap_at != -1
            and grand_at != -1
            and fail_at < recap_at < grand_at,
            "failed reprint sits above the recap, not after GRAND TOTAL",
        )

        buf = StringIO()
        with redirect_stderr(buf):
            _print_summary(jobs, "baseline", "commenting")
        baseline = buf.getvalue()
        after_pass = baseline.split("Successful trials", 1)
        check(
            "baseline_has_pass_section",
            len(after_pass) == 2,
            "baseline summary reprints successful trials after the trial dump",
        )
        tail = after_pass[1] if len(after_pass) == 2 else ""
        check(
            "baseline_pass_has_source",
            "PASS_SRC" in tail,
            "successful trial source is in the reprint above the recap",
        )
        check(
            "baseline_pass_omits_fail_source",
            "FAIL_SRC" not in tail,
            "failed trial source is not in the successful reprint",
        )

        all_pass = Path(tmp) / "all-pass"
        _write_trial_fixture(
            all_pass, name="calculator__ok", reward=1.0, source_marker="ONLY_PASS"
        )
        buf = StringIO()
        with redirect_stderr(buf):
            _print_summary(all_pass, "positive", "commenting")
        empty = buf.getvalue()
        check(
            "positive_none_when_all_pass",
            "Failed trials (0)" in empty and "(none)" in empty,
            "all-pass positive run still prints an empty failed section",
        )

    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} print-summary self-test(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} print-summary self-tests passed", flush=True)
    return 0


def _print_summary(jobs_root: Path, run_mode: str, skills_csv: str) -> None:
    """Print the categorized Harbor trial summary to stderr.

    Parameters: jobs_root - Harbor jobs directory; run_mode - positive or
        baseline; skills_csv - skill list for the header.

    Returns: none.
    """
    trial_dirs = _trial_dirs(jobs_root)
    if not trial_dirs:
        print("No trial reward.json files found under", jobs_root, file=sys.stderr)
        return

    run_stamp, runtime_text = _run_and_runtime(jobs_root)
    identity = ""
    if run_stamp:
        identity += f"run={run_stamp}  "
    if runtime_text:
        identity += f"runtime={runtime_text}  "

    _section(
        f"Trial results ({len(trial_dirs)}) — {identity}mode={run_mode} "
        f"skills={skills_csv or '-'} — {jobs_root}"
    )

    by_harness: dict[str, list[float]] = defaultdict(list)
    by_harness_skill: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_harness_task: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_harness_task_skill: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    by_eval_agent: dict[str, list[float]] = defaultdict(list)
    by_harness_eval: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_harness_eval_skill: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    by_skill: dict[str, list[float]] = defaultdict(list)
    by_task: dict[str, list[float | None]] = defaultdict(list)
    rewards: list[float] = []
    ratelimited_n = 0
    reports: list[TrialReport] = []

    for index, trial_dir in enumerate(trial_dirs, start=1):
        reward = _reward_value(trial_dir)
        limited = trial_is_ratelimited(trial_dir)
        judge_rows = _judge_criteria(trial_dir)
        sources = _python_sources(trial_dir)
        task = _task_name(trial_dir)
        harness = _harness_of(trial_dir, jobs_root)
        per_skill = _per_skill_rewards(trial_dir)
        per_eval = _per_eval_agent_rewards(trial_dir)
        if limited:
            ratelimited_n += 1
        else:
            by_task[task].append(reward)
            if reward is not None:
                rewards.append(reward)
                by_harness[harness].append(reward)
                by_harness_task[(harness, task)].append(reward)
            for skill, value in per_skill.items():
                by_skill[skill].append(value)
                by_harness_skill[(harness, skill)].append(value)
                by_harness_task_skill[(harness, task, skill)].append(value)
            for (skill, agent), value in per_eval.items():
                by_eval_agent[agent].append(value)
                by_harness_eval[(harness, agent)].append(value)
                by_harness_eval_skill[(harness, agent, skill)].append(value)

        if limited:
            verdict = "RATELIMIT"
        elif reward is not None and reward >= 1.0:
            verdict = "PASS"
        else:
            verdict = "FAIL"
        report = TrialReport(
            index=index,
            total=len(trial_dirs),
            harness=harness,
            name=trial_dir.name,
            verdict=verdict,
            reward_text="n/a" if reward is None else f"{reward:g}",
            limited=limited,
            per_skill=per_skill,
            per_eval=per_eval,
            judge_rows=judge_rows,
            sources=sources,
        )
        reports.append(report)
        _print_trial(report)

    _print_highlights(run_mode, reports)

    _section(f"By harness (mode={run_mode})")
    for harness in sorted(by_harness):
        _rate_line(harness, by_harness[harness])

    if by_eval_agent:
        _section(f"By eval agent (mode={run_mode})")
        for agent in sorted(by_eval_agent):
            _rate_line(agent, by_eval_agent[agent])

        _section(f"By harness × eval agent (mode={run_mode})")
        for harness, agent in sorted(by_harness_eval):
            _rate_line(
                f"{harness} / evalAgent={agent}",
                by_harness_eval[(harness, agent)],
            )

        _section(f"By harness × eval agent × skill (mode={run_mode})")
        for harness, agent, skill in sorted(by_harness_eval_skill):
            _rate_line(
                f"{harness} / evalAgent={agent} / {skill}",
                by_harness_eval_skill[(harness, agent, skill)],
            )

    _section(f"By harness × skill (mode={run_mode})")
    for harness, skill in sorted(by_harness_skill):
        _rate_line(f"{harness} / {skill}", by_harness_skill[(harness, skill)])

    _section(f"By harness × coding task (mode={run_mode})")
    for harness, task in sorted(by_harness_task):
        _rate_line(f"{harness} / {task}", by_harness_task[(harness, task)])

    _section(f"By harness × task × skill (mode={run_mode})")
    for harness, task, skill in sorted(by_harness_task_skill):
        _rate_line(
            f"{harness} / {task} / {skill}",
            by_harness_task_skill[(harness, task, skill)],
        )

    if by_skill:
        _section(f"By skill judge — all harnesses (mode={run_mode})")
        for skill in sorted(by_skill):
            _rate_line(skill, by_skill[skill])

    _section(f"By coding task — all harnesses (mode={run_mode})")
    for task in sorted(by_task):
        values = [value for value in by_task[task] if value is not None]
        passed = sum(1 for value in values if value >= 1.0)
        print(f"  {task}: {_fmt_rate(passed, len(values))}", file=sys.stderr)

    if len(by_harness) >= 2:
        _section("Harness comparison (same mode/skills/tasks)")
        print(
            f"  {'harness':<10} {'pass_rate':<22} {'passed':>7} {'total':>7}",
            file=sys.stderr,
        )
        for harness in sorted(by_harness):
            values = by_harness[harness]
            passed = sum(1 for value in values if value >= 1.0)
            print(
                f"  {harness:<10} {_fmt_rate(passed, len(values)):<22} "
                f"{passed:>7} {len(values):>7}",
                file=sys.stderr,
            )

    print(file=sys.stderr)
    print("-" * 78, file=sys.stderr)
    runtime_suffix = f"  runtime={runtime_text}" if runtime_text else ""
    rate_suffix = (
        f"  rate_limited={ratelimited_n} (excluded from pass_rate)"
        if ratelimited_n
        else ""
    )
    if rewards:
        passed = sum(1 for value in rewards if value >= 1.0)
        total = len(rewards)
        print(
            f"GRAND TOTAL pass_rate={_fmt_rate(passed, total)}"
            f"{runtime_suffix}{rate_suffix}",
            file=sys.stderr,
        )
    else:
        print(
            f"GRAND TOTAL pass_rate=n/a (no numeric rewards)"
            f"{runtime_suffix}{rate_suffix}",
            file=sys.stderr,
        )
    print("-" * 78, file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    """Print a summary or run the fixture self-test.

    Parameters: argv - optional argument override.

    Returns: process exit code.
    """
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "--self-test":
        return _run_self_test()
    if not args:
        print(
            "Usage: print_summary.py JOBS_ROOT [MODE] [SKILLS_CSV]\n"
            "       print_summary.py --self-test",
            file=sys.stderr,
        )
        return 2
    _print_summary(
        Path(args[0]),
        args[1] if len(args) > 1 else "unknown",
        args[2] if len(args) > 2 else "",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

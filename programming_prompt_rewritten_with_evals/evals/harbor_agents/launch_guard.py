"""Automatically pace Harbor trial starts without consuming agent time budgets.

The START hook runs before container setup. Agent timestamps are recorded only
at AGENT_START, which Harbor emits before starting its execution timeout.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tomllib

from harbor.models.job.plugin import BaseJobPlugin
from harbor.trial.hooks import TrialEvent, TrialHookEvent


DOCKER_STORAGE_RESERVE = 2 * 1024**3
TRIAL_STORAGE_ALLOWANCE = 4 * 1024**3


def docker_storage_root() -> Path | None:
    """Locate the local filesystem backing Docker's image and container data.

    Parameters: none.
    Returns: the locally accessible Docker root, or None if it cannot be measured.
    """
    print("parameters=none")
    try:
        probe = subprocess.run(
            ["docker", "info", "--format", "{{.DockerRootDir}}"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        root = Path(probe.stdout.strip())
        result = root if probe.returncode == 0 and root.is_absolute() and root.is_dir() else None
    except (OSError, subprocess.TimeoutExpired):
        result = None
    print(result)
    return result


def storage_trial_ceiling(trial_ceiling: int, storage_root: Path | None) -> int:
    """Reserve build and writable-layer headroom before admitting trials.

    Parameters: trial_ceiling - requested job capacity; storage_root - measured
        local Docker data filesystem, or None when unavailable.
    Returns: storage-bounded capacity; zero when even one trial lacks headroom.
    """
    print(f"trial_ceiling={trial_ceiling} storage_root={storage_root}")
    if storage_root is None:
        result = trial_ceiling
    else:
        available = shutil.disk_usage(storage_root).free
        result = min(trial_ceiling, max(0, (available - DOCKER_STORAGE_RESERVE) // TRIAL_STORAGE_ALLOWANCE))
    print(result)
    return result


@dataclass
class ActiveTrial:
    """Admission held from trial start through verification and cleanup."""

    name: str
    admitted: float
    setup_budget: float
    started: float | None = None
    budget: float | None = None
    setup_recorded: bool = False


def execution_budget(event: TrialHookEvent) -> float | None:
    """Resolve the agent budget using Harbor's override/max/multiplier rules.

    Parameters: event - lifecycle event containing the resolved local task path.
    Returns: effective seconds, or None for an unlimited agent phase.
    """
    base = event.config.agent.override_timeout_sec
    if not base:
        path = event.config.task.path
        if path is None:
            raise ValueError("Launch guard requires a resolved local task path")
        with (path / "task.toml").open("rb") as handle:
            base = tomllib.load(handle).get("agent", {}).get("timeout_sec")
    if base is None:
        return None
    maximum = event.config.agent.max_timeout_sec or float("inf")
    multiplier = event.config.agent_timeout_multiplier
    if multiplier is None:
        multiplier = event.config.timeout_multiplier
    result = min(float(base), maximum) * multiplier
    return result


def environment_budget(event: TrialHookEvent) -> float:
    """Read the environment startup timeout using Harbor's multiplier rules.

    Parameters: event - lifecycle event with a resolved local task path.
    Returns: effective environment startup budget in seconds.
    """
    path = event.config.task.path
    if path is None:
        raise ValueError("Launch guard requires a resolved local task path")
    with (path / "task.toml").open("rb") as handle:
        base = tomllib.load(handle).get("environment", {}).get("build_timeout_sec", 600.0)
    multiplier = event.config.environment_build_timeout_multiplier
    if multiplier is None:
        multiplier = event.config.timeout_multiplier
    result = float(base) * multiplier
    return result


def setup_ceiling(trial_ceiling: int) -> int:
    """Bound simultaneous startup work independently of running agents.

    Parameters: trial_ceiling - configured full-job trial capacity.
    Returns: startup capacity bounded by half the available CPUs and an optional lower cap.
    """
    cpus = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)
    capacity = max(1, cpus // 2)
    raw = os.environ.get("EVAL_SETUP_MAX_CONCURRENT", "").strip()
    if raw:
        requested = int(raw)
        if requested < 1:
            raise ValueError("EVAL_SETUP_MAX_CONCURRENT must be a positive integer")
        capacity = min(capacity, requested)
    result = min(trial_ceiling, capacity)
    return result


class DeadlineLaunchGuard(BaseJobPlugin):
    """Bound setup surges and hold launches near active phase deadlines."""

    poll_interval = 5.0

    async def on_job_start(self, job) -> None:
        """Attach admission and release hooks to the job's public lifecycle.

        Parameters: self - launch guard; job - Harbor job whose starts will be paced.
        Returns: None.
        """
        print(f"self={object.__repr__(self)} job={object.__repr__(job)}")
        self.condition = asyncio.Condition()
        self.active: dict[str, ActiveTrial] = {}
        self.requested_ceiling = job.config.n_concurrent_trials
        self.storage_root = docker_storage_root()
        self.ceiling = storage_trial_ceiling(self.requested_ceiling, self.storage_root)
        if self.ceiling == 0:
            raise RuntimeError("Docker storage has insufficient free space for one trial plus its reserve")
        self.setup_ceiling = setup_ceiling(self.ceiling)
        self.setup_durations: deque[float] = deque(maxlen=64)
        job.add_hook(TrialEvent.START, self.admit)
        job.add_hook(TrialEvent.AGENT_START, self.agent_started)
        job.add_hook(TrialEvent.AGENT_END, self.agent_ended)
        job.add_hook(TrialEvent.END, self.finished)
        job.add_hook(TrialEvent.CANCEL, self.cancelled)
        print(
            f"Automatic launch guard: requested trial ceiling={self.requested_ceiling}; "
            f"storage-bounded full trial ceiling={self.ceiling}; "
            f"setup ceiling={self.setup_ceiling}; deadline headroom uses measured "
            f"setup p95 + {self.poll_interval:.1f}s (queue time is excluded)",
            file=sys.stderr,
        )
        print(None)

    def deadline_headroom(self) -> float:
        """Allow observed setup cost plus a polling interval before deadlines.

        Parameters: self - launch guard holding the observed setup samples.
        Returns: seconds of headroom, using the latest setup durations' p95.
        """
        samples = sorted(self.setup_durations)
        setup = samples[math.ceil(0.95 * len(samples)) - 1] if samples else 0.0
        result = setup + self.poll_interval
        return result

    def pressured_trials(self, now: float) -> list[tuple[ActiveTrial, float]]:
        """Compare each running phase's remaining time with measured headroom.

        Parameters: self - launch guard; now - current monotonic timestamp.
        Returns: records and remaining seconds that block additional starts.
        """
        headroom = self.deadline_headroom()
        result = [
            (trial, trial.budget - (now - trial.started))
            for trial in self.active.values()
            if trial.started is not None and trial.budget is not None
            and trial.budget - (now - trial.started) <= headroom
        ]
        return result

    def setup_pressure(self, now: float) -> tuple[int, list[str]]:
        """Count setup slots and hold new starts while setup work stalls.

        Parameters: self - launch guard; now - current monotonic timestamp.
        Returns: setup slot count and names using at least half their startup budget.
        """
        starting = [trial for trial in self.active.values() if not trial.setup_recorded]
        stalled = [
            trial.name for trial in starting
            if now - trial.admitted >= trial.setup_budget / 2
        ]
        result = (len(starting), stalled)
        return result

    async def admit(self, event: TrialHookEvent) -> None:
        """Wait before environment setup, then reserve this trial's admission.

        Parameters: self - launch guard; event - trial START event with an attempt ID.
        Returns: None after admission; cancellation releases a pending waiter.
        """
        print(f"self={object.__repr__(self)} event={object.__repr__(event)}")
        key = str(event.trial_id)
        setup_budget = environment_budget(event)
        async with self.condition:
            while key not in self.active:
                now = time.monotonic()
                pressured = self.pressured_trials(now)
                starting, stalled = self.setup_pressure(now)
                storage_capacity = storage_trial_ceiling(self.ceiling, self.storage_root)
                if storage_capacity == 0 and not self.active:
                    raise RuntimeError("Docker storage has insufficient free space for another trial plus its reserve")
                if (not pressured and not stalled and len(self.active) < self.ceiling
                        and len(self.active) < storage_capacity and starting < self.setup_ceiling):
                    self.active[key] = ActiveTrial(
                        name=event.trial_name, admitted=now, setup_budget=setup_budget,
                    )
                    print(None)
                    return
                # Periodic wakeups detect approaching deadlines even when no
                # phase finishes. A Condition notification wakes us sooner.
                try:
                    await asyncio.wait_for(
                        self.condition.wait(), timeout=self.poll_interval,
                    )
                except TimeoutError:
                    pass
        print(None)

    async def agent_started(self, event: TrialHookEvent) -> None:
        """Start tracking the phase budget after admission and setup complete.

        Parameters: self - launch guard; event - AGENT_START before Harbor's timer.
        Returns: None.
        """
        budget = execution_budget(event)
        async with self.condition:
            trial = self.active[str(event.trial_id)]
            now = time.monotonic()
            if not trial.setup_recorded:
                self.setup_durations.append(now - trial.admitted)
                trial.setup_recorded = True
            trial.started = now
            trial.budget = budget
            self.condition.notify_all()

    async def agent_ended(self, event: TrialHookEvent) -> None:
        """Clear phase deadline pressure immediately when execution ends.

        Parameters: self - launch guard; event - AGENT_END, including failures.
        Returns: None; admission stays held through verification and cleanup.
        """
        async with self.condition:
            trial = self.active.get(str(event.trial_id))
            if trial is None or trial.started is None:
                return
            trial.started = None
            self.condition.notify_all()

    async def finished(self, event: TrialHookEvent) -> None:
        """Release admission without permanent backoff or changing rewards.

        Parameters: self - launch guard; event - END after outputs have been saved.
        Returns: None.
        """
        async with self.condition:
            trial = self.active.pop(str(event.trial_id), None)
            if trial is None:
                return
            self.condition.notify_all()

    async def cancelled(self, event: TrialHookEvent) -> None:
        """Release only this attempt's permit on cancellation, once.

        Parameters: self - launch guard; event - CANCEL; a later END is harmless.
        Returns: None.
        """
        async with self.condition:
            self.active.pop(str(event.trial_id), None)
            self.condition.notify_all()

    async def on_job_end(self, job_result) -> None:
        """Finish silently without changing Harbor's results or retry policy.

        Parameters: self - launch guard; job_result - original Harbor job result.
        Returns: None.
        """

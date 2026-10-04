"""Automatically pace Harbor trial starts without consuming agent time budgets.

The START hook runs before container setup. Agent timestamps are recorded only
at AGENT_START, which Harbor emits before starting its execution timeout.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
import math
import time
import tomllib

from harbor.models.job.plugin import BaseJobPlugin
from harbor.trial.hooks import TrialEvent, TrialHookEvent
from harbor.utils.logger import logger


@dataclass
class ActiveTrial:
    """Admission held from trial start through verification and cleanup."""

    name: str
    admitted: float
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
    return min(float(base), maximum) * multiplier


class DeadlineLaunchGuard(BaseJobPlugin):
    """Hold queued trials when active agents approach their own deadlines."""

    poll_interval = 5.0

    async def on_job_start(self, job) -> None:
        """Attach admission and release hooks to the job's public lifecycle.

        Parameters: job - Harbor job whose trial starts will be paced.
        Returns: None.
        """
        self.condition = asyncio.Condition()
        self.active: dict[str, ActiveTrial] = {}
        self.ceiling = job.config.n_concurrent_trials
        self.setup_durations: deque[float] = deque(maxlen=64)
        self.log = logger.getChild(__name__)
        job.add_hook(TrialEvent.START, self.admit)
        job.add_hook(TrialEvent.AGENT_START, self.agent_started)
        job.add_hook(TrialEvent.AGENT_END, self.agent_ended)
        job.add_hook(TrialEvent.END, self.finished)
        job.add_hook(TrialEvent.CANCEL, self.cancelled)
        self.log.info(
            "Automatic launch guard: full trial ceiling=%s; deadline headroom "
            "uses measured setup p95 + %.1fs (queue time is excluded)",
            self.ceiling, self.poll_interval,
        )

    def deadline_headroom(self) -> float:
        """Allow observed setup cost plus a polling interval before deadlines.

        Parameters: none.
        Returns: seconds of headroom, using the latest setup durations' p95.
        """
        samples = sorted(self.setup_durations)
        setup = samples[math.ceil(0.95 * len(samples)) - 1] if samples else 0.0
        return setup + self.poll_interval

    def pressured_trials(self, now: float) -> list[tuple[ActiveTrial, float]]:
        """Compare each running phase's remaining time with measured headroom.

        Parameters: now - current monotonic timestamp.
        Returns: records and remaining seconds that block additional starts.
        """
        headroom = self.deadline_headroom()
        return [
            (trial, trial.budget - (now - trial.started))
            for trial in self.active.values()
            if trial.started is not None and trial.budget is not None
            and trial.budget - (now - trial.started) <= headroom
        ]

    async def admit(self, event: TrialHookEvent) -> None:
        """Wait before environment setup, then reserve this trial's admission.

        Parameters: event - trial START event; retries have distinct trial IDs.
        Returns: None after admission; cancellation releases a pending waiter.
        """
        key = str(event.trial_id)
        waiting_reason: tuple[str, ...] | None = None
        async with self.condition:
            while key not in self.active:
                now = time.monotonic()
                pressured = self.pressured_trials(now)
                if not pressured and len(self.active) < self.ceiling:
                    self.active[key] = ActiveTrial(name=event.trial_name, admitted=now)
                    self.log.info(
                        "Automatic launch guard: admitted %s; active=%s ceiling=%s",
                        event.trial_name, len(self.active), self.ceiling,
                    )
                    return
                reason = tuple(sorted(trial.name for trial, _ in pressured))
                if reason != waiting_reason:
                    self.log.info(
                        "Automatic launch guard: queued %s before container setup; "
                        "active=%s ceiling=%s headroom=%.1fs near_deadline=%s",
                        event.trial_name, len(self.active), self.ceiling,
                        self.deadline_headroom(),
                        [(trial.name, round(remaining, 1)) for trial, remaining in pressured],
                    )
                    waiting_reason = reason
                # Periodic wakeups detect approaching deadlines even when no
                # phase finishes. A Condition notification wakes us sooner.
                try:
                    await asyncio.wait_for(
                        self.condition.wait(), timeout=self.poll_interval,
                    )
                except TimeoutError:
                    pass

    async def agent_started(self, event: TrialHookEvent) -> None:
        """Start tracking the phase budget after admission and setup complete.

        Parameters: event - AGENT_START event emitted before Harbor's timer.
        Returns: None.
        """
        budget = execution_budget(event)
        async with self.condition:
            trial = self.active[str(event.trial_id)]
            now = time.monotonic()
            if not trial.setup_recorded:
                self.setup_durations.append(now - trial.admitted)
                trial.setup_recorded = True
                self.log.info(
                    "Automatic launch guard: setup %s took %.1fs; "
                    "samples=%s deadline headroom=%.1fs",
                    trial.name, now - trial.admitted, len(self.setup_durations),
                    self.deadline_headroom(),
                )
            trial.started = now
            trial.budget = budget
            self.condition.notify_all()

    async def agent_ended(self, event: TrialHookEvent) -> None:
        """Clear phase deadline pressure immediately when execution ends.

        Parameters: event - AGENT_END event, including timeout and cancellation.
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

        Parameters: event - END event after outputs and results have been saved.
        Returns: None.
        """
        async with self.condition:
            trial = self.active.pop(str(event.trial_id), None)
            if trial is None:
                return
            self.condition.notify_all()

    async def cancelled(self, event: TrialHookEvent) -> None:
        """Release only this attempt's permit on cancellation, once.

        Parameters: event - CANCEL event; a later END event is harmless.
        Returns: None.
        """
        async with self.condition:
            self.active.pop(str(event.trial_id), None)
            self.condition.notify_all()

    async def on_job_end(self, job_result) -> None:
        """Log completion without changing Harbor's results or retry policy.

        Parameters: job_result - original Harbor job result.
        Returns: None.
        """
        self.log.info("Automatic launch guard finished; trial ceiling=%s", self.ceiling)

"""Automatically pace Harbor trial starts without consuming agent time budgets.

The START hook runs before container setup. Agent timestamps are recorded only
at AGENT_START, which Harbor emits before starting its execution timeout.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import time
import tomllib

from harbor.models.job.plugin import BaseJobPlugin
from harbor.trial.hooks import TrialEvent, TrialHookEvent
from harbor.utils.logger import logger


@dataclass
class ActiveTrial:
    """Admission held from trial start through verification and cleanup."""

    name: str
    started: float | None = None
    budget: float | None = None
    elapsed: float | None = None
    pressured: bool = False


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

    async def on_job_start(self, job) -> None:
        """Attach admission and release hooks to the job's public lifecycle.

        Parameters: job - Harbor job whose trial starts will be paced.
        Returns: None.
        """
        self.condition = asyncio.Condition()
        self.active: dict[str, ActiveTrial] = {}
        self.ceiling = job.config.n_concurrent_trials
        self.window = min(4, self.ceiling)
        self.healthy = 0
        self.log = logger.getChild(__name__)
        job.add_hook(TrialEvent.START, self.admit)
        job.add_hook(TrialEvent.AGENT_START, self.agent_started)
        job.add_hook(TrialEvent.AGENT_END, self.agent_ended)
        job.add_hook(TrialEvent.END, self.finished)
        job.add_hook(TrialEvent.CANCEL, self.cancelled)
        self.log.info(
            "Automatic launch guard: initial=%s ceiling=%s; pause at 80%% "
            "of an active agent's execution budget (queue time is excluded)",
            self.window, self.ceiling,
        )

    def pressured_trials(self, now: float) -> list[ActiveTrial]:
        """Identify running agents in the final fifth of their budgets.

        Parameters: now - current monotonic timestamp.
        Returns: active records that should block additional trial starts.
        """
        return [
            trial for trial in self.active.values()
            if trial.started is not None and trial.budget is not None
            and now - trial.started >= 0.8 * trial.budget
        ]

    def reduce_window(self, reason: str) -> None:
        """Lower future admission pressure while preserving running trials.

        Parameters: reason - diagnostic explaining the slowdown.
        Returns: None.
        """
        previous = self.window
        self.window = max(1, self.window // 2)
        self.healthy = 0
        self.log.info(
            "Automatic launch guard: %s; admission window %s -> %s",
            reason, previous, self.window,
        )

    async def admit(self, event: TrialHookEvent) -> None:
        """Wait before environment setup, then reserve this trial's admission.

        Parameters: event - trial START event; retries have distinct trial IDs.
        Returns: None after admission; cancellation releases a pending waiter.
        """
        key = str(event.trial_id)
        waiting_logged = False
        async with self.condition:
            while key not in self.active:
                pressured = self.pressured_trials(time.monotonic())
                for trial in pressured:
                    if not trial.pressured:
                        trial.pressured = True
                        self.reduce_window(f"{trial.name} is near its execution deadline")
                if not pressured and len(self.active) < self.window:
                    self.active[key] = ActiveTrial(name=event.trial_name)
                    self.log.info(
                        "Automatic launch guard: admitted %s; active=%s window=%s",
                        event.trial_name, len(self.active), self.window,
                    )
                    return
                if not waiting_logged:
                    self.log.info(
                        "Automatic launch guard: queued %s before container setup; "
                        "active=%s window=%s near_deadline=%s",
                        event.trial_name, len(self.active), self.window,
                        [trial.name for trial in pressured],
                    )
                    waiting_logged = True
                # Periodic wakeups detect approaching deadlines even when no
                # phase finishes. A Condition notification wakes us sooner.
                try:
                    await asyncio.wait_for(self.condition.wait(), timeout=5.0)
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
            trial.started = time.monotonic()
            trial.budget = budget
            trial.elapsed = None
            trial.pressured = False
            self.condition.notify_all()

    async def agent_ended(self, event: TrialHookEvent) -> None:
        """Stop deadline tracking and lower pressure after a slow agent phase.

        Parameters: event - AGENT_END event, including timeout and cancellation.
        Returns: None; admission stays held through verification and cleanup.
        """
        async with self.condition:
            trial = self.active.get(str(event.trial_id))
            if trial is None or trial.started is None:
                return
            trial.elapsed = time.monotonic() - trial.started
            if trial.budget is not None and trial.elapsed >= 0.8 * trial.budget:
                if not trial.pressured:
                    self.reduce_window(f"{trial.name} used at least 80% of its budget")
                trial.pressured = True
            trial.started = None
            self.condition.notify_all()

    async def finished(self, event: TrialHookEvent) -> None:
        """Release admission, retaining timeout evidence and original rewards.

        Parameters: event - END event after outputs and results have been saved.
        Returns: None.
        """
        async with self.condition:
            trial = self.active.pop(str(event.trial_id), None)
            if trial is None:
                return
            error = event.result.exception_info
            if error is not None:
                self.healthy = 0
                if error.exception_type in {
                    "AgentTimeoutError", "ApiRateLimitError",
                    "EnvironmentStartTimeoutError", "AgentSetupTimeoutError",
                } and not trial.pressured:
                    self.reduce_window(f"{trial.name}: {error.exception_type}")
            elif (
                not trial.pressured and trial.elapsed is not None
                and (trial.budget is None or trial.elapsed < 0.6 * trial.budget)
            ):
                self.healthy += 1
                if self.healthy >= self.window and self.window < self.ceiling:
                    self.window += 1
                    self.healthy = 0
                    self.log.info(
                        "Automatic launch guard: healthy completed wave; window=%s",
                        self.window,
                    )
            else:
                self.healthy = 0
            self.condition.notify_all()

    async def cancelled(self, event: TrialHookEvent) -> None:
        """Release only this attempt's permit on cancellation, once.

        Parameters: event - CANCEL event; a later END event is harmless.
        Returns: None.
        """
        async with self.condition:
            self.active.pop(str(event.trial_id), None)
            self.healthy = 0
            self.condition.notify_all()

    async def on_job_end(self, job_result) -> None:
        """Log completion without changing Harbor's results or retry policy.

        Parameters: job_result - original Harbor job result.
        Returns: None.
        """
        self.log.info("Automatic launch guard finished; admission window=%s", self.window)

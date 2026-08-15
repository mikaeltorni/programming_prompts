"""Clean Grok CLI agent for rewritten-prompt Harbor benchmarks.

Wraps Harbor's Grok Build agent (``grok-build``) so each trial:

* pins the CLI version from ``evals/grok-version.txt``;
* wipes ``~/.grok/skills`` (and plugins) then installs only the skills Harbor
  injected for the job — host SuperGrok marketplace skills never enter the
  session;
* defaults ``reasoning_effort`` to ``low`` (Grok 4.6) unless the job overrides
  it.

Auth is SuperGrok OAuth (``~/.grok/auth.json``) forwarded as ``XAI_API_KEY``,
or an explicit ``XAI_API_KEY`` on the host. The wrapper never logs the key.
"""

from __future__ import annotations

from typing import override

from harbor.agents.installed.grok_build import GrokBuild
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.name import AgentName

from harbor_agents.clean_skills import (
    build_clean_grok_skills_register_command,
    load_grok_version,
)


class BenchmarkGrok(GrokBuild):
    """Grok CLI agent that pins a CLI version and keeps skills job-local."""

    def __init__(
        self,
        *args,
        version: str | None = None,
        **kwargs,
    ) -> None:
        """Create the agent, defaulting version and low reasoning effort.

        Args:
            *args: Forwarded to Harbor's Grok Build agent.
            version: Grok CLI version to install/verify inside the trial.
                When omitted, reads ``evals/grok-version.txt``.
            **kwargs: Forwarded to the Harbor Grok agent (model flags, skills
                directory, reasoning effort, ``grok_config``, and so on).
                ``reasoning_effort`` defaults to ``low`` when the job did not
                set it. Marketplace auto-install is pinned off so host
                SuperGrok plugins never enter the trial.
        """
        pinned = version if version is not None else load_grok_version()
        kwargs.setdefault("reasoning_effort", "low")
        grok_config = dict(kwargs.get("grok_config") or {})
        models = dict(grok_config.get("models") or {})
        models.setdefault("default_reasoning_effort", "low")
        grok_config["models"] = models
        marketplace = dict(grok_config.get("marketplace") or {})
        marketplace.setdefault("official_marketplace_auto_installed", False)
        marketplace.setdefault("default_skills_installs_purged", True)
        grok_config["marketplace"] = marketplace
        kwargs["grok_config"] = grok_config
        super().__init__(*args, version=pinned, **kwargs)
        self.logger.info(
            "BenchmarkGrok initialized version=%s skills_dir=%s "
            "reasoning_effort=%s marketplace_auto_install=%s",
            self._version,
            self.skills_dir,
            kwargs.get("reasoning_effort"),
            marketplace.get("official_marketplace_auto_installed"),
        )

    @staticmethod
    @override
    def name() -> str:
        """Return Harbor's Grok Build agent name for job labels."""
        return AgentName.GROK_BUILD.value

    @override
    def _build_register_skills_command(self) -> str | None:
        """Always wipe Grok skill roots; install Harbor-injected skills when present."""
        command = build_clean_grok_skills_register_command(self.skills_dir)
        self.logger.info(
            "Resetting Grok skill discovery paths; installing skills_dir=%s",
            self.skills_dir,
        )
        return command

    async def _installed_grok_satisfies_version(
        self, environment: BaseEnvironment
    ) -> bool:
        """Return True when ``grok --version`` matches the pin.

        Args:
            environment: Trial container.

        Returns:
            True when the pinned CLI is already on PATH.
        """
        command = self.get_version_command()
        if command is None:
            return False
        result = await environment.exec(command=command)
        if result.return_code != 0:
            return False
        installed = self.parse_version(result.stdout or "")
        if self._version is None:
            return bool(installed)
        return installed == self._version

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        """Skip the curl installer when the image already has the pinned CLI."""
        if await self._installed_grok_satisfies_version(environment):
            self.logger.info(
                "Grok CLI is already available at the requested version %s",
                self._version,
            )
            skills_command = self._build_register_skills_command()
            if skills_command:
                await self.exec_as_agent(environment, command=skills_command)
            return
        await super().install(environment)

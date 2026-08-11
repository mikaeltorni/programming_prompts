"""Clean Codex agent for rewritten-prompt Harbor benchmarks.

Harbor already points Codex at a fresh ``CODEX_HOME`` (``/tmp/codex-home``) for
each trial. This agent goes further: before the trial starts it wipes every
user skill discovery path Codex scans, then installs only the skills Harbor
injected for the job (``--skill`` / agent ``skills``). Host skills under
``~/.agents/skills`` never enter the benchmark container session.

The Codex CLI version defaults to the pin in ``evals/codex-version.txt``
(currently 0.147.0) unless ``--ak version=...`` overrides it.
"""

from __future__ import annotations

from typing import override

from harbor.agents.installed.codex import Codex
from harbor.models.agent.name import AgentName

from harbor_agents.clean_skills import (
    build_clean_skills_register_command,
    load_codex_version,
)


class BenchmarkCodex(Codex):
    """Codex agent that pins a CLI version and keeps the skill set job-local."""

    def __init__(
        self,
        *args,
        version: str | None = None,
        **kwargs,
    ) -> None:
        """Create the agent, defaulting ``version`` to the evals pin file.

        Args:
            *args: Forwarded to :class:`harbor.agents.installed.codex.Codex`.
            version: Codex CLI version to install/verify inside the trial
                environment. When omitted, reads ``evals/codex-version.txt``.
            **kwargs: Forwarded to the Harbor Codex agent (model flags, skills
                directory, resume, and so on).
        """
        pinned = version if version is not None else load_codex_version()
        super().__init__(*args, version=pinned, **kwargs)
        self.logger.info(
            "BenchmarkCodex initialized version=%s skills_dir=%s",
            self._version,
            self.skills_dir,
        )

    @staticmethod
    @override
    def name() -> str:
        """Return Harbor's Codex agent name so existing job labels stay valid."""
        return AgentName.CODEX.value

    @override
    def _build_register_skills_command(self) -> str | None:
        """Always wipe skill roots; install Harbor-injected skills when present."""
        command = build_clean_skills_register_command(self.skills_dir)
        self.logger.info(
            "Resetting Codex skill discovery paths; installing skills_dir=%s",
            self.skills_dir,
        )
        return command

"""Pure helpers for clean Codex skill registration in rewritten-prompt evals.

Kept free of Harbor imports so the shell wipe/install command can be inspected
without loading the Harbor tool environment.
"""

from __future__ import annotations

import shlex
from pathlib import Path

# Fallback when codex-version.txt is missing; keep in sync with that file.
DEFAULT_CODEX_VERSION = "0.147.0"


def codex_version_file() -> Path:
    """Return the path of the evals Codex version pin file.

    The file lives next to the Harbor task tree at ``evals/codex-version.txt``.
    """
    return Path(__file__).resolve().parents[1] / "codex-version.txt"


def load_codex_version(version_file: Path | None = None) -> str:
    """Load the pinned Codex CLI version from disk.

    Args:
        version_file: Optional override path. Defaults to
            :func:`codex_version_file`.

    Returns:
        A stripped version string such as ``0.147.0``. Falls back to
        :data:`DEFAULT_CODEX_VERSION` when the file is absent or empty.
    """
    path = version_file or codex_version_file()
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return DEFAULT_CODEX_VERSION
    return text or DEFAULT_CODEX_VERSION


def build_clean_skills_register_command(skills_dir: str | None) -> str:
    """Build a shell snippet that resets Codex skills then installs only *skills_dir*.

    Codex discovers skills from ``$HOME/.agents/skills``, ``/etc/codex/skills``,
    and ``$CODEX_HOME/skills`` (including seeded ``.system`` skills). This
    command removes those trees, recreates empty destinations, and — when
    Harbor uploaded benchmark skills — copies only that upload into the user
    and ``CODEX_HOME`` skill roots.

    Args:
        skills_dir: Absolute path inside the trial environment where Harbor
            uploaded the configured skills (for example ``/harbor/skills``),
            or ``None`` when the job configured no skills.

    Returns:
        A shell command string safe to run with ``CODEX_HOME`` already set.
    """
    wipe = (
        'rm -rf "$HOME/.agents/skills" /etc/codex/skills "$CODEX_HOME/skills"; '
        'mkdir -p "$HOME/.agents/skills" "$CODEX_HOME/skills"'
    )
    if not skills_dir:
        return wipe

    quoted = shlex.quote(skills_dir)
    return (
        f"{wipe}; "
        f'cp -a {quoted}/. "$HOME/.agents/skills/"; '
        f'cp -a {quoted}/. "$CODEX_HOME/skills/"'
    )

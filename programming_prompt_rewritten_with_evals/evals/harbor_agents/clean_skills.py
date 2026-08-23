"""Pure helpers for clean skill registration in rewritten-prompt evals.

Kept free of Harbor imports so the shell wipe/install command can be inspected
without loading the Harbor tool environment.
"""

from __future__ import annotations

import shlex
from pathlib import Path

# Fallback when pin files and the instance-start cache are missing.
# Keep in sync with evals/*-version.txt.
DEFAULT_CODEX_VERSION = "0.149.0"
DEFAULT_CLAUDE_VERSION = "2.1.241"
DEFAULT_GROK_VERSION = "1.0.5"

_EVALS_DIR = Path(__file__).resolve().parents[1]


def generated_versions_dir() -> Path:
    """Return the gitignored cache of CLI versions resolved at instance start.

    ``run_benchmark.sh`` writes one ``*-version.txt`` per harness here after
    looking up npm / the Grok stable channel. Loaders prefer this cache over
    the committed pin files so a new Harbor instance uses the newest CLIs
    without dirtying git.
    """
    return _EVALS_DIR / ".generated" / "cli-versions"


def generated_version_file(name: str) -> Path:
    """Return the instance-start cache path for one harness pin.

    Args:
        name: ``codex``, ``claude``, or ``grok``.
    """
    return generated_versions_dir() / f"{name}-version.txt"


def _read_version_text(path: Path) -> str:
    """Return stripped file text, or empty when the path is missing/unreadable.

    Args:
        path: Version pin or cache file.
    """
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _load_version(
    *,
    name: str,
    pin_file: Path,
    default: str,
    version_file: Path | None = None,
    use_cache: bool = True,
) -> str:
    """Load a CLI version: explicit override, then instance cache, then pin.

    Args:
        name: Harness pin stem (``codex``, ``claude``, ``grok``).
        pin_file: Committed fallback pin under ``evals/``.
        default: Last-resort constant when every file is missing.
        version_file: Optional explicit path (skips the instance cache).
        use_cache: When False, skip ``.generated/cli-versions/`` and read
            the committed pin (used for ``--no-pin-refresh``).
    """
    if version_file is not None:
        return _read_version_text(version_file) or default
    if use_cache:
        cached = _read_version_text(generated_version_file(name))
        if cached:
            return cached
    return _read_version_text(pin_file) or default


def codex_version_file() -> Path:
    """Return the path of the evals Codex version pin file.

    The file lives next to the Harbor task tree at ``evals/codex-version.txt``.
    """
    return _EVALS_DIR / "codex-version.txt"


def claude_version_file() -> Path:
    """Return the path of the evals Claude Code version pin file."""
    return _EVALS_DIR / "claude-version.txt"


def grok_version_file() -> Path:
    """Return the path of the evals Grok CLI version pin file."""
    return _EVALS_DIR / "grok-version.txt"


def load_codex_version(
    version_file: Path | None = None, *, use_cache: bool = True
) -> str:
    """Load the Codex CLI version for this instance.

    Prefers the gitignored instance-start cache, then the committed pin.

    Args:
        version_file: Optional override path. When set, only that file is
            read (no instance cache).
        use_cache: When False, read only the committed pin.

    Returns:
        A stripped version string such as ``0.149.0``. Falls back to
        :data:`DEFAULT_CODEX_VERSION` when every source is absent or empty.
    """
    return _load_version(
        name="codex",
        pin_file=codex_version_file(),
        default=DEFAULT_CODEX_VERSION,
        version_file=version_file,
        use_cache=use_cache,
    )


def load_claude_version(
    version_file: Path | None = None, *, use_cache: bool = True
) -> str:
    """Load the Claude Code CLI version for this instance.

    Args:
        version_file: Optional override path. When set, only that file is
            read (no instance cache).
        use_cache: When False, read only the committed pin.

    Returns:
        A stripped version string such as ``2.1.241``. Falls back to
        :data:`DEFAULT_CLAUDE_VERSION` when every source is absent or empty.
    """
    return _load_version(
        name="claude",
        pin_file=claude_version_file(),
        default=DEFAULT_CLAUDE_VERSION,
        version_file=version_file,
        use_cache=use_cache,
    )


def load_grok_version(
    version_file: Path | None = None, *, use_cache: bool = True
) -> str:
    """Load the Grok CLI version for this instance.

    Args:
        version_file: Optional override path. When set, only that file is
            read (no instance cache).
        use_cache: When False, read only the committed pin.

    Returns:
        A stripped version string such as ``1.0.5``. Falls back to
        :data:`DEFAULT_GROK_VERSION` when every source is absent or empty.
    """
    return _load_version(
        name="grok",
        pin_file=grok_version_file(),
        default=DEFAULT_GROK_VERSION,
        version_file=version_file,
        use_cache=use_cache,
    )


def build_ensure_git_repo_command(repo: str = "/Projects/app") -> str:
    """Build a snippet that git-inits ``repo`` with an empty commit if needed.

    Harbor task images already do this at build time. This is a safety net when
    ``/Projects/app`` was remounted empty.

    Args:
        repo: Absolute project checkout inside the trial (default
            ``/Projects/app``).

    Returns:
        A shell command that is a no-op when ``repo/.git`` already exists.
    """
    quoted = shlex.quote(repo)
    return (
        f"if [ ! -e {quoted}/.git ]; then "
        f"git -C {quoted} init -b master && "
        f'git -C {quoted} commit --allow-empty -m "Initial empty commit"; '
        "fi"
    )


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
    ensure = build_ensure_git_repo_command()
    wipe = (
        'rm -rf "$HOME/.agents/skills" /etc/codex/skills "$CODEX_HOME/skills"; '
        'mkdir -p "$HOME/.agents/skills" "$CODEX_HOME/skills"'
    )
    if not skills_dir:
        return f"{ensure}; {wipe}"

    quoted = shlex.quote(skills_dir)
    return (
        f"{ensure}; {wipe}; "
        f'cp -a {quoted}/. "$HOME/.agents/skills/"; '
        f'cp -a {quoted}/. "$CODEX_HOME/skills/"'
    )


def build_clean_claude_skills_register_command(skills_dir: str | None) -> str:
    """Build a shell snippet that resets Claude skills then installs only *skills_dir*.

    Harbor's Claude agent may copy ``~/.claude/skills`` into
    ``$CLAUDE_CONFIG_DIR/skills`` before this runs. This command wipes both
    trees and — when Harbor uploaded benchmark skills — installs only that
    upload into ``$CLAUDE_CONFIG_DIR/skills``.

    Args:
        skills_dir: Absolute path inside the trial environment where Harbor
            uploaded the configured skills, or ``None`` for baseline jobs.

    Returns:
        A shell command string safe to run after ``CLAUDE_CONFIG_DIR`` is set.
    """
    ensure = build_ensure_git_repo_command()
    wipe = (
        'rm -rf "$HOME/.claude/skills" "$CLAUDE_CONFIG_DIR/skills"; '
        'mkdir -p "$HOME/.claude/skills" "$CLAUDE_CONFIG_DIR/skills"'
    )
    if not skills_dir:
        return f"{ensure}; {wipe}"

    quoted = shlex.quote(skills_dir)
    return f"{ensure}; {wipe}; cp -a {quoted}/. \"$CLAUDE_CONFIG_DIR/skills/\""


def build_clean_grok_skills_register_command(skills_dir: str | None) -> str:
    """Build a shell snippet that resets Grok skills then installs only *skills_dir*.

    Grok discovers skills from ``$HOME/.grok/skills`` (and may auto-install
    marketplace plugins). This command wipes those trees and — when Harbor
    uploaded benchmark skills — copies only that upload into
    ``$HOME/.grok/skills``. Host SuperGrok marketplace skills never enter
    the trial.

    Args:
        skills_dir: Absolute path inside the trial where Harbor uploaded the
            configured skills, or ``None`` for baseline jobs.

    Returns:
        A shell command string safe to run after ``$HOME/.grok`` exists.
    """
    ensure = build_ensure_git_repo_command()
    wipe = (
        'rm -rf "$HOME/.grok/skills" "$HOME/.grok/installed-plugins"; '
        'mkdir -p "$HOME/.grok/skills"'
    )
    if not skills_dir:
        return f"{ensure}; {wipe}"

    quoted = shlex.quote(skills_dir)
    return f"{ensure}; {wipe}; cp -a {quoted}/. \"$HOME/.grok/skills/\""

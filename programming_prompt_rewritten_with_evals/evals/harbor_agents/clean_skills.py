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


def _build_global_register_command(skills_dir: str | None, runtime: str) -> str:
    """Reset trial discovery and install only the generated global document."""
    ensure = build_ensure_git_repo_command()
    if runtime == "codex":
        wipe = (
            'rm -rf "$HOME/.agents/skills" /etc/codex/skills "$CODEX_HOME/skills"; '
            'mkdir -p "$CODEX_HOME"; '
            'rm -f "$CODEX_HOME/AGENTS.md" "$CODEX_HOME/AGENTS.override.md"'
        )
        target = '"$CODEX_HOME/AGENTS.md"'
    elif runtime == "claude":
        wipe = (
            'rm -rf "$HOME/.claude/skills" "$CLAUDE_CONFIG_DIR/skills"; '
            'mkdir -p "$CLAUDE_CONFIG_DIR"; '
            'rm -f "$HOME/.claude/CLAUDE.md" "$CLAUDE_CONFIG_DIR/CLAUDE.md"'
        )
        target = '"$CLAUDE_CONFIG_DIR/CLAUDE.md"'
    else:
        wipe = (
            'rm -rf "$HOME/.grok/skills" "$HOME/.grok/installed-plugins" '
            '"$HOME/.agents/skills" "$HOME/.claude/skills"; '
            'mkdir -p "$HOME/.grok"; '
            'rm -f "$HOME/.grok/AGENTS.md" "$HOME/.claude/CLAUDE.md"'
        )
        target = '"$HOME/.grok/AGENTS.md"'
    command = f"({ensure}) && ({wipe})"
    if skills_dir:
        source = shlex.quote(skills_dir.rstrip("/") + "/global-instructions/instructions.md")
        command += f" && test -f {source} && cp {source} {target}"
    return command


def build_clean_skills_register_command(skills_dir: str | None) -> str:
    """Install a job-local AGENTS.md, or clear all policies for baseline."""
    return _build_global_register_command(skills_dir, "codex")


def build_clean_claude_skills_register_command(skills_dir: str | None) -> str:
    """Install CLAUDE.md into Harbor's isolated CLAUDE_CONFIG_DIR."""
    return _build_global_register_command(skills_dir, "claude")


def build_clean_grok_skills_register_command(skills_dir: str | None) -> str:
    """Install a job-local Grok AGENTS.md without registering native skills."""
    return _build_global_register_command(skills_dir, "grok")

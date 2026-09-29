"""Writable Codex / Claude Code homes for Harbor judge calls.

The trial bind-mounts host credentials read-only. The CLIs also write
sessions and may refresh those files, so each judge run gets a temp copy.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from llm_judge.log import log
from llm_judge.scores import reasoning_first_schema


def _copy_auth(source: Path, dest: Path) -> None:
    """Copy an auth file with mode 0600. Does not log contents."""
    dest.write_bytes(source.read_bytes())
    dest.chmod(stat.S_IRUSR | stat.S_IWUSR)


def find_codex_auth() -> Path | None:
    """Return the first readable Codex ``auth.json``, if any."""
    home = os.environ.get("CODEX_HOME", "").strip()
    candidates = []
    if home:
        candidates.append(Path(home) / "auth.json")
    acc_auth = _acc_selected_codex_auth()
    if acc_auth is not None:
        candidates.append(acc_auth)
    candidates.extend(
        [
            Path("/tmp/codex-home/auth.json"),
            Path.home() / ".codex" / "auth.json",
        ]
    )
    for path in candidates:
        if path and path.is_file():
            return path
    return None


def _acc_selected_codex_auth() -> Path | None:
    """Return the ACC-selected Codex auth file when the Harbor helper is importable."""
    evals_root = Path(__file__).resolve().parents[2]
    if str(evals_root) not in sys.path:
        sys.path.insert(0, str(evals_root))
    try:
        from harbor_agents.codex_account import selected_codex_auth
    except ImportError:
        return None
    path = selected_codex_auth()
    return path if path.is_file() else None


def setup_codex_home(effort: str) -> Path:
    """Create a writable ``CODEX_HOME`` with reasoning effort and a copied auth.

    Args:
        effort: ``low``, ``medium``, or ``high``.

    Returns:
        Temporary directory to export as ``CODEX_HOME``.
    """
    judge_home = Path(tempfile.mkdtemp(prefix="codex-judge-"))
    auth = find_codex_auth()
    if auth is not None:
        _copy_auth(auth, judge_home / "auth.json")
        log("codex eval agent: copied auth.json into writable CODEX_HOME")
    (judge_home / "config.toml").write_text(
        f'model_reasoning_effort = "{effort}"\n'
        'sandbox_mode = "danger-full-access"\n',
        encoding="utf-8",
    )
    return judge_home


def _oauth_from_credentials(path: Path) -> str:
    """Return the Claude access token from a credentials JSON file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    oauth = data.get("claudeAiOauth") if isinstance(data, dict) else None
    token = oauth.get("accessToken") if isinstance(oauth, dict) else None
    if isinstance(token, str) and token.strip():
        return token.strip()
    return ""


def find_claude_credentials() -> Path | None:
    """Return the first readable Claude credentials file, if any."""
    for path in (
        Path.home() / ".claude" / ".credentials.json",
        Path("/root/.claude/.credentials.json"),
    ):
        if path.is_file():
            return path
    return None


def setup_claude_home() -> tuple[Path, str]:
    """Create a writable ``CLAUDE_CONFIG_DIR`` and resolve the OAuth token.

    Args:
        None.

    Returns:
        Temp config dir and token string (empty when unset).

    Raises:
        FileNotFoundError: When neither a token nor credentials exist.
    """
    judge_home = Path(tempfile.mkdtemp(prefix="claude-judge-"))
    (judge_home / "debug").mkdir()
    (judge_home / "projects").mkdir()
    (judge_home / "skills").mkdir()
    cred_src = find_claude_credentials()
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
    if cred_src is not None:
        _copy_auth(cred_src, judge_home / ".credentials.json")
        log("claude eval agent: copied credentials.json into writable CLAUDE_CONFIG_DIR")
        if not token:
            token = _oauth_from_credentials(judge_home / ".credentials.json")
            if token:
                log("claude eval agent: loaded CLAUDE_CODE_OAUTH_TOKEN from credentials.json")
    if token and not (judge_home / ".credentials.json").is_file():
        (judge_home / ".credentials.json").write_text(
            json.dumps({"claudeAiOauth": {"accessToken": token}}) + "\n",
            encoding="utf-8",
        )
        (judge_home / ".credentials.json").chmod(stat.S_IRUSR | stat.S_IWUSR)
        log("claude eval agent: wrote credentials.json from CLAUDE_CODE_OAUTH_TOKEN")
    if not token and not (judge_home / ".credentials.json").is_file():
        shutil.rmtree(judge_home, ignore_errors=True)
        raise FileNotFoundError(
            "Claude Code eval agent needs CLAUDE_CODE_OAUTH_TOKEN or "
            "~/.claude/.credentials.json"
        )
    log(
        f"claude eval agent: CLAUDE_CONFIG_DIR={judge_home} "
        f"token_set={'yes' if token else 'no'} "
        f"credentials={'yes' if (judge_home / '.credentials.json').is_file() else 'no'}"
    )
    return judge_home, token


def claude_judge_env(home: Path, token: str) -> dict[str, str]:
    """Build the environment overlay for a Claude Code rewardkit judge.

    Parameters: home - writable ``CLAUDE_CONFIG_DIR``; token - OAuth access token
        (empty when credentials file is enough).

    Returns: env keys for the judge subprocess. Values are secrets; do not log them.
    """
    env = {
        "CLAUDE_FORCE_OAUTH": "true",
        "REWARDKIT_FORCE_OAUTH": "true",
        "CLAUDE_CONFIG_DIR": str(home),
        "IS_SANDBOX": "1",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    }
    if token:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = token
    return env


@contextmanager
def overlay_environ(extra: dict[str, str]) -> Iterator[None]:
    """Temporarily apply *extra* to ``os.environ``.

    Parameters: extra - keys to set for the duration of the context.

    Returns: context manager that restores previous values.
    """
    saved = {key: os.environ.get(key) for key in extra}
    os.environ.update(extra)
    log(f"environ overlay keys={','.join(sorted(extra))}")
    try:
        yield
    finally:
        for key, previous in saved.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def claude_wrapper_script(real: str, effort: str) -> str:
    """Return bash for a PATH wrapper that injects effort and bypassPermissions.

    Args:
        real: Absolute path of the real ``claude`` binary.
        effort: ``low``, ``medium``, or ``high``.

    Returns:
        Script text (no secrets).
    """
    # Quote via json.dumps so the wrapper is safe for spaces in paths.
    real_q = json.dumps(real)
    effort_q = json.dumps(effort)
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"real={real_q}\n"
        f"effort={effort_q}\n"
        'for arg in "$@"; do\n'
        '  if [[ "$arg" == "-p" || "$arg" == "--print" ]]; then\n'
        '    exec "$real" --effort "$effort" --permission-mode bypassPermissions "$@"\n'
        "  fi\n"
        "done\n"
        'exec "$real" "$@"\n'
    )


def rewrite_codex_output_schema(arguments: list[str]) -> None:
    """Order the backend's temporary Codex schema before CLI execution.

    Args:
        arguments: Original CLI arguments, including either accepted spelling
            of ``--output-schema``. Arguments and semantic constraints survive.

    Returns:
        None; only the supplied response-schema file is rewritten.
    """
    schema_path = None
    for index, argument in enumerate(arguments):
        if argument == "--output-schema" and index + 1 < len(arguments):
            schema_path = arguments[index + 1]
            break
        if argument.startswith("--output-schema="):
            schema_path = argument.split("=", 1)[1]
            break
    if schema_path is None:
        return
    try:
        path = Path(schema_path)
        schema = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps(reasoning_first_schema(schema)), encoding="utf-8")
    except (OSError, ValueError) as exc:
        log(f"codex judge schema ordering failed: {type(exc).__name__}")
        raise
    log("codex judge response schema ordered reasoning before score")


def codex_wrapper_script(real: str) -> str:
    """Return a schema-ordering shim that forwards argv to the real Codex CLI.

    Args:
        real: Absolute executable path resolved before installing the shim.

    Returns:
        Python source; probes and calls without schemas pass through unchanged.
    """
    module_root = str(Path(__file__).resolve().parent.parent)
    return (
        f"#!{sys.executable}\n"
        "import os, sys\n"
        f"sys.path.insert(0, {module_root!r})\n"
        "from llm_judge.homes import rewrite_codex_output_schema\n"
        "rewrite_codex_output_schema(sys.argv[1:])\n"
        f"os.execv({real!r}, [{real!r}, *sys.argv[1:]])\n"
    )


@contextmanager
def _judge_cli_on_path(command: str, script: Callable[[str], str]) -> Iterator[Path]:
    """Install one temporary CLI shim and restore PATH and files on exit.

    Args:
        command: Existing CLI executable name to locate before wrapping.
        script: Shared wrapper generator receiving the located executable.

    Yields:
        Temporary wrapper directory; cleanup also runs after failed judgments.
    """
    real = shutil.which(command)
    if not real:
        raise FileNotFoundError(f"{command} CLI not found on PATH for the eval agent")
    wrapper_dir = Path(tempfile.mkdtemp(prefix=f"{command}-wrap-"))
    wrapper = wrapper_dir / command
    wrapper.write_text(script(real), encoding="utf-8")
    wrapper.chmod(0o755)
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{wrapper_dir}{os.pathsep}{old_path}"
    log(f"{command} eval agent: temporary PATH wrapper enabled")
    try:
        yield wrapper_dir
    finally:
        os.environ["PATH"] = old_path
        shutil.rmtree(wrapper_dir, ignore_errors=True)


@contextmanager
def codex_reasoning_on_path() -> Iterator[Path]:
    """Make backend-created Codex schemas explanation-first in a scoped PATH.

    Args:
        None.

    Yields:
        The temporary wrapper directory; installed CLIs remain unchanged.
    """
    with _judge_cli_on_path("codex", codex_wrapper_script) as directory:
        yield directory


@contextmanager
def claude_effort_on_path(effort: str) -> Iterator[Path]:
    """Prepend a ``claude`` wrapper that adds effort on ``-p`` calls.

    Args:
        effort: ``low``, ``medium``, or ``high``.

    Yields:
        The temporary wrapper directory; PATH is restored on exit.
    """
    log(f"claude eval agent: PATH wrapper effort={effort} bypassPermissions")
    with _judge_cli_on_path("claude", lambda real: claude_wrapper_script(real, effort)) as directory:
        yield directory

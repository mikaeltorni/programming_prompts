#!/usr/bin/env python3
"""Resolve newest stable coding-agent CLI versions at Harbor instance start.

``run_benchmark.sh`` calls this once per invocation. Lookups are small JSON /
plain-text GETs (npm ``latest`` dist-tag, Grok ``stable`` channel pointer) —
not LLM calls. Results go to the gitignored
``evals/.generated/cli-versions/`` cache; committed ``*-version.txt`` pins
stay as fallbacks when the network is down.

Stdout is ``name=version`` lines. Diagnostics go to stderr.

Usage (from ``evals/``)::

    python3 harbor_agents/refresh_versions.py
    python3 harbor_agents/refresh_versions.py --self-test
    HARNESS_PIN_REFRESH=0 python3 harbor_agents/refresh_versions.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

_EVALS_DIR = Path(__file__).resolve().parents[1]
if str(_EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(_EVALS_DIR))

from harbor_agents.clean_skills import (
    generated_version_file,
    generated_versions_dir,
    load_claude_version,
    load_codex_version,
    load_grok_version,
)
from harbor_agents.log import log

HTTP_TIMEOUT_SEC = 15.0
USER_AGENT = "programming-prompts-evals-refresh/1.0"

NPM_PACKAGES: dict[str, str] = {
    "codex": "@openai/codex",
    "claude": "@anthropic-ai/claude-code",
}
GROK_STABLE_URLS: tuple[str, ...] = (
    "https://x.ai/cli/stable",
    "https://storage.googleapis.com/grok-build-public-artifacts/cli/stable",
)

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?$")
PRERELEASE_RE = re.compile(r"(?i)(?:^|[-.])(alpha|beta|rc|pre|dev)(?:[-.]|$)")
FALSEY = frozenset({"0", "false", "no", "off"})

Fetcher = Callable[[str], str]


def refresh_enabled(raw: str | None = None) -> bool:
    """Return whether instance-start version lookup should run.

    Args:
        raw: Environment value. Defaults to ``HARNESS_PIN_REFRESH``.
    """
    value = (raw if raw is not None else os.environ.get("HARNESS_PIN_REFRESH", "1"))
    return value.strip().lower() not in FALSEY


def is_stable_version(version: str) -> bool:
    """Return True when *version* is X.Y.Z without a prerelease suffix.

    Args:
        version: Candidate such as ``0.149.0`` or ``0.150.0-alpha.7``.
    """
    stripped = version.strip()
    if not VERSION_RE.match(stripped):
        return False
    return PRERELEASE_RE.search(stripped) is None


def fetch_url(url: str, timeout: float = HTTP_TIMEOUT_SEC) -> str:
    """GET *url* and return the decoded body.

    Args:
        url: Absolute HTTP(S) URL.
        timeout: Socket timeout in seconds.

    Returns:
        Response body as text.

    Raises:
        OSError: On HTTP or network failure.
    """
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json, text/plain"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise OSError(f"GET {url} failed: {exc}") from exc
    return body.decode("utf-8", errors="replace")


def fetch_npm_latest(package: str, fetcher: Fetcher = fetch_url) -> str:
    """Return the npm ``latest`` dist-tag for *package*.

    Args:
        package: Scoped npm name such as ``@openai/codex``.
        fetcher: HTTP GET used in tests.

    Returns:
        A stable X.Y.Z version.

    Raises:
        OSError: When the registry is unreachable or the tag is a prerelease.
    """
    encoded = urllib.parse.quote(package, safe="@")
    url = f"https://registry.npmjs.org/{encoded}/latest"
    raw = fetcher(url)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OSError(f"npm {package}: response is not JSON") from exc
    version = str(payload.get("version") or "").strip()
    if not is_stable_version(version):
        raise OSError(f"npm {package}: latest {version!r} is not a stable X.Y.Z")
    return version


def fetch_grok_stable(fetcher: Fetcher = fetch_url) -> str:
    """Return the Grok Build ``stable`` channel pointer.

    Args:
        fetcher: HTTP GET used in tests. Tries x.ai then the public GCS mirror.

    Returns:
        A stable X.Y.Z version.

    Raises:
        OSError: When every channel URL fails or the body is not a version.
    """
    errors: list[str] = []
    for url in GROK_STABLE_URLS:
        try:
            body = fetcher(url).strip().splitlines()[0].strip()
        except OSError as exc:
            errors.append(str(exc))
            continue
        version = body.removeprefix("v").strip()
        if is_stable_version(version):
            return version
        errors.append(f"{url}: {body!r} is not a stable X.Y.Z")
    raise OSError("Grok stable channel failed: " + "; ".join(errors))


def write_generated_version(name: str, version: str) -> Path:
    """Write one harness version into the instance-start cache.

    Args:
        name: ``codex``, ``claude``, or ``grok``.
        version: Stable X.Y.Z string.

    Returns:
        The cache file path.
    """
    directory = generated_versions_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = generated_version_file(name)
    path.write_text(version + "\n", encoding="utf-8")
    log(f"cached {name} CLI {version} -> {path}")
    return path


def resolve_one(
    name: str,
    fallback: str,
    lookup: Callable[[], str],
) -> str:
    """Look up one CLI version, keeping *fallback* when the registry fails.

    Args:
        name: Harness pin stem.
        fallback: Committed pin / default already loaded.
        lookup: Network function that returns a stable version.

    Returns:
        Newest stable version, or *fallback*.
    """
    try:
        newest = lookup()
    except OSError as exc:
        log(f"{name}: keeping pin {fallback} ({exc})")
        return fallback
    if newest != fallback:
        log(f"{name}: {fallback} -> {newest}")
    else:
        log(f"{name}: already at newest stable {newest}")
    return newest


def refresh_versions(*, fetcher: Fetcher | None = None) -> dict[str, str]:
    """Look up newest stable CLIs and write the instance-start cache.

    Args:
        fetcher: Optional HTTP GET override for tests.

    Returns:
        Mapping of ``codex`` / ``claude`` / ``grok`` to the version this
        instance should install. Network failures keep the committed pin.
    """
    get = fetcher or fetch_url
    resolved = {
        "codex": resolve_one(
            "codex",
            load_codex_version(),
            lambda: fetch_npm_latest(NPM_PACKAGES["codex"], get),
        ),
        "claude": resolve_one(
            "claude",
            load_claude_version(),
            lambda: fetch_npm_latest(NPM_PACKAGES["claude"], get),
        ),
        "grok": resolve_one(
            "grok",
            load_grok_version(),
            lambda: fetch_grok_stable(get),
        ),
    }
    for name, version in resolved.items():
        write_generated_version(name, version)
    return resolved


def _self_test() -> int:
    """Check prerelease filtering, fallbacks, and cache writes without HTTP."""
    cases: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {name}: {detail}", file=sys.stderr)

    check("stable_ok", is_stable_version("0.149.0"), "0.149.0 is stable")
    check(
        "alpha_rejected",
        not is_stable_version("0.150.0-alpha.7"),
        "alpha tag is not used",
    )
    check("refresh_off", not refresh_enabled("0"), "HARNESS_PIN_REFRESH=0 disables")
    check("refresh_on", refresh_enabled("1"), "default/1 enables refresh")

    def fake_fetch(url: str) -> str:
        if url.endswith("/@openai/codex/latest") or "openai%2Fcodex" in url:
            return json.dumps({"version": "0.149.0"})
        if "anthropic-ai" in url:
            return json.dumps({"version": "2.1.241"})
        if url.endswith("/stable"):
            return "1.0.5\n"
        raise OSError(f"unexpected url {url}")

    versions = refresh_versions(fetcher=fake_fetch)
    check(
        "fake_lookup",
        versions == {"codex": "0.149.0", "claude": "2.1.241", "grok": "1.0.5"},
        f"versions={versions}",
    )
    check(
        "cache_written",
        generated_version_file("codex").read_text(encoding="utf-8").strip()
        == "0.149.0",
        "instance cache stores Codex",
    )

    def failing_fetch(url: str) -> str:
        raise OSError("offline")

    # Pins/cache already written above; failing lookup must not crash.
    kept = refresh_versions(fetcher=failing_fetch)
    check("offline_keeps_cache", "codex" in kept and bool(kept["codex"]), f"kept={kept}")

    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} refresh_versions self-test(s) failed", file=sys.stderr)
        return 1
    print(f"{len(cases)}/{len(cases)} refresh_versions self-tests passed", file=sys.stderr)
    return 0


def _cli(argv: list[str]) -> int:
    """Dispatch refresh or the in-module self-test."""
    parser = argparse.ArgumentParser(
        description="Look up newest stable Codex / Claude Code / Grok CLI versions"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run in-module checks (no live registry calls)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip lookups; rewrite the instance cache from current pins",
    )
    args = parser.parse_args(argv[1:])
    if args.self_test:
        return _self_test()
    if args.offline or not refresh_enabled():
        log("refresh disabled; using committed pin files")
        versions = {
            "codex": load_codex_version(use_cache=False),
            "claude": load_claude_version(use_cache=False),
            "grok": load_grok_version(use_cache=False),
        }
        for name, version in versions.items():
            write_generated_version(name, version)
    else:
        versions = refresh_versions()
    for name, version in versions.items():
        print(f"{name}={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv))

"""Docker mount serialization for Harbor coding-agent harnesses."""

from __future__ import annotations

import json
from pathlib import Path

from harbor_agents.harness_registry import (
    CODEX_AUTH_MOUNT,
    BindMount,
    require_harness,
)


def _mount_dict(
    mount: BindMount, home: Path
) -> dict[str, str | bool] | None:
    """Build one Docker mount mapping.

    Parameters: mount - bind-mount metadata; home - host home directory.

    Returns: Mount mapping, or ``None`` when an optional source is absent.
    """
    source = home.joinpath(*mount.source_parts)
    if mount.optional and not source.is_file():
        return None
    return {
        "type": "bind",
        "source": str(source),
        "target": mount.target,
        "read_only": True,
    }


def mounts_json(*names: str, home: Path | None = None) -> str:
    """Serialize auth mounts for one or more harnesses.

    Parameters: names - canonical harness ids; home - optional host home.

    Returns: JSON array of bind mounts, deduplicated by target.
    """
    if not names:
        raise ValueError("mounts requires at least one harness id")
    home = home or Path.home()
    mounts: list[dict[str, str | bool]] = []
    seen_targets: set[str] = set()

    def _append(mount: BindMount) -> None:
        item = _mount_dict(mount, home)
        if item is None:
            return
        target = str(item["target"])
        if target in seen_targets:
            return
        seen_targets.add(target)
        mounts.append(item)

    _append(CODEX_AUTH_MOUNT)
    for name in names:
        spec = require_harness(name)
        for extra in spec.extra_mounts:
            _append(extra)
    return json.dumps(mounts)

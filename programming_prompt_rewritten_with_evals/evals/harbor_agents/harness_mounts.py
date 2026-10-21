"""Docker mount serialization for Harbor coding-agent harnesses."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from harbor_agents.codex_account import selected_codex_auth_parts
from harbor_agents.harness_registry import (
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


def _snapshot_catalog(source: Path, destination: Path) -> Path:
    """Freeze one run's metadata so native clients share identical model data.

    Parameters: source - selected account's existing cache; destination - run archive copy.
    Returns: existing or newly copied run snapshot path.
    """
    print(f"source={source} destination={destination}", file=sys.stderr)
    if not destination.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination.parent) as temporary:
            shutil.copyfile(source, temporary.name)
            try:
                os.link(temporary.name, destination)
            except FileExistsError:
                pass
    print(destination, file=sys.stderr)
    return destination


def mounts_json(*names: str, home: Path | None = None) -> str:
    """Serialize selected-account auth and optional catalogue mounts for harnesses.

    Parameters: names - canonical harness ids; home - optional host home.

    Returns: JSON array of bind mounts, deduplicated by target.
    """
    print(f"names={names} home={home}", file=sys.stderr)
    if not names:
        raise ValueError("mounts requires at least one harness id")
    home = home or Path.home()
    mounts: list[dict[str, str | bool]] = []
    seen_targets: set[str] = set()
    archive = os.environ.get("RUN_DIR")
    run_directory = Path(archive) if archive else None

    def _append(mount: BindMount) -> None:
        """Append an available mount and freeze catalogue input once per run.

        Parameters: mount - converted mount specification.
        Returns: None.
        """
        print(f"mount={mount}", file=sys.stderr)
        item = _mount_dict(mount, home)
        if item is None:
            print(None, file=sys.stderr)
            return
        target = str(item["target"])
        if target in seen_targets:
            print(None, file=sys.stderr)
            return
        if target == "/root/.codex/models_cache.json" and run_directory:
            item["source"] = str(_snapshot_catalog(
                Path(str(item["source"])), run_directory / "codex-model-catalog.json",
            ))
        seen_targets.add(target)
        mounts.append(item)
        print(None, file=sys.stderr)

    auth_parts = selected_codex_auth_parts(home)
    _append(
        BindMount(
            source_parts=auth_parts,
            target="/root/.codex/auth.json",
        )
    )
    _append(
        BindMount(
            source_parts=(*auth_parts[:-1], "models_cache.json"),
            target="/root/.codex/models_cache.json",
            optional=True,
        )
    )
    for name in names:
        spec = require_harness(name)
        for extra in spec.extra_mounts:
            _append(extra)
    result = json.dumps(mounts)
    print(result, file=sys.stderr)
    return result

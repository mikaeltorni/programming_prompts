"""Reclaim leftover Harbor trial containers, images, and build cache.

Harbor names one compose project per trial (``calculator__abc1234__env``),
so ``docker compose up --build`` tags a unique ``*__env-main`` image even
when layers are cached. Automatic reclaim only removes exited containers
and empty networks (IPAM). Deleting unused image tags and BuildKit cache
is opt-in so the next trial can reuse layers instead of rebuilding.
"""

from __future__ import annotations

import subprocess
from typing import Any

from .log import log
from .math import is_harbor_trial_container, is_harbor_trial_image


def _docker(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run Docker and capture text output.

    Parameters: args - arguments after ``docker``.

    Returns: completed process (never raises on non-zero).
    """
    return subprocess.run(
        ["docker", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _docker_rows(args: list[str]) -> list[str]:
    """Return non-empty stdout lines from a Docker command.

    Parameters: args - arguments after ``docker``.

    Returns: stripped lines, or an empty list on failure.
    """
    proc = _docker(args)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        if err:
            log(f"docker {' '.join(args)} failed: {err}")
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def prune_exited_harbor_containers() -> list[str]:
    """Remove exited Harbor trial containers that hold networks and images.

    Parameters: none.

    Returns: removed container ids.
    """
    rows = _docker_rows(
        ["ps", "-a", "--filter", "status=exited", "--format", "{{.ID}}\t{{.Names}}"]
    )
    removed: list[str] = []
    for row in rows:
        container_id, _, name = row.partition("\t")
        if not container_id or not is_harbor_trial_container(name):
            continue
        proc = _docker(["rm", "-f", container_id])
        if proc.returncode == 0:
            removed.append(container_id)
        else:
            log(f"could not remove container {name}: {(proc.stderr or '').strip()}")
    if removed:
        log(f"removed {len(removed)} exited Harbor container(s)")
    return removed


def _in_use_image_keys() -> set[str]:
    """Return image names and ids still attached to any container.

    Parameters: none.

    Returns: repository, tag, and id strings that must not be deleted.
    """
    keys: set[str] = set()
    for row in _docker_rows(["ps", "-a", "--format", "{{.Image}}\t{{.ID}}"]):
        image, _, _cid = row.partition("\t")
        if image:
            keys.add(image)
            keys.add(image.split(":", 1)[0])
    return keys


def prune_unused_harbor_images() -> list[str]:
    """Delete Harbor trial image tags that no container still uses.

    Parameters: none.

    Returns: removed ``repo:tag`` names.
    """
    in_use = _in_use_image_keys()
    rows = _docker_rows(["images", "--format", "{{.Repository}}:{{.Tag}}\t{{.ID}}"])
    removed: list[str] = []
    for row in rows:
        ref, _, image_id = row.partition("\t")
        repo = ref.split(":", 1)[0]
        if not is_harbor_trial_image(repo):
            continue
        if ref in in_use or repo in in_use or image_id in in_use:
            continue
        proc = _docker(["rmi", "-f", ref])
        if proc.returncode == 0:
            removed.append(ref)
        else:
            log(f"could not remove image {ref}: {(proc.stderr or '').strip()}")
    if removed:
        log(f"removed {len(removed)} unused Harbor trial image(s)")
    return removed


def prune_unused_builder_cache() -> bool:
    """Drop dangling BuildKit cache not referenced by current images.

    Parameters: none.

    Returns: true when Docker accepted the prune command.
    """
    proc = _docker(["builder", "prune", "-f"])
    if proc.returncode != 0:
        log(f"builder prune failed: {(proc.stderr or proc.stdout or '').strip()}")
        return False
    summary = (proc.stdout or "").strip().splitlines()
    if summary:
        log(f"builder prune: {summary[-1]}")
    else:
        log("builder prune: no unused cache")
    return True


def reclaim_docker_leftovers(
    *,
    images: bool = False,
    builder_cache: bool = False,
) -> dict[str, Any]:
    """Free leftover Harbor Docker state in a safe order.

    Automatic evals reclaim (the default) only drops exited containers and
    empty networks so the next trial can reuse image layers and BuildKit
    cache. Passing ``images`` / ``builder_cache`` is the manual disk-reclaim
    path — that is what made jobs slow when it ran between every Harbor job.

    Parameters: images - delete unused ``*__env-main`` tags; builder_cache - also prune dangling BuildKit cache.

    Returns: counts of removed containers, networks, and images.
    """
    from .live import prune_stale_networks

    containers = prune_exited_harbor_containers()
    networks = prune_stale_networks()
    removed_images = prune_unused_harbor_images() if images else []
    if builder_cache:
        prune_unused_builder_cache()
    log(
        f"reclaim containers={len(containers)} networks={len(networks)} "
        f"images={len(removed_images)} builder_cache={int(builder_cache)}"
    )
    return {
        "containers": len(containers),
        "networks": len(networks),
        "images": len(removed_images),
    }

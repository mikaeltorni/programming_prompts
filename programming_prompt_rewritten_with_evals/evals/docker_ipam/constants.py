"""Constants governing Docker IPAM capacity and slot coordination."""

from pathlib import Path


DEFAULT_ADDRESS_POOLS: tuple[tuple[str, int], ...] = (
    ("172.17.0.0/16", 16),
    ("172.18.0.0/16", 16),
    ("172.19.0.0/16", 16),
    ("172.20.0.0/14", 16),
    ("172.24.0.0/14", 16),
    ("172.28.0.0/14", 16),
    ("192.168.0.0/16", 20),
)

RECOMMENDED_ADDRESS_POOLS: tuple[tuple[str, int], ...] = (
    ("172.18.0.0/16", 24),
    ("172.19.0.0/16", 24),
    ("172.20.0.0/14", 24),
    ("172.24.0.0/13", 24),
    ("192.168.0.0/16", 24),
)

BUILTIN_NETWORKS = frozenset({"bridge", "host", "none"})
HARBOR_NETWORK_SUFFIX = "__env_default"
HARBOR_IMAGE_SUFFIX = "__env-main"
HARBOR_CONTENT_IMAGE_PREFIX = "hb__"
LLM_MAX_CONCURRENT_DEFAULT = 10
LLM_MAX_CONCURRENT_UNLIMITED = 10**9
DAEMON_JSON_PATH = Path("/etc/docker/daemon.json")
SAFETY_MARGIN = 2
STALE_GRACE_SEC = 60.0
POLL_SEC = 1.0
WAIT_LOG_SEC = 15.0
POOL_EXHAUSTED_NEEDLE = "all predefined address pools have been fully subnetted"

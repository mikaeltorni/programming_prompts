"""Monitor discovery and terminal-window geometry."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Sequence

XRANDR_CONNECTED_RE = re.compile(
    r"^(\S+)\s+connected(?:\s+primary)?\s+(\d+)x(\d+)\+(\d+)\+(\d+)",
    re.MULTILINE,
)
NORMAL_WIDTH_PX = 1100
NORMAL_HEIGHT_PX = 700
CASCADE_STEP_PX = 56


@dataclass(frozen=True)
class Monitor:
    """One connected display in screen coordinates."""

    name: str
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        """Return the right screen coordinate.

        Parameters: none.

        Returns: the coordinate immediately after the monitor's right edge.
        """
        return self.x + self.width

    @property
    def bottom(self) -> int:
        """Return the bottom screen coordinate.

        Parameters: none.

        Returns: the coordinate immediately after the monitor's bottom edge.
        """
        return self.y + self.height

    def contains(self, px: int, py: int) -> bool:
        """Check whether a point lies inside this monitor.

        Parameters: px - screen X; py - screen Y.

        Returns: True when the point is inside.
        """
        return self.x <= px < self.right and self.y <= py < self.bottom

    def center_distance(self, px: int, py: int) -> float:
        """Measure distance from a point to the monitor center.

        Parameters: px - screen X; py - screen Y.

        Returns: Euclidean distance in pixels.
        """
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        return math.hypot(px - cx, py - cy)


@dataclass(frozen=True)
class Rect:
    """Pixel rectangle for a cascaded terminal."""

    x: int
    y: int
    width: int
    height: int


def parse_xrandr(text: str) -> list[Monitor]:
    """Parse connected outputs from xrandr.

    Parameters: text - raw ``xrandr --current`` stdout.

    Returns: connected monitors in xrandr order.
    """
    return [
        Monitor(
            name=match.group(1),
            width=int(match.group(2)),
            height=int(match.group(3)),
            x=int(match.group(4)),
            y=int(match.group(5)),
        )
        for match in XRANDR_CONNECTED_RE.finditer(text)
    ]


def monitor_for_point(
    monitors: Sequence[Monitor], px: int, py: int
) -> Monitor | None:
    """Choose the monitor containing or nearest a point.

    Parameters: monitors - connected displays; px - screen X; py - screen Y.

    Returns: the containing or nearest monitor, or None for an empty sequence.
    """
    if not monitors:
        return None
    for monitor in monitors:
        if monitor.contains(px, py):
            return monitor
    return min(monitors, key=lambda item: item.center_distance(px, py))


def cascade_rects(
    monitor: Monitor,
    count: int,
    *,
    width: int = NORMAL_WIDTH_PX,
    height: int = NORMAL_HEIGHT_PX,
    step: int = CASCADE_STEP_PX,
) -> list[Rect]:
    """Create staggered normal-sized rectangles on one monitor.

    Parameters: monitor - target display; count - window count; width - desired width; height - desired height; step - cascade offset.

    Returns: rectangles clamped within the monitor.
    """
    if count < 1:
        return []
    width = min(width, max(640, monitor.width - 80))
    height = min(height, max(400, monitor.height - 80))
    max_x = monitor.x + max(0, monitor.width - width - 16)
    max_y = monitor.y + max(0, monitor.height - height - 16)
    start_x = min(monitor.x + 48, max_x)
    start_y = min(monitor.y + 48, max_y)
    span_x = max(step, max_x - start_x)
    span_y = max(step, max_y - start_y)
    return [
        Rect(
            x=start_x + (index * step) % span_x,
            y=start_y + (index * step) % span_y,
            width=width,
            height=height,
        )
        for index in range(count)
    ]

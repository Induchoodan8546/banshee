"""Easing, squash, and a lagging ground shadow. Never teleport."""

from __future__ import annotations

import math
from collections import deque


def clamp(value: float, lo: float, hi: float) -> float:
    return lo if value < lo else hi if value > hi else value


def ease_in_out_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0


def ease_out_back(t: float, overshoot: float = 1.12) -> float:
    t = clamp(t, 0.0, 1.0)
    s = overshoot
    t -= 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def breathe_px(now: float) -> tuple[int, int]:
    """Whole-pixel hover and squash. Fractional scale dissolves pixel art."""
    hover = int(round(math.sin(now * 2.15) * 3.0))
    squash = int(round(math.sin(now * 3.7) * 3.0))
    return hover, squash


class LagShadow:
    """Oval that trails the body by 80–120ms."""

    def __init__(self, lag_s: float = 0.1) -> None:
        self.lag_s = lag_s
        self._hist: deque[tuple[float, float, float]] = deque(maxlen=48)
        self.x = 0.0
        self.y = 0.0

    def push(self, now: float, x: float, y: float) -> None:
        self._hist.append((now, x, y))
        target = now - self.lag_s
        chosen = self._hist[0]
        for sample in self._hist:
            if sample[0] <= target:
                chosen = sample
            else:
                break
        self.x, self.y = chosen[1], chosen[2]

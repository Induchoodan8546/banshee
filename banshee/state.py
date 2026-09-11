"""Haunt phase clock. ROOM / MANIFEST live in Phase 1."""

from __future__ import annotations

from enum import Enum


class Haunt(str, Enum):
    ROOM = "ROOM"
    MANIFEST = "MANIFEST"
    POSSESS = "POSSESS"
    SYSTEM = "SYSTEM"
    BANISHED = "BANISHED"


class Clock:
    def __init__(self) -> None:
        self.t = 0.0
        self.phase = Haunt.ROOM

    def tick(self, dt: float) -> None:
        self.t += dt

    def skip_to(self, seconds: float) -> None:
        self.t = max(self.t, seconds)

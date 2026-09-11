"""One shadowy figure at a time. Not the cute blob."""

from __future__ import annotations

from enum import Enum

import pygame

from banshee.config import ASSETS_SHADOWS, INNER


class ShadeKind(str, Enum):
    WALL_SLIDE = "WALL_SLIDE"
    UNDER_FURNITURE = "UNDER_FURNITURE"
    DOOR_CRACK = "DOOR_CRACK"
    FALSE_GHOST = "FALSE_GHOST"


class Shade:
    def __init__(self) -> None:
        self.kind: ShadeKind | None = None
        self.x = 0.0
        self.y = 0.0
        self.t = 0.0
        self.dur = 1.0
        self.alpha = 0
        self.alive = False
        self.images = {
            ShadeKind.WALL_SLIDE: pygame.image.load(str(ASSETS_SHADOWS / "wall_slide.png")).convert_alpha(),
            ShadeKind.UNDER_FURNITURE: pygame.image.load(str(ASSETS_SHADOWS / "crawl.png")).convert_alpha(),
            ShadeKind.DOOR_CRACK: pygame.image.load(str(ASSETS_SHADOWS / "door_crack.png")).convert_alpha(),
            ShadeKind.FALSE_GHOST: pygame.image.load(str(ASSETS_SHADOWS / "false_ghost.png")).convert_alpha(),
        }

    def spawn(self, kind: ShadeKind, extra: dict | None = None) -> None:
        extra = extra or {}
        self.kind = kind
        self.alive = True
        self.t = 0.0
        left, top, right, bot = INNER
        if kind is ShadeKind.WALL_SLIDE:
            self.dur = extra.get("dur", 3.2)
            img = self.images[kind]
            self.x = float(left - img.get_width())
            self.y = float(extra.get("y", top + 40))
            self._end_x = float(right + 8)
        elif kind is ShadeKind.UNDER_FURNITURE:
            self.dur = 2.4
            self.x = float(extra.get("x", 420))
            self.y = float(extra.get("y", 480))
            self._end_x = self.x + 160
        elif kind is ShadeKind.DOOR_CRACK:
            self.dur = 2.6
            self.x = float(extra.get("x", 390))
            self.y = float(extra.get("y", 280))
            self._end_x = self.x
        elif kind is ShadeKind.FALSE_GHOST:
            self.dur = 2.2
            self.x = float(extra.get("x", 430))
            self.y = float(extra.get("y", 360))
            self._end_x = self.x + 90

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        self.t += dt
        u = min(1.0, self.t / self.dur)
        if self.kind is ShadeKind.WALL_SLIDE:
            self.x += (self._end_x - self.x) * min(1.0, dt / max(0.01, self.dur - self.t + dt))
            start = INNER[0] - 40
            self.x = start + (self._end_x - start) * u
            self.alpha = 150 if 0.08 < u < 0.92 else int(150 * min(u, 1 - u) / 0.08)
        elif self.kind is ShadeKind.UNDER_FURNITURE:
            origin = self._end_x - 160
            self.x = origin + 160 * u
            self.alpha = 130
        elif self.kind is ShadeKind.DOOR_CRACK:
            pulse = 0.5 + 0.5 * abs((u * 2) % 2 - 1)
            self.alpha = int(90 + 70 * pulse)
        elif self.kind is ShadeKind.FALSE_GHOST:
            origin = self._end_x - 90
            self.x = origin + 90 * u
            self.alpha = int(180 * (1.0 - u))
        if u >= 1.0:
            self.alive = False
            self.kind = None

    def draw(self, surf: pygame.Surface) -> None:
        if not self.alive or self.kind is None:
            return
        img = self.images[self.kind].copy()
        img.set_alpha(max(0, min(220, self.alpha)))
        surf.blit(img, (int(self.x), int(self.y)))

"""Furniture hotspots and tiny motion (rock, tap, flicker)."""

from __future__ import annotations

import json
import math

import pygame

from banshee.config import ASSETS_ROOM


class Prop:
    def __init__(self, pid: str, image: pygame.Surface | None, spec: dict) -> None:
        self.id = pid
        self.image = image
        self.x = int(spec["x"])
        self.y = int(spec["y"])
        self.z = int(spec.get("z", 1))
        self.hide = bool(spec.get("hide", False))
        self.ox = 0
        self.oy = 0
        self.alpha = 255
        if image is not None:
            self.w = image.get_width()
            self.h = image.get_height()
        else:
            self.w = int(spec.get("w", 80))
            self.h = int(spec.get("h", 80))

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x + self.ox, self.y + self.oy, self.w, self.h)

    def draw(self, surf: pygame.Surface) -> None:
        if self.image is None:
            return
        img = self.image
        if self.alpha < 255:
            img = self.image.copy()
            img.set_alpha(self.alpha)
        surf.blit(img, (self.x + self.ox, self.y + self.oy))


class Props:
    def __init__(self) -> None:
        raw = json.loads((ASSETS_ROOM / "occlusion_map.json").read_text(encoding="utf-8"))
        self.map = raw
        self.items: dict[str, Prop] = {}
        names = {
            "wardrobe": "wardrobe.png",
            "chair": "chair.png",
            "chest": "chest.png",
            "stool": "stool.png",
            "lamp": "lamp.png",
            "window": None,
        }
        for pid, spec in raw["props"].items():
            img = None
            file_name = names.get(pid)
            if file_name:
                img = pygame.image.load(str(ASSETS_ROOM / file_name)).convert_alpha()
            self.items[pid] = Prop(pid, img, spec)
        self.perches = {k: tuple(v) for k, v in raw["perches"].items()}
        self.manifest = tuple(raw["manifest"])
        self._chest_tap = 0.0
        self.hover_chair = False

    def hit(self, pos: tuple[int, int]) -> str | None:
        for pid in ("wardrobe", "chair", "chest", "stool", "lamp", "window"):
            if self.items[pid].rect.collidepoint(pos):
                return pid
        return None

    def hide_slot(self, pid: str) -> tuple[float, float]:
        prop = self.items[pid]
        return (prop.x + 18, prop.y + 40)

    def peek_slot(self, pid: str) -> tuple[float, float]:
        prop = self.items[pid]
        return (prop.x + prop.w - 12, prop.y + 70)

    def update(self, dt: float, now: float) -> None:
        chair = self.items["chair"]
        rock = math.sin(now * 1.7) * (2.0 if self.hover_chair else 1.0)
        chair.ox = int(rock)
        if self._chest_tap > 0:
            self._chest_tap -= dt
            self.items["chest"].oy = -3
        else:
            self.items["chest"].oy = 0
        flicker = 255 if math.sin(now * 11.0) > -0.75 else 150
        self.items["lamp"].alpha = flicker

    def tap_chest(self) -> None:
        self._chest_tap = 0.18

    def draw(self, surf: pygame.Surface) -> None:
        for pid in ("lamp", "stool", "chest", "chair", "wardrobe"):
            self.items[pid].draw(surf)

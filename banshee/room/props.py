"""Live furniture: open cupboard, drag chair, chest lid, lamp toggle."""

from __future__ import annotations

import json
import math

import pygame

from banshee.config import ASSETS_ROOM, FLOOR_Y, WINDOW_W


class Prop:
    def __init__(self, pid: str, image: pygame.Surface | None, spec: dict) -> None:
        self.id = pid
        self.closed_img = image
        self.open_img = image
        self.x = int(spec["x"])
        self.y = int(spec["y"])
        self.z = int(spec.get("z", 1))
        self.hide = bool(spec.get("hide", False))
        self.draggable = bool(spec.get("drag", False))
        self.opened = False
        self.ox = 0
        self.oy = 0
        self.alpha = 255
        self.lamp_on = True
        self._flicker = 0.0
        if image is not None:
            self.w = image.get_width()
            self.h = image.get_height()
        else:
            self.w = int(spec.get("w", 80))
            self.h = int(spec.get("h", 80))

    @property
    def image(self) -> pygame.Surface | None:
        return self.open_img if self.opened and self.open_img is not None else self.closed_img

    @property
    def rect(self) -> pygame.Rect:
        img = self.image
        w = img.get_width() if img is not None else self.w
        h = img.get_height() if img is not None else self.h
        return pygame.Rect(self.x + self.ox, self.y + self.oy, w, h)

    def draw(self, surf: pygame.Surface) -> None:
        img = self.image
        if img is None:
            return
        blit = img
        alpha = self.alpha
        if self.id == "lamp" and self._flicker > 0:
            alpha = 110 if int(self._flicker * 20) % 2 == 0 else 255
        elif self.id == "lamp" and not self.lamp_on:
            alpha = 120
        if alpha < 255:
            blit = img.copy()
            blit.set_alpha(alpha)
        if self.id == "chest" and self.opened:
            blit = pygame.transform.rotate(img, 12)
        surf.blit(blit, (self.x + self.ox, self.y + self.oy))


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
        open_path = ASSETS_ROOM / "wardrobe_open.png"
        if open_path.exists():
            self.items["wardrobe"].open_img = pygame.image.load(str(open_path)).convert_alpha()
        self.perches = {k: (float(v[0]), float(v[1])) for k, v in raw["perches"].items()}
        self.manifest = (float(raw["manifest"][0]), float(raw["manifest"][1]))
        self._chest_tap = 0.0
        self.dragging: str | None = None
        self._grab = (0, 0)
        self.unease_rock = True

    def hit(self, pos: tuple[int, int]) -> str | None:
        for pid in ("wardrobe", "chair", "chest", "stool", "lamp", "window"):
            if self.items[pid].rect.collidepoint(pos):
                return pid
        return None

    def hide_slot(self, pid: str) -> tuple[float, float]:
        prop = self.items[pid]
        return (prop.x + 28, prop.y + 50)

    def peek_slot(self, pid: str) -> tuple[float, float]:
        prop = self.items[pid]
        return (prop.x + prop.rect.w - 20, prop.y + 64)

    def begin_drag(self, pid: str, pos: tuple[int, int]) -> bool:
        prop = self.items.get(pid)
        if prop is None or not prop.draggable:
            return False
        self.dragging = pid
        self._grab = (pos[0] - prop.x, pos[1] - prop.y)
        return True

    def drag_to(self, pos: tuple[int, int]) -> None:
        if not self.dragging:
            return
        prop = self.items[self.dragging]
        prop.x = int(pos[0] - self._grab[0])
        prop.y = int(pos[1] - self._grab[1])
        prop.x = max(8, min(WINDOW_W - prop.rect.w - 8, prop.x))
        prop.y = max(int(FLOOR_Y - prop.h - 40), min(int(FLOOR_Y - prop.h + 8), prop.y))

    def end_drag(self) -> None:
        self.dragging = None

    def toggle(self, pid: str) -> str:
        if pid == "wardrobe":
            wr = self.items["wardrobe"]
            wr.opened = not wr.opened
            return "open" if wr.opened else "close"
        if pid == "chest":
            ch = self.items["chest"]
            ch.opened = not ch.opened
            self._chest_tap = 0.2
            return "open" if ch.opened else "close"
        if pid == "lamp":
            lp = self.items["lamp"]
            lp.lamp_on = not lp.lamp_on
            return "lamp"
        return "poke"

    def tap_chest(self) -> None:
        self._chest_tap = 0.18

    def flicker_lamp(self, seconds: float = 0.8) -> None:
        self.items["lamp"]._flicker = seconds

    def nudge(self, pid: str, dx: int) -> None:
        prop = self.items[pid]
        prop.x = max(8, min(WINDOW_W - prop.rect.w - 8, prop.x + dx))

    def update(self, dt: float, now: float) -> None:
        chair = self.items["chair"]
        if self.dragging != "chair" and self.unease_rock:
            chair.ox = int(round(math.sin(now * 1.4) * 1))
        else:
            chair.ox = 0
        if self._chest_tap > 0:
            self._chest_tap -= dt
            self.items["chest"].oy = -4
        else:
            self.items["chest"].oy = 0
        lamp = self.items["lamp"]
        if lamp._flicker > 0:
            lamp._flicker -= dt

    def draw(self, surf: pygame.Surface) -> None:
        for pid in ("lamp", "stool", "chest", "chair", "wardrobe"):
            self.items[pid].draw(surf)

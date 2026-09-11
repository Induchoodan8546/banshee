"""Blob state machine. She is a body, not a sticker."""

from __future__ import annotations

import random
from enum import Enum
import pygame

from banshee.actors import motion
from banshee.config import ASSETS_GHOST, FLOOR_Y


class GhostState(str, Enum):
    ABSENT = "ABSENT"
    MANIFEST = "MANIFEST"
    IDLE = "IDLE"
    DRIFT = "DRIFT"
    HIDE = "HIDE"
    PEEK = "PEEK"
    SCARE = "SCARE"
    TALK = "TALK"


def _load(name: str) -> pygame.Surface:
    path = ASSETS_GHOST / name
    return pygame.image.load(str(path)).convert_alpha()


class Ghost:
    def __init__(self, manifest_xy: tuple[float, float]) -> None:
        self.body = _load("body.png")
        self.blink = _load("eyes_closed.png")
        self.talk = _load("mouth_talk.png")
        self.peek_img = _load("peek.png")
        self.shadow_img = _load("ground_shadow.png")
        self.state = GhostState.ABSENT
        self.x, self.y = manifest_xy
        self.home = manifest_xy
        self.sx = 1.0
        self.sy = 1.0
        self.alpha = 0
        self.hidden_behind: str | None = None
        self._state_t = 0.0
        self._blink_in = random.uniform(2.0, 4.0)
        self._blink_left = 0.0
        self._from = manifest_xy
        self._to = manifest_xy
        self._drift_dur = 0.8
        self._lag = motion.LagShadow(0.1)
        self._scare_phase = 0
        self._hide_prop: str | None = None
        self._pending_hide = False
        self._peek_pos = manifest_xy

    @property
    def w(self) -> int:
        return self.body.get_width()

    @property
    def h(self) -> int:
        return self.body.get_height()

    def hitbox(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def contains(self, pos: tuple[int, int]) -> bool:
        if self.state in (GhostState.ABSENT, GhostState.HIDE):
            return False
        return self.hitbox().collidepoint(pos)

    def manifest(self) -> None:
        self.state = GhostState.MANIFEST
        self._state_t = 0.0
        self.alpha = 0
        self.x, self.y = self.home
        self._to = self.home
        self._pending_hide = False
        self.sx, self.sy = 1.15, 0.75

    def talk_now(self) -> None:
        if self.state is GhostState.ABSENT:
            return
        self.state = GhostState.TALK
        self._state_t = 0.0

    def drift_to(self, xy: tuple[float, float], duration: float = 0.9) -> None:
        if self.state is GhostState.ABSENT:
            return
        self._from = (self.x, self.y)
        self._to = xy
        self._drift_dur = duration
        self._state_t = 0.0
        self.state = GhostState.DRIFT
        self.hidden_behind = None
        self._pending_hide = False

    def hide_behind(self, prop_id: str, slot: tuple[float, float], peek: tuple[float, float]) -> None:
        if self.state is GhostState.ABSENT:
            return
        self._hide_prop = prop_id
        self._peek_pos = peek
        self.drift_to(slot, 0.7)
        self._pending_hide = True  # after drift_to, which clears this flag

    def scare(self) -> None:
        if self.state in (GhostState.ABSENT, GhostState.MANIFEST):
            return
        self.state = GhostState.SCARE
        self._state_t = 0.0
        self._scare_phase = 0
        self.hidden_behind = None
        self._from = (self.x, self.y)

    def update(self, dt: float, now: float) -> None:
        if self.state is GhostState.ABSENT:
            return
        self._state_t += dt
        self._blink_in -= dt
        if self._blink_in <= 0:
            self._blink_left = 0.12
            self._blink_in = random.uniform(2.0, 4.0)
        if self._blink_left > 0:
            self._blink_left -= dt

        if self.state is GhostState.MANIFEST:
            self._tick_manifest()
        elif self.state is GhostState.IDLE:
            self._tick_idle(now)
        elif self.state is GhostState.DRIFT:
            self._tick_drift(now)
        elif self.state is GhostState.HIDE:
            self._tick_hide(now)
        elif self.state is GhostState.PEEK:
            self._tick_peek(now)
        elif self.state is GhostState.SCARE:
            self._tick_scare(now)
        elif self.state is GhostState.TALK:
            self._tick_idle(now)
            if self._state_t > 2.4:
                self.state = GhostState.IDLE
                self._state_t = 0.0

        self._lag.push(now, self.x + self.w / 2, self.y)

    def _tick_manifest(self) -> None:
        t = motion.clamp(self._state_t / 1.2, 0.0, 1.0)
        self.alpha = int(255 * t)
        drop = motion.lerp(-18.0, 0.0, motion.ease_out_back(t))
        self.y = self.home[1] + drop
        self.x = self.home[0]
        if t < 0.75:
            self.sx, self.sy = 0.92, 1.12
        else:
            land = (t - 0.75) / 0.25
            self.sx = motion.lerp(1.2, 1.0, land)
            self.sy = motion.lerp(0.72, 1.0, land)
        if t >= 1.0:
            self.alpha = 255
            self.state = GhostState.IDLE
            self._state_t = 0.0

    def _tick_idle(self, now: float) -> None:
        self.sx, self.sy, hover = motion.breathe(now)
        self.y = self._idle_base_y() + hover
        self.alpha = 255

    def _idle_base_y(self) -> float:
        if self.state is GhostState.DRIFT:
            return self.y
        return self._to[1] if hasattr(self, "_to") else self.home[1]

    def _tick_drift(self, now: float) -> None:
        t = motion.clamp(self._state_t / self._drift_dur, 0.0, 1.0)
        k = motion.ease_out_back(t)
        self.x = motion.lerp(self._from[0], self._to[0], k)
        self.y = motion.lerp(self._from[1], self._to[1], k)
        self.sx, self.sy, _hover = motion.breathe(now)
        self.alpha = 255
        if t >= 1.0:
            self.x, self.y = self._to
            if getattr(self, "_pending_hide", False):
                self._pending_hide = False
                self.hidden_behind = self._hide_prop
                self.state = GhostState.HIDE
                self._state_t = 0.0
            else:
                self.state = GhostState.IDLE
                self._state_t = 0.0

    def _tick_hide(self, now: float) -> None:
        self.sx, self.sy, hover = motion.breathe(now)
        self.y = self._to[1] + hover * 0.4
        self.alpha = 220
        if self._state_t > 1.15:
            self.state = GhostState.PEEK
            self._state_t = 0.0
            self.hidden_behind = None
            self.x, self.y = self._peek_pos

    def _tick_peek(self, now: float) -> None:
        self.sx, self.sy, hover = motion.breathe(now)
        self.y = self._peek_pos[1] + hover * 0.5
        self.alpha = 255
        if self._state_t > 1.4:
            self.drift_to(self.home, 0.8)

    def _tick_scare(self, now: float) -> None:
        t = self._state_t
        if t < 0.16:
            back = t / 0.16
            self.x = self._from[0] - 14 * back
            self.sx, self.sy = 0.88, 1.12
        elif t < 0.42:
            lung = (t - 0.16) / 0.26
            self.x = motion.lerp(self._from[0] - 14, self._from[0] + 8, lung)
            self.sx = motion.lerp(0.88, 1.38, lung)
            self.sy = motion.lerp(1.12, 1.38, lung)
        elif t < 0.7:
            land = (t - 0.42) / 0.28
            self.sx = motion.lerp(1.38, 1.0, land)
            self.sy = motion.lerp(0.7, 1.0, land)
            self.x = motion.lerp(self._from[0] + 8, self._from[0], land)
        else:
            self.x, self.y = self._from
            self._to = self._from
            self.state = GhostState.IDLE
            self._state_t = 0.0

    def current_body(self) -> pygame.Surface:
        if self.state is GhostState.PEEK:
            return self.peek_img
        if self.state is GhostState.TALK and self._blink_left <= 0:
            return self.talk
        if self._blink_left > 0:
            return self.blink
        return self.body

    def draw_shadow(self, surf: pygame.Surface) -> None:
        if self.state in (GhostState.ABSENT, GhostState.HIDE, GhostState.PEEK):
            return
        img = self.shadow_img
        rise = max(0.0, (FLOOR_Y - (self.y + self.h)) / 80.0)
        sw = max(24, int(img.get_width() * (1.0 - 0.25 * rise) * self.sx))
        sh = max(8, int(img.get_height() * (1.0 - 0.2 * rise)))
        scaled = pygame.transform.scale(img, (sw, sh))
        scaled.set_alpha(int(self.alpha * 0.55))
        rect = scaled.get_rect(center=(int(self._lag.x), FLOOR_Y))
        surf.blit(scaled, rect)

    def draw(self, surf: pygame.Surface) -> None:
        if self.state is GhostState.ABSENT:
            return
        src = self.current_body()
        w = max(1, int(src.get_width() * self.sx))
        h = max(1, int(src.get_height() * self.sy))
        body = pygame.transform.scale(src, (w, h))
        body.set_alpha(self.alpha)
        # hem lag: a faint copy 3px lower
        hem = body.copy()
        hem.set_alpha(max(0, int(self.alpha * 0.28)))
        surf.blit(hem, (int(self.x), int(self.y) + 3))
        surf.blit(body, (int(self.x), int(self.y)))

"""Blob state machine. Opaque body, whole-pixel motion, clamped to the rug."""

from __future__ import annotations

import random
from enum import Enum

import pygame

from banshee.actors import motion
from banshee.config import ASSETS_GHOST, FLOOR_Y, ROOM_W


class GhostState(str, Enum):
    ABSENT = "ABSENT"
    MANIFEST = "MANIFEST"
    IDLE = "IDLE"
    DRIFT = "DRIFT"
    HIDE = "HIDE"
    PEEK = "PEEK"
    SCARE = "SCARE"
    TALK = "TALK"
    VANISH = "VANISH"


def _load(name: str) -> pygame.Surface:
    return pygame.image.load(str(ASSETS_GHOST / name)).convert_alpha()


class Ghost:
    def __init__(self, manifest_xy: tuple[float, float]) -> None:
        body = _load("body.png")
        bw, bh = int(body.get_width() * 1.35), int(body.get_height() * 1.35)
        self.body = pygame.transform.scale(body, (bw, bh))
        self.blink = pygame.transform.scale(_load("eyes_closed.png"), (bw, bh))
        self.talk = pygame.transform.scale(_load("mouth_talk.png"), (bw, bh))
        peek = _load("peek.png")
        ph = max(48, int(bh * 0.75))
        pw = max(24, int(peek.get_width() * (ph / max(1, peek.get_height()))))
        self.peek_img = pygame.transform.scale(peek, (pw, ph))
        self.shadow_img = _load("ground_shadow.png")
        self.state = GhostState.ABSENT
        self.x, self.y = float(manifest_xy[0]), float(manifest_xy[1])
        self.home = (float(manifest_xy[0]), float(manifest_xy[1]))
        self.hover = 0
        self.squash = 0
        self.alpha = 255
        self.hidden_behind: str | None = None
        self._state_t = 0.0
        self._blink_in = random.uniform(2.0, 4.0)
        self._blink_left = 0.0
        self._from = self.home
        self._to = self.home
        self._drift_dur = 0.8
        self._lag = motion.LagShadow(0.1)
        self._hide_prop: str | None = None
        self._pending_hide = False
        self._peek_pos = self.home
        self._vanish_to = self.home

    @property
    def w(self) -> int:
        return self.body.get_width()

    @property
    def h(self) -> int:
        return self.body.get_height()

    def hitbox(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y) + self.hover, self.w, self.h)

    def contains(self, pos: tuple[int, int]) -> bool:
        if self.state in (GhostState.ABSENT, GhostState.HIDE, GhostState.VANISH):
            return False
        return self.hitbox().collidepoint(pos)

    def busy(self) -> bool:
        return self.state in (
            GhostState.MANIFEST,
            GhostState.DRIFT,
            GhostState.HIDE,
            GhostState.PEEK,
            GhostState.SCARE,
            GhostState.VANISH,
        )

    def idle_for(self) -> float:
        if self.state is GhostState.IDLE:
            return self._state_t
        return 0.0

    def clamp_pos(self) -> None:
        self.x = motion.clamp(self.x, 6, ROOM_W - self.w - 6)
        self.y = motion.clamp(self.y, 24, FLOOR_Y - self.h + 12)

    def manifest(self, xy: tuple[float, float] | None = None) -> None:
        if xy:
            self.home = (float(xy[0]), float(xy[1]))
        self.x, self.y = self.home
        self._to = self.home
        self.state = GhostState.MANIFEST
        self._state_t = 0.0
        self.alpha = 255
        self._pending_hide = False
        self.hidden_behind = None
        self.clamp_pos()

    def talk_now(self) -> None:
        if self.state is GhostState.ABSENT:
            return
        self.state = GhostState.TALK
        self._state_t = 0.0
        self.alpha = 255

    def drift_to(self, xy: tuple[float, float], duration: float = 0.9) -> None:
        if self.state is GhostState.ABSENT:
            return
        self._from = (self.x, self.y)
        self._to = (float(xy[0]), float(xy[1]))
        self._drift_dur = max(0.35, duration)
        self._state_t = 0.0
        self.state = GhostState.DRIFT
        self.hidden_behind = None
        self._pending_hide = False
        self.alpha = 255

    def hide_behind(self, prop_id: str, slot: tuple[float, float], peek: tuple[float, float]) -> None:
        if self.state is GhostState.ABSENT:
            return
        self._hide_prop = prop_id
        self._peek_pos = peek
        self.drift_to(slot, 0.7)
        self._pending_hide = True

    def scare(self) -> None:
        if self.state in (GhostState.ABSENT, GhostState.MANIFEST, GhostState.VANISH):
            return
        self.state = GhostState.SCARE
        self._state_t = 0.0
        self.hidden_behind = None
        self._from = (self.x, self.y)
        self.alpha = 255

    def vanish_to(self, xy: tuple[float, float]) -> None:
        """Relocate without going invisible — a fast drift, not a fade."""
        if self.state is GhostState.ABSENT:
            return
        self.alpha = 255
        self.drift_to(xy, 0.45)

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
        self.hover, self.squash = motion.breathe_px(now)

        if self.state is not GhostState.ABSENT:
            self.alpha = 255
        if self.state is GhostState.MANIFEST:
            self._tick_manifest()
        elif self.state is GhostState.IDLE:
            pass
        elif self.state is GhostState.DRIFT:
            self._tick_drift()
        elif self.state is GhostState.HIDE:
            self._tick_hide()
        elif self.state is GhostState.PEEK:
            self._tick_peek()
        elif self.state is GhostState.SCARE:
            self._tick_scare()
        elif self.state is GhostState.TALK:
            if self._state_t > 6.0:
                self.state = GhostState.IDLE
                self._state_t = 0.0
        elif self.state is GhostState.VANISH:
            self.drift_to(self._vanish_to, 0.45)

        self.clamp_pos()
        self._lag.push(now, self.x + self.w / 2, self.y)

    def _tick_manifest(self) -> None:
        t = motion.clamp(self._state_t / 0.7, 0.0, 1.0)
        self.alpha = 255
        drop = motion.lerp(-12.0, 0.0, motion.ease_out_back(t))
        self.y = self.home[1] + drop
        self.x = self.home[0]
        self.squash = 5 if t > 0.7 else -2
        if t >= 1.0:
            self.state = GhostState.IDLE
            self._to = self.home
            self._state_t = 0.0

    def _tick_drift(self) -> None:
        t = motion.clamp(self._state_t / self._drift_dur, 0.0, 1.0)
        k = motion.ease_in_out_cubic(t)
        self.x = motion.lerp(self._from[0], self._to[0], k)
        self.y = motion.lerp(self._from[1], self._to[1], k)
        self.alpha = 255
        if t >= 1.0:
            self.x, self.y = self._to
            if self._pending_hide:
                self._pending_hide = False
                self.hidden_behind = self._hide_prop
                self.state = GhostState.HIDE
                self._state_t = 0.0
            else:
                self.state = GhostState.IDLE
                self._state_t = 0.0

    def _tick_hide(self) -> None:
        self.alpha = 255
        if self._state_t > 1.1:
            self.state = GhostState.PEEK
            self._state_t = 0.0
            self.hidden_behind = None
            self.x, self.y = self._peek_pos

    def _tick_peek(self) -> None:
        self.alpha = 255
        if self._state_t > 1.4:
            self.drift_to(self.home, 0.8)

    def _tick_scare(self) -> None:
        t = self._state_t
        self.alpha = 255
        if t < 0.16:
            self.x = self._from[0] - 12 * (t / 0.16)
            self.squash = 4
        elif t < 0.42:
            lung = (t - 0.16) / 0.26
            self.x = motion.lerp(self._from[0] - 12, self._from[0] + 6, lung)
            self.squash = -6
        elif t < 0.65:
            land = (t - 0.42) / 0.23
            self.x = motion.lerp(self._from[0] + 6, self._from[0], land)
            self.squash = 5
        else:
            self.x, self.y = self._from
            self._to = self._from
            self.state = GhostState.IDLE
            self._state_t = 0.0

    def _tick_vanish(self) -> None:
        self.alpha = 255
        self.drift_to(self._vanish_to, 0.45)

    def current_body(self) -> pygame.Surface:
        if self.state is GhostState.PEEK:
            return self.peek_img
        if self.state is GhostState.TALK and self._blink_left <= 0:
            return self.talk
        if self._blink_left > 0:
            return self.blink
        return self.body

    def draw_shadow(self, surf: pygame.Surface) -> None:
        if self.state in (GhostState.ABSENT, GhostState.HIDE):
            return
        img = self.shadow_img
        sw = max(28, int(img.get_width() * 1.2))
        sh = max(10, img.get_height())
        scaled = pygame.transform.scale(img, (sw, sh))
        scaled.set_alpha(140)
        rect = scaled.get_rect(center=(int(self._lag.x), FLOOR_Y))
        surf.blit(scaled, rect)

    def draw(self, surf: pygame.Surface) -> None:
        if self.state is GhostState.ABSENT:
            return
        src = self.current_body()
        if self.state is GhostState.PEEK:
            surf.blit(src, (int(self.x), int(self.y) + self.hover))
            return
        h = max(self.h - 2, self.h + min(3, self.squash))
        img = pygame.transform.scale(src, (self.w, h))
        y = int(self.y) + self.hover - max(0, self.squash)
        surf.blit(img, (int(self.x), y))

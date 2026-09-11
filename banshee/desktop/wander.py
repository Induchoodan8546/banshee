"""Always-visible house blob wandering the real desktop."""

from __future__ import annotations

import ctypes
import random
import time

import pygame

from banshee.actors.ghost import Ghost, GhostState
from banshee.desktop import monitor, possessor
from banshee.desktop.overlay import Overlay
from banshee.room.bubbles import Bubble
from banshee.room.voice import Voice
from banshee.system.banisher import Banisher

KEY_MAGENTA = (255, 0, 255)
WIN_W, WIN_H = 280, 240
PAD_X, PAD_Y = 70, 70

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_NOACTIVATE = 0x08000000
LWA_COLORKEY = 0x00000001
HWND_TOPMOST = -1
SWP_SHOWWINDOW = 0x0040
SWP_NOACTIVATE = 0x0010


def _hwnd_tools():
    user32 = ctypes.windll.user32
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        return user32, user32.GetWindowLongPtrW, user32.SetWindowLongPtrW
    return user32, user32.GetWindowLongW, user32.SetWindowLongW


def _style_window(hwnd: int) -> None:
    user32, get_long, set_long = _hwnd_tools()
    style = get_long(hwnd, GWL_EXSTYLE)
    set_long(
        hwnd,
        GWL_EXSTYLE,
        style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_NOACTIVATE,
    )
    user32.SetLayeredWindowAttributes(hwnd, 0x00FF00FF, 255, LWA_COLORKEY)


def _move_window(hwnd: int, x: int, y: int) -> None:
    ctypes.windll.user32.SetWindowPos(
        hwnd,
        HWND_TOPMOST,
        int(x),
        int(y),
        WIN_W,
        WIN_H,
        SWP_SHOWWINDOW | SWP_NOACTIVATE,
    )


class Wanderer:
    def __init__(self, voice: Voice, overlay: Overlay, killer: Banisher) -> None:
        self.voice = voice
        self.overlay = overlay
        self.killer = killer

    def run(self) -> None:
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("BANSHEE")
        vx, vy, sw, sh = possessor.virtual_screen()
        if sw <= 0 or sh <= 0:
            sw, sh = possessor._screen()
            vx, vy = 0, 0
        screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.NOFRAME)
        hwnd = pygame.display.get_wm_info().get("window")
        hwnd = int(hwnd) if hwnd else 0
        if hwnd:
            _style_window(hwnd)

        ghost = Ghost((vx + sw // 2, vy + sh // 3), scale=1.7)
        ghost.set_world(sw, sh, vy + sh - 48, origin_x=vx, origin_y=vy)
        start = (
            vx + random.randint(40, max(80, sw - WIN_W - 40)),
            vy + random.randint(40, max(80, sh - WIN_H - 80)),
        )
        ghost.manifest(start)
        bubble = Bubble()
        self.voice.ask(
            "you just took the desktop. say: now your system is mine. then one more short mean line.",
            activity="desktop",
            kind="ambient",
        )

        clock = pygame.time.Clock()
        t = 0.0
        next_drift = time.monotonic() + 0.5
        next_scare = time.monotonic() + 6.0
        next_talk = time.monotonic() + 5.0
        next_pin = 0.0
        follow = False

        while not self.killer.hit.is_set():
            dt = clock.tick(60) / 1000.0
            t += dt
            now = time.monotonic()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pass

            if self.voice.busy:
                live = self.voice.snapshot()
                if live:
                    bubble.set(live, final=False)
            line = self.voice.poll()
            if line:
                bubble.set(line, final=True)
                self.overlay.add("banshee", line)
                if ghost.state is not GhostState.ABSENT:
                    ghost.talk_now()
            bubble.tick(dt)

            if ghost.state is GhostState.ABSENT:
                ghost.manifest(self._perch(vx, vy, sw, sh))

            if (not ghost.busy()) and now >= next_drift:
                follow = random.random() < 0.22
                if follow:
                    mx, my = possessor._cursor()
                    target = (
                        max(vx + 16, min(vx + sw - WIN_W - 16, mx - 40)),
                        max(vy + 16, min(vy + sh - WIN_H - 80, my - 40)),
                    )
                else:
                    target = self._perch(vx, vy, sw, sh)
                ghost.drift_to(target, random.uniform(1.4, 2.8))
                next_drift = now + random.uniform(0.9, 1.8)
            if (not ghost.busy()) and now >= next_scare:
                ghost.scare()
                next_scare = now + random.uniform(7.0, 12.0)
            if now >= next_talk and not self.voice.talking_to_player() and not self.voice.pending_work():
                title = monitor.foreground_title() or "the desktop"
                self.voice.ask(
                    f"you are wandering the desktop. front window: {title}. "
                    "one short line. stay in character.",
                    activity=f"foreground: {title}",
                    kind="ambient",
                )
                next_talk = now + random.uniform(7.0, 11.0)

            ghost.update(dt, t)

            wx = int(ghost.x - PAD_X)
            wy = int(ghost.y - PAD_Y)
            wx = max(vx, min(vx + sw - WIN_W, wx))
            wy = max(vy, min(vy + sh - WIN_H, wy))
            if hwnd:
                _style_window(hwnd)
                _move_window(hwnd, wx, wy)
            if now >= next_pin:
                self.overlay.keep_front()
                next_pin = now + 0.2

            screen.fill(KEY_MAGENTA)
            sx, sy = ghost.x, ghost.y
            fy = ghost.floor_y
            ghost.x, ghost.y = PAD_X, PAD_Y
            ghost.floor_y = PAD_Y + ghost.h + 10
            ghost.draw_shadow(screen)
            ghost.draw(screen)
            bubble.draw(screen, ghost)
            ghost.x, ghost.y = sx, sy
            ghost.floor_y = fy
            pygame.display.flip()

        pygame.quit()

    def _perch(self, vx: int, vy: int, sw: int, sh: int) -> tuple[float, float]:
        chat_x = vx + sw - 300
        chat_y = vy + sh - 220
        for _ in range(12):
            x = random.uniform(vx + 8, vx + max(80, sw - WIN_W - 8))
            y = random.uniform(vy + 8, vy + max(80, sh - WIN_H - 48))
            if x + WIN_W < chat_x or y + WIN_H < chat_y:
                return (x, y)
        return (float(vx + 40), float(vy + 40))

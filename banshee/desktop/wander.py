"""Small always-on-top blob that wanders the desktop like in the house."""

from __future__ import annotations

import ctypes
import random
import time

import pygame

from banshee.actors.ghost import Ghost, GhostState
from banshee.desktop import possessor
from banshee.room.bubbles import Bubble
from banshee.room.voice import Voice
from banshee.system.banisher import Banisher

KEY_MAGENTA = (255, 0, 255)
WIN_W, WIN_H = 360, 300
PAD_X, PAD_Y = 90, 90

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
LWA_COLORKEY = 0x00000001
HWND_TOPMOST = -1
SWP_SHOWWINDOW = 0x0040


def _hwnd_tools():
    user32 = ctypes.windll.user32
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        return user32, user32.GetWindowLongPtrW, user32.SetWindowLongPtrW
    return user32, user32.GetWindowLongW, user32.SetWindowLongW


def _style_window(hwnd: int) -> None:
    user32, get_long, set_long = _hwnd_tools()
    style = get_long(hwnd, GWL_EXSTYLE)
    set_long(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST)
    user32.SetLayeredWindowAttributes(hwnd, 0x00FF00FF, 255, LWA_COLORKEY)


def _move_window(hwnd: int, x: int, y: int) -> None:
    ctypes.windll.user32.SetWindowPos(
        hwnd, HWND_TOPMOST, int(x), int(y), WIN_W, WIN_H, SWP_SHOWWINDOW
    )


class Wanderer:
    def __init__(self, voice: Voice, killer: Banisher) -> None:
        self.voice = voice
        self.killer = killer

    def run(self) -> None:
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("BANSHEE")
        sw, sh = possessor._screen()
        screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.NOFRAME)
        hwnd = pygame.display.get_wm_info().get("window")
        if hwnd:
            hwnd = int(hwnd)
            _style_window(hwnd)
        else:
            hwnd = 0

        ghost = Ghost((sw // 2, sh // 3), scale=1.6)
        ghost.set_world(max(200, sw - 40), sh, sh - 48)
        start = (random.randint(80, max(120, sw - 400)), random.randint(80, max(120, sh - 320)))
        ghost.manifest(start)
        bubble = Bubble()
        self.voice.ask(
            "you climbed onto the real desktop. one short line. you are a blob ghost.",
            activity="desktop wander",
            kind="ambient",
        )

        clock = pygame.time.Clock()
        t = 0.0
        next_drift = time.monotonic() + 1.4

        while not self.killer.hit.is_set():
            dt = clock.tick(60) / 1000.0
            t += dt
            now = time.monotonic()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.killer.hit.set()

            if self.voice.busy:
                live = self.voice.snapshot()
                if live:
                    bubble.set(live, final=False)
            line = self.voice.poll()
            if line:
                bubble.set(line, final=True)
                if ghost.state is not GhostState.ABSENT:
                    ghost.talk_now()
            bubble.tick(dt)

            if ghost.idle_for() > 1.15 and now >= next_drift:
                gx = random.uniform(24, max(40, sw - WIN_W - 24))
                gy = random.uniform(24, max(40, sh - WIN_H - 48))
                ghost.drift_to((gx, gy), random.uniform(1.1, 2.2))
                next_drift = now + random.uniform(1.6, 3.2)

            ghost.update(dt, t)

            wx = int(ghost.x - PAD_X)
            wy = int(ghost.y - PAD_Y)
            wx = max(0, min(sw - WIN_W, wx))
            wy = max(0, min(sh - WIN_H, wy))
            if hwnd:
                _move_window(hwnd, wx, wy)

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

            if possessor.cursor_in_panic_corner():
                self.killer.hit.set()
                break

        pygame.quit()

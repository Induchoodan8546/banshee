"""The one pygame bedroom. --house-only lives here."""

from __future__ import annotations

import random
import sys

import pygame

from banshee.actors.ghost import Ghost, GhostState
from banshee.actors.shade import Shade, ShadeKind
from banshee.config import ASSETS_ROOM, FPS, WINDOW_H, WINDOW_W
from banshee.room.layers import blit_world
from banshee.room.props import Props
from banshee.room.whispers import Whispers
from banshee.state import Clock, Haunt


def run_house() -> int:
    pygame.init()
    pygame.display.set_caption("BANSHEE")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock = pygame.time.Clock()
    bg = pygame.image.load(str(ASSETS_ROOM / "bg.png")).convert()
    if bg.get_size() != (WINDOW_W, WINDOW_H):
        bg = pygame.transform.scale(bg, (WINDOW_W, WINDOW_H))

    props = Props()
    ghost = Ghost(props.manifest)
    shade = Shade()
    whispers = Whispers()
    haunt = Clock()

    clicks = 0
    fired: set[str] = set()
    running = True
    now = 0.0

    def fire(name: str) -> bool:
        if name in fired:
            return False
        fired.add(name)
        return True

    def start_manifest() -> None:
        haunt.phase = Haunt.MANIFEST
        haunt.skip_to(38.0)
        ghost.manifest()
        fire("manifest")
        fire("t38")

    while running:
        dt = clock.tick(FPS) / 1000.0
        now += dt
        haunt.tick(dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                pid = props.hit(event.pos)
                props.hover_chair = pid == "chair"
                if pid or ghost.contains(event.pos):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if ghost.contains(event.pos) and haunt.t >= 38.0:
                    ghost.scare()
                    continue
                pid = props.hit(event.pos)
                if not pid:
                    continue
                if haunt.t < 38.0:
                    clicks += 1
                    if clicks >= 3:
                        start_manifest()
                else:
                    perch = props.perches.get(pid, props.manifest)
                    if pid in ("wardrobe", "chest"):
                        ghost.hide_behind(pid, props.hide_slot(pid), props.peek_slot(pid))
                    else:
                        gx = perch[0] - ghost.w / 2
                        gy = perch[1]
                        ghost.drift_to((gx, gy))

        t = haunt.t
        if t >= 4.0 and fire("w1"):
            whispers.set("dont close the window")
        if t >= 8.0 and fire("slide"):
            shade.spawn(ShadeKind.WALL_SLIDE)
        if t >= 14.0 and fire("chest"):
            props.tap_chest()
        if t >= 22.0 and fire("w2"):
            whispers.set("someone is in the wardrobe")
        if t >= 26.0 and fire("crack"):
            wr = props.items["wardrobe"]
            shade.spawn(ShadeKind.DOOR_CRACK, {"x": wr.x + wr.w - 40, "y": wr.y + 80})
        if t >= 32.0 and fire("false"):
            ch = props.items["chair"]
            shade.spawn(ShadeKind.FALSE_GHOST, {"x": ch.x - 10, "y": ch.y + 20})
        if t >= 38.0 and fire("t38"):
            start_manifest()
        if t >= 40.0 and fire("line"):
            whispers.set("you looked too long")
            ghost.talk_now()

        if (
            haunt.t >= 41.0
            and ghost.state is GhostState.IDLE
            and ghost._state_t > 3.0
        ):
            name = random.choice(list(props.perches))
            px, py = props.perches[name]
            ghost.drift_to((px - ghost.w / 2, py), 1.05)

        props.update(dt, now)
        shade.update(dt)
        ghost.update(dt, now)

        blit_world(screen, bg, shade, props, ghost)
        whispers.draw(screen)
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(run_house())

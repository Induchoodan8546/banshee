"""The one pygame bedroom. --house-only. No TV bezel."""

from __future__ import annotations

import sys

import pygame

from banshee.actors.ghost import Ghost
from banshee.actors.shade import Shade
from banshee.config import ASSETS_ROOM, FPS, WINDOW_H, WINDOW_W
from banshee.room.director import Director
from banshee.room.layers import blit_world
from banshee.room.props import Props
from banshee.room.whispers import Whispers


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
    director = Director(props, ghost, shade, whispers)

    running = True
    now = 0.0

    while running:
        dt = clock.tick(FPS) / 1000.0
        now += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                if props.dragging:
                    props.drag_to(event.pos)
                pid = props.hit(event.pos)
                if pid or ghost.contains(event.pos):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                props.end_drag()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if ghost.contains(event.pos):
                    ghost.scare()
                    director.note_interact("poke")
                    continue
                pid = props.hit(event.pos)
                if not pid:
                    continue
                if props.begin_drag(pid, event.pos):
                    director.note_interact("drag")
                    continue
                kind = props.toggle(pid)
                director.note_interact(kind)

        director.update(dt)
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

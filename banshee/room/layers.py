"""Draw order: bg → shadows → furniture → ghost shadow → ghost."""

from __future__ import annotations

import pygame

from banshee.actors.ghost import Ghost, GhostState
from banshee.actors.shade import Shade
from banshee.room.props import Props


def blit_world(
    screen: pygame.Surface,
    bg: pygame.Surface,
    shade: Shade,
    props: Props,
    ghost: Ghost,
) -> None:
    screen.blit(bg, (0, 0))
    shade.draw(screen)
    hiding = ghost.state is GhostState.HIDE
    if hiding:
        ghost.draw(screen)
    props.draw(screen)
    ghost.draw_shadow(screen)
    if not hiding:
        ghost.draw(screen)

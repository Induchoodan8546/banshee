"""Scripted caption-bar lines. Not the LLM."""

from __future__ import annotations

import pygame

from banshee.config import CAPTION_RECT

FONT_COLOR = (236, 214, 168)


class Whispers:
    def __init__(self) -> None:
        self.text = ""
        self.font = pygame.font.SysFont("consolas", 22)

    def set(self, text: str) -> None:
        self.text = text

    def draw(self, surf: pygame.Surface) -> None:
        if not self.text:
            return
        x0, y0, x1, y1 = CAPTION_RECT
        label = self.font.render(self.text, True, FONT_COLOR)
        rect = label.get_rect(center=((x0 + x1) // 2, (y0 + y1) // 2))
        surf.blit(label, rect)

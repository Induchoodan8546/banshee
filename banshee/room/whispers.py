"""In-room subtitles. No TV caption bar."""

from __future__ import annotations

import pygame

from banshee.config import CAPTION_Y, WINDOW_W

FONT_COLOR = (236, 214, 168)
DIM = (18, 12, 28)


class Whispers:
    def __init__(self) -> None:
        self.text = ""
        self.font = pygame.font.SysFont("consolas", 20)

    def set(self, text: str) -> None:
        self.text = text

    def draw(self, surf: pygame.Surface) -> None:
        if not self.text:
            return
        bar = pygame.Surface((WINDOW_W, 32), pygame.SRCALPHA)
        bar.fill((18, 12, 28, 150))
        surf.blit(bar, (0, CAPTION_Y - 6))
        label = self.font.render(self.text, True, FONT_COLOR)
        rect = label.get_rect(center=(WINDOW_W // 2, CAPTION_Y + 8))
        surf.blit(label, rect)

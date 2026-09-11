"""Speech bubble above the ghost. LLM text only after she appears."""

from __future__ import annotations

import pygame

from banshee.actors.ghost import Ghost
from banshee.config import ROOM_H, ROOM_W

INK = (28, 18, 42)
FILL = (248, 240, 255)
LILAC = (186, 160, 214)


class Bubble:
    def __init__(self) -> None:
        self.text = ""
        self.font = pygame.font.SysFont("consolas", 16)

    def set(self, text: str) -> None:
        self.text = text.replace("\n", " ").strip()

    def draw(self, surf: pygame.Surface, ghost: Ghost) -> None:
        if not self.text:
            return
        words = self.text.split()
        lines: list[str] = []
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.font.size(trial)[0] > 280 and cur:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        if cur:
            lines.append(cur)
        lines = lines[:4]
        if not lines:
            return
        pads = 8
        widths = [self.font.size(line)[0] for line in lines]
        bw = min(300, max(widths) + pads * 2)
        bh = len(lines) * 18 + pads * 2
        x = int(ghost.x + ghost.w / 2 - bw / 2)
        y = int(ghost.y) - bh - 10
        x = max(6, min(ROOM_W - bw - 6, x))
        y = max(4, min(ROOM_H - bh - 40, y))
        box = pygame.Rect(x, y, bw, bh)
        pygame.draw.rect(surf, FILL, box, border_radius=6)
        pygame.draw.rect(surf, LILAC, box, 2, border_radius=6)
        tip = [
            (int(ghost.x + ghost.w / 2) - 6, y + bh),
            (int(ghost.x + ghost.w / 2) + 6, y + bh),
            (int(ghost.x + ghost.w / 2), y + bh + 8),
        ]
        pygame.draw.polygon(surf, FILL, tip)
        for i, line in enumerate(lines):
            label = self.font.render(line, True, INK)
            surf.blit(label, (x + pads, y + pads + i * 18))

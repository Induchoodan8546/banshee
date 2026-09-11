"""Speech bubble above the ghost. Wraps, then plays long replies beat by beat."""

from __future__ import annotations

import re

import pygame

from banshee.actors.ghost import Ghost
from banshee.config import ROOM_H, ROOM_W

INK = (28, 18, 42)
FILL = (248, 240, 255)
LILAC = (186, 160, 214)
WRAP_PX = 240
MAX_LINES = 2


def wrap_words(font: pygame.font.Font, text: str, max_px: int) -> list[str]:
    words: list[str] = []
    for raw in text.split():
        words.extend(_break_long(font, raw, max_px))
    if not words:
        return []
    lines: list[str] = []
    cur = words[0]
    for word in words[1:]:
        trial = f"{cur} {word}"
        if font.size(trial)[0] > max_px:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines.append(cur)
    return lines


def _break_long(font: pygame.font.Font, word: str, max_px: int) -> list[str]:
    if font.size(word)[0] <= max_px:
        return [word]
    parts: list[str] = []
    buf = ""
    for ch in word:
        if buf and font.size(buf + ch)[0] > max_px:
            parts.append(buf)
            buf = ch
        else:
            buf += ch
    if buf:
        parts.append(buf)
    return parts


def split_beats(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    bits = re.split(r"(?<=[.!?])\s+", text)
    bits = [b.strip() for b in bits if b.strip()]
    if not bits:
        return [text]
    beats: list[str] = []
    for bit in bits:
        if len(bit) <= 80:
            beats.append(bit)
            continue
        chunks = re.split(r"(?<=,)\s+", bit)
        buf = ""
        for chunk in chunks:
            trial = (buf + " " + chunk).strip()
            if buf and len(trial) > 80:
                beats.append(buf)
                buf = chunk
            else:
                buf = trial
        if buf:
            beats.append(buf)
    return beats or [text]


def hold_for(text: str) -> float:
    return max(3.8, min(8.5, 1.6 + len(text) * 0.07))


class Bubble:
    def __init__(self) -> None:
        self.text = ""
        self._hold = 0.0
        self._queue: list[str] = []
        self.font = pygame.font.SysFont("consolas", 16)

    def set(self, text: str, *, final: bool = False) -> None:
        text = text.replace("\n", " ").strip()
        if not text or text == "...":
            return
        if not final:
            self.text = text
            self._queue = []
            self._hold = max(self._hold, 2.5)
            return
        beats = split_beats(text)
        if not beats:
            return
        self.text = beats[0]
        self._queue = beats[1:]
        self._hold = hold_for(self.text)

    def tick(self, dt: float) -> None:
        if self._hold > 0:
            self._hold -= dt
            return
        if self._queue:
            self.text = self._queue.pop(0)
            self._hold = hold_for(self.text)

    def blocking(self) -> bool:
        return self._hold > 0.4 or bool(self._queue)

    def draw(self, surf: pygame.Surface, ghost: Ghost) -> None:
        if not self.text or (self._hold <= 0 and not self._queue):
            return
        lines = wrap_words(self.font, self.text, WRAP_PX)[:MAX_LINES]
        if not lines:
            return
        pads = 8
        widths = [self.font.size(line)[0] for line in lines]
        bw = min(WRAP_PX + pads * 2, max(widths) + pads * 2)
        bh = len(lines) * 18 + pads * 2
        x = int(ghost.x + ghost.w / 2 - bw / 2)
        y = int(ghost.y) - bh - 12
        x = max(6, min(ROOM_W - bw - 6, x))
        y = max(4, min(ROOM_H - bh - 40, y))
        box = pygame.Rect(x, y, bw, bh)
        pygame.draw.rect(surf, FILL, box, border_radius=6)
        pygame.draw.rect(surf, LILAC, box, 2, border_radius=6)
        tip_x = max(box.left + 10, min(box.right - 10, int(ghost.x + ghost.w / 2)))
        pygame.draw.polygon(
            surf,
            FILL,
            [(tip_x - 6, y + bh), (tip_x + 6, y + bh), (tip_x, y + bh + 8)],
        )
        for i, line in enumerate(lines):
            label = self.font.render(line, True, INK)
            surf.blit(label, (x + pads, y + pads + i * 18))

"""Chat dock under the bedroom. Type to talk to her."""

from __future__ import annotations

import pygame

from banshee.config import CHAT_DOCK_H, ROOM_H, WINDOW_W
from banshee.room.bubbles import wrap_words

BG = (22, 14, 36)
LINE = (90, 62, 120)
CREAM = (236, 214, 168)
LILAC = (198, 170, 230)
MUTED = (140, 120, 160)
CARET = (248, 240, 255)


class ChatDock:
    def __init__(self) -> None:
        self.log: list[tuple[str, str]] = []
        self.draft = ""
        self.focus = False
        self.enabled = False
        self.font = pygame.font.SysFont("consolas", 16)
        self.small = pygame.font.SysFont("consolas", 14)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(0, ROOM_H, WINDOW_W, CHAT_DOCK_H)

    def add(self, who: str, text: str) -> None:
        text = text.replace("\n", " ").strip()
        if not text:
            return
        self.log.append((who, text))
        self.log = self.log[-5:]
        if who == "banshee":
            from banshee.voice_io import maybe_speak

            maybe_speak(text)

    def _btn_rects(self) -> dict[str, pygame.Rect]:
        y = ROOM_H + 4
        return {
            "text": pygame.Rect(WINDOW_W - 210, y, 52, 18),
            "audio": pygame.Rect(WINDOW_W - 154, y, 56, 18),
            "speak": pygame.Rect(WINDOW_W - 94, y, 56, 18),
        }

    def click_button(self, pos: tuple[int, int]) -> str | None:
        for name, rect in self._btn_rects().items():
            if rect.collidepoint(pos):
                return name
        return None

    def contains(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

    def handle_key(self, event: pygame.event.Event) -> str | None:
        if not self.enabled:
            return None
        if event.key == pygame.K_RETURN:
            line = self.draft.strip()
            self.draft = ""
            return line or None
        if event.key == pygame.K_BACKSPACE:
            self.draft = self.draft[:-1]
            return None
        if event.key == pygame.K_ESCAPE:
            if self.draft:
                self.draft = ""
                return ""
            return None
        return None

    def handle_text(self, text: str) -> None:
        if not self.enabled:
            return
        if text and text.isprintable() and text not in "\r\n":
            self.draft += text
            if len(self.draft) > 140:
                self.draft = self.draft[:140]

    def draw(self, surf: pygame.Surface, now: float) -> None:
        dock = self.rect
        pygame.draw.rect(surf, BG, dock)
        pygame.draw.line(surf, LINE, (0, ROOM_H), (WINDOW_W, ROOM_H), 2)
        for name, rect in self._btn_rects().items():
            pygame.draw.rect(surf, (40, 24, 64), rect, border_radius=3)
            surf.blit(self.small.render(name, True, CREAM), (rect.x + 6, rect.y + 1))
        y = ROOM_H + 8
        if not self.log:
            hint = "she will talk when she arrives" if not self.enabled else "say something. she is listening."
            surf.blit(self.small.render(hint, True, MUTED), (12, y))
            y += 18
        for who, text in self.log:
            color = CREAM if who == "you" else LILAC
            prefix = "you: " if who == "you" else "banshee: "
            wrapped = wrap_words(self.small, prefix + text, WINDOW_W - 28)
            for i, line in enumerate(wrapped[:2]):
                surf.blit(self.small.render(line, True, color), (12, y))
                y += 16
            y += 2
        field = pygame.Rect(10, ROOM_H + CHAT_DOCK_H - 36, WINDOW_W - 20, 26)
        pygame.draw.rect(surf, (12, 8, 22), field, border_radius=4)
        pygame.draw.rect(surf, LINE if self.focus else (50, 36, 70), field, 1, border_radius=4)
        shown = self.draft if self.draft or self.focus else "type here..."
        color = CREAM if self.draft or self.focus else MUTED
        surf.blit(self.font.render(shown[:70], True, color), (field.x + 8, field.y + 4))
        if self.focus and self.enabled and int(now * 2) % 2 == 0:
            cx = field.x + 8 + self.font.size(self.draft[:70])[0]
            pygame.draw.line(surf, CARET, (cx, field.y + 4), (cx, field.y + 20), 1)

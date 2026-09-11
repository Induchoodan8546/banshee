"""Bedroom + chat dock. Ghost talks through the local model."""

from __future__ import annotations

import random
import sys

import pygame

from banshee.actors.ghost import Ghost, GhostState
from banshee.actors.shade import Shade
from banshee.config import ASSETS_ROOM, FPS, KILL_SPELL, ROOM_H, WINDOW_H, WINDOW_W
from banshee.room.bubbles import Bubble
from banshee.room.chat import ChatDock
from banshee.room.director import Act, Director
from banshee.room.layers import blit_world
from banshee.room.props import Props
from banshee.room.voice import Voice
from banshee.room.whispers import Whispers


def run_house() -> int:
    pygame.init()
    pygame.display.set_caption("BANSHEE")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock = pygame.time.Clock()
    bg = pygame.image.load(str(ASSETS_ROOM / "bg.png")).convert()
    if bg.get_size() != (WINDOW_W, ROOM_H):
        bg = pygame.transform.scale(bg, (WINDOW_W, ROOM_H))

    props = Props()
    ghost = Ghost(props.manifest)
    shade = Shade()
    whispers = Whispers()
    voice = Voice()
    bubble = Bubble()
    chat = ChatDock()
    director = Director(props, ghost, shade, whispers, voice)

    running = True
    now = 0.0
    pygame.key.stop_text_input()

    def in_room(pos: tuple[int, int]) -> bool:
        return pos[1] < ROOM_H

    while running:
        dt = clock.tick(FPS) / 1000.0
        now += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if chat.contains(event.pos):
                    chat.focus = True
                    pygame.key.start_text_input()
                    continue
                chat.focus = False
                pygame.key.stop_text_input()
                if not in_room(event.pos):
                    continue
                if ghost.contains(event.pos) and director.here():
                    if random.random() < 0.35:
                        ghost.drift_to(director._random_perch(), 0.6)
                    else:
                        ghost.scare()
                    director.note_interact("poke", "poked the ghost")
                    continue
                pid = props.hit(event.pos)
                if not pid:
                    continue
                if props.begin_drag(pid, event.pos):
                    director.note_interact("drag", f"dragged the {pid}")
                    continue
                kind = props.toggle(pid)
                director.note_interact(kind, f"{kind} the {pid}")
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                props.end_drag()
            elif event.type == pygame.MOUSEMOTION:
                if props.dragging:
                    props.drag_to(event.pos)
                pid = props.hit(event.pos) if in_room(event.pos) else None
                if pid or ghost.contains(event.pos) or chat.contains(event.pos):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            elif event.type == pygame.TEXTINPUT and chat.focus:
                chat.handle_text(event.text)
            elif event.type == pygame.KEYDOWN:
                if chat.focus and chat.enabled:
                    sent = chat.handle_key(event)
                    if sent:
                        chat.add("you", sent)
                        if sent.lower() == KILL_SPELL:
                            voice.ask(
                                "the human said bazinga. short goodbye. then stop haunting.",
                                activity="bazinga",
                            )
                        else:
                            voice.ask(
                                f'the human said: "{sent}". answer in 1-3 short sentences.',
                                activity=f"player said: {sent}",
                            )
                    elif sent == "":
                        pass
                    elif event.key == pygame.K_ESCAPE and not chat.draft:
                        running = False
                    continue
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN and director.here():
                    chat.focus = True
                    pygame.key.start_text_input()

        line = voice.poll()
        if line:
            bubble.set(line)
            chat.add("banshee", line)
            if ghost.state is not GhostState.ABSENT:
                ghost.talk_now()

        if director.act is Act.HAUNT and not chat.enabled:
            chat.enabled = True

        with voice._lock:
            if voice.bubble:
                bubble.set(voice.bubble)

        director.update(dt)
        props.update(dt, now)
        shade.update(dt)
        ghost.update(dt, now)

        blit_world(screen, bg, shade, props, ghost)
        whispers.draw(screen)
        if director.here():
            bubble.draw(screen, ghost)
        chat.draw(screen, now)
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(run_house())

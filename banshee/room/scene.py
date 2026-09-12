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


def run_house(*, possess_on_close: bool = False) -> str:
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
    director = Director(props, ghost, shade, whispers, voice, bubble)

    running = True
    outcome = "quit"
    now = 0.0
    pygame.key.stop_text_input()

    def request_close() -> None:
        nonlocal running, outcome
        running = False
        if possess_on_close:
            outcome = "possess"

    def in_room(pos: tuple[int, int]) -> bool:
        return pos[1] < ROOM_H

    while running:
        dt = clock.tick(FPS) / 1000.0
        now += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                request_close()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if chat.contains(event.pos):
                    btn = chat.click_button(event.pos)
                    if btn == "text":
                        from banshee.voice_io import set_audio_mode

                        set_audio_mode(False)
                        chat.add("banshee", "fine. text only.")
                    elif btn == "audio":
                        from banshee.voice_io import set_audio_mode

                        set_audio_mode(True)
                        chat.add("banshee", "i'll hiss in your speakers.")
                    elif btn == "speak":
                        import threading

                        def _mic() -> None:
                            from banshee.voice_io import listen_once

                            heard = listen_once()
                            if heard:
                                chat.add("you", heard)
                                voice.ask(heard, activity="player", kind="player")
                            else:
                                chat.add("banshee", "i didn't catch that.")

                        threading.Thread(target=_mic, daemon=True).start()
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
                                "bazinga",
                                activity="bazinga",
                                kind="player",
                            )
                        else:
                            voice.ask(sent, activity="player", kind="player")
                    elif sent == "":
                        pass
                    elif event.key == pygame.K_ESCAPE and not chat.draft:
                        request_close()
                    continue
                if event.key == pygame.K_ESCAPE:
                    request_close()
                elif event.key == pygame.K_RETURN and director.here():
                    chat.focus = True
                    pygame.key.start_text_input()

        if voice.busy:
            live = voice.snapshot()
            if live:
                bubble.set(live, final=False)
        line = voice.poll()
        if line:
            bubble.set(line, final=True)
            chat.add("banshee", line)
            if ghost.state is not GhostState.ABSENT:
                ghost.talk_now()

        if director.here() and not chat.enabled:
            chat.enabled = True

        bubble.tick(dt)
        director.update(dt)
        props.update(dt, now)
        shade.update(dt)
        ghost.update(dt, now)

        blit_world(screen, bg, shade, props, ghost)
        whispers.draw(screen)
        if ghost.state is not GhostState.ABSENT:
            bubble.draw(screen, ghost)
        chat.draw(screen, now)
        pygame.display.flip()

    pygame.quit()
    return outcome


if __name__ == "__main__":
    sys.exit(0 if run_house() == "quit" else 0)

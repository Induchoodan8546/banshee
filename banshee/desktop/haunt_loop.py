"""Possess: notepad, wallpaper, then tk mascot + chat (always on top)."""

from __future__ import annotations

import random
import threading
import time

from banshee import config
from banshee.desktop import possessor
from banshee.desktop.overlay import Overlay
from banshee.room.voice import Voice
from banshee.system.banisher import Banisher


def _mischief(stop: threading.Event, overlay: Overlay) -> None:
    time.sleep(2.2)
    while not stop.is_set():
        roll = random.random()
        if roll < 0.42:
            possessor.possess_cursor_burst(
                random.uniform(2.0, 2.8),
                overlay=overlay,
                on_end=overlay.release_input,
            )
        elif roll < 0.78:
            name = random.choice(["notepad", "calculator", "paint"])
            possessor.open_app(name, note_index=random.randint(0, 4))
            overlay.keep_front()
        else:
            possessor.open_search()
            overlay.keep_front()
        waited = 0.0
        gap = random.uniform(5.0, 6.5)
        while waited < gap and not stop.is_set():
            time.sleep(0.1)
            waited += 0.1


def run_possession() -> int:
    print("", flush=True)
    print("she left the drawing.", flush=True)
    print("type  bazinga  in the bottom-right box to banish her.", flush=True)
    print("", flush=True)

    killer = Banisher()
    killer.start()
    voice = Voice()
    overlay = Overlay()
    overlay.attach(voice, killer)

    possessor.write_note()
    possessor.open_app("notepad", note_index=0)
    time.sleep(0.6)
    possessor.set_wallpaper()

    mischief = threading.Thread(target=_mischief, args=(killer.hit, overlay), daemon=True)
    mischief.start()

    voice.ask(
        "you just took the desktop. say now your system is mine. one more short line.",
        activity="desktop",
        kind="ambient",
    )

    try:
        overlay.run()
    except KeyboardInterrupt:
        print("[banshee] interrupted", flush=True)
        killer.hit.set()
    finally:
        possessor.stop_cursor_grab()
        overlay.stop()
        killer.stop()
        possessor.restore_wallpaper()
        config.DATA.mkdir(parents=True, exist_ok=True)
        config.BANISHED_FLAG.write_text("1", encoding="utf-8")
        print("banished. wallpaper restored.", flush=True)
    return 0

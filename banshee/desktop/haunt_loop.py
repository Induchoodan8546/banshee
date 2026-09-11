"""Timed desktop mischief after the room window closes."""

from __future__ import annotations

import time

from banshee import config
from banshee.desktop import possessor
from banshee.system.banisher import Banisher


def run_possession() -> int:
    print("", flush=True)
    print("she left the drawing.", flush=True)
    if config.SAFE:
        print("--safe: no real desktop changes.", flush=True)
    print("type  bazinga  anywhere to banish her.", flush=True)
    print("", flush=True)

    killer = Banisher()
    killer.start()

    possessor.write_note()
    time.sleep(0.25)
    possessor.set_wallpaper()
    time.sleep(0.2)
    possessor.open_app("notepad")
    time.sleep(0.35)
    possessor.open_app("calculator")
    time.sleep(0.25)
    possessor.open_app("paint")
    possessor.start_cursor_grab()

    panic = 0.0
    try:
        while not killer.hit.is_set():
            time.sleep(0.05)
            if possessor.cursor_in_panic_corner():
                panic += 0.05
                if panic >= 0.45:
                    print("[banshee] panic corner — leaving", flush=True)
                    break
            else:
                panic = 0.0
    except KeyboardInterrupt:
        print("[banshee] interrupted", flush=True)
    finally:
        possessor.stop_cursor_grab()
        killer.stop()
        possessor.restore_wallpaper()
        print("banished. wallpaper restored.", flush=True)
    return 0

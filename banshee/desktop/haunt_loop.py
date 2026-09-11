"""Tension first. Strike when they try to use the machine."""

from __future__ import annotations

import random
import time

from banshee import config
from banshee.desktop import possessor
from banshee.desktop.overlay import Overlay
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

    overlay = Overlay()
    overlay.start()
    watch = possessor.ActivityWatch()
    watch.start()

    possessor.write_note()
    time.sleep(1.2)
    possessor.set_wallpaper()
    overlay.set_line("dont close the window. too late.")

    pool = ["notepad", "calculator", "paint"]
    first = random.choice(pool)
    rest = [a for a in pool if a != first]
    random.shuffle(rest)
    apps = [first] + rest

    stage = 0
    marked = 0
    grab_at = None
    next_app = 0
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

            if stage == 0 and watch.events >= 1:
                name = apps[next_app] if next_app < len(apps) else "notepad"
                possessor.open_app(name)
                overlay.set_line("you looked. that's how we get in.")
                next_app += 1
                stage = 1
                marked = watch.events
                grab_at = time.monotonic() + 1.8
            elif stage == 1 and (
                watch.events >= marked + 1 or (grab_at and time.monotonic() >= grab_at)
            ):
                possessor.start_cursor_grab()
                overlay.set_line("your cursor asked me for directions.")
                stage = 2
                marked = watch.events
            elif stage == 2 and watch.events >= marked + 4 and next_app < len(apps):
                possessor.open_app(apps[next_app])
                next_app += 1
                marked = watch.events
    except KeyboardInterrupt:
        print("[banshee] interrupted", flush=True)
    finally:
        possessor.stop_cursor_grab()
        watch.stop()
        overlay.stop()
        killer.stop()
        possessor.restore_wallpaper()
        config.DATA.mkdir(parents=True, exist_ok=True)
        config.BANISHED_FLAG.write_text("1", encoding="utf-8")
        print("banished. wallpaper restored.", flush=True)
    return 0

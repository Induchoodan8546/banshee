"""Tension first. Strike when they try to use the machine. Keep striking."""

from __future__ import annotations

import random
import time

from banshee import config
from banshee.desktop import possessor
from banshee.desktop.overlay import Overlay
from banshee.system.banisher import Banisher

LINES = [
    "you looked. that's how we get in.",
    "your cursor asked me for directions.",
    "i live in notepad now.",
    "closing the x is cute.",
    "still here.",
]


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
    time.sleep(2.4)
    possessor.set_wallpaper()
    overlay.set_line("dont close the window. too late.")
    time.sleep(1.6)
    watch.reset()

    pool = ["notepad", "calculator", "paint"]
    first = random.choice(pool)
    rest = [a for a in pool if a != first]
    random.shuffle(rest)
    apps = [first] + rest

    stage = 0
    marked = 0
    grab_after = 0.0
    next_app = 0
    note_n = 0
    next_ghost_app = 0.0
    panic = 0.0

    def spawn_app() -> None:
        nonlocal next_app, note_n
        name = apps[next_app % len(apps)]
        extra = 0
        if name == "notepad":
            extra = note_n
            note_n += 1
        possessor.open_app(name, note_index=extra)
        overlay.set_line(random.choice(LINES))
        next_app += 1

    try:
        while not killer.hit.is_set():
            time.sleep(0.05)
            now = time.monotonic()
            if possessor.cursor_in_panic_corner():
                panic += 0.05
                if panic >= 0.45:
                    print("[banshee] panic corner — leaving", flush=True)
                    break
            else:
                panic = 0.0

            if stage == 0 and watch.events >= 1:
                spawn_app()
                stage = 1
                marked = watch.events
                grab_after = now + 3.0
            elif stage == 1 and now >= grab_after:
                watch.ignore_motion = True
                possessor.start_cursor_grab()
                overlay.set_line("your cursor asked me for directions.")
                stage = 2
                next_ghost_app = now + random.uniform(4.5, 7.0)
            elif stage == 2 and now >= next_ghost_app:
                spawn_app()
                next_ghost_app = now + random.uniform(5.0, 9.0)
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

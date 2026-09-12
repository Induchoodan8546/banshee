"""Faster haunt. After 15s the cursor is hers. Closed apps come back. Bazinga ends it."""

from __future__ import annotations

import random
import threading
import time

from banshee import config
from banshee.desktop import monitor, possessor
from banshee.desktop.overlay import Overlay
from banshee.room.voice import Voice
from banshee.system.banisher import Banisher


def _mischief(stop: threading.Event, overlay: Overlay, voice: Voice) -> None:
    started = time.monotonic()
    locked = False
    i = 0
    time.sleep(0.7)
    while not stop.is_set():
        elapsed = time.monotonic() - started
        heat = min(1.0, elapsed / 90.0)
        if elapsed >= 15 and not locked:
            possessor.lock_cursor_forever()
            locked = True
        possessor.reopen_missing()
        if overlay.chatting() and not locked:
            time.sleep(0.3)
            continue
        cycle = [
            "notepad",
            "search",
            "paint",
            "calculator",
            "cursor",
            "wordpad",
            "search",
            "paint",
            "charmap",
            "search",
        ]
        kind = cycle[i % len(cycle)]
        i += 1
        title = monitor.foreground_title() or "this"
        if kind == "paint":
            possessor.doodle_in_paint(title)
        elif kind == "cursor":
            if not locked:
                possessor.possess_cursor_burst(1.6 + heat)
        elif kind in ("calculator", "notepad", "wordpad", "charmap"):
            possessor.open_app(kind, note_index=1 if kind == "notepad" else 0)
        else:
            brain = None
            if not voice.busy and not voice.talking_to_player():
                brain = voice.brain
            possessor.open_search(title=title, brain=brain)
        overlay.keep_front()
        gap = 2.1 - 1.2 * heat
        waited = 0.0
        while waited < gap and not stop.is_set():
            possessor.reopen_missing()
            if overlay.chatting() and not locked:
                waited = 0.0
            time.sleep(0.15)
            waited += 0.15


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
    time.sleep(0.4)
    possessor.set_wallpaper()

    mischief = threading.Thread(target=_mischief, args=(killer.hit, overlay, voice), daemon=True)
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
        possessor.unlock_cursor()
        overlay.stop()
        killer.stop()
        possessor.restore_wallpaper()
        config.DATA.mkdir(parents=True, exist_ok=True)
        config.BANISHED_FLAG.write_text("1", encoding="utf-8")
        print("banished. wallpaper restored.", flush=True)
    return 0

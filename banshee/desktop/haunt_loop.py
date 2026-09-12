"""Possess: one haunt at a time. Chat box is never part of the haunt."""

from __future__ import annotations

import threading
import time

from banshee import config
from banshee.desktop import monitor, possessor
from banshee.desktop.overlay import Overlay
from banshee.room.voice import Voice
from banshee.system.banisher import Banisher


def _mischief(stop: threading.Event, overlay: Overlay) -> None:
    started = time.monotonic()
    i = 0
    time.sleep(2.5)
    while not stop.is_set():
        if overlay.chatting():
            time.sleep(0.4)
            continue
        elapsed = time.monotonic() - started
        heat = min(1.0, elapsed / 90.0)
        # later: more paint, search, cursor
        if heat < 0.25:
            bag = ("paint", "cursor", "notepad", "search", "calc")
        elif heat < 0.6:
            bag = ("paint", "search", "cursor", "search", "paint", "calc", "notepad")
        else:
            bag = ("search", "paint", "cursor", "search", "paint", "cursor", "notepad")
        kind = bag[i % len(bag)]
        i += 1
        title = monitor.foreground_title() or "this"
        if kind == "paint":
            possessor.doodle_in_paint(title)
        elif kind == "cursor":
            possessor.possess_cursor_burst(1.8 + heat)
        elif kind == "calc":
            possessor.open_app("calculator")
        elif kind == "notepad":
            possessor.open_app("notepad", note_index=1)
        else:
            possessor.open_search()
        overlay.keep_front()
        gap = 6.5 - 3.8 * heat
        waited = 0.0
        while waited < gap and not stop.is_set():
            if overlay.chatting():
                waited = 0.0
            time.sleep(0.2)
            waited += 0.2


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

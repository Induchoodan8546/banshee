"""After the bedroom closes, the blob wanders the real desktop."""

from __future__ import annotations

from banshee import config
from banshee.desktop import possessor
from banshee.desktop.wander import Wanderer
from banshee.room.voice import Voice
from banshee.system.banisher import Banisher


def run_possession() -> int:
    print("", flush=True)
    print("she left the drawing.", flush=True)
    print("type  bazinga  anywhere to banish her.", flush=True)
    print("", flush=True)

    killer = Banisher()
    killer.start()
    voice = Voice()
    wander = Wanderer(voice, killer)
    try:
        wander.run()
    except KeyboardInterrupt:
        print("[banshee] interrupted", flush=True)
    finally:
        possessor.stop_cursor_grab()
        killer.stop()
        possessor.restore_wallpaper()
        config.DATA.mkdir(parents=True, exist_ok=True)
        config.BANISHED_FLAG.write_text("1", encoding="utf-8")
        print("banished.", flush=True)
    return 0

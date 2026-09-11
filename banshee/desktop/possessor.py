"""Windows side effects. --safe turns every call into a log line."""

from __future__ import annotations

import json
import math
import random
import subprocess
import threading
import time
from pathlib import Path

from banshee.config import (
    ALLOWED_APPS,
    ASSETS_ROOM,
    ASSETS_UI,
    NOTE_NAME,
    PLAYGROUND,
    SAFE,
    WALLPAPER_SAVE,
)

NOTE_BODY = """you closed the window.
that is not an exorcism.

i am in the cursor now.
i am in notepad.
i am in the wallpaper.

the only spell is: bazinga
type it anywhere.

— banshee
"""

SPI_SETDESKWALLPAPER = 0x0014
SPI_GETDESKWALLPAPER = 0x0073
SPIF_UPDATEINIFILE = 0x0001
SPIF_SENDCHANGE = 0x0002


def _log(msg: str) -> None:
    print(f"[banshee] {msg}", flush=True)


def _user32():
    import ctypes

    return ctypes.windll.user32


class POINT:
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y


def _cursor() -> tuple[int, int]:
    import ctypes

    class P(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    pt = P()
    _user32().GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


def _set_cursor(x: int, y: int) -> None:
    _user32().SetCursorPos(int(x), int(y))


_grab: threading.Event | None = None
_grab_thread: threading.Thread | None = None


def _screen() -> tuple[int, int]:
    return _user32().GetSystemMetrics(0), _user32().GetSystemMetrics(1)


def move_cursor(dx: int | None = None, dy: int | None = None) -> None:
    dx = dx if dx is not None else random.randint(120, 280) * random.choice((-1, 1))
    dy = dy if dy is not None else random.randint(60, 160) * random.choice((-1, 1))
    if SAFE:
        _log(f"would drift cursor by ({dx}, {dy})")
        return
    x0, y0 = _cursor()
    sw, sh = _screen()
    x1 = max(8, min(sw - 8, x0 + dx))
    y1 = max(8, min(sh - 8, y0 + dy))
    steps = 18
    for i in range(1, steps + 1):
        _set_cursor(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps)
        time.sleep(0.01)


def start_cursor_grab() -> None:
    """Keep stealing the pointer so the human cannot hold it."""
    global _grab, _grab_thread
    stop_cursor_grab()
    if SAFE:
        _log("would possess the cursor (random wander, no human control)")
        return
    _grab = threading.Event()
    _grab_thread = threading.Thread(target=_cursor_loop, args=(_grab,), daemon=True)
    _grab_thread.start()
    _log("cursor possessed")


def stop_cursor_grab() -> None:
    global _grab, _grab_thread
    if _grab is not None:
        _grab.set()
    if _grab_thread is not None:
        _grab_thread.join(timeout=0.6)
    _grab = None
    _grab_thread = None


def _cursor_loop(stop: threading.Event) -> None:
    sw, sh = _screen()
    tx, ty = _cursor()
    angle = random.random() * math.tau
    speed = 9.0
    next_turn = time.monotonic()
    while not stop.is_set():
        now = time.monotonic()
        if now >= next_turn:
            angle += random.uniform(-1.2, 1.2)
            speed = random.uniform(6.0, 16.0)
            next_turn = now + random.uniform(0.35, 1.1)
            # new wander target so it does not sit still
            tx = max(20, min(sw - 20, tx + random.randint(-280, 280)))
            ty = max(20, min(sh - 20, ty + random.randint(-180, 180)))
        cx, cy = _cursor()
        # yank back if the human fought the pointer
        pull = 0.35
        tx = tx + (cx - tx) * 0.04
        x = cx + (tx - cx) * pull + math.cos(angle) * speed
        y = cy + (ty - cy) * pull + math.sin(angle) * speed
        x = max(2, min(sw - 3, x))
        y = max(2, min(sh - 3, y))
        # keep panic corner reachable: never park in 0,0 ourselves
        if x < 28 and y < 28:
            x, y = 80, 80
            tx, ty = sw * 0.5, sh * 0.5
        _set_cursor(x, y)
        time.sleep(0.016)


def write_note(text: str | None = None) -> Path:
    body = text or NOTE_BODY
    if SAFE:
        _log(f"would write {NOTE_NAME} in BansheePlayground")
        return PLAYGROUND / NOTE_NAME
    PLAYGROUND.mkdir(parents=True, exist_ok=True)
    path = PLAYGROUND / NOTE_NAME
    path.write_text(body, encoding="utf-8")
    _log(f"left a note at {path}")
    return path


def _current_wallpaper() -> str:
    import ctypes

    buf = ctypes.create_unicode_buffer(512)
    _user32().SystemParametersInfoW(SPI_GETDESKWALLPAPER, 512, buf, 0)
    return buf.value


def set_wallpaper() -> None:
    still = ASSETS_UI / "wallpaper.png"
    if not still.exists():
        still = ASSETS_ROOM / "bg.png"
    if SAFE:
        _log(f"would set wallpaper to {still}")
        return
    original = _current_wallpaper()
    WALLPAPER_SAVE.parent.mkdir(parents=True, exist_ok=True)
    WALLPAPER_SAVE.write_text(json.dumps({"original": original}), encoding="utf-8")
    _user32().SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        str(still.resolve()),
        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
    )
    _log("wallpaper possessed")


def restore_wallpaper() -> None:
    if SAFE:
        _log("would restore wallpaper")
        return
    original = ""
    if WALLPAPER_SAVE.exists():
        try:
            original = json.loads(WALLPAPER_SAVE.read_text(encoding="utf-8")).get("original", "")
        except json.JSONDecodeError:
            original = ""
    if original:
        _user32().SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            original,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
        )
        _log("wallpaper restored")
    if WALLPAPER_SAVE.exists():
        WALLPAPER_SAVE.unlink()


def open_app(name: str = "notepad") -> None:
    exe = ALLOWED_APPS.get(name.lower().strip(), ALLOWED_APPS["notepad"])
    if SAFE:
        _log(f"would open {exe}")
        return
    note = PLAYGROUND / NOTE_NAME
    args = [exe]
    if exe == "notepad.exe" and note.exists():
        args.append(str(note))
    subprocess.Popen(args, close_fds=True)
    _log(f"opened {exe}")


def cursor_in_panic_corner() -> bool:
    if SAFE:
        return False
    x, y = _cursor()
    return x <= 24 and y <= 24


class ActivityWatch:
    """Counts real attempts to use the machine (move, click, type)."""

    def __init__(self) -> None:
        self.events = 0
        self._origin: tuple[int, int] | None = None
        self._mouse = None
        self._keys = None

    def start(self) -> None:
        try:
            from pynput import keyboard, mouse
        except ImportError:
            _log("pynput missing — cannot watch input")
            return
        self._origin = _cursor() if not SAFE else (0, 0)

        def on_move(x: float, y: float) -> None:
            if self._origin is None:
                self._origin = (int(x), int(y))
                return
            ox, oy = self._origin
            if abs(int(x) - ox) + abs(int(y) - oy) >= 14:
                self.events += 1
                self._origin = (int(x), int(y))

        def on_click(x: float, y: float, button: object, pressed: bool) -> None:
            if pressed:
                self.events += 1

        def on_press(key: object) -> None:
            self.events += 1

        self._mouse = mouse.Listener(on_move=on_move, on_click=on_click)
        self._keys = keyboard.Listener(on_press=on_press)
        self._mouse.daemon = True
        self._keys.daemon = True
        self._mouse.start()
        self._keys.start()

    def stop(self) -> None:
        for listener in (self._mouse, self._keys):
            if listener is None:
                continue
            try:
                listener.stop()
            except Exception:
                pass
        self._mouse = None
        self._keys = None

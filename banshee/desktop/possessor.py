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

NOTE_BODY = """now your system is mine.

you closed the window.
that is not an exorcism.

type bazinga in the little box
if you want me gone.

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
_safe_zone = None  # callable -> (x0,y0,x1,y1) or None; cursor grab skips this box


def _screen() -> tuple[int, int]:
    return _user32().GetSystemMetrics(0), _user32().GetSystemMetrics(1)


def virtual_screen() -> tuple[int, int, int, int]:
    """x, y, w, h of the whole desktop (all monitors)."""
    u = _user32()
    return (
        int(u.GetSystemMetrics(76)),
        int(u.GetSystemMetrics(77)),
        int(u.GetSystemMetrics(78) or _screen()[0]),
        int(u.GetSystemMetrics(79) or _screen()[1]),
    )


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


def open_search() -> None:
    from banshee.config import SEARCH_URLS
    import webbrowser

    url = random.choice(SEARCH_URLS)
    if SAFE:
        _log(f"would open search {url}")
        return
    webbrowser.open(url)
    _log("opened a haunted search")


def nudge_brief() -> None:
    """One short yank. Cursor is then the human's again."""
    move_cursor()


def set_cursor_safe_zone(fn) -> None:
    """Chat box screen rect. Grab loop will not move the pointer inside it."""
    global _safe_zone
    _safe_zone = fn


def _in_safe_zone(x: int, y: int) -> bool:
    fn = _safe_zone
    if fn is None:
        return False
    try:
        box = fn()
    except Exception:
        return False
    if not box:
        return False
    x0, y0, x1, y1 = box
    pad = 8
    return (x0 - pad) <= x <= (x1 + pad) and (y0 - pad) <= y <= (y1 + pad)


def possess_cursor_burst(seconds: float = 2.4, on_end=None, overlay=None) -> None:
    """Brief cursor haunt. Never drags the pointer into the chat box."""
    start_cursor_grab()

    def _release() -> None:
        stop_cursor_grab()
        if on_end is not None:
            try:
                on_end()
            except Exception:
                pass

    threading.Timer(max(1.5, seconds), _release).start()


def start_cursor_grab() -> None:
    """Steal the pointer until stop_cursor_grab."""
    global _grab, _grab_thread
    stop_cursor_grab()
    if SAFE:
        _log("would possess the cursor briefly")
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
        if _in_safe_zone(cx, cy):
            time.sleep(0.016)
            continue
        pull = 0.35
        tx = tx + (cx - tx) * 0.04
        x = cx + (tx - cx) * pull + math.cos(angle) * speed
        y = cy + (ty - cy) * pull + math.sin(angle) * speed
        x = max(2, min(sw - 3, x))
        y = max(2, min(sh - 3, y))
        if x < 28 and y < 28:
            x, y = 80, 80
            tx, ty = sw * 0.5, sh * 0.5
        if _in_safe_zone(int(x), int(y)):
            time.sleep(0.016)
            continue
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


def open_app(name: str = "notepad", note_index: int = 0) -> None:
    exe = ALLOWED_APPS.get(name.lower().strip(), ALLOWED_APPS["notepad"])
    if SAFE:
        _log(f"would open {exe}")
        return
    args = [exe]
    if exe == "notepad.exe":
        PLAYGROUND.mkdir(parents=True, exist_ok=True)
        if note_index <= 0:
            path = PLAYGROUND / NOTE_NAME
            if not path.exists():
                path.write_text(NOTE_BODY, encoding="utf-8")
        else:
            path = PLAYGROUND / f"STILL_HERE_{note_index}.txt"
            path.write_text(
                f"still here.\nthis is note {note_index}.\ntype bazinga.\n— banshee\n",
                encoding="utf-8",
            )
        args.append(str(path))
    subprocess.Popen(args, close_fds=True)
    _log(f"opened {exe}")


def cursor_in_panic_corner() -> bool:
    if SAFE:
        return False
    x, y = _cursor()
    return x <= 24 and y <= 24


class ActivityWatch:
    """Counts the human trying to use the machine. Ignores ghost-moved cursor."""

    def __init__(self) -> None:
        self.events = 0
        self.ignore_motion = False
        self._origin: tuple[int, int] | None = None
        self._last = 0.0
        self._mouse = None
        self._keys = None

    def reset(self) -> None:
        self.events = 0
        self._origin = _cursor() if not SAFE else (0, 0)
        self._last = time.monotonic()

    def _bump(self) -> None:
        now = time.monotonic()
        if now - self._last < 0.7:
            return
        self._last = now
        self.events += 1

    def start(self) -> None:
        try:
            from pynput import keyboard, mouse
        except ImportError:
            _log("pynput missing — cannot watch input")
            return
        self.reset()

        def on_move(x: float, y: float) -> None:
            if self.ignore_motion:
                return
            if self._origin is None:
                self._origin = (int(x), int(y))
                return
            ox, oy = self._origin
            if abs(int(x) - ox) + abs(int(y) - oy) >= 80:
                self._origin = (int(x), int(y))
                self._bump()

        def on_click(x: float, y: float, button: object, pressed: bool) -> None:
            if pressed:
                self._bump()

        def on_press(key: object) -> None:
            self._bump()

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

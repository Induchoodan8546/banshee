"""Windows side effects. --safe turns every call into a log line."""

from __future__ import annotations

import json
import random
import subprocess
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


def move_cursor(dx: int | None = None, dy: int | None = None) -> None:
    dx = dx if dx is not None else random.randint(200, 400) * random.choice((-1, 1))
    dy = dy if dy is not None else random.randint(80, 180) * random.choice((-1, 1))
    if SAFE:
        _log(f"would drift cursor by ({dx}, {dy}) then return")
        return
    x0, y0 = _cursor()
    sw, sh = _user32().GetSystemMetrics(0), _user32().GetSystemMetrics(1)
    x1 = max(0, min(sw - 2, x0 + dx))
    y1 = max(0, min(sh - 2, y0 + dy))
    steps = 24
    for i in range(1, steps + 1):
        _set_cursor(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps)
        time.sleep(0.012)
    time.sleep(0.35)
    for i in range(1, steps + 1):
        _set_cursor(x1 + (x0 - x1) * i / steps, y1 + (y0 - y1) * i / steps)
        time.sleep(0.012)
    _set_cursor(x0, y0)
    _log("cursor drifted and came home")


def write_note(text: str | None = None) -> Path:
    body = text or (
        "you closed the window.\n"
        "that is not an exorcism.\n"
        "i live in the taskbar now.\n"
        "type bazinga if you want me gone.\n"
        "— banshee\n"
    )
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

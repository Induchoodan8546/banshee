"""Windows side effects. --safe turns every call into a log line."""

from __future__ import annotations

import ctypes
import json
import math
import os
import random
import shutil
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

def _exe_path(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    windir = os.environ.get("WINDIR", r"C:\Windows")
    for sub in ("System32", "SysWOW64"):
        cand = os.path.join(windir, sub, name)
        if os.path.isfile(cand):
            return cand
    return None


def _spawn(args: list[str]) -> bool:
    if not args:
        return False
    exe = _exe_path(args[0])
    if not exe:
        _log(f"skip missing app {args[0]}")
        return False
    try:
        subprocess.Popen([exe, *args[1:]], close_fds=True)
        return True
    except FileNotFoundError:
        _log(f"skip missing app {args[0]}")
        return False


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
_pause_until = 0.0
_cursor_locked = False
_wanted: set[str] = set()  # app keys: notepad, calculator, paint, ...


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


_SEARCH_FALLBACK = [
    "why is my mouse possessed windows 11",
    "can a cartoon ghost use google chrome",
    "how to get a blob out of taskbar",
    "is my wallpaper haunted",
    "notepad opened itself help",
    "paint drawing by itself windows",
    "bazinga exorcism keyboard spell",
    "why does calculator keep launching",
    "desktop pet stole my cursor",
    "do ghosts read window titles",
    "remove poltergeist from mspaint",
    "my computer is roasting me",
    "how to stop a banshee on windows",
    "why did chrome search for ghosts",
    "floating white blob on monitor",
    "is RAM a valid ghost habitat",
    "task manager vs cartoon spirit",
    "who keeps opening wikipedia randomly",
    "cursor moving without me touching it",
    "exorcise laptop with one word",
]
_used_queries: set[str] = set()


def _clean_query(text: str) -> str:
    import re

    line = (text or "").replace("\n", " ").strip().strip("\"'`")
    line = re.sub(r"https?://\S+", "", line)
    line = re.sub(r"[^a-zA-Z0-9 '\-?]", " ", line)
    line = " ".join(line.split())
    if len(line) > 80:
        line = line[:80].rsplit(" ", 1)[0]
    return line


def invent_search_query(title: str = "", brain=None) -> str:
    q = ""
    if brain is not None:
        try:
            raw = brain.chat(
                "Invent a silly Google search a cartoon ghost would type. "
                f"The human was just using: {title or 'the desktop'}. "
                "Reply with ONLY 5 to 8 search words. No quotes. No URL. No extra sentences.",
                remember=False,
            )
            q = _clean_query(raw)
        except Exception:
            q = ""
    if len(q) < 4:
        unused = [s for s in _SEARCH_FALLBACK if s not in _used_queries]
        q = random.choice(unused or _SEARCH_FALLBACK)
    _used_queries.add(q)
    return q


def open_search(title: str = "", brain=None) -> None:
    import urllib.parse
    import webbrowser

    query = invent_search_query(title, brain=brain)
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    if SAFE:
        _log(f"would search: {query}")
        return
    webbrowser.open(url)
    _wanted.add("browser")
    _log(f"searched: {query}")


def nudge_brief() -> None:
    """One short yank. Cursor is then the human's again."""
    move_cursor()


def set_cursor_safe_zone(fn) -> None:
    """Chat box screen rect. Grab loop will not move the pointer inside it."""
    global _safe_zone
    _safe_zone = fn


def pause_cursor(seconds: float = 12.0) -> None:
    """Stop haunting the mouse so the human can use the chat box."""
    global _pause_until
    if _cursor_locked:
        return
    _pause_until = time.monotonic() + seconds
    stop_cursor_grab()


def lock_cursor_forever() -> None:
    global _cursor_locked
    _cursor_locked = True
    start_cursor_grab()
    _log("cursor locked — bazinga is the only way out")


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
    pad = 140
    return (x0 - pad) <= x <= (x1 + pad) and (y0 - pad) <= y <= (y1 + pad)


def possess_cursor_burst(seconds: float = 2.4, on_end=None, overlay=None) -> None:
    """Brief cursor haunt. Never drags the pointer into the chat box."""
    if time.monotonic() < _pause_until:
        _log("skip grab — chat is in use")
        if on_end is not None:
            on_end()
        return
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


def unlock_cursor() -> None:
    global _cursor_locked
    _cursor_locked = False
    stop_cursor_grab()


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
        if now < _pause_until:
            time.sleep(0.05)
            continue
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
    key = name.lower().strip()
    exe = ALLOWED_APPS.get(key, ALLOWED_APPS["notepad"])
    if SAFE:
        _log(f"would open {key} ({exe})")
        _wanted.add(key)
        return
    args = [exe]
    if key == "notepad":
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
    if not _spawn(args):
        return
    _wanted.add(key)
    _log(f"opened {key}")


def doodle_in_paint(mock_line: str = "") -> None:
    """Open Paint, maximize, then actually drag-draw with pynput."""
    if SAFE:
        _log("would scribble in paint with the cursor")
        return
    paused = _cursor_locked
    stop_cursor_grab()
    if not _spawn(["mspaint.exe"]):
        if paused or _cursor_locked:
            start_cursor_grab()
        return
    _wanted.add("paint")
    hwnd = 0
    for _ in range(60):
        hwnd = _find_window("paint")
        if hwnd:
            break
        time.sleep(0.1)
    if not hwnd:
        _log("paint window not found")
        if paused or _cursor_locked:
            start_cursor_grab()
        return
    u = _user32()
    u.ShowWindow(hwnd, 3)  # maximize
    _foreground(hwnd)
    time.sleep(1.0)
    rect = _window_rect(hwnd)
    if not rect:
        if paused or _cursor_locked:
            start_cursor_grab()
        return
    left, top, right, bottom = rect
    w, h = max(100, right - left), max(100, bottom - top)
    # Win11 ribbon is tall — canvas is the lower 55%
    cx = left + w // 2
    cy = top + int(h * 0.62)
    try:
        _pynput_scribble(cx, cy)
        _log("scribbled in paint")
    except Exception as exc:
        _log(f"paint scribble failed: {exc}")
    if paused or _cursor_locked:
        start_cursor_grab()


def _pynput_scribble(cx: int, cy: int) -> None:
    from pynput.mouse import Button, Controller

    mouse = Controller()
    mouse.position = (cx, cy)
    time.sleep(0.12)
    mouse.click(Button.left, 1)
    time.sleep(0.18)
    mouse.position = (cx - 40, cy)
    time.sleep(0.06)
    mouse.press(Button.left)
    # jagged scribble, not a circle
    pts = []
    for i in range(70):
        x = cx - 80 + i * 5
        y = cy + int(45 * math.sin(i * 0.35)) + (20 if i % 6 == 0 else -16)
        pts.append((x, y))
    for x, y in pts:
        mouse.position = (x, y)
        time.sleep(0.02)
    mouse.release(Button.left)
    time.sleep(0.1)
    # second stroke: a big X
    mouse.position = (cx - 50, cy - 40)
    mouse.press(Button.left)
    for t in range(20):
        mouse.position = (cx - 50 + t * 6, cy - 40 + t * 5)
        time.sleep(0.018)
    mouse.release(Button.left)
    mouse.position = (cx + 70, cy - 40)
    mouse.press(Button.left)
    for t in range(20):
        mouse.position = (cx + 70 - t * 6, cy - 40 + t * 5)
        time.sleep(0.018)
    mouse.release(Button.left)


def _find_window(title_part: str) -> int:
    user32 = _user32()
    found: list[int] = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def _cb(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        title = buf.value.lower()
        if title_part in title and "3d" not in title:
            found.append(int(hwnd))
        return True

    cb = WNDENUMPROC(_cb)
    user32.EnumWindows(cb, 0)
    return found[0] if found else 0


def _window_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    r = RECT()
    if not _user32().GetWindowRect(hwnd, ctypes.byref(r)):
        return None
    return int(r.left), int(r.top), int(r.right), int(r.bottom)


def _foreground(hwnd: int) -> None:
    u = _user32()
    u.ShowWindow(hwnd, 9)
    u.keybd_event(0x12, 0, 0, 0)
    u.SetForegroundWindow(hwnd)
    u.keybd_event(0x12, 0, 2, 0)


def _send_mouse(flags: int, x: int = 0, y: int = 0) -> None:
    extra = ctypes.c_ulong(0)

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", ctypes.c_long),
            ("dy", ctypes.c_long),
            ("mouseData", ctypes.c_ulong),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]

    inp = INPUT()
    inp.type = 0
    inp.mi = MOUSEINPUT(x, y, 0, flags, 0, ctypes.pointer(extra))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def _move_abs(x: int, y: int) -> None:
    sw, sh = _screen()
    ax = int(x * 65535 / max(1, sw - 1))
    ay = int(y * 65535 / max(1, sh - 1))
    _set_cursor(x, y)
    _send_mouse(0x0001 | 0x8000, ax, ay)  # MOVE | ABSOLUTE


def _drag_scribble(x0: int, y0: int) -> None:
    _move_abs(x0, y0)
    time.sleep(0.08)
    _send_mouse(0x0002)  # LEFTDOWN
    time.sleep(0.04)
    for i in range(56):
        x = x0 + i * 6
        y = y0 + int(28 * math.sin(i * 0.7)) + (18 if i % 5 == 0 else -14)
        _move_abs(x, y)
        time.sleep(0.016)
    _send_mouse(0x0004)  # LEFTUP
    time.sleep(0.05)


def _is_running(exe: str) -> bool:
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {exe}"],
            text=True,
            errors="ignore",
            creationflags=0x08000000,
        )
        return exe.lower() in out.lower() and "PID" in out
    except Exception:
        return False


_APP_PROCS = {
    "notepad": ("notepad.exe",),
    "calculator": ("calc.exe", "calculator.exe", "applicationframehost.exe"),
    "paint": ("mspaint.exe",),
    "wordpad": ("wordpad.exe", "write.exe"),
    "charmap": ("charmap.exe",),
}
_APP_TITLES = {
    "notepad": "notepad",
    "calculator": "calculator",
    "paint": "paint",
    "wordpad": "wordpad",
    "charmap": "character map",
}


def _app_alive(key: str) -> bool:
    title = _APP_TITLES.get(key)
    if title and _find_window(title):
        return True
    if key == "calculator" and _find_window("calc"):
        return True
    for proc in _APP_PROCS.get(key, ()):
        if key == "calculator" and proc == "applicationframehost.exe":
            continue
        if _is_running(proc):
            return True
    return False


def reopen_missing() -> None:
    """If the human closed a haunted app, open it again."""
    for key in list(_wanted):
        if key == "browser":
            browsers = ("msedge.exe", "chrome.exe", "firefox.exe", "brave.exe")
            if not any(_is_running(b) for b in browsers) and not _find_window("google"):
                _log("browser was closed — searching again")
                open_search()
            continue
        if _app_alive(key):
            continue
        _log(f"{key} was closed — opening it again")
        if key == "paint":
            _spawn(["mspaint.exe"])
        else:
            open_app(key, note_index=1)


def defy(text: str) -> None:
    """If they dare her, she does the thing they said she couldn't."""
    t = text.lower()
    did = False
    if any(w in t for w in ("browser", "chrome", "google", "search", "internet")):
        open_search()
        did = True
    if any(w in t for w in ("cursor", "mouse", "pointer")):
        if _cursor_locked:
            start_cursor_grab()
        else:
            possess_cursor_burst(2.6)
        did = True
    if any(w in t for w in ("paint", "draw", "doodle")):
        doodle_in_paint()
        did = True
    if any(w in t for w in ("stop", "leave", "annoying", "go away", "enough", "quit", "can't", "cant", "cannot")):
        open_search()
        doodle_in_paint()
        open_app("calculator")
        did = True
    if did:
        _log("proved them wrong")


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

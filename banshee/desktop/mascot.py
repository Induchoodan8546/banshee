"""Always-on-top ghost with a speech bubble, wandering the whole desktop."""

from __future__ import annotations

import ctypes
import math
import random
import time
import tkinter as tk

from PIL import Image, ImageTk

from banshee.config import ASSETS_GHOST
from banshee.desktop import possessor

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_NOACTIVATE = 0x08000000
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

WIN_W = 240
WIN_H = 250
SPRITE = 120


def _click_through(widget: tk.Misc) -> None:
    try:
        widget.update_idletasks()
        user32 = ctypes.windll.user32
        wid = int(widget.winfo_id())
        parent = int(user32.GetParent(wid) or 0)
        hwnd = parent or wid
        if ctypes.sizeof(ctypes.c_void_p) == 8:
            get_long = user32.GetWindowLongPtrW
            set_long = user32.SetWindowLongPtrW
        else:
            get_long = user32.GetWindowLongW
            set_long = user32.SetWindowLongW
        style = get_long(hwnd, GWL_EXSTYLE)
        set_long(
            hwnd,
            GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_NOACTIVATE,
        )
        user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
    except Exception:
        pass


def _wrap(text: str, width: int = 24) -> list[str]:
    words = text.replace("\n", " ").split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = (cur + " " + word).strip()
        if len(trial) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines[:3]


class DesktopMascot:
    def __init__(self, root: tk.Tk) -> None:
        vx, vy, sw, sh = possessor.virtual_screen()
        if sw <= 1:
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            vx, vy = 0, 0
        self.vx, self.vy, self.sw, self.sh = vx, vy, sw, sh
        self.x = float(vx + sw * 0.4)
        self.y = float(vy + sh * 0.3)
        self.tx, self.ty = self.x, self.y
        self._speed = 1.45
        self._t = 0.0
        self._talk = 0.0
        self._blink = 0.0
        self._next_blink = random.uniform(1.6, 3.2)
        self._next_drift = time.monotonic() + 0.2
        self._line = ""
        self._hold = 0.0
        self._photos: dict[str, ImageTk.PhotoImage] = {}
        self._kind = "body"
        self._bubble_ids: list[int] = []

        win = tk.Toplevel(root)
        self.win = win
        win.overrideredirect(True)
        win.configure(bg="#ff00ff")
        win.attributes("-topmost", True)
        try:
            win.wm_attributes("-transparentcolor", "#ff00ff")
        except tk.TclError:
            pass
        win.geometry(f"{WIN_W}x{WIN_H}+{int(self.x)}+{int(self.y)}")

        self.canvas = tk.Canvas(
            win,
            width=WIN_W,
            height=WIN_H,
            bg="#ff00ff",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()
        self._load_frames()
        self._sprite = self.canvas.create_image(
            WIN_W // 2,
            WIN_H - 70,
            image=self._photos["body"],
        )
        win.update_idletasks()
        _click_through(win)

    def _load_frames(self) -> None:
        for name, file in (
            ("body", "body.png"),
            ("blink", "eyes_closed.png"),
            ("talk", "mouth_talk.png"),
        ):
            path = ASSETS_GHOST / file
            im = Image.open(path).convert("RGBA")
            im = im.resize((SPRITE, SPRITE), Image.Resampling.NEAREST)
            self._photos[name] = ImageTk.PhotoImage(im)

    def talk(self, text: str = "") -> None:
        self._talk = 3.0
        if text:
            self.say(text)

    def say(self, text: str, hold: float | None = None) -> None:
        text = (text or "").replace("\n", " ").strip()
        if not text or text == "...":
            return
        self._line = text
        self._talk = max(self._talk, 2.0)
        self._hold = hold if hold is not None else max(6.5, min(12.0, 2.4 + len(text) * 0.1))
        self._draw_bubble()

    def pin(self) -> None:
        try:
            self.win.attributes("-topmost", True)
            _click_through(self.win)
        except tk.TclError:
            pass

    def step(self, dt: float = 0.033) -> None:
        self._t += dt
        now = time.monotonic()
        self._next_blink -= dt
        if self._next_blink <= 0:
            self._blink = 0.12
            self._next_blink = random.uniform(1.5, 3.0)
        if self._blink > 0:
            self._blink -= dt
        if self._talk > 0:
            self._talk -= dt
        if self._hold > 0:
            self._hold -= dt
            if self._hold <= 0:
                self._line = ""
                self._clear_bubble()

        if self._hold <= 0.6 and now >= self._next_drift:
            self._pick_target()
            self._next_drift = now + random.uniform(1.5, 2.6)

        # crawl while the bubble is up so the user can read it
        rate = 0.45 if self._hold > 0.5 else self._speed
        k = min(1.0, dt * rate)
        self.x += (self.tx - self.x) * k
        self.y += (self.ty - self.y) * k
        bob = math.sin(self._t * 1.8) * 5.0

        chat_x = self.vx + self.sw - 300
        chat_y = self.vy + self.sh - 230
        x = int(self.x)
        y = int(self.y + bob)
        x = max(self.vx, min(self.vx + self.sw - WIN_W, x))
        y = max(self.vy, min(self.vy + self.sh - WIN_H - 36, y))
        if x + WIN_W > chat_x and y + WIN_H > chat_y:
            x = int(chat_x - WIN_W - 8)

        try:
            self.win.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")
            kind = "body"
            if self._blink > 0:
                kind = "blink"
            elif self._talk > 0 or self._hold > 0:
                kind = "talk"
            if kind != self._kind:
                self._kind = kind
                self.canvas.itemconfigure(self._sprite, image=self._photos[kind])
            gy = WIN_H - 70 + math.sin(self._t * 2.2) * 2
            self.canvas.coords(self._sprite, WIN_W // 2, gy)
        except tk.TclError:
            pass
        self.pin()

    def _draw_bubble(self) -> None:
        self._clear_bubble()
        if not self._line:
            return
        lines = _wrap(self._line)
        if not lines:
            return
        pad = 8
        line_h = 16
        bw = min(WIN_W - 12, max(len(s) for s in lines) * 8 + pad * 2)
        bh = len(lines) * line_h + pad * 2
        x0 = (WIN_W - bw) // 2
        y0 = 8
        box = self.canvas.create_rectangle(
            x0, y0, x0 + bw, y0 + bh,
            fill="#f8f0ff",
            outline="#baa0d6",
            width=2,
        )
        tip = self.canvas.create_polygon(
            WIN_W // 2 - 7, y0 + bh,
            WIN_W // 2 + 7, y0 + bh,
            WIN_W // 2, y0 + bh + 8,
            fill="#f8f0ff",
            outline="#baa0d6",
        )
        self._bubble_ids = [box, tip]
        for i, line in enumerate(lines):
            tid = self.canvas.create_text(
                WIN_W // 2,
                y0 + pad + i * line_h + 6,
                text=line,
                fill="#1c122a",
                font=("Consolas", 9),
            )
            self._bubble_ids.append(tid)

    def _clear_bubble(self) -> None:
        for item in self._bubble_ids:
            try:
                self.canvas.delete(item)
            except tk.TclError:
                pass
        self._bubble_ids = []

    def _pick_target(self) -> None:
        roll = random.random()
        if roll < 0.3:
            try:
                mx, my = possessor._cursor()
                self.tx = mx - WIN_W / 2
                self.ty = my - WIN_H / 2
                self._speed = random.uniform(1.2, 1.9)
                return
            except Exception:
                pass
        self.tx = random.uniform(self.vx + 8, self.vx + max(40, self.sw - WIN_W - 8))
        self.ty = random.uniform(self.vy + 8, self.vy + max(40, self.sh - WIN_H - 70))
        self._speed = random.uniform(1.15, 1.85)
